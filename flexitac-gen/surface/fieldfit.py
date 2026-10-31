"""Field-only containment for CAD mode: the fit option ``containment: field`` (masked-field phase P5d).

The user's routing decisions (claude/specs/masked-field/PLAN.md, section 9;
P5-diagonal-bus.md, section 4): only the taxel field has to lie on the
selected surface; the Row bands, the Column fan-out and both tails may leave
it.  Every proposal is built with the diagonal Row bus
(``routing.row_sides``, :mod:`engine.diagonal`), so any row- and
column-convex (HV-convex) field builds.

**F.**  The taxel field F is the crossing region P (each row's crossing
strip and the fillers between rows) grown by the field margin
(``routing.active_edge_clearance_mm``, 0.5 mm) as a box, slab by slab.  F
must lie inside the surface's outline inset by ``edge_margin_mm``, the exit
edge included (P may come up to the exit at the margin), outside the holes,
the covered walls and the strained facets, and off the bends tighter than
the stack may follow, but for its corner zones (the user's corner
tolerance, P5-diagonal-bus.md section 16, at every convex corner since
section 24): at each convex corner of F (a run's end that the neighbouring
row's run does not reach, and the outer ends of the first and last rows),
F's margin within :func:`corner_reach` of P's corner may leave that usable
surface by :data:`CORNER_TOLERANCE_MM` across x and across y (with the 0.5
mm margin it always does at most: every point of a zone lies within it of
P's corner).  P always lies on it, the middle third of every side of F
keeps its full margin, and a corner where the neighbouring run reaches as
far or farther (an aligned or a concave end) keeps its whole margin too.
The search decides it exactly on the strips of
:class:`surface.fill.FreeSpace`; the winners are built and F less its zones
checked exactly (:func:`field_parts`, :func:`convex_corners`,
:func:`surface.fit.check_containment`, the exit a wall).

**The lattice.**  Per pitch, frame (each exit, unturned and, with
``rotation: auto``, turned by 10-30 degrees) and lattice phase, cell
``(a, j)`` is the crossing square ``[X(a), X(a) + w] x [Y(j), Y(j) + w]``,
phase 0 putting the first column's and the first row's grown strips on the
usable edge (the frame's outline extremes less the edge margin).
Row j's run ``[a, b]`` is free when the strip ``[X(a) - m, X(b) + w + m] x
[Y(j) - m, Y(j) + w + m]`` less its four corner zones lies on the free
space (its bands, :func:`row_bands`, each in one free interval), and each
zone is free on its own or not (``zones``); when the gap between rows is
wider than ``2 m`` (sparse pitches) the filler band up to ``Y(j + 1) - m``
must be free over the two rows' common extent, as the engine builds the
filler (:func:`lattice`'s ``band``, exact since section 26b; a full
rectangle's rows share their runs, so ``up`` holds it there).  The
coarse phases also take the phase that centres the whole lattice in the
usable extent (:func:`centred_phase`), searched last.

**The search.**  The largest HV-convex set of free runs within the caps is
found exactly by a dynamic program (:func:`best_convex`: per row and run,
four monotonicity phases of the two ends, the predecessors read from 2-D
prefix maxima in O(C^2) per row, each corner zone held free unless its
corner is convex, which depends on the two runs' ends and is folded into
the tables exactly (:func:`_zone_tables`); it stops once no state can still beat the
threshold, each state's reach bounded by the runs above it within the ends
its phase allows), and the largest full rectangle on its own
(:func:`best_rectangle`); with ``max_area`` the DP takes the most cells
per lattice and the rank P's area.  Shaped fields and rectangles take the
same caps (the user's decision, P5-diagonal-bus.md section 21: coverage of
the selection first): ``max_rows`` x ``max_columns`` (64), a named reader
its lines, either way round, ``auto`` the largest reader's 48 x 48
(:func:`caps`).  A lattice
larger than the caps is first searched whole (no window holds more, and
the whole one's field is the answer when it fits the caps), then window by
window.  Lattices are searched best bound first (:func:`lattice_bound`, an
exact upper bound) and pruned against the best counts found: the unturned
frames first (the coarse phases 0 and p/2 on every exit, then the quarter
phases on every exit), then the turned frames, only where they can beat the
best unturned field by :data:`TURN_GAIN` (3 %), so that the unturned search
is never pruned by a turned field.  The search stops after
:data:`WORK_BUDGET` cells of DP work (a deterministic count): the
pathological inputs (large non-convex faces at fine pitches) keep the best
fields found by then.

**Symmetric faces** (the user's request, P5-diagonal-bus.md section 22:
"if the geometric face is symmetric, make the sensor symmetric too, as far
as possible").  Per exit, the selection's outline and holes mirrored about
the axis through the exit chord's midpoint, perpendicular to it, must lie
within :data:`SYMMETRY_TOLERANCE_MM` of themselves (:func:`exit_symmetry`).
On such an exit the fit also searches lattices centred on the axis (a
column on it, or the axis between two columns: :func:`symmetric_lattice`)
for fields whose every row is its own mirror image, exactly
(:func:`best_symmetric`: runs about one centre, their half widths rising
then falling), and turns no frame of an exit whose such field holds
within :data:`SYMMETRY_GAIN` (20 %) of its best unturned field (the user's
decisions of 2026-10-27, sections 26.17 and 26.19: on a symmetric face the
sensor is symmetric, unless a field that breaks the symmetry holds at
least 20 % more).

**Rank.**  More taxels (``max_area``: a larger P), then the larger pitch,
the smaller turn, the unmasked field, the denser readout, the fewer corners
that need the tolerance, a symmetric field; a turned field only when it has
at least 3 % more taxels than the best unturned one.  When
the fit chooses among several exits, the fields within
:data:`NARROW_TIP_TAXELS` (or 1 %) of the most go first, their exits ordered by the
tip of each exit's best such field (F's width at ROW_01, the narrowest
first) and each exit's fields by rank: the user's answer to the crank pad,
whose cut corner gives 669 taxels (670 with the corner tolerance) with F
64.4 mm wide at ROW_01 and its 70 mm leg 666 with F 14.4 mm wide there
(within :data:`NARROW_TIP_TAXELS` or 1 % of the most).  Then symmetric
fields first (:func:`symmetric_first`; the user's decisions of 2026-10-27,
section 26.17: faces symmetric like the WidowX's take a centred sensor
too, and section 26.19: a threshold of 20 %): each symmetric exit's best
symmetric field that holds within :data:`SYMMETRY_GAIN` of the most of
all the fields goes first, the narrow tip choosing among several, and each
other one leads its exit's fields when it holds within it of their best;
a field that breaks the symmetry (an asymmetric or a turned one) leads
only with at least 1.2 times the best symmetric field's value, decided on
the search's fields before the tip step (the symmetric field then follows
as an alternative).  Then tip first (section 26, the option
``tip_first``, :func:`tip_first`): within 3 % of the most taxels
on an exit (a symmetric group's: of its symmetric fields) the field
reaching nearest the fingertip (the face's end opposite the exit) leads
its group, its zero-cost tie taking the place of the field it displaces
(section 26.17).  The fit follows the selected area alone (the user's
decision of 2026-10-26, section 26.16): no rectangle shape, no rectangle
preference; a full rectangle is a field like any other
(:func:`best_rectangle`), proposed when it ranks.

**Realize.**  Each winner is built with ``routing.row_sides`` (the option
``row_sides``), default routing and ``rows_top`` first, its tails long
enough that both end on one line across the boards, so the stacked contacts
line up (P5-diagonal-bus.md sections 27.3 and 27.4): the nearest line on
which each tail is at least the shortest tail long and ends at least
``tail_extension_mm`` beyond the surface's lowest edge under it
(:func:`tail_lengths`), DRC and registration as every build; its F is
checked exactly, and a field whose F leaves the surface is peeled (an end
cell nearest the failure, both ends of its row for a symmetric field,
:func:`peel_field`), at most :data:`MAX_ATTEMPTS` builds per field.  The
proposal reports how much of each board lies on the surface and how far it
overhangs the surface's sides (:func:`routing_report`), and its symmetry
(:func:`symmetry_report`).
"""

from __future__ import annotations

import bisect
import math
from itertools import accumulate, repeat
from operator import add, rshift, sub
from typing import Any, Mapping, Sequence

from engine import design_mask, field_footprint, generate_design
from engine.geometry import orthoconvex_ring, point_in_polygon, rect_union_slabs, segments_intersect

from . import fill, fit
from . import reader as reader_module
from .errors import SurfaceError

# A turned field ranks only with at least TURN_GAIN[0] / TURN_GAIN[1] times the best unturned field's taxels.
TURN_GAIN = (103, 100)
# With several exits, the fields within this many taxels of the most, or within this share of it when that is more, rank
# by their tip (the user's answer: on the crank pad 666 on the 70 mm leg against 669 at the cut corner; with the corner
# tolerance 670 there).
NARROW_TIP_TAXELS = 3
NARROW_TIP_SHARE = (1, 100)
# Builds per field (the first and its peels).
MAX_ATTEMPTS = 3
# Fields built at most per fit (every proposal and the fields that failed).
MAX_REALIZE = 24
# Quarter phases on this many of the best turned frames (and on every unturned one).
FINE_FRAMES = 2
# With rotation auto, the frames turned against this many of the best exits (by their unturned fields).
TURNED_EXITS = 2
# The pitches of max_area beyond the first: on this many of the best frames; and the exits its seed searches.
LADDER_FRAMES = 2
SEED_EXITS = 2
# Distinct readouts the pruning keeps beyond the best one (the proposals' alternatives), and the least share of
# the best value an alternative is searched for.
SPARE_READOUTS = 1
ALTERNATIVE_SHARE = (97, 100)
# The caps of the fit without caps that chooses the exit when a cap binds (section 23): more than any lattice holds.
UNCAPPED = 4096
# The searches of a capped exit whose field at the far end needs tails past the template's maximum (200 mm on the
# surface), each nearer the exit (section 23).
REACH_ATTEMPTS = 4
_NOISE = 1e-9
# F's margin may leave the usable surface by at most this (mm) at F's corners: the user's corner tolerance (P5-diagonal-bus.md
# section 16).  The taxels (P) stay wholly on it, and along F's sides the full margin (the cross: P grown across x and
# across y); only the corner squares beyond P's convex corners may leave it.
CORNER_TOLERANCE_MM = 0.5
# A board's bend across a boundary edge looks this many facets beyond it (a fillet's inner edges).
WRAP_RINGS = 3
# A lattice larger than the caps is searched whole first when that costs at most this many windows' DPs.
WHOLE_LATTICE_COST = 4
# The DP work of one fit's search (cells of the DP's tables, n * n per row walked, :func:`best_convex`): the lattices and
# windows beyond it are not searched (about 2-3 s).  With shaped fields up to 64 x 64 (P5-diagonal-bus.md section 21) the
# fixtures need at most 1.9 million (fewer windows than at 32 x 32: the fin 0.75 million, 3.0 before), a 60 x 40 plate with
# a round hole at 1.5 mm 3.2 million and keeps its fields; a long face spends it on its unturned lattices (a 150 x 30 mm
# strip at 2 mm: 66 million unbounded, 54 s, for a field turned 30 degrees with 7 % more taxels).
WORK_BUDGET = 3_000_000
# Bits of a DP state's identity in its packed key (value << _SHIFT | identity).
_SHIFT = 24
_MASK = (1 << _SHIFT) - 1
# A free zone's cap on a packed key (``min(key, cap)``: a blocked zone's cap is -1).
_FREE = 1 << 62
# Symmetric sensors on symmetric faces (the user's request, P5-diagonal-bus.md section 22): the selection is symmetric about
# an exit when its outline and holes, mirrored about the axis through the exit's chord midpoint perpendicular to it, lie
# within this (mm) of themselves (faceting, collinear segments and flattening noise stay under it).
SYMMETRY_TOLERANCE_MM = 0.05
# The mirrored outline is sampled at every vertex and at most this far apart (mm) along its segments; its deviation is
# reported up to SYMMETRY_REPORT_MM (None beyond).
SYMMETRY_SAMPLE_MM = 1.0
SYMMETRY_REPORT_MM = 1.0
# A field that breaks a symmetric face's symmetry (an asymmetric field, on any exit, or a turned one) ranks before the best
# symmetric field only with at least SYMMETRY_GAIN[0] / SYMMETRY_GAIN[1] times its value (taxels; with max_area P's area),
# 20 % more or exactly that: the user's decision of 2026-10-27 (P5-diagonal-bus.md section 26.19), "可以加个门槛" (a
# threshold can be added), the 20 % the lead's example ("例如大 20 % 以上就让不对称的排第一", 20 % or more).  Compared
# on the search's fields, before the tip step (:func:`symmetric_first`), so the tip never flips it: symmetry costs under
# 20 %, the tip at most 3 % more of the best symmetric field.
SYMMETRY_GAIN = (120, 100)
# Tip first (the user's request of 2026-10-26, P5-diagonal-bus.md section 26: "the taxels stack from the fingertip as far as
# possible"; the fingertip the end of the face opposite the exit).  Shape fill: within TIP_SHARE of the most taxels on a
# group's exit (unturned, at its pitch: TURN_GAIN's 3 %; a symmetric group's the most of its symmetric fields there, so
# symmetry itself is free and the tip costs at most 3 % of the best symmetric field: the user's decision of 2026-10-27,
# section 26.17), the field reaching nearest the fingertip leads; a reach within pitch / TIP_SLACK of the farthest counts
# as reaching it (the lattice phases step by p / 4; a symmetric group's by p / 8, TIP_ROW_PHASES); the field it displaces
# gives its place to its own zero-cost tie (at least as many taxels, reaching within that slack of the farthest such
# field).  Reach first: at a pointed tip the tip-first field may end in a single taxel (the user, 2026-10-26: "if the
# gripper is very pointed, it can stick out just one taxel").  With tip_first false that tie alone takes the slot
# (coverage first: no taxel given up).
TIP_SHARE = (97, 100)
TIP_SLACK = 8
# A symmetric group's tip pass takes the row phases k p / TIP_ROW_PHASES (and the centred one): its fields' columns are
# fixed by the axis, so the row phase alone moves a field toward the tip (the isosceles triangle's apex: 322 taxels reach
# 57.15 mm at 5 p / 8, the quarter phases' farthest within the share 56.9 mm; section 26.18).  A symmetric lattice's DP is
# linear in its rows.  Its slack is half that step, p / TIP_SYMMETRIC_SLACK, as p / 8 is half the quarter phases' step: a
# field a phase short of the farthest does not count as reaching it.
TIP_ROW_PHASES = 8
TIP_SYMMETRIC_SLACK = 16
# The tip pass's own work budget per group (its meter, :func:`tip_pass`; the search's meter and WORK_BUDGET untouched).
TIP_WORK_BUDGET = 3_000_000  # cells, as WORK_BUDGET


# --------------------------------------------------------------------------
# The lattice: free runs per row
# --------------------------------------------------------------------------


def corner_inset(margin: float, tolerance: Any = None) -> float:
    """How far P grows all round on the usable surface besides its sides' margin: ``margin - tolerance`` (box), 0 when the
    corner tolerance holds the margin (every point of a corner zone lies within the margin of P's corner, across x and
    across y)."""

    tolerance = CORNER_TOLERANCE_MM if tolerance is None else tolerance
    return round(max(0.0, margin - tolerance), 9)


def corner_reach(margin: float, width: float, tolerance: Any = None) -> float:
    """How far a corner zone reaches along P's sides from its convex corner: the margin, at most a third of a crossing
    (the middle third of every side of a taxel keeps the full margin), and 0 without a corner tolerance."""

    tolerance = CORNER_TOLERANCE_MM if tolerance is None else tolerance
    if tolerance <= 0:
        return 0.0
    return round(min(margin, width / 3), 9)


def row_bands(y: float, width: float, margin: float, reach: float, inner: float) -> list:
    """The bands a row's run must hold free: ``(low, high, growth across x)`` from the strip's bottom margin to its top
    one (:func:`lattice`), a growth -r keeping the run's ends' zones out."""

    cuts = sorted({y - margin, y - inner, y, y + reach, y + width - reach, y + width, y + width + inner, y + width + margin})
    bands = []
    for low, high in zip(cuts, cuts[1:]):
        middle = (low + high) / 2
        grow = -reach if (middle < y or middle > y + width) else 0.0
        if y + reach - _NOISE <= middle <= y + width - reach + _NOISE:
            grow = margin
        if y - inner - _NOISE <= middle <= y + width + inner + _NOISE:
            grow = max(grow, inner)
        bands.append((low, high, grow))
    return bands


def lattice(space: Any, pitch: float, width: float, margin: float, phase: Sequence[float], tolerance: Any = None,
            count: Any = None) -> dict:
    """The lattice of one frame and phase: per row (bottom to top) the largest free run end from each cell, and the free
    corner zones of each cell.

    F less its corner zones at its convex corners must lie on the usable
    surface (section 24; :func:`convex_corners`): a corner zone is F's
    margin within ``reach`` (:func:`corner_reach`, the margin) of a run's
    end where the neighbouring row's run does not reach as far (or there is
    none), across x and across y; with a tolerance under the margin
    P grown all round by :func:`corner_inset` too (:data:`CORNER_TOLERANCE_MM`;
    ``tolerance`` 0: F all round, the rule before the corner tolerance).  Per row,
    ``plain[j][a]`` is the largest ``b`` with the run ``[a, b]`` of row j
    free with its four zones left out, or -1: its crossing strip, the margin
    beside it across x (``[X(a) - m, X(b) + w + m]``) between ``Y(j) + r``
    and ``Y(j) + w - r``, and the margin below and above it across y (``Y(j)
    - m`` to ``Y(j)``, ``Y(j) + w`` to ``Y(j) + w + m``) between ``X(a) + r``
    and ``X(b) + w - r``, each in one free interval of ``space``
    (:func:`row_bands`).  ``up[j][a]`` the same for a row with a row above
    it, which with gaps between the grown strips wider than ``2 m`` (sparse
    pitches) also holds the filler band up to the next row's grown strip over
    the run's whole extent (exact for full rectangles, whose rows share their
    runs: :func:`best_rectangle`).  ``band[j]`` (None at dense pitches): per
    cell c the largest d with that filler band, from ``Y(j) + w + m`` to
    ``Y(j + 1) - m`` across y and from ``X(c) - m`` to ``X(d) + w + m``
    across x, in one free interval; the engine's filler between a run of row
    j and one of row j + 1 spans only their common extent, so the shaped DPs
    ask ``band[j][max(a, a')] >= min(b, b')`` (section 26b, exact; the whole
    lower run before, which kept pointed fingertips bare).  ``zones[j]``:
    None when every zone of row j is free, else
    ``(bottom left, bottom right, top left, top right)`` flags per cell, the
    zone ``[X(c) - m, X(c) + r] x [Y(j) - m, Y(j) + r]`` and its mirror
    images (:func:`best_convex` asks a run's bottom left zone to be free when
    the run below starts at or left of it, its bottom right zone when that
    run ends at or right of it, its top zones likewise against the run
    above: :func:`_zone_tables`).  ``count``:
    at most this many columns (a symmetric lattice, :func:`symmetric_lattice`).
    """

    # Phase 0 puts the first crossing's grown strip on the usable edge (the outline's extreme less the edge margin).
    x0 = space.x0 + space.margin + phase[0] + margin
    y0 = space.y0 + space.margin + phase[1] + margin
    columns = int(math.floor((space.x1 - margin - width - x0) / pitch + _NOISE)) + 1
    rows = int(math.floor((space.y1 - margin - width - y0) / pitch + _NOISE)) + 1
    columns, rows = max(0, columns), max(0, rows)
    if count is not None:
        columns = min(columns, count)
    sparse = pitch - width > 2 * margin + _NOISE
    inner = corner_inset(margin, tolerance)
    reach = corner_reach(margin, width, tolerance)
    plain, up, zones = [], [], []
    fillers = [] if sparse else None
    for j in range(rows):
        y = y0 + j * pitch
        ends = None
        for low, high, grow in row_bands(y, width, margin, reach, inner):
            found = _free_ends(space.intervals(round(low, 9), round(high, 9)), x0, pitch, width, grow, columns)
            ends = found if ends is None else list(map(min, ends, found))
        if getattr(space, "border", None) is not None:
            # The user's border (surface.border): a run's every taxel square inside it.
            ends = list(map(min, ends, space.border.ends(y, x0, pitch, width, columns)))
        plain.append(ends)
        if sparse:
            band = space.intervals(round(y + width + margin, 9), round(y + pitch - margin, 9))
            filler = _free_ends(band, x0, pitch, width, margin, columns)
            fillers.append(filler)
            up.append(list(map(min, ends, filler)))
        else:
            up.append(ends)
        zones.append(_zones(space, x0, y, pitch, width, margin, reach, columns) if reach > 0 else None)
    return {"x0": x0, "y0": y0, "columns": columns, "rows": rows, "plain": plain, "up": up, "zones": zones, "band": fillers,
            "pitch": pitch, "width": width, "margin": margin, "phase": (phase[0], phase[1])}


def _free_ends(intervals: Sequence, x0: float, pitch: float, width: float, margin: float, columns: int) -> list:
    """Per cell of a row, the largest run end whose grown strip lies in the free interval of the cell's left end, or -1
    (a negative ``margin`` shrinks the run's range)."""

    ends = [-1] * columns
    for low, high in intervals:
        first = max(0, int(math.ceil((low + margin - x0) / pitch - _NOISE)))
        last = min(columns - 1, int(math.floor((high - margin - width - x0) / pitch + _NOISE)))
        if last >= first:
            ends[first:last + 1] = [last] * (last - first + 1)
    return ends


