# Result and layout schema (`tactile-fpc-layout/v3`)

This is the contract of what `engine.generate_design()` returns, of the
`boards` in the `/api/generate` reply and of `derived-layout.json` in the
project review bundle.  The request side (design fields, aliases, JSON
Schema) is in [API.md](API.md); how the two boards meet the reader
connectors is in [INTEGRATION.md](INTEGRATION.md).
`tests/test_docs_consistency.py` checks the code, record and profile tables
below, the item kinds and anchors and the fixed values against generated
layouts.

## Frames, units and resolution

- Every length is in millimetres.  Each board has its own **Gerber frame**:
  X right, **Y up**, origin at the lower-left corner of the board's outline
  bounding box, seen from the **copper side** (the top view a Gerber viewer
  shows).  The two boards share a build identity, not a frame; they are
  registered on their taxel fields (`grid_registration.active_region`).
- Every coordinate lies on the **1e-6 mm layout grid** (6 decimals), the
  resolution of the emitted JSON and Gerber files.  Design numbers are taken
  on the same grid before validation and hashing, so `2`, `2.0` and
  `2.0000004` are one design.
- A board is built with its tail pointing down (-Y) and then turned as a
  whole, never mirrored, so that the tail exits `tail.side`; see
  [INTEGRATION.md](INTEGRATION.md) for where pin 1, `ROW_01` and `COL_01` end
  up on each side.

## The result object

| Key | Content |
| --- | --- |
| `ok` | `true` when the design validates and both boards pass the whole-board DRC |
| `design` | the canonical design (`tactile-fpc-design/v1`, nested, numbers on the grid) |
| `profile` | the locked manufacturing profile the build used: the one of the design's template (`generic_matrix_v1`: `jlc-fpc-standard-v1`; `surface_matrix_v1`: `jlc-fpc-surface-v1`, [below](#surface-template-profile-jlc-fpc-surface-v1)) |
| `validation` | `errors`, `warnings` (each `{code, field, message}`) and `normalization` (see [API.md](API.md)) |
| `boards` | `{row, column}`: the two board objects below; `{}` when input validation fails |
| `derived_layout` | `{format: "tactile-fpc-layout/v3", units: "mm", boards}`; Python only, the HTTP full view leaves it out (a client rebuilds it from `manifest.layout_format` and `boards`) |
| `manifest` | build identity and summary (`tactile-fpc-manifest/v2`, see [API.md](API.md)) |

Input errors (request, input, feasibility and profile codes) stop the build
before any geometry: `boards` is `{}`.  DRC errors come after the geometry is
built: `ok` is `false`, but `boards` holds the failing geometry and its
measurements for inspection, and every export is blocked.

## Board object

