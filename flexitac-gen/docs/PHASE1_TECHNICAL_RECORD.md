# Phase 1 technical record

> **Historical record.** The dated sections below describe the engine of
> 2026-09-13/14 (layout v1, generator 0.2.x, exporter 0.1.x) and keep its
> measurements as they were.  They are superseded: the current geometry,
> rules and measurements are in [LAYOUT_SCHEMA.md](LAYOUT_SCHEMA.md) and
> [APP_HANDOFF](../claude/APP_HANDOFF.md), and the audit that found the gaps
> is [the 2026-10-12 report](../claude/verification/2026-10-12-audit-report.md).
> Notes marked *2026-10-14* correct statements that the audit measured to be
> untrue or that no longer hold.

## Implemented scope (2026-09-14)

- Local HTTP application at `127.0.0.1:8008`, using Python standard library
  only.
- Versioned high-level matrix design schema (`tactile-fpc-design/v1`).
- Deterministic generic-matrix geometry generation for two **separate** FPCs:
  row electrodes and column electrodes.
- Standardized single-copper FPC profile, top copper routing, Polyimide
  coverlay openings, bottom 0.200 mm PI tail stiffener and locked fabrication
  limits.  *2026-10-14: the PI stiffener is 0.225 mm since stage G;
  2026-11-06: 0.1 mm, for the 2-layer 0.2 mm order (JLC's rule: FPC
  thickness + stiffener thickness = the 0.3 mm gold fingers).*
- DRC-style input and manufacturing-rule validation.  *2026-10-14: the
  post-generation DRC then checked routes only; electrodes, contacts,
  coverlay, stiffener, outline shape, connectivity and the registration of
  the two boards were unchecked (audit H5).  The whole-board DRC replaced it.*
- Independent 2D SVG and locally generated oblique flexible-FPC review for
  both pieces.
- Column-side routing with a true adjustable connector-tail extension.  For
  17–32 channels it uses two dense, ordered route decks around a computed
  central routed slot, then merges mechanically into one N-pin connector.
- Downloadable canonical design JSON, expanded derived layout JSON and a
  SHA-addressed build manifest.

## Deliberate boundaries

`generic_matrix_v1` is a new regular parametric template.  Its default 12 ×
32 / 2 mm form is a useful functional preset, but it is **not** declared to
be a bit-for-bit reproduction of the legacy complex 12pin/32pin outlines,
slots or stiffener shapes.

The preview is generated directly from layout geometry and clearly labelled as
an oblique FPC review.  It is not claimed to be KiCad's or EasyEDA Pro's
native 3D viewer.

The build manifest has `geometry_valid` and `production_ready` as separate
states.  Geometry-valid builds always set `production_ready: false`.  Phase 2
now provides a separate Direct Gerber/JLC-review-candidate output; details are
in [`PHASE2_DIRECT_GERBER.md`](PHASE2_DIRECT_GERBER.md).  It is neither a
native EasyEDA export nor a production download.  The known R4 12pin EasyEDA
bottom-view issue is therefore not hidden or propagated into this new
generator.

## 2026-09-13 column-side routing correction

The early generic column board used a narrow rectangular tail while drawing
direct diagonal lines to the broad electrode array.  This could place much of
the 32-channel fan-out outside the board outline and made the intended tail
extension visually ineffective.

The corrected generic shape uses a broad fan-out region, a central routed
slot, a tapered merger and a real narrow connector-tail extension.  The shape
is inspired by the original 32pin design's two 16-line channels and central
clearance slot, but no original coordinates, outline, slot, PI geometry or
Gerber is imported at run time.  The fixed 0.500 mm lane pitch, 0.254 mm trace
width and 0.246 mm nominal clearance remain profile-controlled.  A 20-channel
case becomes two 10-channel decks; 32 becomes two 16-channel decks; values
above 32 are rejected by this initial two-lane profile.

## 2026-09-14 route-envelope, clearance and independent-tail correction

