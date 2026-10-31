# Surface tactile arrays: plan, research and roadmap

Status, 2026-10-20: **CAD mode is implemented**, reviewed and hardened, as
described in [CAD_MODE.md](CAD_MODE.md).  This document keeps three things:

- why it is built the way it is: the measured facts and the decisions;
- the results on the example parts;
- what comes next.

The decisions are recorded with their IDs in `claude/specs/cad-mode/SPEC.md`,
and the step-by-step log is in `claude/specs/cad-mode/PROGRESS.md`.  The
first version of this plan (planar surfaces only) was reviewed by four
independent checks the same night; its corrections are folded in below.

## 1. What the user asked for

- Any CAD part, any surface.
- Drag the file in, rotate it, select a surface, set the resolution and
  other options, then Generate.
- Keep the rectangular mode as a separate mode.
- The server stays authoritative, behind stateless routes that carry the
  mesh.
- three.js "or anything better".
- Either electrode set may go to either connector, up to 64 x 64.
- Everything above the tail roots lies on the surface, with the margins as
  small as possible.  Superseded on 2026-10-21 by the user's routing
  decisions (claude/specs/masked-field/PLAN.md, section 9): as many taxels
  on the surface as possible, only the taxel field must lie on it, the Row
  traces on both sides (selectable) as straight diagonals so that the tip
  is the narrowest.  That is the default fit from 2026-10-22
  (`containment: field`); `containment: board` keeps the first rule.

## 2. How it works, in one paragraph

The browser shows the part (vendored three.js) and sends the STL with
every request; the stdlib package `surface/` does the geometry.

1. **Select.**  It grows the clicked surface: the default leaves out tight
   blends, so a flat sensor is never asked to follow a fillet.
2. **Flatten.**  It flattens the selection exactly when the surface is
   developable, and with a measured stretch otherwise.
3. **Fit.**  It searches rows, columns, routing, role mapping and a turn of
   up to 30° against the edge the tails leave through.  The footprints come
   from the engine's own plans for the new `surface_matrix_v1` template
   (tight margins, a direct fan-out, up to 64 columns).
4. **Verify.**  It generates the best candidates and checks their real
   outlines.
5. **Map.**  It maps every taxel back onto the part.

The design that comes out is an ordinary engine design.  The validation,
the whole-board DRC and the Gerber export are the existing ones.

## 3. Results on the example parts

All at 2.0 mm pitch with the defaults: the surface template, `shape: fill`
(masked fields merged with the rectangles, masked-field phase P4; CAD mode's
only shape and template since P5-diagonal-bus.md section 26.16) and
`containment: field` (only the taxel field on the surface, every proposal a
diagonal Row bus: phase P5e, 2026-10-22), edge margin 0, the base edge given.
`containment: board` keeps the whole stack above the tail roots on the
surface (the fit of phase P4); `shape: rectangle` gave the rectangular fit
of before (the Rectangle column; no CAD option since section 26.16, its
rectangles still among Whole board's, pinned by
`tests/test_surface_fit_snapshot.py`).

| Part, surface, tail exit | Rectangle | Whole board (`containment: board`) | Field only (the default) | Coverage (field only) |
| --- | --- | --- | --- | --- |
| Soft finger (`asset/soft_gripper_finger.stl`), flat contact face, tails toward the mount | 44 x 8 = 352 | 44 x 8 = 352 (masked fields stop at 32 rows) | 59 x 12 = 708 (tip 24.5 mm) | 89% |
| Same, within 32 rows (`max_rows: 32`) | 32 x 9 = 288 | 334 of 32 x 12 (87% sampled; the lane taper) | 417 of 32 x 31, turned 30° (8.6% more than the unturned 32 x 12 = 384) | 52% |
| Same, tails across the long side (`base: auto`) | 9 x 58 | 9 x 58 = 522 (the rectangle) | 59 x 12 = 708 (the mount end: the narrow tip) | 89% |
| Same, pitch at least 1.5 mm (`max_taxels`) | 49 x 10 = 490 | 49 x 10 = 490 (the rectangle) | 64 x 16 = 1024 at 1.53 mm | 76% |
| Crank tip (`asset/crank_gripper/tip_left.stl`), raised pad, `base: auto` | 17 x 18 = 306 | 549 of 30 x 32 (57% sampled) | 666 of 32 x 32 (65% sampled; the 70 mm leg, tip 14.5 mm) | 87% |
| Crank tip, FlexiTac reader (`reader: 32x16`, 16 + 32 lines) | 16 x 19 = 304 | 427 of 16 x 32 | 477 of 16 x 32 | 63% |
| Crank tip, `reader: auto` | 17 x 18 = 306 | 550 of 30 x 32 (the 32 x 32 reader) | 666 of 32 x 32 (the 32 x 32 reader) | 87% |
| Right-triangle plate, legs 60 mm (`tests/surface_fixtures.py`) | 13 x 14 = 182 | 325 of 24 x 26 | 406 of 28 x 28 | 87% |
| Equilateral-triangle plate, side 60 mm | 12 x 13 = 156 | 196 of 14 x 18 | 340 of 24 x 28 | 83% |
| Disk plate, radius 25 mm (an arc exit) | 19 x 12 = 228 | 261 of 16 x 17 (turned 10°) | 436 of 24 x 24 | 86% |