| Key | Content |
| --- | --- |
| `id` | `<physical_side>_<role>_fpc`, e.g. `top_rows_fpc` |
| `role` | `rows` (horizontal electrodes in its own frame) or `columns` |
| `physical_side` | `top` or `bottom` of the sensor stack, from `role_mapping` |
| `units` | `mm` |
| `fpc` | `is_flexible`, `construction` and a copy of `profile.stackup` |
| `grid_registration` | taxel field, electrode field, matrix size and pitches (below) |
| `tail` | connector tail record (below) |
| `outline` | `kind: "polygon"`, `layer: "board_outline"`, `points` (one ring) and `cutouts` (routed slots, rings) |
| `layers` | `top_copper` {`electrodes`, `routes`, `pads`}, `top_coverlay_openings`, `bottom_stiffener` |
| `construction` | construction values that are not rules (below) |
| `metrics` | outline size and bounding box, counts of channels, contacts, electrodes, routes, openings, stiffeners and cutouts; a [masked board](#masked-boards) adds `active_taxel_count` |
| `verification` | whole-board DRC summary, the 30 check records and the registration record (below) |
| `svg` | the copper-side top-view preview (see [API.md](API.md#svg-previews)) |

Rings (`outline.points`, each cutout, each stiffener's `points`) are
counter-clockwise lists of `[x, y]` without a repeated closing vertex.

### Rectangles and anchors

Electrodes, contacts and coverlay openings are rectangles with
`x, y, width_mm, height_mm` and an explicit `anchor`:

- `"center"`: `x, y` is the centre (connector contacts);
- `"lower_left"`: `x, y` is the lower-left corner (electrodes and openings).

`engine.geometry.rect_bounds()` is the one interpreter of an anchored
rectangle; the DRC, the SVG preview and the exporter all use it.  Layout v1
used the same keys with two meanings and no anchor (audit M11, the cause of
C1); v2 is not readable by v1 consumers.

**Compatibility.**  Layout v3 (2026-10-15, generator 0.4.0) has two route
objects per net, each with a `segment` key (below); v2 had one route of one
width per net.  A v2 consumer that takes one route per net reads only a part
of each net in v3.  Every build id changed with v3.

### `layers.top_copper`

| Item | Keys | Notes |
| --- | --- | --- |
| electrode | `net, kind, anchor, x, y, width_mm, height_mm` | `kind` `row_electrode` or `column_electrode`; nets `ROW_01`... / `COL_01`... (two digits or more); `lower_left` |
| route | `net, kind, segment, width_mm, points, fanout`, Column also `fanout_group`, diagonal Row bus also `bus_side` | `kind: "polyline"`, one constant `width_mm`; two per net: `segment` `tail` (the finger width, from the contact straight up to the junction) and `fanout` (the design's bundle width, from the junction to the electrode), listed in that order and sharing the junction point; `fanout` `left_channel_non_crossing` (Row), `diagonal_bus` (Row, [diagonal Row bus](#diagonal-row-bus)), `dual_lane_slot_merger` or `single_lane_merger` (Column), or `single_lane_direct` (Column, surface template, and the diagonal Row bus on either template: straight into the contact columns); `fanout_group` 1 or 2 is the lane; `bus_side` `near` or `far` is the side of the Row frame the lane leaves its electrode on |
| pad (contact) | `pin, net, kind, position, anchor, x, y, width_mm, height_mm` | `kind` `connector_pad` or `connector_nc_pad`; `center` anchor |

Contacts: `position` counts 1..P along the contact row (P = connector
positions, `tail.connector_pins`); channel *k* sits at position *k*, except
on the Row board of a [diagonal Row bus](#diagonal-row-bus), whose channels
take the positions of `tail.row_contact_order`.
`pin` runs monotonically along the row: pin = position for `ascending`,
pin = P + 1 - position for `descending`.  Positions N+1..P (N channels)
are unused: `connector_nc_pad` contacts with the net `NC_<pin>` (pin zero
padded to two digits, e.g. `NC_04`), no route and no electrode.

### `layers.top_coverlay_openings`

| `kind` | When | Extent |
| --- | --- | --- |
| `sensor_electrode_opening` | the coverlay bridges between electrode windows are all at least `coverlay.coverlay_min_bridge_mm` | one per electrode, `coverlay.coverlay_expansion_mm` larger on every side |
| `electrode_field_opening` | some bridge would be narrower (it would be removed by JLC) | one merged window over all electrodes plus the expansion |
| `connector_contact_opening` | always | one gang window from the tip edge to the contact ends plus the expansion; laterally it stops at the straight part of the tip edge between the R0.30 tip corners, i.e. 0.05 mm beyond the outer contacts |

Every opening has `kind, net, nets, opening_for, anchor, x, y, width_mm,
height_mm`: `net` is the one net of a single-electrode window, else `null`;
`nets` lists every net the window exposes; `opening_for` is the electrode
kind or `connector_contacts`.  Openings never cross the outline.  The
default design (1.0 mm electrodes at 2.0 mm pitch, bridges of 0.8 mm) gets
one window per electrode; with 1.4 mm electrodes at 2.0 mm pitch (bridges of
0.4 mm, the default until 2026-11-06) it gets one merged field window per board.

On a [masked board](#masked-boards) the merged field window follows the
electrodes: `{kind: "electrode_field_opening", shape: "polygon", net: null,
nets, opening_for, points}`, where `points` is a counter-clockwise ring on
the 1e-6 mm grid (rectilinear and orthogonally convex: every horizontal and
vertical line meets it in one interval), the union of each electrode's
window (the electrode plus `coverlay.coverlay_expansion_mm`) and, between
consecutive electrodes, a filler over their common extent plus the
expansion.  It has no `anchor, x, y, width_mm, height_mm`, so a reader
that knows only rectangles fails instead of exposing the wrong area.
Per-electrode windows stay rectangles, and so does every window of an
unmasked board; `shape` appears on polygon windows only.  The exporter
writes a polygon window as one GTS region over its ring and refuses a
polygon opening of another kind, on an unmasked board, with rectangle
fields, or whose ring is not simple, counter-clockwise, rectilinear and on
the grid ([PHASE2_DIRECT_GERBER.md](PHASE2_DIRECT_GERBER.md#masked-taxel-fields)).

### `layers.bottom_stiffener`

One object per stiffener: `kind: "polygon"`, `zone` (`connector` for the
connector-zone stiffener, exactly one per board), `side` (`bottom`), `layer`
(`bottom_stiffener`), `material` (`polyimide`), `thickness_mm`, `length_mm`
and `points`.  Side, material and thickness come from `profile.stackup`; the
thickness must be a JLC PI option.  The connector zone is flush with the tip
and both tail sides and `tail.stiffener_length_mm` (6.0 mm) long.

### `grid_registration`

| Key | Content |
| --- | --- |
| `coordinate_system` | `active_region_lower_left` |
| `active_region` | `{x, y, width, height}`: the **taxel crossing field**, `(columns-1)*pitch_x + taxel_width` by `(rows-1)*pitch_y + taxel_height` before the board is turned |
| `electrode_field` | `{x, y, width, height}`: the bounds of this board's electrodes; they overhang the taxel field by `routing.electrode_overhang_mm` (0.2 mm) at both ends, along their length only |
| `rows`, `columns`, `pitch_x_mm`, `pitch_y_mm` | the matrix on the layout grid |
| `taxel_mask` | [masked boards](#masked-boards) only, identical on both: `{format: "row_spans/v1", rows, columns, row_spans}`, `row_spans` the design's `matrix.mask` (one `[first, last]` pair of 1-based COL indices per ROW_01..ROW_R, the readout's net indices) |
| `active_outline` | masked boards only: the crossing region P, a counter-clockwise ring on the 1e-6 mm grid in the board's frame (turned with it): each electrode without its overhang, from its first to its last crossing edge, plus between consecutive electrodes a filler over their common extent.  P is rectilinear and orthogonally convex, and lies inside `active_region`, which stays the bounding R x C crossing box |
| `active_taxel_count` | masked boards only: the number of active taxels (crossings), the sum of the row spans |

### `tail`

`length_mm`, `width_mm` (`(P + 1) x pitch`), `side`, `connector_pins` (P),
`connector_channels` (N), `connector_pitch_mm`, `contact_width_mm`,
`contact_length_mm`, `contact_start_from_tip_mm`,
`first_contact_center_from_side_mm`, `tip_corner_radius_mm`,
`stiffener_length_mm`, `bounds` (the tail rectangle), `neck_bounds` (from
above the rounded tip to the body, where the board must not be narrower
than the tail), on the Column board `fanout_lane_count` and
`fanout_lane_channel_counts`, and on the Row board of a
[diagonal Row bus](#diagonal-row-bus) `row_contact_order` (the Row nets at
contact positions 1..N).

### `outline`

`points` is the outer ring and `cutouts` the routed slots (a Column board
with two fan-out lanes has one, with `outline.outline_fillet_radius_mm`
corners).  A board is built tail down: the tail with its
`connector.tail_tip_corner_radius_mm` tip corners; on the Column board the
fan-out envelope, the two outer routes offset outward by half the wider of
their two widths (the finger width), `routing.copper_to_edge_mm` and
`outline.offset_allowance_mm` (round joins)
and joined monotonically to the tail; and the body around the taxel field,
with at least `routing.active_edge_clearance_mm` of board material on every
side (the Row body also holds the routes' left channel).  Where a body side
meets the tail or the envelope below it, the two are flush or at least
`outline.outline_fillet_radius_mm` apart (a narrower step is closed or
widened to one radius), so every concave corner gets a full fillet.

### Route pieces, bundles and bends

Since 2026-10-15 every net is a thin **fan-out piece** and a wide **tail
piece**.  The fan-out piece (`routing.trace_width_mm`, 0.127 mm by default)
leaves the electrode (the Column electrode's bottom end, the Row electrode's
left end), converges into a **bundle** whose straight sections are exactly
q = `trace_width_mm + trace_space_mm` apart (0.254 mm by default), and
expands again to the 0.5 mm contact pitch.  The tail piece
(`routing.finger_trace_width_mm`, 0.254 mm) runs straight at the contact
pitch from the **junction** down into its contact.  All junctions of a board
lie at one level, below every bend, so the width changes only where the
routes run straight at the contact pitch; there the wide pieces keep the
finger-section spacing (contact pitch less finger width, 0.246 mm) to every
neighbour, also to a neighbour whose diagonal leaves the contact column at
the lowest bend (the junction lies `(R - pitch cos A) / sin A` below that
bend, R being half the finger width + half the bundle width + 0.246 mm).
The whole-board DRC holds every route pair with a tail piece to that
spacing (the `finger_section` of `route_route_clearance`).
The tail is the straight part from the tip to the junction: the wide traces
cross the stiffener edge, where the tail flexes.

Converging and expanding routes make **bus-style bends**.  The routes that
move the same way form a run whose diagonals are parallel, at the bus angle A
from the vertical, and q apart.  A lies just below the taper cap
`fanout.maximum_taper_angle_deg` (60 degrees; 59.998891 degrees for the
default 0.254 mm pitch), because the stagger is rounded down to the grid and
the diagonals are built two grid steps (2e-6 mm) farther apart than q, which
absorbs the rounding of their end points.  On the
bundle side of a run neighbouring bends are staggered by q tan(A / 2) (the
recorded `bend_stagger_mm`, on the grid), rising toward the side the run
moves to, as in a mitred bend of a bus; on the other side each route bends
where its diagonal meets its own electrode or contact column, rounded to the
grid away from the bundle, so that no diagonal, however short, leans further
from the vertical than A.  Routes that
move apart or not at all need no stagger.  Every centreline keeps at least q
to its neighbours in the vertical runs, along the diagonals and around each
bend, which the whole-board DRC measures exactly.

### Column fan-out

Up to `fanout.maximum_channels_per_lane` columns share one lane: one bundle
centred under the field (a middle route of an odd count runs straight),
with a straight stretch of one pitch between the converging and the
expanding bends.  The routes left of the centre move right and those right of
it move left into the bundle, and the bundle expands into the centred
contacts.  More columns use two lanes of up to that many routes each, two
bundles at q on either side of a routed slot with
`fanout.lane_to_slot_clearance_mm` to it; each lane converges from its
electrodes (it may hold routes moving either way) and expands into its half
of the contact row.  The slot is as wide as the body allows, up to
`fanout.slot_width_mm`, and never narrower than
`fanout.minimum_slot_width_mm`.  On a narrow field with a wide bundle (17
columns at 0.6 mm pitch with 0.254 mm traces at 0.246 mm spacing, say) the
two bundles and the minimum slot need more width than the body has: they
then spread wider than the body, and the outline follows them with a
filleted shoulder below it or, where they reach less than
`outline.outline_fillet_radius_mm` beyond the body, with the body side
moved out flush with them (the board is then that much wider beside the
taxel field too), while the body keeps its
`routing.active_edge_clearance_mm` around the taxel field.  Each side
follows the step rule on its own: with an odd column count the first lane
(from COL_01) carries one route more, so that side spreads one bundle pitch
further, and close to those limits the board width changes by up to one
fillet radius (0.5 mm) for a small change of pitch.  Such a design is
not rejected (until 2026-10-15 it was, with `E_DUAL_LANE_WIDTH`); the board
outline is simply wider than the sensor below the taxel field.  With the
default 0.254 mm bundle pitch both bundles fit every legal field (with an
odd column count the narrower bundle can leave a step of less than one
fillet radius to the body side, which then moves out to stand one radius
beyond the bundle's envelope, D5).

On the surface template (`fanout.column_convergence` `direct`, one lane of
up to 64 routes), and on either template for a design built as the
[diagonal Row bus](#diagonal-row-bus) (`diagonal-bus/11`, built with the
surface profile; the generic template's straight Row channel keeps the
lanes above), the routes converge from the electrodes straight into
their contact columns: there is no bundle and so no expansion
(`merger_taper_angle_deg` and `merger_height_mm` are 0), the routes'
`fanout` is `single_lane_direct`, and the contact columns keep the 0.5 mm
contact pitch the routes arrive at.  Nor is there a straight stretch
between the convergence and the contacts: the tail starts the widening drop
below the lowest bend.  The convergence takes the bus angle of the lowest
transition among whole-degree caps of 60-85 degrees, measured down to that
tail root (`fanout.bus_angle` `shortest`, `entry_taper_angle_deg`; the
widening drop grows with the angle): 4.2 mm below the field for 16 x 32
taxels at 2 mm with 0.2032 mm bundles instead of 22.2 mm with two lanes at
60 degrees.

### Row channel

The Row routes run up a left channel of one lane per row at the bundle
pitch q: lane 1 (logical row 1, the uppermost) is outermost, right above
contact position 1 at `connector.contact_center_to_side_edge_mm` from the
left edge, so it needs no lateral move.  Each route is an L: a horizontal
stub from its row electrode's left end into its lane, then down.  The
channel is `(rows - 1) q + 2 x 0.5 mm` wide (`channel_width_mm`), and the
taxel field starts `routing.active_edge_clearance_mm` to its right.  Below
the active field (by the same margin) the lanes expand with bus-style bends
to the contact positions; this expansion lies inside the body, which grows
by its height, and its lowest bend lies the widening drop above the tail
root (y = 0 of the build frame), where the traces widen.  The body is at
least as wide as the contact row the channel expands to, `(rows + 1) x
0.5 mm`, even where the taxel field is narrower.  The tail stays flush with
the left body side and its straight full-width part beyond the stiffener is
unchanged.

As the bus angle is the cap for every bundle pitch, the stagger grows with q
while the lateral move per lane, 0.5 mm - q, shrinks: the expansion is lowest
near a 0.25 mm pitch and grows on either side.  For 64 rows it is 9.234087 mm
high at the default 0.254 mm pitch, 14.376017 mm at 0.4 mm and 17.894312 mm
at 0.4999 mm, and 0 at 0.5 mm, where no lane moves (the Column merger, with
at most 16 routes per lane, behaves the same way).  A wide spacing can thus
make a board taller and decide whether it fits the board-size limit; the
`E_BOARD_SIZE` advice names the tail, pitch, row and column fields only.

On the surface template (`routing.row_channel` `tight`) lane 1 sits
`ceil(copper_to_edge + trace width / 2 + offset allowance)` from the left
edge (0.3518 mm at 0.1016 mm traces) instead of above contact position 1,
the field starts so that the innermost lane keeps the coverlay
opening-to-trace rule (plus one grid step) from the merged field window
(`channel_width_mm` is then the field's distance from the edge less the
0.5 mm margin), and the field starts that same gap above the highest
expansion bend instead of one margin.  The expansion takes the bus angle of
its lowest transition among whole-degree caps of 60-85 degrees, measured
down to the tail root, where the traces widen (`fanout.bus_angle`
`shortest`, recorded as `merger_taper_angle_deg`).  Lanes that would sit
right above their contacts anyway, with one row or a bundle pitch equal to
the 0.5 mm contact pitch, are put there: they need no expansion, run
straight down into the contacts, and the field starts one margin above the
tail root.  The expansion height still grows with the bundle pitch as above
(lane 1 moves too), but the field starts lower than on the generic
template.  For 64 rows the field starts 8.933576 mm above the tail root
with 0.2032 mm bundles, 9.845781 mm with 0.254 mm, 15.213878 mm with
0.4 mm, 18.890117 mm with 0.4999 mm and 0.5 mm with 0.5 mm bundles
(generic: 11.74674, 10.199434, 15.383515, 18.932987 and 0.75 mm).

A design whose `routing.row_sides` is `left`, `right` or `both` (the
generic template's default since P5-diagonal-bus.md section 18) has no Row
channel: its rows run on the [diagonal Row bus](#diagonal-row-bus).  The
Row channel above is that of `routing.row_sides` `channel` (and of the
surface template's designs without the key).

### `construction`

Not rules, but the values the geometry was built with:
`minimum_concave_fillet_radius_mm` (both boards; `null` when the outline has
no concave corner), `fanout_bundle_pitch_mm` (q, both boards; it replaced
the deck pitch), `bend_stagger_mm` (both), `merger_taper_angle_deg` and
`merger_height_mm` (the expansion from the bundle to the contacts: the bus
angle in degrees, 0 when no route moves, and the height from its highest to
its lowest bend; both boards), on the Row board `channel_width_mm`, and on
the Column board `entry_taper_angle_deg`, `entry_transition_height_mm` (the
convergence from the electrodes into the bundle) and `slot_bounds` (`null`
with one lane).  On the generic profile (the generic template's straight
Row channel) every transition runs at the one bus angle and
`bend_stagger_mm` is its stagger.  With `fanout.bus_angle`
`shortest` each transition takes its own angle, and `bend_stagger_mm` is
the stagger of the lowest transition with bends (the Column merger, or the
convergence where no route expands).  On the surface template each board
has one such transition: the Row expansion, and the Column convergence (its
merger angle and height are 0).  A [masked board](#masked-boards) adds
`mask_class`, `{"row": "straight", "column": "straight"}` (the same on both
boards), and its Row `channel_width_mm` is that of its tapered field.  A
[diagonal Row bus](#diagonal-row-bus) has `mask_class` `{"row":
"diagonal", "column": "straight"}` on both boards; its Row board keeps
`minimum_concave_fillet_radius_mm` and `fanout_bundle_pitch_mm` only and
adds `row_bus` (the record below), without `channel_width_mm`,
`bend_stagger_mm`, `merger_taper_angle_deg` or `merger_height_mm`; its
Column board has the straight one's of the same design without
`routing.row_sides` (its tail centred under its body), but for `mask_class`,
`minimum_concave_fillet_radius_mm` (of its outline, shared with the Row
board down to the tails' roots) and `shared_outline_below_field_mm` (the
level down to which the two boards share one outline, as the Row board's
`row_bus.shared_outline_below_field_mm`); its tail root lies on that level.

### Masked boards

A surface design with a field mask (`matrix.mask`, see
[API.md](API.md#field-mask-matrixmask)) keeps every net, lane, contact and
pin of the unmasked R x C design; each electrode spans only its taxels.
Its spans are counted in each board's canonical frame (copper side up, tail
down): on the Row board as x-slots from the Row channel (`row_frame_spans`:
COL_c is slot `C - c` when both tails leave on one side, `c - 1` when they
are opposite), on the Column board as row slots from its tail
(`column_frame_spans`: ROW_r is slot `R - r` or `r - 1`).  The engine
builds the straight constructions (`construction.mask_class`):

- **Row board, straight channel.**  The plan is the bounding R x C plan
  (lanes, expansion, tail and height unchanged).  The field slides toward
  the channel as far as the lane taper lets: beside row k only lanes 1..k
  run, so its channel-side crossing edge may start at `W_k = lane_k +
  window gap + overhang` (`row_taper`), and the field starts at `active_x =
  max(margin, max_k (W_k - lo_k x pitch_x))`, the unmasked start when every
  row reaches the channel side.  Electrode k spans `[active_x + lo_k x
  pitch_x - 0.2, active_x + hi_k x pitch_x + taxel_width + 0.2]`, and its
  stub runs from its lane to that left end.  The outline keeps today's left
  side and tail; its far side is F, the crossing region P dilated by
  `routing.active_edge_clearance_mm` (as y-slabs, square corners), and the
  part below the field, which holds the expansion, is today's body width
  taken from the bottom row's far crossing edge (at least the contact row,
  with a step of zero or one fillet radius to the tail); the body keeps that
  width as high as the field reaches as far as its bottom row.
- **Column board, straight fan-out.**  The plan is the bounding plan.
  Electrode c spans `[active_y + b_c x pitch_y - 0.2, active_y + t_c x
  pitch_y + taxel_height + 0.2]`; a raised column (`b_c > 0`) runs its
  stub straight up its own centre line from today's entry bend to its
  electrode, past the rows between its taxels and the tail on their
  Row-channel side.  The outline keeps today's tail and fan-out sides and
  the body down to its bottom (y = 0, where every stub enters its bends);
  its top is F's top as x-slabs, extended to the body sides where they
  moved out for the fillets.
- Concave corners of the staircase outlines get the rolling-circle fillets.
  Where the outline has a vertex of the unmasked outline it keeps its exact
  value, so a mask whose spans are all full gives the unmasked board byte for
  byte, and a mask whose rows all reach the Row channel and whose row next
  to the Column tail is full keeps the unmasked routes, contacts, gang
  window, stiffener and tail.
- The merged field window is the polygon above;
  `grid_registration` adds `taxel_mask`, `active_outline` and
  `active_taxel_count`, `metrics` adds `active_taxel_count`, and the SVG
  preview adds `data-active-outline` ([API.md](API.md#svg-previews)).
  `field_footprint` measures the masked boards and adds each board's
  outline above its tail root before the fillets (`mask`); the fillets add
  board material only outside that ring, within the 0.5 mm fillet radius
  of its concave corners and of its corners on the tail root (where the
  body meets a wider tail or the Column fan-out).
- `active_region` and `electrode_field` keep their meaning: the bounding
  crossing box (identical on both boards) and the electrodes' bounds.
- The DRC keeps the 30 records; five of them measure the masked field
  ([records of masked boards](#records-of-masked-boards)), and the
  registration of a masked pair checks the crossings of the stacked boards
  against the mask ([registration record](#registration-record)).
- The exports of a masked build
  ([PHASE2_DIRECT_GERBER.md](PHASE2_DIRECT_GERBER.md#masked-taxel-fields))
  write the polygon window as a GTS region and add `taxels.csv` to the
  review bundle: every R x C position (`row`, `column`, `row_net`,
  `column_net`, `row_pin`, `column_pin`, `active`), read back against both
  boards' `taxel_mask`, electrodes, contacts and `active_taxel_count`.  The
  netlist keeps one far-end land per electrode, on its trimmed copper.

### Diagonal Row bus

A design whose `routing.row_sides` is `left`, `right` or `both` (see
[API.md](API.md#diagonal-row-bus-routingrow_sides)), on either template, is
built as the construction `diagonal-bus/11` (`engine/diagonal.py`) instead of
the straight Row channel (`channel`), masked or not; every valid mask
builds (claude/specs/masked-field/P5-diagonal-bus.md, sections 2, 12-20, 24, 27 and 27.8).
It is the rectangular mode's default: the generic template defaults
`routing.row_sides` to `both` (section 18).  Both templates build it with
one rule set, the surface profile's (`engine.core.rules_template`, section
20; see the last items), so a design builds the same boards on either.
Outside the taxel field the two boards may overlap freely (two separate FPCs
on either side of the film), their tails too: the tails are stacked, both
centred on the field, the Row tail lying on the Column tail, and they part
to their own connectors.  Down to the tails' roots the two boards have one outline in
the stack, so the films align by their edges.  Only the field, the tails'
exit side and each board's own rules constrain them.

- **Sides.**  `routing.row_sides` is seen from outside the stack with the
  tails down.  The *near* side of the Row board's canonical frame is the
  side of ROW_01's lane (the stack's right with the rows on top, its left
  with the columns on top), the *far* side the other.  `both` puts ROW_01,
  03, 05, ... on the near side and ROW_02, 04, ... on the far side (the
  alternate split); `left` or `right` puts every row on that side, built in
  the mirrored frame when it is the far one.
- **Bands.**  Each side is an onion of lanes that hug the field's boundary
  at the bundle pitch q around a keep-out K: every Row window and every
  stacked Column window grown by the window clearance.  The stacked Column
  copper is not in K (the boards may overlap outside the field): a lane may
  cross a raised Column stub beside the field, at any angle, reported like
  every crossing outside the field.  A row trace leaves the end of its
  electrode on a slant where the field lets it: the first segment of a 32 x
  12 rectangle's lanes runs at 16.7 degrees from the vertical at 2 mm with
  1.4 mm electrodes (toward its own zone's outer-bottom corner).  Where the
  keep-out of the rows below reaches the row's own height, the lane leaves
  nearly flat (at fine pitch a row above a much wider one goes around that
  row's keep-out).  `flat_lane_rows` lists the rows whose lane has a
  segment more than 85 degrees from the vertical.
- **Receding fields.**  Where the field narrows toward its bottom edge
  beside a lane (a disk below its equator), the lane follows it inward: its
  chain runs around everything it must avoid on its own board (the
  windows, the other rows' electrodes, the lanes inside it), the convex
  hull of them, down to the field's bottom edge, as far in as the keep-out
  at that edge and the lanes inside it allow and no flatter than the 85
  degree taper cap, and turns straight down there into its fan.  The lanes
  nest at the bundle pitch around the turn inward (each one exactly q
  farther out at the inner lane's westmost corner, not spreading).  On a
  disk of 24 x 24 at 2 mm the Row traces beside the field keep within 3.4
  mm of an electrode with both (11.1 mm when they ran straight down from
  the widest rows) and its Row root lies 2.7 mm below the field (6.8 mm).
  The outline over the field is still the union with the Column board's
  own body, whose traces drop straight down beside the receding rows: the
  disk's stack keeps its widest width down to the field's bottom edge.
- **The edge.**  The onion is `diagonal-bus/1`'s, whose inner lanes turn
  straight down up to 0.3 mm below the field (the bottom row's zone
  reaches that far): here every lane whose band crosses the field's bottom
  edge turns down on it instead, where it crosses (or just outside the
  stacked Column windows' keep-out, for thin rows), moving its ray inward
  by up to about 0.2 mm.  Beside a field that does not recede the bands,
  and everywhere the tip, are `diagonal-bus/1`'s to the nanometre, and no
  lane bends below the field before its fan.
- **Fans.**  Below the field every Row trace bends at most twice: off its
  band into a fan, and into its contact (a lane straight above its contact
  runs on down without a bend); the tail then runs straight down.  The
  lanes of a side that move the same way toward their contacts form a run:
  a bus of parallel lines at one cap of 60-85 degrees from the vertical
  (the surface profile's whole-degree caps; the one that roots the tail
  highest, never within 5 degrees of the Column fan-out's entry angle, so
  no fan runs along the Column fan-out's diagonals: it crosses them at 5
  degrees or more), its front lane turning
  first just below every window and each lane behind it one bundle pitch
  lower.  The Row contact columns may lie on the Column board's (both
  tails at the 0.5 mm contact pitch, stacked), from the tails up to the
  traces' last bends; like every overlap outside the field they are
  reported (`trace_overlap_mm`), not avoided.
- **Tails** (`diagonal-bus/10`, the user's request of P5-diagonal-bus.md
  section 27: the tails within the sensor's width).  The Row tail is
  centred on the field's width in every side mode, as the Column tail: it
  lies within the field wherever it is narrower, and is centred on it
  where it is wider.  The rows take the tail's positions 1..R from its
  canonical left, so with `both` (and two rows or more, a contact per row)
  the two sides' runs meet in a V (the funnel) whose near and far contacts
  part on the field's centre line (half a contact pitch off for an odd
  row count), and with one side the whole bundle fans inward under the
  field (half a funnel); built mirrored, the rows take the contacts at the
  tail's far end from the band (turned back, positions 1..R), a reader
  tail's unused contacts on the band's side.  Its own root lies just below
  the fans' junctions.  Until `diagonal-bus/9` the Row tail lay under the
  band with one side (the outermost contact used straight below ROW_01's
  lane) and, with `both`, parted midway between the two innermost lanes,
  which put the tails beyond the field on one-sided and asymmetric fields.
  The Column board has
  the copper of the straight Column board of the same design without
  `routing.row_sides` (the [masked](#masked-boards) builder on its mask, the
  full spans of an unmasked rectangle): its tail centred under its fan-out,
  no shift, no neck, no stub drop, in every side mode, its V capped (the
  Column V, below) and its tail root moved down to the shared body's bottom
  edge (its contact columns running on straight down to it, the tail as
  long below it); its outline is that board's but down to the tails' roots
  (below).  The tails are stacked: both
  leave through the same exit side, both centred on the field, so the
  narrower lies wholly on the wider, the top board's tail over the bottom
  board's; each part to its own connector.  Above the tail roots the boards overlap too: the Row
  fans cross the Column fan-out at any angle.
- **Contacts.**  The lanes' order is the contacts' order: with `both`
  ROW_01, 03, 05, ..., 06, 04, 02 (the near band from outside in, then the
  far band from inside out), with one side ROW_01..ROW_R from position 1,
  or ROW_R..ROW_01 when built mirrored (`tail.row_contact_order`).
  `channel_order` still numbers the pins along the contact row, so pin *k*
  carries ROW_k only where the order puts it; `pinout.csv`, `netlist.ipc`
  and `taxels.csv` take each row's pin from the pads
  ([PHASE2_DIRECT_GERBER.md](PHASE2_DIRECT_GERBER.md#diagonal-row-bus)).
- **Outline.**  The Row outline is y-monotone: on each side the exact
  envelope of F (the crossing region dilated by the 0.5 mm margin, as
  y-slabs) and the outermost lane's outer envelope, never narrowing from the
  tip down to the widest level and from the tail up to it (the funnel's V);
  with one side the inner flank follows the field down to its bottom and
  steps once straight down into a tail narrower than F's bottom.  A tail
  side beyond the envelope above it (beside the outer lanes, or a centred
  tail wider than F's bottom under one side's inner flank) slants out to
  it from F's bottom at the highest, or, where that would lie flatter than
  45 degrees (a tail far wider than the field), steps out once (on the
  inner flank at F's bottom).  On the soft finger 59 x 12 one-sided the
  30 mm Row tail reaches 2.8 mm beyond each side of F, and the inner flank
  slants out to it from F's bottom corner instead of a 2.8 mm ledge along
  F's bottom.  Both tail sides hold straight above the tail root, and the
  concave corners get the R0.5 fillets.
- **One outline down to the tail roots** (`diagonal-bus/8`,
  P5-diagonal-bus.md section 20).  Both tails leave one bottom edge, the
  shared level: the deeper of the two boards' own tail roots (the Row
  funnel's, just below its last bends, or the Column V's), lowered where
  the union's fillets into the tails reach below it, until the union runs
  straight down the tails' sides there (`_build`, at most three passes).
  The shallower board's tail root moves down to the level, its contact
  columns running on straight; each tail keeps its width, position and
  length below it (CAD mode's `tail_extension_mm` is measured from it).
  From the tip down to the level both boards have one outline in the
  stack, seen from outside (the top board turned over): the union of the
  two boards' own outlines before their fillets (each as above, made
  regular), filled across at every height, made regular again, given
  straight sides and filleted once (a vertex turning by under 4
  micro-radians, where a fillet would not leave the vertex's grid step,
  keeps its vertex): the field, the Row bands and funnel and the Column
  fan-out, each board gaining blank film where only the other has copper.
  Below the level each board is its own tail: a board narrower there steps
  in along the level, its concave corner's R0.5 fillet below it; under the
  other board's fillet into a tail wider than its body it runs straight
  down 0.5 mm first and steps in there.  Where a tail is flush with the
  union's side (a tail as wide as the union at the level: the funnel
  narrowing into a reader tail, a Column tail wider than the Row tail, a
  centred tail wider than the field; before `diagonal-bus/10` also one
  side's Row tail under the band), the side meets the
  tail's edge on the level straight or at a filleted corner, never a step
  a few micrometres wide: the union's points on the level stay while it is
  made regular (a flat run above merges into the tail's edge), it runs on
  below the level along that tail's side, and a tail's root corner its
  side meets at a slant (a side made regular into the tail through that
  corner) stays a corner of the union, filleted on both boards with the
  level lowered below that fillet.  More than 1.0 mm below the level
  each outline is its own tail exactly; the copper of both boards is the
  same as with its own outline at that level.  Both boards record the
  level (`construction.row_bus.shared_outline_below_field_mm` and the
  Column board's `construction.shared_outline_below_field_mm`: 5.866 mm on
  the default 12 x 32), and the registration checks that the outlines
  coincide down to it.  `diagonal-bus/4` to `/7` shared the outline over
  the field only, down to F's bottom, each board keeping its own funnel or
  fan-out below.
- **Regular outlines.**  No vertex of either outline turns by less than
  5 degrees (`REGULAR_TURN_DEG` of `engine/diagonal.py`) but on a fillet or
  the tail.  Between two corners (a turn of 5 degrees or more, a fillet's
  vertex, the tail from its root down) a run of flatter turns is one
  straight edge on or outside every vertex of the run: the outer hull edge
  over the middle of its chord (the least added area), joined to the edges
  beside it where their lines meet; a long smooth curve (flat turns adding
  up to more than 5 degrees) becomes a polygon whose corners turn by
  5 degrees or more, each edge covering a few degrees of it.  Each board's
  own outline is made regular before its fillets (its tail, from the
  deeper own root down, as built), and the union down to the tails' roots
  again (the crossings of nearly parallel sides, the vertices one board's
  heights add on the other's side; its points on the level and below it,
  and the tails' root corners a side meets at a slant, stay) before its
  concave corners get the R0.5 fillets; the union's sides run on below
  the level along a flush tail's side, else along their last edge, so a
  straight side meets the level without a corner.  No vertex on or below
  the level turns by under 5 degrees but on a fillet or a tail's tip
  corners.  The copper is not touched: every clearance to the outline
  only grows.  The outline built without this lies inside
  the regular one (within a fillet's step, a few micrometres, where a
  fillet is the same circle stepped at other angles); on the named fields
  with `both` the tip stays within 1 micrometre (the equilateral's 0.57 mm
  wider: its slanted side one straight edge from below the tip down to F's
  bottom) and the board widens by up to 0.41 mm at F's bottom, where a
  band's long side met the short drop to the funnel at 2.9-3.6 degrees.
- **Chamfered notches** (`diagonal-bus/6`, P5-diagonal-bus.md section
  16).  Where a masked field misses cells at a corner (a rounded face's
  notch), both boards cross the notch on F's convex hull, not on F's
  staircase: on each side, between two consecutive corners of the hull,
  the staircase becomes the hull's edge when none of its corners lies
  deeper inside that edge than a step of two cells across one row does
  (`CHAMFER_STEP_CELLS` of `engine/diagonal.py`: 2 p / sqrt 5, 1.79 mm at
  2 mm; a one-cell notch is a 45-degree chamfer, a notch of several steps a
  polygon following F).  A deeper pocket (a narrow tip row over a much
  wider one) keeps its staircase, so such a tip does not widen.  The
  chamfer's ends are F's corners: it lies on or outside F, every copper,
  coverlay and window clearance to the outline only grows, and the shared
  outline over the field carries it on both boards (a vertex convex on one
  board's own outline that turns concave in the union, the Column board's
  side stepping out beyond the chamfer, gets its R0.5 fillet).  The tip
  widens where a notch is chamfered at the tip: the disk with `both`
  14.81 -> 17.21 mm, the equilateral 3.12 -> 4.32 mm; the crank and every
  full field are unchanged (a full field keeps `diagonal-bus/5`'s outline
  byte for byte, only its build id changes).
- **Straight sides** (`diagonal-bus/7`, P5-diagonal-bus.md section 17).
  On each side of the outline over the field, the stretch from the tip
  corner down to the side's widest point is one straight line wherever one
  line encloses it lying no more than 1.0 mm (`SIDE_STRAIGHTEN_MM` of
  `engine/diagonal.py`) outside it anywhere, measured to the side as the
  boards have it, its concave corners filleted (a staircase of the Column
  board's column ends beyond the Row field's chamfer, on a masked 25 x 32
  field at 0.7 mm, lies 1.106 mm inside the line at its sharp inner
  corners and 0.898 mm as filleted: one line): the line through the widest
  point tangent to the stretch (every old vertex on or inside it, the
  least added), the tip corner moving out along the top edge to meet it
  (at most 1.0 mm), so a short vertical stub, a concave fillet and a jog
  below the tip corner become one edge from the tip corner down to the
  widest point.  The stretch from the widest point down to the shared
  level (F's bottom before `diagonal-bus/8`) is the chord likewise, where
  it lies within the bound and heads in no flatter than 45 degrees.  A line
  is taken only where it meets each board's own side below the level
  straight on or at a convex corner of 5 degrees or more, and leaves the
  widest point a corner of 5 degrees or more; a curved side (the disk, a
  long receding side, a step out to the other board's body) keeps its
  polyline.  The widest point stays (no board is wider), the old outline
  lies inside the new one (every clearance only grows), and the copper and
  both outlines more than 1.0 mm below the level are unchanged.  On the named fields with `both` the rectangle's
  and the soft finger's tips widen by 0.435 mm (the tip corners 0.14 and
  0.24 mm out), the crank's by 0.234 mm (its long side keeps its
  polyline); the equilateral and the disk are unchanged.
- **Convex sides** (`diagonal-bus/9`, P5-diagonal-bus.md section 24).
  Then, on each side, the stretch from the tip corner down to the widest
  point is its convex hull (the hull of its vertices): each dent between
  two consecutive corners of the hull (the S-shaped kink where the lanes
  start beside a narrow tip, a short step) becomes the hull's edge where no
  point of it lies deeper inside that edge than a step of
  `CHAMFER_STEP_CELLS` cells (2 p / sqrt 5, 1.79 mm at 2 mm), measured to
  the side as the boards have it (filleted), no anchor of the union lies in
  it, and the tip corner and the widest point stay corners of 5 degrees or
  more; a deeper pocket keeps its outline.  The hull's corners flatter than
  5 degrees merge as in the regular outlines (the widest point held: the
  tip corner may move out along the top edge, 0.81 mm on the user's crank
  32 x 32).  A slanted side down a staircase is one straight line from the
  tip corner to its convex bend into the funnel; that bend lies on the hull
  and stays.  The old outline lies inside the new one, the widest point and
  the copper are unchanged.  On the named fields the crank's tip widens by
  1.70 mm with `both` (2.22 mm with `left`), the disk's by 1.8-4.1 mm, the
  equilateral's by 0.06-0.99 mm; the rectangle and the soft finger are
  unchanged in every side mode, and so is the rectangular generator's named
  corpus.
- **Convex flank** (`diagonal-bus/11`, P5-diagonal-bus.md section 27.8).
  With one side, the side without lanes is convex from the field's outline
  corner (its outermost point on F's bottom) down to the tail: before the
  convex sides, its stretch from that corner down to the last convex
  corner before the junction into the tail becomes its convex hull, so the
  Column board's body corner, its ledge in to its outermost route and that
  route's turn into the V (a notch 0.19-0.53 mm deep just below the field
  on the video's sensors, which the lanes cover on the bus side and with
  both) are bridged, wherever no anchor of the union lies in a dent and
  every corner of the side stays 5 degrees or more (a bridge meeting an
  edge flatter moves along that edge's line to meet it at 6 degrees), and,
  as filleted, the side's straight run down a tail's edge and the old
  flank stay (on or inside the new one; the guard compares the lower of
  the two sides' runs, so on 31 seeded and generic builds a tail's
  straight edge starts up to 0.124 mm lower: P5-diagonal-bus.md section
  27.9).  No depth bounds it.  The tails' roots, the copper and the widest
  point are unchanged; with both nothing changes.  On the named fields
  one-sided the areas grow by 0.23-0.24 mm2 (the soft finger's by 1.06:
  its slant out to the wider tail now from F's corner).
- **One rule set** (`diagonal-bus/8`, P5-diagonal-bus.md section 20).  The
  rectangular mode is a subset of CAD mode: a bus design on the generic
  template is built with the surface profile (`engine.core.rules_template`,
  the surface template for every bus design; `result.profile` is it), by
  the one construction, so it builds byte for byte the boards the same
  design builds on the surface template, only its identity differing (the
  build id, its hashes and the manifest's `template`).  Its rules are CAD
  mode's: the 0.5 mm active-edge margin, one Column lane of up to 64
  channels, the 60-85 degree caps, tails of at least 7.5 mm (the generic
  default bottom tail 12 mm, the top tail's length, since P5-diagonal-bus.md
  section 27.7; 7.5 mm before).  The straight Row channel (`channel`) keeps
  the standard profile byte for byte (its 0.75 mm margin, 32 columns, two
  Column lanes round a slot, 7.0 mm tails and default).  Section 18's own
  rules for the bus on the standard profile (its fan caps, its fans' start
  at F's bottom, a careful second pass of the shared outline) and section
  19's Column V override are gone.  The default 12 x 32 design: both
  boards 67.920 mm wide and 41.766 mm long (the Column board 37.266 mm with
  the 7.5 mm bottom tail of before section 27.7; `diagonal-bus/7` on the
  standard profile: 67.941 x 41.143 mm
  and 67.890 x 52.989 mm, the Column board in two lanes round a slot), the
  tip 64.901 mm, the field's own width with the 0.5 mm margin.
- **The Column V** (`diagonal-bus/8`, P5-diagonal-bus.md section 20).  The
  Column board converges in one V straight into its contact columns (each
  trace bending at most twice below the field): no bundle, no second lane,
  no stress-relief slot.  The rule (section 20.1): the construction plans
  the Column board twice, its V at the profile's whole-degree caps up to
  80 degrees from the vertical (`COLUMN_V_CAP_DEG`, `column_profile`) and
  at the profile's own caps (60-85 degrees), arranges the Row fans for
  each (5 degrees or more off that V's entry angle), and takes the one
  whose tails root higher: the deeper of the two boards' own roots (the
  Row funnel's, just below its fans' junctions, and the Column V's),
  compared before the level is lowered below the union's fillets; a tie
  (within a nanometre) takes the capped V, and a plan whose lanes cannot
  be arranged is passed over.  The capped V leaves the fans 85 degrees:
  on the default 12 x 32 design with `both` the V runs at 80 degrees and
  both tails root 5.866 mm below the field, against 9.494 mm with the V at
  82 degrees and the fans at 76; one-sided, since the Row tail is centred
  (`diagonal-bus/10`), the whole bundle fans inward under the field and
  takes 85 degrees as well, the tails 6.282 mm below the field against
  11.040 mm (under the band the single fan gained nothing from the cap and
  the profile's V at 82 degrees rooted the tails higher, 5.214 mm against
  5.866 mm).  Measured with `diagonal-bus/8` on 433 builds (the
  generic named designs and the CAD cases in every side mode, the design
  workflow judge's 400): the two Vs differ on 258, and the rule takes the
  capped one on 126 (85 of the 124 with `both`, 41 of the 134 one-sided);
  the V runs at the cap on 140.  A V always capped would root the tails
  deeper than a V never capped on 132 builds (by 0.73 mm in the median, up
  to 4.27 mm) and higher on 84; the rule roots them deeper than a V never
  capped on 9 (0.04 mm in the median, up to 0.27 mm) and higher on 76
  (1.01 mm, up to 5.13 mm), deeper than a V always capped on 8 (at most
  0.07 mm) and higher on 123 (0.81 mm, up to 4.27 mm).  Its tails root up
  to 0.27 mm deeper than the better of the two Vs on 17 builds (the choice
  compares the roots before the level is lowered below the fillets).
- **Records.**  Both boards carry the masked records
  (`grid_registration.taxel_mask`, with full spans for an unmasked
  rectangle, `active_outline` and `active_taxel_count`), the polygon field
  window and `construction.mask_class` `{"row": "diagonal", "column":
  "straight"}`; the Row routes have `fanout` `diagonal_bus` and `bus_side`.

The Row board's `construction.row_bus`:

| Key | Content |
| --- | --- |
| `kind` | `diagonal-bus/11` |
| `sides` | the design's `routing.row_sides` |
| `near_side` | `left` or `right`, seen from outside the stack with the tails down: ROW_01's side (with one side, that side) |
| `split` | `alternate` with `both`, else `null` |
| `near_rows`, `far_rows` | the row indices on each side (`far_rows` empty with one side) |
| `contact_order` | the nets at contact positions 1..N, as `tail.row_contact_order` |
| `tail_position` | `centred`: the Row tail centred on the field in every side mode (`diagonal-bus/10`; `under_body` with both and `under_band` one-sided before) |
| `tails` | `stacked`: both tails leave on one side, both centred on the field, the Row tail on the Column tail; the Column tail centred under its fan-out |
| `shared_outline_below_field_mm` | how far below the taxel field (the active region's edge toward the tails) both boards have one outline in the stack, from the tip down: the tails' roots, where both tails leave the shared body's bottom edge (5.866 mm on the default 12 x 32; F's bottom, 0.5 mm, before `diagonal-bus/8`); the Column board records the same in `construction.shared_outline_below_field_mm` |
| `fans` | per run of lanes moving the same way: `{rows, move, angle_deg, height_mm}`, the rows front first, `west` or `east` in the Row frame (the near side west), the cap in degrees from the vertical and the run's height from its highest bend to its lowest |
| `tip_width_mm` | the board's width at ROW_01's centre |
| `tip_excess_mm` | that width less F's width there |
| `band_mm` | `{near, far}`: the largest overhang of the board beyond F on each side, at the rows' centres |
| `lane_angle_deg` | `{near, far}`: the least and the largest slope from the vertical of each lane's longest band segment (from its electrode's end to where it turns straight down), `[min, max]` in degrees (`null` for a side without lanes) |
| `flat_lane_rows` | the rows (indices, ascending) whose band has a segment more than `fanout.maximum_taper_angle_deg` (85 degrees) from the vertical: a lane around a much wider row below it; `[]` when every lane stays within the cap |
| `widest_mm` | the outline's width across the tail axis |
| `tip_is_narrowest_relative` | no row whose part of F is at least as wide as ROW_01's has a narrower board than the tip (at the rows' centres): the tip is the board's thinnest part wherever the field is not narrower than there |

The widths, excesses and bands are measured on the published outline.  The
tip's excess need not be the least of every row's: where F widens just
below the tip on a lane's side, ROW_01's lane goes around the wider row and
the tip carries that much more (the disk with `right`, rows on top: the
tip's excess is 2.408 mm, the second row's 1.726 mm).
`tip_is_narrowest_relative` is true on every build of the plan's named
corpus and false on under 1 % of seeded random designs, where such a
widening is followed by a row of F narrower than it but still wider than
the tip's.

For 32 x 12 taxels at 2 mm with 1.4 mm electrodes and 0.1016 mm traces at
0.1016 mm spacing, rows on top, `both` makes the tip 24.902 mm wide (31.052
mm with the straight channel); the Row funnel's last bends lie 3.950 mm
below the field and both tails root 4.730 mm below it, on the shared body's
bottom edge, the Column tail centred and stacked under the Row tail.  One
side, the fans' last bends lie 7.206 mm and the tails root 7.986 mm below
the field.  (With the Row tail under the band, `diagonal-bus/9`, one side
rooted them 4.557 and 4.798 mm below the field: centring the tail costs the
one-sided rectangle 2.65 mm of depth at the fans' last bends (4.557 -> 7.206
mm) and 3.19 mm at the roots (4.798 -> 7.986 mm).)  The tip is 24.652 mm
wide one-sided (both 24.468 mm before the straight sides of
`diagonal-bus/7`).  Both boards are 31.521 mm wide with `both` (the Column
board 24.4 mm with `diagonal-bus/3`, before the shared outline, 31.191 mm
with `diagonal-bus/4`, before the regular outline, and 31.335 mm with
`diagonal-bus/7`, which shared the outline over the field only), 31.052 mm
one-sided (31.2 mm with the Row tail under the band, which reached 0.148 mm
beyond it).  `diagonal-bus/7` rooted the Row tail 4.88 mm and the Column
tail 2.367 mm below the field with `both` (its Column V at up to 85 degrees,
the Row fans held 5 degrees off it); `diagonal-bus/1` put them 11.814 and
8.326 mm below the field with `both` (a corridor under the field and raised
Column stubs) and 6.278 and 2.367 mm one-sided; `diagonal-bus/2` (the tails
side by side) 4.797 and 5.564 mm with `both`, its Column tail moved 12.455
mm.
`tests/test_diagonal_bus.py` pins these figures for the plan's named corpus.

The DRC measures a diagonal-bus board as [masked](#records-of-masked-boards)
(the gate is `construction.row_bus.kind` `diagonal-bus/11`), and the
registration of the pair adds the stack keys of the
[registration record](#registration-record).  `field_footprint` and the
feasibility check's `E_BOARD_SIZE` measure its built boards, as the DRC's
board-size records do.

## Verification

`verification` holds `drc_version` (`whole-board-v3`), `numeric_epsilon_mm`,
`all_checks_passed`, `checks`, `registration` and route summary fields:

- kept from layout v1: `route_segment_count`,
  `minimum_inter_net_center_distance_mm`,
  `minimum_inter_net_copper_clearance_mm`,
  `minimum_required_inter_net_copper_clearance_mm`,
  `closest_inter_net_route_pair` (the route pair with the smallest copper
  gap: `nets`, `segments`, the piece of each, `tail` or `fanout`, since
  layout v3, and `segment_indices`, the segment within each piece; its
  centreline distance is `minimum_inter_net_center_distance_mm`, which with
  pieces of different widths need not be the smallest centre distance),
  `inter_net_copper_overlap_segment_pair_count`,
  `inter_net_clearance_violation_segment_pair_count` (both exact now; a
  pair with a tail piece counts against the finger-section spacing),
  `minimum_route_to_outline_copper_clearance_mm`, `route_clearance_passed`,
  `outline_containment_passed`, `cutout_clearance_passed`;
- new: `minimum_copper_to_outline_mm` (all copper),
  `minimum_required_outline_copper_clearance_mm`,
  `minimum_copper_to_cutout_mm`;
- dropped with the centreline rules: `minimum_route_to_outline_center_distance_mm`,
  `minimum_required_outline_center_clearance_mm`,
  `minimum_route_to_cutout_copper_clearance_mm`,
  `minimum_route_to_cutout_center_distance_mm`.

### Check records

Each of the 30 `checks` is

```json
{"rule": "copper_to_outline", "required_mm": 0.3, "measured_mm": 0.3, "comparison": "min>=",
 "violation_count": 0, "passed": true, "where": ["pad", "ROW_01"]}
```

- `comparison` is `min>=` (the smallest measured value must reach the
  requirement) or `max<=`; values are compared with the profile's
  `drc.numeric_epsilon_mm` (1e-6 mm) and no other tolerance.
- `violation_count` is exact: every pair that can violate a rule is measured
  (sort-and-sweep over bounding boxes; nothing is pruned).
- `measured_mm` is `null` when nothing was in reach (pairs are measured up
  to 2 mm beyond the rule), e.g. `coverlay_bridge` on boards whose only two
  windows are far apart (the merged field window and the contacts' window of
  1.4 mm electrodes at 2 mm); a `required_mm` of `null` marks a
  pass/fail containment check.
- `where` names the extreme: among values equal at 1e-6 mm the first in the
  deterministic sweep order wins, so records are identical across Python
  versions.
- A failing record raises its error with field `boards.<row|column>.<part>`.
- `route_route_clearance` also holds `finger_section` (`required_mm`,
  `measured_mm`, `violation_count`, `where`): the route pairs with a wide
  tail piece, which must keep the finger-section spacing (the contact pitch
  less the finger width, 0.246 mm) instead of the trace space.  The record's
  `violation_count` counts every route pair against its own rule, so it can
  fail while its `measured_mm` (the smallest gap of any route pair) meets
  its `required_mm` (the trace space).

### Whole-board DRC records

Required values are Row / Column; measured values are those of the default
build (`null`: not applicable or nothing in reach), since
P5-diagonal-bus.md section 18 the diagonal Row bus with `both`, whose boards
are checked in their masked form (the strict `coverlay_opening_to_trace`
below), and since section 20 with the surface profile's rules (its 0.5 mm
field margin); the straight Row channel of the same design
(`routing.row_sides` `channel`) measures as before, with the generic
profile's 0.75 mm (`tests/test_golden_default.py`).  The route rule is the
design's `routing.trace_space_mm` on both boards (0.127 mm by default; until
2026-10-15 it was a fixed 0.246 mm on the Row and 0.17 mm on the Column
board); the electrode-to-route and electrode-to-contact records use it too.
A route pair with a wide tail piece keeps the finger-section spacing
instead, 0.246 mm, as the traces between the contacts do (measured 0.246 /
0.246 mm on the default build).

| Record | Rule | Required (Row / Column) | Error | Field part | Default measured (Row / Column) |
| --- | --- | --- | --- | --- | --- |
| `route_route_clearance` | different-net route copper gap; the design's `routing.trace_space_mm`, and for a pair with a tail piece the finger-section spacing (`finger_section`) | 0.127 / 0.127 | `E_ROUTE_CLEARANCE` | `layers.top_copper.routes` | 0.127 / 0.169721 |
| `pad_trace_clearance` | contact to other-net route; `routing.min_pad_to_trace_mm` | 0.2 / 0.2 | `E_PAD_TRACE_CLEARANCE` | `layers.top_copper.pads` | 0.223 / 0.223 |
| `pad_pad_clearance` | contact to contact; `routing.min_pad_space_mm` | 0.2 / 0.2 | `E_PAD_CLEARANCE` | `layers.top_copper.pads` | 0.2 / 0.2 |
| `electrode_electrode_clearance` | electrode to electrode; `routing.min_electrode_gap_mm` | 0.25 / 0.25 | `E_ELECTRODE_CLEARANCE` | `layers.top_copper.electrodes` | 1.0 / 1.0 |
| `electrode_route_clearance` | electrode to other-net route; the route rule | 0.127 / 0.127 | `E_ELECTRODE_ROUTE_CLEARANCE` | `layers.top_copper.electrodes` | 0.250001 / 0.984833 |
| `electrode_pad_clearance` | electrode to contact; the route rule | 0.127 / 0.127 | `E_ELECTRODE_PAD_CLEARANCE` | `layers.top_copper.electrodes` | null / null |
| `copper_to_outline` | contacts and electrodes to the outer edge; `routing.copper_to_edge_mm` | 0.3 / 0.3 | `E_COPPER_EDGE_CLEARANCE` | `outline.points` | 0.3 / 0.3 |
| `route_to_outline` | route copper to the outer edge; `routing.copper_to_edge_mm` | 0.3 / 0.3 | `E_ROUTE_EDGE_CLEARANCE` | `layers.top_copper.routes` | 0.300999 / 0.364499 |
| `copper_to_cutout` | any copper to a routed slot; `routing.copper_to_cutout_mm` | 0.3 / 0.3 | `E_COPPER_CUTOUT_CLEARANCE` | `outline.cutouts` | null / null |
| `copper_inside_outline` | the centre of every copper item inside the outline and outside the cutouts (the distance records cover the rest) | pass/fail | `E_COPPER_OUTLINE` | `outline.points` | null / null |
| `active_field_margin` | board material around the taxel field; `routing.active_edge_clearance_mm` | 0.5 / 0.5 | `E_ACTIVE_MARGIN` | `outline.points` | 0.5 / 0.5 |
| `coverlay_openings_inside_outline` | openings inside the outline, clear of cutouts | pass/fail | `E_COVERLAY_OUTLINE` | `layers.top_coverlay_openings` | null / null |
| `coverlay_bridge` | coverlay between two openings; `coverlay.coverlay_min_bridge_mm` | 0.5 / 0.5 | `E_COVERLAY_BRIDGE` | `layers.top_coverlay_openings` | 0.8 / 0.8 |
| `coverlay_opening_to_trace` | opening to a route of another net; `coverlay.coverlay_opening_to_trace_mm` | 0.15 / 0.15 | `E_COVERLAY_TRACE_CLEARANCE` | `layers.top_coverlay_openings` | 0.150001 / 0.214656 |
| `contact_exposure` | margin by which each contact and electrode lies inside an opening of its net | 0.0 / 0.0 | `E_CONTACT_EXPOSURE` | `layers.top_coverlay_openings` | 0.05 / 0.05 |
| `stiffener_inside_outline` | every stiffener inside the outline, clear of cutouts | pass/fail | `E_STIFFENER_OUTLINE` | `layers.bottom_stiffener` | null / null |
| `stiffener_zone` | connector stiffener flush with the tip and both tail sides, `tail.stiffener_length_mm` long (largest deviation) | 0.0 / 0.0 | `E_STIFFENER_ZONE` | `layers.bottom_stiffener` | 0.0 / 0.0 |
| `stiffener_end_clearance` | straight, full-width flexible tail beyond the stiffener, up to where the outline starts to widen; `tail.stiffener_end_clearance_mm` | 0.5 / 0.5 | `E_STIFFENER_ZONE` | `layers.bottom_stiffener` | 5.5 / 6.0 |
| `outline_simple` | crossing or touching non-adjacent edge pairs plus fold-backs, outline and cutouts | 0.0 / 0.0 | `E_OUTLINE_SELF_INTERSECTION` | `outline.points` | 0.0 / 0.0 |
| `cutouts_inside_outline` | each slot strictly inside the outline; measured: narrowest board bridge beside it | pass/fail | `E_CUTOUT_OUTLINE` | `outline.cutouts` | null / null |
| `unfilleted_concave_turn_deg` | largest concave turn at one vertex; `outline.maximum_unfilleted_concave_turn_deg` | 15.0 / 15.0 | `E_CONCAVE_CORNER` | `outline.points` | 10.000589 / 10.000332 |
| `concave_fillet_radius` | effective radius of each concave run; R x cos(arc step / 2) from `outline.outline_fillet_radius_mm` and `outline.arc_segment_max_angle_deg` | 0.498097 / 0.498097 | `E_CONCAVE_CORNER` | `outline.points` | 0.517862 / 0.532658 |
| `neck_width` | narrowest outer-outline cross-section between the rounded tip and the body; the tail width (the slot is covered by the cutout records) | 6.5 / 16.5 | `E_NECK_WIDTH` | `outline.points` | 6.5 / 16.5 |
| `connectivity` | nets whose tail piece does not start on its contact, whose fan-out piece does not continue from the tail piece's end (the junction) or does not end on its electrode, or that lack exactly one piece of each; NC contacts touching copper; nets without a contact | 0.0 / 0.0 | `E_CONNECTIVITY` | `layers.top_copper.routes` | 0.0 / 0.0 |
| `min_electrode_width` | narrowest electrode; `routing.min_electrode_width_mm` | 0.1016 / 0.1016 | `E_ELECTRODE_WIDTH` | `layers.top_copper.electrodes` | 1.0 / 1.0 |
| `route_width` | largest deviation of a route piece from its width (fan-out: the design's `routing.trace_width_mm`, tail: `routing.finger_trace_width_mm`); a piece of neither kind, or narrower than JLC's minimum for the profile's copper (0.1016 mm for 1 oz), also fails | 0.0 / 0.0 | `E_ROUTE_WIDTH` | `layers.top_copper.routes` | 0.0 / 0.0 |
| `tail_width` | tail width at the contacts minus (P + 1) x pitch; `connector.tail_width_tolerance_mm` | 0.07 / 0.07 | `E_CONNECTOR_TAIL` | `outline.points` | 0.0 / 0.0 |
| `contact_geometry` | largest deviation of contact size, start from the tip, pitch and outer side offsets | 0.0 / 0.0 | `E_CONNECTOR_TAIL` | `layers.top_copper.pads` | 0.0 / 0.0 |
| `board_short_side` | short side of the outline; `limits.maximum_outline_short_side_mm` | 234.0 / 234.0 | `E_BOARD_SIZE` | `outline.points` | 41.365841 / 41.365841 |
| `board_long_side` | long side of the outline; `limits.maximum_outline_long_side_mm` | 490.0 / 490.0 | `E_BOARD_SIZE` | `outline.points` | 67.520543 / 67.520543 |

The concave-fillet requirement is the one value not taken verbatim from the
profile: it allows the sagitta of the 10 degree polygonal arcs (R0.5 drawn
in 10 degree chords meets an effective radius of at least 0.4981 mm).

### Records of masked boards

A [masked board](#masked-boards) (one with `grid_registration.taxel_mask`,
or a [diagonal Row bus](#diagonal-row-bus) board, whose
`construction.row_bus.kind` `diagonal-bus/11` is enough: without
`active_outline` its `active_field_margin` fails at `active_outline`)
has the same 30 records, rules, error codes and fields; `drc_version`
stays `whole-board-v3`.  Five records measure the masked field, every
polygon test by a sweep over edge boxes (never all pairs).  Every other
record already holds for any outline.  Unmasked boards keep the semantics
of the table above, including the own-net skip of
`coverlay_opening_to_trace`.

| Record | On a masked board | Extra key |
| --- | --- | --- |
| `active_field_margin` | the distance from the crossing region P (`grid_registration.active_outline`) to the outline and cutout edges, `where` `active_outline`; one vertex of P inside the outline and outside the cutouts; and P must be the region the board's electrodes give (each without its overhang, plus the fillers between consecutive electrodes), else a violation with `where` `active_outline_mismatch`.  Measured: 0.5 mm, the rule, where F meets P | `region`: `taxel_mask` |
| `coverlay_openings_inside_outline` | a polygon window must be simple, rectilinear and orthogonally convex; every opening lies inside the outline (it may touch it, as the gang window touches the tip; the generated field window keeps 0.2 mm) and clear of the cutouts | |
| `coverlay_bridge` | between two openings, the gap of their regions: by their edges when one is a polygon (0 when they overlap or nest), the box gap between rectangles | |
| `coverlay_opening_to_trace` | **strict**: a route piece is exempt only near its own features, the contacts and electrodes of its net that one of its ends touches.  The piece is clipped outside each own feature grown by the expansion, the rule and half its width; the openings' edges lying on an own feature's window (the feature plus the expansion) are left out, which loses nothing (every remaining part is farther than the rule from that window).  The rest keeps the rule from every remaining edge, and must lie outside every opening (`where` ends in `inside` otherwise).  On the surface profile it measures 0.214656 mm, the gang window's corner beside the outer contacts' tail pieces; the field window alone keeps at least 0.15 mm (0.2742 mm at 0.6 mm pitch with 0.35 mm cells and 0.1016 mm traces) | `semantics`: `strict` |
| `contact_exposure` | a feature's margin in a polygon window is its distance to the window's edges, negative when it is not inside; rectangles as above | `electrodes`: `{measured_mm, where}`, the electrodes' own minimum (the 0.1 mm expansion) |

### Registration record

`verification.registration` is the same cross-board record on both boards:
`rule`, `required_mm` (the epsilon), `row_electrode_axis` and
`column_electrode_axis` (`x` or `y` in the shared frame), `orthogonal`,
`active_region_size_deviation_mm`, `identical_active_region`,
`row_grid_deviation_mm`, `row_grid_matches`, `column_grid_deviation_mm`,
`column_grid_matches` and `passed`.  A grid matches when electrode *i*
starts *i* x pitch into the taxel field, all electrodes have the field
width and each overhangs the field by `routing.electrode_overhang_mm` at both
ends.

A masked pair (either board with `grid_registration.taxel_mask`) is
registered in the **stack frame** (`stack_frame` in `engine/drc.py`): each turned
board moved so its active region's centre is the origin, and the physical
top board, which lies copper side down on the film, turned over about its
tail axis (`x -> -x` for bottom and top tails, `y -> -y` for left and right
ones), so both boards are seen from outside the stack.  The record then
measures the grids on the masked grid: across its length electrode *i*
starts *i* x pitch into the field and has the cell width, as above; along
it, both ends overhang by `routing.electrode_overhang_mm` the outer taxels
of its span, which are the other board's electrodes of the nets in its span
on their grid slots.  It adds:

| Key | Meaning |
| --- | --- |
| `taxel_mask_identical` | both boards carry the same `taxel_mask` |
| `crossing_set_matches_mask` | `wrong_crossing_count` is 0 |
| `wrong_crossing_count` | the ROW x COL electrode pairs whose overlap in the stack frame (of positive width and height) differs from the mask: a crossing it does not have, or a taxel it has without one |
| `inactive_crossing_separation_mm` | the smallest misregistration that makes an inactive pair overlap: over the inactive pairs, the least of the larger of their x and y gaps (`max(pitch - cell) - overhang` at a step of the mask: 0.05 mm at 0.6 mm pitch with 0.35 mm cells, 0.4 mm at 2 mm with 1.4 mm) |
| `inactive_crossings_separated` | that separation is more than the epsilon (or there is no inactive pair) |
| `trace_overlap_mm` | reported only: the longest run of one Row net's traces on one Column net's traces in the stack frame (their parallel segments whose copper overlaps across them by a positive width, summed per net pair; crossings at an angle are not runs), 0 when there is none |
| `trace_overlap_nets` | that pair, `[ROW_xx, COL_yy]` (the first in net order on a tie), or `null` |
| `trace_overlap_pairs` | the number of ROW x COL net pairs with such a run |
| `trace_overlap_area_mm2` | the copper area both boards cover along the runs, every pair together |

`passed` then also needs `taxel_mask_identical`,
`crossing_set_matches_mask` and `inactive_crossings_separated`; the trace
overlap never fails it.  An unmasked pair has none of these keys.

Both traces of a run lie under their coverlay, with the film between, so
they never touch; but the ROW and COL nets couple capacitively along it,
whether that matters is a question for the film vendor (risk 3 of
`claude/specs/masked-field/PLAN.md`).  Runs come from the straight
constructions with both tails on one side: the lane taper slides the field
over the Row channel, and a raised Column stub, which runs down its own
centre line, lies on a Row lane from its electrode to the tail.  The
soft-finger taper (48 x 12, tight routing) has 5 pairs, the longest
`ROW_07` on `COL_12` for 83.8 mm, 11.6 mm² in all; with opposite tails
there are none.  Unmasked pairs with both tails on one side have short
runs, up to a few mm, beside the tail roots (not reported).

A [diagonal Row bus](#diagonal-row-bus) pair (either board with
`construction.row_bus`; its boards are masked, so it has the keys above)
adds its **stack keys** when the boards are orthogonal, measured in the
stack frame.  Outside the taxel field the boards may overlap freely, the
stacked tails too, so crossings, runs and the tails' overlap are reported
only; the field, the outline over it and the tails' exit side are rules:

| Key | Meaning and rule |
| --- | --- |
| `trace_over_other_electrode_count` | route parts, outside their own electrode's zone (the electrode grown by the coverlay expansion, the opening-to-trace rule and half the trace width, as in the strict `coverlay_opening_to_trace`), whose copper reaches an electrode of the other board, each part once however many it reaches; must be 0 |
| `trace_over_other_window_count` | such parts whose copper reaches the other board's field window: the union of its electrode openings (the merged field window, or one opening per electrode); must be 0.  Either count fails the registration (a hand-edited board without its openings still fails on its electrodes) |
| `row_trace_to_column_window_mm`, `column_trace_to_row_window_mm` | the nearest such part to the other board's field window (`null` beyond 2 mm); under the 0.15 mm opening-to-trace rule it is the warning `W_STACK_TRACE_WINDOW` (fine pitches), not an error |
| `trace_crossing_count`, `trace_crossing_pairs`, `trace_crossing_min_angle_deg` | the Row and Column trace segments whose copper overlaps at an angle (runs along each other are `trace_overlap_mm`'s), the ROW x COL net pairs among them and their least angle (`null` without a crossing); reported only (the fans keep 5 degrees or more from the Column fan-out's diagonals) |
| `trace_overlap_mm` | as above; reported only: chiefly the stacked tails' contact columns, one on the other (both at the 0.5 mm contact pitch) from the tails up to the traces' last bends |
| `tail_sides_match` | both tails leave through the same exit side (the design's `E_ROW_BUS_TAILS` rule, on the built pair); must be `true` |
| `tail_overlap_width_mm` | the width, across the tails, over which the two tails' rectangles (tip to root) overlap in the stack: the Row tail on the Column tail (0 when they do not meet); reported only |
| `shared_outline_below_field_mm` | the Row board's `construction.row_bus.shared_outline_below_field_mm`: how far below the taxel field (the active region's edge toward the tails) the two boards share one outline, their tails' roots since `diagonal-bus/8` (`null` without the record) |
| `outline_deviation_over_field_mm` | in the stack, tails down, the largest distance from a vertex of either outline's part beyond that level (away from the tails; an edge lying on the level counts as below it) to the other's outline there, up to 2 mm (2: that far or farther); `null` without the record |
| `outlines_coincide_over_field` | the two outlines are one down to that level (the name kept from when it was F's bottom): the deviation within the layout grid (the profile's epsilon, 1e-6 mm); must be `true` |

`passed` then also needs every rule of the table.

Each failing sub-check raises its own `E_REGISTRATION`:

| Failure | Field |
| --- | --- |
| parallel electrodes (the boards would not cross) | `tail.column_side` |
| taxel fields of different size | `boards.column.grid_registration.active_region` |
| Row or Column electrodes off the taxel grid (on a masked pair, the masked grid) | `boards.row.layers.top_copper.electrodes` / `boards.column.layers.top_copper.electrodes` |
| masked pair: the boards' taxel masks differ | `boards.column.grid_registration.taxel_mask` |
| masked pair: crossings that differ from the mask (the first is named), or an inactive crossing not separated | `boards.row.grid_registration.taxel_mask` |
| diagonal pair: a trace over the other board's electrodes or field window | `boards.row.layers.top_copper.routes` / `boards.column.layers.top_copper.routes` |
| diagonal pair: tails that leave on different sides | `boards.column.tail.side` |
| diagonal pair: outlines that differ above the shared level (the tails' roots) | `boards.column.outline` |
| diagonal pair: a Row board without the shared level | `boards.row.construction.row_bus.shared_outline_below_field_mm` |

Validation rejects quarter-turn tail combinations first
(`E_TAIL_SIDE_PARALLEL`), so a generated design reaches the parallel case
only through edited geometry.  The electrode axis is inferred from where the
electrode field outgrows the taxel field, so a single electrode displaced
sideways by more than the overhang can also be reported as parallel (with
field `tail.column_side`) next to the DRC error that names the real defect.

## Profile rules used by the layout and the DRC

Values of `profiles/jlc_fpc_standard_v1.json` (revision 2026-11-06b);
[APP_HANDOFF](../claude/APP_HANDOFF.md#locked-profile) lists the whole profile.

| Profile key | Value | Used for |
| --- | --- | --- |
| `routing.finger_trace_width_mm` | 0.254 | tail (gold-finger) pieces; contact pitch less this is the finger-section spacing, 0.246 mm, which every route pair with a tail piece keeps |
| `limits.minimum_trace_width_mm` | 0.1016 | narrowest bundle trace (JLC 1 oz: 4 mil) |
| `limits.maximum_trace_width_mm` | 0.254 | widest bundle trace (the finger width) |
| `limits.minimum_trace_space_mm` | 0.1016 | narrowest bundle spacing (JLC 1 oz: 4 mil) |
| `limits.maximum_trace_space_mm` | 0.246 | widest bundle spacing (the finger-section spacing) |
| `routing.min_pad_space_mm` | 0.2 | contact to contact |
| `routing.min_pad_to_trace_mm` | 0.2 | contact to other-net route (JLC: 0.15) |
| `routing.min_electrode_gap_mm` | 0.25 | electrode to electrode, and the input rule width + gap <= pitch |
| `routing.min_electrode_width_mm` | 0.1016 | narrowest electrode (JLC's 1 oz minimum since 2026-10-15; 0.1 before, re-audit N4) |
| `routing.copper_to_edge_mm` | 0.3 | all copper to the board edge (JLC laser outline) |
| `routing.copper_to_cutout_mm` | 0.3 | all copper to routed slots (JLC) |
| `routing.active_edge_clearance_mm` | 0.75 | board material around the taxel field |
| `routing.electrode_overhang_mm` | 0.2 | electrode overhang beyond the crossing field |
| `connector.pad_pitch_mm` | 0.5 | contact pitch |
| `connector.pad_width_mm` | 0.3 | contact width |
| `connector.contact_length_mm` | 4.0 | contact length |
| `connector.contact_tip_clearance_mm` | 0.3 | tip edge to contact start |
| `connector.contact_center_to_side_edge_mm` | 0.5 | tail side to the outer contact centre |
| `connector.tail_tip_corner_radius_mm` | 0.3 | tip corner radius |
| `connector.tail_width_tolerance_mm` | 0.07 | tail width tolerance (THD0515 drawing) |
| `connector.maximum_pins` | 64 | largest connector |
| `coverlay.coverlay_expansion_mm` | 0.1 | opening expansion per side (JLC) |
| `coverlay.coverlay_min_bridge_mm` | 0.5 | narrowest coverlay bridge (JLC) |
| `coverlay.coverlay_opening_to_trace_mm` | 0.15 | opening to other-net trace (JLC) |
| `tail.minimum_length_mm` | 7.0 | shortest tail |
| `tail.stiffener_length_mm` | 6.0 | connector-zone stiffener length |
| `tail.stiffener_end_clearance_mm` | 0.5 | straight flexible tail beyond the stiffener (product default) |
| `outline.outline_fillet_radius_mm` | 0.5 | concave corner fillets |
| `outline.arc_segment_max_angle_deg` | 10.0 | polygonal arc step |
| `outline.maximum_unfilleted_concave_turn_deg` | 15.0 | sharpest concave turn at one vertex |
| `outline.offset_allowance_mm` | 0.001 | construction allowance of the fan-out envelope |
| `fanout.maximum_taper_angle_deg` | 60.0 | angle cap of the bus-style diagonals (both boards) |
| `drc.numeric_epsilon_mm` | 1e-06 | the only comparison tolerance |
| `limits.maximum_outline_short_side_mm` | 234.0 | fabrication maximum, short side |
| `limits.maximum_outline_long_side_mm` | 490.0 | fabrication maximum, long side |
| `stackup.stiffener_thickness_mm` | 0.1 | PI stiffener (JLC options 0.1, 0.15, 0.2, 0.225, 0.25; 0.225 until 2026-11-06) |

## Surface template profile (`jlc-fpc-surface-v1`)

`profiles/jlc_fpc_surface_v1.json` (revision 2026-11-06b), the locked
profile of the surface template (`surface_matrix_v1`, see
[API.md](API.md#surface-template-surface_matrix_v1)).  It is the generic
profile with `template_id: "surface_matrix_v1"` and these rules; every
other rule is the generic value above.  The three policy keys are optional
in any profile and checked only when present; absent, they are the generic
behaviour (`contact_aligned`, `cap`, `bundle`).

| Profile key | Value | Used for |
| --- | --- | --- |
| `routing.active_edge_clearance_mm` | 0.5 | board material around the taxel field (the 0.2 mm overhang + 0.3 mm copper to edge) |
| `routing.row_channel` | tight | Row lanes packed against the edge and the field window, the field just above the expansion ([Row channel](#row-channel)) |
| `tail.minimum_length_mm` | 7.5 | shortest tail (the tail check needs 7.344 mm at an 85 degree cap) |
| `fanout.maximum_channels_per_lane` | 64 | one lane holds every column |
| `fanout.maximum_lanes` | 1 | one Column fan-out lane, no slot |
| `fanout.maximum_taper_angle_deg` | 85.0 | steepest bus angle cap |
| `fanout.minimum_taper_angle_deg` | 60.0 | first cap of the bus-angle search (a whole number of degrees, at least 1; the maximum is tried last when it is fractional) |
| `fanout.bus_angle` | shortest | each transition at the whole-degree cap (60-85) that makes it lowest down to the tail root; a tie keeps the smaller |
| `fanout.column_convergence` | direct | the Column routes converge straight into the contact columns ([Column fan-out](#column-fan-out)) |
| `limits.maximum_columns` | 64 | most columns |
| `limits.maximum_tail_length_mm` | 200.0 | longest tail (80.0 before P5-diagonal-bus.md section 23: a capped field stacks at the fingertip and its tails run down the face to the exit) |

## Issue catalogue

Every code the engine emits (`engine/schema.py`, also served by `GET
/api/schema` as `x-error-codes` / `x-warning-codes`, and by `GET
/api/default` as `profile.issue_codes`).  Field conventions: request and
input issues name the design path (an alias value error names the alias,
e.g. `connector_side`); profile issues name `profile.<section>.<key>`; DRC
issues name `boards.<row|column>.<part>` (registration: see above).  The
HTTP and CLI codes are in [API.md](API.md).

| Code | Source | Meaning |
| --- | --- | --- |
| `E_DESIGN_TYPE` | request | The design is not a JSON object. |
| `E_UNKNOWN_FIELD` | request | A key outside `tactile-fpc-design/v1` and its aliases; the field is its JSON path. Wrapper objects such as `{"design": {...}}` are rejected the same way. |
| `E_MATRIX_OBJECT` | request | `matrix` is not an object. |
| `E_TAIL_OBJECT` | request | `tail` is not an object. |
| `E_CONNECTOR_OBJECT` | request | `connector` is not an object. |
| `E_ROUTING_OBJECT` | request | `routing` is not an object. |
| `E_SCHEMA_VERSION` | request | `schema_version` is present but is not `tactile-fpc-design/v1`. |
| `E_TEMPLATE_UNSUPPORTED` | request | `template_id` is not `generic_matrix_v1` or `surface_matrix_v1` (`null` included), or the profile given to `generate_design` belongs to the other template (then the only error). |
| `E_PROJECT_NAME` | input | `project_name` is empty, longer than `limits.maximum_project_name_length` after trimming, or contains control characters. |
| `E_ROWS_INTEGER` | input | `matrix.rows` is not an integer (an integral float such as 12.0 is accepted). |
| `E_ROWS_RANGE` | input | `matrix.rows` is outside `limits.minimum_rows`..`maximum_rows`. |
| `E_COLUMNS_INTEGER` | input | `matrix.columns` is not an integer (32.0 is accepted). |
| `E_COLUMNS_RANGE` | input | `matrix.columns` is outside `limits.minimum_columns`..`maximum_columns`. |
| `E_COLUMNS_LANE_CAPACITY` | input | `matrix.columns` exceeds `fanout.maximum_lanes` x `fanout.maximum_channels_per_lane`. |
| `E_NUMERIC` | input | A millimetre field is not a finite number (NaN, Infinity, strings, booleans and integers beyond 2^53 included). |
| `E_PITCH_RANGE` | input | A pitch is outside `limits.minimum_pitch_mm`..`maximum_pitch_mm`. |
| `E_TAXEL_SIZE` | input | An electrode width is negative. |
| `E_ELECTRODE_WIDTH` | input+drc | An electrode is narrower than `routing.min_electrode_width_mm`. |
| `E_ELECTRODE_GAP` | input | taxel width + `routing.min_electrode_gap_mm` exceeds the pitch; the message gives the largest legal width. |
| `E_TAIL_LENGTH` | input | A tail length is outside `tail.minimum_length_mm`..`limits.maximum_tail_length_mm`. |
| `E_TAIL_SIDE` | input | A tail side (or the `connector_side` alias) is not bottom, top, left or right. |
| `E_TAIL_SIDE_PARALLEL` | input | `tail.column_side` is a quarter turn from `tail.row_side`, which makes the electrodes parallel; the message lists the allowed sides. |
| `E_ROLE_MAPPING` | input | A `role_mapping` position is not rows or columns (field `role_mapping.top`/`.bottom`), both name one role (field `role_mapping`), or the `row_fpc_position` alias is invalid. |
| `E_CHANNEL_ORDER` | input | A channel order (or the `scan_order` alias) is not ascending/descending (forward/reverse for `scan_order`). |
| `E_CONNECTOR_PINS` | input | A connector size is not `null` or an integer between the channel count and `connector.maximum_pins`. |
| `E_TRACE_WIDTH` | input | `routing.trace_width_mm` is outside `limits.minimum_trace_width_mm`..`maximum_trace_width_mm` (JLC's 1 oz minimum to the finger width); the message gives both bounds. |
| `E_TRACE_SPACE` | input | `routing.trace_space_mm` is outside `limits.minimum_trace_space_mm`..`maximum_trace_space_mm` (JLC's 1 oz minimum to the finger-section spacing); the message gives both bounds. |
| `E_MASK_TYPE` | request | `matrix.mask` (surface template only) is not `null` or an array of `[first, last]` integer pairs; the field is `matrix.mask`, or `matrix.mask[i]` for one pair. |
| `E_MASK_ROWS` | input | `matrix.mask` does not have one pair per row (`matrix.rows`). |
| `E_MASK_RANGE` | input | A row's span (`matrix.mask[i]`) is not `1 <= first <= last <= matrix.columns`. |
| `E_MASK_DISCONNECTED` | input | Two consecutive rows share no column (`matrix.mask[i]` of the lower one). |
| `E_MASK_COLUMN_EMPTY` | input | A column has no taxel: the mask spans every column of `matrix.columns`. |
| `E_MASK_COLUMN_GAP` | input | A column's taxels are not consecutive rows. |
| `E_ROW_SIDES` | input | `routing.row_sides` is not `left`, `right`, `both` or `channel`; absent or `null` is the template's default (generic: `both`, or `channel` for opposite tails or a single row or column; surface: the straight Row channel). |
| `E_ROW_BUS_TAILS` | input | `routing.row_sides` `left`, `right` or `both` with `tail.row_side` opposite `tail.column_side`: the diagonal Row bus puts both tails on one side (field `routing.row_sides`; a quarter turn is `E_TAIL_SIDE_PARALLEL`; `channel` takes opposite tails). |
| `E_BOARD_SIZE` | feasibility+drc | An outline exceeds the fabrication maximum (either orientation); the message lists verified bounds that fit. |
| `E_MASK_ROUTING` | feasibility | A valid mask outside the construction classes the engine builds, the straight Row channel and Column fan-out ([masked boards](#masked-boards)); the field is `matrix.mask[i]` of the row the message names, and the message gives the fix. |
| `E_ROW_BUS_INFEASIBLE` | build | The diagonal Row bus (`diagonal-bus/11`) cannot order or place its lanes (field `routing.row_sides`); `generate_design` builds no boards. Reserved: no design measured so far raises it. |
| `E_PROFILE_MISSING` | profile | A profile section or rule is missing or not a positive finite number. |
| `E_PROFILE_FAB_LIMIT` | profile | A profile design rule is looser than the published fabrication capability (the trace minimums: the one of `stackup.copper_thickness_mm`). |
| `E_PROFILE_INCONSISTENT` | profile | Profile rules contradict each other. |
| `E_PROFILE_PAD_SPACE` | profile | Connector contacts or their leads violate the pad spacing rules. |
| `E_PROFILE_ROUTE_SPACE` | profile | Routes at the contact pitch cannot keep the largest trace space the limits allow. |
| `E_ROUTE_CLEARANCE` | drc | Route-to-route clearance between different nets. |
| `E_PAD_TRACE_CLEARANCE` | drc | Contact-to-other-net route clearance. |
| `E_PAD_CLEARANCE` | drc | Contact-to-contact clearance. |
| `E_ELECTRODE_CLEARANCE` | drc | Electrode-to-electrode clearance. |
| `E_ELECTRODE_ROUTE_CLEARANCE` | drc | Electrode-to-other-net route clearance. |
| `E_ELECTRODE_PAD_CLEARANCE` | drc | Electrode-to-contact clearance. |
| `E_COPPER_EDGE_CLEARANCE` | drc | Copper-to-board-edge clearance. |
| `E_ROUTE_EDGE_CLEARANCE` | drc | Route-to-board-edge clearance. |
| `E_COPPER_OUTLINE` | drc | Copper outside the outline. |
| `E_COPPER_CUTOUT_CLEARANCE` | drc | Copper-to-routed-slot clearance. |
| `E_ACTIVE_MARGIN` | drc | Board material around the active field below `routing.active_edge_clearance_mm`. |
| `E_COVERLAY_OUTLINE` | drc | A coverlay opening crosses the outline. |
| `E_COVERLAY_BRIDGE` | drc | A coverlay bridge narrower than `coverlay.coverlay_min_bridge_mm`. |
| `E_COVERLAY_TRACE_CLEARANCE` | drc | A coverlay opening too close to another net's trace. |
| `E_CONTACT_EXPOSURE` | drc | A contact or electrode is not fully exposed by an opening of its net. |
| `E_STIFFENER_OUTLINE` | drc | A stiffener leaves the outline. |
| `E_STIFFENER_ZONE` | drc | The stiffened connector zone, or the straight flexible tail beyond it, is wrong. |
| `E_OUTLINE_SELF_INTERSECTION` | drc | The outline or a cutout is not a simple polygon. |
| `E_CUTOUT_OUTLINE` | drc | A routed slot is not inside the outline. |
| `E_CONCAVE_CORNER` | drc | An unfilleted or too tightly filleted concave outline corner. |
| `E_NECK_WIDTH` | drc | The board is narrower than the tail between tail and body. |
| `E_CONNECTIVITY` | drc | A net's tail and fan-out pieces do not join its contact, each other and its electrode, or an NC contact touches copper. |
| `E_ROUTE_WIDTH` | drc | A route piece is not its width (fan-out: `routing.trace_width_mm`, tail: `routing.finger_trace_width_mm`) or is below the copper's fabrication minimum. |
| `E_CONNECTOR_TAIL` | drc | Tail width or contact geometry differs from the connector model. |
| `E_REGISTRATION` | drc | Row and Column electrodes are not orthogonal or their taxel grids differ; for a diagonal Row bus pair also a stacked trace over the other board's electrodes or its field window, tails that leave on different sides, or outlines that differ over the taxel field, where the two boards share one outline (outside it the boards and their stacked tails may overlap). |
| `W_SCHEMA_VERSION_DEFAULTED` | request | `schema_version` was missing; `tactile-fpc-design/v1` was assumed. |
| `W_ALIAS_SHADOWED` | request | An alias was ignored because a nested field (or a higher-precedence alias) gave the same field another value. |
| `W_HIGH_FILL_FACTOR` | input | An electrode uses more than `limits.high_fill_factor_warning` of its pitch. |
| `W_LARGE_MATRIX` | input | rows x columns exceeds `limits.large_matrix_warning_taxels`. |
| `W_MASK_INACTIVE_GAP` | input | The mask's inactive crossings are under 0.15 mm from the electrodes beside them (the larger electrode gap less the 0.2 mm overhang), so a misregistered stack may make one read; field `matrix.pitch_x_mm`. |
| `W_STACK_TRACE_WINDOW` | drc | A diagonal Row bus pair has a stacked trace closer to the other board's field window than the 0.15 mm coverlay opening-to-trace rule (fine pitches); field `boards.row.layers.top_copper.routes` or `boards.column.layers.top_copper.routes`. |

Request warnings (`W_SCHEMA_VERSION_DEFAULTED`, `W_ALIAS_SHADOWED`) describe
how a request was written, not the design: the manifest does not count
them, so equivalent requests share one manifest.