- The physical **Top FPC** and **Bottom FPC** now have independent tail-length
  inputs: `tail.top_length_mm` and `tail.bottom_length_mm`.  A role gets its
  length from `role_mapping`, so the correct physical piece keeps its selected
  length even if the row/column assignment is swapped.  The legacy single
  `tail_length_mm` / `tail.length_mm` input remains a migration alias that
  assigns both lengths equally.
- The column-board perimeter is now a normal-offset envelope of the two
  outermost fan-out traces.  In particular, it no longer relies on a broad
  straight trapezoid or an X-only offset, both of which leave excess material
  around diagonals or reduce real perpendicular copper-to-edge clearance.
  The generated outline remains a close, continuous route envelope and has a
  nominal 0.350 mm route-centre-to-Edge.Cuts allowance.  *2026-10-14: not
  met.  The offset moved each vertex along one averaged normal, without
  joins, and kept only 0.3329 mm at the deck-to-entry bend of the default
  board (audit M8).  It was replaced by a true one-sided offset with round
  joins; the centreline-to-edge envelope is now 0.127 + 0.3 + 0.001 mm.*
- A post-generation geometric DRC is now part of every build.  It measures
  exact segment-to-segment distance between every pair of different nets,
  detects any outer-outline or routed-slot intersection, and records the
  minimum values in each board's `verification` object and derived-layout
  JSON.  Downloads are blocked if that DRC reports an error.  *2026-10-14:
  the violation counters pruned pairs against the running minimum, so they
  could undercount on crossing or mixed-width geometry (audit I5, latent on
  generated layouts); the current counters are exact.*
- The rounded dual-bank implementation at this point measured **0.177573 mm
  copper clearance** at its closest 32-column approach, exceeding its locked
  0.170 mm fan-out minimum.  It was later superseded by the compact
  three-stage topology below, which has a different recorded clearance.
- The rounded implementation's outline measurement was 0.222989 mm minimum
  copper-to-board-edge clearance and 0.623 mm copper-to-central-slot
  clearance.  A 5 um curve-chord tolerance is used only when comparing the
  nominal 0.350 mm centreline route envelope to its rounded polyline output;
  actual measured clearances are always retained in the manifest data.
  *2026-10-14: not so.  The 5 um tolerance was applied to the 0.200 mm
  copper-to-edge acceptance itself, so 0.1952 mm passed (audit L4).  It has
  been removed: every rule is compared with a 1e-6 mm numerical epsilon.*
- The Row FPC outline was corrected to a single non-self-intersecting closed
  loop.  Earlier point ordering drew an interior tail/body Edge.Cuts segment;
  it could look harmless in an SVG fill but is not valid as a board cut.  The
  new loop has no interior cut line and passes the same containment DRC.
- The one-lane (1–16 column) contour now joins its entry and merger at their
  actual shared deck point.  This eliminates an obsolete dual-lane bridge
  that could have crossed routes on small channel-count variants.

## 2026-09-14 compact dual-bank topology correction

The 32-column layout was revised from a broad, rounded two-bank fan-out to a
three-stage symmetric topology:

1. The left 16 and right 16 electrode routes begin tapering inward immediately
   after the active field, rather than retaining broad outside shoulders.
2. Each side becomes a constant-pitch, 0.600 mm dense route bank while passing
   the two sides of the central routed slot.
3. The two dense banks then taper together into the single 32-pin, 0.500 mm
   connector-pitch tail.

The board outline is derived from each complete outer route (entry taper, slot
bypass and tail merger) as one continuous normal-offset envelope.  This avoids
the former small inward outline notch at the junction of separately offset
curves.  It also gives the intended shape: a perimeter that starts narrowing
as soon as the lead-out begins, follows the two dense banks, then narrows once
more into the connector tail.

The direct tapers are permitted only for the two-bank topology and are checked
by the segment-level DRC.  The default 32-column result measures 0.192368 mm
minimum copper clearance (0.446368 mm centre-to-centre) at its closest
different-net approach; the dual-bank requirement remains 0.170 mm.  Single
lane variants (1–16 columns) retain the established 1.200 mm deck pitch and
smooth transition, because applying the compact dual-bank taper there would
unnecessarily reduce their clearance.

