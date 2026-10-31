# API, CLI and HTTP contract

The machine-facing surface of the generator: the Python functions, the
design input and its normalization, the JSON Schema, the build identity, the
local HTTP server and `cli.py`.  What a result contains is in
[LAYOUT_SCHEMA.md](LAYOUT_SCHEMA.md); what the exports contain is in
[PHASE2_DIRECT_GERBER.md](PHASE2_DIRECT_GERBER.md) and, for the EasyEDA Pro
projects, [EASYEDA_EXPORT.md](EASYEDA_EXPORT.md).
`tests/test_docs_consistency.py` checks the entry points, the input table,
the code tables and the limits and sizes quoted below against the engine,
the server and the CLI, and runs the Python snippet.

## Python entry points

```python
from engine import check_design, default_design, design_schema, generate_design, result_view
from exporters import artifact_filenames, build_easyeda_exports, build_exports, easyeda_filenames

result = generate_design({"matrix": {"rows": 16, "columns": 32}})   # partial designs take the defaults
assert result["ok"], result["validation"]["errors"]
zips = build_exports(result)          # {top_fpc_gerber_zip, bottom_fpc_gerber_zip, project_review_bundle_zip}: bytes
names = artifact_filenames(result)    # the download names of the same keys
easyeda = build_easyeda_exports(result)    # {easyeda_pro_zip}: one native EasyEDA Pro .epro2 per board
assert easyeda_filenames(result)["easyeda_pro_zip"].endswith("-easyeda-pro.zip")
```

