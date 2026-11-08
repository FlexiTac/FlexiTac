# Tactile FPC Customizer — implementation plan

> **Status 2026-10-15.** Phases 1 and 2 are implemented, and the fixes of the
> 2026-10-12 audit (C1-C3, H1-H6, M1-M14 and L1-L13) are on branch
> `fpc-customizer-audit-fixes`; the final review of 2026-10-15 rates H4, M6,
> M9, M12, M14, L1, L7 and L13 only partly fixed (section 9.2 of the audit
> report lists what is left; for L7 the reference design's 0.6 mm electrodes
> and slits are open product decisions, while the contact-zone thickness was
> decided on 2026-10-14 with the 0.225 mm PI stiffener of stage G).  The
> branch has layout v3 with reader-connector tails and necked routing
> (adjustable thin fan-out traces in bundles that widen to the gold-finger
> width in the tail, 2026-10-15), a whole-board DRC, strict input, a JSON
> Schema / validate / compact API and a CLI, exporter 0.3.0 with a netlist,
> the profile's JLCPCB order requirements (`ORDER_NOTES.txt`) and a
> self-verifying review bundle.  Phase 3 is partly done
> (golden values of the default build, legal-range sweeps, a mutation check);
> its manufacturing evidence (EasyEDA import, JLCPCB upload, physical tests)
> is still missing.  Phase 4 has not started.  Statements below that the
> code does not meet are marked as plan or open.

## Product decision

The first release is a local, deterministic web application.  It creates two
separate flexible PCBs for a matrix tactile sensor: a row-electrode FPC and a
column-electrode FPC.  It does **not** call a chatbot, cloud API, existing
EasyEDA project, KiCad board, or Gerber file during generation.

An LLM may later be offered only as an optional form-filling/explanation
assistant.  It must never decide geometry, waive a DRC error, or modify a
manufacturing output.  (None exists; the machine-readable surface such an
assistant would use is in [API.md](API.md).)

## Source of truth and outputs

One versioned `design.json` is the input.  The geometry engine derives both
FPCs from it once, then all previews and export formats are made from that
same derived layout:

```text
design.json + locked manufacturing profile
              │
              ▼
     validation + derived dimensions
              │
              ▼
 row FPC layout       column FPC layout
       │                        │
       ├── 2D SVG top view      ├── 2D SVG top view
       ├── oblique view         ├── oblique view
       ├── project JSON         ├── project JSON
       └── manufacturing files  └── manufacturing files
```

Every build is deterministic and named by its build id, a digest of the
canonical design, the full profile and the generator and exporter versions.
The project review bundle of a build contains its input, profile, validation
report, derived geometry, pinout, previews, both Gerber ZIPs, a manifest and
the SHA-256 of every file.  The application stores nothing: downloads are
created in memory (no saved-build history).

## User-visible parameters

The UI exposes functional sensor parameters, not raw PCB drawing controls:

| Group | Parameters | Implemented |
| --- | --- | --- |
| Matrix | row count, column count | yes |
| Taxel | X/Y pitch, row-electrode width, column-electrode width, active-area margins | pitches and widths; the margin is locked in the profile |
| Mechanical | tail length, connector side, matrix orientation | Top/Bottom tail lengths and one shared connector side; per-board sides through the API |
| Electrical mapping | which independent FPC is rows/columns, scan order, reverse order, connector size | all: role, one shared scan order and both connector sizes in the form; a per-role order through the API |
| Routing | fan-out trace width and spacing | both, in the form and the API (2026-10-15), within JLC's 1 oz minimum and the gold-finger width |
| Product | design name, version, selected validated template/profile | name only; one template and one locked profile |

The nominal taxel footprint is the intersection of the row and column
electrodes.  Its geometric size is therefore `row electrode width × column
electrode width`; its spacing comes from the X/Y pitch.  Material stack,
spacer, adhesive and force-sensitive material are intentionally not inferred
from that footprint and must be specified separately for a production sensor
stack-up.

## Locked manufacturing profile

The `jlc-fpc-standard-v1` profile (`profiles/jlc_fpc_standard_v1.json`,
revision 2026-11-06b) owns the following settings; the JLCPCB flexible-PCB
capabilities it follows are quoted in its `sources` block:

- 0.254 mm gold-finger traces, a 0.1016-0.254 mm fan-out trace width,
  0.1016-0.246 mm fan-out spacing and 0.500 mm contact pitch (the fan-out
  width and spacing are design inputs within these limits, 0.127 / 0.127 mm
  by default; JLC's minimum for the ordered 1 oz copper is 4/4 mil,
  0.1016 mm, also the narrowest electrode);
- a 0.5 mm-pitch ZIF connector tail: width (pins + 1) x 0.5 mm, 0.30 x 4.0 mm
  contacts from 0.30 mm behind the tip, R0.30 tip corners;
- single top copper (1 oz, the copper of the boards' own 0.11 mm build,
  ordered as JLC's 2-layer 0.2 mm FPC with the bottom copper empty since
  2026-11-06),
  polyimide coverlay openings (0.1 mm expansion, merged where a bridge would
  be under 0.5 mm) and 0.3 mm copper-to-edge;
- a bottom polyimide stiffener at 0.1 mm over a 6.0 mm connector zone (0.225 mm until 2026-11-06);
- fan-out, slot, fillet, board-size and input limits.

The form reports these values read-only (the rule text is generated from the
profile).  A custom fabrication profile is a new, reviewed profile rather
than a collection of unchecked form inputs; the profile is checked for
internal consistency and against the published capabilities on every load.

