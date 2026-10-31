# Tactile FPC Customizer — application and development handoff

Updated 2026-10-15 (UTC).  Source: branch `fpc-customizer-audit-fixes`,
based on `92cdcb6` (the code the 2026-10-12 audit examined).
`git log 92cdcb6..` lists the fix commits: C1, stages E, A, X, F, T and G,
the remote-access fix and the follow-ups of the final review.  What the
final review of 2026-10-15 left open is section 9 of
[the audit report](verification/2026-10-12-audit-report.md).

## What this is

A self-contained local application that generates the two flexible PCBs of
a matrix tactile sensor, a Row-electrode FPC and a Column-electrode FPC,
from a small versioned design.  It validates the design, builds both boards,
runs a whole-board DRC on the emitted geometry, shows copper-side previews
and an assembly preview, and exports deterministic Direct Gerber review
candidates with an IPC-D-356A netlist and a self-verifying review bundle.
It uses the Python standard library only (Python 3.9+), reads nothing from
`../fpc_design`, any EDA project or any Gerber at runtime, and has no LLM or
agent despite the directory name; the JSON Schema, validate and compact
endpoints and `cli.py` are the surface an agent would use.

Where to read further: [README](../README.md) (run, features, limits),
[docs/API.md](../docs/API.md), [docs/LAYOUT_SCHEMA.md](../docs/LAYOUT_SCHEMA.md),
[docs/INTEGRATION.md](../docs/INTEGRATION.md),
[docs/PHASE2_DIRECT_GERBER.md](../docs/PHASE2_DIRECT_GERBER.md), the plan
with its status in [docs/IMPLEMENTATION_PLAN.md](../docs/IMPLEMENTATION_PLAN.md)
and the [2026-10-12 audit report](verification/2026-10-12-audit-report.md).

## History

- 2026-09-13/14: Phase 1 (engine, UI, JSON) and Phase 2 (Direct Gerber
  exporter 0.1.0), recorded in [docs/PHASE1_TECHNICAL_RECORD.md](../docs/PHASE1_TECHNICAL_RECORD.md);
  imported as commit `045b737` (synced from `far-pi5`).
- 2026-10-11: a first review ([verification/2026-10-11-review.json](verification/2026-10-11-review.json)).
- 2026-10-12: the full audit (3 critical, 6 high, 14 medium, 13 low, 5 info).
- 2026-10-13: C1 fixed (exporter 0.1.1); the fix-all specification decided
  the product defaults D1-D24.
- 2026-10-13/14: the fix in five stages, each implemented, reviewed and
  repaired: **E** engine geometry and whole-board DRC, **A** API, identity,
  HTTP and SVG, **X** exporter 0.2.0, **F** browser UI, **T** tests and
  documents.  Dated session notes are in `claude/sessions/` (not in the public copy).
- 2026-10-14: stage **G**, approved by the user after a review of the
  reader-connector drawings: the default PI stiffener is 0.225 mm (was
  0.2 mm), and the profile's validated `order` block, with the stack-up of
  the ordered 0.11 mm build (1 oz copper), is written to `ORDER_NOTES.txt` in
  every ZIP, to both manifests (`order_requirements`), to `/api/default` and
  to the browser's manufacturing note; `engine.profile.order_requirements`
  words the entries from the profile values and cites the profile's JLCPCB
  and connector sources.  Profile revision 2026-10-14.2.  The gold-finger
  geometry is unchanged and is now measured on the emitted Gerbers
  (`test_export_gold_fingers`).
- 2026-10-15: **necked routing**, on the user's request ("the traces are too
  thick"): the fan-out trace width and spacing are design inputs
  (`routing.trace_width_mm` / `trace_space_mm`, 0.127 / 0.127 mm by
  default, from JLC's 1 oz minimum of 0.1016 mm up to the 0.254 mm finger
  width and the 0.246 mm finger gap); the traces converge into bundles at
  width + spacing with bus-style bends and widen to 0.254 mm in the tail,
  below every bend.  Layout v3 (a tail and a fan-out piece per net), the
  `route_width` record (30 per board), the route rule is the design's
  spacing on both boards, the trace minimum depends on the copper (closes
  re-audit N4: electrodes from 0.1016 mm), per-route SVG stroke widths
  (closes N18).  Generator 0.4.0, exporter 0.3.0, profile revision
  2026-10-15: every build id changed.  After its independent review the DRC
  also holds every route pair with a tail piece to the 0.246 mm
  finger-section spacing (the `finger_section` of `route_route_clearance`),
  the far bends of the diagonals are rounded away from the bundle (no
  diagonal leans past the 60 degree cap), each board's lines of
  `ORDER_NOTES.txt` say what JLC's -20% width tolerance makes of its fan-out
  traces, and `order_requirements` takes the default design from its caller.
- 2026-10-20: **CAD mode**.  The user asked for it and the build ran
  overnight without supervision; the log is
  `claude/specs/cad-mode/PROGRESS.md`, the decisions are in
  `claude/specs/cad-mode/SPEC.md` (C-D1 to C-D12; neither is in the public copy),
  and the feature is documented in [docs/CAD_MODE.md](../docs/CAD_MODE.md).
  - The workflow: drop in an STL, select a surface, set the resolution,
    Generate.
  - New package `surface/` (stdlib): mesh, selection, flattening, fit,
    placement, taxel map.  Routes `/api/surface/{inspect,select,fit,map}`
    take a framed body up to 64 MiB; `cli.py surface`.
  - A browser CAD mode with vendored three.js 0.186.1.
  - New engine template `surface_matrix_v1` with its own profile: margins
    0.5 mm, a tight Row channel, the bus angle searched up to 85°, a direct
    one-lane fan-out, up to 64 columns.  Generic designs keep their build
    ids (guard fixture).
  - Nothing is committed yet: the user decides.

## Audit issue status

The status of each finding as its fix stage reported it after an
independent review and a repair round; stage T re-checked them through the
full suite and the mutation catalogue (which re-introduces the audit's
defects), not by re-auditing each one.  The final review of 2026-10-15
rates H4, M6, M9, M12, M14, L1, L7 and L13 only partly fixed (section 9.2 of
[the audit report](verification/2026-10-12-audit-report.md)).