def _zones(space: Any, x0: float, y: float, pitch: float, width: float, margin: float, reach: float, columns: int) -> Any:
    """A row's corner zones: None when every one is free, else ``(bottom left, bottom right, top left, top right)`` flags
    per cell (``[X(c) - m, X(c) + r]`` or ``[X(c) + w - r, X(c) + w + m]`` across ``[Y - m, Y + r]`` or ``[Y + w - r, Y + w
    + m]`` in one free interval)."""

    found = []
    for low, high in ((y - margin, y + reach), (y + width - reach, y + width + margin)):
        left, right = [False] * columns, [False] * columns
        for start, end in space.intervals(round(low, 9), round(high, 9)):
            for flags, first, last in ((left, int(math.ceil((start + margin - x0) / pitch - _NOISE)), int(math.floor((end - reach - x0) / pitch + _NOISE))),
                                       (right, int(math.ceil((start - width + reach - x0) / pitch - _NOISE)),
                                        int(math.floor((end - width - margin - x0) / pitch + _NOISE)))):
                first, last = max(0, first), min(columns - 1, last)
                if last >= first:
                    flags[first:last + 1] = [True] * (last - first + 1)
        found += [left, right]
    if all(all(flags) for flags in found):
        return None
    return tuple(found)


def centred_phase(space: Any, pitch: float, width: float, margin: float) -> tuple:
    """The phase that centres the frame's whole lattice in the usable extent across x and across y (a symmetric face's
    field keeps the same room at both ends: the rounded plates' corners)."""

    found = []
    for low, high in ((space.x0, space.x1), (space.y0, space.y1)):
        extent = high - low - 2 * space.margin
        count = int(math.floor((extent - width - 2 * margin) / pitch + _NOISE)) + 1
        left = extent - ((count - 1) * pitch + width + 2 * margin) if count > 0 else 0.0
        found.append(round(max(0.0, left) / 2, 6))
    return (found[0], found[1])


# --------------------------------------------------------------------------
# Symmetric faces: the axis of an exit and its symmetric lattices
# --------------------------------------------------------------------------


def exit_symmetry(chart: Any, side: Mapping[str, Any], obstacles: Mapping[str, Any], tolerance: Any = None) -> dict:
    """Whether the selection is mirror-symmetric about an exit's axis: ``{"symmetric", "axis", "axis_mm", "deviation_mm"}``.

    The axis runs through the midpoint of the exit's chord (a straight side's
    ends, an arc's ends, a border edge's ends), perpendicular to it: x =
    ``axis`` in the exit's unturned base frame (:class:`surface.fit.BaseFrame`;
    ``axis_mm`` the same to the nanometre).  The outline and the holes are
    mirrored about it and sampled at every vertex and at most
    :data:`SYMMETRY_SAMPLE_MM` apart along each segment; ``deviation_mm`` is
    the largest distance of a sample from the unmirrored outline and holes
    (None beyond :data:`SYMMETRY_REPORT_MM`).  The mirror is an involution, so
    the samples of the mirror near the outline also put the outline's
    vertices near the mirror.  The face is symmetric when it is at most
    ``tolerance`` (:data:`SYMMETRY_TOLERANCE_MM`): sides split into several
    segments, a faceted arc and flattening noise stay within it.

    With the user's border (``obstacles["border"]``, :mod:`surface.border`)
    the region the taxels may take is the border's part on the surface: the
    samples of the outline and holes inside the border must mirror onto the
    outline and holes and into the border (within the tolerance), and the
    samples of the border on the surface onto the border and onto the
    surface, so that each kind of edge (the surface's, with F's margin, and
    the border's, the taxels only) mirrors onto its own kind.
    """

    tolerance = SYMMETRY_TOLERANCE_MM if tolerance is None else tolerance
    frame = fit.BaseFrame(side, 0.0)
    axis = frame.length / 2
    outline = [frame.to_base(p) for p in chart.outline()]
    holes = [[frame.to_base(p) for p in hole] for hole in obstacles["holes"]]
    surface = [(ring[k - 1], ring[k]) for ring in [outline] + holes for k in range(len(ring))]
    on_surface = fit._SegmentIndex(surface)
    polygon = [frame.to_base(p) for p in obstacles["border"]] if obstacles.get("border") is not None else []
    edges = [(polygon[k - 1], polygon[k]) for k in range(len(polygon))]
    on_border = fit._SegmentIndex(edges) if edges else None

    def inside_surface(p: Sequence[float]) -> bool:
        return point_in_polygon(p, outline) and not any(point_in_polygon(p, hole) for hole in holes)

    def off_border(p: Sequence[float]) -> float:
        return 0.0 if not polygon or point_in_polygon(p, polygon) else on_border.point_distance(p, SYMMETRY_REPORT_MM)

    def off_surface(p: Sequence[float]) -> float:
        return 0.0 if inside_surface(p) else on_surface.point_distance(p, SYMMETRY_REPORT_MM)

    worst = 0.0
    groups = [(surface, on_surface, lambda p: not polygon or point_in_polygon(p, polygon), off_border)]
    if polygon:
        groups.append((edges, on_border, inside_surface, off_surface))
    for segments, index, kept, other in groups:
        for a, b in segments:
            steps = max(1, int(math.ceil(math.hypot(b[0] - a[0], b[1] - a[1]) / SYMMETRY_SAMPLE_MM - 1e-9)))
            for k in range(steps):
                x, y = a[0] + (b[0] - a[0]) * k / steps, a[1] + (b[1] - a[1]) * k / steps
                if not kept((x, y)):
                    continue
                mirror = (2 * axis - x, y)
                found = max(index.point_distance(mirror, SYMMETRY_REPORT_MM), other(mirror))
                if found > worst:
                    worst = found
            if worst == math.inf:
                break
    return {"symmetric": worst <= tolerance, "axis": axis, "axis_mm": round(axis, 6), "deviation_mm": round(worst, 6) if worst != math.inf else None}


def symmetric_columns(space: Any, pitch: float, width: float, margin: float, axis: float, even: bool) -> Any:
    """The columns of a lattice symmetric about x = ``axis`` (frame coordinates): ``(x0, count)`` or None.

    Odd (``even`` false): a column centred on the axis; even: the axis
    midway between two columns.  As many columns on each side as the usable
    extent holds on both (phase 0's bounds: a crossing's grown strip from the
    frame's outline extremes less the edge margin), so that column ``a``'s
    mirror image is column ``count - 1 - a``.
    """

    low = space.x0 + space.margin + margin
    high = space.x1 - space.margin - margin
    first = axis - width / 2 - (pitch / 2 if even else 0.0)  # the centre column's (even: the left one's) left edge
    last = first + (pitch if even else 0.0)  # the centre column's (even: the right one's) left edge
    if first < low - _NOISE or last + width > high + _NOISE:
        return None
    side = min(int(math.floor((first - low) / pitch + _NOISE)), int(math.floor((high - width - last) / pitch + _NOISE)))
    return (first - side * pitch, 2 * side + (2 if even else 1))


def symmetric_lattice(space: Any, pitch: float, width: float, margin: float, axis: float, even: bool, phase_y: float,
                      tolerance: Any = None) -> Any:
    """:func:`lattice` with the columns of :func:`symmetric_columns` (and the row phase ``phase_y``), or None."""

    found = symmetric_columns(space, pitch, width, margin, axis, even)
    if found is None:
        return None
    x0, count = found
    grid = lattice(space, pitch, width, margin, (x0 - (space.x0 + space.margin + margin), phase_y), tolerance, count)
    grid["axis"] = axis
    grid["even"] = even
    return grid


def symmetric_runs(columns: int) -> list:
    """The runs ``(a, b)`` of a symmetric lattice's columns that are their own mirror image (``a + b = columns - 1``: about
    the middle column of an odd count, between the middle two of an even one), narrowest first."""

    centre = (columns - 1) // 2
    return [(centre - h, columns - 1 - centre + h) for h in range(centre + 1)]


