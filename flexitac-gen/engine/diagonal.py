"""The diagonal Row bus: the construction ``diagonal-bus/11`` (``routing.row_sides``).

A design whose ``routing.row_sides`` is ``left``, ``right`` or ``both`` (as
seen from outside the stack with the tails down) is built here instead of
with the straight Row channel (``channel``), masked or not, on either
template: the surface template (CAD mode) and the generic one, the
rectangular generator, whose default it is
(claude/specs/masked-field/P5-diagonal-bus.md, phase P5b and sections
12-20).  Both templates build it with one rule set, the surface profile's
(``engine.core.rules_template``: the rectangular generator's bus is CAD
mode's, section 20), so one design builds the same boards on either.
Every row trace runs as a slant from its electrode's end, hugging the
field's boundary; below the field it turns once into a fan and once more
into its contact, and runs straight down the tail.  Outside the taxel field
the two boards overlap freely (two separate FPCs on either side of the
film), their tails too: the tails are stacked, one on the other where they
meet, and part to their own connectors.  Only the field and each board's
own rules constrain them.  Both boards have one outline in the stack down
to their tail roots (the union of their bodies), so the films align by
their edges; only the tails differ.

The Row board's canonical frame is the one of :mod:`engine.layout` (tail
down, slot 0 on the Row-channel side), with the field's lower-left corner at
the origin.  Its *near* side (x < 0) is the side of ROW_01's lane, its *far*
side the other one.  ``both`` puts ROW_01, 03, 05, ... on the near side and
ROW_02, 04, ... on the far side (the alternate split); one side puts every
row on it, and the side opposite the near one is built in the mirrored frame
(``_Geo.flip``) and turned back.

- **Bands** (integer nanometres, :mod:`engine.bus`): each side is an onion
  of west convex chains (:func:`engine.bus.west_chain`), innermost first,
  around the keep-out K (every Row window and every stacked Column window
  grown by the window clearance; the stacked Column copper is none, the
  boards overlapping outside the field) and the keep-out of the lane
  inside it (:func:`engine.bus.lane_keepout`); a lane is exempt from K
  inside its own zone (its electrode grown by the coverlay expansion and
  the window clearance) and keeps east of the zone's outer-bottom corner:
  diagonal-bus/1's onion.  On a receding field (a field narrowing toward
  its bottom edge beside a lane) the lane follows the field inward: its
  chain runs around what it must avoid down to the field's bottom edge, as
  far in as the keep-out below that edge and the lanes inside it allow and
  no flatter than the taper cap, then straight down, the lanes nested at
  the bundle pitch (:func:`engine.bus.lane_offset`).  Elsewhere its inner
  lanes turn down up to 0.3 mm below the field (the bottom row's zone
  reaches that far below it); :func:`_cut_at_field` turns every lane down
  on the field's bottom edge instead, where its band crosses it (or just
  outside K there), so above the field the bands of a field that does not
  recede and the tip are diagonal-bus/1's, and no lane bends below the
  field before its fan.
- **Row tail** (diagonal-bus/10, the user's request of
  P5-diagonal-bus.md section 27): centred on the field's width in every
  side mode, as the Column tail is (``tail_position`` ``centred``): within
  the sensor's width wherever it is narrower than the field, centred on it
  where it is wider.  The rows take its contacts from its canonical left
  (positions 1..R), so with ``both`` and a contact per row its near and far
  contacts part on the field's centre line (half a contact pitch east of it
  for an odd row count; a reader tail's unused contacts lie east of the
  rows'), and with one side the whole bundle fans inward under the field.
  Mirrored, the rows take the contacts at the tail's far end (turned back
  they are positions 1..R).  The contact order folds with ``both`` (ROW_01,
  03, ..., 04, 02).  Its own root lies just below the fans' junctions; the
  tail leaves the shared body's bottom edge (below).
- **Fans** (:func:`_plan_fans`): the lanes of a side, in contact order, form
  runs that move the same way (toward or away from the tail's middle; a
  lane straight above its contact runs on down).  A run is a bus of
  parallel lines at one cap of the profile's ``fanout`` caps (whole
  degrees of 60-85 from the vertical), never within
  ``ENTRY_ANGLE_GUARD_DEG`` of the Column fan-out's entry angle, so no fan
  runs along the Column fan-out's diagonals (it crosses them at 5 degrees or
  more), the one whose junction lies highest: its front lane (the farthest
  along the move) turns at ``y_hug`` and each
  lane behind it one bundle pitch farther back, so every lane bends twice
  below the field, into its fan and into its contact.  With ``both`` the two
  sides' runs meet under the field in a V (a funnel), one side's run fans
  inward under it (half a funnel), crossing the Column fan-out at any
  angle.  The vertical rays and contact columns may
  lie over the Column board's traces outside the field (its fan-out and its
  tail, under the Row tail): reported by the registration
  (``trace_overlap_mm``), as every overlap outside the field, not avoided.
- **Column board**: the straight Column board of the same design without
  ``routing.row_sides`` (:func:`engine.layout._masked_column_board` on the
  design with its mask written out): its copper, and its tail centred under
  its fan-out, no shift, no neck, no stub drop, in every side mode; it
  differs from that board in the classes it records
  (``construction.mask_class``), for an unmasked design in carrying the
  masked records, and in its outline (below).  It converges in one V
  straight into its contacts (the profile's one lane).  **The Column V
  rule** (diagonal-bus/8, P5-diagonal-bus.md section 20.1): the
  construction plans the Column board twice, its V at the profile's
  whole-degree caps up to ``COLUMN_V_CAP_DEG`` (80 degrees from the
  vertical, :func:`column_profile`) and at the profile's own (60-85),
  arranges the Row fans for each (off its entry angle by
  ``ENTRY_ANGLE_GUARD_DEG``), and takes the one whose tails root higher:
  the deeper of its two boards' own roots (the Row funnel's, just below
  the fans' junctions; the Column V's), compared before the level is
  lowered below the union's fillets; a tie (within a nanometre) takes the
  capped V, a plan that cannot be arranged is passed over.  The capped V
  leaves the fans 85 degrees: with ``both`` the funnel's (the default 12 x
  32: its tails 5.866 mm below the field, 9.494 mm with the V at 82 and the
  fans at 76) and, since the Row tail is centred (diagonal-bus/10), one
  side's run inward under the field (6.282 against 11.040 mm; under the
  band the single fan gained nothing and the profile's V rooted higher,
  5.214 against 5.866 mm).  Measured with diagonal-bus/8 on 433 builds (the
  named generic designs and the CAD cases in every side mode, the design
  workflow judge's 400): the two Vs differ on 258 and the rule takes the
  capped one on 126; a V always capped would root the tails deeper on 132
  (by 0.73 mm in the median, up to 4.27 mm), the rule does so on 9 against
  a V never capped (0.04 mm, up to 0.27 mm: the choice is made before the
  level is lowered) and roots them higher on 76 (1.01 mm, up to 5.13 mm).
- **Outline**: y-monotone, the exact envelope of the field's margin slabs
  and the outermost lanes' envelopes, never narrowing below the tip down to
  its widest level, and from the tail up to there (the funnel's V); one
  side's inner flank follows the field down to its bottom and steps once
  straight down into a tail narrower than F's bottom; a tail side beyond
  the envelope above it (beside the outer lanes, or a tail wider than F's
  bottom under one side's inner flank, diagonal-bus/10) slants out to it
  from F's bottom at the highest, or steps out once where that would lie
  flatter than 45 degrees (just above the tail, or at F's bottom on the
  inner flank); the fillets of every board.
- **Chamfered notches** (:func:`_hull_sides`, diagonal-bus/6, the user's
  decision of P5-diagonal-bus.md section 16): a masked field's sides are
  taken as F's convex hull where F's staircase between two corners of the
  hull lies no deeper inside the hull's edge than a step of
  ``CHAMFER_STEP_CELLS`` (2) cells (cells missing at a corner, a rounded
  face's notch: a chamfer, or a polygon following F); a deeper pocket (a
  narrow tip over a much wider row) keeps its staircase.  The chamfer's
  ends are F's corners, so it lies on or outside F and every clearance to
  the outline only grows; the shared outline carries it on both boards.
- **One outline down to the tail roots** (:func:`_share_outline`,
  diagonal-bus/8, the user's decision of P5-diagonal-bus.md section 20):
  both tails leave one bottom edge, the deeper of the two boards' own tail
  roots, or lower where the outline's fillets into the tails reach below it
  (the shallower tail's root moves down to it, its contact columns running
  on straight; the tails keep their widths and positions, each its length
  below that root).  From the tip down to that level both boards take the
  union of their own outlines before their fillets, in the stack, filled
  across at every height (the field, the Row bands and funnel, the Column
  fan-out: each board gains blank film where only the other has copper),
  made regular and filleted once (a board's own corner that is the union's
  gets the fillet it has on its own); below it each board is its own tail,
  stepping in along that level (or, below the other board's fillet into a
  tail wider than its body, a fillet radius lower).  Where a tail is flush
  with the union's side (its side the union's down to the level: a tail
  wider than the body above it, or, before diagonal-bus/10, one side's Row
  tail under the band), the side meets the tail's edge on the level
  straight or at a filleted corner
  (:func:`_union_above`): the union's points on the level stay while it is
  made regular, it runs on below the level along that tail's side
  (:func:`_flush`), and a tail's root corner its side meets at a slant
  stays a corner of the union (:func:`_root_corners`), filleted on both
  boards with the level below that fillet; no step a few micrometres
  wide at the level.
  ``construction.row_bus.shared_outline_below_field_mm`` and the Column
  board's ``construction.shared_outline_below_field_mm`` record the level
  (the tail roots' depth below the field); the registration checks that
  the outlines coincide down to it.
- **Regular outlines** (:func:`_regular`): no vertex of either outline
  turns by less than ``REGULAR_TURN_DEG`` (5 degrees) but on a fillet or
  the tail.  Between two corners (a turn of 5 degrees or more, a fillet's
  vertex, the tail from its root down) a run of flatter turns becomes one
  straight edge on or outside every vertex of the run (the outer hull edge
  over the middle of its chord: the least added area), joined to the edges
  beside it where their lines meet; a long smooth curve becomes a polygon
  whose corners turn by 5 degrees or more.  Each board's own outline is
  made regular, and the union of the two again (the crossings of nearly
  parallel sides; its points on the shared level and below it, and the
  tails' root corners a side meets at a slant, stay) before it is
  filleted, so both boards carry one regular outline; the union's sides run
  on below the shared level along a flush tail's side, else along their
  last edge.  The copper is not touched: every clearance to the outline
  only grows.
- **Straight sides** (:func:`_straight_sides`, diagonal-bus/7, the user's
  request of P5-diagonal-bus.md section 17): on each side of the union,
  made regular, the stretch from the tip corner down to the side's widest
  point becomes one straight line (through the widest point, tangent to
  the stretch; the tip corner moves out along the top edge to meet it), and
  the stretch from there down to the shared level the chord, wherever the
  line lies no more than ``SIDE_STRAIGHTEN_MM`` (1.0 mm) outside the old
  side anywhere (the old side as the boards have it, its concave corners
  filleted: a staircase's sharp inner corners lie deeper than its
  fillets, diagonal-bus/8), meets each board's own side below that level
  straight on or convex by ``REGULAR_TURN_DEG`` or more, and leaves the
  widest point a corner of that turn or more.  A curved side (a disk, a
  long receding side) keeps its polyline.  The old outline lies inside the
  new one, so every clearance only grows; the widest point stays, so the
  board is no wider.
- **Convex sides** (:func:`_convex_sides`, diagonal-bus/9, the user's
  request of P5-diagonal-bus.md section 24): then, on each side, the
  stretch from the tip corner down to the widest point becomes its convex
  hull (field F and the lanes): each dent between two corners of the hull
  (the S-shaped kink where the lanes start beside a narrow tip, a short
  step) becomes the hull's edge wherever it lies no deeper inside that
  edge than a step of ``CHAMFER_STEP_CELLS`` cells (2 p / sqrt 5, the depth
  to which F's notches are chamfered) and the tip corner and the widest
  point stay corners of ``REGULAR_TURN_DEG`` or more; a deeper pocket keeps
  its outline.  A slanted side down a staircase is then one straight line
  from the tip corner to its convex bend into the funnel; that bend (the
  lanes turning down beside the field's widest rows) lies on the hull and
  stays, as does the funnel arm.  The widest point stays (the tip corner
  moves out along the top edge only where a corner of the hull flatter than
  ``REGULAR_TURN_DEG`` merges), every clearance only grows, no board is
  wider.
- **Convex flank** (:func:`_convex_flank`, diagonal-bus/11, the
  multi-gripper video's notch of P5-diagonal-bus.md section 27.8): with one
  side, the side without lanes came down the field's side and stepped in
  just below the field (the Column board's body corner, its ledge in to
  its outermost route and that route's turn into the V) before it sloped to
  the centred tail.  Before the convex sides, its stretch from the field's
  outline corner (on F's bottom) down to the last convex corner before the
  junction into the tail becomes its convex hull wherever no anchor lies in
  a dent and every corner stays ``REGULAR_TURN_DEG`` or more (a bridge
  meeting an edge flatter moves along that edge's line to meet it at a
  degree more), and, as filleted, the side's straight run down a tail's
  edge and the old flank stay (on or inside the new one), so the tails'
  roots and the copper do not move; no depth bounds it.  With both sides the
  lanes cover either side.

Both boards carry the masked records (``grid_registration.taxel_mask``,
full spans for the rectangle), so DRC records 11-15 apply in their masked,
strict form; the Row board's ``construction.row_bus`` names the
construction and its measurements (with ``tails``: ``stacked``, and the
shared outline's level), and ``tail.row_contact_order`` the nets of its
contacts.

The pair is built once: :func:`build_row_board` and
:func:`build_column_board` share a small cache of the pair, keyed on the
design and the profile.  A construction that cannot order its lanes raises
:class:`RowBusInfeasible` (``E_ROW_BUS_INFEASIBLE``).
"""

from __future__ import annotations

import functools
import json
import math
from typing import Any, Mapping