Measured before the user's correction of 2026-10-25 (coverage first,
P5-diagonal-bus.md section 21), since which masked fields take the
rectangles' caps (64 x 64, 32 x 32 before): the soft finger's whole board
470 of 50 x 12, the crank's field 683 of 34 x 34; docs/CAD_MODE.md
("Measured") lists the current numbers.

With field-only containment the Row traces' bands, the Column fan-out and
both tails may leave the surface (beyond its side edges and the exit), so
the field fills the face: every row- and column-convex shape builds on the
diagonal Row bus, the board is narrowest at the tip (the field's width at
ROW_01 plus 0.08 mm at 2 mm and 4 mil), and the map reports each board's
share on the surface (the soft finger's Row board 62%, its Column board
86%) and warns where a board crosses an edge sharper than a single FPC may
bend, a side or the base edge (`W_BAND_EDGE_RADIUS`: the soft finger's
square edges), with what to do.  A turned field ranks only with 3% more
taxels than the best unturned one (the soft finger within 32 rows: 417
turned against 384), and with `base: auto` the exits whose best field is
within 3 taxels of the most go by its tip (the crank pad: 666 on its 70 mm
leg with a 14.5 mm tip, not 669 at the cut corner with F 64.4 mm wide at
ROW_01).  Both tails end together, on one line across the boards (since
P5-diagonal-bus.md section 27.3; before, each the same distance past the
base edge under it): the nearer end the 20 mm asked past it, or farther
where the shortest tail (7.5 mm) sets the line (the soft finger with both
sides: 13.176 mm tails, the nearer end 20.001 mm past; with one side its
tail roots lie 14.527 mm past the base edge, so its 7.5 mm tails end
22.027 mm past).  A field-only fit takes 0.2-1.5 s on these parts on
Python 3.12 and 0.3-1.7 s on 3.9 (the same proposals), the whole-board fit
0.7-1.7 s and 1.0-2.5 s; a deterministic work budget bounds it at about
2-4 s on large non-convex faces at fine pitches.  After the P5d/P5e
reviews (2026-10-22) phase 0 lies on the usable edge (the equilateral
plate: 340 unturned, where its 339 turned 30° had been 1.8% above 333),
and narrow strips and small plates are never worse than the whole-board
fit.

With `containment: board` the masked fields are of the engine's straight
construction classes: a staircase on the field's far side and the lane
taper on the Row channel's side.  They fill right-angled faces (the crank
pad, the right triangle); on the equilateral triangle and the disk the far
side alone follows the outline.  After the P4 reviews (2026-10-21) the
count does not depend on `placement` or on `role_mapping: auto` against a
single role (each role is searched as it is alone), a named reader caps
the masked fields at its lines (`reader: 16x16` takes 235 of 16 x 16 on
the right triangle, as `max_rows`/`max_columns` 16 do), and the proposals
carry one mask per readout and none that an earlier one dominates (the
crank: 549 of 30 x 32, 548 of 28 x 32, 545 of 27 x 32, 541 of 26 x 32, then
the 17 x 18 rectangle).

Every proposal builds with the whole-board DRC clean, and every taxel map
passes its checks: on the surface, spacing along the surface equal to the
pitch, the boards (with field-only containment the taxel field) inside the
surface, stretch, bend radius, tail lengths and tail reach beyond the exit.

With the generic (rectangular-mode) rules, the soft finger gets 49 x 7 = 343
and the crank 16 x 15 = 240.  The surface template's margins give the
difference.

On synthetic parts (`tests/surface_fixtures.py` and a sweep in the log):

- a cone: 18 x 10;
- a tilted cylinder: 23 x 25;
- a wavy plate: 18 x 27;
- a face across the seam of two touching parts: 8 x 18.

Domes and saddles are cut to the disk a flat sheet covers.  Fingertip-sized
ellipsoids are refused, with the reason.

## 4. What the research measured

Six investigations on 2026-10-20 informed the design:

- **Flattening.**
  - Developable patches (planes with creases, cylinders, cones,
    extrusions) unfold exactly, even on decimated meshes.
  - On doubly curved patches the best flat map stretches by about
    `|K| rho^2 / 8` over a disk of radius `rho`.
  - Copper stays elastic only to about 0.2-0.3%.  A wrinkle-free bond
    allows about the same.
  - So the gate is 0.3%.  It covers a disk of about 9 mm on a 60 mm
    sphere (7-8 mm measured on welded test domes), 3 mm on a 20 mm sphere
    and about 1.5 mm on a fingertip.
- **Selection.**  A seed-normal cone is exact on flat faces but fails on
  curved ones.  Growth bounded by feature edges, minus tight blends
  (radius under 4 mm), selected the intended surface on every test shape;
  that is the `surface` preset.