def best_symmetric(plain: Sequence[Sequence[int]], up: Sequence[Sequence[int]], columns: int, row_lo: int, row_hi: int, columns_cap: int,
                   threshold: int = 0, zones: Any = None, rectangle: bool = False, band: Any = None, per_row: Any = None) -> tuple:
    """The largest row- and column-convex set of mirror-symmetric free runs within rows ``row_lo..row_hi``:
    ``(count, spans)`` (``(row, a, b)`` bottom to top) or ``(0, [])`` when none has more than ``threshold`` cells.

    Exact for that restriction, the shapes of :func:`best_convex` whose every
    run is its own mirror image: runs about one centre are always row-convex
    and share a column, and the field is column-convex when the runs' half
    widths first do not decrease, then do not increase (each column's rows
    are those whose half width reaches it).  State ``(row, half width,
    phase)``, phase 0 rising, 1 falling; a rising state's predecessors are
    the rising states no wider (a prefix maximum), a falling state's any
    state no narrower (a suffix maximum).  The predicates are
    :func:`best_convex`'s: ``plain`` frees a run, ``up`` one with a row
    above, and the corner rule of section 24: a run over a narrower one
    holds that one's top zones (its own bottom corners convex), over a
    wider one its own bottom zones, over one as wide all four.  ``columns_cap`` caps the width;
    ``rectangle``: one half width throughout (the full rectangles).  Packed
    keys (value and identity, ties to the larger identity) as in
    :func:`best_convex`.  ``band`` (:func:`lattice`, sparse pitches): the
    filler between two rows over their common extent (section 26b) in place
    of ``up``: a run over a narrower one needs that one's band, over a wider
    one its own cells' band in the row below.  ``per_row`` (a list): it gets
    per row of the window, bottom to top, the best field whose top run lies
    in that row as ``(count, spans)``, or None when none beats ``threshold``
    (:func:`tip_pass`).
    """

    runs = [run for run in symmetric_runs(columns) if run[1] - run[0] + 1 <= columns_cap]
    count = len(runs)
    height = row_hi - row_lo + 1
    if not count or height <= 0:
        return 0, []
    sizes = [b - a + 1 for a, b in runs]
    best = -1
    prev = None  # per phase, per half width: the packed key of a state of the row below that may carry, or -1
    lid = None  # per half width: the row below's top zones free (its states may lie under an aligned or wider run)
    back = []  # per row, per phase: the predecessor key of each state
    tops = []  # per row: the best key of a state there (the best field whose top run lies in that row)
    for jj in range(height):
        j = row_lo + jj
        flags = zones[j] if zones else None
        free = [plain[j][a] >= b for a, b in runs]
        carry = [up[j][a] >= b for a, b in runs] if band is None else free
        held = [flags is None or (flags[0][a] and flags[1][b]) for a, b in runs]
        if prev is None:
            rising = falling = [-1] * count
        else:
            # The corner rule (section 24): a narrower run below (h' < h) has concave top corners, so its top zones are
            # held, and this run's bottom corners are convex; a wider one (h' > h) the other way round; the same half
            # width needs all four.
            narrower = [key if ok else -1 for key, ok in zip(prev[0], lid)]
            filled = None
            if band is not None:
                # The filler over the common extent (section 26b): a narrower run below holds it over its own run, a
                # wider one over this run's cells (the same condition at the same half width).
                filled = [band[j - 1][a] >= b for a, b in runs]
                narrower = [key if ok else -1 for key, ok in zip(narrower, filled)]
            if rectangle:
                rising, falling = [key if ok else -1 for key, ok in zip(narrower, held)], [-1] * count
            else:
                rising = list(accumulate(narrower, max))
                rising = [rising[h] if held[h] else (rising[h - 1] if h else -1) for h in range(count)]
                wider = list(accumulate(reversed(list(map(max, prev[0], prev[1]))), max))
                wider.reverse()
                wider.append(-1)
                falling = [(wider[h] if lid[h] else wider[h + 1]) if held[h] else -1 for h in range(count)]
                if filled is not None:
                    falling = [key if ok else -1 for key, ok in zip(falling, filled)]
        lid = [flags is None or (flags[2][a] and flags[3][b]) for a, b in runs]
        cur = [[-1] * count, [-1] * count]
        links = [[-1] * count, [-1] * count]
        top = -1
        for h in range(count):
            if not free[h]:
                continue
            for phase, source in ((0, rising[h]), (1, falling[h])):
                if source < 0:
                    if phase:
                        continue
                    source = -1
                value = sizes[h] + (source >> _SHIFT if source >= 0 else 0)
                key = (value << _SHIFT) | ((h * height + jj) * 2 + phase)
                links[phase][h] = source
                if key > best:
                    best = key
                if key > top:
                    top = key
                if carry[h]:
                    cur[phase][h] = key
        back.append(links)
        tops.append(top)
        prev = cur

    def walk(found: int) -> list:
        spans = []
        ident = found & _MASK
        while ident >= 0:
            phase = ident % 2
            h, jj = divmod(ident // 2, height)
            a, b = runs[h]
            spans.append((row_lo + jj, a, b))
            source = back[jj][phase][h]
            ident = source & _MASK if source >= 0 else -1
        spans.reverse()
        return spans

    if per_row is not None:
        per_row.extend((top >> _SHIFT, walk(top)) if top >= 0 and top >> _SHIFT > threshold else None for top in tops)
    if best < 0 or best >> _SHIFT <= threshold:
        return 0, []
    return best >> _SHIFT, walk(best)


def search_symmetric(grid: Mapping[str, Any], rows_cap: int, columns_cap: int, threshold: int, rectangle: bool = False,
                     far: Any = None) -> tuple:
    """The best symmetric field of a symmetric lattice within one cap that beats ``threshold`` cells: ``(count, spans)``
    or ``(0, [])``: in the ``rows_cap`` rows down from the farthest row with a free symmetric run (:func:`tip_window`,
    section 23; the width cap is exact).  With ``far`` (:func:`far_row`) no row beyond it."""

    plain, up, zones = grid["plain"], grid["up"], grid.get("zones")
    rows, columns = grid["rows"], grid["columns"]
    top = rows - 1 if far is None else min(far, rows - 1)
    if not rows or not columns or top < 0:
        return (0, [])
    runs = [run for run in symmetric_runs(columns) if run[1] - run[0] + 1 <= columns_cap]
    last = next((j for j in range(top, -1, -1) if any(plain[j][a] >= b for a, b in runs)), None)
    if last is None:
        return (0, [])
    low, high = tip_window(last, rows_cap)
    count, spans = best_symmetric(plain, up, columns, low, high, columns_cap, threshold, zones, rectangle, grid.get("band"))
    return (count, spans) if count > threshold else (0, [])


def lattice_bound(runs: Sequence[Sequence[int]], rows_cap: int, columns_cap: int) -> int:
    """An upper bound of a field within the caps: the most cells of ``rows_cap`` consecutive rows' longest runs."""

    longest = []
    for ends in runs:
        most = 0
        for a, b in enumerate(ends):
            if b >= a and min(b - a + 1, columns_cap) > most:
                most = min(b - a + 1, columns_cap)
        longest.append(most)
    window = best = 0
    for j, most in enumerate(longest):
        window += most
        if j >= rows_cap:
            window -= longest[j - rows_cap]
        if window > best:
            best = window
    return best


# --------------------------------------------------------------------------
# The exact HV-convex field and the full rectangle
# --------------------------------------------------------------------------


def best_convex(plain: Sequence[Sequence[int]], up: Sequence[Sequence[int]], col_lo: int, col_hi: int, row_lo: int, row_hi: int,
                threshold: int = 0, meter: Any = None, zones: Any = None, band: Any = None, per_row: Any = None) -> tuple:
    """The largest row- and column-convex set of free runs within rows ``row_lo..row_hi`` and columns ``col_lo..col_hi``.

    Returns ``(count, spans)``, ``spans`` the ``(row, a, b)`` bottom to top,
    or ``(0, [])`` when no set has more than ``threshold`` cells (the walk
    stops once the best state that may go on, plus the longest runs of the
    rows above, cannot beat it).  Going up, a convex set's left ends do not increase and
    then do not decrease, its right ends do not decrease and then do not
    increase, and consecutive runs share a column.  State ``(row, a, b,
    phase)``, phase 0 both ends widening, 1 the left end narrowing, 2 the
    right one, 3 both; its predecessors in the row below are a range answered
    by one of four prefix tables of that row (:func:`_prefix_tables`).  A run
    is a top row when ``plain`` frees it and a predecessor when ``up`` does.
    A state's value and identity are packed in one integer key (ties go to
    the larger identity); a state's predecessor is its source key in the
    tables of its row, kept for the walk back.  ``meter`` (a one-item list)
    adds the work done, ``n * n`` per row walked (:data:`WORK_BUDGET`).

    ``zones`` (:func:`lattice`): the corner rule of section 24, every zone
    held free but at F's convex corners (:func:`_zone_tables`): between a
    run ``(a', b')`` below and ``(a, b)``, ``a' >= a`` holds the lower run's
    top left zone and ``a' <= a`` the upper run's bottom left zone, ``b' <=
    b`` the lower's top right and ``b' >= b`` the upper's bottom right; a
    field's first row keeps its bottom zones out of the check, its last row
    its top ones.  Exact (each predecessor range of a phase is split where a
    condition holds only at an aligned end), checked against brute force.

    ``band`` (:func:`lattice`, sparse pitches; None at dense ones): the
    filler between a run ``(a', b')`` of a row and ``(a, b)`` of the next
    lies on the surface over their common extent only, ``band[j][max(a,
    a')] >= min(b, b')`` (section 26b, :func:`_band_tables`); every run
    ``plain`` frees is then a predecessor and ``up`` is not read.  ``per_row``
    (a list): it gets per row of the window, bottom to top, the best field
    whose top run lies in that row as ``(count, spans)``, or None when none
    beats ``threshold`` (a state's value is the best field whose top run it
    is; :func:`tip_pass`); nothing when the walk stops early (no row has
    one).
    """

    n = col_hi - col_lo + 1
    height = row_hi - row_lo + 1
    if n <= 0 or height <= 0:
        return 0, []
    cells = n * n
    step = 4 * height
    best = -1
    prev = None
    history = []
    row_keys = []  # per row: the best key of a state there
    rows_tops = [_row_tops(plain[row_lo + jj], col_lo, col_hi) for jj in range(height)]
    # The longest runs of the rows from jj up: anywhere (rest), right of a (rest_left[jj][a]), left of b (rest_right[jj][b]).
    rest = [0] * (height + 1)
    rest_left = [[0] * n for _ in range(height + 1)]
    rest_right = [[0] * n for _ in range(height + 1)]
    for jj in range(height - 1, -1, -1):
        right_of, left_of = _longest_beside(rows_tops[jj])
        rest[jj] = rest[jj + 1] + right_of[0]
        rest_left[jj] = list(map(add, rest_left[jj + 1], right_of))
        rest_right[jj] = list(map(add, rest_right[jj + 1], left_of))
    for jj in range(height):
        j = row_lo + jj
        if meter is not None:
            meter[0] += cells
        tops = rows_tops[jj]
        carries = _row_tops(up[j], col_lo, col_hi) if band is None else tops
        if prev is None:
            sources = None
        else:
            # The corner rule (section 24): a zone at a convex corner of F is left out, every other one held free.
            below, own = zones[j - 1] if zones else None, zones[j] if zones else None
            if band is not None:
                sources = _band_tables(prev, n, None if below is None else (below[2][col_lo:col_hi + 1], below[3][col_lo:col_hi + 1]),
                                       None if own is None else (own[0][col_lo:col_hi + 1], own[1][col_lo:col_hi + 1]),
                                       _row_tops(band[j - 1], col_lo, col_hi))
            elif below is None and own is None:
                sources = _prefix_tables(prev, n)
            else:
                sources = _zone_tables(prev, n, None if below is None else (below[2][col_lo:col_hi + 1], below[3][col_lo:col_hi + 1]),
                                       None if own is None else (own[0][col_lo:col_hi + 1], own[1][col_lo:col_hi + 1]))
        history.append(sources)
        cur = [[-1] * cells for _ in range(4)] if max(carries) >= 0 else None
        # What a field that goes on above can still reach: a state's value plus the longest runs above it within the
        # ends its phase allows (left ends from a on when narrowing, right ends up to b).
        above, left_above, right_above = rest[jj + 1], rest_left[jj + 1], rest_right[jj + 1]
        reach = above
        row_best = -1
        for a in range(n):
            top = tops[a]
            if top < a:
                continue
            first = a * n + a
            length = top - a + 1
            carry = min(carries[a], top) - a + 1 if cur is not None else 0
            base = (first * height + jj) * 4
            sizes = range(1, length + 1)
            for phase in range(4):
                idents = range(base + phase, base + phase + length * step, step)
                if sources is None:
                    if phase:
                        break
                    keys = [(size << _SHIFT) | ident for size, ident in zip(sizes, idents)]
                elif phase == 0:
                    keys = [((max(source >> _SHIFT, 0) + size) << _SHIFT) | ident
                            for source, size, ident in zip(sources[0][first:first + length], sizes, idents)]
                else:
                    keys = [((((source >> _SHIFT) + size) << _SHIFT) | ident) if source >= 0 else -1
                            for source, size, ident in zip(sources[phase][first:first + length], sizes, idents)]
                largest = max(keys)
                if largest > best:
                    best = largest
                if largest > row_best:
                    row_best = largest
                if carry > 0:
                    carried_keys = keys[:carry]
                    cur[phase][first:first + carry] = carried_keys
                    if phase == 0:
                        value = (max(carried_keys) >> _SHIFT) + above
                    elif phase == 1:
                        value = (max(carried_keys) >> _SHIFT) + left_above[a]
                    elif phase == 2:
                        value = max(map(add, map(rshift, carried_keys, repeat(_SHIFT)), right_above[a:a + carry]))
                    else:
                        value = max(map(add, map(rshift, carried_keys, repeat(_SHIFT)), map(min, repeat(left_above[a]), right_above[a:a + carry])))
                    if value > reach:
                        reach = value
        prev = cur
        row_keys.append(row_best)
        if max(best >> _SHIFT, reach) <= threshold:
            return 0, []

    def walk(found: int) -> list:
        spans = []
        ident = found & _MASK
        while ident >= 0:
            phase = ident % 4
            cell, jj = divmod(ident // 4, height)
            a, b = divmod(cell, n)
            spans.append((row_lo + jj, a + col_lo, b + col_lo))
            sources = history[jj]
            source = -1 if sources is None else sources[phase][cell]
            ident = source & _MASK if source >= 0 else -1
        spans.reverse()
        return spans

    if per_row is not None:
        per_row.extend((key >> _SHIFT, walk(key)) if key >= 0 and key >> _SHIFT > threshold else None for key in row_keys)
    if best < 0 or best >> _SHIFT <= threshold:
        return 0, []
    return best >> _SHIFT, walk(best)


def _longest_beside(tops: Sequence[int]) -> tuple:
    """Per window column a, the longest free run of a row within the columns from a on, and within those up to a."""

    n = len(tops)
    right_of = [0] * (n + 1)
    for a in range(n - 1, -1, -1):
        right_of[a] = max(right_of[a + 1], tops[a] - a + 1 if tops[a] >= a else 0)
    left_of = [0] * n
    start = longest = 0
    for b in range(n):
        if tops[b] < b:
            start = b + 1
        elif b == 0 or tops[b - 1] != tops[b]:
            start = b  # a run starts here (a free cell after a blocked one, or the next free interval)
        if tops[b] >= b and b - start + 1 > longest:
            longest = b - start + 1
        left_of[b] = longest
    return right_of[:n], left_of


def _row_tops(ends: Sequence[int], col_lo: int, col_hi: int) -> list:
    """Per window column a, the largest window column b with the run free, or -1."""

    tops = []
    for a in range(col_lo, col_hi + 1):
        b = ends[a]
        tops.append(min(b, col_hi) - col_lo if b >= a else -1)
    return tops


def _masked(values: Sequence[int], n: int, left: Sequence[bool], right: Sequence[bool]) -> list:
    """A flat ``a * n + b`` table with -1 where the left flag of a or the right flag of b is off."""

    if all(left) and all(right):
        return values
    caps = [_FREE if flag else -1 for flag in right]
    none = [-1] * n
    found: list = []
    for a in range(n):
        found.extend(map(min, values[a * n:a * n + n], caps) if left[a] else none)
    return found


def _prefix_tables(prev: Sequence[Sequence[int]], n: int) -> tuple:
    """The four predecessor tables of the row above ``prev`` (flat ``a * n + b``; packed keys, -1 for none).

    ``sub``: the best phase-0 state on a sub-run of ``[a, b]``; ``left``:
    phases 0 and 1 with ``a' <= a <= b' <= b``; ``right``: phases 0 and 2
    with ``a <= a' <= b <= b'``; ``holds``: any phase on a run holding
    ``[a, b]``.  Each is a running maximum along rows or columns (C-level
    ``map`` and ``accumulate`` over integer keys).
    """

    v0, v1, v2, v3 = prev
    w01 = list(map(max, v0, v1))
    w02 = list(map(max, v0, v2))
    return _tables(v0, w01, w02, list(map(max, w01, v2, v3)), n)[:4]


def _tables(v0: Sequence[int], w01: Sequence[int], w02: Sequence[int], w_all: Sequence[int], n: int, strict_left: bool = False,
            strict_right: bool = False) -> tuple:
    """:func:`_prefix_tables` of its four inputs (``sub`` of ``v0``, ``left`` of ``w01``, ``right`` of ``w02``, ``holds`` of
    ``w_all``), and with ``strict_left`` / ``strict_right`` ``left`` over ``a' < a`` only and ``right`` over ``b' > b``
    only (else None): ``(sub, left, right, holds, left strict, right strict)``."""

    cells = n * n
    sub = [-1] * cells
    below = [-1] * n  # sub's row a + 1 (-1 left of its diagonal)
    for a in range(n - 1, -1, -1):
        row = a * n
        run = list(accumulate(map(max, v0[row + a:row + n], below[a:]), max))
        sub[row + a:row + n] = run
        below = [-1] * a + run
    left = [-1] * cells
    left_strict = [-1] * cells if strict_left else None
    column = [-1] * n  # per b', the best over the rows a' <= a
    for a in range(n):
        row = a * n
        if left_strict is not None:
            left_strict[row + a:row + n] = accumulate(column[a:], max)
        column = list(map(max, column, w01[row:row + n]))
        left[row + a:row + n] = accumulate(column[a:], max)
    right = [-1] * cells
    right_strict = [-1] * cells if strict_right else None
    line = [-1] * n  # per a', the best over the right ends b' >= b
    for b in range(n - 1, -1, -1):
        if right_strict is not None:
            values = list(accumulate(reversed(line[:b + 1]), max))
            values.reverse()
            right_strict[b:b * n + b + 1:n] = values
        line = list(map(max, line, w02[b::n]))
        values = list(accumulate(reversed(line[:b + 1]), max))
        values.reverse()
        right[b:b * n + b + 1:n] = values
    holds = [-1] * cells
    above = [-1] * n  # holds' row a - 1
    for a in range(n):
        row = a * n
        values = list(accumulate(reversed(list(map(max, w_all[row:row + n], above))), max))
        values.reverse()
        holds[row:row + n] = values
        above = values
    return sub, left, right, holds, left_strict, right_strict


def _zone_tables(prev: Sequence[Sequence[int]], n: int, below: Any, own: Any) -> tuple:
    """The four predecessor tables of a row under the corner rule (P5-diagonal-bus.md section 24): ``below`` the row
    below's top zones ``(left, right)`` (window flags, None: all free), ``own`` this row's bottom zones.

    A corner zone is left out of the check (its F may leave the surface by
    the corner tolerance) where F's corner is convex: a run's bottom left
    zone where no row lies below it or the row below starts right of it
    (``a' > a``), its bottom right zone where that row ends left of it
    (``b' < b``), its top zones likewise against the row above.  Where the
    neighbouring run reaches as far or farther (an aligned or a concave end)
    the zone must be free.  Between a run ``(a', b')`` below and ``(a, b)``:
    ``a' >= a`` needs the lower run's top left zone, ``a' <= a`` the upper
    run's bottom left zone, ``b' <= b`` the lower's top right, ``b' >= b``
    the upper's bottom right.  Per phase (:func:`_prefix_tables`) a
    condition every predecessor of the range meets masks the row below's
    states before the running maxima (phase 0: both top zones; 1: the top
    right; 2: the top left), the state's own zones a phase always needs
    leave out the state (1: bottom left; 2: bottom right; 3: both), and a
    condition only the aligned end meets (``a' = a`` or ``b' = b``) moves
    the range's end by one where its zone is blocked (the strict tables).
    Exact: every predecessor is taken under exactly its own conditions.
    """

    full = [True] * n
    tl, tr = below if below is not None else (full, full)
    bl, br = own if own is not None else (full, full)
    v0, v1, v2, v3 = prev
    cells = n * n
    sub, left, right, holds, left_strict, right_strict = _tables(
        _masked(v0, n, tl, tr), _masked(list(map(max, v0, v1)), n, full, tr), _masked(list(map(max, v0, v2)), n, tl, full),
        list(map(max, v0, v1, v2, v3)), n, not all(tl), not all(tr))
    blocked_br = [b for b in range(n) if not br[b]]
    blocked_tr = [b for b in range(n) if not tr[b]]
    t0, t1, t2, t3 = [-1] * cells, [-1] * cells, [-1] * cells, [-1] * cells
    for a in range(n):
        row = a * n
        # Phase 0 (a' >= a, b' <= b): an aligned end needs this run's bottom zone too, else the range stops short of it.
        x = a if bl[a] else a + 1
        if x < n:
            t0[row + a:row + n] = sub[x * n + a:x * n + n]
            t2[row + a:row + n] = right[x * n + a:x * n + n]
            for b in blocked_br:
                if b >= a:
                    t0[row + b] = sub[x * n + b - 1] if b - 1 >= x else -1
            # Phase 2 (a' >= a, b' >= b): this run's bottom right zone always; the lower's top right only at b' = b.
            for b in blocked_tr:
                if b >= a:
                    t2[row + b] = right_strict[x * n + b]
            for b in blocked_br:
                if b >= a:
                    t2[row + b] = -1
        if not bl[a]:
            continue
        # Phase 1 (a' <= a, b' <= b): this run's bottom left zone always; the lower's top left only at a' = a.
        source = left if tl[a] else left_strict
        t1[row + a:row + n] = source[row + a:row + n]
        for b in blocked_br:
            if b >= a:
                t1[row + b] = source[row + b - 1] if b - 1 >= a else -1
        # Phase 3 (a' <= a, b' >= b): both bottom zones always; the lower's top zones only where aligned.
        x = a if tl[a] else a - 1
        if x >= 0:
            t3[row + a:row + n] = holds[x * n + a:x * n + n]
            for b in blocked_tr:
                if b >= a:
                    t3[row + b] = holds[x * n + b + 1] if b + 1 < n else -1
            for b in blocked_br:
                if b >= a:
                    t3[row + b] = -1
    return t0, t1, t2, t3


def _band_start(band: Sequence[int]) -> list:
    """Per window cell b, the first cell c with ``band[c'] >= b`` for every c' in ``[c, b]`` (the start of b's free run of
    the filler band), or ``b + 1`` when ``band[b] < b``."""

    found = []
    for b, end in enumerate(band):
        c = b + 1
        if end >= b:
            c = b
            while c > 0 and band[c - 1] >= b:
                c -= 1
        found.append(c)
    return found


def _band_tables(prev: Sequence[Sequence[int]], n: int, below: Any, own: Any, band: Sequence[int]) -> tuple:
    """:func:`_zone_tables` at a sparse pitch (P5-diagonal-bus.md section 26b): the filler between a run ``(a', b')`` below
    and ``(a, b)`` lies on the surface over their common extent, ``band[max(a, a')] >= min(b, b')`` (``band`` the lower
    row's :func:`lattice` band in window cells).

    Every run the row below frees is in ``prev`` (not only those that hold
    the filler over their whole run).  Per phase the condition bounds one end
    of the predecessor range, and the tighter of it and the zone rule's bound
    wins (the strict tables bound the other end, as in
    :func:`_zone_tables`): phase 0 (``a <= a'``, ``b' <= b``, the lower run
    the common extent) masks the row below's states by their own band before
    ``sub``; phase 1 (``a' <= a <= b' <= b``, extent ``[a, b']``) reads
    ``left`` at ``(a, min(b, band[a]))``; phase 2 (``a <= a' <= b <= b'``,
    extent ``[a', b]``) reads ``right`` at ``(max(a, start[b]), b)``, start
    the first cell of b's free run of the band (:func:`_band_start`); phase 3
    (the upper run the extent) has a predecessor only where ``band[a] >= b``.
    """

    full = [True] * n
    tl, tr = below if below is not None else (full, full)
    bl, br = own if own is not None else (full, full)
    v0, v1, v2, v3 = prev
    cells = n * n
    filled = list(v0)
    for a in range(n):
        end = band[a]
        if end < n - 1:
            first = max(a, end + 1)
            filled[a * n + first:a * n + n] = [-1] * (n - first)
    sub, left, right, holds, left_strict, right_strict = _tables(
        _masked(filled, n, tl, tr), _masked(list(map(max, v0, v1)), n, full, tr), _masked(list(map(max, v0, v2)), n, tl, full),
        list(map(max, v0, v1, v2, v3)), n, not all(tl), not all(tr))
    left_strict = left_strict if left_strict is not None else left
    right_strict = right_strict if right_strict is not None else right
    start = _band_start(band)
    # Phase 2's value where the band's run starts right of the range's own start: the same for every a left of it.
    beyond = [((right if tr[b] else right_strict)[start[b] * n + b] if br[b] and band[b] >= b else -1) for b in range(n)]
    t0, t1, t2, t3 = [-1] * cells, [-1] * cells, [-1] * cells, [-1] * cells
    for a in range(n):
        row = a * n
        # Phase 0 (a' >= a, b' <= b): the lower run's own band (masked above); an aligned end needs this run's zone too.
        x = a + (0 if bl[a] else 1)
        if x < n:
            t0[row + a:row + n] = sub[x * n + a:x * n + n]
            for b in range(a, n):
                if not br[b]:
                    t0[row + b] = sub[x * n + b - 1] if b - 1 >= x else -1
        # Phase 2 (a' >= a, b' >= b): b' = b needs the lower's top right zone, every b' this run's bottom right; a' from
        # the later of x and the band's start.
        for b in range(a, n):
            if not br[b] or band[b] < b:
                continue
            t2[row + b] = beyond[b] if start[b] > x else ((right if tr[b] else right_strict)[x * n + b] if x <= b else -1)
        if not bl[a]:
            continue
        # Phase 1 (a' <= a, b' <= b): this run's bottom left zone always; the lower's top left only at a' = a; b' at most
        # band[a] (the band from a) and b - 1 where this run's bottom right zone is blocked.
        limit = band[a]
        if limit >= a:
            source = left if tl[a] else left_strict
            for b in range(a, n):
                end = b if br[b] else b - 1
                end = min(end, limit)
                t1[row + b] = source[row + end] if end >= a else -1
        # Phase 3 (a' <= a, b' >= b): both bottom zones always; the lower's top zones only where aligned; the band over
        # this run.
        x = a if tl[a] else a - 1
        if x >= 0:
            for b in range(a, min(limit, n - 1) + 1):
                if not br[b]:
                    continue
                y = b if tr[b] else b + 1
                t3[row + b] = holds[x * n + y] if y < n else -1
    return t0, t1, t2, t3


def best_rectangle(plain: Sequence[Sequence[int]], up: Sequence[Sequence[int]], rows_cap: int, columns_cap: int, threshold: int = 0,
                   zones: Any = None) -> tuple:
    """The full rectangle with the most cells within the caps: ``(count, rows, columns, row, a)`` (bottom row, left cell),
    or zeros when none has more than ``threshold`` cells.

    Per bottom row and height, a cell's reach is the least run end over the
    rows (the top row's ``plain``, the others' ``up``); the widest run
    (capped) times the height is the rectangle there.  A bottom row stops
    growing once its widest run times the most rows it can still take
    cannot beat the best (the widest run only narrows as it grows).  With
    ``zones`` (:func:`lattice`) every row but the bottom one holds its bottom
    corner zones free, every row but the top one its top ones; a run's end is
    capped by ``columns_cap`` before its right zones are read (section 26a).
    """

    best = (threshold, 0, 0, 0, 0)
    count = len(plain)
    width = len(plain[0]) if count else 0
    offsets = [a - 1 for a in range(width)]
    for j0 in range(count if width else 0):
        tallest = min(rows_cap, count - j0)
        reach = [width] * width  # the least end over the rows below the top one (their up runs)
        left_ok = right_ok = None  # the zones free on the rows so far that need them (None: all)
        last = None  # per cell, the last cell at or left of it whose right zones are free, or -1
        for j1 in range(j0, j0 + tallest):
            height = j1 - j0 + 1
            if j1 > j0 and zones and zones[j1] is not None:
                left_ok, right_ok = _and(left_ok, zones[j1][0]), _and(right_ok, zones[j1][1])
                last = _last_true(right_ok)
            if last is None:
                spans = list(map(sub, map(min, plain[j1], reach), offsets))
            else:
                # The column cap first, then the right zones of the capped end (section 26a: the uncapped end's flags let a
                # capped rectangle end on a blocked zone).
                spans = [last[min(end, a + columns_cap - 1)] - a + 1 if end >= a and left_ok[a] else 0
                         for a, end in enumerate(map(min, plain[j1], reach))]
            widest = max(spans)
            if widest <= 0 or min(widest, columns_cap) * tallest <= best[0]:
                break
            if min(widest, columns_cap) * height > best[0]:
                a = spans.index(widest)
                best = (min(widest, columns_cap) * height, height, min(widest, columns_cap), j0, a)
            reach = list(map(min, reach, up[j1]))
            if zones and zones[j1] is not None:
                left_ok, right_ok = _and(left_ok, zones[j1][2]), _and(right_ok, zones[j1][3])
                last = _last_true(right_ok)
    return best if best[1] else (0, 0, 0, 0, 0)


def _and(held: Any, flags: Sequence[bool]) -> list:
    return list(flags) if held is None else [x and y for x, y in zip(held, flags)]


def _last_true(flags: Sequence[bool]) -> list:
    """Per index, the last index at or before it whose flag is on, or -1."""

    found, held = [], -1
    for index, flag in enumerate(flags):
        if flag:
            held = index
        found.append(held)
    return found


def windows(count: int, cap: int) -> list:
    """The ``(low, high)`` index windows of at most ``cap`` of ``count`` (one when it fits)."""

    if count <= cap:
        return [(0, count - 1)] if count else []
    return [(start, start + cap - 1) for start in range(count - cap + 1)]


def tip_rows(plain: Sequence[Sequence[int]], cap: int, far: Any = None) -> Any:
    """The rows ``(low, high)`` a field of the lattice takes under a row cap: the ``cap`` rows down from its row farthest
    from the exit that frees a cell (row 0 is the exit's), none beyond ``far`` (:func:`tip_window`, section 23); None
    when no such row frees one."""

    top = len(plain) - 1 if far is None else min(far, len(plain) - 1)
    for j in range(top, -1, -1):
        if any(end >= a for a, end in enumerate(plain[j])):
            return tip_window(j, cap)
    return None


def tip_window(last: int, cap: int) -> tuple:
    """The rows of a capped field: the ``cap`` rows down from ``last``, the face's free row farthest from the exit (the
    fingertip), toward the exit (the user's rule, P5-diagonal-bus.md section 23: the taxels stack at the end opposite the
    edge the tails leave by, not wherever the face holds most; the tails run down the face to the exit)."""

    return (max(0, last - cap + 1), last)


def far_row(grid: Mapping[str, Any], reach: float) -> int:
    """The last row of the lattice whose taxels lie within ``reach`` (mm from the exit in its frame) of the exit: the
    farthest a field may take when its tails would pass the maximum otherwise (section 23); -1 when none does."""

    return int(math.floor((reach - grid["y0"]) / grid["pitch"] + 1e-9))


def row_intervals(ends: Sequence[int]) -> list:
    """The free runs ``(first, last)`` of a row (its maximal runs, left to right)."""

    runs = []
    for a, end in enumerate(ends):
        if end >= a and (not runs or runs[-1][1] != end):
            runs.append((a, end))
    return runs


def _longest(runs: Sequence, low: int, high: int) -> int:
    """The longest free run of a row within the columns ``low..high``."""

    most = 0
    for first, last in runs:
        if first > high:
            break
        size = min(last, high) - max(first, low) + 1
        if size > most:
            most = size
    return most


def window_bounds(runs: Sequence, rows: int, columns: int, rows_cap: int, columns_cap: int, far: Any = None) -> list:
    """``(bound, row_lo, col_lo, row_hi, col_hi)`` per window: the sum of its rows' longest free runs within its columns.
    The columns slide; the rows are :func:`tip_window`'s: ``rows_cap`` rows down from the free row farthest from the
    exit (none beyond ``far``)."""

    last = max((j for j in range(rows) if runs[j] and (far is None or j <= far)), default=None)
    if last is None:
        return []
    row_windows = [tip_window(last, rows_cap)]
    boxes = []
    for col_lo, col_hi in windows(columns, columns_cap):
        prefix = [0]
        for j in range(rows):
            prefix.append(prefix[-1] + _longest(runs[j], col_lo, col_hi))
        for row_lo, row_hi in row_windows:
            boxes.append((prefix[row_hi + 1] - prefix[row_lo], row_lo, col_lo, row_hi, col_hi))
    return boxes


def quadrant_bound(runs: Sequence, row_lo: int, col_lo: int, row_hi: int, col_hi: int) -> Any:
    """A tighter bound of a window that holds blocked cells with free cells on their four sides, or None.

    A row- and column-convex set cannot surround a blocked cell c: its runs
    in c's row and column each lie on one side of c, and then it misses one
    of the four closed quadrants at c (the rows on c's side of the row run,
    the columns on c's side of the column run, cannot reach past it).  Each
    such cell bounds the window by its rows' longest runs less one quadrant
    (the best of the four); the bound is the least over the middle cells of
    the rows' gaps.
    """

    whole = [_longest(runs[k], col_lo, col_hi) for k in range(row_lo, row_hi + 1)]
    total = 0
    for value in whole:
        total += value
    found = None
    for j in range(row_lo + 1, row_hi):
        clipped = [(max(first, col_lo), min(last, col_hi)) for first, last in runs[j] if last >= col_lo and first <= col_hi]
        for (_, last), (first, _) in zip(clipped, clipped[1:]):
            g = (last + first + 1) // 2
            below = any(any(a <= g <= b for a, b in runs[k]) for k in range(row_lo, j))
            above = any(any(a <= g <= b for a, b in runs[k]) for k in range(j + 1, row_hi + 1))
            if not (below and above):
                continue
            split = j - row_lo
            sides = []
            for low, high in ((col_lo, g - 1), (g + 1, col_hi)):
                upper = lower = 0
                for k in range(len(whole)):
                    lost = whole[k] - _longest(runs[row_lo + k], low, high)
                    if k >= split:
                        upper += lost
                    if k <= split:
                        lower += lost
                sides += [total - upper, total - lower]
            if found is None or max(sides) < found:
                found = max(sides)
    return found


def search_shaped(grid: Mapping[str, Any], rows_cap: int, columns_cap: int, threshold: int, meter: Any = None,
                  budget: Any = None, far: Any = None) -> tuple:
    """The best shaped field of a lattice within one cap that beats ``threshold`` cells: ``(count, spans)`` or ``(0, [])``.

    The field takes the ``rows_cap`` rows down from the lattice's free row
    farthest from the exit (:func:`tip_rows`, the fingertip: section 23),
    none beyond ``far`` (:func:`far_row`).  A lattice wider than the column
    cap is first searched whole across, when that costs at most
    :data:`WHOLE_LATTICE_COST` windows: a window's field is a field of the
    lattice, so nothing beats the threshold when the whole one does not, and
    the whole one's best is every window's best when it fits the cap.
    Otherwise the column windows, best bound first (:func:`window_bounds`,
    then :func:`quadrant_bound`), each searched by :func:`best_convex` while
    its bound can beat the best so far and the work ``meter`` is under
    ``budget``.
    """

    plain, up = grid["plain"], grid["up"]
    rows, columns = grid["rows"], grid["columns"]
    window = tip_rows(plain, rows_cap, far) if rows and columns else None
    if window is None:
        return (0, [])
    low, high = window
    if columns > columns_cap:
        height = high - low + 1
        if height * columns * columns <= WHOLE_LATTICE_COST * height * columns_cap ** 2 and 4 * rows * columns * columns <= _MASK:
            count, spans = best_convex(plain, up, 0, columns - 1, low, high, threshold, meter, grid.get("zones"), grid.get("band"))
            if not count:
                return (0, [])
            if max(b for _, _, b in spans) - min(a for _, a, _ in spans) < columns_cap:
                return (count, spans)
    runs = [row_intervals(ends) for ends in plain]
    found = (0, [])
    boxes = window_bounds(runs, rows, columns, rows_cap, columns_cap, far)
    boxes.sort(key=lambda box: (-box[0], box[1:]))
    for bound, row_lo, col_lo, row_hi, col_hi in boxes:
        floor = max(threshold, found[0])
        if bound <= floor or (budget is not None and meter[0] >= budget):
            break
        tighter = quadrant_bound(runs, row_lo, col_lo, row_hi, col_hi)
        if tighter is not None and tighter <= floor:
            continue
        count, spans = best_convex(plain, up, col_lo, col_hi, row_lo, row_hi, floor, meter, grid.get("zones"), grid.get("band"))
        if count > found[0]:
            found = (count, spans)
    return found if found[0] > threshold else (0, [])


# --------------------------------------------------------------------------
# The search
# --------------------------------------------------------------------------


def caps(options: Mapping[str, Any]) -> tuple:
    """``(shaped caps, rectangle caps)``: the ``(rows, columns)`` caps of the shaped fields and of the full rectangles.

    The same caps for both (the user's decision, P5-diagonal-bus.md section
    21: coverage first; shaped fields were capped at 32 x 32 before, so on a
    long face a thin rectangle beat the field following it):
    ``max_rows`` x ``max_columns``, a named reader's lines, either way round
    (:func:`surface.reader.walk_caps`), ``auto`` the largest reader's
    (:func:`surface.reader.field_caps`).
    """

    found = reader_module.field_caps(options["reader"], options["max_rows"], options["max_columns"])
    return list(found), list(found)


def ladder(options: Mapping[str, Any]) -> list:
    """The pitches searched: ``fixed_pitch`` its pitch, ``max_taxels`` the smallest and the next three 0.01 mm steps,
    ``max_area`` the smallest x 1.15^k up to 10 mm (:func:`surface.fit.max_area_pitches`)."""

    if options["objective"] == "fixed_pitch":
        return [round(options["pitch_mm"], 3)]
    low = round(options["min_pitch_mm"], 3)
    if options["objective"] == "max_taxels":
        return [round(low + k * fit.PITCH_STEP_MM, 3) for k in range(4) if low + k * fit.PITCH_STEP_MM <= fit.MAX_PITCH_MM + 1e-9]
    return fit.max_area_pitches(low)


class _Search:
    """The candidates of one fit and the values that prune its lattices."""

    def __init__(self, options: Mapping[str, Any], profile: Mapping[str, Any], auto_exit: bool) -> None:
        self.options = options
        self.margin = float(profile["routing"]["active_edge_clearance_mm"])
        self.shaped_caps, self.rectangle_caps = caps(options)
        self.area = options["objective"] == "max_area"
        self.auto_exit = auto_exit
        self.found: dict = {}  # (turned, rows, columns, full) -> the best candidate of that readout, unturned and turned
        self.unturned = 0  # the best value of an unturned field
        self.searched = 0
        self.meter = [0]  # the DP work done (:data:`WORK_BUDGET`)
        self.frame_best: dict = {}  # (frame order, angle, pitch) -> the best candidate found there
        # How far from the exit (mm, its frame) a field's taxels may lie: set by fit_chart_field when a capped field at the
        # far end would need tails past the maximum (section 23); None: the face's far end.
        self.reach = options.get("tip_reach_mm")
        self.capped = False  # whether a lattice searched is longer or wider than a cap (the cap binds there)

    def threshold(self, turned: bool, pitch: float) -> int:
        """What a field must beat to be kept.

        The second-best readout's value (one alternative readout), but never
        less than :data:`ALTERNATIVE_SHARE` of the best (alternatives far
        below the best are not searched for); with several exits at most the
        best less the narrow tip's tolerance (those fields rank by their
        tip); a turned field at least :data:`TURN_GAIN` over the best
        unturned one.  An unturned lattice is pruned by the unturned fields
        only: a turned field is proposed only with :data:`TURN_GAIN` over the
        best unturned one, so the unturned search must find that one, and
        its alternatives, whatever the turned frames hold.
        """

        readouts: dict = {}
        for (kind, rows, columns, full), candidate in self.found.items():
            if kind and not turned:
                continue
            if candidate["value"] > readouts.get((rows, columns, full), -1):
                readouts[(rows, columns, full)] = candidate["value"]
        values = sorted(readouts.values(), reverse=True)
        best = values[0] if values else 0
        floor = values[SPARE_READOUTS] if len(values) > SPARE_READOUTS else 0
        if self.auto_exit:
            floor = min(floor, best - tip_slack(pitch, self.area, best) - 1)
        floor = max(floor, best * ALTERNATIVE_SHARE[0] // ALTERNATIVE_SHARE[1])
        if turned and self.unturned:
            floor = max(floor, -(-self.unturned * TURN_GAIN[0] // TURN_GAIN[1]) - 1)
        return floor

    def add(self, candidate: dict) -> None:
        key = (candidate["angle_deg"] != 0.0, candidate["rows"], candidate["columns"], candidate["full"])
        held = self.found.get(key)
        if held is None or candidate["rank"] < held["rank"]:
            self.found[key] = candidate
        if candidate["angle_deg"] == 0.0 and candidate["value"] > self.unturned:
            self.unturned = candidate["value"]


def tip_slack(pitch: float, area: bool, most: int = 0) -> int:
    """The narrow tip's tolerance in the ranked value: :data:`NARROW_TIP_TAXELS` taxels (or as many cells' area), or
    :data:`NARROW_TIP_SHARE` of the most (``most``) when that is more."""

    return max(NARROW_TIP_TAXELS * (int(round(pitch * pitch * 1e6)) if area else 1), most * NARROW_TIP_SHARE[0] // NARROW_TIP_SHARE[1])


def _value(candidate_cells: Sequence, pitch: float, width: float, area: bool) -> int:
    """What a field ranks by: its taxels, or with ``max_area`` the area of P in square micrometres (an integer)."""

    if area:
        return int(round(fill.field_area(candidate_cells, pitch, width) * 1e6))
    count = 0
    for low, high in candidate_cells:
        count += high - low + 1
    return count


def _lattice_bound_value(bound_cells: int, pitch: float, width: float, area: bool) -> int:
    """An upper bound of :func:`_value` from an upper bound of the cells (P's area at most a cell's pitch square each)."""

    return int(math.ceil(bound_cells * pitch * pitch * 1e6)) if area else bound_cells


def _make(search: _Search, grid: Mapping[str, Any], spans: Sequence, frame: Mapping[str, Any], kind: str) -> dict:
    """A candidate from a lattice's runs ``(row, a, b)`` bottom to top."""

    pitch, width, margin = grid["pitch"], grid["width"], grid["margin"]
    amin = min(a for _, a, _ in spans)
    columns = max(b for _, _, b in spans) - amin + 1
    cells = tuple((a - amin, b - amin) for _, a, b in reversed(spans))  # ROW_01 (the top) first, from the left
    taxels = 0
    for low, high in cells:
        taxels += high - low + 1
    rows = len(cells)
    full = taxels == rows * columns
    value = _value(cells, pitch, width, search.area)
    tip = round((cells[0][1] - cells[0][0]) * pitch + width + 2 * margin, 6)
    origin = (grid["x0"] + amin * pitch, grid["y0"] + spans[0][0] * pitch)
    angle = frame["angle"]
    # How many of the corner zones at F's convex corners leave the usable surface (the corner tolerance used; 0 ranks
    # first; section 24: every convex corner, not only the field's four).
    zones = grid.get("zones") or []
    corners = 0
    for (row, a, b), exempt in zip(spans, exempt_zones(spans)):
        flags = zones[row] if row < len(zones) else None
        if flags is not None:
            for corner, end in enumerate((a, b, a, b)):
                corners += exempt[corner] and not flags[corner][end]
    candidate = {
        "rows": rows, "columns": columns, "cells": cells, "taxels": taxels, "full": full, "value": value, "tip_mm": tip,
        "pitch": pitch, "width": width, "margin": margin, "field_origin": origin, "angle_deg": angle, "side": frame["side"],
        "frame": frame["frame"], "region": frame["space"], "order": frame["order"], "phase": grid["phase"], "kind": kind,
        "spans": [tuple(span) for span in spans], "lattice": {key: grid[key] for key in ("x0", "y0", "pitch", "width", "margin")},
        "peels": 0, "corners": corners, "symmetry": frame.get("symmetry"), "reach_limit": getattr(search, "reach", None),
    }
    candidate["symmetric"] = mirror_symmetric(candidate)
    candidate["rank"] = field_rank(candidate)
    return candidate


def mirror_symmetric(candidate: Mapping[str, Any]) -> bool:
    """Whether a field is its own mirror image about its exit's axis (:func:`exit_symmetry`): an unturned field on an
    exit whose face is symmetric, centred on the axis, every row's run its own mirror image (first + last = columns -
    1 from the field's left column)."""

    info = candidate.get("symmetry")
    if not info or not info["symmetric"] or candidate["angle_deg"] != 0.0:
        return False
    columns = candidate["columns"]
    if any(low + high != columns - 1 for low, high in candidate["cells"]):
        return False
    centre = candidate["field_origin"][0] + ((columns - 1) * candidate["pitch"] + candidate["width"]) / 2
    return abs(centre - info["axis"]) <= 1e-6


def field_rank(candidate: Mapping[str, Any]) -> tuple:
    """A field's rank (smaller first): ``(-value, -pitch, |turn|, masked, positions, corners off the surface, asymmetric,
    exit order, phase, origin)``: of two fields alike, the one whose F needs the corner tolerance at fewer corners first,
    then a symmetric one (:func:`mirror_symmetric`).

    The turn threshold and the narrow tip are applied to the ranked pool
    (:func:`ordered`), not here.
    """

    origin = candidate["field_origin"]
    return (
        -candidate["value"],
        -candidate["pitch"],
        abs(candidate["angle_deg"]),
        candidate["angle_deg"],
        0 if candidate["full"] else 1,
        candidate["rows"] * candidate["columns"],
        candidate.get("corners", 0),
        0 if candidate.get("symmetric") else 1,
        candidate["order"],
        candidate["phase"],
        round(-origin[1], 6),
        round(origin[0], 6),
    )


def ordered(candidates: Sequence[Mapping[str, Any]], auto_exit: bool) -> list:
    """The fit's fields in proposal order: by rank, a turned field only with :data:`TURN_GAIN` over the best unturned one;
    with several exits the fields within :data:`NARROW_TIP_TAXELS` (or :data:`NARROW_TIP_SHARE`) of the most first, their exits by the tip of each
    exit's best such field (the narrowest first) and each exit's fields by rank (the narrow tip chooses the exit); then
    symmetric faces' symmetric fields first within :data:`SYMMETRY_GAIN` (:func:`symmetric_first`)."""

    ranked = sorted(candidates, key=lambda candidate: candidate["rank"])
    unturned = max((candidate["value"] for candidate in ranked if candidate["angle_deg"] == 0.0), default=0)
    kept = [
        candidate for candidate in ranked
        if candidate["angle_deg"] == 0.0 or candidate["value"] * TURN_GAIN[1] >= unturned * TURN_GAIN[0]
    ]
    return symmetric_first(by_tip(kept, auto_exit), auto_exit)


def by_tip(kept: Sequence[Mapping[str, Any]], auto_exit: bool) -> list:
    """Fields in rank order with the narrow tip applied (several exits): the fields within the narrow tip's tolerance of
    the most first, their exits by the tip of each exit's best such field, each exit's fields by rank; the rest by rank."""

    kept = list(kept)
    if not auto_exit or not kept:
        return kept
    most = max(candidate["value"] for candidate in kept)
    near = [candidate for candidate in kept if candidate["value"] >= most - tip_slack(candidate["pitch"], candidate["value"] != candidate["taxels"], most)]
    rest = [candidate for candidate in kept if candidate["value"] < most - tip_slack(candidate["pitch"], candidate["value"] != candidate["taxels"], most)]
    lead: dict = {}  # exit order -> (tip, rank) of its best field among the near ones
    for candidate in near:
        lead.setdefault(candidate["order"], (candidate["tip_mm"], candidate["rank"]))
    near.sort(key=lambda candidate: (lead[candidate["order"]], candidate["rank"]))
    return near + rest


def symmetric_leads(symmetric: int, other: int) -> bool:
    """Whether a symmetric field's value holds within :data:`SYMMETRY_GAIN` of another's: under 1.2 times it (the other
    ranks first only with at least 20 % more, exactly 20 % included)."""

    return symmetric * SYMMETRY_GAIN[0] > other * SYMMETRY_GAIN[1]


def symmetric_first(queue: Sequence[Mapping[str, Any]], auto_exit: bool) -> list:
    """The proposal order with symmetric fields on symmetric faces first (the user's request, P5-diagonal-bus.md section 22:
    "if the geometric face is symmetric, make the sensor symmetric too, as far as possible"; the user's decisions of
    2026-10-27, section 26.17: faces symmetric like the WidowX's take a centred sensor too, and section 26.19: unless a
    field that breaks the symmetry holds at least 20 % more).

    Each exit's best symmetric field (:func:`mirror_symmetric`, by rank)
    whose value holds within :data:`SYMMETRY_GAIN` of the most of all the
    fields (:func:`symmetric_leads`) goes first; of several such exits, the
    narrow tip chooses (:func:`by_tip`: within its tolerance of the best of
    them, the narrowest tip first).  Then the other fields in ``queue``'s
    order, each exit's best symmetric field moved before that exit's other
    fields when it holds within :data:`SYMMETRY_GAIN` of their best.  A field
    that breaks the symmetry (an asymmetric field on any exit, a turned one)
    thus ranks first only with at least 1.2 times the best symmetric field's
    value (with ``max_area`` area), and stays a later proposal otherwise; a
    symmetric field so passed stays an alternative (the proposals keep one
    per readout and kind).  ``queue`` holds the search's fields, before the
    tip step (:func:`tip_first`), so the tip never changes this order.
    """

    queue = list(queue)
    if not queue:
        return queue
    most = max(candidate["value"] for candidate in queue)
    best: dict = {}  # exit order -> its best symmetric field
    top: dict = {}  # exit order -> the most of its fields
    for candidate in sorted(queue, key=lambda candidate: candidate["rank"]):
        top.setdefault(candidate["order"], candidate["value"])
        if candidate.get("symmetric"):
            best.setdefault(candidate["order"], candidate)
    if not best:
        return queue
    lead = by_tip(sorted((candidate for _, candidate in sorted(best.items()) if symmetric_leads(candidate["value"], most)),
                         key=lambda candidate: candidate["rank"]), auto_exit)
    placed = {id(candidate) for candidate in lead}
    found = list(lead)
    for candidate in queue:
        first = best.get(candidate["order"])
        if first is not None and id(first) not in placed and symmetric_leads(first["value"], top[candidate["order"]]):
            found.append(first)
            placed.add(id(first))
        if id(candidate) not in placed:
            found.append(candidate)
            placed.add(id(candidate))
    return found


def uncapped(options: Mapping[str, Any]) -> dict:
    """The options without any readout cap (:data:`UNCAPPED` rows and columns, reader ``none``): the fit that chooses
    the exit when a cap binds (its fields are compared, never built)."""

    return dict(options, max_rows=UNCAPPED, max_columns=UNCAPPED, reader="none")


def keep_exits(queue: Sequence[Mapping[str, Any]], reference: Sequence[Mapping[str, Any]]) -> list:
    """The capped fields in the order of their exits in ``reference`` (the fit without the caps), each exit's fields in
    ``queue``'s order; exits the reference has no field on last (the user's rule, P5-diagonal-bus.md section 23: a
    smaller readout keeps the exit the face gets, its taxels stacking from that edge, and never moves the tails to
    another side because the cap holds more taxels there)."""

    exits: dict = {}
    for candidate in reference:
        exits.setdefault(candidate["order"], len(exits))
    return sorted(queue, key=lambda candidate: exits.get(candidate["order"], len(exits)))


def own_exits(reference: Sequence[Mapping[str, Any]]) -> list:
    """The exits ``reference`` (the fit without the caps) has fields on, in its order: each is searched on its own with
    the caps (section 23; :func:`fit_chart_field`, when the proposals reach its fields), so that no exit's capped fields
    are pruned by another's."""

    exits: list = []
    for candidate in reference:
        if candidate["order"] not in exits:
            exits.append(candidate["order"])
    return exits


# --------------------------------------------------------------------------
# Tip first (P5-diagonal-bus.md section 26)
# --------------------------------------------------------------------------


def tip_on(options: Mapping[str, Any]) -> bool:
    """Whether the tip step runs (never with ``max_area``; with ``tip_first: false`` its zero-cost ties alone,
    :func:`tip_leads`)."""

    return options.get("objective") != "max_area"


def tip_leads(options: Mapping[str, Any]) -> bool:
    """Whether a tip-first field may give up taxels to lead its group (the option ``tip_first``, true by default: the
    share :data:`TIP_SHARE`); false keeps coverage first, a group's lead giving its slot only to its zero-cost tie
    (:func:`tip_choice`)."""

    return bool(options.get("tip_first", True)) and tip_on(options)


def tip_reach(candidate: Mapping[str, Any]) -> int:
    """How far an unturned field reaches from its exit (integer nanometres, its exit's base frame: y along the inward
    normal, the exit chord on y = 0): its top row's far edge, ``y0 + L p + w``."""

    top = candidate["field_origin"][1] + (candidate["rows"] - 1) * candidate["pitch"] + candidate["width"]
    return int(round(top * 1e6))


def _field_key(candidate: Mapping[str, Any]) -> tuple:
    """What tells two fields apart: the exit, frame, pitch, origin and cells."""

    origin = candidate["field_origin"]
    return (candidate["order"], candidate["angle_deg"], candidate["pitch"], round(origin[0], 6), round(origin[1], 6), tuple(candidate["cells"]))


class _PassSearch:
    """What :func:`_make` reads of a search in the tip pass (counts, not areas; the lead's reach limit)."""

    area = False

    def __init__(self, reach: Any) -> None:
        self.reach = reach


def rectangles_by_top(plain: Sequence[Sequence[int]], up: Sequence[Sequence[int]], rows_cap: int, columns_cap: int,
                      zones: Any = None) -> list:
    """Per top row of the rows given (bottom to top), the full rectangle with the most cells whose top row it is, within the
    caps: ``(count, rows, columns, row, a)`` (bottom row, left cell) or None.

    :func:`best_rectangle`'s rules (the top row's ``plain``, the others'
    ``up``; every row but the bottom one holds its bottom corner zones, every
    row but the top one its top ones; the column cap before the right zones,
    section 26a), grown down from the top row, and its choice among equal
    widths (the first widest run).
    """

    count = len(plain)
    width = len(plain[0]) if count else 0
    found = []
    for top in range(count if width else 0):
        best = None
        reach = list(plain[top])
        left_ok = right_ok = None
        for j0 in range(top, max(-1, top - rows_cap), -1):
            height = top - j0 + 1
            if j0 < top:
                if zones and zones[j0 + 1] is not None:
                    left_ok, right_ok = _and(left_ok, zones[j0 + 1][0]), _and(right_ok, zones[j0 + 1][1])
                if zones and zones[j0] is not None:
                    left_ok, right_ok = _and(left_ok, zones[j0][2]), _and(right_ok, zones[j0][3])
                reach = list(map(min, reach, up[j0]))
            if left_ok is None and right_ok is None:
                spans = [end - a + 1 if end >= a else 0 for a, end in enumerate(reach)]
            else:
                left = left_ok if left_ok is not None else [True] * width
                last = _last_true(right_ok if right_ok is not None else [True] * width)
                spans = [last[min(end, a + columns_cap - 1)] - a + 1 if end >= a and left[a] else 0 for a, end in enumerate(reach)]
            widest = max(spans)
            if widest <= 0:
                break
            cells = min(widest, columns_cap) * height
            if best is None or cells > best[0]:
                best = (cells, height, min(widest, columns_cap), j0, spans.index(widest))
        found.append(best)
    return found


def _tip_lattices(lead: Mapping[str, Any], options: Mapping[str, Any]) -> list:
    """The lattices of a lead's frame at its pitch that the tip pass visits: ``(grid, symmetric)`` (the quarter phases and
    the centred one; a symmetric lead's symmetric lattices of both parities at the row phases k p / 8,
    :data:`TIP_ROW_PHASES`, and the centred one: the quarter ones first, as before section 26.18)."""

    space, pitch, width, margin = lead["region"], lead["pitch"], lead["width"], lead["margin"]
    found = []
    if lead.get("symmetric"):
        rows = [0.0, round(pitch / 2, 6), round(pitch / 4, 6), round(3 * pitch / 4, 6)]
        rows += [round(k * pitch / TIP_ROW_PHASES, 6) for k in range(1, TIP_ROW_PHASES, 2)]
        middle = centred_phase(space, pitch, width, margin)[1]
        if middle not in rows:
            rows.append(middle)
        for even in (False, True):
            for phase in rows:
                grid = symmetric_lattice(space, pitch, width, margin, lead["symmetry"]["axis"], even, phase)
                if grid is not None:
                    found.append(grid)
        return found
    phases = quarter_phases(pitch)
    middle = centred_phase(space, pitch, width, margin)
    if middle not in phases:
        phases.append(middle)
    return [lattice(space, pitch, width, margin, phase) for phase in phases]


def tip_pass(lead: Mapping[str, Any], options: Mapping[str, Any], floor: int, slack: int) -> dict:
    """The tip pass of a group (section 26): its lattices' fields of at least ``floor`` per top row, as candidates.

    The pool is the fields (as the lead: a masked or asymmetric lead's
    :func:`best_convex`, a symmetric one's :func:`best_symmetric`, a full
    one's full rectangles only, :func:`rectangles_by_top`) whose top run
    lies in a row reaching within ``slack`` (nm) of the farthest reach R of
    a pool field, and the lead's ties (the pool fields of at least its
    value) reaching within ``slack`` of the farthest of them, R_G
    (``tied``): the fields :func:`tip_choice` takes the tip-first field and
    the lead's zero-cost tie T0 from.  Each lattice's DP runs once at the
    threshold ``floor - 1`` (the lead's value - 1 on a lattice whose
    farthest row cannot reach R - ``slack``: only ties count there) and
    gives every row's best (``per_row``).  The lattices are visited by
    their farthest free row (within the caps, section 23's window and
    ``far``), farthest first, and none whose farthest row cannot reach R_G
    - ``slack`` (R_G only grows), nor one whose bound is under its
    threshold.  The pass has its own meter, :data:`TIP_WORK_BUDGET` cells;
    past it the pool is what was found (``complete`` false;
    deterministic).  Returns ``{"pool", "farthest", "tied", "complete",
    "work"}`` (nm).
    """

    pitch, width = lead["pitch"], lead["width"]
    symmetric = bool(lead.get("symmetric"))
    full = bool(lead["full"])
    frame = {"order": lead["order"], "side": lead["side"], "angle": 0.0, "frame": lead["frame"], "space": lead["region"], "symmetry": lead.get("symmetry")}
    search = _PassSearch(lead.get("reach_limit"))
    shaped_caps, rectangle_caps = caps(options)
    meter = [0]
    visits = []
    for index, grid in enumerate(_tip_lattices(lead, options)):
        rows, columns = grid["rows"], grid["columns"]
        if not rows or not columns:
            continue
        far = None if search.reach is None else far_row(grid, search.reach)
        for rows_cap, columns_cap in (rectangle_caps if full else shaped_caps):
            if symmetric:
                top = rows - 1 if far is None else min(far, rows - 1)
                runs = [run for run in symmetric_runs(columns) if run[1] - run[0] + 1 <= columns_cap]
                last = next((j for j in range(top, -1, -1) if any(grid["plain"][j][a] >= b for a, b in runs)), None) if runs and top >= 0 else None
                window = None if last is None else tip_window(last, rows_cap)
            else:
                window = tip_rows(grid["plain"], rows_cap, far)
            if window is None:
                continue
            reach = int(round((grid["y0"] + window[1] * pitch + width) * 1e6))
            visits.append((-reach, index, rows_cap, columns_cap, grid, window))
    visits.sort(key=lambda item: item[:4])
    pool = [lead]
    farthest = tied = tip_reach(lead)
    complete = True
    kind = "rectangle" if full else "shaped"
    for negative, _, rows_cap, columns_cap, grid, (low, high) in visits:
        reach_top = -negative
        if reach_top < tied - slack:
            break  # no field of this lattice (nor of the next) reaches the tip-first field or the lead's tie
        # Short of the tip-first field's reach only the lead's ties count (fields of at least its value).
        need = floor if reach_top >= farthest - slack else lead["value"]
        plain, up, zones, band = grid["plain"], grid["up"], grid.get("zones"), grid.get("band")
        if lattice_bound(plain[low:high + 1], rows_cap, columns_cap) <= need - 1:
            continue
        if meter[0] >= TIP_WORK_BUDGET:
            complete = False
            break
        found = []  # (count, spans)
        if symmetric:
            per_row: list = []
            best_symmetric(plain, up, grid["columns"], low, high, columns_cap, need - 1, zones, full, band, per_row)
            meter[0] += (high - low + 1) * grid["columns"]
            found = [item for item in per_row if item is not None]
        elif full:
            window_zones = zones[low:high + 1] if zones else zones
            for item in rectangles_by_top(plain[low:high + 1], up[low:high + 1], rows_cap, columns_cap, window_zones):
                if item is not None and item[0] >= need:
                    count, height, wide, row, a = item
                    found.append((count, [(j, a, a + wide - 1) for j in range(low + row, low + row + height)]))
            meter[0] += (high - low + 1) * min(rows_cap, high - low + 1) * grid["columns"]
        else:
            columns = grid["columns"]
            boxes = [(0, low, 0, high, columns - 1)] if columns <= columns_cap else \
                sorted(window_bounds([row_intervals(ends) for ends in plain], grid["rows"], columns, rows_cap, columns_cap, high),
                       key=lambda box: (-box[0], box[1:]))
            for bound, row_lo, col_lo, row_hi, col_hi in boxes:
                if columns > columns_cap and bound <= need - 1:
                    break
                if meter[0] >= TIP_WORK_BUDGET:
                    complete = False
                    break
                per_row = []
                best_convex(plain, up, col_lo, col_hi, row_lo, row_hi, need - 1, meter, zones, band, per_row)
                found += [item for item in per_row if item is not None]
        for count, spans in found:
            candidate = _make(search, grid, spans, frame, kind)
            if candidate["value"] < floor or candidate["symmetric"] != symmetric or (full and not candidate["full"]):
                continue
            reach = tip_reach(candidate)
            tie = candidate["value"] >= lead["value"]
            if reach < farthest - slack and not (tie and reach >= tied - slack):
                continue
            pool.append(candidate)
            if reach > farthest:
                farthest = reach
            if tie and reach > tied:
                tied = reach
        if not complete:
            break
    return {"pool": pool, "farthest": farthest, "tied": tied, "complete": complete, "work": meter[0]}


def lead_rank(candidate: Mapping[str, Any]) -> tuple:
    """The order within a group's lead (section 26): :func:`field_rank` (the most taxels first), fields alike in taxels,
    pitch, turn, fill and readout positions reaching farther toward the fingertip first (a tie-break that costs nothing;
    ``field_rank`` itself, which also orders exits, is unchanged)."""

    rank = field_rank(candidate)
    return rank[:6] + (-tip_reach(candidate),) + rank[6:]


def tip_choice(lead: Mapping[str, Any], queue: Sequence[Mapping[str, Any]], options: Mapping[str, Any]) -> tuple:
    """The tip-first field of a group (section 26c): ``(T, report)``; T is the lead itself when no other field leads.

    M the most value on the lead's exit, unturned, at its pitch (both
    symmetry kinds; a symmetric lead's of the symmetric fields there:
    symmetry is free, the tip costs at most 3 % of the best symmetric
    field, section 26.17), the floor ``min(lead, ceil(M * 97 / 100))``
    (:data:`TIP_SHARE`); of the pool's fields (:func:`tip_pass`) reaching
    within the slack of the farthest (``p / 8``, :data:`TIP_SLACK`; a
    symmetric lead's ``p / 16``, :data:`TIP_SYMMETRIC_SLACK`, half its row
    phases' step), the best by :func:`lead_rank` (the most taxels first:
    reach first, so at a pointed tip T may end in a single taxel); and the
    lead's zero-cost tie T0 (``report["tie"]``): of the pool's fields of at
    least the lead's value reaching within the slack of the farthest such
    field, the best by
    :func:`lead_rank`.  With ``tip_first: false`` (:func:`tip_leads`) the
    floor is the lead's value and T the lead: its zero-cost tie alone may
    move (coverage first, no taxel given up).  ``report["most"]``: the
    most of the lead and its pool (the lead, or a larger field of the pass's
    own: what the tip-first field could have held instead, which
    ``taxels_given`` counts from, :func:`tip_metrics`; not M, which may be
    another readout's never proposed in the group's place).
    """

    same = [candidate for candidate in queue
            if candidate["order"] == lead["order"] and candidate["angle_deg"] == 0.0 and candidate["pitch"] == lead["pitch"]]
    if lead.get("symmetric"):
        same = [candidate for candidate in same if candidate.get("symmetric")]
    most = max([candidate["value"] for candidate in same] + [lead["value"]])
    leads = tip_leads(options)
    floor = min(lead["value"], -(-most * TIP_SHARE[0] // TIP_SHARE[1])) if leads else lead["value"]
    slack = int(round(lead["pitch"] * 1e6)) // TIP_SLACK
    if lead.get("symmetric"):
        slack = int(round(lead["pitch"] * 1e6)) // TIP_SYMMETRIC_SLACK
    found = tip_pass(lead, options, floor, slack)
    pool = found["pool"]
    # T0: the lead's own tie toward the fingertip (as many taxels; what the field the most taxels shows looks like).
    ties = [candidate for candidate in pool if candidate["value"] >= lead["value"]]
    tied = max(tip_reach(candidate) for candidate in ties)
    tie = min([candidate for candidate in ties if tip_reach(candidate) >= tied - slack], key=lead_rank)
    if not leads:
        # tip_first false: the zero-cost tie alone (coverage first: no taxel given up).
        best, cut = lead, tip_reach(lead)
    else:
        cut = found["farthest"] - slack
        best = min([candidate for candidate in pool if tip_reach(candidate) >= cut], key=lead_rank)
    report = {"floor": floor, "most": max([lead["value"]] + [candidate["value"] for candidate in pool]), "cut": cut, "farthest": found["farthest"],
              "complete": found["complete"], "work": found["work"], "full": bool(lead["full"]), "tie": tie}
    return best, report


def proposed(queue: Sequence[Mapping[str, Any]], count: int) -> list:
    """The first ``count`` fields of ``queue`` that :func:`fit_chart_field` would propose were each built as found: one per
    readout and kind (full or masked, symmetric or not) and none an earlier one dominates (:func:`surface.fill.dominated`:
    as many taxels on no more rows and columns)."""

    found: list = []
    shapes = set()
    for candidate in queue:
        if len(found) >= count:
            break
        shape = fill.proposal_shape(candidate["rows"], candidate["columns"], candidate["taxels"], None if candidate["full"] else True) + (bool(candidate.get("symmetric")),)
        if shape in shapes or any(other["taxels"] >= candidate["taxels"] and other["rows"] <= candidate["rows"] and other["columns"] <= candidate["columns"]
                                  for other in found):
            continue
        shapes.add(shape)
        found.append(candidate)
    return found


def tip_peel_holds(tip: Mapping[str, Any], peeled: Mapping[str, Any]) -> bool:
    """Whether a tip-first field's peel (:func:`peel_field`) still leads its group (section 26): at least its floor,
    within its lead's cut and full when its lead was full; a peel below its floor, out of its lead or a full one notched
    gives the slot back to the field it displaced.  ``tip`` is the tip-first field's report (:func:`tip_choice`)."""

    return peeled["value"] >= tip["floor"] and tip_reach(peeled) >= tip["cut"] and (peeled["full"] or not tip["full"])


def tip_metrics(candidate: Mapping[str, Any]) -> dict:
    """A proposal's ``tip`` metrics (section 26): ``reach_mm`` (an unturned field's reach from its exit, None turned),
    ``lead`` (a tip-first field in its group's lead's slot), and for a lead ``farthest_mm`` (the farthest reach of its
    pool), ``displaced`` (the rank of the proposal in the place of the field it displaced: that field's, or its zero-cost
    tie's that took its place, the lead's own when it is that tie itself; None when none was proposed), ``taxels_given``
    (what the tip cost: how many taxels fewer than the lead it displaced, or than a larger field its own pass found;
    never negative, at most the lead's value less the floor unless the pass found more) and ``complete`` (whether its
    pass finished within its work budget)."""

    tip = candidate.get("tip") if candidate.get("tip_lead") else None
    return {
        "reach_mm": round(tip_reach(candidate) / 1e6, 6) if candidate["angle_deg"] == 0.0 else None,
        "lead": tip is not None,
        "farthest_mm": round(tip["farthest"] / 1e6, 6) if tip else None,
        "displaced_root": tip["displaced"] if tip else None,
        "taxels_given": tip["given"] if tip else 0,
        "complete": tip["complete"] if tip else None,
    }


def tip_first(queue: Sequence[Mapping[str, Any]], options: Mapping[str, Any], report: Any = None, skip: Sequence = ()) -> list:
    """The proposal order with the tip-first fields (the user's request of 2026-10-26, P5-diagonal-bus.md section 26: "the
    taxels stack from the fingertip as far as possible"): after :func:`ordered` (and :func:`keep_exits`).

    Each unturned field among the first ``proposals`` fields of ``queue``
    the fit would propose (:func:`proposed`) whose group (exit, pitch,
    symmetry kind) is new leads its group; its
    tip-first field (:func:`tip_choice`, a full lead taking full rectangles
    only) takes its slot when it is another field, flagged ``tip_lead`` (one
    more proposal key, :func:`fit_chart_field`), then the lead's zero-cost
    tie T0 when that is another field still, flagged ``tip_tie``: T0 takes
    the lead's place (``place``, section 26.17; T does when it is T0), and
    the lead follows directly, proposed only should no field in its place
    be proposed with at least its taxels (T0 not built, or peeled).  The
    exits, frames, pitches and symmetry kinds stay as ``queue`` has them;
    turned leads and ``max_area`` keep the order.  ``tip_first: false``
    places the zero-cost ties alone (no taxel given up): the proposals are
    coverage alone's, but for the lead's slot.
    ``report`` (a dict) gets per exit ``order`` the passes' work and
    whether they completed; ``skip``: exits left alone.
    """

    queue = list(queue)
    if not tip_on(options) or not queue:
        return queue
    leads = []
    groups = set()
    for candidate in proposed(queue, options["proposals"]):
        if candidate["angle_deg"] != 0.0:
            continue
        group = (candidate["order"], candidate["pitch"], bool(candidate.get("symmetric")))
        if group in groups:
            continue
        groups.add(group)
        if candidate["order"] not in skip:
            leads.append(candidate)
    for lead in leads:
        best, found = tip_choice(lead, queue, options)
        tie = found.pop("tie")
        if report is not None:
            held = report.setdefault(lead["order"], {"work": 0, "complete": True})
            held["work"] += found["work"]
            held["complete"] = held["complete"] and found["complete"]
        placed = []
        if _field_key(best) != _field_key(lead):
            best = dict(best)
            best["tip_lead"] = True
            best["tip"] = dict(found, displaced=id(lead), given=found["most"] - best["value"])
            placed.append(best)
        if _field_key(tie) != _field_key(lead):
            if _field_key(tie) != _field_key(best):
                tie = dict(tie)
                tie["tip_tie"] = True
                placed.append(tie)
            # T0 (or T, when it is T0) takes the lead's place (section 26.17): ``(id, taxels)`` of the lead it stands for.
            placed[-1]["place"] = (id(lead), lead["value"])
        if not placed:
            continue
        keys = {_field_key(candidate) for candidate in placed}
        queue = [candidate for candidate in queue
                 if _field_key(candidate) not in keys or candidate.get("tip_lead") or candidate.get("tip_tie")]
        at = next(k for k, candidate in enumerate(queue) if candidate is lead)
        queue[at:at] = placed
    return queue


def _search_grid(search: _Search, grid: Mapping[str, Any], frame: Mapping[str, Any], turned: bool) -> list:
    """The best rectangle and the best shaped field of one lattice under each cap that beat the search's threshold.

    The rectangles first: they are cheap, and a shaped field must then beat them too.
    """

    pitch, width = grid["pitch"], grid["width"]
    found = []
    search.searched += 1
    for kind, limits in (("rectangle", search.rectangle_caps), ("shaped", search.shaped_caps)):
        for rows_cap, columns_cap in limits:
            search.capped = search.capped or grid["rows"] > rows_cap or grid["columns"] > columns_cap
            threshold = search.threshold(turned, pitch)
            bound = _lattice_bound_value(lattice_bound(grid["plain"], rows_cap, columns_cap), pitch, width, search.area)
            if bound <= threshold:
                continue
            far = None if search.reach is None else far_row(grid, search.reach)
            if kind == "rectangle":
                # In the cap's rows at the far end (section 23), as a shaped field.
                plain, up, zones = grid["plain"], grid["up"], grid.get("zones")
                window = tip_rows(plain, rows_cap, far)
                if window is None:
                    continue
                low, high = window
                count, rows, columns, row, a = best_rectangle(plain[low:high + 1], up[low:high + 1], rows_cap, columns_cap,
                                                              threshold if not search.area else 0, zones[low:high + 1] if zones else zones)
                spans = [(j, a, a + columns - 1) for j in range(low + row, low + row + rows)]
            else:
                # The DP counts cells: with max_area every cell counts at most a pitch square of P.
                cells = threshold if not search.area else int(threshold // int(math.ceil(pitch * pitch * 1e6)))
                count, spans = search_shaped(grid, rows_cap, columns_cap, cells, search.meter, WORK_BUDGET, far)
            if not count:
                continue
            candidate = _make(search, grid, spans, frame, kind)
            if candidate["value"] > threshold:
                found.append(candidate)
                search.add(candidate)
    return found


def search_fields(chart: Any, bases: Sequence, options: Mapping[str, Any], profile: Mapping[str, Any], obstacles: Mapping[str, Any],
                  per_base: list, info: Any = None) -> list:
    """Every field the search keeps (the lattices' winners), unordered (:func:`ordered` ranks them).

    The unturned frames first, then (``rotation: auto``) the frames turned
    against the :data:`TURNED_EXITS` best exits, so that the best unturned
    field, which a turned one must beat by :data:`TURN_GAIN`, is known before
    any turned lattice is searched.  Per kind: the coarse phases (0 and p/2
    in x and y, phase 0 on the usable edge) at the first pitch of
    :func:`ladder` on every frame and at the other pitches on the
    :data:`LADDER_FRAMES` best frames; then the quarter phases at each
    frame's best pitch (the first where it found nothing): every unturned
    frame, and the :data:`FINE_FRAMES` best turned ones.  ``max_area`` first
    seeds its first :data:`SEED_EXITS` exits unturned at phase 0, the
    largest pitch first.  Each frame's lattices are searched best bound
    first; one whose bound does not beat :meth:`_Search.threshold` is not.
    ``per_base`` gets every frame searched (``field_candidates``: the fields
    it kept, 0 when none; ``symmetric``: whether the face is symmetric about
    the exit, :func:`exit_symmetry`; ``symmetric_candidates``: the symmetric
    fields found there, one per symmetric lattice and cap).

    Symmetric faces (the user's request, P5-diagonal-bus.md section 22):
    after the unturned frames, every exit whose face is symmetric
    (:func:`exit_symmetry`) is searched for mirror-symmetric fields
    (:func:`search_symmetric` on :func:`symmetric_lattice`: a column on the
    axis and the axis between two columns, the coarse row phases at every
    pitch, then the quarter and centred row phases at the exit's best one),
    without the work budget (a symmetric lattice's DP is linear in its rows
    and half widths) and outside the pruning of the others (their
    alternatives stay as they were).  An exit whose best symmetric field
    holds within :data:`SYMMETRY_GAIN` of its best unturned field is not
    turned (a turned field there would break the symmetry; section 26.19).
    """

    search = _Search(options, profile, len(bases) > 1)
    margin = search.margin
    frames = []
    symmetry = [exit_symmetry(chart, side, obstacles) for side in bases]

    def add_frames(order: int, side: Mapping[str, Any], angles: Sequence[float]) -> list:
        made = []
        for angle in angles:
            frame = fit.BaseFrame(side, angle)
            space = fill.FreeSpace(chart, frame, obstacles, options["edge_margin_mm"], side["edges"])
            made.append({"order": order, "side": side, "angle": angle, "frame": frame, "space": space, "symmetry": symmetry[order]})
        frames.extend(made)
        return made

    for order, side in enumerate(bases):
        add_frames(order, side, (0.0,))
    tally: dict = {}
    mirrored: dict = {}  # exit order -> the symmetric fields found there
    kept: list = []

    def run(chosen: Sequence, pitch: float, phases: Sequence, centred: bool = False) -> None:
        width = fit._electrode(pitch, options["fill"])
        for turned in (False, True):
            grids = []
            for frame in chosen:
                if (frame["angle"] != 0.0) != turned:
                    continue
                tally.setdefault((frame["order"], frame["angle"]), 0)
                mine = list(phases)
                if centred:
                    middle = centred_phase(frame["space"], pitch, width, margin)
                    if middle not in mine and middle not in quarter_phases(pitch):
                        mine.append(middle)
                for phase in mine:
                    grid = lattice(frame["space"], pitch, width, margin, phase)
                    bound = 0
                    for rows_cap, columns_cap in search.shaped_caps + search.rectangle_caps:
                        bound = max(bound, lattice_bound(grid["plain"], rows_cap, columns_cap))
                    grids.append((-bound, frame["order"], abs(frame["angle"]), frame["angle"], phase, grid, frame))
            grids.sort(key=lambda item: item[:5])
            for negative, _, _, _, _, grid, frame in grids:
                if _lattice_bound_value(-negative, pitch, width, search.area) <= search.threshold(turned, pitch):
                    break
                if WORK_BUDGET is not None and search.meter[0] >= WORK_BUDGET:
                    break
                found = _search_grid(search, grid, frame, turned)
                kept.extend(found)
                key = (frame["order"], frame["angle"])
                tally[key] += len(found)
                for candidate in found:
                    held = search.frame_best.get((frame["order"], frame["angle"], pitch))
                    if held is None or candidate["rank"] < held["rank"]:
                        search.frame_best[(frame["order"], frame["angle"], pitch)] = candidate

    def best_frames(turned: bool, count: int, skipped: Sequence = ()) -> list:
        ranked = sorted(search.frame_best.items(), key=lambda item: item[1]["rank"])
        chosen = []
        for (order, angle, pitch), _ in ranked:
            if (angle != 0.0) != turned or order in skipped or any(item[0] == order and item[1] == angle for item in chosen):
                continue
            chosen.append((order, angle, pitch))
        return chosen[:count]

    def run_symmetric(chosen: Sequence, pitch: float, rows: Sequence, centred: bool = False) -> None:
        # Mirror-symmetric fields on the symmetric exits' lattices (both parities, the row phases ``rows``).
        width = fit._electrode(pitch, options["fill"])
        for frame in chosen:
            space = frame["space"]
            mine = list(rows)
            if centred:
                middle = centred_phase(space, pitch, width, margin)[1]
                if middle not in mine and middle not in [phase for _, phase in quarter_phases(pitch)]:
                    mine.append(middle)
            for even in (False, True):
                for phase in mine:
                    grid = symmetric_lattice(space, pitch, width, margin, frame["symmetry"]["axis"], even, phase)
                    if grid is None:
                        continue
                    for kind, limits in (("rectangle", search.rectangle_caps), ("shaped", search.shaped_caps)):
                        for rows_cap, columns_cap in limits:
                            search.capped = search.capped or grid["rows"] > rows_cap or grid["columns"] > columns_cap
                            count, spans = search_symmetric(grid, rows_cap, columns_cap, 0, kind == "rectangle",
                                                            None if search.reach is None else far_row(grid, search.reach))
                            if not count:
                                continue
                            candidate = _make(search, grid, spans, frame, kind)
                            mirrored.setdefault(frame["order"], []).append(candidate)
                            # A turned field must beat the symmetric ones by TURN_GAIN too (ordered): its lattices prune by them.
                            search.unturned = max(search.unturned, candidate["value"])

    def best_pitch(order: int) -> float:
        found = sorted((candidate["rank"], candidate["pitch"]) for candidate in mirrored.get(order, []))
        return found[0][1] if found else pitches[0]

    def search_kind(chosen: Sequence, turned: bool, fine: Any) -> None:
        # The coarse phases over the ladder, then the quarter phases of the fine frames (all of them when None).
        run(chosen, pitches[0], coarse_phases(pitches[0]))
        best = {(order, angle) for order, angle, _ in best_frames(turned, LADDER_FRAMES)}
        ladder_frames = [frame for frame in chosen if (frame["order"], frame["angle"]) in best]
        for pitch in pitches[1:]:
            run(ladder_frames, pitch, coarse_phases(pitch))
        if fine is not None:
            best = {(order, angle) for order, angle, _ in best_frames(turned, fine)}
            # Where no turned frame's coarse lattices found a field (none beat the unturned one by TURN_GAIN: section 24's
            # staircases hold more), every turned frame takes its fine phases, each lattice still pruned by its bound: a
            # quarter or the centred phase may hold the field the coarse ones miss (the slanted strip's 74 at -30 degrees).
            if not (turned and not best):
                chosen = [frame for frame in chosen if (frame["order"], frame["angle"]) in best]
        centring = []
        for frame in chosen:
            mine = sorted((candidate["rank"], pitch) for (order, angle, pitch), candidate in search.frame_best.items()
                          if order == frame["order"] and angle == frame["angle"])
            pitch = mine[0][1] if mine else pitches[0]
            coarse = coarse_phases(pitch)
            run([frame], pitch, [phase for phase in quarter_phases(pitch) if phase not in coarse])
            centring.append((frame, pitch))
        # Last, the phase that centres the lattice in the usable extent, on the same frames at the same pitch (the
        # rounded plates' full rectangle; searched after the others, so that the work budget goes to them first).
        for frame, pitch in centring:
            run([frame], pitch, [], centred=True)

    pitches = [pitch for pitch in ladder(options) if fit._electrode(pitch, options["fill"]) <= pitch - fit.MIN_GAP_MM + 1e-9]
    if pitches:
        if search.area:
            # max_area: a seed of the first exits unturned at one phase, the largest pitch first (a capped field has the
            # most area there), so that its area prunes the large lattices of the small pitches below.
            for pitch in sorted(pitches, reverse=True):
                run(frames[:SEED_EXITS], pitch, [(0.0, 0.0)])
        search_kind(list(frames), False, None)
        # The symmetric exits' mirror-symmetric fields: the coarse row phases at every pitch, then the quarter and centred
        # row phases at each exit's best pitch.
        symmetric = [frame for frame in frames if frame["symmetry"]["symmetric"]]
        for pitch in pitches:
            run_symmetric(symmetric, pitch, [phase for _, phase in coarse_phases(pitch)[:2]])
        for frame in symmetric:
            pitch = best_pitch(frame["order"])
            run_symmetric([frame], pitch, [round(pitch / 4, 6), round(3 * pitch / 4, 6)], centred=True)
        for order in sorted(mirrored):
            kept.extend(symmetric_alternatives(mirrored[order]))
        if options["rotation"] == "auto":
            # Turn the board against the best exits (the tails cross them obliquely, at most 30 degrees), but for those whose
            # symmetric field holds within SYMMETRY_GAIN of their best unturned field (a turn breaks the symmetry, section
            # 26.19).
            best: dict = {}
            for candidate in kept:
                if candidate["angle_deg"] == 0.0:
                    best[candidate["order"]] = max(best.get(candidate["order"], 0), candidate["value"])
            skipped = [order for order in sorted(mirrored) if symmetric_leads(max(c["value"] for c in mirrored[order]), best[order])]
            turned = []
            for order, _, _ in best_frames(False, TURNED_EXITS, skipped):
                turned += add_frames(order, bases[order], fit.ROTATION_STEPS_DEG)
            if turned:
                search_kind(turned, True, FINE_FRAMES)
    for frame in frames:
        key = (frame["order"], frame["angle"])
        if key in tally:
            record = {"side": frame["side"]["index"], "angle_deg": frame["angle"], "chord_mm": frame["side"]["chord_mm"],
                      "candidates": 0, "field_candidates": tally[key]}
            if frame["angle"] == 0.0:
                record["symmetric"] = frame["symmetry"]["symmetric"]
                record["symmetric_candidates"] = len(mirrored.get(frame["order"], []))
            per_base.append(record)
    if info is not None:
        info["capped"] = search.capped
    return kept


def symmetric_alternatives(candidates: Sequence[Mapping[str, Any]]) -> list:
    """The symmetric fields of one exit that the fit keeps, by rank: the best per readout (rows, columns, full or masked),
    the best readout and :data:`SPARE_READOUTS` more within :data:`ALTERNATIVE_SHARE` of it (as the other fields'
    pruning keeps)."""

    ranked = sorted(candidates, key=lambda candidate: candidate["rank"])
    if not ranked:
        return []
    most = ranked[0]["value"]
    found: list = []
    readouts: list = []
    for candidate in ranked:
        readout = (candidate["rows"], candidate["columns"], candidate["full"])
        if readout in readouts or len(readouts) > SPARE_READOUTS or candidate["value"] * ALTERNATIVE_SHARE[1] < most * ALTERNATIVE_SHARE[0]:
            continue
        readouts.append(readout)
        found.append(candidate)
    return found


def coarse_phases(pitch: float) -> list:
    half = round(pitch / 2, 6)
    return [(x, y) for x in (0.0, half) for y in (0.0, half)]


def quarter_phases(pitch: float) -> list:
    return [(round(kx * pitch / 4, 6), round(ky * pitch / 4, 6)) for kx in range(4) for ky in range(4)]


# --------------------------------------------------------------------------
# F of a build, the tails' run on the surface, the walls of a frame
# --------------------------------------------------------------------------


def field_body(result: Mapping[str, Any], origin: Sequence[float] = (0.0, 0.0), grow: Any = None) -> list:
    """F of a build as seen from outside, in the base frame: P (:func:`surface.fill.field_polygon`) grown by the field margin
    as a box, slab by slab (a counter-clockwise ring; ``origin`` is the field's lower-left corner).  ``grow``: the growth
    all round in place of the margin (:func:`field_parts`)."""

    margin = float(result["profile"]["routing"]["active_edge_clearance_mm"]) if grow is None else grow
    rects = [(x0 - margin, low - margin, x1 + margin, high + margin) for low, high, x0, x1 in _p_slabs(result)]
    ring = orthoconvex_ring(rect_union_slabs(rects, 1), 1)
    return [(x + origin[0], y + origin[1]) for x, y in ring]


def _p_slabs(result: Mapping[str, Any]) -> list:
    """P of a build (its frame from outside, the field's lower-left corner at the origin) as y-slabs ``(low, high, x0,
    x1)``, bottom to top."""

    registration = result["boards"]["row"]["grid_registration"]
    if "active_outline" in registration:
        polygon = fill.field_polygon(result, (0.0, 0.0))
    else:
        # A full field of a straight Row channel (no P outline): P is its active region.
        grid = registration["active_region"]
        polygon = [(0.0, 0.0), (grid["width"], 0.0), (grid["width"], grid["height"]), (0.0, grid["height"])]
    levels = sorted({y for _, y in polygon})
    slabs = []
    count = len(polygon)
    for low, high in zip(levels, levels[1:]):
        middle = (low + high) / 2
        xs = []
        for k in range(count):
            (ax, ay), (bx, by) = polygon[k - 1], polygon[k]
            if (ay > middle) != (by > middle):
                xs.append(ax + (middle - ay) * (bx - ax) / (by - ay))
        slabs.append((low, high, min(xs), max(xs)))
    return slabs


def _reach_of(result: Mapping[str, Any], margin: float, tolerance: Any = None) -> float:
    """:func:`corner_reach` of a build's crossings (the narrower of the Row and Column electrode widths)."""

    matrix = result["design"]["matrix"]
    return corner_reach(margin, min(float(matrix["taxel_width_mm"]), float(matrix["taxel_height_mm"])), tolerance)


def convex_corners(slabs: Sequence) -> list:
    """Per y-slab ``(low, high, x0, x1)`` of P (bottom to top), which of its corners are convex corners of F: ``(bottom
    left, bottom right, top left, top right)``, a corner where no slab lies beyond it or the next slab does not reach
    as far (P5-diagonal-bus.md section 24: their zones may leave the surface by the corner tolerance; an aligned or a
    concave end keeps its zone)."""

    found = []
    count = len(slabs)
    for k, (_, _, x0, x1) in enumerate(slabs):
        below = slabs[k - 1] if k > 0 else None
        above = slabs[k + 1] if k + 1 < count else None
        found.append((below is None or below[2] > x0 + _NOISE, below is None or below[3] < x1 - _NOISE,
                       above is None or above[2] > x0 + _NOISE, above is None or above[3] < x1 - _NOISE))
    return found


def exempt_zones(spans: Sequence) -> list:
    """Per run ``(row, a, b)`` of a field (bottom to top), which of its corner zones lie at convex corners of F (the
    lattice's rule of :func:`convex_corners`): ``(bottom left, bottom right, top left, top right)``."""

    found = []
    for k, (_, a, b) in enumerate(spans):
        below = spans[k - 1] if k > 0 else None
        above = spans[k + 1] if k + 1 < len(spans) else None
        found.append((below is None or below[1] > a, below is None or below[2] < b, above is None or above[1] > a,
                      above is None or above[2] < b))
    return found


def field_parts(result: Mapping[str, Any], origin: Sequence[float] = (0.0, 0.0), tolerance: Any = None) -> list:
    """What of F must lie on the usable surface (base-frame rings): F less its corner zones at its convex corners
    (:func:`corner_zones`, :func:`convex_corners`), as P with its margin across x and P with its margin across y, each
    margin left out within the corner reach (:func:`corner_reach`) of each convex corner; and with a corner tolerance
    under the margin, P grown all round by :func:`corner_inset` (:data:`CORNER_TOLERANCE_MM`; ``tolerance`` 0: F all
    round)."""

    margin = float(result["profile"]["routing"]["active_edge_clearance_mm"])
    reach = _reach_of(result, margin, tolerance)
    slabs = _p_slabs(result)
    convex = convex_corners(slabs)
    across, along = [], []  # P with its margin across x (y-slabs), and across y (x-slabs, transposed)
    count = len(slabs)
    for k, (low, high, x0, x1) in enumerate(slabs):
        bottom_left, bottom_right, top_left, top_right = convex[k]
        across.append((x0, low, x1, high))
        along.append((low, x0, high, x1))
        # The margin beside the slab, short of the zones at its convex corners.
        across += [(x0 - margin, low + reach if bottom_left else low, x0, high - reach if top_left else high),
                   (x1, low + reach if bottom_right else low, x1 + margin, high - reach if top_right else high)]
        # The margin below and above the slab where no slab covers it, short of the zones at its convex corners.
        for other, level, outward, left, right in ((slabs[k - 1] if k > 0 else None, low, -1, bottom_left, bottom_right),
                                                    (slabs[k + 1] if k + 1 < count else None, high, 1, top_left, top_right)):
            if other is None:
                spans = [(x0 + reach, x1 - reach)]
            else:
                spans = [(x0 + reach if left else x0, min(x1, other[2])), (max(x0, other[3]), x1 - reach if right else x1)]
            for start, end in spans:
                if end > start + _NOISE:
                    along.append((min(level, level + outward * margin), start, max(level, level + outward * margin), end))
    rings = [orthoconvex_ring(rect_union_slabs([tuple(round(v, 6) for v in rect) for rect in across], 1), 1),
             [[x, y] for y, x in orthoconvex_ring(rect_union_slabs([tuple(round(v, 6) for v in rect) for rect in along], 1), 1)][::-1]]
    parts = [[(x + origin[0], y + origin[1]) for x, y in ring] for ring in rings]
    inner = corner_inset(margin, tolerance)
    if inner > 0:
        parts.append(field_body(result, origin, inner))
    return parts


def corner_zones(result: Mapping[str, Any], origin: Sequence[float] = (0.0, 0.0), tolerance: Any = None) -> list:
    """F's corner zones at its convex corners (base frame; :func:`convex_corners`): ``(corner, outward x, outward y, reach,
    margin)``, the zone the box from ``reach`` inside P's sides to ``margin`` beyond them, less P."""

    margin = float(result["profile"]["routing"]["active_edge_clearance_mm"])
    reach = _reach_of(result, margin, tolerance)
    slabs = _p_slabs(result)
    zones = []
    for (low, high, x0, x1), flags in zip(slabs, convex_corners(slabs)):
        for (corner, sx, sy), convex in zip((((x0, low), -1, -1), ((x1, low), 1, -1), ((x0, high), -1, 1), ((x1, high), 1, 1)), flags):
            if convex:
                zones.append(((corner[0] + origin[0], corner[1] + origin[1]), sx, sy, reach, margin))
    return zones


def parts_clearance(parts: Sequence, region: Any, frame: Any, chart: Any, obstacles: Mapping[str, Any], margin: float) -> Any:
    """The smallest clearance of F's parts (:func:`field_parts`) to the surface's edge and obstacles
    (:func:`surface.fit.check_containment`), or None when one leaves the usable surface."""

    smallest = math.inf
    for k in range(0, len(parts), 2):
        found = fit.check_containment({"row": parts[k], "column": parts[min(k + 1, len(parts) - 1)]}, region, frame, chart, obstacles, margin)
        if found is None:
            return None
        smallest = min(smallest, found)
    return smallest


def parts_failure(parts: Sequence, region: Any, frame: Any, obstacles: Mapping[str, Any], margin: float) -> Any:
    """Where one of F's parts leaves the usable surface (:func:`surface.fill.containment_failure`), or None."""

    for k in range(0, len(parts), 2):
        point = fill.containment_failure({"row": parts[k], "column": parts[min(k + 1, len(parts) - 1)]}, region, frame, obstacles, margin,
                                         {"row": math.inf, "column": math.inf})
        if point is not None:
            return point
    return None


def corner_overhang(zones: Sequence, region: Any, frame: Any, obstacles: Mapping[str, Any], margin: float) -> float:
    """How far F leaves the usable surface (mm, 0 when it lies on it), across x and across y (the box metric of the
    search's edge margin): the largest distance from a point of F's corner zones (:func:`corner_zones`, sampled every
    eighth of their side; F's parts, :func:`field_parts`, hold the rest) to the surface inset by the edge margin
    ``margin``, off its holes and obstacles (from outside: the edge margin plus the distance to the nearest edge or
    obstacle; inside nearer to one than the margin: the margin less that distance)."""

    context = fit._containment_context(region, frame, obstacles)
    index = context["clear_index"]
    outline = region.outline
    polygons = [polygon for polygon, _ in context["obstacle_polygons"]]
    worst = 0.0
    steps = 8
    for (cx, cy), sx, sy, reach, field_margin in zones:
        span = reach + field_margin
        for i in range(steps + 1):
            for j in range(steps + 1):
                u, v = -reach + span * i / steps, -reach + span * j / steps
                if u <= _NOISE and v <= _NOISE:
                    continue  # inside P
                p = (cx + sx * u, cy + sy * v)
                usable = point_in_polygon(p, outline) and not any(point_in_polygon(p, polygon) for polygon in polygons)
                if usable and (margin <= 0 or (index.segments and index.point_distance(p) >= margin * math.sqrt(2.0))):
                    continue  # on the usable surface: at least the margin across x or y from every edge
                distance = _box_distance(index, p)
                over = margin - distance if usable else margin + distance
                if over > worst:
                    worst = over
    return worst


def _box_distance(index: Any, p: Sequence[float]) -> float:
    """The distance across x and across y (the largest of the two) from a point to the nearest segment of an index."""

    if not index.segments:
        return math.inf
    euclid = index.point_distance(p)
    best = euclid
    for a, b in index.near(p, p, euclid * 1.5 + _NOISE):
        best = min(best, _segment_box_distance(p, a, b))
    return best


def _segment_box_distance(p: Sequence[float], a: Sequence[float], b: Sequence[float]) -> float:
    """``min over t of max(|p - s(t)|_x, |p - s(t)|_y)`` on the segment ``s(t) = a + t (b - a)``."""

    dx, dy = b[0] - a[0], b[1] - a[1]
    ex, ey = p[0] - a[0], p[1] - a[1]
    candidates = [0.0, 1.0]
    if dx:
        candidates.append(ex / dx)
    if dy:
        candidates.append(ey / dy)
    for sign in (1.0, -1.0):
        denominator = dx - sign * dy
        if denominator:
            candidates.append((ex - sign * ey) / denominator)
    best = math.inf
    for t in candidates:
        if 0.0 <= t <= 1.0:
            best = min(best, max(abs(ex - t * dx), abs(ey - t * dy)))
    return best


def walls(space: Any) -> Any:
    """The surface's outline of a frame with every segment a wall (no exit): what F must stay inside."""

    found = getattr(space, "_field_walls", None)
    if found is None:
        found = fit.ExitOutline(space.outline, [])
        space._field_walls = found
    return found


def bottoms(outline: Sequence) -> Any:
    """The surface's outline with every segment an exit: ``exit_y`` gives the surface's lowest edge at x."""

    return fit.ExitOutline(outline, range(len(outline)))


def surface_bottom(lowest: Any, x0: float, x1: float) -> Any:
    """The lowest edge of the surface under ``x0..x1`` (at both ends and every outline vertex between), or None beside it."""

    if lowest._vertex_xs is None:
        lowest._vertex_xs = sorted({point[0] for point in lowest.outline})
    xs = [x0 + 1e-9, x1 - 1e-9]
    for x in lowest._vertex_xs[bisect.bisect_right(lowest._vertex_xs, x0 + 1e-9):bisect.bisect_left(lowest._vertex_xs, x1 - 1e-9)]:
        xs += [x - 1e-9, x]
    found = [y for y in (lowest.exit_y(x) for x in xs) if y is not None]
    return min(found) if found else None


def bottom_beside(lowest: Any, x0: float, x1: float, frame: Any = None) -> float:
    """The lowest edge of the surface under ``x0..x1`` (:func:`surface_bottom`), or, for a span wholly beside the surface,
    the base side's line continued beside it (its lower end under the span): a point of a board beside the surface (a
    funnel or a band wider than the part, :func:`routing_report`; a tail's end there, :func:`tail_reach`) lies as far
    past the base edge as one under it.  The tails, centred on the field (P5-diagonal-bus.md section 27), always have
    the surface above part of them.

    ``frame``: the :class:`surface.fit.BaseFrame` of the base frame, whose base side lies on the line through the
    origin along ``side_dir`` (on y = 0 unrotated, the default)."""

    found = surface_bottom(lowest, x0, x1)
    if found is not None:
        return found
    dx, dy = (1.0, 0.0) if frame is None else frame.side_dir
    return min(x0 * dy / dx, x1 * dy / dx)


def tail_runs(lowest: Any, tails: Mapping[str, Any], frame: Any = None) -> dict:
    """Per board, how far its tail root lies above the surface's lowest edge under it: the run of its tail on the surface,
    negative when the root lies beyond that edge already (the Row bus and the fan-out reach past the exit); for a tail
    beside the surface, from the base side's line continued beside it (:func:`bottom_beside`).  ``tails``: per board
    ``(x0, x1, root y)`` in the base frame."""

    return {key: root - bottom_beside(lowest, x0, x1, frame) for key, (x0, x1, root) in tails.items()}


def tail_lengths(runs: Mapping[str, float], extension: float, minimum: float, roots: Mapping[str, float]) -> dict:
    """The tails' lengths (micrometres, rounded up): both end on one line across the boards, square to the tails (the
    board frame's), so the stacked tails' contacts line up (the user's request of P5-diagonal-bus.md section 27.3): the
    nearest line that every tail's own constraints allow, each tail at least ``minimum`` (the shortest tail) long and
    ending at least ``extension`` (the option ``tail_extension_mm``) past the surface's lowest edge under it.  That is
    the farthest of the ends each tail would have alone, ``max(minimum, run + extension)`` below its root: with equal
    roots (the diagonal Row bus's two tails leave one bottom edge) both are ``max(minimum, max(run + extension))`` long;
    with unequal ones the line lies that far below the root of the tail that sets it, and each other tail reaches it.
    On an arc or a slanted exit (or a turned field, whose exit is slanted in this frame) the tail over the higher edge
    ends farther past it.  ``runs``: :func:`tail_runs`; ``roots``: per board its tail root's y in the same frame
    (:func:`tails_base`)."""

    alone = {key: max(minimum, math.ceil((run + extension) * 1000 - 1e-6) / 1000) for key, run in runs.items()}
    end = min(roots[key] - alone[key] for key in runs)
    return {key: round(math.ceil((roots[key] - end) * 1000 - 1e-6) / 1000, 3) for key in runs}


def tails_base(footprint: Mapping[str, Any], role: str, origin: Sequence[float]) -> dict:
    """Per board ``(x0, x1, root y)`` of its tail in the base frame, from :func:`engine.field_footprint` (the top board seen
    from outside is mirrored about the field's centre line)."""

    width = footprint["field"]["width"]
    found = {}
    for key in ("row", "column"):
        board = footprint[key]
        x, w = board["tail"]["x"], board["tail"]["width"]
        mirrored = (key == "row") == (role == "rows_top")
        x0, x1 = (width - x - w, width - x) if mirrored else (x, x + w)
        found[key] = (origin[0] + x0, origin[0] + x1, origin[1] - board["bottom"])
    return found


def tails_of(result: Mapping[str, Any], origin: Sequence[float]) -> dict:
    """Per board ``(x0, x1, root y)`` of its tail in the base frame, from a build (as :func:`surface.fit.board_outlines_base`
    places the boards: from the active region's lower-left corner, the top board mirrored)."""

    top = result["design"]["role_mapping"]["top"]
    found = {}
    for key in ("row", "column"):
        board = result["boards"][key]
        grid = board["grid_registration"]["active_region"]
        bounds = board["tail"]["bounds"]
        x0, x1 = bounds["x"] - grid["x"], bounds["x"] + bounds["width"] - grid["x"]
        if (key == "row") == (top == "rows"):
            x0, x1 = grid["width"] - x1, grid["width"] - x0
        found[key] = (origin[0] + x0, origin[0] + x1, origin[1] + bounds["y"] + bounds["height"] - grid["y"])
    return found


def mask_for(cells: Sequence, columns: int, role: str) -> Any:
    """``matrix.mask`` of a field (its cells' runs from the left, ROW_01 first) for a role mapping, or None when full.

    Seen from outside, COL_01 is on the left with the rows on top and on the
    right with the columns on top (the top board is turned over)."""

    if all(cell == (0, columns - 1) for cell in cells):
        return None
    if role == "rows_top":
        return [(low + 1, high + 1) for low, high in cells]
    return [(columns - high, columns - low) for low, high in cells]


# --------------------------------------------------------------------------
# Realize
# --------------------------------------------------------------------------


def realize_field(candidate: Mapping[str, Any], chart: Any, obstacles: Mapping[str, Any], options: Mapping[str, Any],
                  profile: Mapping[str, Any], cache: Any, rejected: dict) -> tuple:
    """Build a field and check its F: ``(proposal, None)``, ``(None, peeled)`` or ``(None, None)``.

    The role mappings and routings of the options are tried in order
    (``rows_top`` and default routing first) until the engine builds one; a
    field whose F leaves the surface is peeled (:func:`peel_field`) while it
    has had fewer than :data:`MAX_ATTEMPTS` builds.
    """

    roles = ["rows_top", "columns_top"] if options["role_mapping"] == "auto" else [options["role_mapping"]]
    routings = ["default", "tight"] if options["routing"] == "auto" else [options["routing"]]
    reason, point = "nothing was built", None
    for role in roles:
        for routing in routings:
            outcome = _realize_once(candidate, role, routing, chart, obstacles, options, profile, cache)
            if isinstance(outcome, dict):
                return outcome, None
            reason, point = outcome
            if point is not None:
                break
        if point is not None:
            break
    peeled = None
    if point is not None and candidate["peels"] + 1 < MAX_ATTEMPTS:
        peeled = peel_field(candidate, point)
    if peeled is None:
        rejected[reason] = rejected.get(reason, 0) + 1
    return None, peeled


def probe_tails(candidate: Mapping[str, Any], role: str, routing: str, options: Mapping[str, Any], profile: Mapping[str, Any]) -> tuple:
    """A field's tails before it is built: ``(lengths, runs, None)`` (:func:`tail_lengths`, :func:`tail_runs`) or
    ``(None, None, reason)``.  The probe measures the roots and the tails' x (a tail's length moves neither) with the
    shortest tails, so that its size check refuses no field that fits with the tails it gets."""

    from engine import check_design

    rows, columns, pitch = candidate["rows"], candidate["columns"], candidate["pitch"]
    space, frame = candidate["region"], candidate["frame"]
    shortest = fit.TAIL_MIN_MM[options["template"]]
    probe = fit.design_for(rows, columns, pitch, pitch, options, role, routing, (shortest, shortest), mask_for(candidate["cells"], columns, role))
    probe["routing"]["row_sides"] = options["row_sides"]
    checked = check_design(probe)
    if not checked["ok"]:
        codes = sorted({issue["code"] for issue in checked["validation"]["errors"]})
        return (None, None, "engine rejected the design (" + ", ".join(codes[:3]) + ")")
    try:
        footprint = field_footprint(checked["design"], profile)
    except ValueError as error:
        return (None, None, f"the diagonal Row bus does not build ({error})")
    lowest = getattr(space, "_field_bottoms", None)
    if lowest is None:
        lowest = bottoms(space.outline)
        space._field_bottoms = lowest
    tails = tails_base(footprint, role, candidate["field_origin"])
    runs = tail_runs(lowest, tails, frame)
    return (tail_lengths(runs, options["tail_extension_mm"], shortest, {key: root for key, (_, _, root) in tails.items()}), runs, None)


def _realize_once(candidate: Mapping[str, Any], role: str, routing: str, chart: Any, obstacles: Mapping[str, Any],
                  options: Mapping[str, Any], profile: Mapping[str, Any], cache: Any) -> Any:
    """A proposal, or ``(reason, failure point or None)``."""

    rows, columns, pitch = candidate["rows"], candidate["columns"], candidate["pitch"]
    mask = mask_for(candidate["cells"], columns, role)
    space, frame = candidate["region"], candidate["frame"]
    origin = candidate["field_origin"]
    lengths, runs, reason = probe_tails(candidate, role, routing, options, profile)
    if reason is not None:
        return (reason, None)
    top, bottom = ("row", "column") if role == "rows_top" else ("column", "row")
    if max(lengths.values()) > fit.TAIL_MAX_MM[options["template"]] + 1e-9:
        return (fit.tails_too_long(options["template"]), None)
    design = fit.design_for(rows, columns, pitch, pitch, options, role, routing, (lengths[top], lengths[bottom]), mask)
    design["routing"]["row_sides"] = options["row_sides"]
    result = generate_design(design, cache=cache)
    if not result["ok"]:
        codes = sorted({issue["code"] for issue in result["validation"]["errors"]})
        return ("engine rejected the design (" + ", ".join(codes[:3]) + ")", None)
    outlines = fit.board_outlines_base(result, origin)
    # F less its corner squares (P and the margin along F's sides) on the usable surface: the corners may leave it.
    parts = field_parts(result, origin)
    margin = options["edge_margin_mm"]
    region = walls(space)
    clearance = parts_clearance(parts, region, frame, chart, obstacles, margin)
    if clearance is None:
        return ("the taxel field leaves the surface", parts_failure(parts, region, frame, obstacles, margin))
    manifest = result["manifest"]
    row_board = result["boards"]["row"]
    registration = row_board["grid_registration"]
    bus = row_board["construction"]["row_bus"]
    active = registration["active_taxel_count"]
    area = chart.stats["area_mm2"]
    aw = (columns - 1) * pitch + candidate["width"]
    ah = (rows - 1) * pitch + candidate["width"]
    xs = [point[0] for key in ("row", "column") for point in outlines[key]]
    placement = {
        "base_side": candidate["side"]["index"],
        "base_kind": candidate["side"].get("kind", "side"),
        "exit_edges": sorted(space.exit_edges),
        "base_angle_deg": candidate["angle_deg"],
        "base_from_uv": candidate["side"]["from_uv"],
        "base_to_uv": candidate["side"]["to_uv"],
        "base_inward_uv": candidate["side"]["inward_uv"],
        "field_origin_base": [round(origin[0], 6), round(origin[1], 6)],
        "field_origin_uv": [round(c, 6) for c in frame.to_chart(origin)],
        "field_x_uv": [round(c, 9) for c in frame.ex],
        "field_y_uv": [round(c, 9) for c in frame.ey],
        "seen_from": "outside",
        "bottom_board": result["design"]["role_mapping"]["bottom"],
    }
    holes = getattr(space, "_field_holes", None)
    if holes is None:
        holes = [[frame.to_base(p) for p in hole] for hole in obstacles["holes"]]
        space._field_holes = holes
    report = routing_report(outlines, space, holes, tails_of(result, origin), frame)
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
            "field_coverage": round(fill.polygon_area(outlines["field"]) / area, 6) if area else 0.0,
            "stack_width_mm": round(max(xs) - min(xs), 6),
            "row_tail_mm": lengths["row"],
            "column_tail_mm": lengths["column"],
            # How far the tails' ends lie beyond the surface's lowest edge under them, the nearer one (tail_extension_mm or
            # farther; both end on one line, so the other may end farther past the edge under it).
            "tail_reach_mm": round(min(lengths[key] - runs[key] for key in lengths), 3),
            "min_clearance_mm": round(clearance, 6),
            "role_mapping": role,
            "routing": routing,
            "angle_deg": candidate["angle_deg"],
            "positions": rows * columns,
            "sampled": round(active / (rows * columns), 6),
            "mask_class": row_board["construction"].get("mask_class") if mask is not None else None,
            "reader": reader_module.of_readout(rows, columns, options["reader"]),
            "containment": "field",
            "row_bus": {
                "sides": bus["sides"],
                "tip_width_mm": bus["tip_width_mm"],
                "tip_excess_mm": bus["tip_excess_mm"],
                "band_mm": dict(bus["band_mm"]),
                "widest_mm": bus["widest_mm"],
                "tail_position": bus["tail_position"],
                "tails": bus["tails"],
                "shared_outline_below_field_mm": bus["shared_outline_below_field_mm"],
                "row_contact_order": list(row_board["tail"]["row_contact_order"]),
                "row_pin_order": _row_pins(row_board),
            },
            "routing_on_surface": report,
            "symmetry": symmetry_report(candidate),
        },
        "outlines_uv": {name: [[round(c, 6) for c in frame.to_chart(p)] for p in pts] for name, pts in outlines.items()},
    }


def symmetry_report(candidate: Mapping[str, Any]) -> dict:
    """A proposal's ``symmetry`` metrics (P5-diagonal-bus.md section 22): ``face``, whether the selection is symmetric about
    the exit's axis (:func:`exit_symmetry`; ``deviation_mm`` how far its mirror image lies from it, None when farther than
    a few millimetres), ``axis_mm`` where the axis crosses the exit (from the exit's start, along it), ``field``, whether
    the field is its own mirror image about it (:func:`mirror_symmetric`), and ``field_offset_mm`` how far the field's
    centre lies from the axis across the exit (unturned base frame)."""

    info = candidate.get("symmetry") or {}
    unturned = fit.BaseFrame(candidate["side"], 0.0)
    axis = info.get("axis", unturned.length / 2)
    pitch, width = candidate["pitch"], candidate["width"]
    middle = (candidate["field_origin"][0] + ((candidate["columns"] - 1) * pitch + width) / 2,
              candidate["field_origin"][1] + ((candidate["rows"] - 1) * pitch + width) / 2)
    offset = unturned.to_base(candidate["frame"].to_chart(middle))[0] - axis
    return {
        "face": bool(info.get("symmetric")),
        "deviation_mm": info.get("deviation_mm"),
        "axis_mm": round(axis, 6),
        "field": bool(candidate.get("symmetric")),
        "field_offset_mm": round(offset, 6) if abs(offset) > 1e-6 else 0.0,
    }


def _row_pins(board: Mapping[str, Any]) -> list:
    """The Row nets by connector pin, pin 1 first, from the Row board's pads (:func:`surface.place.row_pin_order`)."""

    from .place import row_pin_order

    return row_pin_order({pad["net"]: pad["pin"] for pad in board["layers"]["top_copper"]["pads"] if pad.get("kind") == "connector_pad"})


def peel_field(candidate: Mapping[str, Any], point: Sequence[float]) -> Any:
    """The field less the end cell nearest a failure point that keeps it row- and column-convex, or None.

    A row's left or right end cell goes (an emptied row only at the top or
    the bottom); the field origin and the readout follow the cells left.  A
    symmetric field (:func:`mirror_symmetric`) loses both end cells of that
    row, so that it stays its own mirror image (a row of one or two cells
    goes whole, at the top or the bottom only).
    """

    cells = [list(cell) for cell in candidate["cells"]]
    rows = len(cells)
    pitch, width, margin = candidate["pitch"], candidate["width"], candidate["margin"]
    ox, oy = candidate["field_origin"]
    choices = []
    for r, (low, high) in enumerate(cells):
        for u in sorted({low, high}):
            x0, y0 = ox + u * pitch - margin, oy + (rows - 1 - r) * pitch - margin
            x1, y1 = x0 + width + 2 * margin, y0 + width + 2 * margin
            dx = max(x0 - point[0], 0.0, point[0] - x1)
            dy = max(y0 - point[1], 0.0, point[1] - y1)
            choices.append((dx * dx + dy * dy, r, u))
    choices.sort()
    both = bool(candidate.get("symmetric"))
    for _, r, u in choices:
        trial = [list(cell) for cell in cells]
        low, high = trial[r]
        if low == high or (both and high - low < 2):
            if r not in (0, rows - 1) or rows == 1:
                continue
            trial.pop(r)
        elif both:
            trial[r] = [low + 1, high - 1]
        elif u == low:
            trial[r][0] += 1
        else:
            trial[r][1] -= 1
        if not _convex(trial):
            continue
        shift = min(low for low, _ in trial)
        trial = [(low - shift, high - shift) for low, high in trial]
        dropped_bottom = r == rows - 1 and len(trial) < rows
        peeled = dict(candidate)
        taxels = 0
        for low, high in trial:
            taxels += high - low + 1
        columns = max(high for _, high in trial) + 1
        peeled.update(
            cells=tuple(trial), rows=len(trial), columns=columns, taxels=taxels, full=taxels == len(trial) * columns,
            value=_value(trial, pitch, width, candidate["value"] != candidate["taxels"]),
            tip_mm=round((trial[0][1] - trial[0][0]) * pitch + width + 2 * margin, 6),
            field_origin=(ox + shift * pitch, oy + (pitch if dropped_bottom else 0.0)),
            peels=candidate["peels"] + 1,
        )
        peeled["symmetric"] = mirror_symmetric(peeled)
        peeled["rank"] = field_rank(peeled)
        return peeled
    return None


def _convex(cells: Sequence) -> bool:
    """Whether runs (top row first) are row- and column-convex: consecutive rows share a column, each column's rows are consecutive."""

    if not cells:
        return False
    for (a0, b0), (a1, b1) in zip(cells, cells[1:]):
        if a1 > b0 or a0 > b1:
            return False
    lows = [low for low, _ in cells]
    highs = [high for _, high in cells]
    return _unimodal(lows, -1) and _unimodal(highs, 1)


def _unimodal(values: Sequence[int], sign: int) -> bool:
    """Whether ``sign * values`` first rises (or stays) and then falls (or stays)."""

    k = 0
    while k + 1 < len(values) and sign * values[k + 1] >= sign * values[k]:
        k += 1
    while k + 1 < len(values) and sign * values[k + 1] <= sign * values[k]:
        k += 1
    return k == len(values) - 1


# --------------------------------------------------------------------------
# How much of each board lies on the surface
# --------------------------------------------------------------------------


def routing_report(outlines: Mapping[str, Sequence], space: Any, holes: Sequence, tails: Mapping[str, Any], frame: Any = None) -> dict:
    """Per board, the share of its outline's area on the surface and how far it overhangs it.

    ``on_surface``: the area on the surface (inside the outline, outside the
    holes) over the board's, by scanlines.  ``overhang_mm``: ``left`` and
    ``right``, the farthest a board corner, or the outline where it crosses
    the surface's lowest level (a straight side running on past it), lies
    from the surface beside it, left or right of the field's centre line:
    off the surface, not beyond the exit under it and not below the
    surface's lowest point (the parts past the base edge, such as the tails
    beside an arc exit, do not count);
    ``exit``, the farthest a corner above the board's tail root, or the
    outline where it crosses the root's level, lies beyond the exit, or,
    beside the surface (outside its extent across) and below its lowest
    point, beyond the base side's line continued beside it
    (:func:`bottom_beside`: a funnel or a band wider than the part).
    ``space``: the frame's outline with its exits (``outline``,
    ``exit_y``), ``holes`` in the base frame, ``tails``: per board ``(x0,
    x1, root y)`` (:func:`tails_of`), ``frame`` the base frame.
    """

    polygons = [space.outline, *holes]
    field = outlines["field"]
    centre = (min(p[0] for p in field) + max(p[0] for p in field)) / 2
    lowest = min(p[1] for p in space.outline)
    bottom = getattr(space, "_field_bottoms", None)
    if bottom is None:
        bottom = bottoms(space.outline)
        space._field_bottoms = bottom
    index = getattr(space, "_field_index", None)
    if index is None:
        outline = space.outline
        index = fit._SegmentIndex([(outline[k - 1], outline[k]) for k in range(len(outline))])
        space._field_index = index
    report = {}
    for key in ("row", "column"):
        polygon = list(outlines[key])
        total, on = _area_on(polygon, polygons)
        left = right = beyond = 0.0
        root = tails[key][2]
        # The corners, and where the outline crosses the tail root's level (a neck or a tail as wide as the board
        # above it has no corner there).
        at_root = [(a[0] + (b[0] - a[0]) * (root - a[1]) / (b[1] - a[1]), root)
                   for a, b in zip(polygon, polygon[1:] + polygon[:1]) if (a[1] - root) * (b[1] - root) < 0]
        # And where it crosses the surface's lowest level (a side running on straight past the base edge has no corner
        # there: diagonal-bus/8's straight sides down to the shared tail roots).
        at_lowest = [(a[0] + (b[0] - a[0]) * (lowest - a[1]) / (b[1] - a[1]), lowest)
                     for a, b in zip(polygon, polygon[1:] + polygon[:1]) if (a[1] - lowest) * (b[1] - lowest) < 0]
        for p in polygon + at_root + at_lowest:
            if point_in_polygon(p, space.outline):
                continue
            y = space.exit_y(p[0])
            if y is not None and p[1] <= y + 1e-6:
                if p[1] >= root - 1e-6:
                    beyond = max(beyond, y - p[1])
                continue
            if p[1] < lowest - 1e-6:
                if y is None and not bottom.x0 <= p[0] <= bottom.x1 and p[1] >= root - 1e-6:
                    beyond = max(beyond, bottom_beside(bottom, p[0], p[0], frame) - p[1])
                continue
            distance = index.point_distance(p)
            if p[0] < centre:
                left = max(left, distance)
            else:
                right = max(right, distance)
        report[key] = {
            "on_surface": round(on / total, 4) if total > 0 else 0.0,
            "overhang_mm": {"left": round(left, 3), "right": round(right, 3), "exit": round(beyond, 3)},
        }
    return report


def _area_on(polygon: Sequence, surface: Sequence) -> tuple:
    """``(area, area on the surface)`` of a polygon, by midpoint scanlines (at most 2000; ``surface``: outline and holes)."""

    ys = [p[1] for p in polygon]
    low, high = min(ys), max(ys)
    step = max(0.05, (high - low) / 2000)
    count = max(1, int(math.ceil((high - low) / step)))
    lines = [low + (k + 0.5) * (high - low) / count for k in range(count)]
    boards = fit._scanlines([polygon], lines)
    surfaces = fit._scanlines(surface, lines)
    total, on = [], []
    for board, cover in zip(boards, surfaces):
        for a0, a1 in board:
            total.append(a1 - a0)
            for s0, s1 in cover:
                if min(a1, s1) > max(a0, s0):
                    on.append(min(a1, s1) - max(a0, s0))
    height = (high - low) / count
    return math.fsum(total) * height, math.fsum(on) * height


# --------------------------------------------------------------------------
# The fit with containment: field
# --------------------------------------------------------------------------


def tail_excess(candidate: Mapping[str, Any], options: Mapping[str, Any], profile: Mapping[str, Any]) -> float:
    """How much longer than the template's maximum (``fit.TAIL_MAX_MM``) a field's longer tail would be (mm; 0 when it
    fits or the probe does not build), with the first role mapping and routing :func:`realize_field` tries."""

    role = "rows_top" if options["role_mapping"] == "auto" else options["role_mapping"]
    routing = "default" if options["routing"] == "auto" else options["routing"]
    lengths, _, reason = probe_tails(candidate, role, routing, options, profile)
    if reason is not None:
        return 0.0
    return max(0.0, max(lengths.values()) - fit.TAIL_MAX_MM[options["template"]])


def reaching(chart: Any, bases: Sequence, options: Mapping[str, Any], profile: Mapping[str, Any], obstacles: Mapping[str, Any],
             per_base: list, tips: Any = None) -> list:
    """The ordered fields of ``bases`` with the caps (section 23): a capped field stacks at the far end from the exit, and
    when the first one's tails would pass the maximum (200 mm on the surface) the search runs again with its rows that
    much nearer the exit (``tip_reach_mm``, :func:`far_row`), at most :data:`REACH_ATTEMPTS` times; then the tip-first
    fields (:func:`tip_first`, section 26; ``tips`` gets its report)."""

    reach = None
    queue: list = []
    ranked: list = []
    for _ in range(REACH_ATTEMPTS):
        frames: list = []
        mine = options if reach is None else dict(options, tip_reach_mm=reach)
        ranked = ordered(search_fields(chart, bases, mine, profile, obstacles, frames), len(bases) > 1)
        queue = list(ranked)
        excess = tail_excess(queue[0], options, profile) if queue else 0.0
        if excess <= 0.0:
            break
        first = queue[0]
        reach = first["field_origin"][1] + (first["rows"] - 1) * first["pitch"] - excess
    per_base.extend(frames)
    if tip_on(options):
        # The tip-first fields (section 26) once the exit's fields are settled: one that cannot be built (its tails past
        # the maximum) gives its slot back to the field it displaced.
        queue = tip_first(ranked, options, tips)
    return queue


def fit_chart_field(mesh: Any, chart: Any, sides: Sequence, bases: Sequence, options: Mapping[str, Any], cache: Any = None) -> dict:
    """:func:`surface.fit.fit_chart` with ``containment: field``: the fields, ranked (:func:`ordered`) and realized best first.

    One proposal per readout and kind (full or masked, symmetric or not) and
    none that an earlier one dominates (:func:`surface.fill.proposal_shape`,
    :func:`surface.fill.dominated`); at most :data:`MAX_REALIZE` builds.
    """

    profile = fit.load_profile_cached(options["template"])
    obstacles = fit.surface_obstacles(mesh, chart, options)
    rejected: dict = {}
    per_base: list = []
    info: dict = {}
    tips: dict = {}  # per exit order: the tip passes' work and whether they completed (section 26)
    ranked = None
    if len(bases) == 1:
        queue = reaching(chart, bases, options, profile, obstacles, per_base, tips)
    else:
        ranked = ordered(search_fields(chart, bases, options, profile, obstacles, per_base, info), True)
        queue = list(ranked)
    pending: list = []  # the capped exits still to be searched on their own (section 23), in the reference's order
    later: list = []  # then the fields of the exits the reference has none on
    if info.get("capped"):
        # A cap binds on some exit (the user's, a reader's or the template's 64): the caps never choose the exit (section
        # 23).  Every exit the fit without any cap has fields on, each searched on its own with the caps (another exit's
        # larger fields would prune its fields: a symmetric exit's leave a leg of the right triangle none), in that fit's
        # exit order (its symmetric exits first within SYMMETRY_GAIN, sections 26.17 and 26.19: the symmetry judged on the
        # face without the caps); then the exits it has no field on.  Each exit is searched when the proposals reach its
        # fields (the work budget, section 26.18: one whose fields would follow the last proposal is not searched; the
        # proposals as with every exit searched first).
        free = uncapped(options)
        reference = ordered(search_fields(chart, bases, free, profile, obstacles, []), True)
        if reference:
            pending = own_exits(reference)
            if tip_on(options):
                queue = tip_first(ranked, options, tips, pending)
            later = keep_exits([candidate for candidate in queue if candidate["order"] not in pending], reference)
            queue = []
            ranked = None
    if ranked is not None and tip_on(options):
        # Several exits, no cap binding (or no reference): the tip-first fields of the fit's order (section 26).
        queue = tip_first(ranked, options, tips)
    proposals = []
    taken: list = []  # what a later field may be dominated by: the proposals, and each lead whose place its tie took
    shapes = set()
    built = 0
    index = 0
    tipped = tip_on(options)
    for candidate in queue:
        candidate.setdefault("root", id(candidate))  # what a peel came from (the tip-first field's displaced lead, section 26)
    ranks: dict = {}  # root -> the rank of its proposal
    places: dict = {}  # a displaced lead's root -> the rank of the proposal in its place (its zero-cost tie's, section 26.17)
    while built < MAX_REALIZE and len(proposals) < options["proposals"]:
        if index == len(queue):
            # The queue's end: the next capped exit searched on its own, then the exits the reference has no field on.
            if pending:
                order = pending.pop(0)
                own_tips: dict = {}
                more = reaching(chart, [bases[order]], options, profile, obstacles, [], own_tips)
                for candidate in more:
                    candidate["order"] = order
                if own_tips:
                    tips[order] = own_tips[0]
            elif later:
                more, later = later, []
            else:
                break
            for candidate in more:
                candidate.setdefault("root", id(candidate))
            queue.extend(more)
            continue
        candidate = queue[index]
        index += 1
        # One proposal per readout and kind of field (full or masked, symmetric or not: a larger asymmetric field of the
        # symmetric field's readout stays an alternative, P5-diagonal-bus.md section 22; a tip-first field and the field it
        # displaced, section 26).
        lead = bool(candidate.get("tip_lead"))
        shape = fill.proposal_shape(candidate["rows"], candidate["columns"], candidate["taxels"], None if candidate["full"] else True) + (bool(candidate["symmetric"]), lead)
        if candidate["root"] in places:
            # A lead whose zero-cost tie took its place (section 26.17): not proposed, its readout taken as it would have
            # been (the later proposals as without the tip step).
            shapes.add(shape)
            taken.append({"metrics": {"rows": candidate["rows"], "columns": candidate["columns"], "taxels": candidate["taxels"]}})
            continue
        if shape in shapes or fill.dominated(candidate["rows"], candidate["columns"], candidate["taxels"], taken):
            continue
        built += 1
        proposal, peeled = realize_field(candidate, chart, obstacles, options, profile, cache, rejected)
        if peeled is not None and lead and not tip_peel_holds(candidate["tip"], peeled):
            peeled = None  # the displaced field keeps its slot (it follows directly)
        if peeled is not None and candidate.get("tip_tie") and peeled["value"] < candidate["place"][1]:
            peeled = None  # a tie gives up no taxel: the lead takes its place back (it follows directly)
        if peeled is not None:
            queue.insert(index, peeled)
        if proposal is None:
            continue
        metrics = proposal["metrics"]
        found_shape = fill.proposal_shape(metrics["rows"], metrics["columns"], metrics["taxels"], design_mask(proposal["design"])) + (metrics["symmetry"]["field"], lead)
        if found_shape in shapes or fill.dominated(metrics["rows"], metrics["columns"], metrics["taxels"], taken):
            continue
        shapes.add(found_shape)
        shapes.add(shape)
        proposal["rank"] = len(proposals) + 1
        if tipped:
            metrics["tip"] = tip_metrics(candidate)
        ranks.setdefault(candidate["root"], proposal["rank"])
        if "place" in candidate and candidate["value"] >= candidate["place"][1]:
            places.setdefault(candidate["place"][0], proposal["rank"])
        proposals.append(proposal)
        taken.append(proposal)
    if not queue:
        # Not one crossing with the field margin fits the usable surface beside any exit: the reason the client shows.
        margin = float(profile["routing"]["active_edge_clearance_mm"])
        rejected[f"no taxel field fits the surface (a crossing and its {margin:g} mm field margin)"] = len(bases)
    for proposal in proposals:
        # The rank of the proposal in the place of the field a tip-first field displaced: its tie's, or its own (None when
        # neither was proposed).
        tip = proposal["metrics"].get("tip")
        if tip is not None:
            root = tip.pop("displaced_root")
            tip["displaced"] = None if root is None else places.get(root, ranks.get(root))
    for base in per_base:
        # The tip passes' work per exit (its unturned frame's record; section 26).
        held = tips.get(next((order for order, side in enumerate(bases) if side["index"] == base["side"]), None))
        if held is not None and base["angle_deg"] == 0.0:
            base["tip_work"] = held["work"]
            base["tip_complete"] = held["complete"]
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


# --------------------------------------------------------------------------
# The map with containment: field
# --------------------------------------------------------------------------


def verify_field(mesh: Any, chart: Any, frame: Any, exits: Any, outlines: Mapping[str, Sequence], records_out: Sequence, mapped: Sequence,
                 result: Mapping[str, Any], misses: int, options: Mapping[str, Any], origin: Sequence[float]) -> tuple:
    """The map's records with ``containment: field`` and its ``routing_on_surface`` report: ``(records, report)``.

    Required (the records of :func:`surface.place.verify` that do not
    depend on the containment, and these): ``field_clearance``, F less the
    corner squares at its convex corners (P and the margin along F's sides,
    :func:`field_parts`) on the surface clear of its edge (the exit
    included), holes and obstacles by the edge margin;
    ``field_corner_overhang``, how far those corner squares leave that, at
    every convex corner of F (at most :data:`CORNER_TOLERANCE_MM`,
    :func:`corner_overhang`, :func:`corner_zones`); ``strain_under_field`` and
    ``field_bend_radius`` under F less its corner squares; each tail's end at least 6.5 mm beyond the surface below it (beside
    the surface, beyond the base side's line continued).  Reported: per board its share on the surface and its
    overhang (:func:`routing_report`), the strain and the tightest bend
    under the boards, and warnings: ``W_BAND_EDGE_RADIUS`` where a board
    crosses an edge of the surface, a side or the base edge, that bends
    tighter than a single FPC may (10 x 0.11 mm; :func:`edge_warnings`),
    ``W_ROUTING_HOLE``, ``W_ROUTING_COVERED``,
    ``W_ROUTING_BEND`` and ``W_ROUTING_STRAIN`` where a board lies over a
    hole, a covered wall, a bend tighter than that or a facet stretched
    beyond the strain limit.
    """

    from . import place

    design = result["design"]
    shared = place.verify(mesh, chart, frame, exits, outlines, records_out, mapped, design, misses, options)
    by_rule = {record["rule"]: record for record in shared}
    obstacles = fit.surface_obstacles(mesh, chart, options)
    field_margin = float(result["profile"]["routing"]["active_edge_clearance_mm"])
    parts = field_parts(result, origin)
    outline = [frame.to_base(p) for p in chart.outline()]
    region = fit.ExitOutline(outline, [])
    clearance = parts_clearance(parts, region, frame, chart, obstacles, options["edge_margin_mm"])
    overhang = corner_overhang(corner_zones(result, origin), region, frame, obstacles, options["edge_margin_mm"])
    limit = options["strain_limit"]
    field_limit = fit.STATIC_BEND_FACTOR * fit.STACK_THICKNESS_MM
    board_limit = fit.STATIC_BEND_FACTOR * fit.SINGLE_FPC_MM
    records = [by_rule[rule] for rule in ("taxels_on_surface", "taxel_surface_distance", "neighbour_spacing_error")]
    records.append({
        "rule": "field_clearance",
        "required": place._r(options["edge_margin_mm"]),
        "measured": None if clearance is None else place._r(clearance, 9),
        "comparison": "min>=",
        "unit": "mm",
        "passed": clearance is not None,
        "what": f"the taxels (P) and the {field_margin:g} mm margin along the taxel field's sides (F less the corner squares at its convex corners) lie on "
                "the surface, clear of its edge (the exit included), holes and obstacles",
    })
    records.append(place._record("field_corner_overhang", CORNER_TOLERANCE_MM, overhang, "max<=", "mm",
                                 f"F's convex corners (its {field_margin:g} mm margin beyond the taxels' corners) leave the surface by at most "
                                 f"{CORNER_TOLERANCE_MM:g} mm"))
    records.append(place._record("strain_under_field", limit, place._strain_under(chart, mesh, frame, parts), "max<=", "ratio",
                                 "the sheet does not stretch beyond the limit under the taxel field (F less its corner squares)"))
    records.append(place._record("field_bend_radius", field_limit, min(place._min_bend_radius(mesh, chart, frame, part, field_limit) for part in parts),
                                 "min>=", "mm", "static bend of the laminated field (10 x 0.47 mm) under F less its corner squares"))
    records += [by_rule["tail_top_length_mm"], by_rule["tail_bottom_length_mm"]]
    lowest = bottoms(outline)
    for key in ("row", "column"):
        records.append(place._record(f"{key}_tail_reach", fit.TAIL_REACH_MIN_MM, tail_reach(lowest, outlines[key], frame), "min>=", "mm",
                                     "the tail's stiffened end (6.0 + 0.5 mm) lies off the surface: beyond its edge below it (beside the surface, "
                                     "beyond the base side's line continued)"))
    holes = [[frame.to_base(p) for p in hole] for hole in obstacles["holes"]]
    space = _MapFrame(outline, exits)
    report = routing_report(outlines, space, holes, tails_of(result, origin), frame)
    strain = by_rule["strain_under_boards"]["measured"]
    bend_radius = by_rule["board_bend_radius"]["measured"]
    report["strain_max"] = strain
    report["bend_radius_min_mm"] = bend_radius
    warnings = edge_warnings(mesh, chart, frame, outlines, exits.exit_edges, board_limit)
    for key in ("row", "column"):
        polygon = list(outlines[key])
        for code, kind, what in (("W_ROUTING_HOLE", "holes", "a hole of the selection"),
                                 ("W_ROUTING_COVERED", "covered", "a covered wall (another part touches the surface there)")):
            polygons = holes if kind == "holes" else [[frame.to_base(p) for p in item] for item in obstacles[kind]]
            count = 0
            for other in polygons:
                if len(other) >= 3 and _polygons_overlap(polygon, other):
                    count += 1
            if count:
                warnings.append({"code": code, "board": key, "count": count, "message": f"The {key} board lies over {count} x {what}."})
    if bend_radius is not None and bend_radius < board_limit - 1e-12:
        warnings.append({"code": "W_ROUTING_BEND", "board": None, "measured_mm": bend_radius, "limit_mm": place._r(board_limit),
                         "message": f"A board lies over a bend of {bend_radius:g} mm, tighter than a single FPC's {board_limit:g} mm."})
    if strain is not None and strain > limit + 1e-12:
        warnings.append({"code": "W_ROUTING_STRAIN", "board": None, "measured": strain, "limit": limit,
                         "message": f"A board lies over facets the flattening stretches by {strain:g}, beyond the strain limit {limit:g}."})
    report["warnings"] = warnings
    return records, report


class _MapFrame:
    """What :func:`routing_report` reads of a frame in the map: the outline and the exits' ``exit_y``."""

    def __init__(self, outline: Sequence, exits: Any) -> None:
        self.outline = list(outline)
        self.exit_y = exits.exit_y


def tail_reach(lowest: Any, polygon: Sequence, frame: Any = None) -> float:
    """How far a tail's end lies beyond the surface's lowest edge under it, or for a tail beside the surface beyond the
    base side's line continued beside it (:func:`bottom_beside`)."""

    tip = min(p[1] for p in polygon)
    xs = [p[0] for p in polygon if p[1] <= tip + 0.5]
    left, right = min(xs), max(xs)
    reach = math.inf
    steps = 8
    for k in range(steps + 1):
        x = left + (right - left) * k / steps
        y = lowest.exit_y(min(max(x, left + 1e-9), right - 1e-9) if right > left else x)
        if y is not None:
            reach = min(reach, y - tip)
    if reach == math.inf:
        reach = bottom_beside(lowest, left, right, frame) - tip
    return reach


def edge_warnings(mesh: Any, chart: Any, frame: Any, outlines: Mapping[str, Sequence], exit_edges: Any, limit: float) -> list:
    """``W_BAND_EDGE_RADIUS`` per board that crosses an edge of the surface bending tighter than ``limit``.

    Every boundary segment the board's outline crosses counts, the base edge
    (an exit) included: under field-only containment the bands, the Row
    bus's fans and the Column fan-out leave the surface there, not only the
    tails.
    The bend at a segment is the tightest of the mesh edge between the
    selected facet and its neighbour outside the selection
    (:func:`surface.bend.edge_radius`) and of the edges up to
    :data:`WRAP_RINGS` facets beyond it (a fillet: its first edge shows
    about twice its radius, its inner ones the radius); a free edge (no
    neighbour) does not bend.  The warning names the tightest side edge and
    the tightest base edge separately (``side_mm``, ``base_mm``, None when the
    board crosses none) and says what to do.
    """

    from . import bend

    loop = chart.loops[chart.outer]
    count = len(loop)
    outline = [frame.to_base(chart.uv[v]) for v in loop]
    in_chart = set(chart.facets)
    owner: dict = {}
    for facet in chart.facets:
        vertices = mesh.facets[facet]
        for k in range(3):
            owner.setdefault(frozenset((vertices[k], vertices[(k + 1) % 3])), []).append(facet)
    radii: dict = {}
    warnings = []
    for key in ("row", "column"):
        polygon = list(outlines[key])
        index = fit._SegmentIndex([(polygon[k - 1], polygon[k]) for k in range(len(polygon))])
        smallest = {"side": math.inf, "base": math.inf}
        crossed = 0
        for i in range(count):
            a, b = outline[i], outline[(i + 1) % count]
            hit = point_in_polygon(a, polygon) or point_in_polygon(b, polygon) or any(
                segments_intersect(a, b, c, d) for c, d in index.near(a, b, 0.0)
            )
            if not hit:
                continue
            kind = "base" if i in exit_edges else "side"
            u, v = loop[i], loop[(i + 1) % count]
            for facet in sorted(owner.get(frozenset((u, v)), ())):
                for other in sorted(mesh.neighbors[facet]):
                    if other in in_chart or u not in mesh.facets[other] or v not in mesh.facets[other]:
                        continue
                    crossed += 1
                    if (facet, other) not in radii:
                        radii[(facet, other)] = _wrap_radius(mesh, facet, other, in_chart, limit, bend)
                    smallest[kind] = min(smallest[kind], radii[(facet, other)])
        tightest = min(smallest.values())
        if tightest < limit - 1e-12:
            sharp = {kind: (round(value, 6) if value < limit - 1e-12 else None) for kind, value in smallest.items()}
            where = " and ".join(f"{'the base edge' if kind == 'base' else 'a side edge'} ({value:g} mm)"
                                 for kind, value in (("base", sharp["base"]), ("side", sharp["side"])) if value is not None)
            title = "Row" if key == "row" else "Column"
            advice = ("keep the board flat where it leaves the surface (run it straight off the edge, do not fold it around), "
                      "or give the part's edge a radius of at least " f"{limit:g} mm")
            warnings.append({
                "code": "W_BAND_EDGE_RADIUS", "board": key, "edges": crossed, "measured_mm": round(tightest, 6), "limit_mm": round(limit, 6),
                "side_mm": sharp["side"], "base_mm": sharp["base"],
                "message": f"The {title} FPC crosses {where} of the surface, sharper than a single FPC can wrap ({limit:g} mm, "
                           f"10 x 0.11 mm): {advice}.",
            })
    return warnings


def _wrap_radius(mesh: Any, facet: int, other: int, in_chart: Any, limit: float, bend: Any) -> float:
    """The tightest bend from a selected facet across a boundary edge into its outside neighbour and up to
    :data:`WRAP_RINGS` facets beyond it (breadth first over facets outside the selection)."""

    smallest = bend.edge_radius(mesh, facet, other, limit)
    seen = {facet, other}
    ring = [other]
    for _ in range(WRAP_RINGS):
        following = []
        for current in ring:
            for nxt in sorted(mesh.neighbors[current]):
                if nxt in seen or nxt in in_chart:
                    continue
                seen.add(nxt)
                smallest = min(smallest, bend.edge_radius(mesh, current, nxt, limit))
                following.append(nxt)
        ring = following
    return smallest


def _polygons_overlap(first: Sequence, second: Sequence) -> bool:
    """Whether two simple polygons overlap: a vertex of one inside the other, or crossing edges."""

    if any(point_in_polygon(p, first) for p in second) or any(point_in_polygon(p, second) for p in first):
        return True
    return any(segments_intersect(first[k - 1], first[k], second[m - 1], second[m]) for k in range(len(first)) for m in range(len(second)))