## Templates

Two explicitly different product modes are planned.

1. **Canonical 12 × 32 compatibility** reproduces the approved 2 mm-pitch
   reference topology.  It is a regression target; it is not stretched when
   a user changes matrix dimensions.  *Not implemented (open product
   decision D8).*
2. **Generic matrix v1** uses a regular, computed outline, tail, coverlay and
   stiffener template.  It supports valid arbitrary row/column counts and
   pitches within the selected fabrication profile.  *Implemented
   (`generic_matrix_v1`, the only template).*

This division prevents the existing complex outline, internal slot and
stiffeners from being geometrically scaled into an invalid board.

## Validation gate

Generation must fail with an explicit message when it finds any of the
following; the codes are in [LAYOUT_SCHEMA.md](LAYOUT_SCHEMA.md#issue-catalogue):

| Gate | Status |
| --- | --- |
| non-positive dimensions, invalid direction, or unsupported template | implemented (input rules) |
| a matrix that does not fit the selected active-area/tail template | implemented: feasibility before geometry (`E_BOARD_SIZE`) with field-level bounds; since 2026-10-15 a narrow two-lane fan-out spreads wider than the body instead of being rejected (`E_DUAL_LANE_WIDTH` is gone) |
| connector capacity inconsistent with row/column counts | implemented (`E_CONNECTOR_PINS`, `E_COLUMNS_LANE_CAPACITY`) |
| trace centre pitch or edge clearance below profile minimums | implemented: whole-board DRC on the emitted layout |
| electrode, connector, outline, slot, coverlay or stiffener interference | implemented: whole-board DRC (30 records per board), with the design's trace spacing as the route rule, the finger-section spacing for every pair with a tail piece and a width check of every route piece |
| missing net-to-electrode or net-to-connector connection | implemented (`connectivity`, NC contacts isolated) |
| incompatible top/bottom alignment or scan mapping | alignment implemented (registration record); the scan mapping is recorded in `pinout.csv` and `netlist.ipc`, and matching it to a reader is described in [INTEGRATION.md](INTEGRATION.md) |

Warnings are advisory; errors block export.  A visual preview by itself is
not an acceptance test.

## Download and manufacturing policy

The UI provides:

- `design.json` — the canonical design;
- `derived-layout.json` — fully expanded auditable geometry;
- top and bottom 2D previews, an oblique view and an assembly preview;
- a project review ZIP; and
- one Direct Gerber ZIP per FPC.

The Gerber ZIPs are downloadable now, as **review candidates**: every
package states `production_ready: false` and `requires_final_jlc_review:
true`, and none has passed a JLCPCB upload review or a physical test yet.
A direct Gerber backend is deterministic and fast but requires the normal
JLCPCB upload review of outline, coverlay, slots and PI stiffeners.
EasyEDA Pro native Gerber export is a separate, gated local desktop workflow:
it depends on an installed/logged-in application and currently cannot be
truthfully advertised as a reliable browser-only headless service.  The
current R4 12pin native project also remains excluded from a generic
production-release claim until its EasyEDA 3D regression is fixed.

## Delivery phases

### Phase 1 — foundation (implemented)

- Create this self-contained project directory and implementation record.
- Create the locked manufacturing profile.
- Implement a generic matrix schema, deterministic geometry engine, and DRC.
- Provide the local browser UI, two independent SVG previews and JSON export.

### Phase 2 — auditable artifacts (implemented as Direct Gerber review candidate)

- Implemented: deterministic project-review ZIPs with canonical input,
  profile, validation report, derived geometry, pinout, SVG previews, both
  Gerber ZIPs, manifests and SHA-256 evidence.
- Implemented: separate top/bottom Direct Gerber candidate ZIPs with an
  IPC-D-356A netlist each.
- Implemented: the exporter decodes every Gerber, `jlcpcb.json` and netlist
  it writes and compares them with the layout; the tests read the emitted
  copper, openings, outline, stiffener, netlist and pinout back and check
  connectivity, clearances, chirality and pin 1 on every tail side.
- Deferred: persisted local build history and raster preview PNGs.  The
  browser currently creates downloads in memory to avoid silently accumulating
  user designs on disk.

Details are in [`PHASE2_DIRECT_GERBER.md`](PHASE2_DIRECT_GERBER.md).  The
output deliberately remains outside the production-ready and EasyEDA-native
claims until Phase 3 import evidence.

### Phase 3 — regression and manufacturing gates (in progress)

- Done: golden values of the default generic 12 × 32 build (identity,
  geometry, DRC measurements, archive digests).  Open: golden tests of the
  canonical compatibility template, which does not exist yet.
- Done: legal-range feasibility sweeps (sampled legal inputs generate a
  DRC-clean pair or fail validation with a field bound: 64 designs plus
  random full-precision ones in the suite, thousands in the fix-stage
  reviews) and a mutation check of the suite (`tools/mutation_check.py`).
- Open: import representative outputs into EasyEDA Pro and review JLCPCB
  upload results before declaring a profile production-ready; insert the
  tails into the reader connectors and test continuity.

### Phase 4 — optional UX extensions (not started)

- Template picker, saved presets, comparison view and batch variants (the CLI
  already runs batches).
- Optional natural-language helper that only populates the visible form and
  always requires user confirmation before deterministic generation.

## Definition of done for Phase 1

A user can run one local command, open the web page, edit rows, columns,
pitch and taxel dimensions, immediately inspect separately labelled row and
column FPC previews, see blocked-invalid cases, and download reproducible
JSON without any chatbot or network request.