## 2026-09-14 compact outline and turn-overlap audit

- The compact dual-bank board envelope was tightened again to target a
  **0.200 mm copper-to-Edge.Cuts** margin in the lead-out/merger region.
  *2026-10-14: below JLCPCB's 0.3 mm laser-outline rule (audit H3), and the
  outermost Column electrodes came within 0.000-0.155 mm of the outline,
  which no check covered (audit C2).  The rule is now 0.3 mm for all copper.*  The
  nominal route-centre envelope is 0.330 mm for 0.254 mm copper.  The current
  default 32-column geometry measures **0.202808 mm** at its closest board
  edge, so the perimeter follows the outer copper closely without consuming
  more FPC area than this mechanical margin.
- Route DRC now records both `inter_net_copper_overlap_segment_pair_count`
  and `inter_net_clearance_violation_segment_pair_count`.  It deliberately
  excludes same-net segments: their round joined corners may overlap as one
  continuous conductor, whereas any different-net overlap is an error.
- The default 32-column compact layout records **zero** different-net copper
  overlap segment pairs and **zero** different-net clearance-violation segment
  pairs.  Its closest different-net approach is 0.446368 mm centre-to-centre,
  leaving 0.192368 mm copper clearance through the direct-taper turn region.

## 2026-09-14 registered two-FPC assembly preview

The local UI now includes a third, assembly-only 3D review.  It registers the
two independent generated boards by their common active-region grid: the Row
FPC is shown below and the Column FPC is shown above.  *2026-10-14: that
order ignored `role_mapping` (rows are on top by default) and the flipped
board was offset by its active-region origin (audit M3).  The preview now
draws the physical top board upper, turned over about its tail axis, and
registers both on their taxel fields; see [INTEGRATION.md](INTEGRATION.md).*  The Column board is
flipped 180° about the long axis of its column electrodes (the layout Y axis),
not rotated in the board plane.  This preserves the connector/tail direction
while reversing the face normal, so its electrode copper is explicitly marked
as facing down toward the Row FPC.  The visible exploded gap and transparency
exist only to make registration inspectable; they do not define a spacer,
assembly thickness or manufacturing change.  The two Gerber/project exports
remain separate FPCs.

## 2026-09-14 compact column lead-out profile

The fixed column lead-out was shortened while retaining independent physical
tail-length control:

- The two-bank central slot is now a locked 12.0 mm opening rather than a
  large proportional opening.  This lets both route banks approach the centre
  earlier, so less lateral movement is needed at the connector merger.
- The two-bank merger is 16.0 mm (previously 26.0 mm).  For 1–16-column
  single-bank layouts, the fixed merger is 12.0 mm.  The separate physical
  Top/Bottom tail-length inputs remain editable.  The compact default is
  12.0 mm for physical Top and 7.0 mm for physical Bottom (the default Column
  FPC); users can lengthen either value in the UI.
- At the default 12 × 32 / 2 mm preset, the Column FPC outline is now
  **64.9 × 70.9 mm**, 15.0 mm shorter than the preceding 85.9 mm compact
  dual-bank version.  A 16-column Column FPC is **32.9 × 55.9 mm**, 14.0 mm
  shorter than its preceding 69.9 mm version when the tail is held at 12.0
  mm; with the new 7.0 mm Bottom-tail default it is **32.9 × 50.9 mm**.
- The shortened default 32-column merger measures 0.196332 mm minimum
  different-net copper clearance and 0.205897 mm minimum copper-to-board-edge
  clearance.  Its route DRC records zero different-net overlaps and zero
  clearance violations.  The separate normal-offset outline allowance and
  the 0.200 mm actual copper-to-edge DRC rule are intentionally distinct, so
  rounded outline joins retain the required physical edge clearance.

## Parameter-to-layout contract

| User input | Deterministic result |
| --- | --- |
| `rows` | row FPC channels, connector pins and horizontal electrodes |
| `columns` | column FPC channels, connector pins and vertical electrodes |
| X/Y pitch | common registered grid spacing on both boards |
| Row/column electrode widths | taxel intersection height/width respectively |
| Top / bottom tail length and direction | each physical board's outline and fanout orientation (*2026-10-14: the PI stiffener is now a fixed 6.0 mm connector zone, independent of the tail length*) |
| Top/bottom row assignment | physical-side labels; boards remain separate files |
| Scan direction | connector-pin mapping, without changing taxel registration |