| Issue | Status | Where |
| --- | --- | --- |
| C1 contact pads exported off-centre | fixed | exporter 0.1.1/0.2.0; read-back tests |
| C2 Column electrodes at the outline | fixed | 0.75 mm margin below the field, copper-to-outline DRC (E) |
| C3 tails do not fit the reader connectors | fixed | (P + 1) x 0.5 mm tails, 0.3 x 4.0 mm contacts, NC contacts, `connector.*_pins` (E); the default Row tail stays 12 positions (see open items) |
| H1 most of the pitch range infeasible | fixed | scaled tapers, feasibility errors with field bounds (E) |
| H2 previews mirrored | fixed | copper-side SVG top views (A), browser registration and pin-1 ring (F) |
| H3 0.2 mm copper-to-edge rule | fixed | 0.3 mm for all copper and slots, profile checked against JLC (E) |
| H4 tests blind to geometry | fixed | read-back, golden, chirality, negative DRC flow, HTTP and CLI tests, mutation check (A, X, T) |
| H5 verification gates missing | fixed | whole-board DRC, 30 records per board plus registration (E; `route_width` since 2026-10-15) |
| H6 unknown fields silently dropped | fixed | strict normalization, `E_UNKNOWN_FIELD`, normalization report (A) |
| M1 stiffener outside the outline | fixed | fixed 6.0 mm connector zone, flush (E) |
| M2 V-notch at the tail root | fixed | monotone hull, rolling-circle fillets, neck rule (E) |
| M3 assembly preview order and offset | fixed | top board upper, turned over about its tail axis (F) |
| M4 stale results downloadable | fixed | stale banner, downloads disabled (F) |
| M5 integration semantics undefined | fixed | monotonic pins, pinout and netlist (E, X), [INTEGRATION.md](../docs/INTEGRATION.md) (T) |
| M6 provenance and identity | fixed | identity over design, profile and versions (A); complete bundle, build-id names (X) |
| M7 profile not the single source | fixed | rules in the profile, profile checks, stiffeners from objects (E, X) |
| M8 vertex-normal offset | fixed | true offset with round joins (E) |
| M9 no width or size limits | fixed | 0.1016 mm electrodes (JLC's 1 oz minimum since 2026-10-15; re-audit N4), 234 x 490 mm boards (E) |
| M10 no netlist | fixed | `netlist.ipc`, `pinout.csv` (X); X2 object attributes not written |
| M11 two anchor meanings | fixed | anchored rectangles, layout v2 (E), [LAYOUT_SCHEMA.md](../docs/LAYOUT_SCHEMA.md) (T) |
| M12 documents overclaim | fixed | documents rewritten; their tables, snippets and the quoted figures listed in `tests/test_docs_consistency.py` are checked there (prose without figures is not) (T) |
| M13 no observability | fixed | zoom and pan, DRC panel, failure clearing (F) |
| M14 not agent-ready | fixed | JSON Schema, `/api/validate`, compact view, CLI (A) |
| L1 / L2 HTTP robustness and origin | fixed | (A) |
| L3 validation edges | fixed | (A, F) |
| L4 0.005 mm tolerance | fixed | 1e-6 mm epsilon only (E) |
| L5 single-lane fan-out too wide | fixed | (E) |
| L6 coverlay bridges | fixed | merged windows, bridge rule (E) |
| L7 reference-design differences | partly | electrode overhang done (E); contact-zone thickness: 0.225 mm PI default (G); 0.6 mm electrodes and slits open (D8) |
| L8 / L9 / L10 exporter input, X2, ZIP bytes | fixed | (X) |
| L11 performance | fixed | sort-and-sweep DRC (E), build cache, no duplicated layout (A) |
| L12 UI details | fixed | (F) |
| L13 development hygiene | fixed | `pyproject.toml`, CI (suite on 3.9 and 3.12, catalogue check, manual full mutation run), links and paths, `outputs/`, `tools/`, the test map; no lint step (T) |
| I1 no alignment features | open | product decision D8 |
| I2 no canonical 12 x 32 template | open | product decision D8 |
| I3, I4 | information | PCB-Agent-Teams is unrelated; the reader BOM's LCSC number needs an external check |
| I5 DRC counters | fixed | exact counters (E) |

## Architecture

```text
browser (web/) --HTTP--> app.py --+
                         cli.py --+--> engine.generate_design(data, cache=BuildCache)
                 Python callers --+      1 load_profile()               profile checked on every load
                                         2 _normalize_design()          strict keys, aliases, 1e-6 mm grid
                                         3 validate_design()            input rules, profile, feasibility
                                         4 _identity()                  design/profile digests, versions, build id
                                         5 _build_boards()              cached by build_sha256
                                             build_row_board, build_column_board   canonical frame, tail down
                                             apply_tail_side            whole-board quarter turns, origin at 0,0
                                             apply_physical_assignment  top/bottom from role_mapping
                                             verify_board x2 (with the design's routing), verify_registration  whole-board DRC
                                             _svg_for_board             copper-side top views
                                         6 _manifest()
                               --> exporters.build_exports(result, cache=)
                                         checks, regeneration binding, write, read-back, ZIPs
```

| Path | Responsibility |
| --- | --- |
| `app.py` | stdlib HTTP server: routes, request rules and limits, security headers, generation semaphore and build cache, `profile_for_ui()` / `display_rules()`; the routes' answers without HTTP (`answer()`, `Reply`), which the static site runs in the browser |
| `cli.py` | `schema`, `validate`, `generate [--compact]`, `export --out DIR`, batches |
| `engine/__init__.py` | the public API |
| `engine/core.py` | orchestration, normalization and aliases, input validation, identity and manifest, `BuildCache`, `result_view`, SVG top views (with polygon windows and `data-active-outline` on masked boards); the optional surface fields `matrix.mask` and `routing.row_sides` (E_ROW_SIDES, E_ROW_BUS_TAILS for opposite tails, the identity extra `row_bus`, E_ROW_BUS_INFEASIBLE from the build); `rules_template(design)`, the template whose profile builds a design (the surface template for every bus design on either template, the plan's section 20), the defaulted bottom tail of the generic template (7.5 mm for the bus, 7 mm for the straight channel) |
| `engine/schema.py` | issue catalogue, field specs and form limits, JSON Schema, strict JSON loader |
| `engine/layout.py` | Row and Column plans and geometry (bundles, bus-style bends, tail and fan-out route pieces), contacts, openings, stiffener, rotation, assignment, metrics, feasibility errors, the field mask's frames and construction classes, and the masked boards' straight constructions (`masked_row_plan`, `masked_column_plan`, polygon field windows); both builders hand a `routing.row_sides` design to `engine/diagonal.py` first, and `mask_class` gives it `{row: diagonal, column: straight}`; `field_footprint` and `E_BOARD_SIZE` measure a diagonal Row bus on its built boards (phase P5d), the size advice modelled on the straight plans and verified on the bus |
| `engine/drc.py` | whole-board DRC (30 records) and cross-board registration; on masked boards records 11-15 measure the crossing region and the polygon windows (the strict window-to-trace rule), and a masked pair is registered in the stack frame (`stack_frame`: crossings against the mask, inactive separation, the masked grid, and the reported trace-over-trace runs, `trace_overlap_*`); a diagonal-bus board (`construction.row_bus`) is masked whatever it carries (the gate), and a diagonal-bus pair adds the stack keys (traces over the other board's electrodes or its field window, the union of its electrode openings; the tail gap and each tail to the other board, 1.0 mm; E_REGISTRATION, and W_STACK_TRACE_WINDOW at close windows; crossings and runs outside the field reported only, since the plan's section 12) |
| `engine/geometry.py` | stdlib geometry: anchors, rounding to the grid, offsets, fillets, distances, orthogonally convex unions (bands, fillers, slabs, rings) |
| `engine/bus.py` | the diagonal Row bus's primitives in integer nanometres (masked-field phase P5a): the west convex chain (exact orientation), the mitred offset (slanted segments 2 nm farther, rounded away from the chain), a lane's keep-out (its continuation and a box around its start; at a lane's inward turn, following a receding field, its offset cut on the vertical one pitch out, `lane_offset`), whether a segment enters an open box (exact, for the lanes turned down on the field's edge), boxes and the mirror |
| `engine/diagonal.py` | the diagonal Row bus `diagonal-bus/11` behind `routing.row_sides` on both templates, built with the surface profile's rules (`engine.core.rules_template`; the plan's section 20: the rectangular generator's bus is CAD mode's) (phase P5b, the tail redesign of the plan's section 12, the stacked tails of section 13, the one outline over the field of section 14, extended down to the tail roots in section 20, the regular outlines of section 15: no outline vertex turning by under 5 degrees but on a fillet or the tail, `_regular`, a flatter run one straight edge outside it; the chamfered notches of section 16, `_hull_sides`; the straight sides of section 17, `_straight_sides`: each side from the tip corner down to its widest point one line where one encloses it within `SIDE_STRAIGHTEN_MM`, 1.0 mm; the convex sides of section 24, `_convex_sides`: elsewhere that stretch its convex hull, each dent no deeper than a two-cell step, 2 p / sqrt 5, bridged): the Row frame (mirrored for the one-sided bus opposite ROW_01's side), the bands (diagonal-bus/1's onion around the windows, no Column copper in its keep-out, each lane of a receding field following it inward to its bottom edge, the convex hull of what it avoids, at the bundle pitch and no flatter than the taper cap; every lane turned down on the field's bottom edge where its band crosses it or just outside the Column windows' keep-out, `_cut_at_field`; the bottom row's corner raised before the onion only where that fails, none measured), lane starts, the Row tail (centred on the field in every side mode, as the Column tail, the plan's section 27: with both the funnel, one side fanning in under the field, the rows at the tail's positions 1..R, mirrored at its far end; one side's inner flank slanting out below F's bottom to a tail wider than F's bottom; its root just below the fans' junctions), the staggered fans (a run per side and way, at the cap that roots the tail highest, off the Column entry angle by 5 degrees; their clash check), the folded contact order, the Column board (the straight one of the same design without `routing.row_sides`, `layout._masked_column_board` on the design with its mask written out: its tail centred, the tails stacked, `TAILS`; one lane straight into its contacts, its V at most `COLUMN_V_CAP_DEG`, 80 degrees, where that roots the tails no deeper than the profile's own caps, `column_profile`, `_column_plan`), the y-monotone outline, the one outline down to the tail roots (`_build`: the deeper of the two boards' own roots lowered below the union's fillets into the tails, `_lowered` moving the Column root down to it; `_own_rings`, `_share_outline`: both boards' own outlines before their fillets united in the stack, made regular, straight sides, filleted once (a vertex turning under 4 micro-radians kept: its fillet is ill-conditioned and sub-grid); each board the shared path and its own tail, `_spliced`; checked to coincide), `construction.row_bus` and its measurements on the published outline (the flat lanes, the relative narrow tip, the shared level); with one side the flank without lanes convex from the field's outline corner down to the tail (`_convex_flank`, the plan's section 27.8: the Column fan-out's notch below that corner bridged, every corner 5 degrees or more, the tails' roots and the copper untouched); the pair is built once per design (a small cache) |
| `engine/profile.py` | profile loading and consistency checks (the `order` block included), `fabrication_minimum()` (JLC's trace minimum of the profile's copper), `order_requirements()` |
| `profiles/jlc_fpc_standard_v1.json` | the locked profile, with its JLCPCB, connector and reference sources |
| `exporters/direct_gerber.py` | Direct Gerber ZIPs with `ORDER_NOTES.txt`, review bundle, regeneration binding, read-back; for masked builds (masked-field phase P3) the polygon field window as a GTS region, the form checks of polygon openings, the taxel-field order note, `taxels.csv` and the review manifest's `taxel_map`, all read back; for a diagonal Row bus (phase P5c) `taxels.csv` always (every position active without a mask, and then no taxel-field note), the folded Row pins from the pads, and the review manifest's `diagonal_row_bus` (`construction.row_bus`, `tail.row_contact_order` with the pins of those contacts, its stacked tails since diagonal-bus/3) read back against `pinout.csv`; since P5d the Row board's `ORDER_NOTES.txt` states its folded pins, read back ("one side" for a one-sided bus since the P5d/P5e repair) |
| `exporters/ipc356.py` | IPC-D-356A writer and strict reader |
| `exporters/easyeda_pro.py` | the EasyEDA Pro projects ([EASYEDA_EXPORT.md](../docs/EASYEDA_EXPORT.md)): one native `.epro2` per board in a separate `{build_id}-easyeda-pro.zip` (route `/api/export/easyeda-pro`): tracks, `RECT` pads with their nets through archive-local footprints, devices and a schematic channel, coverlay `FILL`s on layer 5, the outline and cutouts on layer 11, `FPC_FILL` PI stiffeners on layer 59 with the profile's thickness, FPC mode, the board's own DRC rules; the environment records of the user's JLCEDA exports (`easyeda_pro_template.json`); read back against the layout; `tools/compare_easyeda_gerbers.py` compares EasyEDA's Gerbers with ours |
| `web/index.html`, `web/app.js`, `web/styles.css` | the browser UI (no framework); `app.js` dispatches `fpc:result` / `fpc:cleared` for CAD mode; the form's Row traces select (`routing.row_sides`, shown and sent on both templates; on the generic template the form's bounds, badge and locked rules follow it: the bus's rule set, `profile.row_bus`, or the straight channel's own bounds, each limit's `channel`) and the stacked view's note on a diagonal Row bus (the stacked tails, the top FPC's over the bottom FPC's and their overlap, the Row pins by pin from the pads, its lengths to three decimals); the stacked view's pin-1 rings in the boards' colours, moved apart where they would clash, each still round its own triangle (P5-diagonal-bus.md sections 27.3-27.5), both drawn above both boards in an overlay (section 27.8), each as its board's ring lies on screen (section 27.9); the masked badge for a masked field only (not a bus's full field) |
| `web/backend.js`, `web/py/` | the page's one door to the API, `apiFetch` (`fetch` under `app.py`; in the static site a Web Worker, `py/worker.js`, running `app.answer` in Pyodide through `py/bridge.py`) |
| `web/cad/` | CAD mode in the browser (ES modules): mode switch, steps, `/api/surface/*` calls, the three.js viewer and picking, STL parsing for display; the Containment and Row traces selects (phase P5e: Field only, the default; no Field shape, Board rules or Largest rectangle since the plan's section 26.16: the field follows the selected area), the proposal card (tip, bands, the Row pins by pin, where the tails end, each board's share on the surface, overhang), the Tip column, the flat view's boards dotted off the surface, large dark markers where a board leaves the surface in 3D and a note under the view, the map's routing report with its advice and the Row pins by pin; since the P5d/P5e repair a changed option makes the proposals stale (Generate waits for a new fit), one map request at a time, the disabled controls' reasons, the CSV's readout rows for a masked field only, the shortfall of proposals explained |
| `web/vendor/three/` | vendored three.js 0.186.1 (MIT): `three.module.js`, `three.core.js`, `OrbitControls.js` (its bare import patched), `LICENSE`, `NOTICE.md` with the SHA-256 of each file |
| `surface/` | CAD mode (stdlib): `mesh` (STL, weld, orientation, covered walls), `select` (replayable operations, presets), `chart` and `solve` (projection, rigid unfold, band seam, LSCM+ARAP), `fit` (base sides, rotation, raster search on the engine's plans, strain-limited disks), `fill` (Whole board's masked fields (CAD mode's only shape since the plan's section 26.16, which removed `shape: rectangle`, the generic template and the rectangle preference from CAD mode; `fit.CAD_ONLY`): masked fields of the straight construction classes, within the rectangles' caps (`max_rows` x `max_columns`; 32 x 32 before the plan's section 21) and a named reader's lines, on an exact free space, each role mapping searched on its own and the lattices independent of the placement option, merged with the rectangles, peeled and re-ranked, one mask per readout and no dominated proposal; masked-field phase P4 and its reviews' fixes), `fieldfit` (the fit option `containment: field`, phase P5d, the default with `shape: fill` from P5e: only the taxel field F on the surface, every proposal a diagonal Row bus with the option `row_sides`; the exact largest row- and column-convex field per lattice by a DP with window and quadrant bounds, the full rectangles, the pruned phase search, a turned field only with 3 % more taxels, the narrow tip within 3 taxels with several exits, the tails sized to the surface below them, F checked exactly and peeled, the routing's share on the surface and overhang, and the map's records with the routing report and its warnings; the P5d/P5e repair: the unturned search first and never pruned by a turned field, phase 0 on the usable edge and the quarter phases on every exit, a lattice larger than the caps searched whole first, the phase-aware early exit, the deterministic work budget `WORK_BUDGET`, every frame tried listed, the narrow tip choosing the exit, both tails ending on the nearest line across the boards on which each is at least the shortest tail long and ends at least the extension past the edge under it (P5-diagonal-bus.md sections 27.3 and 27.4), the overhang without the tails, the fillet's and the base edge's bends in `W_BAND_EDGE_RADIUS`, F of a straight design; coverage first, the plan's section 21: shaped fields within the rectangles' caps; tip first, section 26: within 3 % of an exit's most taxels the field reaching nearest the fingertip first, the field it displaces after its own zero-cost tie, reach first since 26.16), `reader` (the fit option `reader`: 16x16, 32x16 FlexiTac, 32x32, 48x48, auto; the tails' pins, the walk's caps, the reader the metrics and the map name, and the lines and frame index of each taxel), `place` (taxel map, overlay, wrap template, verification; a masked field's active crossings, `readout` and `taxel_mask_matches_design`; a map without `containment` takes the design's: `field` for a diagonal Row bus; the readout's `row_pin_order` from the pads), `api` (the routes, framed bodies, mesh cache), `errors` |
| `profiles/jlc_fpc_surface_v1.json` | the locked profile of the `surface_matrix_v1` template (CAD mode's tight geometry policies) |
| `tests/` | the stdlib unittest suite (below) |
| `tools/` | `mutation_check.py`, `golden_values.py`, `build_static_site.py` (the static site), `browser/` (Playwright checks) |
| `docs/` | API, layout schema, integration, exporter, plan, historical record, CAD mode and its plan |
| `outputs/` | git-ignored scratch directory for CLI exports; the application stores nothing |
| `claude/` | this handoff, `verification/` (reviews and the audit), `sessions/` (dated notes) and `specs/` (feature specs and their logs) |

## Contracts

- **Input**: `tactile-fpc-design/v1`, strict; aliases, precedence, the
  normalization report and the JSON Schema with its three documented engine
  leniencies are in [API.md](../docs/API.md).
- **Result and layout**: `tactile-fpc-layout/v3`, anchored rectangles, NC
  contacts, the tail and fan-out route pieces, the 30 DRC records, the
  registration record and the issue catalogue are in
  [LAYOUT_SCHEMA.md](../docs/LAYOUT_SCHEMA.md).
- **Identity**: `build_sha256` = SHA-256 of canonical `{design_sha256,
  profile_sha256, generator, exporter}` (plus `template` on the surface
  template and `mask` for a field mask), `build_id` = slug + 12 hex digits;
  generator `deterministic-sensor-core/0.4.0`, exporter
  `direct-gerber-pure-stdlib/0.3.0` (both since the necked routing of
  2026-10-15, which changed every build id).  Bumping either version changes
  every build id, deliberately.  The order-requirement wording
  (`engine.profile.order_requirements`) is engine code that reaches the
  archives but not the identity: a change of it needs a generator-version
  bump, or one build id names two sets of archive bytes (the golden digests
  notice; the build id does not).  A profile change changes the profile
  digest, and with it every build id; bump the profile `revision` too, as
  `ORDER_NOTES.txt` and the manifests quote it.
- **Exports**: board ZIP and review-bundle members, the regeneration binding,
  `build_exports(result, cache=)`, determinism, the order requirements and
  the JLC review items are in
  [PHASE2_DIRECT_GERBER.md](../docs/PHASE2_DIRECT_GERBER.md).
- **Ordering**: order each board as a 1-layer, 0.11 mm FPC with 1 oz copper
  and a 0.225 mm PI stiffener at the contacts, a +/-0.05 mm outline
  tolerance (a special request) and ENIG, and check that the 0.3 mm gold
  fingers come out within +/-0.05 mm (JLC's trace tolerance is +/-20%).
  On the order form, Gold Fingers is Yes with Gold Fingers Thickness 0.3 mm,
  the stiffened contact zone in total (profile revision 2026-10-29: JLC gives
  it the highest priority when it chooses the stiffener under the gold
  fingers).  `engine.profile.order_requirements(profile)` resolves these
  entries (with the contact-zone, contact-start, contact-window and
  coverlay-window notes; each board's lines of `ORDER_NOTES.txt` name its
  coverlay windows and those longer than JLC's general 20 mm) from the
  profile for `ORDER_NOTES.txt`, the manifests and `/api/default`; the
  wording and the sources each entry cites are in that function, the
  figures and the source texts in the profile.
- **Integration**: pin 1, channel order, the stack, the assembly preview and
  the reader connectors are in [INTEGRATION.md](../docs/INTEGRATION.md).
- **Interfaces between components**: `exporters.artifact_filenames(result)`
  names every download (HTTP `Content-Disposition`, CLI, review manifest);
  the SVG root's `data-view="top"` and `data-active-region` register the
  boards in the browser; `/api/default` gives the browser `profile.limits`
  (form limits), `profile.display_rules` (rule text) and
  `profile.order_requirements` (the manufacturing note).

## Locked profile

`profiles/jlc_fpc_standard_v1.json`, id `jlc-fpc-standard-v1`, revision
2026-10-15 (stage G of 2026-10-14: 0.225 mm PI, the `order` block and the
stack-up of the ordered build; 2026-10-15: the fan-out trace limits, the
finger width, JLC's trace minimum per copper thickness and 0.1016 mm
electrodes, and the fixed route-space, lane and deck-pitch rules removed).  The engine checks it on every load (`E_PROFILE_*`):
every rule must be present and positive, no design rule may be looser than
the `fabrication` capability, the rules must be mutually consistent, and the
order must be orderable and fit the reader connectors: a JLC 1-layer
thickness, copper and finish, a stack-up whose layers add up to the ordered
thickness, an outline tolerance JLC offers on request that holds the
THD0515 tail width, and a contact zone (core + copper + stiffener under the
open coverlay) within the connectors' 0.30 +/- 0.03 mm.
Its `sources` block quotes the JLCPCB flexible-PCB capabilities page (fetched
2026-10-12), the two reader connectors and the reference design.

| Key | Value | Note |
| --- | --- | --- |
| `fabrication.copper_to_board_edge_mm` | 0.3 | JLC laser outline |
| `fabrication.copper_to_slot_mm` | 0.3 | JLC |
| `fabrication.outline_tolerance_mm` | 0.1 | JLC |
| `fabrication.outline_tolerance_on_request_mm` | 0.05 | JLC, on request |
| `fabrication.gold_finger_to_board_edge_mm` | 0.2 | JLC |
| `fabrication.trace_width_tolerance_fraction` | 0.2 | JLC trace width +/-20% |
| `fabrication.exposed_pad_to_trace_mm` | 0.15 | JLC |
| `fabrication.coverlay_expansion_mm` | 0.1 | JLC |
| `fabrication.coverlay_min_bridge_mm` | 0.5 | JLC |
| `fabrication.coverlay_opening_to_trace_mm` | 0.15 | JLC |
| `fabrication.maximum_outline_short_side_mm` | 234.0 | JLC regular size |
| `fabrication.maximum_outline_long_side_mm` | 490.0 | JLC regular size |
| `fabrication.single_layer_fpc_thickness_options_mm` | 0.07, 0.11, 0.12 | JLC 1-layer finished thicknesses |
| `fabrication.single_sided_copper_thicknesses_mm` | 0.018, 0.035 | JLC single-sided copper |
| `fabrication.single_sided_copper_weights_oz` | 0.5, 1 | the same copper in oz |
| `fabrication.single_sided_min_trace_width_mm` | 0.0889, 0.1016 | JLC minimum trace width per copper: 3.5 mil (18 um), 4 mil (35 um); the ordered 1 oz gives 0.1016 |
| `fabrication.single_sided_min_trace_space_mm` | 0.0889, 0.1016 | JLC minimum spacing per copper, as above |
| `fabrication.gold_finger_thickness_tolerance_mm` | 0.03 | JLC FPC thickness tolerance, gold-finger area |
| `fabrication.surface_finish` | ENIG | JLC |
| `fabrication.pi_stiffener_thickness_options_mm` | 0.1, 0.15, 0.2, 0.225, 0.25 | JLC PI options |
| `fabrication.recommended_pi_stiffener_mm` | 0.225 | JLC: for a 0.3 mm connector on a 0.11 mm FPC |
| `fabrication.recommended_pi_stiffener_fpc_thickness_mm` | 0.11 | |
| `fabrication.recommended_pi_stiffener_connector_thickness_mm` | 0.3 | |
| `stackup.construction` | single_copper_flexible | |
| `stackup.copper_layer` | top_copper | |
| `stackup.coverlay` | polyimide | |
| `stackup.coverlay_thickness_mm` | 0.025 | coverlay PI |
| `stackup.coverlay_adhesive_thickness_mm` | 0.025 | coverlay adhesive (JLC, on 1 oz copper) |
| `stackup.copper_thickness_mm` | 0.035 | 1 oz, the copper of the ordered 0.11 mm build (was 0.018) |
| `stackup.core_polyimide_thickness_mm` | 0.025 | JLC 25 um dielectric (was 0.05) |
| `stackup.bottom_copper_placeholder_thickness_mm` | 0.001 | descriptive only, no second copper layer |
| `stackup.stiffener_side` | bottom | only bottom is supported |
| `stackup.stiffener_material` | polyimide | |
| `stackup.stiffener_thickness_mm` | 0.225 | since 2026-10-14 (was 0.2) |
| `routing.finger_trace_width_mm` | 0.254 | the tail (gold-finger) route pieces; the finger gap is 0.246 |
| `routing.min_pad_space_mm` | 0.2 | |
| `routing.min_pad_to_trace_mm` | 0.2 | |
| `routing.min_electrode_gap_mm` | 0.25 | |
| `routing.min_electrode_width_mm` | 0.1016 | JLC's 1 oz minimum (was 0.1, re-audit N4) |
| `routing.copper_to_edge_mm` | 0.3 | |
| `routing.copper_to_cutout_mm` | 0.3 | |
| `routing.active_edge_clearance_mm` | 0.75 | board margin around the taxel field |
| `routing.electrode_overhang_mm` | 0.2 | as the reference design |
| `connector.pad_pitch_mm` | 0.5 | |
| `connector.pad_width_mm` | 0.3 | |
| `connector.contact_length_mm` | 4.0 | THD0515 drawing |
| `connector.contact_tip_clearance_mm` | 0.3 | |
| `connector.contact_center_to_side_edge_mm` | 0.5 | one pitch: width (P + 1) x 0.5 mm |
| `connector.tail_tip_corner_radius_mm` | 0.3 | THD0515 drawing |
| `connector.tail_width_tolerance_mm` | 0.07 | THD0515 drawing |
| `connector.contact_width_tolerance_mm` | 0.05 | TXGA drawing |
| `connector.contact_zone_thickness_mm` | 0.3 | both drawings |
| `connector.contact_zone_thickness_tolerance_mm` | 0.03 | TXGA drawing |
| `connector.maximum_pins` | 64 | |
| `coverlay.coverlay_expansion_mm` | 0.1 | |
| `coverlay.coverlay_min_bridge_mm` | 0.5 | |
| `coverlay.coverlay_opening_to_trace_mm` | 0.15 | |
| `coverlay.coverlay_opening_general_max_length_mm` | 20.0 | JLC's general length of one opening (its FPC design rules); the order notes name the longer windows, nothing refuses them |
| `tail.minimum_length_mm` | 7.0 | |
| `tail.stiffener_length_mm` | 6.0 | connector drawings: 6.00 mm thick zone |
| `tail.stiffener_end_clearance_mm` | 0.5 | product default |
| `outline.outline_fillet_radius_mm` | 0.5 | |
| `outline.arc_segment_max_angle_deg` | 10.0 | |
| `outline.maximum_unfilleted_concave_turn_deg` | 15.0 | |
| `outline.offset_allowance_mm` | 0.001 | |
| `fanout.maximum_channels_per_lane` | 16 | |
| `fanout.maximum_lanes` | 2 | |
| `fanout.slot_width_mm` | 12.0 | |
| `fanout.minimum_slot_width_mm` | 4.0 | |
| `fanout.slot_height_fraction` | 0.3 | |
| `fanout.minimum_slot_height_mm` | 1.5 | |
| `fanout.maximum_slot_height_mm` | 4.0 | |
| `fanout.lane_to_slot_clearance_mm` | 0.75 | |
| `fanout.maximum_taper_angle_deg` | 60.0 | bus-style diagonals (both boards) |
| `drc.numeric_epsilon_mm` | 1e-06 | the only DRC tolerance |
| `limits.minimum_rows` | 1 | |
| `limits.maximum_rows` | 64 | |
| `limits.minimum_columns` | 1 | |
| `limits.maximum_columns` | 32 | |
| `limits.minimum_pitch_mm` | 0.6 | |
| `limits.maximum_pitch_mm` | 10.0 | |
| `limits.minimum_trace_width_mm` | 0.1016 | fan-out traces: JLC's 1 oz minimum |
| `limits.maximum_trace_width_mm` | 0.254 | the finger width |
| `limits.minimum_trace_space_mm` | 0.1016 | JLC's 1 oz minimum |
| `limits.maximum_trace_space_mm` | 0.246 | the finger gap (0.5 - 0.254) |
| `limits.maximum_tail_length_mm` | 80.0 | |
| `limits.maximum_outline_short_side_mm` | 234.0 | |
| `limits.maximum_outline_long_side_mm` | 490.0 | |
| `limits.high_fill_factor_warning` | 0.8 | |
| `limits.large_matrix_warning_taxels` | 1024 | |
| `limits.maximum_project_name_length` | 80 | |
| `order.fpc_layers` | 1 | |
| `order.fpc_thickness_mm` | 0.11 | JLC 1-layer option |
| `order.outline_tolerance_mm` | 0.05 | a special request |
| `order.surface_finish` | ENIG | |
| `order.reference_contact_window_margin_mm` | 0.051 | the JLC-accepted reference's contact openings |
| `order.reference_field_window_length_mm` | 63.373 | the JLC-accepted reference's longest field window (23.368 x 63.373 mm, its GTS) |

## Default build

`default_design()` (12 x 32, pitch 2.0 mm, 1.4 mm electrodes, tails 12 mm
top / 12 mm bottom since P5-diagonal-bus.md section 27.7, ending together
(7.5 mm bottom before), both tails at the bottom, rows on top, ascending,
0.127 mm fan-out traces at 0.127 mm spacing, the diagonal Row bus with
`both`: the generic default since P5-diagonal-bus.md section 18,
`diagonal-bus/8` with CAD mode's rule set, one outline down to the tail
roots and the Column V at 80 degrees since section 20, `diagonal-bus/9`
since section 24, the same boards, `diagonal-bus/10` since section 27, the
Row tail 0.048 mm east, on the field's centre line, `diagonal-bus/11` since
section 27.8, the same boards) gives build
`tactile-fpc-12x32-c2243ebd10c5` with no error or warning (with
`routing.row_sides` `channel`, the straight Row channel, the boards of
before, byte for byte, its bottom tail 7 mm).  Values per
board (`—`: the board has no such key):

| Board value | Row | Column |
| --- | --- | --- |
| `id` | top_rows_fpc | bottom_columns_fpc |
| `metrics.outline_width_mm` | 67.919595 | 67.919595 |
| `metrics.outline_height_mm` | 41.765841 | 41.765841 |
| `tail.length_mm` | 12.0 | 12.0 |
| `tail.width_mm` | 6.5 | 16.5 |
| `tail.connector_pins` | 12 | 32 |
| `grid_registration.active_region.width` | 63.4 | 63.4 |
| `grid_registration.active_region.height` | 23.4 | 23.4 |
| `metrics.coverlay_opening_count` | 2 | 2 |
| `metrics.routed_cutout_count` | 0 | 0 |
| `construction.fanout_bundle_pitch_mm` | 0.254 | 0.254 |
| `construction.merger_taper_angle_deg` | — | 0.0 |
| `construction.channel_width_mm` | — | — |
| `verification.checks.route_route_clearance.measured_mm` | 0.127 | 0.169721 |
| `verification.checks.route_route_clearance.finger_section.measured_mm` | 0.246 | 0.246 |
| `verification.checks.route_width.measured_mm` | 0.0 | 0.0 |
| `verification.checks.pad_trace_clearance.measured_mm` | 0.223 | 0.223 |
| `verification.checks.copper_to_outline.measured_mm` | 0.3 | 0.3 |
| `verification.checks.route_to_outline.measured_mm` | 0.300999 | 0.364499 |
| `verification.checks.copper_to_cutout.measured_mm` | null | null |
| `verification.checks.stiffener_end_clearance.measured_mm` | 5.5 | 6.0 |
| `verification.all_checks_passed` | true | true |

Generation of the default takes about 0.1 s on this host (the DRC used to
take 1.1 s).  The three archives and their digests are in
[PHASE2_DIRECT_GERBER.md](../docs/PHASE2_DIRECT_GERBER.md#determinism);
`tests/test_golden_default.py` pins all of these values.

## Tests and tools

The suite is stdlib `unittest`: 963 tests in 45 modules (2026-10-30, with CAD
mode, the surface template and their three reviews, and phases P1, P2
(the builders, the DRC and the registration, and the fixes of their reviews), P3 (the exporter) and P4 (CAD mode's masked fields and readers, and the fixes of its reviews) of the masked field, and phases P5a (the diagonal Row bus's primitives), P5b (its construction, DRC and contract) and P5c (its exports), and the fixes of the P5 reviews, and P5d (CAD mode's field-only containment and the P5c carry-overs) and P5e (the browser's Containment and Row traces, and field-only containment the default), and the fixes of the P5d/P5e reviews, and the Row bus's tail redesign, diagonal-bus/2, and the fixes of its review, and its stacked tails, diagonal-bus/3, and its one outline over the field, diagonal-bus/4, with the lanes off the Column copper and following a receding field, and its regular outlines, diagonal-bus/5, and the corner tolerance, the rectangle preference and the chamfered notches, diagonal-bus/6, and the straight sides at the tip, diagonal-bus/7, and the diagonal Row bus as the rectangular generator's default, the plan's section 18, and the rectangular generator's bus as a subset of CAD mode with one outline down to the tail roots and the Column V at 80 degrees, diagonal-bus/8, sections 19-20, and the fixes of its review, and coverage first, section 21, and CAD mode's border of the taxels, docs/CAD_BORDER.md, and symmetric sensors on symmetric faces, section 22, and the caps keeping the exit, section 23, and the corner tolerance at every convex corner with the convex sides, section 24, and the EasyEDA Pro projects, docs/EASYEDA_EXPORT.md, about 5 s, and the taxels from the fingertip, section 26 (the rectangle's cap order, the exact filler band, tip-first fields and rectangles), about 75 s, and its round 2 (the lead's zero-cost tie, the tip-zone guard, `tip_first: false` as the ties alone, the rectangles' 80 % floor and column guard), about 30 s, and its round 3c (reach first, the tip-zone guard gone; CAD mode without rectangles, its rectangle and rectangle-preference tests gone, the removed options refused), and round 3c's review and the user's decision of 2026-10-27 on symmetric faces, section 26.17 (the lead's tie in the lead's place, the displaced field's rank and the taxels given, saved placements' removed options, symmetric faces' symmetric fields first, the symmetric tip share, T0's slack and ties, the pass's floor), and round 4's review, section 26.18 (every exit of the fit without the caps searched on its own when the proposals reach it, a symmetric group's eighth row phases and its slack, the taxels given from the lead and its pass, saved placements' generic-template options, the tie's place and peel at their edges), and the Row tail centred on the field, section 27, diagonal-bus/10, and the user's threshold of 20 % on symmetric faces, section 26.19, and one side's convex flank, section 27.8, diagonal-bus/11, and the profile revision 2026-10-29: the gold-finger thickness order option and the coverlay-window notes, and the coin for scale's vendored photo, and CAD mode's vendored default part and its shipped fit, and the static site: `app.answer`, the worker's bridge and the site build), about 66 s on Python 3.12 on this host before the masked
field's guards, which add about 22 s, its P2 DRC tests about 10 s more, its P3 export tests about 2 s, its P4 fit tests about 30 s, the P5a bus tests under 1 s, the P5b diagonal-bus tests about 16 s with the P5 reviews' fixes, the P5c export tests about 2 s and the P5d field-fit tests about 35 s (53 s on 3.9), P5e's under 2 s more, the P5d/P5e reviews' fixes about 30 s (the whole suite took 149 s on 3.12 on 2026-10-21 before P5d; 273 tests took 65 s on 3.12, 76 s on
3.9 and 67 s on 3.13 on 2026-10-15).  Branch coverage measured with coverage.py on 2026-10-15: 93%
overall (`app.py` 94%, `engine/core.py` 97%, `engine/drc.py` 96%,
`engine/layout.py` 97%, `exporters/direct_gerber.py` 92%; `cli.py` 63%
because its tests run it as a subprocess).

```bash
PYTHONPATH=. python3 -B -m unittest discover -s tests
```

| Module | Covers |
| --- | --- |
| `test_core` | the original engine regressions, updated for layout v3 |
| `test_geometry_column`, `test_geometry_connector`, `test_geometry_profile` | Column outline and fan-out, body-side steps, tails and contacts, profile rules and limits (E, T) |
| `test_geometry_bundle` | the necked routing of 2026-10-15: two route pieces per net with their widths, straight bundle sections exactly one bundle pitch apart, parallel diagonals, every gap and the finger-section gaps on every design (against the DRC's `finger_section`), the width change below every bend in the tail, the Row channel and expansion, the bend stagger and every diagonal within the bus angle and the cap, the shortest ones included; the `routing` inputs, ranges, aliases, schema and form |
| `test_geometry_drc` | every DRC rule on mutated layouts, exact counters, the finger-section spacing of route pairs with a tail piece, registration, feasibility, speed and determinism (E) |
| `test_direct_gerber_export` | the C1 read-back of the emitted GTL/GTS/GKO in every orientation, archive structure (C1, X) |
| `test_export_readback`, `test_export_artifacts` | exporter self-check against tampered emissions and results, stiffeners, netlist, pinout, names, archive metadata, bundle (X) |
| `test_api_normalization`, `test_api_schema`, `test_api_identity` | strict input, schema contract, identity and cache, browser payload guard (A, T) |
| `test_api_svg` | copper-side top views (A) |
| `test_api_http` | the HTTP server in-process on ephemeral ports: routes, malformed requests, Host/Origin/Content-Type, `--allow-host`, limits, timeouts, the 16-build cache (A, T) |
| `test_api_cli` | `cli.py` as a subprocess, batches and their exit status (A, T) |
| `test_export_gold_fingers` | the gold fingers measured on the emitted GTL, GTS, GKO and GBSL: pitch, outer contact centres, tail width, 0.30 x 4.00 mm contacts from 0.30 mm, R0.30 corners, the contact window and the flush 6.0 mm stiffener, for 12/16/32 pins, NC contacts and every tail side (G) |
| `test_export_order_requirements` | the profile's `order` block and its checks, the resolved order requirements, `ORDER_NOTES.txt` in every ZIP (with each board's trace widths and what JLC's tolerance makes of them), both manifests, `/api/default`, the browser note and the exporter's read-back of the notes (G) |
| `test_golden_default` | golden identity, geometry, DRC measurements and archive digests of the default build, the diagonal Row bus since the plan's section 18 (T); its straight Row channel keeps the golden layout and boards of before |
| `test_chirality` | pin 1, `ROW_01`, `COL_01` and the tails on every side and role mapping, in the layout, the emitted Gerbers, netlist and pinout, and the stack view (T) |
| `test_negative_drc_flow` | one injected defect per DRC code through `generate_design`, the exporter, HTTP and the CLI (T) |
| `test_surface_mesh` | CAD mode's STL input (`surface/mesh.py`): binary and ASCII, padded files, units, bad files; welding, outward shells (inside-out, open shells wherever they sit, cavities), covered walls, T-junctions; repeated triangles and fans on one edge stay fast |
| `test_surface_chart` | selection (presets, growth, operations, the bend barrier at any tessellation and at creases) and flattening (planar, unfold, LSCM+ARAP; inside-out files give the same chart; one hole kept whole; bands opened; pieces refused; T-junctions on flat, folded and curved patches) |
| `test_surface_fit` | the fit (the soft-finger replica's 44 x 8, the whole board's full rectangle (shape rectangle's before section 26.16), and its masked 50 x 12 = 470 with `containment: board` (masked fields within the rectangles' caps, section 21), its default field-only 59 x 12 = 708 on the diagonal Row bus (phase P5e), the crank pad's 683 (34 x 34; 666 before section 21) against the board fit's 546, `max_area` with either containment, the overlay below an arc exit's chord, options (the removed CAD options refused) and their documented table, determinism, FlexiTac, cylinders, arcs, domes, bends, straight sides next to fine corners, the exit crossing's clearance, one proposal per shape) and the map (taxels, chirality of a rectangle's and of a masked field's map, reader lines from pins, mismatches, a masked design mapped only with the placement fitted for its mask, damaged placements, board clearance, tail reach, spacing along curved surfaces) |
| `test_surface_http` | the `/api/surface/*` routes: framing, 413/415/405/403, every bad value a 422, the header's long numbers, CAD mode's own slot, meshes beyond the JSON limit, the unit through the cache, the 413 of a body just over the limit, `/api/default?template=`; a rounded plate's fit and map, the removed CAD options refused (shape rectangle, the generic template, a rectangle preference) and a saved placement naming them mapped, `tip_first` |
| `test_surface_cli` | `cli.py surface` as a subprocess: the files of `fit --out`, `map` with the placement's selection and `--options` over the placement's (F's records by default, the board's with `containment: board`), exit statuses, NaN picks, invalid JSON, `--unit`, `--base N`; the removed CAD options refused by `fit` and a saved placement naming them mapped |
| `test_surface_contract` | contract details the API review found untested: mesh caps and units, hidden seeds, the operation cap, partly covered walls, unknown keys, error details, the header cap, and what each fit option does on a face with a block standing on it (placement, rotation, objective and side with either containment; the tails' reach with either containment) |
| `test_surface_web` | static checks of `web/cad/` and the vendored three.js: digests, the CAD hook events, no fetch patch, the fit options and limits copied from the server; no Field shape, Board rules or Largest rectangle control (section 26.16) |
| `test_static_site` | the static site: `app.answer` equal to the server's replies byte for byte (routes, exports, a surface route, the error replies), only `/api/` and the body limits, the build cache; the worker's `bridge.handle` (its 500s); the site build: the page's policy and backend flag, relative URLs and `apiFetch` only, a reproducible and complete `engine.zip` (it answers from its own files), the Pyodide archive's SHA-256, only an earlier build replaced; the public copy (`tools/export_public.py`): every file its documents link to and the site needs, none of the private notes, the commit's files only, only an earlier export replaced |
| `test_template_surface` | the surface template `surface_matrix_v1`: profile and policies, dispatch and limits, identity, a DRC-clean sweep, the footprint, exports and pinned values |
| `test_generic_identity_guard` | 200 seeded generic designs keep their builds byte for byte (`tests/fixtures/generic_builds.json`, written before the surface template and rewritten by the plan's section 18, the bus the generic default, and section 20, the bus built with CAD mode's rule set (`diagonal-bus/8`): the 75 bus requests' ids and boards, of which 37 build and the rest are refused by the 7.5 mm tail minimum, the 125 channel ones byte for byte; and by section 24, `diagonal-bus/9`: the 75 bus requests' ids, manifests and the 37 layouts, verdicts and codes held; and by section 27, `diagonal-bus/10`, the Row tail centred: the same, and one size refusal's report, which quotes the outline); under `routing.row_sides` `channel` the same requests keep the verdicts, boards and reports of before (`generic_builds_straight_channel.json`) and 8 of them every export member but the identity carriers (`generic_channel_exports.json`, from 8a4b2f1) |
| `test_surface_identity_guard` | 92 unmasked surface designs (85 seeded, aliases, partial, off-grid, rejected and oversize ones) keep their builds byte for byte (`tests/fixtures/surface_identity_baseline.json`, written from the working tree before the masked field) |
| `test_surface_fit_snapshot` | the raster search's rectangles keep their builds (build ids, metrics, outlines, field frames): since section 26.16 (no shape rectangle in CAD mode) among the whole board's proposals, all 35 recorded rectangles (5 per case) in order, on the soft finger's mount end (the replica, and the real mesh when `asset/` is present), the crank tip pad (when `asset/` is present) and three synthetic plates, `max_taxels` once (`tests/fixtures/surface_fit_rectangle_snapshot.json`; its generic-template cases kept, not run) |
| `test_mask_contract` | the field mask's contract (phase P1): each code at its field, null and full masks as the unmasked design, integral floats, the generic refusal, capped issues, the construction-class gate (phase P2), the inactive-gap warning, `mask` in the identity and the exports' identity fields, masked builds exporting from phase P3 on, the surface schema and limits against pinned pre-mask digests (without what the mask and `routing.row_sides` add), the size advice, the frames by hand and on stacked boards in every tail-side and role combination, the lane taper and the construction classes |
| `test_mask_layout` | the masked boards' builders (phase P2): full spans give today's boards byte for byte (eight designs, also turned, and on the generic profile), anchored masks keep today's routes, contacts, gang window, stiffener and tail, the lane taper's field start, electrode spans and stub ends, the polygon windows and the crossing region P (by area and containment), outlines (simple, counter-clockwise, 0.5 mm from P, following F), every DRC record and the registration passing, the masked keys, the crossings of the stacked boards in all 16 tail-side and role combinations, turned windows, the SVG, the footprint's mask block (and the fillets beside it, within their radius of its concave and tail-root corners), the class gate, pinned digests (3.9 and 3.12), no float `sum()` and no set iterated in order (checked on the syntax tree, the checker included), a 64 x 64 build under 5 s |
| `test_mask_drc` | the masked boards' DRC and registration (phase P2): the plan's corpus (right triangles, quarter disk, soft-finger taper, L shape, trapezoid, 0.6 mm tight, per-electrode windows, 64 x 64) with all 30 records and the registration passing, margin 0.5 from P, the strict window-to-trace rule (exact values), electrode exposure 0.1; tampered boards failing each masked check (P unlike the electrodes, too close or off the board, unsound or outside windows, a window touching the outline passing and one on a cutout failing, bridges to a polygon, routes beside or inside another electrode's window, an electrode outside its window, per-electrode windows); unmasked boards keeping today's semantics; the registration in all 16 tail-side and role combinations, mirrored spans, a too-long electrode, electrodes moved or widened across their length, different masks, the inactive separation (0.05 and 0.4 mm) and touching electrodes, the stack frame; the reported trace-over-trace runs (the soft-finger taper's 83.8 mm, the corpus against an independent measure, none with opposite tails, a Column trace laid on a lane); class refusals naming the first offending row or column; 200 seeded random class A+B designs; 64 x 64 under 5 s; pinned verification digests (3.9 and 3.12); no float `sum()` and no set iterated in order; the geometry helpers; the docs naming every masked key |
| `test_mask_export` | the exports of masked builds (phase P3): a right triangle (polygon windows), per-electrode windows, tails on the right with the columns on top, descending rows and NC contacts, and opposite tails; the usual members plus `taxels.csv`; each polygon window decoded from the GTS as its ring; `taxels.csv` (R x C lines, ROW-major, the mask's active positions, the nets and the pins of `pinout.csv`); the review manifest's `taxel_map` and digest; the order notes' taxel field in its place; one far-end land per trimmed electrode; no taxel map unmasked and a full mask as the unmasked build; polygon windows refused for each form defect (self-crossing, another kind, another shape, rectangle fields, an unmasked board, clockwise, off the grid, slanted, short, closed, non-finite); the read-back catching a bounding-box or moved window, a wrong taxel map (flipped, wrong pin, column-major, short, missing or unexpected) and a missing or miscounted order note; pinned archive digests (3.9.6 and 3.12, any hash seed); the documented sizes and order-note line; the HTTP export routes and `cli.py export` |
| `test_mask_fit` | CAD mode's masked fields (phase P4, `shape: fill` with `containment: board`, explicit since P5d) and readers: the reader option (choices, the `flexitac` alias, the legacy `connector`), the tails' pins per reader, `auto`, the lines and frame index of every reader, a square reader in the metrics and the map, a named reader capping the masked walk (16x16 finds what `max_rows`/`max_columns` 16 find), the metrics and the map naming the same reader (a 16 x 32 readout without a reader is the FlexiTac's); the exact free space against `check_containment` on random rectangles (holes, an obstacle, a bend; with and without an edge margin) and the tails' exit; the fill fit on the right-triangle (pinned proposals), equilateral and disk plates, the crank tip pad (549 of 30 x 33 and four more masks) and the soft finger (the masked 50 x 12 = 470 first since section 21, the 44 x 8 rectangle fifth; 32 x 12 masked within 32 rows), every masked proposal DRC-clean and mapped with every record (metrics, P as the field outline and its coverage, the wrap template's taxels), under 6 s, deterministic; a full mask's build id; the masked stack extent's taper slide; the peel and the re-ranking of a peeled candidate; one mask per readout and no proposal an earlier one dominates; the same count for every placement (the holed plate) and with `role_mapping: auto` at least what either role finds (a wide ellipse); the masked map's crossings, its mask record and readout, an edited mask refused; on the disk's and the wide ellipse's field fits with a diagonal Row bus no flat lane and the Row traces within a few millimetres of the field (3.85 / 6.15 and 3.80 / 5.27 mm with both / left; the wide ellipse's 38-row field of section 21 5.14 / 9.39 mm); the web client's mask (posted with the form, cleared by a rows or columns edit, kept through a mode switch, its server issues in the note with "Use the full field", "N of R x C"); no float `sum()` and no set iterated in order in the new code |
| `test_bus` | the diagonal Row bus's integer-nanometre primitives (`engine/bus.py`, phase P5a), by exact integer predicates of its own: hand chains and offsets at 0, 2.9, 45 and 84 degrees; seeded chains strictly convex with exact orientations, strictly descending, every point in range east of or on the chain, vertices from the input, blind to order, repeats and containers, and the mirrored frame's east chain; offsets at the distance exactly on axis-parallel segments and the distance + 2 nm on slanted ones, the exact perpendicular ends rounded away from the chain, joins on both offset lines and rounded along the normals' bisector, never nearer the chain than the distance (square joins beyond 120 degrees, steps at nearly straight joins); a keep-out's west hull holding every point at the distance from the lane and its continuation (jogs included, where a trim falls behind a short segment); onions of lanes nesting at the pitch with the continuation and the start box in the keep-out (without the continuation the next lane cuts the bend at 0.1598 of 0.2032 mm); a lane turning inward nests the next one exactly one pitch out at its turn (round the mitre it would spread), and every lane without such a turn keeps the mitred offset; the box helpers; a pinned digest of a seeded corpus (3.9 and 3.12), no float `sum()`, no set iterated in order, no libm call but `sqrt` |
| `test_diagonal_bus` | the diagonal Row bus `diagonal-bus/11` behind `routing.row_sides` (phases P5b, P5f, P5h and P5k, and the plan's sections 16, 17, 20, 24, 27 and 27.8), through `generate_design` and predicates of its own: the convex flank (section 27.8, `ConvexFlankTests`: the rule on synthetic rings, the multi-gripper video's WidowX 250 and Robotiq 3F one-sided designs and the corpora's kinds against the build without it, both sides untouched, the named corpus; `_flank_problems` in `_check_clean`: no notch below the field's outline corner on the side without the bus); the centred Row tail (section 27, `CentredTailTests`: an asymmetric field in every side mode and both role mappings, the Row tail centred on it and within it, the funnel's contacts on its centre line, not midway between the innermost lanes; a reader tail wider than the field centred, the rows at positions 1..R, no flat edge below F's bottom but a mirrored build's chord to its lanes; one side's inner flank leaving F's bottom corner on F's side and widening monotonically down to the tail's side, no edge flatter than 45 degrees; the mirrored contacts at the tail's far end from the band, beside it unmirrored; and, from the review of section 27 (27.3), the band's side taken from where the lanes leave their electrodes with four seeded reader designs on fields receding on the band's side (each reported at the wrong end when built with the side flipped), the inner flank's rule where each part decides (no step across F's bottom where the slant is 45 degrees or steeper, the slant meeting the tail's side at its hold, the side monotone below F's bottom: 31 x 2, 29 x 3, 12 x 2, the fin's 59 x 12 and the fine corpus's first design one-sided), and one side's lanes over straight Column copper, 5.667 and 5.529 mm, within the re-bounded 5.7 mm); the convex sides (section 24: no dent of a side from its tip corner to its widest point at most a two-cell step deep on any build, `_convex_problems`; against the build without them the old outline inside the new one, the new within the bound, the copper, the widest and the narrow tip kept, the changed cases pinned; the rule on a synthetic ring: the crank's kink bridged, a deeper pocket and an anchored dent kept); the Column V capped at 80 degrees where that roots the tails no deeper (each named build byte for byte the capped or the uncapped one, whichever roots the tails higher, ties (equal on the layout grid, as the construction's) capped; the fans at 85 where capped, one-sided too since the Row tail is centred); the straight sides (each side from the tip corner down to its widest point, and from there to F's bottom, one line wherever our own enclosing line within 1.0 mm exists, else unchanged; the old outline inside the new one, nowhere more than 1.0 mm outside it; the copper, the outlines more than 1.0 mm below the level, the widest and the relative narrow tip kept; on the named corpus, the regressions and the user's cases, the r4 plate's, the soft finger's and the crank's tip corners and vertex counts pinned, and the rule on a synthetic ring, its bound measured to the outline as filleted on a synthetic staircase); the shared outline's regressions (`tests/fixtures/diagonal_bus_shared_regressions.json`: the judge's one-sided masked fine-pitch designs, whose side over the Column board's staircase is one straight line with 74e90cd's tip, and designs whose Row tail is flush with the shared side, which meets the tail's edge on the level straight or at a filleted corner); regular outlines on every build checked (no vertex above its tail's tip corners, on and below the shared level too, turning by under 5 degrees but on a fillet, by circles of the fillet radius and its halvings; on and below the level a single-step arc's convex partner a flat vertex, but where the other board runs on below the level through it), each outline containing the one built without the regularization to the fillets' steps with its copper and relative narrow tip, the user's CAD fits' vertex counts (crank 325 -> 89) and the named corpus's tip and widest growth pinned, the regularization on synthetic rings (a bent edge, a roof, anchors, a 100-gon); the named corpus (rectangle 32x12, soft finger 59x12, and the crank, equilateral and disk masks of `tests/fixtures/diagonal_bus_masks.json`, at 2 mm, 4 mil, rows on top) with `both`, `left` and `right`: every DRC record, strict record 14, route-route at the trace space, the registration's stack keys (the tails on one side and their overlap), and our own: the fans' crossings with the Column copper at 5 degrees or more (a band beside the field may cross a raised Column stub at any angle), at most two bends per Row and per Column trace below its field and each trace straight down into its tail, no trace part over the other board's electrodes or field window, Row-on-Column runs of 5.7 mm at most off the stacked contact columns, both tails centred on the field (the Row tail within a nanometre in every side mode, its contacts the tail's positions 1..R, at its far end from the band where mirrored), the narrower lying wholly on the wider; pinned tips, widths, Row and Column roots, areas above them, the tails' overlap, the Column board's width and the bands, the bands never farther out than diagonal-bus/1's by more than 0.15 mm at any row but where the shared outline takes the Column board's own body, beside a field that does not recede never farther in either, and its tip never narrower (`tests/fixtures/diagonal_bus_v1_bands.json`), beside the receding disk the Row traces within their bundle and 1.5 mm of an electrode, the two outlines one over the field in the stack (our own clip and vertex sets) and the Row roots with both far shallower, never deeper than diagonal-bus/2's but by the entry-angle guard's allowance; `construction.row_bus` against the outline (the fans off the Column entry angle), its relative narrow tip and its flat lanes against predicates of our own (the rectangle's lanes leave at 16.7 degrees; no flat lane on the named corpus); the funnel (its near and far contacts parting on the field's centre line, half a contact pitch east of it with an odd row count) and one side's single inward fan under the field; the Column board the straight one's copper of the same design without `routing.row_sides` under the shared outline, field for field (from the active region's corner) but its classes, an unmasked design's masked records, its outline and the shared level, and its archive's members; the shared outline down to the tail roots (`tests/fixtures/diagonal_bus_shared_outline.json`: on the named corpus, 19 regressions of the judge's corpus and the user's CAD fits both boards' copper and their outlines more than 1.0 mm below the level are those of each board built with its own outline at that level; the union down to the tails' roots, both tails leaving its bottom edge, the shallower root moved down with its tail as long below it; outlines that differ above the roots fail the registration); the sides seen from outside the stack in both role mappings and the Row tail centred on the Column tail, and the same with the tails on the top, left and right (seen with the tails down; the tails, the record and every stack key as with bottom tails, and the turned bundle exports with the stacked tails); the folded contact order on the pads with `channel_order` and NC contacts; 100 seeded random designs, 30 at fine pitch (W_STACK_TRACE_WINDOW counted), reader tails of 16-64 pins (NC at the far end), narrow and tiny fields, 0.2 mm traces and 1.25 / 0.8 mm, and the regression designs of the design workflow judge and the review (`tests/fixtures/diagonal_bus_regressions.json`: Row roots within 1.0 mm of diagonal-bus/1's, where the prototypes went 50-113 mm deep, or within its noted allowance, and no deeper than diagonal-bus/2's but by rv:186's noted allowance and, one-sided, the centred Row tail's measured cost; the bands and tips of the onion, mirrored reader tails, tail sides slanting from above the field, thin rows clear of the Column windows; the Row tail centred on every one); the stack keys on edited pairs (stacked tails moved aside, widened or lengthened under the other board register, tails on two sides fail, outlines that differ over the field or a Row board without the shared level fail (a Column tail tip moved does not), crossings and a run on a Column trace outside the field reported only, a trace over a Column electrode, one over three counted once and failing without the Column openings, a trace over the Column field window only and the same between per-electrode windows, a warning) and the DRC gate; the codes (E_ROW_SIDES, E_ROW_BUS_TAILS for opposite tails only, a quarter turn E_TAIL_SIDE_PARALLEL alone, E_UNKNOWN_FIELD on the generic template, no E_MASK_ROUTING, E_ROW_BUS_INFEASIBLE, the fans' clash check, the raised corner where the lanes cannot turn down on the field's edge), the identity extra and the exporter's identity fields, the schema and catalogue; the pair built once; a pinned digest (3.9 and 3.12, any hash seed), no float `sum()`, no set iterated in order (the construction, the registration's stack keys and the field's contract), no `hypot` or `dist` |
| `test_generic_bus` | the diagonal Row bus in the rectangular generator, a subset of CAD mode (the plan's sections 18-20, `diagonal-bus/8`; `diagonal-bus/9` since section 24, `diagonal-bus/10` since section 27): the equivalence (on the named generic corpus, the default, the user's 13 x 32, 16 x 16, 32 x 32, 12 x 32 with 32- and 64-pin connectors, every tail side, the Row FPC at the bottom, scan reverse, with both, left and right, and a seeded random corpus of 40, the generic build equals the surface-template build of the same design but for the identity: boards byte for byte, issues, profile, manifest), every build through test_diagonal_bus's predicates (DRC, registration, Row and Column bends, stacked tails, one outline down to the tail roots, regular outlines, straight sides, the narrow tip), one Column lane without a slot, the fans at 60-85 degrees off the V's entry by the guard, the V at 80 and the fans at 85 on the named corpus in every side mode (one-sided too since the Row tail is centred; 82 one-sided before); the rule set (0.5 mm margin, 64 columns, 7.5 mm tails and the 7.5 mm default bottom tail; the channel's 32 columns, 7.0 mm tails and its own default; the generic profile refused for a bus design and the surface one for the channel); the channel kept (generic profile, two lanes and the slot), the default's figures, the folded Row pins in the exports, a digest equal on 3.9.6 and 3.12 and with any hash seed |
| `test_diagonal_export` | the exports of a diagonal Row bus (phase P5c): both sides with ascending and descending Row pins and NC contacts, each one side (one mirrored) and a diamond mask outside the straight classes; the members of a masked build; `pinout.csv`, the netlist's `J1` records and `taxels.csv` with the folded Row pins (computed by hand: 9 rows with `both` on pins 1, 9, 2, 8, 3, 7, 4, 6, 5), the far-end lands of the odd and even rows at opposite ends; every position active without a mask and no taxel-field note; the review manifest's `diagonal_row_bus` against the boards (the stacked tails; no stub drop, shift or neck), the identity extra in both manifests and the recipe, `derived-layout.json`; the read-back catching an unfolded pinout, a record that disagrees with the construction or names a row twice, and a missing taxel map; tampered contact orders refused; pinned archives (3.9 and 3.12, any hash seed); four straight-channel builds' archives pinned as they were before the phase; the figures LAYOUT_SCHEMA, PHASE2 and INTEGRATION quote; the order notes' folded Row pins (phase P5d: on the Row board's notes only, computed by hand, the read-back catching them missing or unfolded); the HTTP export route and `cli.py export`; "one side" in a one-sided bus's order note (the P5d/P5e repair) |
| `test_field_fit` | CAD mode's field-only containment (phase P5d, `containment: field`, `surface/fieldfit.py`): the DP of the largest row- and column-convex field against brute force (the definition) and a reference DP of our own on larger grids, with the filler rows, caps, thresholds and early exit; the full rectangle; the lattice, window and quadrant bounds never under the best field (a 9 x 9 grid with its centre blocked: 56, bound 76 and 56); the lattice against the exact free space (sparse pitches' filler bands); the caps per reader (shaped fields and rectangles alike since section 21) and the pitch ladder; the rank (a turned field with 3 % more taxels: the equilateral plate keeps its unturned 333 against 339 turned 30 degrees, and maps the turned one without the threshold; with several exits the narrowest tip within 3 taxels: the crank pad's 666 on its 70 mm leg under a 14.5 mm tip against 669 on its cut corner, 683 against 686 since section 21); the plan's targets (soft finger 708, with 48x48 620 turned 30 degrees since section 21 (576 before), 384 with 32x16; crank pad 666 (683); right triangle 559, equilateral 333, disk 436) and never worse than `containment: board`, every proposal DRC-clean, registered, its F inside the surface by our own check and mapped with every record passing (`field_clearance`, `strain_under_field`, F's bend, the tails' reach beyond the surface, the readout's `row_contact_order`, the routing report against the fit's), the holed plate's routing over its hole and the plates' square edges (`W_ROUTING_HOLE`, `W_BAND_EDGE_RADIUS`), reader caps, `row_sides`, columns on top, the tails; the map refusing F beside the surface and across the exit, and board containment refusing the proposal; the options; the peel; `field_footprint` and `E_BOARD_SIZE` on the diagonal boards (64 x 8 at 7.22 mm, the advice built); the cost against the board fit (a ratio); pinned fingerprints (3.9 and 3.12, any hash seed); no float `sum()` and no set iterated in order; phase P5e: field-only containment the default with `shape: fill` (the same proposals as an explicit `field`), a map without `containment` taking the design's, and the web client (the Row traces posted with the form on the surface template only and set from every applied design, the Containment and Row traces selects and their sync, the proposal card, the flat view's clip); the P5d/P5e reviews' fixes: an unturned lattice pruned by unturned fields only, every turned proposal 3 % over the exhaustive unturned optimum and rotation none's top found exactly (the triangle, the equilateral at 2.5 and 3 mm, the parallelogram's 105 against its 107 turned), narrow strips and small plates never worse than the board fit and phase 0 on the usable edge, auto finding the best exit (the right triangle at 5 mm), the frames tried listed (also with E_SURFACE_NO_FIT), the narrow tip choosing the exit, both tails ending together, the nearer the extension past the edge or both the shortest tail (since P5-diagonal-bus.md section 27.3 on one line across the boards, the nearest such line since section 27.4, `TailRunTests`' runs of 4 and -15 mm giving 24 mm: the stacked tails' centres and ends coincide on the slanted plate, the holed plate, the disk and the right triangle's legs turned under 12 rows in every side mode, `StackedTailEndTests`; a tail beside the surface past the base side's line continued; the soft finger's stacked tails, the Column tail under the face on the 30 mm Row tail, end 20 mm past it, measured on the outlines), the overhang and the share (holes out) against our own geometry (the overhang past the edge at the tail root's level, beside the surface too), the Row pins by pin with a reversed scan order, a straight design mapped with field containment, a fillet's inner edges and the base edge in `W_BAND_EDGE_RADIUS` (a R0.8 bracket), the work budget (a round-hole plate at 1.5 mm: 532 at about twice the board fit's cost; the meter at a small budget), the early exit near the threshold and the runs beside a column against references, the rectangle search with a threshold; the browser client's fixes (the badge and the CSV of a full field, the pins from the pads, the stale Generate, one map request at a time, the disabled controls' reasons and the tail extension's range); coverage first (section 21, `CoverageFirstTests`): the fin-gripper face (a synthetic plate of its outline) takes the masked 59 x 12 = 569 following its taper, unturned, its tails at the 25.8 mm mount end, ROW_01 the narrowest at the tip, every proposal built and mapped; the cut square's masked 575 before its full 552 (the rectangle preference that could swap them gone with section 26.16); symmetric sensors on symmetric faces (section 22, `SymmetryTests`): the detection (a trapezoid, turned, split sides, vertices moved 0.03 / 0.1 mm, holes, a disk faceted at uneven steps; the plates' exits), the symmetric lattice (columns mirrored, runs free with their mirror images), the symmetric DP against brute force restricted to symmetric runs (zones, caps, windows, rectangles, thresholds), the mirror test and the symmetric peel, the named faces (the long taper's 924 at its 40 mm end before the 937 on a long side, the isosceles base 318 before a leg's 327, the right triangle's hypotenuse 552 before a leg's 562, the equilateral 342, the disk 440, the rounded plates; the fin's 568 before its asymmetric 569, the soft finger's 708 centred and its readers' 576 unturned), a field that breaks the symmetry first only with 20 % more (section 26.19: 119 / 120 / 121 against a symmetric 100 on one exit, across exits, turned and in area, section 22's order across exits, the tip never flipping it; the axis-hole plates' 19.0 % and 21.4 %, the holed plates' turned 396 and 344 first, the isosceles base's 328 before the legs' 341 and 337, the right triangle's hypotenuse 576 before a leg's 595, the isosceles triangle under 12 rows still its base's 74, the holed plate under 12 rows its 285 before its symmetric 232; no turned frame on an exit whose symmetric field holds within 20 %; the crank pad, without a symmetric exit, keeps its 688), the narrow tip, a border (the border's part on the surface tested: an isosceles trapezoid, a right trapezoid, a rectangle beyond the plate's sides, a square inside the right triangle), a pinned fingerprint of a symmetric fit (3.9 and 3.12, another hash seed); the caps keep the exit (section 23, `CapsKeepTheExitTests`): the fin under 32 rows keeps its mount end and fills its tip (32 x 11 = 256 symmetric since section 24, ROW_01 5 wide at the tip, tails 68.07 mm), its 16 rows with 102 mm tails (past 80 mm: the surface's 200 mm), the 200 mm cap on the fin stretched 2.6 times (the capped field at its tip refused, its tails 293.196 mm, and searched again nearer the exit: 16 x 9 with 199.683 mm tails, the tip-first field of its window; the review of section 27.4), the 12 mm tip as the exit gives the far end's 16 rows, and the helpers `tip_rows`, `tip_window`, `far_row`, `keep_exits` and `uncapped`; the corner tolerance at every convex corner (section 24, `ConvexCornerTests`): the rule on hand-made grids (a triangle of runs with one zone blocked at a convex, a concave and an aligned end) and on random staircases against brute force, the crank pad's 696 (683 before: rows 2, 9-12, 19-22, 29-32 one cell longer), every proposal's F on eight faces by our own predicates (P on the surface, F off it only within the margin and reach of F's convex vertices, by at most 0.5 mm) and the map's records, `field_parts` leaving out only convex corners (an aligned pair of runs keeps its margin), the crank's hypotenuse one edge from the tip corner, convex down to the funnel arm, the lanes inside, the convex sides' growth within their bound; the taxels from the fingertip (section 26): the full rectangle's column cap before its zones against brute force (`RectangleCapTests`, 3000 grids), the filler band over the common extent against brute force for both DPs and the lattice's bands against the free space, a pointed tip gaining its row (`FillerBandTests`), the tip step on synthetic candidates (the floor in integers, the share from the exit's most, the p / 8 slack, the displaced lead following, turned, `max_area` and `tip_first: false` untouched, the leads among the proposals), the real pass keeping its group, the per-row DPs and rectangles against brute force, the named faces (the crank's 688 before its 696, the long taper's 842 before its 844, the disk's 24 x 24, the rounded plates full, the exits as before), the tapered plates, section 23's window, the fin plate at 3 mm reaching its tip (the tip-first 246 at 118.85 mm, the 248 next; kept from the quick fix, section 26.14), the report and the pass's budget (`TipFirstTests`; its round 2's tie and `tip_first: false`, `TipTieTests`, and the pass's centred phases, tails' reach and peel fallback, `TipPassTests`; round 3c's reach first, a pointed tip ending in a single taxel); CAD mode without rectangles (section 26.16, `CadWithoutRectanglesTests`: `CAD_ONLY`, every removed option refused in parse and fit, a saved placement naming them mapped as fitted, only the values a fit then accepted, a rectangular selection's full field); section 26.17: the lead's tie in the lead's place (`tip_first: false` keeps coverage alone's proposals, the lead back when its tie is peeled), the displaced field's place and the taxels given, T0's p / 8 slack and ties of more taxels, the pass's floor within the slack (`TipTieTests`, `TipPassTests`), symmetric faces' symmetric fields first (since section 26.19 within 20 %), the symmetric tip share (`SymmetryTests`, `TipFirstTests`); section 26.18: every exit of the fit without the caps keeping its capped fields, each searched when the proposals reach it (`CapsKeepTheExitTests`), a symmetric lead's eighth row phases and its slack (the isosceles triangle's 322 at 57.15 mm, the taper's 351; `TipPassTests`), the taxels given from the lead and its pass, a tip-first tie peeled under the lead leaving it its place, a tie's peel to the lead's taxels keeping it (`TipTieTests`), saved placements' generic-template refusals (`CadWithoutRectanglesTests`); section 26.19, the user's threshold of 20 % on symmetric faces (`SymmetryTests`) |
| `test_easyeda_export` | the EasyEDA Pro projects of the default design, a soft-finger fit, a masked field and a straight channel with a cutout: the archive and the `.epro2`/`.epru` structure like the user's JLCEDA exports, every record's field set against theirs (a fixture, recomputed from the originals when present) and the environment template against them, layers and FPC mode, the PI stiffeners against the profile (0.225 mm, one of EasyEDA's PI options), each line's net with its contact, electrodes and tracks, EasyEDA's element numbering, the schematic channel, the design rules against the board's DRC, the stack; every layer against our Gerbers by scanline fill (`tools/compare_easyeda_gerbers.py`, also its CLI, EasyEDA-style Gerbers and a missing track or moved stiffener found), a cutout as a hole, the reader against EasyEDA's own export of the user's project; pinned digests (3.9 and 3.12, any hash seed); refusals and the read-back; the Direct Gerber archives unchanged; the HTTP route and the web button |
| `test_border` | CAD mode's border of the taxels (`surface/border.py`, [CAD_BORDER.md](../docs/CAD_BORDER.md)): `E_SURFACE_BORDER` (the request's shape, fewer than 3 vertices, not simple, under 1 mm², off the surface, the base and the exit edge, the containment), the exact orientation predicate, the lattice's cell predicate against brute force and its runs capped by the border; a border inside a plate placing every taxel inside it, one partly beyond the surface, a quadrilateral and a non-convex one; the border's exits (`border_edge`, `auto` over its longest edges, a clockwise border, turned frames); the map's `taxels_inside_border` (passing, failing, its tolerance, absent without a border, a damaged placement border); `facets_uv`; a strain-limited fit carrying the border onto its disk; determinism |
| `test_docs_consistency` | the tables and Python snippets of these documents and the quoted figures it lists against the code and generated boards (including the INTEGRATION side and stack tables), this test map, the mutation summary, that every mutation-catalogue edit still applies, the CI description, links, paths, `pyproject.toml` (T) |

`tests/geometry_checks.py` re-implements the geometry predicates the tests
use, so an engine defect cannot hide itself.  HTTP tests start
`app.AppServer` on an ephemeral loopback port; CLI tests run `cli.py` as a
subprocess.  The older modules regenerate the default design where they need
it (about 100 times per run, 0.057 s each, under a tenth of the run); the
stage-T and stage-G modules generate once per class.  Tools are not part of the suite:

- `tools/mutation_check.py` applies known defects (the audit's 36 baseline
  mutants and the C1 extras re-expressed for the current code, plus mutants
  of every fix stage and of the documents) to scratch copies and runs the
  suite on each.  Catalogue of 2026-10-29: 714 mutants, 709 expected killed; the last full run is of 2026-10-21 (below), and each mutant added or retargeted since was run on its own through the full suite (the EasyEDA Pro projects' `EASYEDA` group of 16 added, all killed; section 24's 7 added, all killed; section 26's 16 added, all killed, run on their own; its round 2's 17 added and 3 retargeted, all killed, run on their own; its round 3c, section 26.16, retired 19 with the code they mutated and added 5 and retargeted 4, all killed, run on their own; round 3c's review, section 26.17, added 5 and retargeted 2; the user's decision of 2026-10-27 on symmetric faces, section 26.17, retired 1 and added 2; the review's test gaps, 3 added; the 14 new, retargeted and redescribed all killed, run on their own; round 4's review, section 26.18, added 10 and described 4 anew; those 14 and 4 re-checked all killed, run on their own; section 27 retired 5 of the Row tail's placement mutants with the code they mutated and added 6 `M/sec27-*`, all killed, and marked `M/sec20-level-points-merged` equivalent: with the Row tail centred no side meets a flush tail at a slant on the level; its review, section 27.3, added 4, `M/sec27-inner-slant-half`, `-inner-slant-to-root`, `-inner-unfilled` and `-tails-own-ends`, each killed alone, and re-checked `M/sec20-level-points-merged`, still an expected survivor; the review of 27.3, the plan's 27.4, retired `M/field-tail-reach-own` with the shared reach it mutated and added `M/sec27-tails-shared-reach`, killed alone, and the seeded flush regression r2712:0469 kills `M/sec20-level-points-merged` alone, so it is no longer equivalent; the review of 27.4, the plan's 27.5, added `M/sec27-tails-reach-floored`, `M/sec23-cap-not-searched-again` and `-cap-not-refused`, each killed alone; the merge of the two lines of 2026-10-27 (the plan's sections 26.16-26.18 and 27-27.5, its 27.6) added and retired none, and the ten whose code or tests it touched were run alone on the merged tree, all killed; the user's threshold of 20 % on symmetric faces, the plan's section 26.19, added `M/sec26-symmetric-without-threshold`, `-symmetric-threshold-boundary`, `-symmetric-threshold-after-tip` and `-symmetric-never-turned` and retargeted `M/sec26-symmetric-within-3-percent` (its threshold at 3 %) and `M/sec22-turned-on-symmetric-exit` (turned within the threshold), each run alone; the rectangular mode's default tails 12 / 12 mm, the plan's section 27.7, added `T/default-tail-surface` and retargeted `T/default-tail`, each run alone; the multi-gripper video's notch, the plan's section 27.8 (`diagonal-bus/11`), added 7 `M/sec27-flank-*` (`-none`, `-no-end-move`, `-unguarded`, `-corner-off-grid`, `-point-kept`, `-anchors-ignored`, `-irregular`) and retargeted `M/diag-shared-row-only` and `T/doc-build-id`, each run alone; the profile revision 2026-10-29 (the gold-finger thickness order option and the coverlay-window notes) added 7 `G/*` (`G/gold-finger-review-note`, `-gold-finger-stiffener`, `-window-key-unchecked`, `-window-none-longer`, `-window-limit-doubled`, `-window-line-dropped`, `-window-line-unchecked`), each run alone): the
  catalogue's totals once the `M/` mutants of the masked field's phases P1
  (11), P2 (the builders: 13 added, and P1's temporary-gate mutant
  replaced by the class gate's; the DRC and registration: 14; the fixes of
  the P2 reviews: 8), P3 (the exporter: 14 added, and P2's exporter-gate
  mutant retired with the gate), P4 (CAD mode's masked fields: 22 added,
  and P2's map-gate mutant retired with the gate) and the fixes of the P4
  reviews (11 added, and P4's readout-dedupe mutant retired: one mask per
  readout is now the rule) and P5a (the diagonal Row bus's primitives, the
  `DIAGONAL` group: 6) and P5b (its construction, DRC and contract: 24
  more in `DIAGONAL`) and P5c (its exports: 5 more in `DIAGONAL`) and the
  fixes of the P5 reviews (9 more in `DIAGONAL`; the tail redesign of the
  plan's section 12, diagonal-bus/2, retired 10 of these and P5b's with
  the corridor, the stub drop and the stack rules outside the field, and
  added 14; its review retired one more and added 13, 8 in `DIAGONAL`
  and 4 in `FIELD_FIT` and a retarget; the stacked tails of the plan's
  section 13, diagonal-bus/3, retired 8 (the fallback beside the Column
  tail twice, the Column tail's side and neck, the Row root's lowering
  below the Column board, the tail gap and clearance and their 0.9 mm
  variant), retargeted 3 and added 6 in `DIAGONAL`, run on their own and
  killed: the full run waits for the final tree; the one outline over the
  field, diagonal-bus/4, added 8 in `DIAGONAL`, run on their own with the
  stacked tails' 6 and killed; its later decisions, no Column copper in the
  lanes' keep-out and lanes following a receding field, retired 2 (the
  Column stubs left out of the keep-out, now the rule, and the stack trace
  gap kept from them), retargeted P5a's 2 keep-out mutants and added 5 in
  `DIAGONAL`, run on their own and killed; its regular outlines,
  diagonal-bus/5, retargeted 2 and added 6 in `DIAGONAL`, run on their
  own: the full run is not to be run for now, the user's decision of
  2026-10-23; the corner tolerance, the rectangle preference and the
  chamfered notches of the plan's section 16, diagonal-bus/6, retargeted 3
  and added 7, 2 in `DIAGONAL` and 5 in `FIELD_FIT`, run on their own; the
  straight sides of the plan's section 17, diagonal-bus/7, retargeted 1
  and added 3 in `DIAGONAL`, run on their own; the rectangular generator's
  bus of the plan's section 18 retired 2 (the generic template accepting
  `routing.row_sides` and the form sending it there, now the rule; their
  inverses are among the new), retargeted 12 and added 9 in `DIAGONAL`,
  run on their own; its one Column V of the plan's section 19,
  diagonal-bus/8, retargeted 3 and added 5 in `DIAGONAL`, run on their
  own, and retargeted 2 document mutants: the default build id and its
  Column tail's flexible length; the rectangular generator as a subset of
  CAD mode, the plan's section 20 (one rule set, one outline down to the
  tail roots, the Column V capped at 80 degrees), retired 9 (the shared
  level at the field's edge or window level, the fillets kept while the
  union is made regular, the standard profile's 60-degree fans, fan start
  and careful pass, the override's two lanes and lane capacity and its
  version per template), retargeted 12 (the default tail, build id and
  flexible tail length of the documents, the DRC gate, the identity
  extra, the necked Column root, no shared outline, the Row board's alone,
  sharp union corners, no straight sides, the bus's rule set reaching the
  straight channel, the overhang at the root's crossings) and added 8, 7
  in `DIAGONAL` and 1 in `FIELD_FIT`, run on their own; the fixes of its
  review retargeted 3 (no straight sides, sharp union corners, the Row
  board's outline alone) and added 4 in `DIAGONAL` (the straight sides'
  bound measured to the sharp union, the union's points on the level
  merged, the run below the level along the last edge, a tail's root
  corner merged), run on their own; coverage first, the plan's section 21,
  retired 1 (`M/fill-shaped-64`), retargeted 3 (a reader not capping the
  field search, the rectangle preference ignored or unbounded) and added
  5 in `FIELD_FIT`, run on their own; CAD mode's border of the taxels
  (docs/CAD_BORDER.md) added 3 in `BORDER` (the border ignored in the
  lattice, `taxels_inside_border` never failing, `base.border_edge` taken
  as the next edge), run on their own; symmetric faces, section 22, added 5
  in `FIELD_FIT` (no face symmetric, an asymmetric row accepted as
  symmetric, the symmetric DP's runs shifted, a symmetric exit turned, a
  symmetric field first however few taxels, retired with section 26.17)
  and retargeted 2 to the
  edited lines, run on their own; the caps keeping the exit, section 23,
  added 3 in `FIELD_FIT` (the caps choosing the exit, a capped field's
  rows next to the exit instead of at the far end, the surface's tails
  held at 80 mm) and retargeted 2 to the edited lines (the no-fit reason,
  the whole lattice's field taken unfit), run on their own; the corner
  tolerance at every convex corner and the convex sides, section 24
  (diagonal-bus/9), added 7 (5 in `FIELD_FIT`: aligned ends exempted in F's
  check or half in the DP, convex corners held in the DP, F's check at the
  field's four corners only, the symmetric DP's old rule; 2 in `DIAGONAL`:
  no convex sides, the hull's bound ignored), retargeted 2 to the edited
  lines (the DP's phases swapped, the Row board's outline alone) and the
  document mutant of the default build id, and re-described
  `M/corner-zones-every-row`, run on their own; the Row tail centred on the
  field, section 27 (diagonal-bus/10), added 6 in `DIAGONAL` (the tail a
  contact pitch off the centre, the funnel's old split midway between the
  innermost lanes, one side's old tail under the band, the mirrored rows on
  the tail's near end, one side's inner flank with its ledge back or
  slanting however flat) and retired 5 of P5b, P5f and P5g with the code
  they mutated (the mirrored contacts, the split, the flush tail, the
  reader's far contacts, the tail a pitch off the split), run on their
  own with the re-checked flush-tail and tail-side ones: the fin's 59 x 12
  with both, a tail flush with both sides of the union, kills
  `M/sec20-run-on-last-edge` and `-root-corners-merged` again, a check of
  `_side_chain` on its own `M/diag-tail-slant-above-field`, and
  `M/sec20-level-points-merged` is marked equivalent; its review, section
  27.3, added 3 in `DIAGONAL` (the inner flank slanting only within half its
  drop, to the tail's root instead of its hold, not made monotone) and 1 in
  `FIELD_FIT` (each tail ending past the edge under its own width, not on
  one line with the other), each run on its own and killed, and re-ran
  `M/sec20-level-points-merged`, still an expected survivor; the review of
  27.3 (the plan's 27.4) retired `M/field-tail-reach-own` with the shared
  reach it mutated, added `M/sec27-tails-shared-reach` (the line pushed by
  that reach), killed alone, and found `M/sec20-level-points-merged` not
  equivalent: the seeded r2712:0469, a flush regression now, kills it alone;
  the review of 27.4 (the plan's 27.5) added 3 in `FIELD_FIT` (a tail
  reaching the line rounded down; the 200 mm cap of section 23 not searched
  again nearer the exit, or its refusal off), each killed alone) and P5d (CAD mode's field-only containment and the P5c carry-overs: the
  `FIELD_FIT` group, 21) and P5e (the default flip, the map's containment
  from the design, the no-fit reason and the browser client's Row traces and
  Containment: 8 more in `FIELD_FIT`) and the fixes of the P5d/P5e reviews
  (24 more in `FIELD_FIT`) were added; a full run of these totals is
  pending.  The run of the 369 before them, on a frozen copy outside the
  repository, killed 363 (2026-10-21, 07:45 UTC): its one unexpected
  survivor, `T/doc-ci`, cannot be killed there because the copy has no
  repository-root CI workflow, and is killed when run from the project.
  Each P1 `M/` mutant was checked killed on its own and through the full
  suite, and each P2 one through the full suite (`--only` its ids), and so
  were each P3 and each P4 one, and each of the P4 reviews' fixes, and each
  P5a, each P5b and each P5c one, and each of the P5 reviews' fixes, and
  each P5d and each P5e one, and each of the P5d/P5e reviews' fixes.
  The `M/` mutants keep a full mask, accept a mask on the generic
  template, drop `mask` from the identity or
  from the exports' identity fields, skip the column-gap rule, the
  inactive-gap warning or the class gate, let the size advice change
  rows, swap the Row-frame sides, and drop the lane taper or the Column rule
  of the construction classes; the builders' mutants end the Row or the
  raised Column stubs at the field's common end, keep the unmasked field
  start, drop the fillers between bands or the window's expansion, make a
  full span's window a polygon, leave the polygon window or the active
  outline unturned, drop the Row body's bottom width or keep either body a
  rectangle, and write the taxel mask in frame slots; the DRC's mutants
  measure the margin to P's bounding box, skip P's equality with the
  electrodes, the window's shape, the inside test or the clip of the
  strict rule, keep its own-net skip or the edges on a route's own window,
  measure a polygon's bridge or exposure on its bounding box, leave the
  top board unturned in the stack frame, skip the crossing test, the
  masked grid's ends, the masks' comparison or the inactive separation; the
  review fixes' mutants skip the masked grid across the electrodes, judge a
  window touching the outline by one vertex, let a window overlap a cutout
  or P lie off the board, drop the trace overlap report or count crossings
  in it, and let the map take a masked build; the exporter's mutants (P3)
  write a polygon window as its bounding box or compare its region with
  itself, let any opening be a polygon, let one sit on an unmasked board,
  carry rectangle fields, cross itself, leave the grid, slant or turn
  clockwise, invert taxels.csv, drop it or its read-back, and drop or
  miscount the order notes' taxel field; the fit's mutants (P4) count
  positions as taxels, give a masked
  proposal its bounding rectangle as field outline, drop the peel, write
  the spans in slot order, drop the free space's edge inset, end a row's
  band half a pitch above it, drop the lane taper, propose masks without
  the rectangles, keep the rows' own far ends, take 64 masked rows (or a
  fill on the generic template, retired with section 26.16); the map's list every position, mirror the
  taxels, blind the mask record or want R x C taxels; the readers' take 16
  sense lines per frame row, the largest reader for `auto`, swap the sides
  or ignore the legacy `connector`; and the web client's post the form
  without the mask or keep it after a rows edit.  The P4 reviews' fixes'
  mutants leave the masked walk uncapped by a named reader, name the
  option's reader in the metrics, seed the lattices at the placement
  option only or from either role's rectangles, prune a role on the other
  role's masks, run the fine phases on either role's frames, keep a
  dominated proposal, drop the mask on a mode switch, show no issue at
  `matrix.mask` and leave "Use the full field" inert (keeping Field shape
  enabled on the Rectangular board rules retired with section 26.16).  The P5a mutants keep collinear
  points on the west chain, offset slanted segments without the 2 nm
  allowance, round offset vertices to the nearest grid value, bevel a
  sharp convex turn, and leave a lane's continuation or the box around its
  start out of its keep-out.  The P5b mutants, re-expressed for
  diagonal-bus/2, let a lane leave its own zone short of its corner or
  within the trace space of another row's electrode, start lanes at a
  corner, drop the tail root's hold, keep ROW_01..ROW_R on the contacts,
  never mirror, split in halves, turn off the DRC gate, accept traces over
  electrodes, warn of no close window, drop the identity extra, accept the
  field on the generic template and let an infeasible bus raise.  The tail
  redesign's mutants keep diagonal-bus/1's corners below the field (three
  bends), turn a thin row's lane down inside the Column windows' keep-out,
  raise the bottom row's corner before the onion (the bands move), let a
  tail side slant out however flat or from above the field, fail a trace
  over an electrode only with a window too or count it per electrode, run
  the fans a grid step inside the bundle pitch or unstaggered, allow the
  Column entry angle, ignore the fans' clash check, land the last lane one
  contact beyond, and leave traces over the field window uncounted or one
  opening per electrode out of the window.  The stacked tails' mutants neck
  the Column board 1.0 mm, give it the straight classes, let the registration
  accept traces over the other board's electrodes and window or tails on two
  sides, and report no tail overlap.  The later decisions' mutants on
  diagonal-bus/4 put the stacked Column copper back in the bands' keep-out,
  run a receding field's lanes straight down from their westmost point, ignore
  the inner lanes' offsets where they cross the field's bottom edge, let a
  lane lean past the taper cap toward it, and take the mitre at a lane's
  inward turn (the lanes outside it spread).  The regular outlines' mutants
  (diagonal-bus/5) leave the outlines as built, merge only vertices that do
  not turn at all, make a merged run's edge its chord (cutting inside a convex
  run), let the union's regularization move the boards' fillets, leave the
  corners where merged edges meet sharp, and make the tails regular too.  The
  chamfered notches' mutants (diagonal-bus/6) take the hull of P for a notch's
  chamfer (cutting inside F) or keep F's staircase; the corner tolerance's
  mutants let the zones reach along F's whole sides or into P and tolerate
  every row's corners (its two that ignored the rectangle preference or
  applied it beyond its share retired with section 26.16).  The straight
  sides' mutants (diagonal-bus/7) leave the sides' polylines, ignore the
  1.0 mm bound, and take the chord from the tip corner for the upper line (not
  enclosing the side).  The one Column V's mutants (section 19) reach the
  straight channel's Column board with the bus's rule set and keep the Row
  fans off the old 60-degree Column entry.  Section 20's mutants give the
  rectangular generator a rule of its own (its Column V always capped: parity
  broken), stop the shared outline at F's bottom, leave the tails' roots above
  the union's fillets, never or always cap the Column V, give the straight
  channel the bus's default tail, drop the channel's column bound from the
  served limits, and skip the side
  overhang where a straight side crosses the surface's lowest level.
  Section 21's mutants (coverage first) cap the field fit's shaped fields
  and the board fit's masked walk at 32 x 32 again (retiring P4's
  `M/fill-shaped-64`) and leave reader `auto` uncapped (its two rectangle
  preference mutants retired with section 26.16).  Section 24's mutants exempt aligned ends from F's
  check (or half of them in the DP), hold a lower run's top zones at its
  convex corners in the DP or check only the field's four corners in F's
  parts (section 16's rule: the crank's 696 back to 683), keep the
  symmetric DP's old rule, leave the convex sides out (the S-kink beside a
  narrow tip stays), and bridge any dent however deep.  Section 26's mutants
  (the taxels from the fingertip) read a capped rectangle's zones before its
  cap, leave the filler band unchecked or held over the lower run (and two of
  its phases wrong), keep no field but the lead, take the share from the lead,
  widen or drop the slack, let a full lead take notched fields, group across
  exits, drop the displaced lead or its proposal key; its round 2's drop the
  lead's zero-cost tie, let `tip_first: false` take the share or skip the
  step, and pin what the first round left open: the reach before the corner
  count, the centred phases, the tails' reach in the pass and the peel
  fallback; its round 3c's five (section 26.16) let a full lead's pass ignore
  section 23's window, drop the lead's ties short of the tip-first field from
  the pass or stop the pass at that field's reach, let a fit take shape
  rectangle, the generic template or a rectangle preference silently, and
  refuse a saved placement that names them.  Retired with what they mutated
  (section 26.16, 19 in all): the tip-first rectangles' three, round 2's
  tip-zone guard (2), tie-break (2), rectangle floor and column guard (4),
  P4's shape fill on the generic template, the browser's Field shape and
  Containment on the Rectangular board rules, the rectangle preference's four
  and the CAD fit's shape per pitch.  Section 26.17's ten (round 3c's review
  and the user's decision of 2026-10-27 on symmetric faces) propose the lead
  beside its zero-cost tie, keep a tie peeled under the lead's taxels in the
  lead's place, report the displaced field's rank only where it is proposed
  itself, count the taxels given from the lead, let the map take any value of
  the removed options, put a symmetric field first only within 3 % again
  (since section 26.19 its threshold at 3 % for the 20 %),
  measure a symmetric group's tip share from every field, drop T0's p / 8
  slack, take T0 of exactly the lead's taxels, and run the pass's lattices
  short of the farthest reach at the lead's value; retired with it: section
  22's symmetric field first however few taxels (its rule then; a defect
  again since section 26.19).  Section 26.19's four (the user's threshold
  of 20 %) put every symmetric exit's lead first however many more taxels
  another field holds, let the symmetric field still lead at exactly 20 %,
  count the tip's 3 % into the decision, and turn no exit with a symmetric
  field; `M/sec22-turned-on-symmetric-exit` turns an exit whose symmetric
  field holds within the threshold.  Section 27's
  mutants (diagonal-bus/10, the Row tail centred on the field) put the Row
  tail a contact pitch off the field's centre, part the funnel's contacts
  midway between the innermost lanes again, put one side's tail under the band
  again, take a mirrored build's contacts at the tail's near end, and give one
  side's inner flank its ledge along F's bottom back or slant it out however
  flat; its review's (section 27.3) slant that flank only within half its
  drop, slant it to the tail's root instead of its hold, leave it unmade
  monotone, and end each tail past the edge under its own width (not on one
  line with the other); its review's (27.4) push that line out by the shared
  reach, and 27.5's round a tail reaching it down and leave the 200 mm cap of
  section 23 without its search nearer the exit or without its refusal.  They
  retired diagonal-bus/2's and /3's placement mutants with the code they
  mutated (the mirrored build's near-end contacts, the funnel's split under
  the near band, the one-sided tail a contact outside the band, a mirrored
  reader tail's rows at its far end, the funnel's Row tail a contact pitch off
  its split).  The P5c
  mutants give an unmasked bus no taxel map, state its full field as a
  masked taxel field in the order notes, leave the bus's record out of
  the review manifest, skip its read-back against `pinout.csv`, and number
  the recorded Row pins by position.  The P5 reviews' fixes' mutants list
  no flat lane, take the plan's least-excess
  clause or every row for the relative narrow tip, and give any unequal
  tails E_ROW_BUS_TAILS.  CAD mode added 110 (`S/`; 46 with the first
  review's fixes, 64 with the second's): the STL weld,
  orientation (inside-out, open shells, cavities), repeated facets, covered
  walls, T-junctions, the selection's cone, blend barrier, creases and fine
  fillets, the chart's hinge, handedness, holes, bands and pieces, the
  fit's mirror, strain gate, arc exits, edge inset, obstacle cells, one proposal per shape,
  exit-crossing clearance and short sides, the map's mirror, mismatch
  checks (design, template, mesh, selection), containment, tail reach,
  reader lines, surface spacing, placement validation and JSON records,
  big integers, long header numbers, the mesh cache's unit, CAD mode's own
  slot, the 413 drain, the content type and two CLI statuses.  The run of
  2026-10-15 had 259 mutants, 254 killed (21 of them added with the necked routing:
  the bundle pitch, the bend stagger, the widening drop, the route rule, the
  `route_width` record, the copper's trace minimum, the input ranges and the
  per-route stroke widths; 6 with its review: the DRC's finger-section rule
  and its pairs, the widening drop for intermediate bundle widths, the grid
  rounding of the far bends and the trace-tolerance line of the order notes); the audit's 36 baseline mutants are all killed
  (9 at the audit; `audit/x`, whose defect, the missing `E_DUAL_LANE_WIDTH`
  check, is the intended behaviour since 2026-10-15, now drops the minimum
  slot of a narrow fan-out instead).  The 5 survivors are justified in the catalogue:
  3 equivalent (`E/F1-inputs`, `X/pinout-index`, `X/given-boards`) and 2
  browser-only (`F/stale-banner`, `F/turn-over-axis`), which the Playwright
  checks kill.
- `tools/golden_values.py` prints the default-build values for
  `test_golden_default.py` after a deliberate change.
- `tools/browser/` holds the Playwright checks of the browser UI (their own
  virtual environment; see its README).

CI (`.github/workflows/fpc-agentic-customization.yml` at the repository
root) runs the suite on Python 3.9 and 3.12, `tools/mutation_check.py
--check` (every catalogue edit still applies) and `node --check
web/app.js`; the full mutation run is a manual job of the same workflow
(estimated at about an hour on a standard runner; the workflow has not run
on GitHub yet).  There is no lint step: the project
stays free of third-party tools (pyflakes, run from a scratch environment,
reports nothing on any file as of 2026-10-15).

## Open items

Product decisions:

- The default Row tail has 12 contacts; the FlexiTac reader needs
  `connector.row_pins = 16`.  Whether the default should follow the reader is
  open.
- Contact-zone thickness about 0.285 mm with the 0.225 mm PI default
  (approved 2026-10-14) against the connectors' 0.30 +/- 0.03 mm; JLC holds
  the gold-finger area to +/- 0.03 mm, so the notes ask to measure it on
  delivery.  The estimate uses the stack-up of the ordered build (0.025 mm
  core PI + 0.035 mm copper, the coverlay open), derived from JLC's
  finished-thickness and coverlay tables, not confirmed by JLC.
- The 0.127 mm default fan-out traces may come out at 0.1016 mm (JLC's
  +/-20% trace tolerance, its 1 oz minimum); whether the default should keep
  more margin (a wider `routing.trace_width_mm`) is a product question, as
  is any rule for trace width near bends or stiffener edges, where JLC sets
  none.
- D8, not implemented: 0.6 mm reference electrodes (default 1.4 mm),
  inter-electrode slits, alignment holes or fiducials, the canonical 12 x 32
  compatibility template.
- `tail.stiffener_end_clearance_mm` 0.5 mm is a product default, not a JLC
  rule; the default 12 mm bottom tail leaves 6.0 mm of flexible tail (1.5
  mm with the 7.5 mm default before P5-diagonal-bus.md section 27.7; the
  diagonal Row bus's Column tail runs straight down from the shared bottom
  edge, section 20; the straight channel's 7 mm tail leaves 0.72 mm, 0.88
  mm before the necked routing, whose merger meets the tail at 60 degrees,
  so the shoulder fillet starts lower), still short for the half twist the
  bottom tail needs (see INTEGRATION.md).
- The bus angle is the 60 degree cap for every bundle pitch, as T-D4
  decided, so the bend stagger grows with the pitch while the lateral move
  of the expansion shrinks: a pitch above 0.25 mm makes the expansion taller
  (64 rows: 9.23 mm at the default 0.254 mm, 17.89 mm at 0.4999 mm, 0 at
  0.5 mm; [LAYOUT_SCHEMA.md](../docs/LAYOUT_SCHEMA.md#row-channel)) and can
  decide whether a large design fits, which `E_BOARD_SIZE` does not trace
  to the routing fields.  Choosing each run's angle to make it as short as
  possible would remove this, but changes every design whose bundle pitch is
  above about 0.25 mm, the default included.

External evidence still missing: a JLCPCB upload of the current outlines,
coverlay windows (the contact window has 0.05 mm lateral expansion) and
stiffener layers; whether JLC uses the extra ZIP members (`ORDER_NOTES.txt`
included), comment-form X2 attributes and the 0.225 mm PI layer; whether the
+/-0.05 mm outline tolerance and the gold-finger width are held; that
JLC builds the 0.11 mm 1-layer FPC with 1 oz copper and the contact-zone
thickness it delivers; connector insertion, continuity and an assembled
stack.

Engine notes found while testing (stage T, code unchanged):

- `engine/drc.py` `_long_axis` infers the electrode axis from where the
  electrode field outgrows the taxel field.  One Column electrode moved 0.6
  mm sideways (edited geometry) is then reported as parallel boards, with an
  `E_REGISTRATION` error at `tail.column_side`, next to the real
  `E_COPPER_EDGE_CLEARANCE`.  Generated designs are unaffected.
- `engine/layout.py` `_body_side` keeps every body-side step flush or at
  least one fillet radius wide (D5).  No DRC rule notices its loss, because
  the rolling-circle fillets round a narrower step as well (without it 311
  of 3948 boards of 2000 random designs keep a narrow step, all passing the
  DRC); `test_geometry_column` therefore pins the step rule itself.
- `engine/layout.py` `matrix_values` rounds inputs that `generate_design`
  has already canonicalised (mutant `E/F1-inputs` is equivalent).
- `engine/schema.py`: the catalogue text of `E_CONTACT_EXPOSURE` ("the
  contact window ...") and `E_OUTLINE_SELF_INTERSECTION` ("the outline ...")
  served by `/api/schema` and `/api/default` is narrower than the DRC, which
  raises them for electrodes and for cutouts as well;
  [LAYOUT_SCHEMA.md](../docs/LAYOUT_SCHEMA.md#issue-catalogue) describes
  what the DRC does.

Engine notes of the necked routing (2026-10-15):

- `engine/layout.py` `_size_advice` lowers two fields in step only when no
  single field is enough.  With the locked profile that branch is never
  reached: one row always fits (the tallest one-row board of a search, 32
  columns at 10 mm, an 80 mm tail, 64 contacts and the widest bundle, is
  321.25 x 194.30 mm against 234 x 490 mm), so `test_geometry_profile`
  reaches it with a 150 mm short side (mutant `E/size-advice`).
- `engine/layout.py` `column_plan` rounds the junction level down to the
  grid although every bend and the widening drop already lie on it; the
  rounding only removes float noise (602 designs byte-identical without it).
  Mutant `E/F1-heights` therefore drops the grid rounding of the bends where
  a diagonal meets its route's own column, which the grid test notices.
- After the independent review: `engine/drc.py` holds a route pair with a
  tail piece to the finger-section spacing instead of the trace space
  (`route_route_clearance` and its `finger_section`).  Before, the 0.246 mm
  gap held by construction only, and two reviewer mutants that shortened the
  widening drop for bundle widths between 0.127 and 0.25 mm passed the suite
  (now mutant `E/junction-drop-mid`).  `engine/layout.py` `_bends` rounds the
  bend where a diagonal meets its own column away from the bundle: rounded
  to the nearest grid value, diagonals 1e-4 mm wide (a bundle pitch near
  0.5 mm) leaned past the cap, by up to 0.26 degrees in the review's sweep
  (mutant `E/bend-rounding`).

## Run and resume

From this directory (`fpc_agentic_customization/`):

```bash
PYTHONPATH=. python3 -B -m unittest discover -s tests
node --check web/app.js
python3 app.py                # http://127.0.0.1:8008 ; --port 8009 for another port
python3 app.py --allow-host abc-8008.usw2.devtunnels.ms   # also serve a tunnel/proxy/LAN Host name
python3 cli.py export design.json --out outputs/
```

```python
from engine import default_design, generate_design
from exporters import build_exports

result = generate_design(default_design())
assert result["ok"], result["validation"]["errors"]
artifacts = build_exports(result)  # three bytes-valued ZIPs
```

No dependency installation is required; the engine finds its profile
relative to its source, independently of the working directory.  The
active-thread log `claude/WORK_LOG.md` is a local file, git-ignored by design
(see `.gitignore`) and not part of this checkout; start it from the
workspace's `WORK_LOG.template.md` at the repository root.  Dated session
notes go to `claude/sessions/week-of-<Monday>/<date>.md`.