from . import bus
from .bus import to_mm, to_nm
from .geometry import (
    band_union,
    ceil6,
    clean_polyline,
    clip_ring_above,
    fillet_concave_corners,
    floor6,
    offset_polyline,
    point_in_polygon,
    point_segment_distance,
    polygon_edges,
    rect_union_slabs,
    ring_deviation,
    round6,
    segment_distance,
)
from .layout import (
    Rules,
    _assemble,
    _column_top_chain,
    _contacts,
    _electrode,
    _junction_drop,
    _mark_masked,
    _masked_column_board,
    _masked_field_window,
    _round_ring,
    _route_pieces,
    _row_spans,
    _tip_corners,
    board_metrics,
    bundle_values,
    column_frame_spans,
    column_plan,
    connector_pins,
    masked_column_outline,
    matrix_values,
    row_frame_spans,
    tail_length_for_role,
    tail_width,
)
# The construction's version, added to the build identity of every design built as the bus (routing.row_sides one of
# ROW_SIDES) on either template; changing any constant below bumps it.  diagonal-bus/8 (P5-diagonal-bus.md section 20):
# the rectangular generator's bus built by CAD mode's rule set (engine.core.rules_template), one outline for both boards
# down to their tail roots, the Column V capped at COLUMN_V_CAP_DEG.  diagonal-bus/9 (section 24): convex sides
# (_convex_sides), each side's dents from the tip corner down to its widest point bridged by its hull.  diagonal-bus/10
# (section 27, the user's request: tails within the sensor's width): the Row tail centred on the field in every side
# mode, as the Column tail, and one side's inner flank slanting out below F's bottom to a tail wider than F's bottom.
# diagonal-bus/11 (section 27.8, the video's notch: "更加clean和直接"): one side's flank without lanes convex from the
# field's outline corner down to the tail (_convex_flank), the Column fan-out's notch below that corner bridged.
ROW_BUS_VERSION = "diagonal-bus/11"
# The values of routing.row_sides that build the bus; CHANNEL builds the straight Row channel (engine.layout) and is
# accepted on every template (P5-diagonal-bus.md section 18).
ROW_SIDES = ("left", "right", "both")
CHANNEL = "channel"
# The Column V rule (P5-diagonal-bus.md section 20.1; the module's docstring): the Column board's V is planned at the
# profile's whole-degree taper caps up to this (degrees from the vertical, :func:`column_profile`) and at the profile's
# own; _build takes the plan whose tails root higher (the deeper of the two boards' own roots, before the level is
# lowered below the union's fillets; ties, equal on the layout grid: the capped one).  The capped V leaves the Row fans
# the profile's steepest cap (85 degrees) outside ENTRY_ANGLE_GUARD_DEG of its entry angle (on the default 12 x 32 a V at
# 82 degrees left the fans 76 and the tails 3.6 mm deeper with both); since the Row tail is centred (diagonal-bus/10) one
# side's fans run inward under the field and gain from it too (the default one-sided: 4.8 mm higher).
COLUMN_V_CAP_DEG = 80.0
# ``both``: odd rows on the near side, even rows on the far side.
SPLIT = "alternate"
# The tails lie one on the other where they meet (construction.row_bus.tails), each board's tail where its own
# construction puts it: the Column tail centred under its fan-out, the Row tail centred under the field (diagonal-bus/10).
TAILS = "stacked"
# A fan runs at no taper cap within this of the Column fan-out's entry angle (degrees), so no fan runs along the
# Column fan-out's diagonals: it crosses them at this angle or more.
ENTRY_ANGLE_GUARD_DEG = 5.0
CLASSES = {"row": "diagonal", "column": "straight"}
# One layout-grid step (the trace-to-window and trace-to-copper clearances keep it beyond their rules).
_GRID_STEP_MM = 1e-6
# Floating-point guard for comparisons of distances built exactly (not a manufacturing rule).
_NOISE_MM = 1e-9
# Parallel fan lanes keep the bundle pitch plus this (grid steps: the rounding of their bends to the grid).
_FAN_ALLOWANCE_MM = 4e-6
# The bands' rays run down to this depth below the field for the hull work (a construction depth).
_DEEP_NM = 1_000 * bus.NM
# A lane follows a receding field inward (turns down on the field's bottom edge east of its westmost obstacle) only
# where that moves its ray inward by more than this (nm), so the grid noise of the offsets never moves a lane.
_HUG_MIN_NM = 1_000
# The taper cap's run per unit rise is taken in millionths (floored).
_RUN_SCALE = 1_000_000
# Pairs kept by the pair cache.
_PAIR_CACHE_SIZE = 16
# The tails' roots are lowered below the boards' fillets into their tails at most this often (_build: one pass lowers
# them, the next confirms; the fillets do not depend on the roots below them).
_LEVEL_PASSES = 3
# While the shared outline is filleted its sides run on straight down this far below its level (a construction depth:
# four fillet radii of the profile, the rolling circle's reach).
_SHARED_RUN_MM = 2.0
# A vertex of the shared outline is a corner to fillet only where a fillet would leave the corner's grid step: it turns
# by more than this many grid steps per fillet radius (rad x mm).  Flatter ones (the envelope's crossings of nearly
# parallel sides, micro-radians) keep their vertex; their rolling circle is ill-conditioned, and Python 3.9's and 3.12's
# last bits once recorded different radii for the same outline.
_SHARED_MIN_TURN = 2 * _GRID_STEP_MM
# Regular outlines (diagonal-bus/5): a vertex of a board's outline turning by less than this (degrees) is no corner.
# Between two corners (a turn of this or more, a fillet's vertex, the tail) a run of flatter turns becomes one straight
# edge outside it (_regular).
REGULAR_TURN_DEG = 5.0
_REGULAR_TURN = REGULAR_TURN_DEG * math.pi / 180
# Chamfered notches (diagonal-bus/6): a masked field's staircase between two corners of F's convex hull becomes the
# hull's edge where no corner of it lies deeper inside that edge than a step of this many cells across one row does
# (2 p / sqrt 5: notches of one or two cells per row or rows per cell; a wider step, a narrow tip over a wide row, stays).
CHAMFER_STEP_CELLS = 2
# Straight sides (diagonal-bus/7): on each side of the shared outline the stretch from the tip corner down to the widest
# point, and from there down to the shared level, becomes one straight line where one line encloses it lying no more than this
# (mm) outside it anywhere (_straight_sides).
SIDE_STRAIGHTEN_MM = 1.0


class RowBusInfeasible(ValueError):
    """The diagonal Row bus cannot order or place its lanes (``E_ROW_BUS_INFEASIBLE``)."""


def row_sides(design: Mapping[str, Any]) -> Any:
    """``routing.row_sides`` of a design built as the bus (one of :data:`ROW_SIDES`), or ``None`` (the straight Row
    channel: :data:`CHANNEL`, or no value)."""

    routing = design.get("routing") if isinstance(design, Mapping) else None
    sides = routing.get("row_sides") if isinstance(routing, Mapping) else None
    return sides if isinstance(sides, str) and sides in ROW_SIDES else None


def column_profile(profile: Mapping[str, Any]) -> Mapping[str, Any]:
    """The profile a bus design's Column board is planned with: ``profile`` with its fan-out's taper cap at most
    :data:`COLUMN_V_CAP_DEG` (the V's whole-degree caps of the profile up to it; every other rule the profile's)."""

    fanout = profile["fanout"]
    if float(fanout["maximum_taper_angle_deg"]) <= COLUMN_V_CAP_DEG:
        return profile
    return {**profile, "fanout": {**fanout, "maximum_taper_angle_deg": COLUMN_V_CAP_DEG}}


def near_side(design: Mapping[str, Any]) -> str:
    """The side of ROW_01's lane with ``both`` (the Row board's canonical left), as seen from outside the stack with
    the tails down.

    The stack shows the bottom board as built and turns the top board over:
    ``right`` when the Row board is on top, else ``left``.
    """

    return "right" if design["role_mapping"]["top"] == "rows" else "left"


def build_row_board(design: Mapping[str, Any], profile: Mapping[str, Any]) -> dict[str, Any]:
    """The Row board of a ``routing.row_sides`` design, in its canonical frame (tail down)."""

    return _pair(design, profile)["row"]


def build_column_board(design: Mapping[str, Any], profile: Mapping[str, Any]) -> dict[str, Any]:
    """The Column board of a ``routing.row_sides`` design, in its canonical frame (tail down)."""

    return _pair(design, profile)["column"]


def _pair(design: Mapping[str, Any], profile: Mapping[str, Any]) -> dict[str, Any]:
    key = json.dumps([design, profile], sort_keys=True, separators=(",", ":"), allow_nan=False)
    return json.loads(_pair_text(key))


@functools.lru_cache(maxsize=_PAIR_CACHE_SIZE)
def _pair_text(key: str) -> str:
    """Both boards of a design as JSON text (each caller gets its own copy)."""

    design, profile = json.loads(key)
    row, column = _construct(design, profile)
    return json.dumps({"row": row, "column": column}, separators=(",", ":"), allow_nan=False)


# --------------------------------------------------------------------------
# The Row frame.
# --------------------------------------------------------------------------


class _Geo:
    """The geometry of a design in the Row frame (the field's lower-left corner at the origin, the near side west).

    ``flip``: the frame is the Row board's canonical frame mirrored about the
    field's centre line (the one-sided bus on the far side), so the near side
    is still west.  ``one_sided``: every lane on the near side, the east side
    the inner flank.
    """

    def __init__(self, design: Mapping[str, Any], rules: Rules, flip: bool) -> None:
        self.rules = rules
        self.flip = flip
        # One side: every lane on the near side (west), the east side the inner flank.
        self.one_sided = row_sides(design) != "both"
        # The fans' taper caps (the profile's, rad, ascending) and the steepest of them.
        self.caps = list(rules.taper_caps)
        self.cap = self.caps[-1]
        self.R, self.C, self.px, self.py, self.cw, self.rw = matrix_values(design)
        self.tw, self.ts, self.bp = bundle_values(design)
        self.aw = round6((self.C - 1) * self.px + self.cw)
        self.ah = round6((self.R - 1) * self.py + self.rw)
        spans = row_frame_spans(design)
        if flip:
            spans = [(self.C - 1 - hi, self.C - 1 - lo) for lo, hi in spans]
        self.spans = spans  # per ROW_k (k - 1): (lo, hi) slots of this frame
        # Trace centre to any window ring, to other copper's edge (this board), and to the outline.
        self.c_win = ceil6(rules.opening_to_trace + self.tw / 2 + _GRID_STEP_MM)
        self.c_cu = ceil6(self.ts + self.tw / 2 + _GRID_STEP_MM)
        self.env = ceil6(rules.copper_to_edge + self.tw / 2 + rules.offset_allowance)
        overhang = rules.overhang
        self.rows = []
        for k in range(1, self.R + 1):
            lo, hi = spans[k - 1]
            y0 = round6((self.R - k) * self.py)
            self.rows.append({
                "k": k, "lo": lo, "hi": hi, "y0": y0, "y1": round6(y0 + self.rw), "yc": round6(y0 + self.rw / 2),
                "L": round6(lo * self.px - overhang), "Rt": round6(hi * self.px + self.cw + overhang),
            })
        # The Column slots of this frame: the rows holding each.
        self.slots = []
        for slot in range(self.C):
            holding = [row["k"] for row in self.rows if row["lo"] <= slot <= row["hi"]]
            top, bottom = min(holding), max(holding)
            x0 = round6(slot * self.px)
            self.slots.append({
                "x0": x0, "x1": round6(x0 + self.cw),
                "yb": round6(self.rows[bottom - 1]["y0"] - overhang), "yt": round6(self.rows[top - 1]["y1"] + overhang),
            })

    def row(self, k: int) -> dict[str, Any]:
        return self.rows[k - 1]

    def own_zone(self, k: int) -> tuple:
        """ROW_k's electrode grown by the coverlay expansion and the window clearance (nm): its lane's own zone."""

        row = self.row(k)
        grow = self.rules.expansion + self.c_win
        return bus.nm_box(row["L"] - grow, row["y0"] - grow, row["Rt"] + grow, row["y1"] + grow)

    def electrode_points(self, k: int, low_nm: int, high_nm: int) -> list[tuple]:
        """The corners, strictly between two heights (nm), of every other row's electrode grown by the copper
        clearance: inside its own zone a lane is exempt from the windows (K), never from the trace space to
        another net's electrode."""

        points = []
        for row in self.rows:
            if row["k"] == k:
                continue
            box = bus.nm_box(row["L"] - self.c_cu, row["y0"] - self.c_cu, row["Rt"] + self.c_cu, row["y1"] + self.c_cu)
            clipped = bus.clip_y(box, low_nm + 1, high_nm - 1)
            if clipped:
                points.extend(bus.box_corners(clipped))
        return points

    def window_boxes(self) -> list[tuple]:
        """The Row windows and the stacked Column windows grown by the window clearance (nm).

        The fillers between consecutive windows lie in the hull of the two boxes.
        """

        grow = self.rules.expansion + self.c_win
        boxes = [bus.nm_box(row["L"] - grow, row["y0"] - grow, row["Rt"] + grow, row["y1"] + grow) for row in self.rows]
        boxes += [bus.nm_box(slot["x0"] - grow, slot["yb"] - grow, slot["x1"] + grow, slot["yt"] + grow) for slot in self.slots]
        return boxes


# --------------------------------------------------------------------------
# The Column board: the straight Column board.
# --------------------------------------------------------------------------


def _column_plan(design: Mapping[str, Any], profile: Mapping[str, Any], capped: bool = True) -> dict[str, Any]:
    """The Column board's plan: the straight Column board's of the same design without ``routing.row_sides``
    (:func:`engine.layout.column_plan`), with ``capped`` its V at most :data:`COLUMN_V_CAP_DEG`
    (:func:`column_profile`), with the masked records of its spans and the classes ``CLASSES``.  Its tail is centred
    under its fan-out; the Row tail lies on it where they meet (stacked tails)."""

    plan = dict(column_plan(design, column_profile(profile) if capped else profile))
    plan["spans"] = column_frame_spans(design)
    plan["top_chain"] = _column_top_chain(plan, plan["spans"])
    plan["mask_class"] = CLASSES
    return plan


def _lowered(plan: Mapping[str, Any], root: float) -> dict[str, Any]:
    """A Column plan with its tail root at ``root`` (its frame) where that lies lower: the shared body's bottom edge
    (:func:`_build`).  Its contact columns run on straight down to it and the tail, as long, below it."""

    if root >= plan["tail_top"] - _NOISE_MM:
        return dict(plan)
    lowered = dict(plan)
    lowered["tail_top"] = root
    lowered["tip"] = round6(root - plan["tail_length"])
    lowered["outline_size"] = (plan["outline_size"][0], plan["body"][3] - lowered["tip"])
    return lowered


def _column_board(design: Mapping[str, Any], profile: Mapping[str, Any], plan: Mapping[str, Any]) -> dict[str, Any]:
    """The Column board of a plan (:func:`_column_plan`, :func:`_lowered`): :func:`engine.layout._masked_column_board`
    on the design with its mask written out, so an unmasked design's board carries the masked records of its full
    spans; its outline is replaced by the shared one (:func:`_share_outline`)."""

    return _masked_column_board(_with_mask(design), profile, plan)


def _with_mask(design: Mapping[str, Any]) -> dict[str, Any]:
    """The design with its mask written out (the full spans of the rectangle when unmasked)."""

    return {**design, "matrix": {**design["matrix"], "mask": [list(span) for span in _row_spans(design)]}}


def _points_for(boxes: list[tuple], zone: tuple, low_nm: int, high_nm: int) -> list[tuple]:
    """The corners of the K boxes outside a lane's own zone, strictly between two heights (nm)."""

    points = []
    for box in boxes:
        for part in bus.subtract(box, zone):
            clipped = bus.clip_y(part, low_nm + 1, high_nm - 1)
            if clipped:
                points.extend(bus.box_corners(clipped))
    return points


def _lane_start(geo: _Geo, k: int, side: int, boxes: list[tuple]) -> tuple:
    """Where ROW_k's lane leaves its electrode's end (nm; ``side`` -1 near, +1 far).

    The end's centre, unless a K box on the outer side straddles the centre
    line (fine pitches: the next row's Column windows reach above it): then
    the end's top corner (a box from below) or bottom corner (from above),
    inset by half the trace width.
    """

    row = geo.row(k)
    x = to_nm(row["L"] if side < 0 else row["Rt"])
    centre = to_nm(row["yc"])
    top, bottom = to_nm(floor6(row["y1"] - geo.tw / 2)), to_nm(ceil6(row["y0"] + geo.tw / 2))
    zone = geo.own_zone(k)
    below = above = False
    for box in boxes:
        for part in bus.subtract(box, zone):
            outer = part[2] <= x if side < 0 else part[0] >= x
            if outer and part[1] < centre < part[3]:
                if part[3] <= top:
                    below = True
                elif part[1] >= bottom:
                    above = True
                else:
                    below = above = True
    if below and not above:
        return (x, top)
    if above and not below:
        return (x, bottom)
    return (x, centre)


# --------------------------------------------------------------------------
# The pair.
# --------------------------------------------------------------------------


