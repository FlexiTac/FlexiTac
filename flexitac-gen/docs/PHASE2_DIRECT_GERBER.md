# Direct Gerber review-candidate exporter

`exporters/direct_gerber.py` (`EXPORTER_VERSION =
"direct-gerber-pure-stdlib/0.3.0"`) turns one `engine.generate_design()`
result into two independent Gerber ZIPs, one per FPC, and a project review
bundle.  It is a fast, local, deterministic adapter written with the Python
standard library only; it never opens an EasyEDA project, a KiCad board, an
earlier Gerber or any network service.  Its output is a **Direct Gerber /
JLC review candidate**: not an EasyEDA-native export and not a production
approval.

## API

```python
from engine import BuildCache, generate_design
from exporters import EXPORTER_VERSION, ExportError, artifact_filenames, build_exports

cache = BuildCache()
result = generate_design(design, cache=cache)
zips = build_exports(result, cache=cache)  # top_fpc_gerber_zip, bottom_fpc_gerber_zip, project_review_bundle_zip
names = artifact_filenames(result)         # the same keys -> download names
```

- `build_exports(result, *, cache=None)` returns the three archives as bytes
  and raises `ExportError` (never another exception type) for anything it
  refuses or cannot write.  The cache is optional: passing the engine's
  `BuildCache` lets the regeneration below reuse the build, as the HTTP
  server and the CLI do.
- `artifact_filenames(result)` gives `{build_id}-top-<role>-direct-gerber.zip`,
  `{build_id}-bottom-<role>-direct-gerber.zip` and
  `{build_id}-project-review.zip`.  The HTTP `Content-Disposition`, the CLI
  file names and the review manifest all use these names.  A name identifies
  the build, not the bundle bytes (see `validation.json` below).

## What the exporter checks

Before writing anything:

1. **Gates.** `result.ok` must be true, `manifest.geometry_valid` true and
   `validation.errors` empty; the result's profile must pass the profile
   consistency check.  A masked taxel field (`matrix.mask`) exports like
   any other build ([below](#masked-taxel-fields)), and so does a diagonal
   Row bus (`routing.row_sides`, [below](#diagonal-row-bus)).
2. **Identity.** The manifest must describe this design and profile:
   `design_sha256`, `profile_sha256`, `generator` (the running engine's),
   `exporter` (this exporter's), `layout_format`, `build_sha256`, slug and
   `build_id`, and `checks` that match the validation.
3. **Form.** Both boards are well-formed: finite numbers, coordinates within
   the +/-10000 mm of `FSLAX46Y46`, anchored rectangles that do not collapse
   at 1e-6 mm, simple rings (outline, cutouts, stiffeners), route pieces
   (`segment` `tail` or `fanout`) at least as wide as JLC's minimum for the
   profile's copper (0.1016 mm for the ordered 1 oz), board ids `[a-z0-9_]`, pins
   1..P each used once, nets `ROW_<n>`, `COL_<n>` or `NC_<pin>`, and supported
   stiffeners (bottom side, polyimide, a JLC PI thickness).  A coverlay
   opening with a `shape` must be `polygon`, the merged
   `electrode_field_opening` of a board with a taxel mask
   (`grid_registration.taxel_mask`), without the rectangle fields (`anchor`,
   `x`, `y`, `width_mm`, `height_mm`), and its `points` a simple,
   counter-clockwise, rectilinear ring of at least four vertices on the
   1e-6 mm grid, given open.
4. **Regeneration binding.** The engine regenerates the boards from the
   result's canonical design and profile (`generate_design(design,
   profile=..., cache=...)`, whole-board DRC included).  The result must be
   exactly the engine's output: the design canonical, the manifest equal, the
   design warnings equal, and both boards equal, geometry, DRC records, SVG
   previews, metrics and construction included.  A refusal names the JSON
   path of the first difference.  The regenerated boards are what is written,
   so the files are bound to the build identity they carry.  A result from
   another generator or exporter version must be regenerated.

After writing:

5. **Read-back.** A strict decoder of the exporter's RS-274X subset reads
   every Gerber again and compares it with the layout within 2e-6 mm: X2
   attributes and polarity, route strokes and apertures, every region (a
   polygon field window against its ring, vertex by vertex), outline and
   cutout contours, stiffener regions and the coordinate range.
   `jlcpcb.json` (mils back to millimetres), `netlist.ipc` (to its 0.001 mm
   resolution) and each board manifest's member digests are checked too.
   `ORDER_NOTES.txt` must state, in order, the build, the board, its archive
   and stiffener layers (and a diagonal Row bus's Row board its folded pins),
   every order requirement with its reason, the upload
   checks and the cited sources, and the contact figures it states (contact
   width, contact start from the tip, the contact window beyond the outer
   contacts, the width of the tail traces) must hold for the board, and each
   board's lines must state the trace widths of the build's design and what
   JLC's width tolerance makes of its fan-out traces; each manifest's
   `order_requirements` must be the profile's.  A masked build's notes must
   state its taxel field, and its `taxels.csv` is read back against both
   boards (below); a diagonal Row bus's `pinout.csv` is read back against
   its folded Row contact order.
6. **Archives.** Every ZIP is re-opened: member list, stored compression,
   timestamps and bytes must be as written.

## Board ZIP

| Member | Content |
| --- | --- |
| `Gerber_TopLayer.GTL` | `Copper,L1,Top`, positive: route pieces as round strokes with one aperture per width (by default `C0.127` for the fan-out pieces and `C0.254` for the tail pieces), electrodes and contacts as G36/G37 regions |
| `Gerber_TopSolderMaskLayer.GTS` | `Soldermask,Top`, declared **negative**: its regions are the coverlay openings (clearances), as EasyEDA and KiCad write them; a masked board's polygon field window is one region over its ring |
| `Gerber_BoardOutlineLayer.GKO` | `Profile,NP`: the closed outline and every routed slot, drawn with a 0.1 mm line |
| `Gerber_BottomStiffenerLayer_pib_<t>.GBSL` | `Other,BottomStiffener`: one layer per side, material and thickness, EasyEDA-style name (default `pib_0.225`) |
| `jlcpcb.json` | `fpcStiffeners`: per stiffener `id` (`direct_pi_01`...), `gerber`, `layer` (`bottom`), `material` (`pi`), `thickness` (`"0.225"`) and `path`, one closed contour in mils in the Gerber frame, nested as `[[[x0, y0, "L", x1, y1, ..., x0, y0]]]` (the first point repeated at the end) |
| `netlist.ipc` | IPC-D-356A netlist (below) |
| `ORDER_NOTES.txt` | how to order this board from JLCPCB (below): the board (with its trace widths and what JLC's width tolerance makes of them), its archive and stiffener layers, its coverlay windows (those longer than JLC's general 20 mm for one opening named), the order options and review notes with their reasons, the upload checks and the sources; UTF-8 text with LF line ends, like the ordering note EasyEDA puts in its exports |
| `manifest.json` | `tactile-fpc-board-manifest/v1`: identity fields, `board_id`, `physical_side`, `role`, status flags, member digests, stiffener groups, netlist summary, geometry counts, `order_notes` and `order_requirements` |

Every Gerber starts with one descriptive comment (for example `G04 Direct
Gerber JLC review candidate: top_rows_fpc top copper*`), then the X2
attributes in comment form, then `%FSLAX46Y46*%` and `%MOMM*%`
(millimetres, six decimals):

```text
G04 #@! TF.GenerationSoftware,TactileFPC,direct-gerber,0.3.0*
G04 #@! TF.SameCoordinates,<build_id>*
G04 #@! TF.FileFunction,...*
G04 #@! TF.FilePolarity,...*
```

`TF.SameCoordinates` is the build id; its scope is one board ZIP (the two
boards of a build share the identifier, not a coordinate frame).  The GTS
and GBSL select a 0.01 mm aperture before their regions, for conservative
RS-274X readers.

### Netlist

`netlist.ipc` is IPC-D-356A in fixed columns: comment lines, then `P JOB
<build_id>`, `P TITLE <board id>`, `P UNITS CUST 1` (millimetres at 0.001
mm), `P VER IPC-D-356A`, `P IMAGE PRIMARY`; one `327` SMD test record per
contact (`J1-<pin>`, the pad's net, centre and size); one more per routed
net, a square land of the strip width at the **far** end of its electrode
(`ROW-<n>` / `COL-<n>`; the end its fan-out piece does not reach), so a
probe pair tests each net from contact to electrode end; then `999`.  Every record has access `A01`, soldermask `S2`
(exposed on the copper side) and rotation `R000`.  NC contacts are their own
`NC_<pin>` nets with one test point each.

## Review bundle

| Member | Content |
| --- | --- |
| `design.json` | the canonical design (canonical JSON plus a newline; `design_sha256` hashes it without the newline) |
| `profile.json` | the profile the build used (`profile_sha256`) |
| `validation.json` | `tactile-fpc-validation/v1`: errors, warnings, normalization, `counts` (`error_count`, `warning_count` of design warnings, equal to the manifest's, and `request_warning_count`), `request_warning_codes` and a note |
| `derived-layout.json` | canonical `{format, units, boards}` of the regenerated boards |
| `pinout.csv` | `pin, net, role, logical_index, contact_center_x_mm, contact_center_y_mm, physical_side`: every contact of both boards, top board first, pins ascending; `logical_index` is empty for NC contacts |
| `taxels.csv` | masked and diagonal Row bus builds only: `row, column, row_net, column_net, row_pin, column_pin, active`, every R x C readout position in ROW-major order with its two nets, their contact pins and `active` (1 where the electrodes cross, 0 where the mask leaves the position without a crossing: it always reads 0) |
| `ORDER_NOTES.txt` | the order notes of both boards: each board with its archive and stiffener layers (top board first), then the shared order options, review notes, upload checks and sources |
| `previews/top_fpc.svg`, `previews/bottom_fpc.svg` | the copper-side top views, the same bytes as the result's `svg` |
| `gerbers/<name>` | both board ZIPs under their artifact names |
| `manifest.json` | `tactile-fpc-export-manifest/v2` (below) |

The export manifest carries the identity fields (`build_id`,
`build_sha256`, `design_sha256`, `profile_sha256`, `generator`, `exporter`,
`profile`, and `template` for a design of another template than
`generic_matrix_v1`, e.g. `surface-matrix/1` for the CAD mode's
`surface_matrix_v1`, which then enters `build_sha256` as well), `layout_format`, the status flags (`status:
direct_gerber_jlc_review_candidate`, `production_ready: false`,
`easyeda_native_export: false`, `requires_final_jlc_review: true`), the
`review_requirements` (the upload checks, then one line per order
requirement), `order_notes` and `order_requirements`, an `identity` block
that explains how to recompute
every digest, `checks` (`error_count`, `warning_count`, `drc_version`,
`boards_equal_engine_generation`, `files_read_back`), `export_verification`,
the `validation` and `pinout` file descriptions, the `canonical_design`, per
artifact its `filename`, `sha256`, `bytes`, member digests, stiffeners,
netlist summary and geometry counts, and `bundle_files` (the digest of every
other member).  The bundle can therefore be verified from its own bytes.  A
masked build's manifest also has `mask` (`field-mask/1`, in the identity and
`build_sha256`) and `taxel_map`: `file` (`taxels.csv`), `columns`, `active`
(the taxel count), `total` (R x C) and `frame`.  A diagonal Row bus's
manifest has `row_bus` (`diagonal-bus/11`; in the identity and
`build_sha256`), `taxel_map` and `diagonal_row_bus`: `kind`, `row_board`,
`construction` (the Row board's `construction.row_bus`, its `tails`
`stacked` and its `shared_outline_below_field_mm`, the level down to which
both boards share one outline: their tails' roots), `row_contact_order` (its
`tail.row_contact_order`), `row_contact_pins` (the pins of those contacts),
`column_board` (the straight Column board's copper, its tail centred: no
shift or neck to record; one V, no slot) and `frame`.

`validation.json` copies the request's normalization report and request
warnings as given: two equivalent requests share the build id and the Gerber
ZIPs, but their review bundles can differ in this file.

## Masked taxel fields

A surface design with a field mask (`matrix.mask`; the boards are in
[LAYOUT_SCHEMA.md](LAYOUT_SCHEMA.md#masked-boards)) exports the same members
as any build, plus `taxels.csv` in the bundle:

- **GTS.**  The merged field window of a masked board is a polygon (the
  union of the electrodes' windows and the fillers between them), written
  as one G36/G37 region over its ring in layout order and read back vertex
  by vertex.  Per-electrode windows and the gang contact window stay
  rectangles; a mask whose electrodes are all the same keeps the rectangle.
- **GTL, GKO, stiffeners, `jlcpcb.json`, `netlist.ipc`, `pinout.csv`.**
  Unchanged in form: the trimmed electrodes are rectangles, the outline is
  the masked board's, every net keeps its contact and pin, and each
  electrode keeps one far-end land, on its copper (the fan-out ends on its
  near end), so no test point sits at an inactive position.
- **`ORDER_NOTES.txt`** (each board ZIP and the bundle) states the field
  after the profile, e.g. "Taxel field: 55 of 10 x 10 crossings (masked):
  the electrodes, their coverlay windows and the outlines follow the mask;
  the other positions have no crossing and read 0."  The read-back takes
  the count from the design's mask and requires it in its place.
- **`taxels.csv`** (bundle) lists every R x C position, and the review
  manifest's `taxel_map` names it.  Its read-back requires the header,
  R x C lines in ROW-major order, each board's electrode nets with the pins
  of their contacts, and `active` exactly where both boards' taxel masks
  (`grid_registration.taxel_mask`, which must be equal) put a taxel, as many
  as each board's `active_taxel_count`.

A full mask is the unmasked design (the same build id and Gerber ZIPs; the
bundle's `validation.json` records the normalization), and an unmasked
build's archives do not change (the table below).
`tests/test_mask_export.py` pins the archives of four masked builds (a
polygon window, per-electrode windows, tails on the right with the columns
on top, opposite tails), the same on Python 3.9 and 3.12; the right
triangle of 55 of 10 x 10 taxels gives a 28495-byte top ZIP, a
29436-byte bottom ZIP and a 171123-byte bundle.

## Diagonal Row bus

A design built as the diagonal Row bus (`routing.row_sides` `left`, `right`
or `both`, on either template: the rectangular mode's default; its boards
are in [LAYOUT_SCHEMA.md](LAYOUT_SCHEMA.md#diagonal-row-bus)) exports the
members of a masked build.  Nothing new is drawn: its lanes are polylines and its
field windows polygons, written and read back as above.

- **Pin order.**  The Row contacts carry the folded order of the lanes
  (`tail.row_contact_order`: with `both` ROW_01, 03, 05, ..., 06, 04, 02),
  and the pins still run monotonically along the contact row
  (`channel_order`).  `pinout.csv`, the `J1-<pin>` records of `netlist.ipc`
  and `taxels.csv` take each row's pin from its contact, so pin *k* carries
  ROW_k only where the order puts it: 9 rows with `both` and ascending
  order put ROW_01..ROW_09 on pins 1, 9, 2, 8, 3, 7, 4, 6, 5.  The
  netlist's land at the far end of each Row electrode lies at the end its
  lane does not leave, so with `both` the odd rows' lands are at one end and
  the even rows' at the other.
- **`taxels.csv`.**  The boards always carry the masked records, so the
  bundle always has the taxel map; without a mask every position is active
  (`taxel_map.active` is R x C) and `ORDER_NOTES.txt` has no taxel-field
  line, since nothing is masked.
- **`diagonal_row_bus`** (review manifest) records the Row board's
  `construction.row_bus` (sides, split, near and far rows, contact order,
  tail position, the stacked tails, the shared outline's level, fans, tip,
  bands, lane angles) and its contact order with the pins of those
  contacts.  The Column board has the straight one's copper, coverlay and
  stiffener (one V: no slot, no `cutouts`), its tail root on the shared
  bottom edge; down to the tails' roots its outline is the Row board's
  (the two boards share one outline there, the union of their bodies: each
  GKO draws the field, the Row bands and funnel and the Column fan-out),
  and its archive holds the same members as the same design's straight Row
  channel (`routing.row_sides` `channel`).
  Its
  read-back requires the Row tail's order to be the one
  `construction.row_bus` reports, to name every row once, and `pinout.csv`
  to list each of its nets at the pin of the contact at its position.
- **Identity.**  `row_bus` (`diagonal-bus/11`) is among the identity fields
  of the review manifest and of each board manifest, and in the
  `build_sha256` recipe.

The straight Row channel's archives keep their bytes:
`tests/test_diagonal_export.py` pins four of them (besides the masked ones
above), and the archives of five diagonal-bus builds, the same on Python 3.9
and 3.12.  The generic template's straight channel (`routing.row_sides`
`channel`, since P5-diagonal-bus.md section 18 no longer its default) names
the channel in its design, so its build ids moved once; every member of its
archives but the identity carriers (the manifests, `design.json`, the
nested ZIPs; the build id masked in the rest) is the byte string of before
(`tests/test_generic_identity_guard.py`, from 8a4b2f1).

## Determinism

Members are stored uncompressed (`ZIP_STORED`) in name order, dated
1980-01-01, with Unix attributes `0644` and no data descriptors, so the
archive bytes depend on the member bytes only, never on the zlib
implementation.  JSON members are canonical.  DRC records report the first
location in the deterministic sweep order among values equal at 1e-6 mm,
so `derived-layout.json` and the review bundle are byte-identical across
Python 3.9 to 3.13 and hash seeds.  The default build gives:

| Archive | Bytes | SHA-256 |
| --- | --- | --- |
| `tactile-fpc-12x32-34a71a29e4d0-top-rows-direct-gerber.zip` | 30097 | `f3edfa708c37455feb74361a9652bf5fe61b9ed13c67d9c86770e1b91288c4bd` |
| `tactile-fpc-12x32-34a71a29e4d0-bottom-columns-direct-gerber.zip` | 42203 | `45ac29dd2b1551477f0a8243a8bfb8bb349a8b9c79c5cb7e19b2d3954cbe905f` |
| `tactile-fpc-12x32-34a71a29e4d0-project-review.zip` | 235822 | `420ecf33f8b65d8ecf664e73f2d36a5e58918bf1d9e6a7be58b75bba10dd5e5d` |

(`tests/test_golden_default.py` pins these values; the bundle shown is the
one of `default_design()` and of the browser's export of the default build,
the diagonal Row bus with `both` since P5-diagonal-bus.md section 18,
`diagonal-bus/8` since section 20: built with CAD mode's rule set, the
surface profile, both boards one outline down to the tail roots;
`diagonal-bus/9` since section 24, the same boards; `diagonal-bus/10` since
section 27, the Row tail 0.048 mm east, on the field's centre line; both
tails 12 mm since section 27.7, the Column board 4.5 mm longer;
`diagonal-bus/11` since section 27.8, the same boards; the 1.0 mm electrodes
of the default fill 0.5 since the user's decision of 2026-11-06, both boards
0.4 mm narrower and shorter and a coverlay window per electrode.)

## Stiffeners

Side, material and thickness come from each stiffener object, which takes
them from `profile.stackup`.  Only bottom polyimide stiffeners (opposite the
top-copper contacts) are supported, and the profile check rejects anything
else before generation (`E_PROFILE_INCONSISTENT` for another side,
`E_PROFILE_FAB_LIMIT` for a material without an orderable thickness list or a
thickness that is not a JLC PI option 0.1, 0.15, 0.2, 0.225 or 0.25 mm).  The
connector-zone thickness must also suit the reader connectors (below): on the
ordered 0.11 mm build that leaves the 0.225 and 0.25 mm options.  The
layer name and `jlcpcb.json` follow the thickness, e.g.
`Gerber_BottomStiffenerLayer_pib_0.225.GBSL` for the default 0.225 mm (since
2026-10-14; it was 0.2 mm); stiffeners of different thicknesses go to
separate layers.

## Order requirements

`ORDER_NOTES.txt` (in each board ZIP and in the bundle), the
`order_requirements` of both manifests and `/api/default` carry the same
entries, resolved from the profile by `engine.profile.order_requirements()`:
the `order` block (`fpc_layers`, `fpc_thickness_mm`, `outline_tolerance_mm`,
`surface_finish`, `reference_contact_window_margin_mm`), the layers and the
stiffener of `stackup` (the ordered build) and the JLCPCB and connector facts
of `fabrication`, `connector` and `sources` (the JLCPCB flexible-PCB
capabilities page fetched 2026-10-12, its trace rules rechecked 2026-10-15,
and the THD0515-32CL-SN and TXGA FFC05001-16SBB124W5M drawings); the trace
note also names the default fan-out trace width, of the default design the
caller passes (`order_requirements(profile, default_design())`).  The
entries do not depend on the build: each board's lines of `ORDER_NOTES.txt`
give the build's fan-out width and spacing and what JLC's -20% width
tolerance makes of them, e.g. for 0.1016 mm traces "Trace tolerance: at
JLC's -20% the 0.1016 mm fan-out traces may come out 0.08128 mm wide, below
JLC's 0.1016 mm minimum for 1 oz copper (traces at least 0.127 mm wide stay
at or above it)."  The wording, and which sources each entry
cites, are in that function.  The profile check rejects an FPC thickness,
copper, surface finish or outline tolerance JLCPCB does not offer
(`E_PROFILE_FAB_LIMIT`), and a stack-up whose layers do not add up to the
ordered thickness or an order the reader connectors cannot take
(`E_PROFILE_INCONSISTENT`).  It checks the connectors two ways: the outline
tolerance must hold the THD0515 tail width (+/-0.07 mm), and the contact zone
(core, copper and stiffener under the open coverlay) must be within
0.30 +/- 0.03 mm.  Each entry has `id`, `kind` (`order_option` or
`review_note`), `topic`, `requirement`, `special_request`, `reason`, `sources`
and `values`.

In short: order each board as a 1-layer, 0.11 mm FPC with 1 oz copper and a
0.225 mm PI stiffener at the contacts, a +/-0.05 mm outline tolerance (a
special request) and ENIG, and check that the 0.3 mm gold fingers come out
within +/-0.05 mm (JLC's trace tolerance is +/-20%).

| Entry | Kind | Requirement (default profile) |
| --- | --- | --- |
| `fpc_thickness` | order option | 1 layer, 0.11 mm FPC thickness (finished, without the stiffener) |
| `copper_weight` | order option | 1 oz (0.035 mm) |
| `pi_stiffener` | order option | PI 0.225 mm on the bottom side at the contacts (the 6 mm zone from the tip) |
| `gold_finger_thickness` | order option | Yes, Gold Fingers Thickness 0.3 mm (the stiffened contact zone in total, from the contact surface to the outer surface of the stiffener) |
| `outline_tolerance` | order option | +/-0.05 mm (special request; JLC's default is +/-0.1 mm) |
| `surface_finish` | order option | ENIG |
| `finger_width` | review note | ask JLC to hold the 0.3 mm contacts within +/-0.05 mm, or measure them on delivery |
| `trace_widths` | review note | the fan-out traces are 0.127 mm wide by default (routing.trace_width_mm, at least 0.1016 mm) and widen to 0.254 mm in the tail, which the stiffener edge flexes |
| `contact_zone` | review note | the tail is about 0.285 mm thick at the contacts; measure it on delivery |
| `contact_start` | review note | the contacts start 0.3 mm from the tip |
| `contact_window` | review note | the gang coverlay window leaves 0.05 mm beyond the outer contacts |
| `coverlay_windows` | review note | check them on the upload: JLC advises one opening no longer than 20 mm, and the merged electrode-field window and the gang contact window are one opening each (each board's lines in ORDER_NOTES.txt give its windows and those longer) |

The reasons, as `ORDER_NOTES.txt` gives them: JLC's 1-layer finished
thicknesses are 0.07, 0.11 and 0.12 mm; the 0.11 mm FPC is a 0.025 mm PI
core, 0.035 mm copper and a 0.025 mm PI + 0.025 mm adhesive coverlay, and
JLC's single-sided copper is 0.5 or 1 oz (0.018 or 0.035 mm); both reader
connectors take a 0.3 +/- 0.03 mm thick FPC at the contacts, and JLC
recommends a 0.225 mm PI stiffener for a 0.3 mm connector on a 0.11 mm FPC;
with the coverlay open, core, copper and stiffener make about 0.285 mm, and
JLC holds the gold-finger area to +/-0.03 mm; THD0515-32CL-SN needs the
tail width 0.5 x (N + 1) mm within +/-0.07 mm, and JLC's default
laser-outline tolerance is +/-0.1 mm (+/-0.05 mm on request); JLC's
trace-width tolerance of +/-20% allows 0.24-0.36 mm for the 0.3 mm contacts,
the TXGA drawing 0.30 +/- 0.05 mm; JLC's minimum trace width and spacing for
1 oz copper is 4/4 mil (0.1016 mm), and at +/-20% a 0.127 mm fan-out trace may
come out at 0.1016 mm (JLC sets no rule on necking or on the trace width near
bends or stiffener edges); JLC cuts back gold fingers closer than 0.2
mm to the board edge and asks for 0.3 mm from copper to the laser outline;
the contact window stops where the R0.30 tip corners begin, and the
JLC-accepted reference design opened its coverlay 0.051 mm beyond each
contact.  Since profile revision 2026-10-29 (JLC's gold-finger stiffener
ordering guide and its FPC design rules, both fetched that day): JLC gives
the total gold-finger thickness ordered (0.3 mm, from the contact surface to
the outer surface of the stiffener) the highest priority when it chooses the
stiffener under the gold fingers, so its PI calculator may take another PI
thickness there than the 0.225 mm of the stiffener option (its guide's
example takes 0.2 mm for 0.3 mm); the contact-zone estimate of 0.285 mm does
not count the stiffener's adhesive.  JLC advises one coverlay opening no
longer than 20 mm (a longer one can stretch and deform when the coverlay is
laminated); the merged electrode-field window is one opening (64 x 23.6 mm
on the default board) and the JLC-accepted reference design's field windows
were up to 63.373 mm long (23.368 x 63.373 mm), so the notes ask for a
check on the upload instead of refusing the build.  Each board's lines name
its windows, for example "Coverlay windows: electrode field 64 x 23.6 mm,
contacts 5.9 x 4.4 mm; longer than JLC's general 20 mm for one opening: the
electrode field window (64 mm)."

## Manufacturing status

Before ordering, upload each board ZIP separately to JLCPCB, set the order
options above and check:

- the independent board outline and the routed slot;
- every coverlay opening, in particular the contact window, which stops at
  the straight part of the tip edge and so leaves only 0.05 mm of coverlay
  expansion beside the outer contacts (JLC's expansion is 0.1 mm);
- that each PI stiffener layer is detected at its thickness (0.225 mm by
  default).

Not verified with JLCPCB (no upload was made): whether JLC ignores or uses
the extra members `manifest.json`, `netlist.ipc` (and the netlist for its
electrical test) and `ORDER_NOTES.txt`, how it treats comment-form X2
attributes, the stiffener detection for the default 0.225 mm PI layer (the
JLC-accepted reference packages used 0.1 and 0.2 mm), whether the +/-0.05
mm outline tolerance and the gold-finger width are held as requested, and
that the 0.11 mm 1-layer FPC comes with 1 oz copper (derived from JLC's
thickness and coverlay tables) at the estimated contact-zone thickness.  Not
implemented: X2 object attributes (`TO.N`, `TO.P`) on the contacts (nets and
pins are in `netlist.ipc`), top-side and non-PI stiffeners.

## Exporter revisions

- One side's convex flank (2026-10-28, construction `diagonal-bus/11`, the
  plan's section 27.8, still `0.3.0`): with one side, the side without lanes
  is convex from the field's outline corner down to the tail.  The exporter
  is unchanged; every archive of a diagonal-bus build changes bytes (its
  build id, and a one-sided build's outlines there); the default's archives
  keep their sizes; straight-channel archives keep theirs.
- The Row tail centred on the field (2026-10-27, construction
  `diagonal-bus/10`, the plan's section 27, still `0.3.0`): the Row tail
  lies centred on the field in every side mode, one side's whole bundle
  fanning in under the field.  The exporter is unchanged; every archive of
  a diagonal-bus build changes bytes (its build id, the Row tail's contacts,
  stiffener and traces, and where the tail moved the outlines); the
  default's tail moves 0.048 mm and its archives grow by 1-5 bytes;
  straight-channel archives keep theirs.
- The Row bus's convex sides and the corner tolerance at every convex corner
  (2026-10-25, construction `diagonal-bus/9`, the plan's section 24, still
  `0.3.0`): each side's dents from the tip corner down to its widest point
  bridged by its hull.  The exporter is unchanged; every archive of a
  diagonal-bus build changes bytes (its build id, and where a side has such a
  dent its outline: GKO and the manifest's outline vertex count); the
  default's outlines and archive sizes are the same; straight-channel archives
  keep theirs.

- The rectangular generator's bus as a subset of CAD mode (2026-10-24,
  construction `diagonal-bus/8`, the plan's section 20, still `0.3.0`):
  one rule set on both templates, one outline down to the tail roots and
  the Column V capped at 80 degrees.  The review manifest's frame says the
  shared outline reaches the tails' roots, below which each board has only
  its tail.  Every archive of a diagonal-bus build changes bytes (its build
  id, both outlines and, where a root moves, the copper of the tails'
  contact columns); straight-channel archives keep theirs.

- The Row bus's regular outlines (2026-10-23, construction `diagonal-bus/5`,
  still `0.3.0`): no outline vertex turns by less than 5 degrees but on a
  fillet.  The exporter is unchanged; every archive of a diagonal-bus build
  changes bytes (its build id and both outlines do, GKO and the outline
  vertex count of the manifest; the copper does not); straight-channel
  archives keep theirs.

- The Row bus's one outline over the field (2026-10-22, construction
  `diagonal-bus/4`, still `0.3.0`): the review manifest's
  `diagonal_row_bus.construction` adds `shared_outline_below_field_mm` and
  its frame states the shared outline.  Every archive of a diagonal-bus
  build changes bytes (its build id and its Column outline do; GKO of the
  Column ZIP draws the outline shared with the Row board over the field);
  straight-channel archives keep theirs.

- The Row bus's stacked tails (2026-10-22, construction `diagonal-bus/3`,
  still `0.3.0`): the review manifest's `diagonal_row_bus` drops
  `column_tail_shift_mm` and `column_neck_mm` (the Column board is the
  straight one again) and its frame states the stacked tails
  (`construction.tails`).  Every archive of a diagonal-bus build changes
  bytes (its build id does; its Row board too); straight-channel archives
  keep theirs.

- The Row bus's tail redesign (2026-10-22, construction `diagonal-bus/2`,
  still `0.3.0`): the review manifest's `diagonal_row_bus` records the
  Column tail's shift and neck (`column_tail_shift_mm`, `column_neck_mm`)
  instead of the stub drop, with their frame.  Every archive of a
  diagonal-bus build changes bytes (its boards do); straight-channel
  archives keep theirs.

- One-sided Row bus in the order notes (2026-10-22, the P5d/P5e repair,
  still `0.3.0`): the Row pin order line of a one-sided bus
  (`routing.row_sides` left or right, the rows in turn) reads "(diagonal
  Row bus, one side)", not "folded"; the Row board's ZIP and the bundle of
  such a build change bytes.

- Folded Row pins in the order notes (2026-10-21, masked-field phase P5d,
  still `0.3.0`): the Row board's lines of a diagonal Row bus's
  `ORDER_NOTES.txt` (its ZIP's and the bundle's) state its contacts' pins
  with their Row nets in the folded order ("Row pin order (diagonal Row
  bus, folded): pin 1 ROW_01, pin 2 ROW_03, ..."), and the read-back asks
  for them from `tail.row_contact_order` and the pads.  The Row board's ZIP
  and the bundle of a diagonal-bus build change bytes (the Column board's
  ZIP keeps them); straight-channel archives keep theirs.

- Diagonal Row bus (2026-10-21, masked-field phase P5c, still `0.3.0`):
  `taxels.csv` and `taxel_map` for every diagonal-bus build (every position
  active without a mask, and then no taxel-field line in the order notes),
  the review manifest's `diagonal_row_bus` and the read-back of
  `pinout.csv` against its folded Row contact order.  Diagonal-bus builds
  are new (phase P5b), and the straight Row channel's archives keep their
  bytes, so the version and every build id stay.

- Masked taxel fields (2026-10-21, masked-field phase P3, still `0.3.0`):
  the polygon field window in the GTS and its read-back, the form checks of
  polygon openings, the taxel-field line of `ORDER_NOTES.txt`, `taxels.csv`
  and `taxel_map`.  No masked archive existed before (phase P2 refused
  masked builds), and unmasked archives keep their bytes, so the version
  and every build id stay.

- `0.3.0` (2026-10-15, with generator 0.4.0 and layout v3): each net is two
  route pieces, a thin fan-out piece and a wide tail piece (`segment`), so
  the GTL has one aperture per width; the route-width check uses JLC's
  minimum for the profile's copper (0.1016 mm for 1 oz, it was the 18 um
  0.0889 mm); the netlist places each electrode land from the fan-out piece;
  `ORDER_NOTES.txt` gains the trace note, each board's trace widths and a
  line on what JLC's -20% width tolerance makes of its fan-out traces, read
  back like the other figures.  Every build id changed.

- `0.2.0`, stage G (2026-10-14): `ORDER_NOTES.txt` in each board ZIP and in
  the bundle, `order_notes` and `order_requirements` in both manifests, one
  `review_requirements` line per order requirement, and their read-back
  (the contact and connector-zone stiffener figures against each board).
  Profile revision 2026-10-14.2: the stack-up of the ordered 0.11 mm build
  (1 oz copper), the copper-weight entry and the contact-zone review note.
  The version stayed 0.2.0 (decision D17), but no build id names archives
  with and without the notes: the profile must now hold the `order` block, so
  every profile digest, and with it every build id, changed (the default
  PI stiffener became 0.225 mm in the same revision).
- `0.2.0` (2026-10-14): layout v2 (anchored rectangles; reader-connector
  tails with NC contacts, R0.30 tip corners and gang contact windows; merged
  electrode windows; the fixed connector-zone stiffener; filleted outlines).
  Stiffeners from the stiffener objects with EasyEDA-style layer names per
  thickness; `netlist.ipc`, board `manifest.json`, `pinout.csv`,
  `validation.json`, `profile.json` and both ZIPs in the bundle; artifact
  names with the build id; X2 `TF.SameCoordinates` and the version in
  `TF.GenerationSoftware`; stored members; the regeneration binding, the
  read-back and `ExportError` only.  Every build id changed (the exporter
  version is part of the identity).
- `0.1.1` (2026-10-13): connector pads emitted around their stored centre
  (audit C1).
- `0.1.0`: shifted every contact by half its size (open circuits on top and
  right tails, 0.073 mm from the neighbouring net on bottom and left tails).
  Packages from `0.1.0` have that defect.  Regenerate every `0.1.x`
  package: those written before the layout v2 commit (`084ca98`) also carry
  the layout v1 defects (electrodes at the Column outline, 0.2 mm
  copper-to-edge rule, tails that do not fit the reader connectors), and the
  exporter version alone does not tell them apart (the build id and the
  profile revision do).