| Function | Returns |
| --- | --- |
| `default_design()` | a fresh default design (12 x 32, 2.0 mm pitch, 1.4 mm electrodes); `default_design("surface_matrix_v1")` is the same preset on the [surface template](#surface-template-surface_matrix_v1) |
| `check_design(data)` | `{ok, design, validation, identity}`: normalization, input rules and feasibility, no geometry and so no DRC; `identity.build_id` is the id `generate_design` would give |
| `generate_design(data=None, *, cache=None, profile=None)` | the result object; `None` means "no request: the defaults" (the HTTP API and the CLI reject a `null` document); `cache` is a `BuildCache` reused across calls; `profile` replaces the locked profile and is checked like it |
| `result_view(result, "full" or "compact")` | the HTTP views below |
| `design_schema()`, `input_limits()`, `issue_codes()` | the JSON Schema, per-field form limits and the issue catalogue, all generated from the profile; `design_schema(profile)` and `input_limits(profile)` are those of the profile's template |
| `load_profile(template_id)` | a fresh, checked copy of a template's locked profile: `generic_matrix_v1` (the default, `profiles/jlc_fpc_standard_v1.json`) or `surface_matrix_v1` (`profiles/jlc_fpc_surface_v1.json`) |
| `field_footprint(design, profile)` | the board material around the taxel field, from the plans alone (no geometry, so cheap enough for a fit search) for a valid canonical design and its template's profile: `field` `{width, height}` and per board (`row`, `column`) `left`, `right`, `top` (the outline beyond the field's sides), `bottom` (the tail root's depth below the field) and `tail` `{x, width, length}`, in mm, in the board's own frame with the tail down; a [masked](#field-mask-matrixmask) design is measured on its masked boards and adds `mask` `{row, column}`, each board's `outline` above its tail root before the fillets (a counter-clockwise ring from the field's lower-left corner; the fillets add material only outside it, within the fillet radius of its concave corners and of its corners on the tail root); a [diagonal Row bus](#diagonal-row-bus-routingrow_sides) is measured on its built boards (the construction has no plan apart from its geometry), and a masked one's `mask` outlines are its boards' outlines above the root, fillets included |
| `design_mask(design)`, `column_spans(mask, columns)`, `row_frame_spans(design)`, `column_frame_spans(design)`, `row_taper(design, profile)`, `mask_class(design, profile)` | the [field mask](#field-mask-matrixmask) of a canonical design (`((first, last), ...)` per row, or `None`), each column's first and last row, the rows' spans as x-slots of the Row board from its channel and the columns' spans as row slots of the Column board from its tail, the lane taper `W_k` (the smallest start of each row's crossings beside a tight Row channel), and the construction classes (`({"row": "straight", "column": "straight"}, None)`; `({"row": "diagonal", "column": "straight"}, None)` for every design with [`routing.row_sides`](#diagonal-row-bus-routingrow_sides), masked or not) or the `E_MASK_ROUTING` issue that refuses the mask |
| `load_design_json(text_or_bytes)` | strict JSON parser of a request (raises `DesignJSONError` only) |
| `build_exports(result, *, cache=None)` | the three ZIPs; raises `ExportError` and nothing else |
| `artifact_filenames(result)` | `{build_id}-{side}-{role}-direct-gerber.zip` and `{build_id}-project-review.zip` |
| `build_easyeda_exports(result, *, cache=None)` | `{easyeda_pro_zip}`: the [EasyEDA Pro projects](EASYEDA_EXPORT.md), one native `.epro2` per board with `README_EASYEDA.txt`, an archive of its own (the three ZIPs above keep their bytes); raises `ExportError` and nothing else |
| `easyeda_filenames(result)` | `{build_id}-easyeda-pro.zip`, and the member `easyeda_pro/{build_id}-{side}-{role}.epro2` of each board as `top_epro2` and `bottom_epro2` |

## Design input (`tactile-fpc-design/v1`)

Every field is optional; a missing field takes the default.

| Field | Kind | Range / values | Default | Accepted aliases |
| --- | --- | --- | --- | --- |
| `schema_version` | string | `tactile-fpc-design/v1` | (assumed, with a warning) | |
| `template_id` | string | `generic_matrix_v1` (this table; the surface template has [its own limits](#surface-template-surface_matrix_v1)) | `generic_matrix_v1` | |
| `project_name` | string | 1-80 characters after trimming, no control characters | `Tactile FPC <rows>x<columns>` | `name` |
| `matrix.rows` | integer | 1-64 | 12 | `rows`, `row_num` |
| `matrix.columns` | integer | 1-64 and at most 32 with `routing.row_sides` `channel` | 32 | `columns`, `column_num` |
| `matrix.pitch_x_mm` | number | 0.6-10 | 2.0 | `pitch_x_mm` |
| `matrix.pitch_y_mm` | number | 0.6-10 | 2.0 | `pitch_y_mm` |
| `matrix.taxel_width_mm` | number | 0.1016-9.75 and at most `pitch_x_mm - 0.25` | 1.4 | `matrix.column_electrode_width_mm`, `taxel_width_mm`, `column_electrode_width_mm`, `column_electrode_width`, `taxel_size_mm` |
| `matrix.taxel_height_mm` | number | 0.1016-9.75 and at most `pitch_y_mm - 0.25` | 1.4 | `matrix.row_electrode_width_mm`, `taxel_height_mm`, `row_electrode_width_mm`, `row_electrode_width`, `taxel_size_mm` |
| `tail.top_length_mm` | number | 7.5-80 and from 7.0 with `routing.row_sides` `channel`; the engine takes the diagonal Row bus's tails to the surface profile's 200 (the schema and the browser's form keep 80) | 12.0 | `tail.length_mm`, `top_tail_length_mm`, `tail_length_mm` |
| `tail.bottom_length_mm` | number | 7.5-80 and from 7.0 with `routing.row_sides` `channel`; the bus's tails to 200 in the engine | 12.0 (7.0 with `channel`) | `tail.length_mm`, `bottom_tail_length_mm`, `tail_length_mm` |
| `tail.row_side` | string | `bottom`, `top`, `left`, `right` | `bottom` | `connector_side` |
| `tail.column_side` | string | equal or opposite to `tail.row_side` | `bottom` | `connector_side` |
| `connector.row_pins` | integer or null | rows-64 | null (one per channel) | |
| `connector.column_pins` | integer or null | columns-64 | null | |
| `role_mapping.top` / `.bottom` | string | `rows` and `columns`, once each | `rows` / `columns` | `row_fpc_position` (`top`: rows on top, `bottom`: columns on top) |
| `channel_order.rows` / `.columns` | string | `ascending`, `descending` | `ascending` | `scan_order` (`forward`/`ascending`, `reverse`/`descending`, both roles) |
| `routing.trace_width_mm` | number | 0.1016-0.254 | 0.127 | `trace_width_mm` |
| `routing.trace_space_mm` | number | 0.1016-0.246 | 0.127 | `trace_space_mm` |
| `routing.row_sides` | string or null | `left`, `right`, `both`, `channel` | `both` ([Row traces](#diagonal-row-bus-routingrow_sides): `channel` for opposite tails or a single row or column) | |

The diagonal Row bus (`routing.row_sides` `both`, `left` or `right`, the
default) is built with CAD mode's rule set, the surface profile, on this
template too ([Diagonal Row bus](#diagonal-row-bus-routingrow_sides)): up to
64 columns and tails from 7.5 mm, the default bottom tail 12 mm, the top
tail's length, so the stacked tails end together (the user's decision of
2026-10-27, P5-diagonal-bus.md section 27.7; 7.5 mm, the rule set's
shortest, before).  The
straight Row channel (`channel`) keeps the generic profile: at most 32
columns, tails from 7.0 mm, the default bottom tail 7.0 mm (where the
design defaults to the channel, too).  `GET /api/schema` gives the bus's
bounds and each field's `x-channel` bounds.

`taxel_width_mm` is the Column electrode width and `taxel_height_mm` the Row
electrode width; their crossing is the nominal taxel.  `routing` sets the thin
fan-out traces between the electrodes and the tail: they run as a bundle at
`trace_width_mm + trace_space_mm` (0.254 mm by default, 5/5 mil) and widen to
the profile's 0.254 mm gold-finger width (`routing.finger_trace_width_mm`) in
the tail.  The range runs from JLCPCB's minimum for the ordered 1 oz copper,
4/4 mil (0.1016 mm, `limits.minimum_trace_width_mm` / `_space_mm`), up to the
finger width and the finger gap (0.254 / 0.246 mm), so width + spacing
never exceeds the 0.5 mm contact pitch; outside it the errors are
`E_TRACE_WIDTH` and `E_TRACE_SPACE` (a value that is not a number is
`E_NUMERIC`, a `routing` that is not an object `E_ROUTING_OBJECT`).  A
bundle pitch near the 0.5 mm contact pitch makes the expansion below the
Row field taller, not shorter ([LAYOUT_SCHEMA.md](LAYOUT_SCHEMA.md#row-channel)),
so the routing fields can decide an `E_BOARD_SIZE` error, whose advice does
not name them.  `tail.top_length_mm`
belongs to the FPC that `role_mapping` puts on top of the stack.  Cross-field
rules (electrode gap, role mapping, tail sides, connector size and the
234 x 490 mm board limit) are enforced by the engine and listed in the
schema's `x-cross-field-rules`.  More than 16 columns no longer need a
minimum X pitch: with a wide bundle on a narrow field the straight
channel's two-lane Column fan-out spreads wider than the sensor (see
[LAYOUT_SCHEMA.md](LAYOUT_SCHEMA.md#column-fan-out)); the board-size limit
(`E_BOARD_SIZE`) still applies.

### Normalization

- **Strict keys.** A key outside the version and its aliases, at any level,
  is `E_UNKNOWN_FIELD` with its JSON path (`matrix.colums`, or
  `matrix["row count"]` for keys that are not identifiers), with a hint such
  as "did you mean matrix.columns?".  A wrapped design (`{"design": {...}}`,
  or a whole posted result) is rejected the same way.  At most 20 unknown
  keys are listed, plus one error counting the rest.
- **Precedence.** For each field: the canonical nested field, then nested
  legacy names (`tail.length_mm`, `matrix.column_electrode_width_mm`,
  `matrix.row_electrode_width_mm`), then specific flat aliases, then flat
  aliases that set two fields (`tail_length_mm`, `taxel_size_mm`,
  `connector_side`, `row_fpc_position`, `scan_order`).  Nested always wins
  over flat.  A shadowed alias with a different value raises
  `W_ALIAS_SHADOWED`.
- **Alias values.** Invalid values of the enumerated aliases
  (`connector_side`, `row_fpc_position`, `scan_order`) are errors at the alias
  path with the domain code (`E_TAIL_SIDE`, `E_ROLE_MAPPING`,
  `E_CHANNEL_ORDER`), even when a nested field shadows them.
- **Versions.** A missing `schema_version` is assumed with
  `W_SCHEMA_VERSION_DEFAULTED`; any other value is `E_SCHEMA_VERSION`.
  `template_id` is `generic_matrix_v1` (the default) or `surface_matrix_v1`,
  and missing fields take that template's defaults; `null` or another value
  is `E_TEMPLATE_UNSUPPORTED`, which is also the only error when
  `generate_design(data, profile=...)` gets the other template's profile.
- **Numbers.** Integral floats are accepted for integer fields (`12.0`).
  Floats are rounded to the 1e-6 mm layout grid and integral results become
  integers, before validation and hashing.  NaN, Infinity, integers beyond
  +/-(2^53 - 1), arrays or objects in leaf fields and other values JSON cannot
  carry are structured errors with the field's own code, never exceptions.
- **Report.** `validation.normalization` records what was done:
  `aliases_applied` (`{alias, field}`), `aliases_shadowed` (`{alias, field,
  by}`), `defaults_applied` (field paths) and `values_normalized` (`{field,
  from, to, reason}`: grid rounding or trimmed whitespace, and on the surface
  template a [field mask](#field-mask-matrixmask) written with floats or as
  the full rectangle).

## Surface template (`surface_matrix_v1`)

CAD mode builds its boards on the surface template: the same sections,
fields and aliases as above with `"template_id": "surface_matrix_v1"`, and
its own locked profile, `profiles/jlc_fpc_surface_v1.json`
(`jlc-fpc-surface-v1`).  That profile keeps every process rule of the
generic one and adds the tight geometry rules the research of 2026-10-20
proved DRC-clean ("V4"), for the smallest margins around the taxel field
(see [LAYOUT_SCHEMA.md](LAYOUT_SCHEMA.md#surface-template-profile-jlc-fpc-surface-v1)):

- **0.5 mm field margin** (`routing.active_edge_clearance_mm`; 0.75 mm on
  the generic template): the 0.2 mm electrode overhang plus JLC's 0.3 mm
  copper to edge.
- **Tight Row channel** (`routing.row_channel` `tight`): lane 1 at the
  copper-to-edge rule from the board edge, the innermost lane at the
  coverlay opening-to-trace rule from the field window, and the field
  starts that same gap above the expansion.  Lanes that need no expansion
  (one row, or a bundle pitch equal to the 0.5 mm contact pitch) run
  straight down into their contacts instead, and the field starts one
  margin above the tail root.
- **Shortest bus angle** (`fanout.bus_angle` `shortest`): the Row expansion
  and the Column convergence each take the whole-degree taper cap from 60
  to 85 degrees that makes them lowest, measured down to where the traces
  widen to the finger width (a tie keeps the smaller angle).
- **Direct Column fan-out** (`fanout.column_convergence` `direct`): one lane
  of up to 64 routes that converge straight into their contact columns,
  with no bundle, no expansion, no slot and no straight stretch above the
  tail.
- **Tails from 7.5 mm** (`tail.minimum_length_mm`; the tail check needs
  7.344 mm at an 85 degree cap).

The fields whose range or default differ from the table above (the
surface template takes them for the straight channel too):

| Field | Kind | Range / values | Default |
| --- | --- | --- | --- |
| `template_id` | string | `surface_matrix_v1` | `surface_matrix_v1` |
| `matrix.columns` | integer | 1-64 | 32 |
| `tail.top_length_mm` | number | 7.5-200 | 12.0 |
| `tail.bottom_length_mm` | number | 7.5-200 | 7.5 |

The tails reach 200 mm since P5-diagonal-bus.md section 23 (80 before).
Every other field keeps its generic range, default and aliases.
`default_design("surface_matrix_v1")` is the generic preset without
`routing.row_sides`, the straight Row channel, and with the 7.5 mm bottom
tail (the generic one's 12 mm since P5-diagonal-bus.md section 27.7, 7.5
mm before), and a request that names only the template gets it.
`input_limits(profile)` and `design_schema(profile)` with
`load_profile("surface_matrix_v1")` give this template's limits and schema;
`GET /api/schema` and `GET /api/default` describe the generic template.
`/api/validate`, `/api/generate`, the exports and `cli.py` take surface
designs as they are: the design's `template_id` picks the profile.

For 16 x 32 taxels at 2 mm with 0.1016 mm traces at 0.1016 mm spacing, the
Column fan-out below the field shrinks from 22.2 mm (two lanes at 60
degrees) to 4.2 mm, the Row channel from 4.8 to 3.9 mm, and every other
margin from 0.75 to 0.5 mm.  `field_footprint` gives these figures for any
design:

```python
from engine import field_footprint, generate_design, load_profile

surface = generate_design({"template_id": "surface_matrix_v1", "matrix": {"rows": 16, "columns": 64}})
assert surface["ok"], surface["validation"]["errors"]
assert surface["manifest"]["template"] == "surface-matrix/1"
margins = field_footprint(surface["design"], load_profile("surface_matrix_v1"))  # {field, row, column}
assert margins["column"]["left"] == margins["column"]["right"] == 0.5
```

Surface builds have their own identity: the build hash also covers the
template version, `template` `surface-matrix/1` (see
[Build identity](#build-identity)).  The generator, exporter, layout format
and DRC versions are the generic template's, and every generic build keeps
its id and its boards byte for byte (`tests/test_generic_identity_guard.py`
freezes 200 generic builds); a later change of the surface geometry bumps
the template version only.

### Field mask (`matrix.mask`)

A surface design may sample only part of its rows x columns grid.
`matrix.mask` gives ROW_01..ROW_R, in order, the `[first, last]` pair of
1-based COL indices of the row's taxels: taxel (r, c) is active when
`first <= c <= last` of row r.  The readout stays the whole matrix (every
ROW and COL net, contact and pin; `channel_order` and the connectors are
unchanged), but each row electrode spans only its active columns and each
column electrode only its active rows, so an inactive position has no
crossing and always reads 0.  The mask is in these net indices, whatever
the pitch, routing, tail sides, role mapping or channel order.  An 8 x 8
triangle whose rows all reach COL_08 is `[[8, 8], [7, 8], [6, 8], [5, 8],
[4, 8], [3, 8], [2, 8], [1, 8]]`.

- Only the surface template takes it; elsewhere it is `E_UNKNOWN_FIELD`
  ("matrix.mask needs template_id 'surface_matrix_v1'").
- Absent or `null` is the full rectangle, and so is `rows` pairs of
  `[1, columns]`: the normalizer leaves that out (`values_normalized`
  says so), so it shares the unmasked build id.  Integral floats become
  integers.  The mask is never a default.
- Every row keeps a taxel, consecutive rows overlap, every column has a
  taxel and each column's taxels are consecutive rows.  Each net then keeps
  one rectangular electrode, and the crossings are exactly the mask's
  taxels (the 0.2 mm electrode overhang is below the 0.25 mm minimum
  electrode gap).
- A masked design adds `mask` to its [build identity](#build-identity).
- The size advice of `E_BOARD_SIZE` never changes `matrix.rows` or
  `matrix.columns` of a masked design; its pitch and tail moves keep the
  mask valid.
- Without `routing.row_sides`, the engine builds the masks of two
  construction classes (phase P2 of `claude/specs/masked-field/PLAN.md`);
  any other mask stops at `E_MASK_ROUTING`, at the field `matrix.mask[i]`
  of the first row it names, with the fix (with `routing.row_sides` the
  [diagonal Row bus](#diagonal-row-bus-routingrow_sides) builds every valid
  mask):
  - **The straight Row channel (A).**  Each row's stub runs straight
    from its lane to its electrode, so a row may stop short of the Row
    channel's side only by the room its lane taper needs: ROW_k starts at
    the Row-frame slot `tau_k` (`row_frame_spans`; slot 0 faces the
    channel, COL_C with both tails on one side, COL_01 with opposite
    tails).  The field slides toward the channel as far as the taper lets:
    `active_x = max(margin, max_k (W_k - lo_k * pitch_x))` with `W_k` from
    `row_taper`, and `tau_k = ceil((W_k - active_x) / pitch_x)`, never
    below 0.  Every mask whose rows all reach the channel side holds, and
    on the surface template's tight channel the lower rows of a tall field
    may stop up to `ceil((rows - 1) x bundle pitch / pitch_x)` columns
    short of it (the soft finger's taper).
  - **The straight Column fan-out (B).**  Each column's stub runs straight
    down its own centre line to the Column tail, so it may pass a row
    without its taxel only on that row's Row-channel side.  A row next to
    the Column tail (ROW_R with both tails on one side, ROW_01 with
    opposite tails) that spans every column always allows it.
  - Right triangles with the right angle at the channel and the Column
    tail, quarter disks, L shapes, trapezoids and tapers are in the
    classes; isosceles and inverted triangles, half disks and disks are
    not yet.
- A masked board keeps every net, contact, lane and pin.  Each electrode
  spans its taxels plus the 0.2 mm overhang; each Row stub ends at its own
  electrode and a raised column's stub rises from today's entry bend on its
  own centre line; the outline follows the crossings with the 0.5 mm
  margin (the Row body's far side, the Column body's top) and the merged
  coverlay window becomes a polygon.  A mask whose rows all reach the Row
  channel and whose row next to the Column tail is full keeps the unmasked
  design's routes, contacts, gang window, stiffener and tail.  The board
  data is in [LAYOUT_SCHEMA.md](LAYOUT_SCHEMA.md#masked-boards).
- `generate_design` checks a masked build with the same 30 DRC records,
  five of them on the masked field: the 0.5 mm margin around the crossing
  region (which must be the electrodes' own), the polygon window's shape,
  bridges and exposure, and a strict window-to-trace rule that exempts a
  route only near its own contact or electrode.  The registration stacks the
  two boards (the top board turned over) and requires the crossings to be
  exactly the mask's taxels, both boards to carry the same mask, every
  electrode on its span of the taxel grid, and the inactive crossings
  apart (`inactive_crossing_separation_mm`, the misregistration a stack
  tolerates before an inactive position reads); any failure is
  `E_REGISTRATION` ([LAYOUT_SCHEMA.md](LAYOUT_SCHEMA.md#records-of-masked-boards)).
  A mask of the classes above generates `ok`.
- The registration also reports, without failing, where a Row trace runs
  on a Column trace in the stack (`trace_overlap_mm`, `trace_overlap_nets`,
  `trace_overlap_pairs`, `trace_overlap_area_mm2`;
  [LAYOUT_SCHEMA.md](LAYOUT_SCHEMA.md#registration-record)).  With both
  tails on one side, a raised column's stub lies on a Row lane from its
  electrode to the tail: both under coverlay with the film between, so no
  contact, but the two nets couple capacitively along the run (the
  soft-finger taper's longest, `ROW_07` on `COL_12`, is 83.8 mm).  Whether
  that matters is a question for the film vendor.
- A masked build exports like any other (`build_exports`,
  `/api/export/*`, `cli.py export`;
  [PHASE2_DIRECT_GERBER.md](PHASE2_DIRECT_GERBER.md#masked-taxel-fields)):
  the polygon field window is one region of the GTS, `ORDER_NOTES.txt`
  states the taxel field ("Taxel field: N of R x C crossings (masked)"),
  and the review bundle adds `taxels.csv` (every R x C position with its
  nets, contact pins and `active`, 0 where the position has no crossing and
  always reads 0) and the review manifest's `taxel_map`.
- CAD mode proposes masked fields (the field follows the selected area;
  the fit option `shape` is fixed at `fill` since P5-diagonal-bus.md
  section 26.16) and maps them (`POST /api/surface/fit` and
  `/api/surface/map`, `cli.py surface`): the taxel map lists only the
  active crossings and adds the `readout` (docs/CAD_MODE.md, "Masked
  fields").  CAD mode has no rectangle shape, no generic template and no
  rectangle preference: a fit naming `shape: rectangle`, `template:
  generic` or a `rectangle_preference_pct` other than 0 is
  `E_SURFACE_REQUEST` (the message names the rectangular mode, which makes
  rectangular fields from rows, columns and the traces' parameters,
  without CAD); a placement saved before that names them maps as fitted
  (the map fits nothing: exactly what a fit then accepted is taken, on the
  generic template not with `shape: fill`, `containment: field` or more
  than 32 `max_columns` named, and anything else is `E_SURFACE_REQUEST`
  with that fit's message; `shape: rectangle` or `template: generic` in
  options without `containment` defaults the map's containment to
  `board`, as such a fit had it).  With the default
  `containment: field` they are built on the diagonal Row bus (below), with
  `containment: board` on the straight channel's construction classes.

| Code | Rule | Source | Field |
| --- | --- | --- | --- |
| `E_MASK_TYPE` | not `null` or an array of `[first, last]` integer pairs | request | `matrix.mask`, or `matrix.mask[i]` for one pair |
| `E_MASK_ROWS` | not one pair per row (`matrix.rows`) | input | `matrix.mask` |
| `E_MASK_RANGE` | not `1 <= first <= last <= matrix.columns` | input | `matrix.mask[i]` |
| `E_MASK_DISCONNECTED` | two consecutive rows share no column | input | `matrix.mask[i]` of the lower one |
| `E_MASK_COLUMN_EMPTY` | a column has no taxel | input | `matrix.mask` |
| `E_MASK_COLUMN_GAP` | a column's taxels are not consecutive rows | input | `matrix.mask` |
| `E_MASK_ROUTING` | the mask is outside the construction classes the engine builds (the straight Row channel and Column fan-out above) | feasibility | `matrix.mask[i]` of the row the message names |
| `W_MASK_INACTIVE_GAP` | the larger electrode gap (pitch less width) less the 0.2 mm overhang is under 0.15 mm, so a misregistered stack may make an inactive position read | input | `matrix.pitch_x_mm` |

At most 20 mask issues are listed, plus one counting the rest.

```python
from engine import check_design

checked = check_design({"template_id": "surface_matrix_v1", "matrix": {"rows": 3, "columns": 5, "mask": [[3, 5], [2, 5], [1, 5]]}})
assert checked["ok"] and checked["identity"]["mask"] == "field-mask/1"
isosceles = check_design({"template_id": "surface_matrix_v1", "matrix": {"rows": 3, "columns": 5, "mask": [[3, 3], [2, 4], [1, 5]]}})
assert [(issue["code"], issue["field"]) for issue in isosceles["validation"]["errors"]] == [("E_MASK_ROUTING", "matrix.mask[0]")]
```

### Diagonal Row bus (`routing.row_sides`)

`routing.row_sides` picks the Row traces on both templates: `both`, `left`
or `right` build the Row board as the diagonal Row bus, the construction
`diagonal-bus/11` ([LAYOUT_SCHEMA.md](LAYOUT_SCHEMA.md#diagonal-row-bus)),
and `channel` the straight Row channel.  The bus is the rectangular mode's
default (the generic template, claude/specs/masked-field/P5-diagonal-bus.md
sections 18-20), and it is one construction with one rule set on both
templates: the rectangular mode builds exactly the boards CAD mode builds
for the same design.  On the bus every row trace leaves its electrode's
end on a slant where the field lets it (the rows of
`construction.row_bus.flat_lane_rows` leave nearly flat), the lanes hug
the field's boundary at the bundle pitch on the sides it names, seen from
outside the stack with the tails down, and below the field every Row trace
turns once into a fan and once into its contact, then runs straight down
the tail.  The lanes keep off the windows of both boards but not off the
Column copper (the boards overlap outside the field), and where the field
narrows toward its bottom edge (a disk's lower half) they follow it inward
down to that edge, nested at the bundle pitch.

| Field | Kind | Values | Default |
| --- | --- | --- | --- |
| `routing.row_sides` | string or null | `left`, `right`, `both`, `channel` | generic: `both` (`channel` for opposite tails or a single row or column); surface: the straight Row channel |

- **Generic template** (`generic_matrix_v1`, the rectangular mode): the
  design always carries the value.  Absent or `null` it is `both`, or
  `channel` where `tail.row_side` and `tail.column_side` are opposite (the
  bus stacks both tails on one side) or the field has a single row or a
  single column (a bus of one lane, or beside one column, is built only on
  request: on the standard profile about 1 in 20 such strips ended in an
  outline corner the DRC refused; with CAD mode's rule set every strip of
  the seeded corpora builds, but the default stays); the default is
  recorded in `validation.normalization.defaults_applied`.  `channel`
  builds the straight Row channel exactly as before section 18, board for
  board and layer for layer, on the generic profile
  (`tests/test_generic_identity_guard.py`); only its build id moved, the
  design naming the channel.
- **One rule set** (section 20).  A bus design is built with the surface
  profile (`jlc-fpc-surface-v1`) on either template:
  `engine.rules_template(design)` names the template whose profile builds
  a design (the surface template for every bus design, the design's own
  for the straight channel), and `generate_design` and `check_design` load
  that profile when none is given.  So the generic bus has a 0.5 mm field
  margin, up to 64 columns and tails from 7.5 mm (the default bottom tail
  12 mm since section 27.7, 7.5 mm before; the straight channel's 7.0 mm),
  `result.profile` and the manifest's profile are the surface profile's,
  and the generic build of a bus design equals the surface-template build
  of the same design but for its identity (the build id and hashes and the
  manifest's `template`; `tests/test_generic_bus.py`).  A profile given
  for the other rule set is `E_TEMPLATE_UNSUPPORTED`.
- **Surface template** (`surface_matrix_v1`, CAD mode): absent, `null` and
  `channel` are the straight Row channel and leave the key out (`channel`
  recorded in `values_normalized`), so those designs keep their build ids.
- Any other value is `E_ROW_SIDES`.
- The bus's fans run at the surface profile's whole-degree caps of 60-85
  degrees from the vertical, never within 5 degrees of the Column V's entry.
- **The Column V** (section 20).  The Column board converges in one V
  straight into its contacts (the surface profile's one lane,
  `column_convergence` `direct`): every Column trace runs straight down
  from its electrode, once on a slant into its contact column and on down
  the tail, no bundle, no slot (`tail.fanout_lane_count` 1).  The V runs at
  most 80 degrees from the vertical (`engine.diagonal.COLUMN_V_CAP_DEG`)
  wherever that roots the tails no deeper than the V at the profile's own
  caps, so the Row fans keep 85 degrees (with `both` and, since the Row
  tail is centred, one-sided too); otherwise (fans the field holds lower)
  it takes the profile's own caps.  On the
  default 12 x 32 design the V runs at 80 degrees and the fans at 85: the
  Row board 67.92 x 41.77 mm and the Column board 67.92 x 37.27 mm, both
  tails rooted 5.87 mm below the field (with the V at 82 degrees the fans
  took 76 and the tails rooted 9.49 mm below it).
- `both` splits the rows alternately: ROW_01, 03, 05, ... on one side (the
  stack's right with the rows on top, its left with the columns on top),
  ROW_02, 04, ... on the other, and the two sides meet in a funnel under the
  field.  `left` or `right` puts every row on that side, its whole bundle
  fanning in under the field.
- **The Row tail is centred on the field** in every side mode, as the
  Column tail (`construction.row_bus.tail_position` `centred`,
  `diagonal-bus/10`, P5-diagonal-bus.md section 27): it lies within the
  sensor's width wherever it is narrower than the field, and is centred
  on it where it is wider.  The rows take its contact positions 1..R
  (built mirrored, its far end from the band), so a reader tail's unused
  contacts lie beyond the rows' (`under_body` with `both` and `under_band`
  one-sided until `diagonal-bus/9`: the funnel's contacts parted midway
  between the innermost lanes, one side's tail lay under the band).
- **The Row pin order folds.**  The Row contacts follow the lanes: with
  `both` ROW_01, 03, 05, ..., 06, 04, 02 from contact position 1, with one
  side ROW_01..ROW_R or, on the side opposite ROW_01's with `both`,
  ROW_R..ROW_01 (`tail.row_contact_order`).  `channel_order` still numbers
  the pins along the contact row (descending: pin 1 is the last contact,
  ROW_02 with `both`).  Take each row's pin from `pinout.csv` or
  `taxels.csv` (CAD mode's taxel map: `readout.row_pin_order`), never as
  pin *k* = ROW_k ([INTEGRATION.md](INTEGRATION.md#the-diagonal-row-bus)).
- Both tails leave on one side (`tail.row_side` equal to
  `tail.column_side`): opposite sides are `E_ROW_BUS_TAILS` (a quarter turn
  is `E_TAIL_SIDE_PARALLEL`, as for every design).  The tails are stacked
  (`construction.row_bus.tails` `stacked`): the Row tail lies on the
  Column tail where they meet, and they part to their own connectors.
- Every valid mask builds (no `E_MASK_ROUTING`), and so does the unmasked
  rectangle.  The Column board has the copper of the straight Column board
  of the same design without `routing.row_sides` (its V capped as above),
  its tail centred under its fan-out and its tail root on the shared
  bottom edge (below), in every side mode: field for field it differs in
  `construction.mask_class` (`{"row": "diagonal", "column": "straight"}`),
  unmasked in carrying the masked records of its full field
  (`grid_registration.taxel_mask`, `active_outline`,
  `active_taxel_count`), and in its outline.
- **One outline down to the tail roots** (section 20).  From the tip down
  to the tails' roots (`construction.row_bus.shared_outline_below_field_mm`
  below the taxel field: the deeper of the two boards' own roots, the Row
  funnel's or the Column V's, lowered below the outline's fillets into the
  tails) both boards have one outline in the stack, the union of their own:
  the field, the Row bands and funnel and the Column fan-out, each board
  gaining blank film where only the other has copper.  The films can be
  aligned by their edges, and both tails leave the shared body's bottom
  edge: the shallower board's contact columns run on straight down to it,
  and each tail keeps its width, position and length below it (CAD mode's
  `tail_extension_mm` measured from it).  Below that level each board is
  its own tail, the tails stacked where they meet.  The copper of both
  boards is the same as with its own outline at that level.
- **Regular outlines.**  No vertex of either outline turns by less than
  5 degrees but on a fillet or the tail: a run of flatter turns between two
  corners is one straight edge on or outside it (the outline only grows, so
  every clearance to it does), a long smooth curve a polygon of corners of
  5 degrees or more ([LAYOUT_SCHEMA.md](LAYOUT_SCHEMA.md#diagonal-row-bus)).
- **Chamfered notches** (`diagonal-bus/6`).  Where a masked field misses
  cells at a corner, both boards cross the notch on the convex hull of F
  (a chamfer, or a polygon following F), not on its staircase, where the
  staircase lies no deeper inside the hull's edge than a two-cell step; a
  deeper pocket (a narrow tip over a much wider row) keeps its staircase.
  The chamfer lies on or outside F, so every clearance to the outline only
  grows; a full field's outline is `diagonal-bus/5`'s.
- **Straight sides** (`diagonal-bus/7`).  On each side of the outline over
  the field the stretch from the tip corner down to the side's widest point
  is one straight line wherever one line encloses it within 1.0 mm (the
  tip corner moving out along the top edge to meet it, at most 1.0 mm),
  and the stretch from there down to the tails' roots likewise; a curved side
  keeps its polyline.  The old outline lies inside the new one, so every
  clearance only grows; the widest point and the copper stay
  ([LAYOUT_SCHEMA.md](LAYOUT_SCHEMA.md#diagonal-row-bus)).
- **Convex flank** (`diagonal-bus/11`, P5-diagonal-bus.md section 27.8).
  With one side, the side without lanes runs convex from the field's
  outline corner down to the tail: the Column board's fan-out notch just
  below the field is bridged by the side's hull where every corner stays 5
  degrees or more; the tails' roots and the copper stay, the outline only
  grows (a clearance to it by the grid at most: P5-diagonal-bus.md section
  27.9) ([LAYOUT_SCHEMA.md](LAYOUT_SCHEMA.md#diagonal-row-bus)).
- The design adds `row_bus` (`diagonal-bus/11`) to its
  [build identity](#build-identity).
- `generate_design` checks the pair with the 30 DRC records in their masked
  form and the registration's stack keys: no trace over the other board's
  electrodes or its field window, both tails on one side, and one outline
  down to the tails' roots (`outlines_coincide_over_field`; each failure an
  `E_REGISTRATION`;
  [LAYOUT_SCHEMA.md](LAYOUT_SCHEMA.md#registration-record)).  Outside the
  taxel field the boards may overlap, the stacked tails too: Row-Column
  crossings, runs and the tails' overlap are reported, not checked (the
  fans keep 5 degrees from the Column fan-out's diagonals; the stacked
  tails' contact columns may lie on each other, `trace_overlap_mm`, and
  `tail_overlap_width_mm` says how much of their width).
- Its exports carry the folded order (`pinout.csv`, `netlist.ipc`,
  `taxels.csv`), and the review manifest records `construction.row_bus`
  and the contact order
  ([PHASE2_DIRECT_GERBER.md](PHASE2_DIRECT_GERBER.md#diagonal-row-bus)).
- CAD mode proposes it with the fit option `containment: field`, the
  default, which keeps only the taxel field on the surface, the convex
  corners of the field within a 0.5 mm tolerance (P5-diagonal-bus.md
  sections 16 and 24; its margin there may leave the surface by that much,
  the taxels never; the map's `field_corner_overhang`); it covers the
  selection first, its masked fields within the rectangles' caps
  (`max_rows` x `max_columns`, 64 x 64; 32 x 32 before P5-diagonal-bus.md
  section 21), a full rectangle ranking as any field (the rectangle
  preference that could put one first is gone with section 26.16); with
  `tip_first` (on by default, section 26) the field reaching nearest the
  fingertip within 3 % of the most taxels on its exit (a symmetric field's:
  of the symmetric fields there, section 26.17) goes first, the field it
  displaces giving its place to its own tie of as many taxels or more; on a
  face symmetric about an exit (its outline and holes mirrored about the
  line through the exit's middle within 0.05 mm) it proposes a field whose
  every row is its own mirror image first unless a field that breaks the
  symmetry (an asymmetric or a turned one) holds at least 20 % more (at
  exactly 20 % that field leads; decided on the search's fields before the
  tip step; the user's decision of 2026-10-27, P5-diagonal-bus.md section
  26.19: section 22's 3 % was gone with section 26.17), and turns no frame
  of an exit whose symmetric field holds within 20 % of its best unturned
  field (the proposal's `metrics.symmetry`); the option `row_sides`
  (the browser's Row traces select) is written into every proposal as
  `routing.row_sides`, and the browser's form carries it (its Row traces
  select, sent on both templates, Straight channel as `channel`) so that
  Generate builds the proposal's build id
  ([CAD_MODE.md](CAD_MODE.md#field-only-containment-containment-field)).
- `field_footprint` and `E_BOARD_SIZE` measure it on its built boards
  (phase P5d; the straight channel's plans differ: the bus's bands and its
  Row root).  The size advice is modelled on the straight plans
  plus the bus's measured excess and kept only where the bus's boards then
  fit.

| Code | Rule | Source | Field |
| --- | --- | --- | --- |
| `E_ROW_SIDES` | not `left`, `right`, `both`, `channel` or `null` | input | `routing.row_sides` |
| `E_ROW_BUS_TAILS` | `left`, `right` or `both` with `tail.row_side` and `tail.column_side` opposite (`channel` takes them) | input | `routing.row_sides` |
| `E_ROW_BUS_INFEASIBLE` | the bus cannot order or place its lanes; no boards are built (reserved: no design measured so far raises it) | build | `routing.row_sides` |
| `E_REGISTRATION` | a stack rule above fails | drc | `boards.<row or column>.<part>` |
| `W_STACK_TRACE_WINDOW` | a stacked trace passes closer than 0.15 mm to the other board's field window (fine pitches) | drc | `boards.row.layers.top_copper.routes` or `boards.column.layers.top_copper.routes` |

```python
from engine import check_design, generate_design

bus = generate_design({"template_id": "surface_matrix_v1", "matrix": {"rows": 5, "columns": 4}, "routing": {"row_sides": "both"}})
assert bus["ok"] and bus["manifest"]["row_bus"] == "diagonal-bus/11"
assert bus["boards"]["row"]["verification"]["registration"]["outlines_coincide_over_field"]
assert bus["boards"]["row"]["tail"]["row_contact_order"] == ["ROW_01", "ROW_03", "ROW_05", "ROW_04", "ROW_02"]
generic = check_design({})  # the rectangular mode's default: the bus with both
assert generic["design"]["routing"]["row_sides"] == "both" and generic["identity"]["row_bus"] == "diagonal-bus/11"
channel = check_design({"routing": {"row_sides": "channel"}})  # the straight Row channel
assert channel["ok"] and "row_bus" not in channel["identity"]
```

## JSON Schema

`GET /api/schema` and `python3 cli.py schema` return a JSON Schema (draft
2020-12) of the request, generated from the profile limits:
`additionalProperties: false` at every level, the deprecated aliases listed
with `deprecated: true`, and the annotations `x-profile` (id, revision,
sha256), `x-alias-precedence`, `x-cross-field-rules`, `x-error-codes`,
`x-warning-codes`, plus `x-http-error-codes` (HTTP) or `x-cli-error-codes`
(CLI).  The surface template's schema
(`design_schema(load_profile("surface_matrix_v1"))`) also has
`matrix.mask` (an array of 1-64 pairs of integers 1-64, or `null`) and its
cross-field rule; both templates' schemas have `routing.row_sides`
(`left`, `right`, `both`, `channel` or `null`; default `both` on the
generic template, `null` on the surface one) and its rule; the issue catalogue is the same for both templates and
lists the mask and Row bus codes, because the same endpoints serve both templates
(`template_id` selects one) and `GET /api/schema` is the only schema the
server returns.

The contract: a request that validates against the schema passes every
single-field rule of the engine; the cross-field rules are checked by the
engine only.  The engine is more lenient than the schema in exactly four
documented ways:

1. it rounds numbers to the 1e-6 mm grid before the range checks, so a value
   within half a grid step outside a bound is accepted;
2. it trims `project_name` before checking its length and characters;
3. it ignores (with `W_ALIAS_SHADOWED`) an alias that a nested field or a
   higher-precedence alias overrides, while the schema checks every alias
   value (the values of `connector_side`, `row_fpc_position` and `scan_order`
   are always checked);
4. on the generic template it takes the diagonal Row bus's tails up to the
   surface profile's maximum, 200 mm (P5-diagonal-bus.md section 23), while
   the schema and the browser's form keep the generic profile's 80 mm.

## Build identity

All digests are SHA-256 of canonical JSON
(`json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)`
as UTF-8):

- `design_sha256`: the canonical design (`result.design`);
- `profile_sha256`: the full profile;
- `build_sha256`: `{design_sha256, profile_sha256, generator, exporter}`, with
  `generator` = `deterministic-sensor-core/0.4.0` and `exporter` =
  `direct-gerber-pure-stdlib/0.3.0`;
- `build_id` = slug + `-` + the first 12 hex digits of `build_sha256`.

A design on the surface template (`surface_matrix_v1`) adds `template`, its
version (`surface-matrix/1`), to the hashed object: `{design_sha256,
profile_sha256, generator, exporter, template}`.  Generic designs have no
`template` key, so their ids are those of the generic template before the
surface template existed.  A masked design ([field mask](#field-mask-matrixmask))
also adds `mask` (`field-mask/1`): `{design_sha256, profile_sha256,
generator, exporter, template, mask}`.  Designs without a mask (the full
rectangle is normalized away) have no `mask` key, so their ids did not
move; `field-mask/1` changes only for a fix of geometry that masked designs
already build.  A design built as the diagonal Row bus (`routing.row_sides`
`left`, `right` or `both`; [diagonal Row bus](#diagonal-row-bus-routingrow_sides)) adds `row_bus`
(`diagonal-bus/11`): `{design_sha256, profile_sha256, generator, exporter,
template, row_bus}` (no `template` on the generic template), and `mask` too
when it is masked; its `profile_sha256` is the surface profile's on either
template (the profile that builds it, section 20).  A surface design without it (absent, `null` and
`channel` are normalized away) has no `row_bus` key, so the surface's
straight Row channel ids did not move; the generic template's ids moved
once with section 18 (its designs name `routing.row_sides`, `channel` for
the straight Row channel, without `row_bus`); a change of any constant of the
construction bumps it (`diagonal-bus/1`, the first construction with a
corridor under the field, and `diagonal-bus/2`, its tails side by side,
were never released).  The exports of a surface build repeat
`template`, `mask` and `row_bus` beside the identity fields (the review
bundle's `manifest.json` and each board ZIP's), and the bundle's
`identity.build_sha256` recipe names them, so the hash can be recomputed
from the bundle's own `design.json` and `profile.json`.

The slug is the lower-cased project name with every run of characters other
than ASCII letters and digits replaced by `-`, trimmed and cut to 48
characters.  A name without ASCII letters or digits (for example an all-Chinese
name) gets `tactile-fpc-` plus 8 hex digits of the SHA-256 of the trimmed
name.  Any change of the design, of profile content or of either version
gives a new build id; equivalent requests (`2` vs `2.0`, flat vs nested)
share one.  The default build is `tactile-fpc-12x32-c2243ebd10c5` (the
diagonal Row bus with `both`, `diagonal-bus/11`, both tails 12 mm since
P5-diagonal-bus.md section 27.7, the profile revision 2026-10-29), for the browser's default form and for
`default_design()` alike.

**Compatibility.**  The necked routing of 2026-10-15 (generator 0.4.0,
exporter 0.3.0, profile revision 2026-10-15, layout v3) changed every build
id: the same design gives other boards and another id than before.  A design
without `routing` takes the default fan-out traces.

The core manifest (`tactile-fpc-manifest/v2`) carries `format`, `generator`,
`exporter`, `layout_format`, `deterministic`, the identity fields, `slug`,
`profile` (`id`, `revision`), `template` (surface designs only), `mask`
(masked designs only), `row_bus` (diagonal Row bus designs only),
`geometry_valid`, `production_ready: false`,
`output_status: "geometry_only"`, `requires_final_jlc_review: true`,
`board_summary` (id, role, physical side and metrics per board) and `checks`
(`error_count`, `warning_count` of design warnings only, `single_copper_fpc`,
`polyimide_stiffener_thickness_mm`, `source_independent`).

## HTTP server

```bash
python3 app.py                         # http://127.0.0.1:8008
python3 app.py --port 8009 --host ::1  # another port or loopback address
python3 app.py --allow-host abc-8008.usw2.devtunnels.ms  # also serve a tunnel, proxy or LAN name
```

A non-loopback `--host` prints a warning: the API has no authentication.  A
port that is already taken is reported in one line (exit status 1), usually
because the customizer is already running there; a port outside 0-65535 or a
malformed `--allow-host` name ends with exit status 2 before anything binds.

**Remote use.**  On a remote machine (for example over VS Code Remote-SSH)
forward the port and open `http://localhost:8008` on your own machine: a
forwarded loopback name passes the Host check, VS Code's port preview
included.  A tunnel, a proxy or a LAN name in the browser's address bar is
answered 421 (the Host check guards against DNS rebinding) until it is
allowed with `--allow-host NAME` (repeatable; `.example.com` allows the domain
and its subdomains, an IP address is given without port).  Pages served
under an allowed name may post with that origin, over `https://` too, even
when a proxy rewrites the Host header.  Every name under an allowed domain
passes the Host and Origin checks, so allow a domain only if you control the
DNS of its subdomains; an exact tunnel name is the safer choice.  A bare
top-level domain (`.com`, `.local`) is refused, and so are scoped IPv6
addresses (`%eth0`), which browsers never send, IPv4-mapped ones
(`::ffff:192.168.1.5`: give the IPv4 address, which also matches the
`[::ffff:c0a8:105]` a browser sends for the mapped form) and IPv4 addresses
not written as four decimal numbers (`127.1`, `192.168.001.005`), which
browsers rewrite before they send them.

| Method and path | Request | Reply |
| --- | --- | --- |
| `GET /`, `GET /index.html`, `GET /static/<file>` | | the browser UI from `web/` (paths are contained; anything else is 404) |
| `GET /api/default` | | `{design, profile}`; `profile` has `id`, `revision`, `name`, `display_rules` (rule text generated from the profile; `Bundle traces` gives the default design's fan-out width and spacing, the other entries the gold-finger width, JLCPCB's trace minimum for the profile's copper and the other locked rules), `limits` (per-field form limits; on the generic template the diagonal Row bus's, with the straight channel's own under each field's `channel`), `issue_codes` and `order_requirements` (the JLCPCB order options and review notes of `ORDER_NOTES.txt`, from `engine.profile.order_requirements`); on the generic template also `row_bus`, the bus's rule set (`id`, `revision`, `name`, `display_rules` of the surface profile, which builds it) |
| `GET /api/schema` | | the JSON Schema plus `x-http-error-codes` and `x-surface-error-codes` |
| `POST /api/validate` | design | 200 with the `check_design` result (`ok` true or false) |
| `POST /api/generate` | design | 200 with the result without `derived_layout`, `ok` true or false |
| `POST /api/generate?view=compact` | design | 200 with `{ok, design, validation, manifest, boards}`, each board reduced to `id, role, physical_side, units, tail, grid_registration, metrics, verification` |
| `POST /api/export/top-gerber`, `/bottom-gerber`, `/project` | design (usually `result.design`) | 200 `application/zip`, `Content-Disposition: attachment; filename="<artifact name>"`, `X-Build-Id`, `X-Design-Sha256`; 422 when blocked |
| `POST /api/export/easyeda-pro` | design | the same reply with `{build_id}-easyeda-pro.zip`: the [EasyEDA Pro projects](EASYEDA_EXPORT.md) of both boards |
| `POST /api/surface/inspect`, `/select`, `/fit`, `/map` | CAD mode: a framed body (`application/x-tactile-surface`: 4-byte big-endian header length, JSON header, STL bytes) | 200 JSON; 422 with an `E_SURFACE_*` code (see [CAD_MODE.md](CAD_MODE.md#http)) |

`HEAD` works on the GET routes; other methods on a known route get 405 with
`Allow`.  The query parameters are `view=full|compact` on `/api/generate`
and `template=generic_matrix_v1|surface_matrix_v1` on `/api/default` (that
template's default design and profile, whose `name` starts with "Generic
Matrix v1" or "Surface Matrix v1"; without it the generic one, as before);
anything else is 400.  For the default design the full
view is about 89 kB and the compact view about 20 kB.

Every failure is JSON: `{"ok": false, "code": "...", "error": "message"}`,
plus `field`, `validation` and `manifest` where they apply (a blocked export
carries the validation).  Nothing is answered with an empty reply.

The answers need no HTTP: `app.answer(method, target, content_type, body,
cache=None)` returns the reply of one `/api/` request as an `app.Reply`
(`status`, `content_type`, `body`, `headers`), with the server's routes,
query, media-type, body and size rules.  What only a connection has is left
out: the Host and Origin checks, Content-Length, the time limits and the busy
slots (503).  The static site (README, "As a static website") calls it in the
browser through `web/py/bridge.py`; the server answers with the same
functions, so both give the same bytes.

### The border of CAD mode's taxels

The surface routes take the border the user draws in CAD mode
([CAD_BORDER.md](CAD_BORDER.md), `surface/border.py`):

- `/api/surface/select` replies `selection.facets_uv`: per selected facet
  (aligned with `selection.facets`) its three corners' uv in the chart, in
  the mesh's vertex order, so a client maps uv to the part and back.
- `/api/surface/fit` takes `border: {"uv": [[u, v], ...]}` in that chart
  (a simple polygon of at least 3 and at most 2048 vertices and 1 mm²,
  overlapping the surface).  The taxels then lie inside it; the routing is
  free (`containment: field`, the default; `containment: board` is
  refused).  The
  base is `"auto"` (the border's edges of at least 3 mm with surface
  beyond them, longest first, at most 6) or `{"border_edge": i}` (edge i
  from vertex i to i + 1); the other bases (`{"side"}`, `{"point_xyz"}`,
  `{"arc"}`) are refused with a border, `{"border_edge"}` without one.
- The reply echoes the border in `request.border` and in each proposal's
  `placement.border` (`placement.base_kind` `"border"`, `base_side` the
  edge) and adds `metrics.border_area_mm2` and
  `metrics.border_on_surface_share` (the share of the border's area on the
  surface).
- `/api/surface/map` checks the placement's border: the required
  verification record `taxels_inside_border` counts the taxel squares
  (the crossings of the stacked Row and Column electrodes) outside it.
- Problems with the border are `E_SURFACE_BORDER` (422): an invalid border
  or exit edge, a base that is not an edge of it, or the containment it
  cannot take.

### HTTP error codes

| Code | Status and meaning |
| --- | --- |
| `E_HTTP_BAD_REQUEST` | 400: malformed request line, header or query parameter; a missing (HTTP/1.1), duplicate or malformed Host |
| `E_HTTP_INVALID_JSON` | 400: the body is not strict UTF-8 JSON (NaN/Infinity, duplicate keys, too deep, number too long) |
| `E_HTTP_BODY_NOT_OBJECT` | 400: the body is empty or not a JSON object |
| `E_HTTP_CONTENT_LENGTH` | 400: malformed, duplicate or short Content-Length |
| `E_HTTP_FORBIDDEN_ORIGIN` | 403: a POST from another origin (not `http://` or `https://` of its Host, nor an `--allow-host` name) |
| `E_HTTP_NOT_FOUND` | 404: unknown route or static file |
| `E_HTTP_METHOD_NOT_ALLOWED` | 405: the route exists for other methods (see `Allow`) |
| `E_HTTP_TIMEOUT` | 408: the request stalled for 30 s or was not complete within 60 s |
| `E_HTTP_LENGTH_REQUIRED` | 411: a POST body without Content-Length (chunked uploads are not supported) |
| `E_HTTP_BODY_TOO_LARGE` | 413: the body exceeds 131072 bytes (128 KiB), or 67108864 bytes (64 MiB) on the surface routes |
| `E_HTTP_URI_TOO_LONG` | 414: request line too long |
| `E_HTTP_UNSUPPORTED_MEDIA_TYPE` | 415: a POST whose Content-Type is not `application/json` (UTF-8), or not `application/x-tactile-surface` on the surface routes |
| `E_HTTP_MISDIRECTED_HOST` | 421: Host is not a loopback name, the configured `--host` or an `--allow-host` name; the message names the Host |
| `E_EXPORT_BLOCKED` | 422: the design does not validate; the reply carries `validation` and `manifest` |
| `E_EXPORT_FAILED` | 422: the exporter rejected the generated geometry |
| `E_SURFACE` | 422: a surface route rejected the mesh, the selection or the fit; the reply's `code` is one of `x-surface-error-codes` (`E_SURFACE_*`) |
| `E_HTTP_HEADERS_TOO_LARGE` | 431: too many or too long header lines |
| `E_INTERNAL` | 500: unexpected server error (details are in the server log) |
| `E_PROFILE_INVALID` | 500: the bundled manufacturing profile is inconsistent |
| `E_HTTP_NOT_IMPLEMENTED` | 501: unsupported method |
| `E_HTTP_BUSY` | 503: 2 generations (or 1 surface request) are running; retry after `Retry-After` seconds |
| `E_HTTP_VERSION_NOT_SUPPORTED` | 505: unsupported HTTP version |

### Request rules and limits

- **Host.** HTTP/1.1 requests need exactly one well-formed `Host`; it must be
  `localhost`, `127.0.0.1`, `[::1]`, the configured `--host` or an
  `--allow-host` name (the port is ignored; an IP address matches in any
  notation: `[2001:db8:0:0::5]` is `[2001:db8::5]`, `[::ffff:c0a8:105]` is
  `192.168.1.5`), else 421.  An absolute-form
  target (`http://host/path`) is checked by its own authority.
- **POST.** `Content-Type: application/json` (charset UTF-8 or none) else 415;
  an `Origin` header, when present, must equal `http://<Host>` or
  `https://<Host>` (a TLS proxy or tunnel in front of the app), or name an
  `--allow-host` host, else 403;
  `Content-Length` is required (411; chunked bodies are not supported) and at
  most 128 KiB (413); the body must be one strict JSON object (400).
  The CAD-mode routes `/api/surface/*` take `application/x-tactile-surface`
  instead (415 otherwise), up to 64 MiB, and answer their own problems with
  422 and an `E_SURFACE_*` code.
- **Time.** 30 s socket timeout per read and 60 s for the whole request,
  however slowly it trickles in (408).  After a reply that leaves request
  bytes unread, the server drains them for at most 2 s or 1 MiB before
  closing, so the reply is not lost to a TCP reset (a surface body over its
  limit by up to another 64 MiB is drained whole, for at most 10 s).  Idle connections that
  send nothing are closed after 30 s without a reply.
- **Load.** Listen backlog 64; at most 2 generations or exports run at once,
  others get 503 `E_HTTP_BUSY` with `Retry-After: 1` (`/api/validate` does
  not count).  CAD-mode (surface) requests run one at a time in a slot of
  their own, so they never hold up the rectangular mode; a second one gets
  the same 503.  The surface routes keep the last four parsed meshes (at most
  1.5 million facets in all, two of a mesh's per-edge bend measurements
  counting as one facet) and the last eight charts in memory, by
  SHA-256; nothing is written to disk.  A build cache of 16 builds, keyed by `build_sha256`, lets
  exports reuse the generation of the same build.
- **Headers on every reply.** `X-Content-Type-Options: nosniff`,
  `Content-Security-Policy: default-src 'self'; img-src 'self' data:;
  style-src 'self' 'unsafe-inline'; base-uri 'none'; form-action 'self'`,
  `Referrer-Policy: no-referrer`, `Cache-Control: no-store`, and the generic
  `Server: TactileFPC`.  The UI's own files are always served as
  `text/html`, `text/javascript` and `text/css` (UTF-8), whatever the host's
  MIME registry says: under `nosniff` a browser refuses a script typed
  `text/plain`, which a Windows registry can map `.js` to.  The page may be
  framed (since 2026-10-14; it was `frame-ancestors 'none'`): VS Code's port
  preview shows it in a frame, and the app keeps no state or credentials a
  framing page could misuse.
- **Logging.** Log lines escape control characters; tracebacks of 500s go to
  standard error, never to the client.

## CLI

```bash
python3 cli.py schema                                   # JSON Schema plus x-cli-error-codes
python3 cli.py validate design.json [more.json ...]     # check_design, no geometry
python3 cli.py generate design.json [--compact]          # full view (no derived_layout) or compact view
python3 cli.py export design.json --out outputs/         # three ZIPs named by artifact_filenames
cat design.json | python3 cli.py generate -             # '-' reads standard input once
python3 cli.py surface inspect part.stl                 # CAD mode: mesh facts and candidate surfaces
python3 cli.py surface fit part.stl --pick X,Y,Z --out outputs/   # fit, then write the best proposal's files
```

A design file holds one JSON object in the same strict format as the HTTP
body: `null`, arrays and other non-objects are rejected, never read as "use
the defaults".  One input prints its result; several inputs are a batch
printed as `{"ok": ..., "results": [{"input": <name>, ...}]}`.  `--pretty`
(before or after the command) indents the output.  A reply too deeply nested to
indent is printed compact, and a reply that cannot be written as JSON at
all is exit 3 `E_CLI_INTERNAL`: the output is always one JSON document
(`map` refuses a placement nested more than 32 levels deep, so its echo of
the placement never gets that deep).  `export` creates the
directory and prints `{ok, build_id, manifest, files}` with absolute paths.

Exit status: **0** when every design is valid (and exported), **1** when a
design does not validate or cannot be exported, **2** for unreadable input or
unwritable output; a batch exits with the largest status of its entries.
`surface` (CAD mode, see [CAD_MODE.md](CAD_MODE.md#command-line)) exits 1 with
an `E_SURFACE_*` code when it rejects the mesh, the selection or the fit, and
3 with `E_CLI_INTERNAL` on an unexpected error (a bug), still as one JSON
document.

### CLI error codes

| Code | Exit status and meaning |
| --- | --- |
| `E_CLI_INPUT` | 2: the design file cannot be read |
| `E_CLI_INVALID_JSON` | 2: the file is not strict UTF-8 JSON (NaN/Infinity, duplicate keys, too deep, number too long) |
| `E_CLI_NOT_OBJECT` | 2: the document is not one JSON object (null, an array, a string or a number) |
| `E_CLI_OUTPUT` | 2: the export directory or an archive cannot be written |
| `E_EXPORT_BLOCKED` | 1: the design does not validate; the entry carries `validation` |
| `E_EXPORT_FAILED` | 1: the exporter rejected the generated geometry |
| `E_SURFACE` | 1: CAD mode rejected the mesh, the selection or the fit; the code is one of `x-surface-error-codes` |
| `E_CLI_INTERNAL` | 3: an unexpected error in a CAD-mode command (a bug; the message names the exception) |

## SVG previews

Each board's `svg` is a standalone, ASCII-only SVG of the **copper-side top
view in the Gerber frame**:

- all geometry sits in one `<g transform="matrix(1 0 0 -1 0 T)">` with `T`
  the sum of the outline's minimum and maximum Y, so Y points up on screen,
  as in a Gerber viewer; one user unit is one millimetre;
- the root carries `viewBox` (the outline plus 1 mm, and a label band above),
  `role="img"`, an `aria-label`, `data-view="top"` and
  `data-active-region="x y width height"`: the taxel field in SVG user units
  after the flip, which the browser uses to register the two boards; a
  [masked](#field-mask-matrixmask) board adds `data-active-outline="x,y
  ..."`, its crossing region (`grid_registration.active_outline`) in the
  same flipped units, and draws its polygon field window as a
  `polygon.opening`;
- a `polygon.pin1-marker` triangle sits beyond the tail tip in line with the
  pin-1 contact, with `<title>pin 1 (NET)</title>`; the `text.view-label`
  reads "TOP VIEW · copper side · ▲ pin 1" and shrinks to fit narrow boards;
- the other classes are `outline`, `cutout`, `stiffener`, `opening`,
  `electrode`, `pad` and `route`; there are no `width`/`height` attributes;
- each `polyline.route` carries its own `stroke-width`, the `width_mm` of its
  route piece (thin fan-out pieces, wide tail pieces); the style sheet sets
  no route width (until 2026-10-15 every route was drawn 0.254 mm wide).

The review bundle's `previews/top_fpc.svg` and `previews/bottom_fpc.svg` are
the same bytes.

## Known limits

- With `--host 0.0.0.0` the `Host` header must still be a loopback name, the
  literal bind address or an `--allow-host` name; LAN use needs `--host <LAN
  address>` or `--allow-host <LAN name>`.
- More than about 64 simultaneous connection attempts can overflow the kernel
  listen queue.
- A client that keeps sending for more than 2 s or 1 MiB after a rejected
  request can still see a reset.
- Integers beyond 2^53 are type errors (`E_NUMERIC`, `E_ROWS_INTEGER`, ...),
  while finite floats such as 1e30 get range errors.
- Review bundles of equivalent requests can differ in `validation.json`
  (request warnings and the normalization report are copied as given) while
  the build id and both Gerber ZIPs are identical.
- No authentication, no persisted build history, one process.