def _construct(design: Mapping[str, Any], profile: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Both boards of a ``routing.row_sides`` design, in their canonical frames."""

    rules = Rules(profile)
    sides = row_sides(design)
    near = near_side(design)
    geo = _Geo(design, rules, flip=sides != "both" and sides != near)
    if sides == "both":
        near_rows = [k for k in range(1, geo.R + 1) if k % 2 == 1]
        far_rows = [k for k in range(1, geo.R + 1) if k % 2 == 0]
    else:
        near_rows, far_rows = list(range(1, geo.R + 1)), []
    try:
        built = _build(design, profile, geo, near_rows, far_rows, raised=False)
    except _CutBlocked:
        # The lanes cannot turn down on the field's bottom edge: the bottom row's corner moves up onto that edge before
        # the onion is built instead (none of the corpora measured needs this).
        built = _build(design, profile, geo, near_rows, far_rows, raised=True)
    row = _row_board(design, profile, geo, built, sides, near)
    return row, built["column"]


def _bands(geo: _Geo, rows: list[int], side: int, boxes: list[tuple], raised: bool = False) -> dict[int, list[tuple]]:
    """Each lane of one side (``side`` -1 near, +1 far) from its electrode's end to the top of its ray, and that ray
    down to ``_DEEP_NM`` below the field (nm, this frame): diagonal-bus/1's onion of west convex chains, innermost
    first (built mirrored on the far side), each around the keep-out K below its start, the keep-out of the lane inside
    it and its own zone's outer-bottom corner.  Every lane runs straight down from its last corner, which lies up to
    0.3 mm below the field for the inner lanes (the bottom row's zone reaches that far below it):
    :func:`_cut_at_field` turns them down on the field's bottom edge instead.

    On a receding field a lane follows the field inward: where everything it must keep west of at or below the field's
    bottom edge (the keep-out points there and the inner lanes' offsets where they cross it) lies east of its westmost
    obstacle above the edge, its chain runs around its points down to the edge as far east as that allows, and no flatter
    than the taper cap from the vertical, then straight down.  The next lane out keeps the bundle pitch from it
    (:func:`engine.bus.lane_offset`: its inward turn does not spread the lanes outside it).

    ``raised``: the bottom row's corner moved straight up onto that edge before the onion is built (the lanes outside it
    lean a little more, and none follows the field inward), for a design whose cut lanes would cut a keep-out or come
    closer than the bundle pitch (none measured)."""

    bp_nm = to_nm(geo.bp)
    deep = -_DEEP_NM
    low = 0  # the field's bottom edge: the lowest Row electrode's bottom
    # The taper cap's run per unit rise (millionths, floored): a lane following the field inward leans no farther.
    run = int(math.sin(geo.cap) / math.cos(geo.cap) * _RUN_SCALE)
    keepout: list[tuple] = []  # in the side frame (mirrored on the far side)
    offsets: list[list[tuple]] = []  # the inner lanes' offsets (side frame), for their crossings with the edge
    chains: dict[int, list[tuple]] = {}
    for k in reversed(rows):  # innermost (the lowest row of the side) first
        start = _lane_start(geo, k, side, boxes)
        zone = geo.own_zone(k)
        corner = (zone[0] if side < 0 else zone[2], zone[1])
        points = _points_for(boxes, zone, deep, start[1]) + geo.electrode_points(k, deep, start[1])
        if side > 0:
            points = bus.mirror(points)
            start = bus.mirror([start])[0]
            corner = bus.mirror([corner])[0]
        if raised and corner[1] < low:
            # The lane turns down on the field's bottom edge, straight above the zone's outer-bottom corner and outside
            # every keep-out point below that edge.
            corner = (min([corner[0]] + [point[0] for point in points if point[1] < low]), low)
        points.append(corner)
        points.extend(point for point in keepout if deep < point[1] < start[1])
        reach = min([point[0] for point in points] + [start[0]])
        # The westmost x the lane's ray down from the field's bottom edge may take: west of everything at or below
        # that edge (the keep-out points there and the inner lanes' offsets where they cross it), and of the line at
        # the taper cap up through every point above it (the chain's last segment, the flattest of a convex chain's
        # inward ones, then keeps within the cap).
        edge = [point[0] for point in points if point[1] <= low] + _crossings(offsets, low)
        hug = None if raised or not edge else min(edge)
        if hug is not None:
            hug = min([hug] + [x + y * run // _RUN_SCALE for x, y in [*points, start] if low < y <= start[1]])
        if hug is not None and hug - reach > _HUG_MIN_NM and start[1] > low:
            # A receding field: the lane runs around its points down to the edge, then straight down.
            chain = bus.west_chain(start, (hug, low), points) + [(hug, deep)]
        else:
            hug = reach
            chain = bus.west_chain(start, (reach, deep), points)
        kept = bus.lane_keepout(chain, (hug, deep - bus.NM), bp_nm)
        offsets.append(kept[:-4])  # the lane's offset (bus.lane_keepout: its offset, then its start box's corners)
        keepout = keepout + kept
        chains[k] = bus.mirror(chain) if side > 0 else chain
    return chains


def _crossings(polylines: list[list[tuple]], level: int) -> list[int]:
    """The x (nm, floored: west) where each polyline crosses the height ``level`` strictly between two vertices."""

    answer = []
    for line in polylines:
        for (x0, y0), (x1, y1) in zip(line, line[1:]):
            if (y0 - level) * (y1 - level) < 0:
                numerator, denominator = x0 * (y1 - y0) + (x1 - x0) * (level - y0), y1 - y0
                if denominator < 0:
                    numerator, denominator = -numerator, -denominator
                answer.append(numerator // denominator)
    return answer


def _fan(lanes: list[int], move: int, angle: float, geo: _Geo, x_band: Mapping[int, float], contact: Mapping[int, float],
         k_boxes: list[tuple], top: float) -> dict[str, Any]:
    """One run of lanes moving the same way (``move`` -1 west, +1 east), front (the lane farthest along the move)
    first, turned at ``angle`` (rad) from the vertical: parallel fan lines ``p . n = s`` with ``n = (-move cos a,
    -sin a)`` (back along the run and down), the front's through its ray at ``top``, each next one the bundle pitch
    (plus the rounding allowance) farther back, all below the K boxes over their spans.  Each lane turns off its
    vertical ray onto its line (``upper``, on the grid) and off its line down its contact column (``lower``, a grid
    step low, so no fan line leans farther than ``angle``)."""

    nx, ny = -move * math.cos(angle), -math.sin(angle)
    step = geo.bp + _FAN_ALLOWANCE_MM
    previous = None
    answer = []
    for k in lanes:
        x, c = x_band[k], contact[k]
        s = x * nx + top * ny
        if previous is not None:
            s = max(s, previous + step)
        low, high = min(x, c), max(x, c)
        for x0, y0, x1, _ in k_boxes:
            a, b = max(x0, low), min(x1, high)
            if a <= b:
                s = max(s, a * nx + y0 * ny, b * nx + y0 * ny)
        upper = [x, round6((s - x * nx) / ny)]
        lower = [c, floor6((s - c * nx) / ny - _GRID_STEP_MM)]
        answer.append({"k": k, "upper": upper, "lower": lower})
        previous = s
    lowest = min(lane["lower"][1] for lane in answer)
    return {"lanes": answer, "lowest": lowest, "angle": angle, "move": move}


def _plan_fans(geo: _Geo, order: list[int], side_of: Mapping[int, int], x_band: Mapping[int, float],
               contact: Mapping[int, float], k_boxes: list[tuple], top: float, caps: list[float]) -> list[dict[str, Any]]:
    """The runs of consecutive lanes of one side (contact order) that move the same way, each at the cap of ``caps``
    whose junction (its lowest bend less the junction drop) lies highest (ties: the smaller cap)."""

    rules = geo.rules
    moves = {}
    for k in order:
        shift = round6(contact[k] - x_band[k])
        moves[k] = 0 if abs(shift) <= _NOISE_MM else (1 if shift > 0 else -1)
    runs = []
    index = 0
    while index < len(order):
        end = index
        while end + 1 < len(order) and moves[order[end + 1]] == moves[order[index]]:
            end += 1
        move = moves[order[index]]
        if move:
            members = order[index:end + 1]
            front = members if move < 0 else members[::-1]
            best = None
            for cap in caps:
                fan = _fan(front, move, cap, geo, x_band, contact, k_boxes, top)
                fan["bottom"] = floor6(fan["lowest"] - _junction_drop(geo.tw, cap, rules))
                if best is None or fan["bottom"] > best["bottom"] + _NOISE_MM:
                    best = fan
            runs.append(best)
        index = end + 1
    return runs


def _fan_clash(order: list[int], lines: Mapping[int, list[list[float]]], geo: _Geo) -> tuple[int, int] | None:
    """The first adjacent pair of lanes (contact order) whose centre lines below the bands come closer than the
    bundle pitch (less a grid step), or ``None``."""

    for a, b in zip(order, order[1:]):
        first, second = lines[a], lines[b]
        for p0, p1 in zip(first, first[1:]):
            for q0, q1 in zip(second, second[1:]):
                if segment_distance(p0, p1, q0, q1) < geo.bp - _GRID_STEP_MM:
                    return a, b
    return None


def _build(design: Mapping[str, Any], profile: Mapping[str, Any], geo: _Geo, near_rows: list[int], far_rows: list[int],
           raised: bool) -> dict[str, Any]:
    """The Row construction (bands, tail, fans, routes, outline) and its Column board (``raised``: see :func:`_bands`)."""

    rules = geo.rules
    rows = geo.R
    two_sided = bool(far_rows)
    windows = geo.window_boxes()
    # The field's bottom window level: below it a lane is clear of every window.
    y_hug = floor6(-rules.overhang - rules.expansion - geo.c_win)

    # ---- the bands (diagonal-bus/1's onion hugging a receding field, every lane straight down below its last corner) --
    boxes = windows  # the stacked Column copper is no keep-out: the boards may overlap outside the field
    chains = {**_bands(geo, near_rows, -1, boxes, raised), **_bands(geo, far_rows, 1, boxes, raised)}
    if not raised:
        chains = _cut_at_field(geo, chains, near_rows, far_rows, boxes, y_hug)
    x_band = {k: to_mm(chain[-1][0]) for k, chain in chains.items()}
    order = list(near_rows) + list(reversed(far_rows))  # contact order, west to east: ROW_01, 03, ..., 04, 02
    side_of = {**{k: -1 for k in near_rows}, **{k: 1 for k in far_rows}}

    # ---- the Row tail: centred on the field in every side mode, as the Column tail; the fans --------------------------
    pins = connector_pins(design, "rows")
    width = tail_width(pins, rules)
    length = tail_length_for_role(design, "rows")
    k_boxes = [tuple(to_mm(value) for value in box) for box in windows]
    # The tail centred on the field's width [0, aw], as the Column tail under its fan-out (P5-diagonal-bus.md section 27:
    # the user's tails within the sensor's width), so both tails lie within it wherever they are narrower than the field
    # and are centred on it where they are wider.  The rows take the contacts from the tail's canonical left (positions
    # 1..R): with ``both`` and a contact per row the near and far contacts part on the field's centre line (half a contact
    # pitch east of it for an odd row count), and one side's whole bundle fans inward under the field.  Mirrored, the rows
    # take the contacts at the tail's far end (turned back they are positions 1..R).
    first = pins - rows if geo.flip else 0
    tail_x, position = round6((geo.aw - width) / 2), "centred"
    # ---- the Column V and the fans (the Column V rule): the V capped at COLUMN_V_CAP_DEG unless the profile's own roots
    # the tails higher.  The tails root at the deeper of the two boards' own roots (this frame: the Row root just below the
    # fans' junctions, the Column root below its V), compared here, before the level is lowered below the union's fillets.
    # A V at the cap leaves the fans the profile's steepest cap outside the entry-angle guard; where the V at the profile's
    # own caps roots the tails higher (a fan below 85 degrees gains nothing from the cap: the fans' caps are whole degrees,
    # those within 5 degrees of the entry angle excluded), it is taken; a tie takes the capped one.
    best, failure = None, None
    for capped in (True, False) if column_profile(profile) is not profile else (True,):
        plan = _column_plan(design, profile, capped)
        try:
            chosen = _arrangement(geo, plan, chains, x_band, order, side_of, k_boxes, y_hug, (tail_x, first))
        except RowBusInfeasible as error:
            failure = failure or error
            continue
        own = min(chosen["root"], round6(plan["tail_top"] - plan["active"][1]))
        if best is None or own > best[0] + _NOISE_MM:
            best = (own, plan, chosen)
    if best is None:
        raise failure
    root, plan, chosen = best
    contact, runs, bands = chosen["contact"], chosen["runs"], chosen["bands"]
    fanned = {lane["k"]: lane for run in runs for lane in run["lanes"]}

    # ---- the tail roots: both on the shared body's bottom edge --------------------------------------------------------
    # That deeper root, lowered below the union's fillets into the tails (the shared outline runs straight down the tails'
    # sides there): the shallower tail's root moves down to it, its contact columns running on straight, and each tail is
    # as long below it.
    active_y = plan["active"][1]
    anchor = root
    for _ in range(_LEVEL_PASSES):
        lowered = _lowered(plan, round6(root + active_y))
        tip = round6(root - length)
        centrelines, pieces = _routes(geo, bands, fanned, order, contact, root, tip)
        raw = _row_outline(geo, (root, tail_x, width, tip), centrelines, order, two_sided)
        owns = _own_rings(lowered, raw, (tail_x, width, root), anchor)
        top = _share_outline(geo, owns, None, lowered, root, probe=True)
        if top >= root - _NOISE_MM:
            break
        root = floor6(top)
    else:
        raise RowBusInfeasible("The tails' roots do not settle below the boards' fillets.")
    plan = lowered
    column = _column_board(design, profile, plan)
    # ---- one outline down to the tail roots: both boards' union above them, each its own tail below ---------------
    level = root
    ring, smallest = _share_outline(geo, owns, column, plan, level)
    fans = [
        {"rows": [lane["k"] for lane in run["lanes"]], "move": "west" if run["move"] < 0 else "east",
         "angle_deg": round6(math.degrees(run["angle"])),
         "height_mm": round6(max(lane["upper"][1] for lane in run["lanes"]) - run["lowest"])}
        for run in runs
    ]
    return {
        "column": column, "tail_position": position,
        "ring": ring, "smallest": smallest, "pieces": pieces, "hulls": bands,
        "order": order, "near_rows": near_rows, "far_rows": far_rows, "fans": fans,
        "root": root, "tip": tip, "tail_x": tail_x, "width": width, "pins": pins, "length": length, "level": level,
    }


class _CutBlocked(RowBusInfeasible):
    """The lanes cannot turn down on the field's bottom edge (see :func:`_cut_at_field`)."""


def _cut_at_field(geo: _Geo, chains: Mapping[int, list[tuple]], near_rows: list[int], far_rows: list[int], boxes: list[tuple],
                  y_hug: float) -> dict[int, list[tuple]]:
    """The chains of :func:`_bands` (nm, this frame) with every corner below the field's bottom edge cut off: a lane
    whose band crosses that edge turns straight down there, so above the field the bands are diagonal-bus/1's and no
    lane bends below the field before its fan.

    The turn lies on the band's crossing with the edge (its grid point outside it), or, where the ray down from there
    to the window level ``y_hug`` would cut the keep-out K (outside its own zone; the bottom row's lane on thin rows),
    just outside that keep-out, the band's last segment turning a little outward to it.  A cut lane thus moves inward
    below the field, by up to about 0.2 mm (the bottom row's).  Each side's rays keep the bundle pitch and a turned
    segment keeps it from the lane outside, or :class:`_CutBlocked` is raised.
    """

    deep, low = -_DEEP_NM, to_nm(y_hug)
    bp_nm = to_nm(geo.bp)
    answer = {}
    for rows, side in ((near_rows, -1), (far_rows, 1)):
        flip = (lambda points: bus.mirror(points)) if side > 0 else (lambda points: [tuple(point) for point in points])
        turned: dict[int, tuple] = {}  # lane -> the turned segment (side frame), where it left the band
        previous = None
        lanes = {}
        for k in reversed(rows):  # innermost first
            chain = flip(chains[k])
            zone = geo.own_zone(k)
            obstacles = [part for box in boxes for part in bus.subtract(box, zone)]
            obstacles += [bus.nm_box(row["L"] - geo.c_cu, row["y0"] - geo.c_cu, row["Rt"] + geo.c_cu, row["y1"] + geo.c_cu)
                          for row in geo.rows if row["k"] != k]
            obstacles = sorted(bus.mirror_box(box) for box in obstacles) if side > 0 else sorted(obstacles)
            cut = chain
            for index, (a, b) in enumerate(zip(chain, chain[1:])):
                if b[1] == deep or b[1] > 0:
                    continue
                if b[1] == 0:
                    cut = chain[: index + 2] + [(b[0], deep)]
                    break
                # The crossing of a-b with the edge, on its grid point outside it, moved outside any keep-out box its ray
                # down to the window level would cut.
                numerator, denominator = a[0] * (b[1] - a[1]) - (b[0] - a[0]) * a[1], b[1] - a[1]
                crossing = x = numerator // denominator
                moved = True
                while moved:
                    moved = False
                    for box in obstacles:
                        if bus.segment_enters((x, 0), (x, low), box):
                            x, moved = box[0], True
                if x != crossing:
                    if any(bus.segment_enters(a, (x, 0), box) for box in obstacles):
                        raise _CutBlocked(f"ROW_{k:02d}'s lane cannot turn down on the field's bottom edge.")
                    turned[k] = (a, (x, 0))
                cut = chain[: index + 1] + [(x, 0), (x, deep)]
                break
            x = cut[-1][0]
            if previous is not None and previous - x < bp_nm:
                raise _CutBlocked(f"ROW_{k:02d}'s lane comes closer than the bundle pitch to the lane inside it on the field's bottom edge.")
            previous = x
            lanes[k] = cut
        # A turned segment keeps the bundle pitch from the lane outside it (the onion was built around the band).
        for inner, outer in zip(reversed(rows), list(reversed(rows))[1:]):
            if inner not in turned:
                continue
            a, b = [[to_mm(value) for value in point] for point in turned[inner]]
            path = [[to_mm(value) for value in point] for point in lanes[outer][:-1]] + [[to_mm(lanes[outer][-1][0]), y_hug]]
            if any(segment_distance(a, b, p, q) < geo.bp - _NOISE_MM for p, q in zip(path, path[1:])):
                raise _CutBlocked(f"ROW_{inner:02d}'s turned lane comes closer than the bundle pitch to ROW_{outer:02d}'s.")
        answer.update({k: flip(chain) for k, chain in lanes.items()})
    return answer


def _below(path: list[list[float]], level: float) -> list[list[float]]:
    """The part of a polyline (top to bottom, y non-increasing) at or below ``level``."""

    for index, (a, b) in enumerate(zip(path, path[1:])):
        if b[1] <= level:
            if a[1] <= level:
                point = list(a)
            else:
                point = [a[0] + (b[0] - a[0]) * (level - a[1]) / (b[1] - a[1]), level]
            return clean_polyline([point, *path[index + 1:]])
    return [list(path[-1])]


def _arrangement(geo: _Geo, plan: Mapping[str, Any], chains: Mapping[int, list[tuple]], x_band: Mapping[int, float],
                 order: list[int], side_of: Mapping[int, int], k_boxes: list[tuple], top: float, tail: tuple) -> dict[str, Any]:
    """The Row tail ``(tail_x, first contact used)``: its contacts, the fans off the entry angle of the Column fan-out
    (``plan``), each lane's band (its chain down to the top of its ray) and the Row root just below the fans' junctions
    (and the fillet radius below the fans' start ``top``)."""

    rules = geo.rules
    tail_x, first = tail
    contact = {k: round6(tail_x + rules.side_offset + (first + index) * rules.pitch) for index, k in enumerate(order)}
    entry = plan["entry_angle_deg"]
    caps = [cap for cap in geo.caps if abs(math.degrees(cap) - entry) > ENTRY_ANGLE_GUARD_DEG + _NOISE_MM]
    if not caps:
        raise RowBusInfeasible(f"No taper cap of the fans keeps {ENTRY_ANGLE_GUARD_DEG:g} degrees off the Column fan-out's entry.")
    runs = _plan_fans(geo, order, side_of, x_band, contact, k_boxes, top, caps)
    fanned = {lane["k"]: lane for run in runs for lane in run["lanes"]}
    bands = {k: list(chains[k][:-1]) for k in order}
    # Below the bands: each lane's ray, fan and contact column.
    depth = min([run["lowest"] for run in runs] + [top]) - 1.0
    lines = {}
    for k in order:
        lane = fanned.get(k)
        bends = [lane["upper"], lane["lower"]] if lane else []
        path = clean_polyline([*([to_mm(x), to_mm(y)] for x, y in bands[k]), *bends, [contact[k], depth]])
        lines[k] = _below(path, top)
    clash = _fan_clash(order, lines, geo)
    if clash is not None:
        raise RowBusInfeasible(f"ROW_{clash[0]:02d} and ROW_{clash[1]:02d} come closer than the bundle pitch below the field.")
    root = min([run["bottom"] for run in runs] + [floor6(top - rules.fillet_radius)])
    return {"contact": contact, "runs": runs, "bands": bands, "root": root}


def _routes(geo: _Geo, bands: Mapping[int, list[tuple]], fanned: Mapping[int, Any], order: list[int], contact: Mapping[int, float],
            root: float, tip: float) -> tuple[dict, dict]:
    """Per row: the route's centre line (electrode end -> junction) and its ``(tail, fanout)`` pieces (contact end
    first, as in engine.layout)."""

    rules = geo.rules
    finger_top = round6(tip + rules.tip_clearance + rules.contact_length)
    centrelines, pieces = {}, {}
    for k in order:
        band = [[to_mm(x), to_mm(y)] for x, y in bands[k]]  # electrode end -> the top of its ray
        lane = fanned.get(k)
        bends = [list(lane["upper"]), list(lane["lower"])] if lane else []
        down = clean_polyline([*band, *bends, [contact[k], root]])
        centrelines[k] = down
        pieces[k] = ([[contact[k], finger_top], [contact[k], root]], list(reversed(down)))
    return centrelines, pieces


# --------------------------------------------------------------------------
# The Row outline: a y-monotone polygon from the field's margin slabs and the outer lanes' envelopes.
# --------------------------------------------------------------------------


def _x_at_levels(pieces: list[list[list[float]]], levels: list[float], sign: int) -> list[float | None]:
    """The extreme x (min for ``sign`` -1, max for +1) of the polylines at each level (None where none spans it)."""

    answer = []
    for y in levels:
        best = None
        for poly in pieces:
            for (x0, y0), (x1, y1) in zip(poly, poly[1:]):
                low, high = min(y0, y1), max(y0, y1)
                if y < low - 1e-12 or y > high + 1e-12:
                    continue
                if high - low < 1e-12:
                    candidate = min(x0, x1) if sign < 0 else max(x0, x1)
                else:
                    candidate = x0 + (x1 - x0) * (y - y0) / (y1 - y0)
                if best is None or (candidate - best) * sign > 0:
                    best = candidate
        answer.append(best)
    return answer


def _running(chain: list[list[float]], sign: int) -> list[list[float]]:
    """The running extreme along a chain: it never moves inward (``sign`` -1 west, +1 east)."""

    answer = [list(chain[0])]
    current = chain[0][0]
    for (x0, y0), (x1, y1) in zip(chain, chain[1:]):
        if (x1 - current) * sign <= 1e-12:
            continue
        if (current - x0) * sign > 1e-12:
            fraction = (current - x0) / (x1 - x0)
            crossing = y0 + (y1 - y0) * fraction
        else:
            crossing = y0
        answer.append([current, crossing])
        answer.append([x1, y1])
        current = x1
    if abs(answer[-1][1] - chain[-1][1]) > 1e-12:
        answer.append([current, chain[-1][1]])
    return clean_polyline(answer)


def _envelope(pieces: list[list[list[float]]], levels: list[float], sign: int) -> list[list[float]]:
    """The exact extreme (min x for ``sign`` -1, max for +1) of the polylines between consecutive levels.

    Between two levels every piece is linear, so the envelope breaks only
    where two of them cross, and those crossings are added; both ends of
    every interval are kept, so a step between intervals keeps both points.
    """

    def lines_at(ya: float, yb: float) -> list[tuple]:
        low, high = min(ya, yb), max(ya, yb)
        answer = []
        for poly in pieces:
            for (x0, y0), (x1, y1) in zip(poly, poly[1:]):
                if min(y0, y1) <= low + 1e-8 and max(y0, y1) >= high - 1e-8 and abs(y1 - y0) > 1e-12:
                    slope = (x1 - x0) / (y1 - y0)
                    answer.append((slope, x0 - slope * y0))
        return answer

    chain: list[list[float]] = []
    for ya, yb in zip(levels, levels[1:]):
        lines = lines_at(ya, yb)
        if not lines:
            continue
        cuts = [ya, yb]
        for first in range(len(lines)):
            for second in range(first + 1, len(lines)):
                (a1, b1), (a2, b2) = lines[first], lines[second]
                if abs(a1 - a2) > 1e-12:
                    crossing = (b2 - b1) / (a1 - a2)
                    if min(ya, yb) + 1e-9 < crossing < max(ya, yb) - 1e-9:
                        cuts.append(crossing)
        for y in sorted(set(cuts), reverse=ya > yb):
            values = [a * y + b for a, b in lines]
            chain.append([min(values) if sign < 0 else max(values), y])
    return clean_polyline(chain)


def _unimodal(chain: list[list[float]], sign: int) -> list[list[float]]:
    """A chain (top to bottom) made monotone outward from the top down to its extreme, and from the bottom up to it."""

    outward = [point[0] * sign for point in chain]
    extreme = max(range(len(chain)), key=lambda index: (outward[index], -index))
    top = _running(chain[: extreme + 1], sign)
    bottom = _running(list(reversed(chain[extreme:])), sign)
    return clean_polyline(top + list(reversed(bottom))[1:])


def _split_at(chain: list[list[float]], y: float) -> tuple[list[list[float]], list[list[float]]]:
    """A polyline (top to bottom, y non-increasing) cut at height ``y``: the parts above and below, sharing the cut."""

    for index, (a, b) in enumerate(zip(chain, chain[1:])):
        if b[1] <= y + 1e-9:
            if abs(b[1] - y) <= 1e-9:
                point = list(b)
            elif abs(a[1] - b[1]) <= 1e-12:
                point = list(a)
            else:
                point = [a[0] + (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]), y]
            return chain[: index + 1] + [point], [point] + chain[index + 1:]
    return list(chain), []


def _cap(centre: list[float], radius: float, sign: int, steps: int = 18) -> list[list[float]]:
    """A half circle (circumscribed polygon) on the ``sign`` side of ``centre``, top to bottom."""

    outer = radius / math.cos(math.pi / steps / 2)
    points = []
    for step in range(steps + 1):
        angle = math.pi / 2 + (math.pi * step / steps) * (1 if sign < 0 else -1)
        points.append([centre[0] + outer * math.cos(angle), centre[1] + outer * math.sin(angle)])
    return points


def _side_chain(pieces: list, root: float, hold: float, y_top: float, seed: float, sign: int, y_field: float) -> list[list[float]]:
    """One side of the outline, top to bottom: the envelope of ``pieces`` from the top down to the tail root, held at
    least at the tail's side ``seed`` over the hold above the root, made monotone outward from the top down to its
    widest level (the board never narrows below the tip down to there) and from the tail up to it.  Where the tail's
    side lies beyond the envelope, the side reaches it below F's bottom ``y_field`` only (the bands beside the field
    stay as they are)."""

    levels = sorted(
        {round(point[1], 9) for poly in pieces for point in poly if root - 1e-9 <= point[1] <= y_top + 1e-9}
        | {y_top, root, round6(root + hold)},
        reverse=True,
    )
    above, below = _split_at(_envelope(pieces, levels, sign), round6(root + hold))
    chain: list[list[float]] = [list(point) for point in above]
    if below and (seed - chain[-1][0]) * sign > 1e-12:
        # The tail's side reaches beyond the envelope there: the side runs on to it, slanting from the envelope's last
        # point above (at F's bottom at the highest), or, where that would lie flatter than 45 degrees (a tail far wider
        # than the field and its bands), straight down and then one step out.
        upper, lower = _split_at(chain, y_field)
        if lower:
            chain = upper + lower[1:]
        if len(chain) > 1 and abs(seed - chain[-2][0]) <= chain[-2][1] - chain[-1][1]:
            chain[-1] = [seed, chain[-1][1]]
        else:
            chain.append([seed, chain[-1][1]])
    for x, y in below[1:]:
        chain.append([min(x, seed) if sign < 0 else max(x, seed), y])
    outward = [point[0] * sign for point in chain]
    split = max(range(len(chain)), key=lambda index: (outward[index], -index))
    top = _running(chain[: split + 1], sign)
    rest = chain[split:]
    if abs(rest[-1][0] - seed) > 1e-12:
        rest = rest + [[seed, rest[-1][1]]]
    bottom = list(reversed(_running(list(reversed(rest)), sign)))
    if abs(top[-1][0] - bottom[0][0]) <= 1e-12 and abs(top[-1][1] - bottom[0][1]) <= 1e-12:
        bottom = bottom[1:]
    return clean_polyline(top + bottom)


def _hold(rules: Rules) -> float:
    """How far above the Row root the tail's sides hold straight: the copper-to-edge rule plus half a finger width."""

    return round6(rules.copper_to_edge + rules.finger_width / 2 + rules.offset_allowance)


def _row_outline(geo: _Geo, tail: tuple, centrelines: dict, order: list[int], two_sided: bool) -> list[list[float]]:
    """The Row outline before its fillets, counter-clockwise.

    Each side is the envelope, per interval with crossings added, of F's
    y-slabs (the crossings dilated by the active-edge margin) and the
    outermost lane's outer envelope with its start cap (the west-most and the
    east-most lane of the contact order, whose fans bound the board below the
    field), made monotone from the tip down to its widest level, and at least
    to F's bottom, and from the tail up to there: with ``both`` a funnel.
    With one side, the inner flank is F's east side down to F's bottom and
    then straight down the tail's side (one step); where the tail is wider
    than F's bottom (diagonal-bus/10: centred under a narrower field), it
    slants out from F's bottom down to the tail's side where that is 45
    degrees or steeper (made monotone from the top down to its widest level
    and from the tail up to it, as :func:`_side_chain`), else it steps out
    at F's bottom.  Both tail sides hold straight for the copper-to-edge
    rule plus half a finger width above the tail root.
    """

    rules = geo.rules
    margin = rules.margin
    root, tail_x, width, tip = tail
    tail_east = round6(tail_x + width)
    dilated = []
    for k in range(geo.R, 0, -1):
        row = geo.row(k)
        dilated.append((round6(row["lo"] * geo.px - margin), round6(row["y0"] - margin),
                        round6(row["hi"] * geo.px + geo.cw + margin), round6(row["y1"] + margin)))
    slabs = rect_union_slabs(band_union(dilated, 1), 1)
    if any(row["lo"] != 0 or row["hi"] != geo.C - 1 for row in geo.rows):
        # A masked field (diagonal-bus/6): F's sides as its convex hull, so that the outline crosses a notch (cells
        # missing at a corner) on a chamfer instead of a staircase.
        body_west, body_east = _hull_sides(slabs, CHAMFER_STEP_CELLS * max(geo.px, geo.py) / math.sqrt(CHAMFER_STEP_CELLS ** 2 + 1))
    else:
        body_west = [[[start, low], [start, high]] for low, high, start, _ in slabs]
        body_east = [[[end, low], [end, high]] for low, high, _, end in slabs]
    y_top = slabs[-1][1]
    y_field = slabs[0][0]  # F's bottom
    env = geo.env
    hold = _hold(rules)
    west_k, east_k = order[0], order[-1]
    west_env = offset_polyline(centrelines[west_k], env, left=False, arc_step_rad=rules.arc_step)
    west_cap = _cap(centrelines[west_k][0], env, -1)
    west_chain = _side_chain(body_west + [west_env, west_cap], root, hold, y_top, tail_x, -1, y_field)
    # The east-most lane of the contact order: the far band's outermost with both, else the innermost lane.
    east_env = offset_polyline(centrelines[east_k], env, left=True, arc_step_rad=rules.arc_step)
    east_cap = _cap(centrelines[east_k][0], env, 1)
    if two_sided:
        east_up = _side_chain(body_east + [east_env, east_cap], root, hold, y_top, tail_east, 1, y_field)[::-1]
    else:
        # The inner flank: F's east side (with the innermost lane's envelope above F's bottom), made monotone from the
        # top down to its widest level and from F's bottom up to it (it follows a field that narrows downward); below
        # F's bottom the innermost lane's ray and fan and the tail's side, monotone from the tail up (one straight
        # step from F's bottom down into the tail where they lie inside it).
        east_upper, east_lower = _split_at(east_env, y_field)
        upper_pieces = body_east + [east_upper, east_cap]
        levels = sorted(
            {round(point[1], 9) for poly in upper_pieces for point in poly if y_field - 1e-9 <= point[1] <= y_top + 1e-9} | {y_top, y_field},
            reverse=True,
        )
        upper = _unimodal(_envelope(upper_pieces, levels, 1), 1)
        levels_lower = sorted(
            {round(point[1], 9) for point in east_lower if root - 1e-9 <= point[1] <= y_field + 1e-9} | {root, round6(root + hold), y_field}
        )
        # A tail wider than F's bottom (centred under a narrower field, diagonal-bus/10) reaches out below F's bottom as a
        # tail side does in _side_chain: slanting from F's bottom corner down to the hold where that is 45 degrees or
        # steeper (no ledge at F's bottom), the side made monotone from the top down to its widest level and from the tail
        # up to it; flatter, it steps out once at F's bottom.
        reach, held = upper[-1][0], round6(root + hold)
        slant = reach < tail_east - 1e-12 and tail_east - reach <= y_field - held
        lower = []
        # Every level lies on the innermost lane's envelope (its centre line runs down to the root): x is never None.
        for x, y in zip(_x_at_levels([east_lower], levels_lower, 1), levels_lower):  # bottom -> top
            if y <= root + hold + 1e-9:
                x = max(x, tail_east)
            elif slant:
                x = max(x, reach + (tail_east - reach) * (y_field - y) / (y_field - held))
            lower.append([x, y])
        east_up = _unimodal(upper + lower[::-1], 1)[::-1] if slant else _running(lower, 1) + upper[::-1]
    left_tip, right_tip = _tip_corners(tail_x, width, tip, rules)
    ring = list(west_chain)  # the top-left corner down to the tail root
    if abs(ring[-1][0] - tail_x) > 1e-9 or abs(ring[-1][1] - root) > 1e-9:
        ring.append([tail_x, root])
    ring += left_tip + right_tip
    if abs(east_up[0][0] - tail_east) > 1e-9 or abs(east_up[0][1] - root) > 1e-9:
        ring.append([tail_east, root])
    ring += east_up  # the tail root (east) up to the top-right corner
    return clean_polyline(ring, closed=True)


def _hull_sides(slabs: list[tuple], depth: float) -> tuple[list[list[list[float]]], list[list[list[float]]]]:
    """F's west and east sides with its notches chamfered, each one chain from F's top down to its bottom (``([west
    chain], [east chain])``, the pieces of :func:`_row_outline`).

    Between two consecutive corners of F's convex hull on a side, F's
    staircase (a notch: cells missing at a corner) becomes the hull's edge,
    on or outside F (its ends are F's corners), where no corner of the
    staircase lies deeper than ``depth`` inside that edge (a step of
    :data:`CHAMFER_STEP_CELLS` cells; a deeper pocket, a wide step at a
    narrow tip, keeps its staircase).
    """

    points = sorted({(x, y) for low, high, start, end in slabs for x in (start, end) for y in (low, high)})

    def half(ordered: list[tuple]) -> list[tuple]:
        chain: list[tuple] = []
        for p in ordered:
            while len(chain) >= 2 and _cross(_minus(chain[-1], chain[-2]), _minus(p, chain[-1])) <= 0:
                chain.pop()
            chain.append(p)
        return chain

    hull = half(points)[:-1] + half(points[::-1])[:-1]  # counter-clockwise from the lowest-leftmost point
    top = max(y for _, y in hull)
    bottom = min(y for _, y in hull)
    count = len(hull)
    top_left = min((index for index in range(count) if hull[index][1] == top), key=lambda index: hull[index][0])
    top_right = max((index for index in range(count) if hull[index][1] == top), key=lambda index: hull[index][0])
    bottom_left = min((index for index in range(count) if hull[index][1] == bottom), key=lambda index: hull[index][0])
    bottom_right = max((index for index in range(count) if hull[index][1] == bottom), key=lambda index: hull[index][0])
    west = [hull[(top_left + k) % count] for k in range((bottom_left - top_left) % count + 1)]
    east = [hull[(top_right - k) % count] for k in range((top_right - bottom_right) % count + 1)]
    sides = []
    for chain, column in ((west, 2), (east, 3)):
        stairs: list[tuple] = []
        for slab in reversed(slabs):
            for point in ((slab[column], slab[1]), (slab[column], slab[0])):
                if not stairs or stairs[-1] != point:
                    stairs.append(point)
        where = {point: index for index, point in enumerate(stairs)}
        side = [list(chain[0])]
        for u, v in zip(chain, chain[1:]):
            between = stairs[where[u] + 1:where[v]]
            length = math.sqrt((v[0] - u[0]) ** 2 + (v[1] - u[1]) ** 2)
            if between and max(abs(_cross(_minus(v, u), _minus(p, u))) / length for p in between) > depth + _NOISE_MM:
                side += [list(point) for point in between]
            side.append(list(v))
        sides.append([side])
    return sides[0], sides[1]


# --------------------------------------------------------------------------
# One outline down to the tail roots: the boards' union above them.
# --------------------------------------------------------------------------


def _own_rings(plan: Mapping[str, Any], raw: list[list[float]], tail: tuple, anchor: float) -> tuple:
    """Each board's own outline before its fillets, made regular (:func:`_regular_own`, the tails from ``anchor`` down
    as built: the deeper of the boards' own roots, this frame), on the layout grid: ``raw`` (the Row board's, this frame;
    its tail ``(x, width, root)``) and the Column board's (:func:`engine.layout.masked_column_outline` of ``plan``, its
    frame; as built where it is regular already), and the corners of their tails on ``anchor`` that each outline turns
    at (:func:`_root_corners`; ``(Row's, Column's)``, each in its frame).  The union of the two is filleted once
    (:func:`_union_above`).  ``anchor`` does not move when the roots are lowered below the fillets (:func:`_build`), so
    neither does a side made regular into a tail's side."""

    x, width, _ = tail
    column_root = round6(anchor + plan["active"][1])
    row = _round_ring(_regular_own(raw, (x, width, anchor)))
    column = _round_ring(_regular_own(masked_column_outline(plan), (plan["tail_x"], plan["tail_width"], column_root)))
    corners = (_root_corners(row, x, width, anchor), _root_corners(column, plan["tail_x"], plan["tail_width"], column_root))
    return row, column, corners


def _root_corners(ring: list[list[float]], x: float, width: float, root: float) -> list[list[float]]:
    """A tail's corners on ``root`` (``(x, root)`` and ``(x + width, root)``) that are corners of ``ring``: vertices more
    than a grid step off the line through their neighbours (a side made regular into the tail's side through its root
    corner at a slant, :func:`_regular_own`)."""

    count = len(ring)
    corners = []
    for corner in ((x, root), (round6(x + width), root)):
        for index, point in enumerate(ring):
            if abs(point[0] - corner[0]) <= _GRID_STEP_MM and abs(point[1] - corner[1]) <= _GRID_STEP_MM:
                before = ring[index - 1]
                if _off(_minus(ring[(index + 1) % count], before), before, point):
                    corners.append(list(point))
                break
    return corners


def _run_top(ring: list[list[float]], x: float, below: float) -> int | None:
    """The index of the top vertex of a ring's straight run along ``x = x`` that reaches below ``below`` (a tail's
    side), or ``None``."""

    count = len(ring)
    on = [abs(point[0] - x) <= _GRID_STEP_MM for point in ring]
    if all(on) or not any(on):
        return None
    start = on.index(False)
    top, run = None, []
    for step in range(1, count + 1):
        index = (start + step) % count
        if on[index]:
            run.append(index)
            continue
        if len(run) >= 2 and min(ring[k][1] for k in run) < below - _NOISE_MM:
            highest = max(run, key=lambda k: (ring[k][1], -k))
            if top is None or ring[highest][1] > ring[top][1]:
                top = highest
        run = []
    return top


def _share_outline(geo: _Geo, owns: tuple, column: Any, plan: Mapping[str, Any], level: float, probe: bool = False) -> Any:
    """The Row outline (this frame, filleted, on the layout grid) and the Column board's (set on ``column``, with its
    records), one outline from the tip down to ``level``: ``(Row ring, smallest fillet radius)``.

    ``level`` is the shared body's bottom edge, where both tails leave it
    (:func:`_build`): there the union runs straight down the tails' sides,
    below its fillets into them.  Above the level both boards take the union
    of their own outlines before their fillets (``owns``,
    :func:`_own_rings`), seen in the stack (filled across at every height),
    made regular again and filleted once (:func:`_union_above`, on the
    layout grid; where a board's own corner is the union's, its fillet is the
    one the board would have on its own); below it each keeps its own tail
    (:func:`_spliced`).  The two outlines are checked to coincide above the
    level, else :class:`RowBusInfeasible`.  ``probe``: only the height (this
    frame) down from which the union, run on below ``level``, runs straight
    down its tails' sides (:func:`_tails_straight`), for :func:`_build`'s
    choice of the level.
    """

    rules = geo.rules
    active_x, active_y = plan["active"][0], plan["active"][1]
    own, column_own, (row_corners, column_corners) = owns

    def from_column(point: Any) -> list[float]:
        x = point[0] - active_x
        return [round6(x if geo.flip else geo.aw - x), round6(point[1] - active_y)]

    def to_column(point: Any) -> list[float]:
        return [round6(active_x + (point[0] if geo.flip else geo.aw - point[0])), round6(point[1] + active_y)]

    upper = [from_column(point) for point in column_own]
    if not geo.flip:
        upper.reverse()  # mirrored, the Column ring runs clockwise in this frame
    corners = row_corners + [from_column(point) for point in column_corners]
    # Convex sides (diagonal-bus/9): a dent no deeper than a step of CHAMFER_STEP_CELLS cells, as F's notches are chamfered.
    depth = CHAMFER_STEP_CELLS * max(geo.px, geo.py) / math.sqrt(CHAMFER_STEP_CELLS ** 2 + 1)
    # One side (diagonal-bus/11): the east side, the inner flank, has no lanes; F's bottom lies the margin below the field.
    flank = round6(-rules.margin) if geo.one_sided else None
    if probe:
        whole, _ = _union_above([own, upper], level, rules, corners, depth, whole=True, flank=flank)
        return _tails_straight(whole, level)
    shared, used = _union_above([own, upper], level, rules, corners, depth, flank=flank)
    on_column = [to_column(point) for point in shared]
    if not geo.flip:
        on_column.reverse()  # mirrored, and the sides swap
    ring, row_join = _spliced(shared, own, level, rules)
    column_ring, column_join = _spliced(on_column, column_own, round6(level + active_y), rules)
    ring, column_ring = _round_ring(ring), _round_ring(column_ring)
    # The two outlines coincide above the level (both carry the same grid points there).
    if ring_deviation(clip_ring_above(ring, level), clip_ring_above([from_column(point) for point in column_ring], level), 1.0) > _GRID_STEP_MM:
        raise RowBusInfeasible("The Row and Column outlines do not coincide down to the tails' roots after their fillets.")
    column["outline"]["points"] = column_ring
    smallest = _least(used, column_join)
    column["construction"]["minimum_concave_fillet_radius_mm"] = None if smallest is None else round6(smallest)
    column["construction"]["shared_outline_below_field_mm"] = round6(-level)
    column["metrics"] = board_metrics(column)
    return ring, _least(used, row_join)


def _tails_straight(ring: list[list[float]], level: float) -> float:
    """The height down from which a union ring (:func:`_union_above`, its sides run on below ``level``) runs straight
    down its tails' sides: the lower top of the straight runs through its points run on below the level, where they
    run straight down (``level`` where none reaches above it)."""

    found = level
    run = round6(level - _SHARED_RUN_MM)
    for point in ring:
        if abs(point[1] - run) <= _NOISE_MM:
            index = _run_top(ring, point[0], level)
            if index is not None:
                found = min(found, ring[index][1])
    return found


def _least(*values: float | None) -> float | None:
    present = [value for value in values if value is not None]
    return min(present) if present else None


def _top_corners(ring: list[list[float]]) -> tuple[int, int]:
    """The indices of a ring's top-left and top-right vertices."""

    top = max(point[1] for point in ring)
    tops = [index for index, point in enumerate(ring) if point[1] >= top - _NOISE_MM]
    return min(tops, key=lambda index: (ring[index][0], index)), max(tops, key=lambda index: (ring[index][0], -index))


def _side_cut(ring: list[list[float]], level: float, side: int, first: bool = False) -> tuple[int, list[float]]:
    """Where a counter-clockwise ring, y-monotone above ``level``, goes below it down one side from its top (``side``
    -1 west, +1 east): ``(index, point on the level)``, the index the vertex before it.  ``first``: where the side
    first reaches the level (an edge lying on the level stays below), else where it first goes below it (such an
    edge stays above)."""

    count = len(ring)
    west, east = _top_corners(ring)
    index, step = (west, 1) if side < 0 else (east, -1)
    for _ in range(count):
        following = (index + step) % count
        a, b = ring[index], ring[following]
        if b[1] > a[1] + _NOISE_MM:
            raise RowBusInfeasible("A board's outline is not y-monotone above its tail root.")
        if first and b[1] <= level + _NOISE_MM:
            return index, ([b[0], level] if b[1] >= level - _NOISE_MM else [a[0] + (b[0] - a[0]) * (level - a[1]) / (b[1] - a[1]), level])
        if not first and b[1] < level - _NOISE_MM:
            return index, ([a[0], level] if a[1] <= level + _NOISE_MM else [a[0] + (b[0] - a[0]) * (level - a[1]) / (b[1] - a[1]), level])
        index = following
    raise RowBusInfeasible("A board's outline does not reach below the field.")


def _side_down(ring: list[list[float]], level: float, side: int) -> list[list[float]]:
    """One side of a counter-clockwise ring, y-monotone above ``level``, from its top down to where it first reaches
    the level."""

    count = len(ring)
    west, east = _top_corners(ring)
    top, step = (west, 1) if side < 0 else (east, -1)
    index, point = _side_cut(ring, level, side, first=True)
    return [list(ring[(top + step * k) % count]) for k in range((index - top) * step % count + 1)] + [point]


def _outer(chains: list[list[list[float]]], sign: int) -> list[list[float]]:
    """The outer envelope (min x for ``sign`` -1, max for +1) of y-monotone chains (top to bottom) over the heights
    they span, exactly: a step where a chain steps, a vertex where two chains cross."""

    levels = sorted({point[1] for chain in chains for point in chain}, reverse=True)
    pointers = [0] * len(chains)
    answer: list[list[float]] = []
    for top, bottom in zip(levels, levels[1:]):
        lines = []
        for slot, chain in enumerate(chains):
            k = pointers[slot]
            while k + 1 < len(chain) and chain[k + 1][1] >= top:
                k += 1
            pointers[slot] = k
            if k + 1 < len(chain) and chain[k][1] >= top and chain[k + 1][1] <= bottom:
                a, b = chain[k], chain[k + 1]
                slope = (b[0] - a[0]) / (b[1] - a[1])
                lines.append((slope, a[0] - slope * a[1]))
        if not lines:
            continue
        cuts = [top, bottom]
        for first in range(len(lines)):
            for second in range(first + 1, len(lines)):
                (a1, b1), (a2, b2) = lines[first], lines[second]
                if a1 != a2:
                    crossing = (b2 - b1) / (a1 - a2)
                    if bottom < crossing < top:
                        cuts.append(crossing)
        for y in sorted(cuts, reverse=True):
            values = [a * y + b for a, b in lines]
            answer.append([min(values) if sign < 0 else max(values), y])
    return clean_polyline([[round6(x), round6(y)] for x, y in answer])


def _union_above(rings: list[list[list[float]]], level: float, rules: Rules, corners: Any = (), depth: float = 0.0,
                 whole: bool = False, flank: float | None = None) -> tuple[list[list[float]], float | None]:
    """The union of counter-clockwise rings before their fillets, on the layout grid, above ``level`` (each y-monotone
    there, all overlapping at every height; filled across at every height), made regular and filleted once: ``(path,
    smallest fillet radius)``, the path counter-clockwise from the union's east side on the level up, over the top and
    down to its west side on the level.

    Where a ring is wider just below the level than the union just above it
    (its edge on the level steps out: a tail wider than its body), the
    union runs on along the level as far.  The union's sides run on
    ``_SHARED_RUN_MM`` below the level (:func:`_run_on`: along a ring's own
    side where it runs on below the union's point on the level, the tail it
    is flush with) while it is made regular (:func:`_regular`: the flat
    vertices merge, among them the crossings of nearly parallel sides and
    the vertices the envelope adds on a side at the other ring's heights;
    the points on the level and below it stay, and ``corners``, the rings'
    tail corners a side meets at a slant, :func:`_root_corners`), given
    straight sides (:func:`_straight_sides`) and filleted, so no fillet is
    cut short and a side meeting a flush tail at a concave corner has its
    fillet; a corner of a ring that is the union's has the fillet that ring
    would have on its own.  ``flank``: F's bottom (this frame) of a one-sided
    bus, whose east side has no lanes; that side's stretch from the field's
    outline corner down to the tail is made convex (:func:`_convex_flank`).
    ``whole``: the union ring itself, run on below the level, not cut."""

    west = _outer([_side_down(ring, level, -1) for ring in rings], -1)
    east = _outer([_side_down(ring, level, 1) for ring in rings], 1)
    left = min([west[-1][0]] + [_side_cut(ring, level, -1)[1][0] for ring in rings])
    right = max([east[-1][0]] + [_side_cut(ring, level, 1)[1][0] for ring in rings])
    run = round6(level - _SHARED_RUN_MM)
    below = [[round6(left), level], [_run_on(west, left, run, _flush(rings, level, left, -1)), run],
             [_run_on(east, right, run, _flush(rings, level, right, 1)), run], [round6(right), level]]
    ring = west + below + east[::-1]
    # Below the level each board keeps its own outline: the union's points on the level and below it stay while it is made
    # regular, so a side merged into its point on the level still runs through it, where a board's own side runs on, and
    # so do the tails' corners a side meets at a slant (filleted below, on both boards).
    anchors = {tuple(point) for point in below}
    anchors |= {tuple(point) for point in ring if any(
        abs(point[0] - corner[0]) <= _GRID_STEP_MM and abs(point[1] - corner[1]) <= _GRID_STEP_MM for corner in corners)}
    ring = _round_ring(_regular(ring, anchors))
    # The straight sides' bound is measured to the outline as the union is filleted (a staircase's concave corners
    # rounded, as the board has them), the line's enclosure to its corners.
    ring = _round_ring(_straight_sides(ring, level, run, rings, _round_ring(_filleted(ring, rules)[0])))
    # One side's flank without lanes (diagonal-bus/11): its stretch from the field's outline corner down to the tail convex,
    # the Column fan-out's notch below that corner bridged, before the convex sides (a tail wider than F's bottom puts
    # that side's widest point below it); regular as it is made (nothing else merges), its corner held.
    kept = set(anchors)
    if flank is not None:
        convex = _convex_flank(ring, level, anchors, flank, rules)
        if convex is not None:
            ring, kept = _round_ring(convex[0]), kept | convex[1]
    # Convex sides (diagonal-bus/9): each side's dents from the tip corner down to its widest point bridged by its hull,
    # no deeper than ``depth`` to the outline as filleted; the hull's flatter corners merged again, its widest points
    # staying.
    convex, widest = _convex_sides(ring, level, _round_ring(_filleted(ring, rules)[0]), anchors, depth)
    if widest:
        ring = _round_ring(_regular(convex, kept | set(widest)))
    ring, smallest = _filleted(ring, rules)
    ring = _round_ring(ring)
    if whole:
        return ring, smallest
    west_index, west_point = _side_cut(ring, level, -1, first=True)
    east_index, east_point = _side_cut(ring, level, 1, first=True)
    count = len(ring)
    path = [east_point] + [ring[(east_index + k) % count] for k in range((west_index - east_index) % count + 1)] + [west_point]
    return clean_polyline([[round6(x), round6(y)] for x, y in path]), smallest


def _filleted(ring: list[list[float]], rules: Rules) -> tuple[list[list[float]], float | None]:
    """The union's concave corners filleted (:func:`engine.geometry.fillet_concave_corners`, the profile's radius,
    ``_SHARED_MIN_TURN``): ``(ring, smallest fillet radius)``."""

    return fillet_concave_corners(ring, rules.fillet_radius, arc_step_rad=rules.arc_step, min_turn_rad=_SHARED_MIN_TURN / rules.fillet_radius)


def _flush(rings: list[list[list[float]]], level: float, x: float, side: int) -> tuple | None:
    """The direction (downward) in which a ring's own side runs on below ``level`` from the union's point on it (``x``;
    ``side`` -1 west, +1 east), where a ring's side passes that point (within a grid step: a tail flush with the union's
    side), the outermost of them; ``None`` where none does (each board steps in along the level from it)."""

    best = None
    for ring in rings:
        index, point = _side_cut(ring, level, side)
        if abs(point[0] - x) > _GRID_STEP_MM:
            continue
        direction = _minus(ring[(index - side) % len(ring)], point)
        if best is None or _cross(best, direction) * side > 0.0:
            best = direction
    return best


def _run_on(side: list[list[float]], x: float, run: float, flush: tuple | None = None) -> float:
    """Where a side of the union (top to bottom, its last point on the level) runs on to the height ``run``: along a
    board's own side where it runs on below the union's point on the level (``flush``, :func:`_flush`: the corner the
    board has there is the union's, regular and filleted with it), else along its last edge, so a straight side meeting
    the level at a slant has no corner there (diagonal-bus/4 ran every side on straight down and filleted that corner
    across the level); straight down from ``x`` where the union steps out along the level to it, where that edge lies
    along the level, or where it lies flatter than 45 degrees."""

    end = side[-1]
    if abs(x - end[0]) > _GRID_STEP_MM or len(side) < 2:
        return round6(x)
    rise = side[-2][1] - end[1] if flush is None else -flush[1]
    run_x = end[0] - side[-2][0] if flush is None else flush[0]
    if rise <= _NOISE_MM or abs(run_x) > rise:
        return round6(x)
    return round6(end[0] + run_x * (end[1] - run) / rise)


def _spliced(shared: list[list[float]], ring: list[list[float]], level: float, rules: Rules) -> tuple[list[list[float]], float | None]:
    """A board's outline: the shared path (:func:`_union_above`, its frame) above ``level`` and the board's own ring below
    it (its tail), the joins filleted: ``(ring, smallest fillet radius of the joins)``.

    On each side, where the board's own side lies outside the shared path's
    end just below the level (its tail stepping out along the level), it
    runs on along the level to it; where it lies inside, the board steps in
    along the level, or, where the shared path ends heading outward (the
    other board's fillet into its own wider tail), runs straight down a
    fillet radius first and steps in there."""

    count = len(ring)
    ends = {-1: shared[-1], 1: shared[0]}
    before = {-1: shared[-2] if len(shared) > 1 else shared[-1], 1: shared[1] if len(shared) > 1 else shared[0]}
    cuts, joins = {}, {}
    for side in (-1, 1):
        end = ends[side]
        index, point = _side_cut(ring, level, side)
        inward = (point[0] - end[0]) * -side  # > 0: the board's own side lies inside the shared end
        joins[side] = []
        if inward > _GRID_STEP_MM:
            dx, dy = (end[0] - before[side][0]) * side, before[side][1] - end[1]  # outward, downward
            if dx > dy:
                # The shared path ends heading outward: straight down a fillet radius, then in to its own side.
                low = round6(level - rules.fillet_radius)
                index, point = _side_cut(ring, low, side)
                joins[side] = ([[end[0], low]] if (point[0] - end[0]) * -side > _GRID_STEP_MM else [])
            joins[side] = joins[side] + [point]
        elif inward < -_GRID_STEP_MM:
            joins[side] = [point]
        cuts[side] = index
    west_index, east_index = cuts[-1], cuts[1]
    middle = [list(ring[(west_index + 1 + k) % count]) for k in range((east_index - west_index - 2) % count + 1)]
    path = list(shared) + joins[-1] + middle + joins[1][::-1]
    # The shared path and the board's own tail stay; the joins' corners are filleted.
    joined = {tuple(point) for point in joins[-1] + joins[1]}
    fixed = list(shared) + [point for point in ring if tuple(point) not in joined]
    return fillet_concave_corners(path, rules.fillet_radius, arc_step_rad=rules.arc_step, fixed=fixed,
                                  min_turn_rad=_SHARED_MIN_TURN / rules.fillet_radius)


# --------------------------------------------------------------------------
# Regular outlines: no corner flatter than REGULAR_TURN_DEG.
# --------------------------------------------------------------------------


def _regular(ring: list[list[float]], anchors: Any) -> list[list[float]]:
    """The counter-clockwise ``ring`` made regular: a ring on or outside it whose vertices turn by ``REGULAR_TURN_DEG``
    or more, but at ``anchors`` (a container of ``(x, y)`` tuples: vertices that stay where they are, at any turn).

    Each edge is a line; while a vertex other than an anchor turns by less
    than the threshold, the flattest one goes and its two lines become one
    (:func:`_fit`: the outer hull edge of the original vertices they cover,
    at the middle of their chord; through an anchor at an end), every vertex
    the meeting of its two lines.  A long smooth curve (flat turns adding up
    to far more than the threshold) becomes a polygon whose corners turn by
    the threshold or more, each edge covering a few degrees of it.  A line
    left pointing backward between its two corners (the lines beside it moved
    out past it) is merged likewise at its flatter end.  Every line keeps the
    original vertices it covers on or inside it, so the ring only grows (the
    clearances to it only grow); a run between two anchors bulging outward
    stays as it is.
    """

    points = [[float(point[0]), float(point[1])] for point in ring]
    # A vertex within a grid step of the next is one corner with it (a repeated vertex, or its turn split over a
    # nanometre edge): the next one goes, or this one where the next is an anchor.  Collinear vertices stay (an anchor
    # may lie on a straight edge); they turn by nothing and merge below.
    index = 0
    while index < len(points) and len(points) > 3:
        following = (index + 1) % len(points)
        offset = _minus(points[following], points[index])
        if _dot(offset, offset) >= _GRID_STEP_MM * _GRID_STEP_MM:
            index += 1
        elif tuple(points[following]) in anchors and tuple(points[index]) not in anchors:
            del points[index]
        else:
            del points[following]
            index = min(index, len(points) - 1) if following else index
    count = len(points)
    fixed = [tuple(point) in anchors for point in points]
    # Line ``index`` runs from vertex ``index`` to vertex ``end[index]`` (original vertices, cyclic).
    end = [(index + 1) % count for index in range(count)]
    before = [(index - 1) % count for index in range(count)]
    lines = [(points[index], _minus(points[end[index]], points[index])) for index in range(count)]
    alive = [True] * count
    stuck = [False] * count
    refit = [False] * count  # a line other than its original edge
    turns = [abs(_turn(lines[before[index]][1], lines[index][1])) for index in range(count)]
    while True:
        node = None
        for index in range(count):
            if alive[index] and not fixed[index] and not stuck[index] and turns[index] < _REGULAR_TURN:
                if node is None or turns[index] < turns[node]:
                    node = index
        if node is None:
            node = _backward(points, lines, end, before, alive, fixed, stuck, refit, turns)
            if node is None:
                break
        first, last = before[node], end[node]
        line = _fit(points, first, last, fixed[first], fixed[last])
        if line is None:
            stuck[node] = True
            continue
        alive[node] = False
        lines[first], end[first], before[last], refit[first] = line, last, first, True
        turns[first] = abs(_turn(lines[before[first]][1], line[1]))
        turns[last] = abs(_turn(line[1], lines[last][1]))
    start = alive.index(True)
    answer, index = [], start
    while True:
        answer.append(_corner(points, lines, before, fixed, refit, index))
        index = end[index]
        if index == start:
            return answer


def _regular_own(ring: list[list[float]], tail: tuple) -> list[list[float]]:
    """A board's own outline before its fillets (counter-clockwise, tail down) made regular, its tail ``(x, width,
    root)`` from the root down as built: every vertex at or below the root an anchor, and the root's two corners put
    back where a side runs on straight into the tail (an edge through them keeps its line)."""

    x, width, root = tail
    points = [list(point) for point in ring]
    for corner in ([x, root], [round6(x + width), root]):
        if any(abs(point[0] - corner[0]) <= _NOISE_MM and abs(point[1] - corner[1]) <= _NOISE_MM for point in points):
            continue
        for index in range(len(points)):
            a, b = points[index], points[(index + 1) % len(points)]
            if min(a[1], b[1]) < root < max(a[1], b[1]) and abs(_cross(_minus(b, a), _minus(corner, a))) <= _NOISE_MM * abs(b[1] - a[1]):
                points.insert(index + 1, corner)
                break
    return _regular(points, {tuple(point) for point in points if point[1] <= root + _NOISE_MM})


def _minus(a: Any, b: Any) -> tuple[float, float]:
    return (a[0] - b[0], a[1] - b[1])


def _cross(a: Any, b: Any) -> float:
    return a[0] * b[1] - a[1] * b[0]


def _dot(a: Any, b: Any) -> float:
    return a[0] * b[0] + a[1] * b[1]


def _turn(first: Any, second: Any) -> float:
    """The signed turn (rad) from direction ``first`` to direction ``second``."""

    return math.atan2(_cross(first, second), _dot(first, second))


def _corner(points: list[list[float]], lines: list[tuple], before: list[int], fixed: list[bool], refit: list[bool],
            index: int) -> list[float]:
    """Vertex ``index``: the original vertex where it is an anchor or between two original edges (bit for bit), or where
    its two lines are parallel (a vertex left stuck), else the meeting of its two lines."""

    if fixed[index] or not (refit[before[index]] or refit[index]):
        return list(points[index])
    (p, d), (q, e) = lines[before[index]], lines[index]
    denominator = _cross(d, e)
    if denominator == 0.0:
        return list(points[index])
    along = _cross(_minus(q, p), e) / denominator
    return [p[0] + along * d[0], p[1] + along * d[1]]


def _outside(direction: Any, offset: Any) -> bool:
    """Whether a point ``offset`` from a line's point lies outside it (right of ``direction``) by more than a grid step."""

    cross = _cross(direction, offset)
    return cross < 0.0 and cross * cross > _GRID_STEP_MM * _GRID_STEP_MM * _dot(direction, direction)


def _fit(points: list[list[float]], first: int, last: int, fixed_first: bool, fixed_last: bool) -> tuple | None:
    """One line ``(point, direction)`` with the original vertices ``first`` .. ``last`` (cyclic) on or inside it (within
    a grid step): through both ends where both are anchors (``None`` where a vertex bulges beyond that chord), through
    the anchored end and tangent to the rest, else the outer hull edge of the vertices over the middle of their chord
    (the edge that adds the least area over a convex run)."""

    count = len(points)
    span = [points[(first + step) % count] for step in range((last - first) % count + 1)]
    head, tail = span[0], span[-1]
    chord = _minus(tail, head)
    if fixed_first and fixed_last:
        return None if any(_outside(chord, _minus(point, head)) for point in span) else (head, chord)
    if fixed_first or fixed_last:
        pivot, direction = (head, chord) if fixed_first else (tail, chord)
        for _ in range(len(span)):
            moved = False
            for point in span:
                offset = _minus(point, pivot)
                if _outside(direction, offset):
                    direction = offset if fixed_first else (-offset[0], -offset[1])
                    moved = True
            if not moved:
                break
        return pivot, direction
    # The lower hull in (along the chord, across it: negative outward), the points in order along the chord.
    keyed = sorted((_dot(_minus(point, head), chord), _cross(chord, _minus(point, head)), step) for step, point in enumerate(span))
    hull: list[tuple] = []
    for item in keyed:
        while len(hull) > 1 and (hull[-1][0] - hull[-2][0]) * (item[1] - hull[-2][1]) - (hull[-1][1] - hull[-2][1]) * (item[0] - hull[-2][0]) <= 0.0:
            hull.pop()
        hull.append(item)
    middle = _dot(chord, chord) / 2
    edge = 0
    while edge + 2 < len(hull) and hull[edge + 1][0] <= middle:
        edge += 1
    start, finish = span[hull[edge][2]], span[hull[edge + 1][2]]
    return start, _minus(finish, start)


def _backward(points: list[list[float]], lines: list[tuple], end: list[int], before: list[int], alive: list[bool],
              fixed: list[bool], stuck: list[bool], refit: list[bool], turns: list[float]) -> int | None:
    """The vertex to merge at for the first line that points backward between its two corners (its flatter end that is
    no anchor), or ``None``."""

    for index in range(len(points)):
        if not alive[index]:
            continue
        start = _corner(points, lines, before, fixed, refit, index)
        finish = _corner(points, lines, before, fixed, refit, end[index])
        if _dot(_minus(finish, start), lines[index][1]) > 0.0:
            continue
        ends = [node for node in (index, end[index]) if not fixed[node] and not stuck[node]]
        if ends:
            return min(ends, key=lambda node: (turns[node], node))
    return None


# --------------------------------------------------------------------------
# Straight sides: one line from the tip corner down to the widest point (diagonal-bus/7).
# --------------------------------------------------------------------------


def _straight_sides(ring: list[list[float]], level: float, run: float, rings: list[list[list[float]]],
                    rounded: list[list[float]] | None = None) -> list[list[float]]:
    """The union above the shared level (counter-clockwise, made regular, y-monotone above ``level``, its sides running on down
    to ``run``) with straight sides (diagonal-bus/7, P5-diagonal-bus.md section 17): on each side the stretch from the
    tip corner down to the side's widest point above the level (its outermost, the highest such) becomes one straight
    line, and the stretch from there down to the level another, wherever one line encloses the stretch lying no more
    than ``SIDE_STRAIGHTEN_MM`` outside it anywhere: outside ``rounded``, the ring with its concave corners filleted as
    the board will have them (the old outline; ``ring`` itself where ``None``), whose stretch's corners lie on or inside
    the line wherever the ring's do.

    The upper line runs through the widest point, tangent to the stretch
    (the supporting line of its convex hull there: every vertex on or inside
    it, the least added), and the tip corner moves out along the top edge to
    meet it.  The lower one is the chord from the widest point to the side's
    point on the level: below the level each board keeps its own outline
    (``rings``, the boards' own), so that end stays.  A line is taken where
    no vertex of its stretch lies more than ``SIDE_STRAIGHTEN_MM`` inside it
    and the tip corner moves no farther; a line ending on the level must run
    on straight into every board's own side through that point, or meet it
    at a convex corner of ``REGULAR_TURN_DEG`` or more (a concave one would
    stay unfilleted on the board, a flatter one would be no corner), and
    the union's side must run on below the level in one edge, which then
    follows the line (:func:`_run_on`'s rule).  Elsewhere (a curved side, a
    side following a receding field, a step out to the other board's body)
    the side keeps its polyline.  Every vertex of the old outline lies on or
    inside the new one, so every clearance to it only grows.
    """

    rounded = ring if rounded is None else rounded
    for side in (-1, 1):
        if side < 0:
            straight = _straight_west(ring, level, run, rings, rounded)
        else:
            straight = _straight_west(_mirrored(ring), level, run, [_mirrored(own) for own in rings], _mirrored(rounded))
        if straight is not None:
            ring = straight if side < 0 else _mirrored(straight)
    return ring


def _mirrored(ring: list[list[float]]) -> list[list[float]]:
    """A counter-clockwise ring mirrored about the y axis, still counter-clockwise: its east side west."""

    return [[-point[0], point[1]] for point in reversed(ring)]


def _straight_west(ring: list[list[float]], level: float, run: float, rings: list[list[list[float]]],
                   rounded: list[list[float]]) -> list[list[float]] | None:
    """The ring with its west side straight (:func:`_straight_sides`), or ``None`` where neither stretch becomes a line;
    the bound measured to ``rounded`` (the ring filleted)."""

    count = len(ring)
    top = _top_corners(ring)[0]
    side = [top]  # the side's vertices above the level, from the tip corner down
    below = (top + 1) % count
    while ring[below][1] > level + _NOISE_MM and len(side) < count:
        side.append(below)
        below = (below + 1) % count
    a, b = ring[side[-1]], ring[below]
    on_level = b[1] >= level - _NOISE_MM
    end = list(b) if on_level else [a[0] + (b[0] - a[0]) * (level - a[1]) / (b[1] - a[1]), level]
    points = [ring[index] for index in side] + [end]
    last = len(points) - 1
    least = min(point[0] for point in points)
    widest = next(k for k, point in enumerate(points) if point[0] <= least + _GRID_STEP_MM)
    # The old outline's side as filleted, split at the widest point (a convex corner: no fillet moves it) into the
    # stretches above and below it, for the bound.
    filleted = _side_down(rounded, level, -1)
    split = next((k for k, point in enumerate(filleted) if abs(point[0] - points[widest][0]) <= _GRID_STEP_MM
                  and abs(point[1] - points[widest][1]) <= _GRID_STEP_MM), None)
    above, beneath = (points[:widest], points[widest + 1:last]) if split is None else (filleted[:split], filleted[split + 1:-1])
    # A line ending on the level other than along the side's last edge there changes the side below the level: it is
    # taken where the union's side runs on below the level in one edge (the run, which then follows the line), not along
    # the level (a step out to a wider board), and meets every board's own side through that point (``afters``) straight
    # on or at a convex corner of REGULAR_TURN_DEG or more.
    bottom = (below + 1) % count if on_level else below
    afters = [] if ring[bottom][1] <= run + _NOISE_MM else None
    if afters is not None:
        for own in rings:
            index, point = _side_cut(own, level, -1, first=True)
            if abs(point[0] - end[0]) <= _GRID_STEP_MM:
                following = own[(index + 1) % len(own)]
                if abs(following[1] - level) <= _NOISE_MM:
                    following = own[(index + 2) % len(own)]
                afters.append(_minus(following, point))

    def ends(direction: Any) -> bool:
        return not _off(direction, end, points[last - 1]) or (afters is not None and all(_meets(direction, after) is not None for after in afters))

    upper = _side_line(ring, top, points, widest, above) if widest >= 2 else None
    if upper is not None and widest == last and not ends(upper[1]):
        upper = None
    lower = None
    if last - widest >= 2:
        pivot = points[widest]
        chord = _minus(end, pivot)
        inner = points[widest + 1:last]
        steep = chord[0] <= 0.0 or chord[0] <= -chord[1]  # heading in flatter than 45 degrees it would run on concave
        if (chord[1] < 0.0 and steep and not any(_outside(chord, _minus(point, pivot)) for point in inner)
                and _within(chord, pivot, beneath) and ends(chord)):
            lower = chord
    # Above the level the widest point stays a corner of REGULAR_TURN_DEG or more: a line that would leave it flatter
    # is not taken (the lower one first).
    if widest < last:
        for upper_, lower_ in ((upper, lower), (upper, None), (None, lower), (None, None)):
            arriving = upper_[1] if upper_ is not None else _minus(points[widest], points[widest - 1]) if widest else None
            leaving = lower_ if lower_ is not None else _minus(points[widest + 1], points[widest])
            if (upper_, lower_) == (None, None) or arriving is None or abs(_turn(arriving, leaving)) >= _REGULAR_TURN:
                upper, lower = upper_, lower_
                break
    if upper is None and lower is None:
        return None
    kept = [list(point) for point in points[:last]]  # the new side above the level, top down
    arrival = None  # the line's direction where it ends on the level, where it changes the side there
    if upper is not None:
        kept = [upper[0]] + kept[widest:]
        if widest == last:
            arrival = upper[1]
    if lower is not None:
        kept = kept[:len(kept) - (last - widest - 1)]
        arrival = lower
    if arrival is not None and not _off(arrival, end, points[last - 1]):
        arrival = None  # along the side's last edge: the side runs on below the level as it did
    rest = [list(ring[(below + k) % count]) for k in range((side[0] - below) % count)]
    if arrival is None:
        answer = kept + rest
    elif abs(arrival[0]) > -arrival[1]:
        # The union runs on below the level straight down where the line lies flatter than 45 degrees (heading out: a
        # convex corner on the level), else along the line, as :func:`_run_on` would.
        answer = kept + [list(end), [end[0], run]] + rest[(bottom - below) % count + 1:]
    else:
        answer = kept + [[end[0] + arrival[0] * (run - end[1]) / arrival[1], run]] + rest[(bottom - below) % count + 1:]
    first = tuple(ring[0])
    start = next((index for index, point in enumerate(answer) if tuple(point) == first), 0)
    return answer[start:] + answer[:start]


def _convex_sides(ring: list[list[float]], level: float, rounded: list[list[float]], anchors: Any, depth: float) -> tuple:
    """The union above the shared level (counter-clockwise, made regular, given straight sides and, one-sided, a convex
    flank, y-monotone above ``level``) with each side's stretch from the tip corner down to its widest point convex
    (diagonal-bus/9, P5-diagonal-bus.md section 24): ``(ring, widest points)``, the ring itself and no points where
    nothing changes.

    Per side, the stretch's convex hull (the hull of its vertices, in their
    order): each dent between two consecutive corners of the hull (a run of
    the side inside the hull's edge: the kink where the lanes start beside
    a narrow tip, a short step of the staircase) becomes that edge wherever
    no point of the dent lies deeper than ``depth`` inside it (a step of
    :data:`CHAMFER_STEP_CELLS` cells, the depth to which F's notches are
    chamfered; measured to ``rounded``, the ring with its concave corners
    filleted as the boards have them, as section 17's bound is) and no
    anchor lies in it, and where the tip corner and the widest point stay
    corners of ``REGULAR_TURN_DEG`` or more.  A deeper pocket keeps its
    outline.  The hull's corners flatter than that merge afterwards
    (:func:`_regular`, the widest points held), so the tip corner may move
    out along the top edge (0.81 mm on the user's crank 32 x 32 of section
    14, micrometres on most); the widest point stays;
    every vertex of the old outline lies on or inside the new one, so every
    clearance only grows and no board is wider.  The convex bend where a
    side turns down beside the field's widest rows into the funnel lies on
    the hull and stays.
    """

    widest: list = []
    for side in (-1, 1):
        if side < 0:
            convex = _convex_west(ring, level, rounded, anchors, depth)
        else:
            convex = _convex_west(_mirrored(ring), level, _mirrored(rounded), {(-x, y) for x, y in anchors}, depth)
        if convex is not None:
            ring = convex[0] if side < 0 else _mirrored(convex[0])
            x, y = convex[1]
            widest.append((x, y) if side < 0 else (-x, y))
    return ring, widest


def _convex_west(ring: list[list[float]], level: float, rounded: list[list[float]], anchors: Any, depth: float) -> tuple | None:
    """The ring with its west side's stretch from the tip corner to its widest point convex (:func:`_convex_sides`) and
    that widest point, or ``None`` where no dent is bridged."""

    count = len(ring)
    top = _top_corners(ring)[0]
    side = [top]  # the side's vertices above the level, from the tip corner down
    below = (top + 1) % count
    while ring[below][1] > level + _NOISE_MM and len(side) < count:
        side.append(below)
        below = (below + 1) % count
    points = [ring[index] for index in side]
    least = min(point[0] for point in points)
    widest = next(k for k, point in enumerate(points) if point[0] <= least + _GRID_STEP_MM)
    if widest < 2:
        return None
    # The hull of the stretch, in its order (y-monotone): a vertex turning right (concave) or straight on goes.
    hull: list[int] = []
    for k in range(widest + 1):
        while len(hull) >= 2 and _cross(_minus(points[hull[-1]], points[hull[-2]]), _minus(points[k], points[hull[-1]])) <= 0.0:
            hull.pop()
        hull.append(k)
    if len(hull) == widest + 1:
        return None
    filleted = _side_down(rounded, level, -1)

    def where(point: Any) -> int | None:
        return next((k for k, other in enumerate(filleted) if abs(other[0] - point[0]) <= _GRID_STEP_MM and abs(other[1] - point[1]) <= _GRID_STEP_MM), None)

    arriving = _minus(ring[top], ring[(top - 1) % count])  # the top edge, into the tip corner
    leaving = _minus(ring[side[widest + 1]] if widest + 1 < len(side) else ring[below], points[widest])  # on from the widest point
    kept = [list(points[0])]
    bridged = False
    for u, v in zip(hull, hull[1:]):
        dent = points[u + 1:v]
        if dent:
            # The dent as the boards have it (its concave corners filleted; the hull's corners, convex, are no fillet's).
            first, last = where(points[u]), where(points[v])
            if first is not None and last is not None and last > first + 1:
                dent = filleted[first + 1:last]
            direction = _minus(points[v], points[u])
            length = math.sqrt(_dot(direction, direction))
            deep = max(_cross(direction, _minus(point, points[u])) / length for point in dent)
            corners_hold = (u > 0 or abs(_turn(arriving, direction)) >= _REGULAR_TURN) and (v < widest or abs(_turn(direction, leaving)) >= _REGULAR_TURN)
            if deep <= depth + _NOISE_MM and corners_hold and not any(tuple(point) in anchors for point in points[u + 1:v]):
                bridged = True
            else:
                kept += [list(point) for point in points[u + 1:v]]
        kept.append(list(points[v]))
    if not bridged:
        return None
    rest = [list(ring[index]) for index in side[widest + 1:]] + [list(ring[(below + k) % count]) for k in range((side[0] - below) % count)]
    answer = kept + rest
    first_point = tuple(ring[0])
    start = next((index for index, point in enumerate(answer) if tuple(point) == first_point), 0)
    return answer[start:] + answer[:start], tuple(points[widest])


def _convex_flank(ring: list[list[float]], level: float, anchors: Any, y_field: float, rules: Rules) -> tuple | None:
    """The union above the shared level of a one-sided bus (counter-clockwise, made regular and given straight sides,
    y-monotone above ``level``) with its east side, the inner flank without lanes, convex from the field's outline
    corner down to the tail (diagonal-bus/11, P5-diagonal-bus.md section 27.8): ``(ring, corners)``, the corner among
    the points the regularization keeps where it is a vertex of the new side, or ``None`` where nothing changes.

    The field's outline corner is the side's outermost point on F's bottom
    ``y_field`` (a vertex, or where the side runs straight on past it).  The
    tail's corner is the top of the side's last run straight down into the
    level along a tail's edge (else its last vertex above the level); it and
    the junction into the tail before it (its corners turning in or on
    straight) stay.  The stretch from the field's outline corner down to the
    last convex corner before that junction becomes its convex hull (the
    hull of its vertices, in their order): each dent between two consecutive
    corners of the hull (the Column fan-out's notch: its body's corner, the
    ledge in to its outermost route and that route's turn into the V; a side
    running on straight below F's bottom before it reaches out to a wider
    tail) becomes that edge wherever no anchor lies in it and the field's
    outline corner stays a corner of ``REGULAR_TURN_DEG`` or more.  Where the
    edge from that corner meets the next edge flatter than that (the hull's
    tangent to a long V slope nearly along the slope), its end moves back
    along the next edge's line to where the two meet at a degree more, so no
    corner merges later and the next edge's line, the copper's, stays.  A
    change that would leave any corner of the side flatter is not made, nor
    one that, as filleted, moves the side's straight run down a tail's edge
    (the rolling circle into the tail reaches past short edges) or leaves a
    point of the old flank outside the new one: the stretch then ends a
    corner higher, else the side stays, so the tails' roots and the copper do
    not move.  No depth
    bounds it: below F's bottom the flank follows no field, only the
    fan-out's copper, which the hull keeps inside.  Every vertex of the old
    outline lies on or inside the new one, so every clearance only grows; the
    board is no wider (the new side spans the stretch's x range).
    """

    convex = _flank_west(_mirrored(ring), level, {(-x, y) for x, y in anchors}, y_field, rules)
    if convex is None:
        return None
    return _mirrored(convex[0]), {(-x, y) for x, y in convex[1]}


def _flank_west(ring: list[list[float]], level: float, anchors: Any, y_field: float, rules: Rules) -> tuple | None:
    """The ring with its west side's stretch from the field's outline corner down to the tail convex
    (:func:`_convex_flank`) and that corner where it is a vertex of the new side (a set, empty where the side runs on
    straight through it), or ``None`` where no dent is bridged."""

    count = len(ring)
    top = _top_corners(ring)[0]
    side = [top]  # the side's vertices above the level, from the tip corner down
    below = (top + 1) % count
    while ring[below][1] > level + _NOISE_MM and len(side) < count:
        side.append(below)
        below = (below + 1) % count
    points = [list(ring[index]) for index in side] + [list(ring[below])]  # and the first vertex on or below the level
    on = [k for k in range(len(points) - 1) if abs(points[k][1] - y_field) <= _GRID_STEP_MM]  # on the layout grid
    if on:
        start = min(on, key=lambda k: (points[k][0], -k))
    else:
        # The side runs straight on past F's bottom: its point there is the corner.
        start = next((k for k in range(1, len(points) - 1) if points[k][1] < y_field), None)
        if start is None:
            return None
        a, b = points[start - 1], points[start]
        points.insert(start, [round6(a[0] + (b[0] - a[0]) * (y_field - a[1]) / (b[1] - a[1])), y_field])
    rest = [list(ring[(below + k) % count]) for k in range(1, (side[0] - below) % count)]
    first_point = tuple(ring[0])

    def turning(k: int) -> float:
        return _cross(_minus(points[k], points[k - 1]), _minus(points[k + 1], points[k]))  # > 0: convex

    def joined(side_points: list[list[float]]) -> list[list[float]]:
        answer = side_points + rest
        begin = next((index for index, point in enumerate(answer) if tuple(point) == first_point), 0)
        return answer[begin:] + answer[:begin]

    # The tail's corner, then back over the junction into the tail (corners turning in or on straight) to the last convex
    # corner: the stretch's end.
    end = len(points) - 2
    if abs(points[-1][0] - points[end][0]) <= _GRID_STEP_MM:
        while end > start and abs(points[end - 1][0] - points[end][0]) <= _GRID_STEP_MM:
            end -= 1
    while end > start and turning(end) <= 0.0:
        end -= 1
    # As the boards have it (filleted): the side's straight runs down the tails' sides, which set the level, the same
    # (the rolling circle into the tail reaches past short edges), and the old flank on or inside the new one (to a grid
    # step: no vertex of either flank on the wrong side of the other).
    fillets = _filleted(ring, rules)[0]
    straight = _tails_straight(fillets, level)
    flank = [point for point in _side_down(fillets, level, -1) if point[1] < y_field + _NOISE_MM]

    def outside(point: Any, polygon: list[list[float]]) -> bool:
        return not point_in_polygon(point, polygon) and min(point_segment_distance(point, a, b) for a, b in polygon_edges(polygon)) > _GRID_STEP_MM

    def inside(point: Any, polygon: list[list[float]]) -> bool:
        return point_in_polygon(point, polygon) and min(point_segment_distance(point, a, b) for a, b in polygon_edges(polygon)) > _GRID_STEP_MM

    while end - start >= 2:
        for kept, held in _flank_stretches(points, start, end, anchors, not on):
            convex = joined(points[:start] + kept + points[end + 1:])
            filleted = _filleted(convex, rules)[0]
            if (abs(_tails_straight(filleted, level) - straight) <= _NOISE_MM and not any(outside(point, filleted) for point in flank)
                    and not any(inside(point, fillets) for point in _side_down(filleted, level, -1) if point[1] < y_field + _NOISE_MM)):
                return convex, held
        end -= 1
        while end > start and turning(end) <= 0.0:
            end -= 1
    return None


def _flank_stretches(points: list[list[float]], start: int, end: int, anchors: Any, inserted: bool) -> Any:
    """The stretch ``points[start:end + 1]`` of a west side made convex (:func:`_convex_flank`), in order of preference:
    each ``(new stretch, held)``, the corner in ``held`` where it is a vertex of the new side.  The dents of the stretch's
    hull that may be bridged (deeper than a grid step, no anchor in them, the corner turning by ``REGULAR_TURN_DEG`` or
    more), all of them first, then the first ones only (the nearest the corner), then each other one alone; from the
    tail up, each bridge meeting the next edge flatter than ``REGULAR_TURN_DEG`` has its end moved back along that
    edge's line, and each leaving the edge before it flatter (but at the corner) its start moved on along that edge's
    line, to where the two meet at a degree more; a choice leaving any corner of the side flatter is passed over.
    ``inserted``: the corner is a point put on F's bottom."""

    stretch = points[start:end + 1]
    # The hull of the stretch, in its order (y-monotone): a vertex turning right (concave) or straight on goes.
    hull: list[int] = []
    for k in range(len(stretch)):
        while len(hull) >= 2 and _cross(_minus(stretch[hull[-1]], stretch[hull[-2]]), _minus(stretch[k], stretch[hull[-1]])) <= 0.0:
            hull.pop()
        hull.append(k)
    arriving = _minus(stretch[0], points[start - 1])  # down the side into the corner
    dents = []
    for u, v in zip(hull, hull[1:]):
        dent = stretch[u + 1:v]
        if dent:
            direction = _minus(stretch[v], stretch[u])
            length = math.sqrt(_dot(direction, direction))
            deep = max(_cross(direction, _minus(point, stretch[u])) / length for point in dent)
            if (deep > _GRID_STEP_MM and (u > 0 or abs(_turn(arriving, direction)) >= _REGULAR_TURN)
                    and not any(tuple(point) in anchors for point in dent)):
                dents.append(u)
    following = points[end + 1]  # the junction into the tail
    spare = _REGULAR_TURN + math.pi / 180  # a degree more
    cos, sin = math.cos(spare), math.sin(spare)
    # All the dents, then the first ones only (fewer and fewer), then each other one alone.
    choices = [dents[:count] for count in range(len(dents), 0, -1)] + [[u] for u in dents[1:]]
    for chosen in choices:
        kept = [stretch[0]]
        ends = []  # the indices in kept of the bridges' ends
        for u, v in zip(hull, hull[1:]):
            if u in chosen:
                ends.append(len(kept))
            else:
                kept += stretch[u + 1:v]
            kept.append(stretch[v])
        for index in reversed(ends):  # from the tail up: each bridge's next edge is as it will be
            # A bridge meeting the next edge flatter than REGULAR_TURN_DEG: its end moved back along that edge's line.
            begin, v = kept[index - 1], kept[index]
            out = _minus(kept[index + 1] if index + 1 < len(kept) else following, v)
            if abs(_turn(_minus(v, begin), out)) < _REGULAR_TURN:
                steeper = (out[0] * cos + out[1] * sin, out[1] * cos - out[0] * sin)
                denominator = _cross(steeper, out)
                reach, back = _cross(_minus(v, begin), out) / denominator, _cross(_minus(v, begin), steeper) / denominator
                if reach <= 0.0 or back >= 0.0:
                    break
                v = kept[index] = [round6(begin[0] + reach * steeper[0]), round6(begin[1] + reach * steeper[1])]
            # A bridge leaving the edge before it flatter than REGULAR_TURN_DEG (not at the corner, which stays): its start
            # moved on along that edge's line to where the two meet at a degree more (the edge before it, another bridge
            # among them, keeps its line).
            if index >= 2:
                before = kept[index - 2]
                into = _minus(begin, before)
                if abs(_turn(into, _minus(v, begin))) < _REGULAR_TURN:
                    wider = (into[0] * cos - into[1] * sin, into[0] * sin + into[1] * cos)
                    denominator = _cross(into, wider)
                    on, ahead = _cross(_minus(v, begin), wider) / denominator, -_cross(_minus(v, begin), into) / denominator
                    if on <= 0.0 or ahead <= 0.0:
                        break
                    kept[index - 1] = [round6(begin[0] + on * into[0]), round6(begin[1] + on * into[1])]
        else:
            held = {tuple(stretch[0])}
            if inserted and kept[1] is stretch[1]:
                # The side runs on straight through the point put on F's bottom: no corner there.
                kept, held = kept[1:], set()
            # Every corner of the new side REGULAR_TURN_DEG or more (none to merge), else the next choice.
            run = [points[start - 1]] + kept + [following]
            if all(abs(_turn(_minus(b, a), _minus(c, b))) >= _REGULAR_TURN for a, b, c in zip(run, run[1:], run[2:])):
                yield kept, held


def _side_line(ring: list[list[float]], top: int, points: list[list[float]], widest: int, above: list[list[float]]) -> tuple | None:
    """The upper stretch's line (:func:`_straight_west`): ``(new tip corner, its direction down)``, the line through the
    widest point ``points[widest]`` tangent to the stretch above it, or ``None`` where it lies more than
    ``SIDE_STRAIGHTEN_MM`` from a point of the stretch as filleted (``above``) or would move the tip corner farther (or
    inward)."""

    pivot, direction = _fit(points, 0, widest, False, True)
    if direction[1] >= 0.0:
        return None
    corner = ring[top]
    edge = _minus(corner, ring[top - 1])  # the top edge, arriving at the tip corner
    denominator = _cross(direction, edge)
    if denominator == 0.0:
        return None
    along = _cross(_minus(corner, pivot), edge) / denominator
    tip = [pivot[0] + along * direction[0], pivot[1] + along * direction[1]]
    move = _minus(tip, corner)
    length = _dot(move, move)
    if length > SIDE_STRAIGHTEN_MM * SIDE_STRAIGHTEN_MM or (_dot(move, edge) < 0.0 and length > _GRID_STEP_MM * _GRID_STEP_MM):
        return None
    return (tip, direction) if _within(direction, pivot, above) else None


def _off(direction: Any, pivot: Any, point: Any) -> bool:
    """Whether ``point`` lies more than a grid step from the line through ``pivot`` along ``direction``."""

    cross = _cross(direction, _minus(point, pivot))
    return cross * cross > _GRID_STEP_MM * _GRID_STEP_MM * _dot(direction, direction)


def _within(direction: Any, pivot: Any, points: list[list[float]]) -> bool:
    """Whether every point lies no more than ``SIDE_STRAIGHTEN_MM`` from the line through ``pivot`` along ``direction``."""

    bound = SIDE_STRAIGHTEN_MM * SIDE_STRAIGHTEN_MM * _dot(direction, direction)
    return all(_cross(direction, _minus(point, pivot)) ** 2 <= bound for point in points)


def _meets(direction: Any, after: Any) -> bool | None:
    """How a side's line arriving at its point on the level meets the side below it (``after``, from that point to the
    next vertex): ``False`` straight on (that vertex within a grid step of the line), ``True`` at a convex corner of
    ``REGULAR_TURN_DEG`` or more, ``None`` otherwise."""

    cross = _cross(direction, after)
    if cross * cross <= _GRID_STEP_MM * _GRID_STEP_MM * _dot(direction, direction) and _dot(direction, after) > 0.0:
        return False
    return True if _turn(direction, after) >= _REGULAR_TURN else None


# --------------------------------------------------------------------------
# The Row board.
# --------------------------------------------------------------------------


def _row_board(design: Mapping[str, Any], profile: Mapping[str, Any], geo: _Geo, built: Mapping[str, Any], sides: str, near: str) -> dict[str, Any]:
    """The Row board from a construction, turned back to the canonical frame when it was built mirrored."""

    rules = geo.rules
    flip = geo.flip
    order = built["order"]

    def turned(points: list) -> list[list[float]]:
        return [[round6(geo.aw - x), y] for x, y in points] if flip else [list(point) for point in points]

    ring = turned(built["ring"])
    if flip:
        ring.reverse()  # mirrored, the ring runs clockwise
    # The record measures the outline the board publishes (on the layout grid), back in this frame.
    published = _round_ring(ring)
    measured = _bus_metrics([[geo.aw - x, y] for x, y in published] if flip else published, geo, built)
    tail_x = round6(geo.aw - (built["tail_x"] + built["width"])) if flip else built["tail_x"]
    contact_order = [f"ROW_{k:02d}" for k in (reversed(order) if flip else order)]
    plan = {
        "role": "rows", "rows": geo.R, "columns": geo.C, "pitch_x": geo.px, "pitch_y": geo.py, "row_width": geo.rw,
        "column_width": geo.cw, "pins": built["pins"], "channels": geo.R, "tail_length": built["length"],
        "active": (0.0, 0.0, geo.aw, geo.ah), "tail_x": tail_x, "tail_width": built["width"], "tail_top": built["root"],
        "tip": built["tip"], "trace_width": geo.tw, "bundle_pitch": geo.bp, "rules": rules,
        "body": (0.0, built["root"], geo.aw, round6(geo.ah + rules.margin)),  # the neck runs up to the tail root
    }
    pads = _contacts(plan, contact_order, design["channel_order"]["rows"], rules)
    near_set = set(built["near_rows"])
    routes = []
    electrodes = []
    spans = row_frame_spans(design)
    for k in range(geo.R, 0, -1):
        lo, hi = spans[k - 1]
        row = geo.row(k)
        bounds = (round6(lo * geo.px - rules.overhang), row["y0"], round6(hi * geo.px + geo.cw + rules.overhang), row["y1"])
        electrodes.append(_electrode(f"ROW_{k:02d}", "row_electrode", bounds))
        tail, fanout = built["pieces"][k]
        extra = {"fanout": "diagonal_bus", "bus_side": "near" if k in near_set else "far"}
        routes.extend(_route_pieces(f"ROW_{k:02d}", turned(tail), turned(fanout), plan, extra))
    left_tip, right_tip = _tip_corners(tail_x, built["width"], built["tip"], rules)
    # The band's side as seen from outside the stack (this frame's west).
    west_name = near if sides == "both" else sides
    row_bus = {
        "kind": ROW_BUS_VERSION,
        "sides": sides,
        "near_side": west_name,
        "split": SPLIT if sides == "both" else None,
        "near_rows": list(built["near_rows"]),
        "far_rows": list(built["far_rows"]),
        "contact_order": contact_order,
        "tail_position": built["tail_position"],
        "tails": TAILS,
        "shared_outline_below_field_mm": round6(-built["level"]),
        "fans": [dict(fan) for fan in built["fans"]],
        **measured,
    }
    board = _assemble(
        plan=plan, design=design, profile=profile, outline=ring, cutouts=[], electrodes=electrodes, routes=routes, pads=pads,
        corners=(left_tip, right_tip), tail_extra={"row_contact_order": contact_order},
        construction={
            "minimum_concave_fillet_radius_mm": None if built["smallest"] is None else round6(built["smallest"]),
            "fanout_bundle_pitch_mm": geo.bp,
            "row_bus": row_bus,
        },
    )
    _masked_field_window(board, spans, rules, 1)
    _mark_masked(board, _with_mask(design), CLASSES, rules, 1)
    return board


def _extent_at(ring: list[list[float]], y: float) -> tuple[float, float]:
    """The outline's westmost and eastmost crossing at height ``y``."""

    xs = []
    count = len(ring)
    for index in range(count):
        (x0, y0), (x1, y1) = ring[index], ring[(index + 1) % count]
        if (y0 > y) != (y1 > y):
            xs.append(x0 + (x1 - x0) * (y - y0) / (y1 - y0))
    return min(xs), max(xs)


def _bus_metrics(ring: list[list[float]], geo: _Geo, built: Mapping[str, Any]) -> dict[str, Any]:
    """``construction.row_bus``'s measurements of the published outline (in this frame, near side west), at each
    row's centre, and of the lanes.

    F (P dilated by the active-edge margin) at row k spans ``[lo_k px - margin, hi_k px + cw + margin]``.
    ``tip_width_mm`` is the board's width at ROW_01's centre, ``tip_excess_mm`` that less F's width
    there; ``band_mm`` the largest overhang beyond F on each side; ``lane_angle_deg`` per side the least
    and the largest slope (from the vertical) of a lane's longest band segment (from its electrode's end
    down to the top of its ray); ``flat_lane_rows`` the rows whose band has a segment more than
    the steepest fan cap (:func:`bus_caps`, 85 degrees) from the vertical: a lane that leaves nearly flat, around the
    keep-out of a wider row below it; ``widest_mm`` the
    outline's width across the tail axis; ``tip_is_narrowest_relative``: no row whose part of F is at
    least as wide as the tip's has a narrower board than the tip (the tip is the thinnest part of the
    board wherever the field is not narrower than at the tip).
    """

    margin = geo.rules.margin
    widths, excesses, field_widths, near_bands, far_bands = [], [], [], [], []
    for row in geo.rows:
        west, east = _extent_at(ring, row["yc"])
        field_west, field_east = row["lo"] * geo.px - margin, row["hi"] * geo.px + geo.cw + margin
        widths.append(east - west)
        field_widths.append(round6(field_east - field_west))
        excesses.append(east - west - (field_east - field_west))
        near_bands.append(field_west - west)
        far_bands.append(east - field_east)
    relative = all(
        width >= widths[0] - 1e-6 for width, field in zip(widths, field_widths) if field >= field_widths[0] - 1e-6
    )
    angles: dict[str, Any] = {}
    flat = []
    for side, rows in (("near", built["near_rows"]), ("far", built["far_rows"])):
        slopes = []
        for k in rows:
            chain = built["hulls"][k]
            steps = [(b[0] - a[0], b[1] - a[1]) for a, b in zip(chain, chain[1:])]
            dx, dy = max(steps, key=lambda step: step[0] * step[0] + step[1] * step[1])
            slopes.append(math.degrees(math.atan2(abs(dx), abs(dy))))
            if any(math.atan2(abs(step[0]), abs(step[1])) > geo.cap + 1e-12 for step in steps):
                flat.append(k)
        angles[side] = [round6(min(slopes)), round6(max(slopes))] if slopes else None
    xs = [point[0] for point in ring]
    near_band, far_band = max(near_bands), max(far_bands)
    return {
        "tip_width_mm": round6(widths[0]),
        "tip_excess_mm": round6(excesses[0]),
        "band_mm": {"near": round6(near_band), "far": round6(far_band)},
        "lane_angle_deg": angles,
        "flat_lane_rows": sorted(flat),
        "widest_mm": round6(max(xs) - min(xs)),
        "tip_is_narrowest_relative": relative,
    }