## Next acceptance gate

Before a Gerber backend can be marked available, it must generate files from
this exact derived layout and independently validate: copper/coverlay/outline
coordinates, slots, bottom PI layer and JLC metadata, then pass representative
JLCPCB upload review.  *2026-10-14: the Direct Gerber backend was opened for
downloads as review candidates before this gate (its 0.1.0 contacts were
shifted, audit C1).  The exporter now decodes every Gerber, `jlcpcb.json`
and netlist it writes, compares them with the derived layout and re-reads
every archive byte for byte; the JLCPCB upload review is still
outstanding.*  The EasyEDA-native project writer is a separate gate:
it needs a full native layer/physical-stack graph regression, including a
fresh import, FPC-mode save and native 3D inspection.

## 2026-10-13/14 fix of the audit findings (layout v2)

The audit of 2026-10-12 was fixed in five stages (engine and DRC, API,
exporter, browser, tests and documents); the details are in
[APP_HANDOFF](../claude/APP_HANDOFF.md).  In short: tails sized for the
reader's 0.5 mm ZIF connectors with NC contacts and R0.30 tip corners; a 0.75
mm board margin around the taxel field on both boards; 0.3 mm copper to every
edge; fan-out tapers that scale with the displacement; a true offset with
rolling-circle fillets; merged coverlay windows; a fixed connector-zone
stiffener; a whole-board DRC on the emitted layout; strict input with a JSON
Schema; a build identity over design, profile and versions; copper-side SVG
top views; exporter 0.2.0 with a netlist, a self-verifying review bundle and
stored ZIP members.  Row FPC 71.4 x 36.9 mm, Column FPC 64.9 x 67.109256 mm.

*2026-10-14, stage G (approved after a review of the connector drawings):
the default PI stiffener is 0.225 mm (it was 0.2 mm), and the profile's new
`order` block (1-layer 0.11 mm FPC with 1 oz copper, +/-0.05 mm outline
tolerance on request, ENIG, with JLCPCB and connector sources) is written to
`ORDER_NOTES.txt` in every ZIP and to both manifests; the profile's
stack-up is now that build (revision 2026-10-14.2).  The geometry is
unchanged; the default build id changed with the profile digest.*

*2026-10-15, necked routing (requested by the user: thinner, adjustable
traces): the fan-out trace width and spacing are design inputs (0.127 /
0.127 mm by default, from JLC's 1 oz minimum of 0.1016 mm), the traces
converge into bundles at width + spacing with bus-style bends and widen to
0.254 mm in the tail; the fixed 0.246 mm Row and 0.17 mm Column route rules,
the 0.6 mm lane pitch and the 1.2 mm deck cap are gone.  Layout v3 (two route
pieces per net), generator 0.4.0, exporter 0.3.0, profile revision
2026-10-15; Row FPC 68.694 x 38.723842 mm, Column FPC 64.9 x 52.989032 mm;
the default build was then `tactile-fpc-12x32-f978429d...` (the straight Row
channel; since P5-diagonal-bus.md section 18 the default is the diagonal Row
bus, since section 20 `diagonal-bus/8`, CAD mode's rule set with one outline
down to the tail roots and the bottom tail 7.5 mm, `diagonal-bus/9` since
section 24, `diagonal-bus/10` since section 27 (the Row tail centred on the
field), both tails 12 mm since section 27.7, `diagonal-bus/11` since section
27.8 (one side's convex flank), the profile revision 2026-10-29 (the
gold-finger thickness order option and the coverlay-window notes), the
1.0 mm electrodes of the default fill 0.5 since 2026-11-06, the profile
revision 2026-11-06b (the 2-layer 0.2 mm order with its 0.1 mm PI
stiffener), build
`tactile-fpc-12x32-ba2e9b58bd8e`).*