- **Slit boards for domes.**  Two comb-shaped layers do **not** form a
  woven (Chebyshev) net.  A copper-on-polyimide strip cannot bend sideways
  in its plane, so each strip follows a geodesic, and the taxels sit where
  two geodesic families cross.  This works, with irregular taxels:
  - about `(0.8 R / p)^2` taxels per comb on a sphere of radius R, e.g.
    7 x 7 on R 20 mm at 2 mm pitch;
  - a "diagrid" layout puts five times more taxels on a fingertip dome.

  It needs slits in the engine (open item D8) and a surface solver.
- **Coverage.**
  - Turning the board against the exit edge gains 15-17% on round and
    triangular charts.
  - A 0.25 mm edge margin costs 0-7% against 0 mm.
  - Tight routing gains 22% on narrow faces.
  - Letting the fan-out wrap off the surface would gain 20-158%, but the
    user ruled it out.
  - Outline-following taxel masks would gain 37% on the crank pad.
- **Engine.**  The 16-channel lane limit was not a manufacturing rule.  A
  separate surface template (0.5 mm margins, tight channel, fan-out bends
  up to 85°, direct one-lane fan-out) raised the field-to-footprint ratio
  from about 50-60% to about 80%, DRC-clean on 1528 designs.  Generic
  designs keep their build ids, with a fixture of 200 frozen designs.
- **Compute.**  Standard-library Python and the browser's JavaScript gave
  bit-identical selections and flattenings; numpy did not (fused
  multiply-add, BLAS).  So the authority stays in stdlib Python:
  - exact methods are cheap: a rigid unfold of 17.6k vertices takes 0.27 s;
  - curved solves are capped at 3000 vertices;
  - a 500k-facet STL reads in 3.4 s, and parsed meshes are cached.
- **Viewer.**  three.js runs under the app's CSP without changes.  viser
  cannot (an inline WASM bootstrap), needs about 57 MB of Python packages,
  keeps state on the server and accepts foreign origins.

## 5. Roadmap

| Step | Content | Gain | Size |
| --- | --- | --- | --- |
| R1 | Taxel masks trimmed at the far ends (surface template S2): rows shortened away from the channel, columns away from the fan-out; polygon coverlay windows; per-electrode registration DRC.  Done for the straight classes (masked-field phases P1-P4, `shape: fill`); the boundary-following buses (P5, P6) are next | crank 306 -> 549 (done) | L |
| R2 | Slit comb boards and a geodesic surface solver (D8a/b): slits in the engine's outlines; strips traced as geodesics on the mesh; taxels at their crossings; layer-by-layer assembly | domes and fingertips: about `(0.8 R / p)^2` taxels per comb | XL |
| R3 | Browser crop transport and a worker: the browser parses, welds and grows the selection; it sends the region plus its 1-ring at full resolution and a 1 mm-clustered context | parts of 1-2 M facets with 2-4 MB requests | M |
| R4 | Split-only remeshing of coarse curved patches (longest-edge bisection) before ARAP, and a cut-and-re-flatten pass that trims blends above the gate | better strain-limited disks on coarse CAD meshes | M |
| R5 | STEP import through the optional `cascadio` extra (server side): one click selects an exact CAD face, and planes, cylinders and cones unroll analytically | exact CAD faces | M |
| R6 | A reader for more than 16 + 32 lines (64 x 64 boards build today; the FlexiTac reader reads 16 x 32).  The fit option `reader` already sizes the tails for 16 x 16, 32 x 32 and 48 x 48 readers and maps their lines | full 64 x 64 | hardware |

## 6. Open questions for the user

- **Edge margin.**  The default is 0, as asked.  The research suggests
  0.25 mm for assembly tolerance (JLC's outline tolerance plus placement),
  at a cost of 0-7% of taxels.
- **Tail exit.**  `auto` picks the side with the most taxels, which on the
  soft finger is a long side (onto the perforated Fin Ray caps).  Should the
  UI require an explicit exit edge?
- **Placement along the exit axis.**  The default is `far`: the field
  toward the tip, tails up to 80 mm.  The alternative is `near`, the
  shortest tails.
- **Routing.**  4/4 mil (0.1016 mm) is chosen automatically when it gains
  taxels.  JLC's +/-20% tolerance can make it 0.081 mm.  Keep the automatic
  choice, or prefer 5/5 mil?
- **Slits.**  Taking R2 on means deciding D8:
  - copper-to-slot of 0.2 or 0.3 mm;
  - slit width of 0.6 or 1.0 mm;
  - an accepted shear limit;
  - layer-by-layer assembly.
- **Reader.**  Confirm the 16 x 16, 32 x 32 and 48 x 48 readers' connectors
  and frame layouts (`reader` assumes the FlexiTac's 0.5 mm tails and
  `(SC - 1) x sense lines + (SR - 1)`).  Also record where swapped tails
  plug in; the taxel map gives SR/SC for every reader.
