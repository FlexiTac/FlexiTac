# CAD mode: a tactile sensor on a surface of a CAD part

CAD mode fits the app's sensor to a surface selected on a CAD part:

1. Drop in an STL.
2. Rotate it and select a surface.
3. Set the resolution and the other options.
4. Generate.

The result is an ordinary Row/Column FPC pair, with the same validation,
whole-board DRC and Gerber export as the rectangular mode.  It also says
where every taxel sits on the part.  The rectangular mode builds the same
diagonal Row bus as a field-only proposal (below) by default since
claude/specs/masked-field/P5-diagonal-bus.md section 18, and since section
20 it is a subset of this mode: CAD mode's rule set (the surface profile:
0.5 mm margins, up to 64 columns, tails from 7.5 mm) and construction
(`diagonal-bus/11`), so the same design builds the same boards in both
modes, only the build id differing; its Row traces select keeps the
straight Row channel on the standard profile, with its two-lane Column
fan-out.

The geometry lives in the stdlib package `surface/`, next to `engine/`.
The plan and the research behind it are in
[SURFACE_TACTILE_PLAN.md](SURFACE_TACTILE_PLAN.md).  The border of the
taxels that the user draws on the selected surface, and the exit edge
chosen among its edges, are in [CAD_BORDER.md](CAD_BORDER.md).

## The pipeline

| Step | Module | What it does |
| --- | --- | --- |
| Read | `surface/mesh.py` | Reads the file and builds the mesh.  See below. |
| Select | `surface/select.py` | Replayable operations, applied in order (see below). |
| Flatten | `surface/chart.py`, `surface/solve.py` | A planar patch is projected; otherwise the facets are unfolded rigidly across shared edges (exact on developable patches: creased pads, cylinders, cones, extrusions, with or without holes, however thin their strips; an unfolding counts when no vertex is placed twice more than 0.01 mm apart and every facet edge keeps its length to 1e-4 of it, plus the float32 spacing of the selection's coordinates); otherwise LSCM, then ARAP, measuring the stretch per facet (two sparse factorizations: about 1.5 s at 2900 vertices on Python 3.9).  A band round a part (two boundary loops) that does not unfold as it is, or whose normals cancel out (a prism's side walls, a symmetric closed cylinder), gets opened along a seam: the facets round the seam on its smaller side are left out.  A selection must be one connected piece.  Curved solves take at most 3000 vertices.  The last eight charts are cached. |
| Fit | `surface/fit.py` | Chooses and places an engine design on the chart.  See below. |
| Map | `surface/place.py` | Takes each taxel centre from the generated electrodes and maps it onto the part (barycentric in the chart).  Writes the taxel map, the 3D outlines, a 1:1 wrap template (SVG) and the verification records. |

**Read.**

- Binary STL (`84 + 50 n` bytes) or ASCII STL.  An ASCII solid's name is
  the rest of its `solid` line (and of its `endsolid` line), at most 4096
  bytes, so a name may hold any word; a solid written on one line (no line
  after its `solid` word) is read by words: its name runs to `facet` or
  `endsolid`, and after `endsolid` to the next `solid`.  Coordinates must lie within 1e9 mm of the origin after the
  unit scale (`E_SURFACE_MESH_NONFINITE`).
- The unit is guessed: a largest extent under 2 means metres, otherwise
  millimetres.  It can be overridden.  A part under 2 mm across (its
  largest extent) gets a `warning` to check the unit.
- Vertices are welded on their exact stored values.  Facet ids are the
  file order, so the browser and the server agree on them.
- A triangle repeated with the same winding counts once (the copies are
  `duplicate_facets`).  At an edge shared by more than two facets, each
  facet is linked to its neighbours by angle around the edge.  Walls lying
  on one another that run the same way are not linked at first: each body
  is oriented on its own.  If a facet of an oriented body next to them
  shows that one wall is wound the wrong way (a body wound inside-out next
  to another), that wall is turned round.  Walls that face the same way
  with no such sign (a body repeated with another triangulation, a patch
  lying on a face) are kept as written.  Two walls on one another that
  face each other are paired so that each body is linked to its own wall:
  touching bodies stay one shell however they are turned in space.  A
  repeated triangle that is the contact face of a body wound inside-out
  against another (a part and its mirror image) is kept and turned with
  its body.
- Cracks are bridged: a vertex lying on another facet's boundary edge (a
  T-junction, within 1 um) links the facets on both sides
  (`t_junction_links`).
- Each shell is oriented outward, by its signed volume about its own
  centroid; a shell inside a closed body (a cavity) is oriented toward its
  void.  A body is the facets joined through every edge they share (parts
  touching over a face are one body); it is closed when no edge is shared
  by an odd number of its facets and every open edge has a twin within
  0.001 mm (a gap of float noise, not a hole).  A cavity is told by ray
  parity from points inside the shell, by majority, so a part standing in
  an open shell, touching another or resting on a cavity's floor is not a
  cavity.  An open sheet that encloses nothing (up to the float32 rounding
  of its coordinates) keeps the file's winding
  (`orientation_ambiguous_shells`).
- Walls where two parts touch are found (coincident, opposite-facing
  facets).  Facets covered almost entirely are hidden; the covered parts
  of the others become obstacles.  The 0.05 mm plane tolerance shrinks
  for a part under 20 mm across (bounding-box diagonal).
- Pathological files stay bounded, with a `warning` in the mesh facts
  when a bound is reached:
  - at most 400,000 overlapping covered-wall pairs (a facet covered enough
    to be hidden is not clipped again);
  - 200,000 open edges and 2,000,000 T-junction tests (vertex tests and
    grid-cell visits); the cracks bridged before the limit stay bridged,
    and a spot of 0.01 mm where more than 64 open-edge ends meet is
    skipped on its own;
  - 2,000,000 tests to tell cavities from parts (box comparisons,
    open-edge twin tests and ray tests).

**Select.**

- `grow` from a clicked facet.  Its presets:
  - `surface` (the default): the smooth region up to 30° edges, without
    blends tighter than a 4 mm bend radius and without crossing a crease
    a 4 mm bend cannot follow (see **Bends**);
  - `flat`: dihedral angles up to 10° within 4° of the seed;
  - `smooth`: up to 30° edges.
- `disk`: a geodesic radius around the seed.
- `facets`: a brush or lasso result.
- `cleanup`.
- Hidden facets are never selected.

**Bends** (`surface/bend.py`, one model for the selection, the fit and the
map).

- A smooth bend (a fillet or cylinder in strips): its radius is the
  narrower strip's width across the edge divided by the edge's angle, at
  any tessellation density.  A strip's width is that of the flat piece at
  the edge (the coplanar facets, within 0.1° and half the edge's angle,
  that reach the edge's ends), so a strip split at a T-junction or into
  slivers keeps its width.  The bend belongs to the narrower strip, and
  the triangles of a strip share it.
- A crease (flat on both sides): a sheet of minimum radius R lifts off a
  crease of angle theta by about `R theta^2 / 8`.  Above 0.05 mm the
  crease counts as radius 0: 16.7° for the 4.7 mm field stack, 18.1° for
  the 4 mm preset, 34° for one 0.11 mm FPC.

**Fit.**

- The tails leave across an exit of the chart's outer boundary.  The exit
  is a straight side of at least 3 mm (`{side}`, or the side nearest
  `{point_xyz}` when that side is at least 20 mm long), or an arc of
  +-15 mm around a boundary point (`{arc}`; `{point_xyz}` when the nearest
  side is shorter than 20 mm, as for a click on a rounded edge or a short
  side; or `auto` on outlines without a 20 mm side).  A side ends at a
  corner or where its direction drifts by more than 1°.  `{side: n}`
  numbers the sides as `/select` returns them, also when a curved
  selection is cut to its strain-limited disk: the exit is then the
  longest part of that side on the disk (`E_SURFACE_BASE_EDGE` when less
  than 3 mm of it is left), and `placement.base_side` stays n.
- What CAD mode generates depends only on the selected area (the user's
  decision of 2026-10-26, P5-diagonal-bus.md section 26.16: "what CAD
  generates depends only on the area selected in CAD; rectangle mode is
  used on its own, without CAD"): the field follows the selection, masked
  fields too, on the surface template.  There is no rectangle shape, no
  generic template and no rectangle preference (a full rectangle is a
  field with every position, proposed where it ranks); rectangular fields
  are the rectangular mode's: rows, columns and the traces' parameters,
  without CAD.
- What must lie on the surface (the option `containment`):
  - `field`, the default: only the taxel field; the Row traces beside it,
    the Column fan-out and both tails may leave it, on the diagonal Row
    bus (see **Field-only containment** below);
  - `board` (Whole board, when asked for): everything above the tail
    roots, the field, the Row channel and expansion, the Column fan-out.
    The rest of this list describes this fit.
- Searched:
  - rows (1-64), columns (1-64);
  - both role mappings and both routings;
  - turns of up to 30° against the exit;
  - masked fields within the rectangles' caps, `max_rows` x `max_columns`
    (see **Masked fields** below; 32 x 32 before the user's correction of
    2026-10-25, coverage of the selection first), merged with the
    rectangles.
- A raster of the usable region gives the tallest base-anchored rectangle
  of each width.  The usable region is the chart minus:
  - holes;
  - covered walls;
  - facets stretched beyond the strain limit;
  - bends tighter than 10 x 0.47 mm (the laminated field, static).
- The stack is placed 0.1 um inside the usable cells, so a board side on
  the surface's edge stays on it after rounding.
- The best candidates are generated with `engine.generate_design`, and
  their real outlines are checked against the chart: inside it (only the
  tails cross the exit: every part of a board beyond the exit lies at or
  below its tail root), off holes and obstacles, and at least
  `edge_margin_mm` from the edge.  The clearance counts an edge that
  crosses the exit up to the crossing.  Each tail reaches
  `tail_extension_mm` beyond the exit's lowest point under its whole width
  (an arc exit sags between the tail's corners).  One proposal per rows x
  columns and taxel count.
- A curved patch that stretches too much is cut to the largest geodesic
  disk that flattens within the limit.  The radius is searched near the
  answer: regula falsi on radius² against stretch, between the largest
  disk within the limit and the smallest beyond it, and no trial more than
  1.5 x the largest disk within the limit until one exceeds it.  At most 7
  distinct trial disks are flattened (a radius that gives a disk already
  tried costs nothing), fewer once the radius is known to 1% or a disk
  stretches 99% of the limit, and none once the trials have flattened 6000
  vertices.

## Options of the fit

| Option | Default | Values |
| --- | --- | --- |
| `objective` | `fixed_pitch` | `fixed_pitch` (the resolution: most taxels at `pitch_mm`), `max_taxels` (most taxels at a pitch of at least `min_pitch_mm`, then the largest pitch), `max_area` (the largest field: the rows x columns staircase at the pitches `min_pitch_mm` x 1.15^k up to 10 mm, the best grown in 0.01 mm steps; the first such fit in a server process takes a few seconds while the board extents are computed) |
| `pitch_mm`, `min_pitch_mm` | 2.0, 1.0 | 0.6-10 mm |
| `fill` | 0.5 | electrode width / pitch, at most pitch - 0.25 mm (0.7 until the user's decision of 2026-11-06) |
| `edge_margin_mm` | 0 | clearance of the boards from the surface's edge (the board outline already keeps its copper 0.3 mm in) |
| `routing` | `auto` | `default` (0.127/0.127 mm), `tight` (0.1016/0.1016 mm), `auto` (both) |
| `role_mapping` | `auto` | `rows_top`, `columns_top`; it decides which board is glued to the part and on which side the Row channel lies |
| `reader` | `none` | the tactile reader the tails are sized for (either electrode set on either connector; see **Readers** below): `none` (one contact per line), `auto` (the smallest reader that holds the readout), `16x16`, `32x16` (the FlexiTac, 16 sense by 32 drive lines; alias `flexitac`), `32x32`, `48x48`.  A name gives the two connectors' line counts, the larger first (for `32x16` that is the drive count).  A named reader also caps the masked fields at its lines.  The option `connector` of earlier fits is still read: `channels` is `none`, `flexitac` is `32x16` |
| `shape` | `fill` | fixed (P5-diagonal-bus.md section 26.16): the field follows the selected area, masked fields that follow the surface within `max_rows`/`max_columns` merged with the rectangles (a masked field ranks before a rectangle only with more taxels; see **Masked fields** below).  A request may name `fill` (older clients; it is echoed and saved as before); `rectangle` (full rows x columns fields only, the fit of before masked fields, a CAD option until section 26.16) is `E_SURFACE_REQUEST`: rectangular fields are the rectangular mode's.  The browser has no Field shape control |
| `containment` | `field` | `field` (only the taxel field F, P and its 0.5 mm margin, on the surface, the margin at F's convex corners within 0.5 mm of it; the Row bands, the Column fan-out and both tails may leave it; every proposal a diagonal Row bus; see **Field-only containment** below), `board` (Whole board: everything above the tail roots on the surface: the rectangles and the masked fields of **Masked fields**, the fit of before phase P5e) |
| `tip_first` | `true` | `true`, `false`: with `containment: field`, the taxels stack from the fingertip (the end of the face opposite the exit; the user's request of 2026-10-26, P5-diagonal-bus.md section 26): within 3 % of the most taxels on an exit (a symmetric field's: of the symmetric fields there, since section 26.17) the field reaching nearest the fingertip is proposed first (reach first: at a pointed tip it may end in a single taxel), then in the place of the field it displaces that field's own tie (as many taxels or more, nearest the fingertip; the field itself only should the tie give no proposal; **Tip first** below); `false` keeps coverage first: a field gives its place only to such a tie, never to fewer taxels, so the proposals are those of sections 21-24 but for those places (section 26.17; a tie with more taxels may also dominate a later field of its readout, section 26.18).  Never with `max_area`; `board` ignores it |
| `row_sides` | `both` | with `containment: field`, the sides of the Row traces seen from outside with the tails down, written into every proposal as `routing.row_sides`: `both` (alternate rows on the two sides meeting in a funnel under the field; the narrowest tip; the Row pins fold), `left`, `right` (every row on that side, fanning in under the field; the Row pins in turn); in every side mode the Row tail is centred on the field and stacked on the centred Column tail (`diagonal-bus/10`); `board` ignores it |
| `placement` | `far` | `far` (field away from the tails), `near`, `center` |
| `rotation` | `auto` | `auto` (up to 30° against the base edge), `none` |
| `template` | `surface` | fixed (section 26.16): `surface_matrix_v1` (0.5 mm margins, up to 64 columns).  A request may name `surface`; `generic` (`generic_matrix_v1`, the rectangular mode's rules, up to 32 columns, a CAD option until section 26.16) is `E_SURFACE_REQUEST`.  The browser has no Board rules control |
| `tail_extension_mm` | 20 | 6.5-72.5 mm of tail beyond the exit (at least the 6.0 mm stiffener and its 0.5 mm clearance); tails stay within 7.5-200 mm (80 mm before P5-diagonal-bus.md section 23; the map of a placement saved from a generic-template fit before section 26.16 checks that template's 7-80 mm).  With `containment: field` both tails end on the nearest line across the boards on which each is at least the shortest tail (7.5 mm) long and ends at least this far past the surface's lowest edge under it (P5-diagonal-bus.md sections 27.3 and 27.4): the nearer end this far past that edge, or farther where the shortest tail sets the line, a tail root lying so far past the edge already that 7.5 mm reaches farther (the diagonal Row bus's tail roots, one level for both boards, lie 2.9-7.5 mm past it on the fixtures with `both`, the Row roots 4.1-10.4 mm before P5-diagonal-bus.md section 20, so 20 mm ends both tails there; the proposal's `tail_reach_mm`) |
| `strain_limit` | 0.003 | 0.0001-0.2: largest stretch of the flattened sheet (copper's elastic limit is about 0.2-0.3%) |
| `max_rows`, `max_columns`, `proposals` | 64, 64, 5 | caps (masked fields and rectangles alike since P5-diagonal-bus.md section 21).  With `containment: field` a cap never moves the exit, and a capped field's rows stack from the exit (**Caps keep the exit** below) |

## Masked fields (`shape: fill`)

This section describes the masked fields of `containment: board` (the fit
of phase P4, the whole stack on the surface); with field-only containment,
the default, see the next section.

A masked field keeps an ordinary R x C readout (the same ROW and COL nets,
connector pins and scan), but each Row electrode spans only its active
columns and each Column electrode only its active rows
([`matrix.mask`](API.md#field-mask-matrixmask)); a position outside the
mask has no copper crossing, so it always reads 0.  The boards' outlines
and the coverlay window follow the taxels, so a triangular face takes a
triangle of taxels.  `surface/fill.py` proposes the masks of the engine's
straight construction classes (claude/specs/masked-field/PLAN.md, phase P4):

- **The class.**  Seen from outside, ROW_01 is the row farthest from the
  tails and the Row channel runs straight along one side of the field (the
  right for `rows_top`, the left for `columns_top`).  Going down, each row
  starts where the lane taper of the rows above it lets it (one column per
  about pitch / bundle pitch rows: every 9.8 rows at 2 mm and 0.2032 mm),
  and its far end never recedes; a column that stops above the bottom row
  lies beside the Row channel.  Right triangles with the right angle at the
  exit's end, trapezoids, the taper beside the Row channel and quarter
  disks are of the class; isosceles and equilateral triangles and disks are
  approximated by a staircase on one side (phases P5 and P6 add
  boundary-following buses).
- **Exact free space.**  The search decides strips of the surface from the
  outline, holes, obstacles and bends themselves (no raster), with the
  edge margin and the rectangle fit's 0.1 um inset, so no cell is lost to
  the raster: a strip is free at x when the vertical segment across it is
  inside the outline and no edge, hole, obstacle or bend comes within the
  margin.
- **Search.**  Each role mapping is searched on its own, so
  `role_mapping: auto` finds what either role finds alone.  Per role, per
  exit (unturned; with `rotation: auto` the role's two best exits also
  turned by 10-30°), per lattice phase (half the pitch, the far side and
  the top row snapped to the surface's extremes, the phases of the role's
  best rectangles placed far; then quarters and eighths of the
  pitch on the role's two best frames), per routing: every top row and
  channel edge is walked down, each row ending at the largest column whose
  Row region (from the board's channel edge to the far crossing edge plus
  the 0.5 mm margin, over the row's band) is free.  Below the bottom row,
  both boards' bodies and fan-outs down to the deeper tail root must be
  free and both tails must reach the exit (at most
  `80 - tail_extension_mm` on the surface).  The lattices searched do not
  depend on `placement`: each mask keeps its highest and its lowest field,
  and the option takes the one farthest from (`far`) or nearest to
  (`near`) the exit first, the other if the first does not realize.  A
  mask found at one height only stays there.  With several
  pitches (`max_taxels`: the smallest and the next three 0.01 mm steps;
  `max_area`: the four best rectangles' pitches) the first is searched on
  every frame and the others on each role's two best frames.  The search
  is a heuristic over these phases: an option that changes the rectangles
  (the reader's tails, the caps) can move the masked count by a taxel or
  two either way.
- **Merged and realized.**  The rectangles of the raster search (above;
  `shape: rectangle`'s own proposals until P5-diagonal-bus.md section
  26.16) stay in the pool: a masked field ranks before a rectangle only
  with more taxels (then by pitch, turn, routing, role mapping, a denser
  readout).  The best
  are generated and their real outlines checked exactly; a masked field
  whose outline leaves the surface loses the far-end cell of the row nearest
  the failure (or its top row) and is ranked again, at most 3 times.  One
  masked proposal per readout, and none that an earlier proposal beats or
  equals in taxels on no more Row lines and no more Column lines (on the
  crank: 549 of 30 x 33, 548 of 29 x 33, 546 of 30 x 32, 546 of 28 x 33,
  543 of 29 x 32).
- **Size.**  Masked fields take the rectangles' caps: `max_rows` x
  `max_columns` (64 x 64), within a named reader's lines either way round
  (`16x16` caps them at 16 x 16, `32x16` at 16 x 32 or 32 x 16, and
  `auto` at the largest reader's 48 x 48), the rectangles also the
  readouts the reader holds (the user's correction of 2026-10-25, coverage
  of the selection first; P5-diagonal-bus.md section 21).  Before it they
  were capped at 32 x 32, so on the soft finger through its mount end the
  44 x 8 rectangle (352) stayed first; now the masked 50 x 12 takes 470
  taxels following the face's taper, the rectangle fifth.  Within 32 rows
  (`max_rows: 32`) the masked 32 x 12 takes 334 taxels against the
  rectangle's 32 x 9 = 288.
- **Caps keep the exit; the taxels stack at the fingertip** (the user's
  rule of 2026-10-25, P5-diagonal-bus.md section 23: "stack the taxels
  along the fingertip, the direction opposite my tail").  Caps smaller
  than the template's (`max_rows`, `max_columns` under 64, a named reader
  or `auto`) never choose the exit: with several exits the fit also runs
  without them (64 x 64, reader `none`); every exit that fit has fields on
  is searched again on its own with the caps (its capped fields would
  otherwise be pruned by larger fields on other exits; since
  P5-diagonal-bus.md section 26.18, before only that fit's first exit, so
  the right triangle's symmetric hypotenuse, first since section 26.17,
  left its legs no field under 12 rows: two proposals), their fields in
  that fit's exit order (its symmetric exits first), then the exits it has
  no field on (`keep_exits`).  Each exit is searched when the proposals
  reach its fields, so one whose fields would follow the last proposal is
  not searched (the proposals as with every exit searched first; over the
  named test faces' 68 capped fits with `base: auto` the searches' work
  +16.5 % and the CPU +6.5 % against section 26.17, every exit searched
  first +100 % and +73 %).  A field that the row cap holds takes the `max_rows`
  rows at the far end from the exit, the fingertip (`tip_window`; a
  rectangle taller than the cap is the best one in those rows), and the
  tails start where the taxels end and run down the face to the exit,
  however long (the surface profile's tails go to 200 mm since section
  23, 80 before; `tail_extension_mm` still sets the part beyond the
  exit).  Only past 200 mm is the exit searched again with the field moved
  toward the exit by the excess (`tip_reach_mm`, `reaching`, at most 4
  searches).  On the fin gripper face (`umi_trap_h75_tip11.8.stl`) with
  `max_rows: 32` the first proposal was 14 x 59 = 567 along a 74.3 mm long
  side, its tails leaving sideways; it is now the symmetric 32 x 10 = 254
  at the fingertip (ROW_01 6 wide at the 12 mm tip), its tails (68.2 mm)
  at the 25.8 mm mount end, the long side's 567 an alternative; with
  `max_rows: 16` 16 x 8 = 106 at the tip with 102 mm tails.  The fit
  without the caps costs a second and a third search when the caps are
  smaller (1.6 -> 2.1 s on the fin).
- **Metrics.**  `taxels` counts the active positions, `positions` is R x C,
  `sampled` their ratio, `mask_class` the boards' construction classes
  (null for a rectangle), `field_mm` the bounding field and
  `field_coverage` the area of the crossing region P over the surface's
  (for a rectangle the field's area, as before).  `outlines_uv.field` is P.
- **Generate.**  The proposal's design carries `matrix.mask`, in net
  indices; the form keeps it until rows or columns change, and through a
  switch to the Rectangular mode and back (that mode's template builds the
  full field; the mask goes with the form again in CAD mode).  The other
  edits keep it, but whether the engine can route it depends on the
  column pitch and the trace width and spacing (the lane taper of the Row
  channel): after such an edit Generate may answer `E_MASK_ROUTING` at
  `matrix.mask[i]`.  The form's note then lists the issue, and its button
  "Use the full field" drops the mask (or fit again in CAD mode).  A full
  mask is the rectangular design: the same build id.
- Masked fields are built on the surface template only, CAD mode's only
  template since section 26.16.

## Field-only containment (`containment: field`)

The default from phase P5e on.  The user's routing
decisions (claude/specs/masked-field/PLAN.md, section 9): the selected
surface holds as many taxels as possible, and only the taxel field has to
lie on it.  The Row traces' bands may lie beyond its
sides, the Column fan-out and both tails beyond the exit; every Row trace
runs as a slant from its row's end, so the board is narrowest at the tip,
and below the field it turns once into a fan and once into its contact
(with `both` the two sides meet in a funnel under the field; the Column
board has the straight one's copper, its tail centred, and the tails are
stacked, the Row tail on the Column tail; the boards overlap freely there).
Down to the tails' roots both boards have one outline, the union of the
field, the Row bands and funnel and the Column fan-out, so the films align
by their edges and both tails leave its bottom edge; below it each board
is only its tail (P5-diagonal-bus.md section 20: on the soft finger with
`both` both FPCs 40.23 x 138.40 mm, the Column FPC 39.82 mm wide before,
their tails 12.51 mm from the shared edge, 12.82 and 17.92 mm before; the
crank's stack 73.22 mm wide, 73.18 and 72.95 mm before; the counts, tips
and lengths as they were).  The Column V runs at most 80 degrees where
that roots the tails no deeper, so the Row funnel's fans keep 85 degrees
(the crank's and the plates' fans 76 -> 85; the soft finger's 67 and 70
and the disk's 76, with its V at 82, as they were).  Both outlines are regular: no
corner turns by less than 5 degrees but on a fillet, a flatter run being
one straight edge outside it (the soft finger's FPCs 40.2 mm wide at the
face's bottom, 39.6 before; the crank's stack 73.2 mm, 72.8; the counts
and the tails as they were), and each side from the tip corner down to
its widest point is one straight line wherever one line encloses it
within 1.0 mm, the tip corner moving out to meet it (P5-diagonal-bus.md
section 17: the soft finger's tip 24.48 -> 24.90 mm, the crank's 15.68 ->
15.91 mm, the 30 x 38 plate's with 4 mm corners 28.48 -> 28.90 mm; the
widest, the counts and the shares on the surface as they were; a curved
side, as the disk's, keeps its polyline).  Elsewhere that stretch is
convex (P5-diagonal-bus.md section 24, `diagonal-bus/9`): its convex hull,
each dent (the S-shaped kink where the lanes start beside a narrow tip, a
short step) bridged by the hull's edge where no deeper than a two-cell
step (1.79 mm at 2 mm), a deeper pocket kept; a slanted side down a
staircase (the crank pad's hypotenuse) is one straight line from the tip
corner to its convex bend into the funnel, which stays (the lanes turn
down beside the field's widest rows there; one line on to the funnel arm
would put the crank's corner 10.2 mm farther out).  On a receding field (a disk below
its equator) the Row traces follow the field inward down to its bottom
edge: on the disk plate with `both` they keep within 3.9 mm of the field
(11.4 mm before) and the Row tail root rises from 8.1 to 3.3 mm below it;
the shared outline still keeps the Column FPC's body there, whose
traces drop straight down beside the lower rows.
`surface/fieldfit.py` (claude/specs/masked-field/P5-diagonal-bus.md,
phase P5d) builds every proposal as a diagonal Row bus
([`routing.row_sides`](API.md#diagonal-row-bus-routingrow_sides), the
option `row_sides`), which builds any row- and column-convex field:

- **F.**  The crossing region P (each row's crossing strip and the fillers
  between rows) grown by the 0.5 mm field margin as a box, slab by slab.
  F lies inside the surface's outline less `edge_margin_mm`, the exit
  edge included (P may come up to the exit at the margin), outside the
  holes, covered walls and strained facets, and off bends tighter than the
  laminated stack may follow (4.7 mm), but for its **corner zones** (the
  user's corner tolerance, P5-diagonal-bus.md section 16, at every convex
  corner since section 24): at each convex corner of F (a run's end that
  the neighbouring row's run does not reach, and the outer ends of the
  first and last rows), F's margin within
  `min(0.5 mm, w / 3)` of P's corner across x and across y (w the
  crossing's width) may leave that usable surface by at most
  `CORNER_TOLERANCE_MM` = 0.5 mm, measured across x and across y (the box
  metric of the search's edge margin; with the 0.5 mm margin that always
  holds: every point of a zone lies within it of P's corner).  The taxels
  (P) always lie wholly on it, and every side of F keeps its full margin
  away from the corners (the middle third of a crossing's side at
  least), so the tolerance never widens a straight side, and a corner where
  the neighbouring run reaches as far or farther (an aligned or a concave
  end) keeps its whole margin.  Before section 24 only the field's four
  corners took it and every step of a staircase kept its margin, so a
  slanted side doubled a row wherever a step's corner left the surface
  (the crank pad 683, now 696; since section 26 its tip-first 688 goes
  first).  On rounded
  corners the full rectangle comes back: on 30 x 38 mm plates at 2 mm the
  corner radii 2, 3, 4 and 5 mm give 252, 252, 252 and 248 taxels (252,
  250, 248, 246 before; at 4 mm the board's corner lies 0.37 mm off
  across x and y, 0.53 mm along the diagonal).  The search decides it on
  the exact free space of **Masked fields**.
- **Search.**  Per pitch, exit (unturned, and with `rotation: auto` the two
  best exits turned by 10-30°) and lattice phase, a run of a row is free
  when its crossing strip, its margin across x between the zones and its
  margin across y between them lie each in one free interval, and each of
  its four zones apart (at sparse pitches, a gap between rows wider than
  twice the margin, the filler band up to the next row over the two rows'
  common extent, as the engine builds the filler: exactly since
  P5-diagonal-bus.md section 26b; it was held over the lower row's whole
  run, which kept pointed fingertips bare; a full rectangle's rows share
  their runs).
  Between a run (a', b') and the run (a, b) above it, a' >= a holds the
  lower run's top left zone, a' <= a the upper run's bottom left zone,
  b' <= b the lower's top right and b' >= b the upper's bottom right, so
  only F's convex corners use the tolerance.  Phase 0 puts the first column's
  and the first row's grown strips on the usable edge (the frame's outline
  extremes less the edge margin), so a strip only as wide as one crossing
  and its margins still takes a column; the coarse phases add the phase
  that centres the whole lattice in the usable extent (a symmetric face's
  field keeps the same room at both ends: the rounded plates' corners).  A dynamic program finds the
  largest row- and column-convex set of free runs exactly (going up, the
  left ends first widen then narrow, the right ends too; four monotonicity
  phases, the predecessors from prefix maxima, O(R x C^2) per lattice; the
  corner rule folded in exactly: a condition every predecessor of a phase's
  range meets masks the row below before the maxima, one the state always
  needs leaves it out, one only the aligned end meets moves the range's end
  by a cell; it
  stops once no state can still beat the threshold, each state bounded by
  the runs above it within the ends its phase allows), and a second search
  the largest full rectangle.  Shaped fields and rectangles take the same
  caps, `max_rows` x `max_columns` (64), a named reader's lines either way
  round, `auto` the largest reader's 48 x 48 (section 21: shaped fields
  were capped at 32 x 32, so on a long face a thin rectangle beat the field
  following it).  A lattice larger than the caps
  is first searched whole (no window holds more, and its field is the
  answer when it fits the caps), then window by window, best bound first: a
  window's bound is its rows' longest runs, and around a blocked cell (a
  hole) the field gives up one of the four quadrants at it, which bounds
  the window tighter.  The unturned frames first: the coarse phases (0 and
  p/2) on every exit, then the quarter phases on every exit; then the
  symmetric lattices of the symmetric exits (**Symmetric faces** below);
  then the turned frames (coarse, then quarter phases on the two best
  exits without a symmetric field), each only
  where it can beat the best unturned field by 3 %, so that no turned
  field prunes the unturned search.  `max_taxels` and `max_area` search
  their further pitches (0.01 mm steps; the smallest x 1.15^k up to
  10 mm) on the two best frames of each kind, and `max_area` first seeds
  two exits at every pitch from the largest down (a capped field has the
  most area there), so that its area prunes the small pitches' large
  lattices.  Besides the best field the search keeps one other readout
  within 3 % of it (the proposals' alternatives).  The search stops after
  3 million cells of DP work (a deterministic count, `WORK_BUDGET`, about
  2-4 s): the fixtures below need at most 1.9 million and are exact; a
  large non-convex face at a fine pitch, or a long face whose lattices
  exceed the 64 x 64 caps, keeps the best fields found by then (a 150 x 30
  mm strip at 2 mm: the unturned 64 x 14 = 896 in 2.6 s; searched to the
  end, 66 million cells in 54 s, a masked field turned 30 degrees, 961).
- **Rank.**  More taxels (`max_area`: a larger P), then the larger pitch,
  the smaller turn, the unmasked field, the denser readout, the fewer
  corners that use the tolerance (of two fields alike, the one wholly on
  the surface).  A turned field
  ranks only with at least 3 % more taxels than the best unturned one.  When
  the fit chooses among several exits (`base: auto`), the fields within 3
  taxels of the most, or within 1 % of it when that is more, go first,
  their exits ordered by the tip of each exit's best such field, the
  narrowest first, and each exit's fields by rank (the user's answer: on
  the crank pad the cut corner holds 669 taxels, 670 with the corner
  tolerance, with F 64.4 mm wide at ROW_01, the 70 mm leg 666 with F 14.4 mm
  wide there, a 14.5 mm board tip; the 1 % keeps that answer; with shaped
  fields up to 64 x 64 the cut corner 686 with F 68.4 mm wide there, the leg
  683 of 34 x 34 with F 12.4 mm, a 12.7 mm board tip).  The tip chooses the exit, not the
  field: on one exit a full readout still ranks before a masked one of the
  same readout, which it then dominates.  **Coverage first** (the user's
  correction of 2026-10-25, P5-diagonal-bus.md section 21: "CAD
  generation is about covering the selected region first"): no rule puts
  a rectangle before a field with more taxels by default.  On the
  fin-gripper face (119 mm long, 25.8 mm wide over its 45 mm straight part
  at the mount end, then tapering to a 12 mm tip) the fit proposes the
  masked 59 x 12 = 569 following the taper, unturned, its tails at the
  mount end and ROW_01 at the tip (11.1 mm board tip); before, 8 x 47 = 376
  along a long side with the tails leaving sideways.  The **rectangle
  preference** (`rectangle_preference_pct`, off by default since section
  21: a full rectangle within that share of a masked first field went
  first) is gone with section 26.16 (CAD mode fits the selected area): a
  request may name it with 0 (nothing changes), any other value is
  `E_SURFACE_REQUEST`.  On a 50 mm square with one 5 mm cut corner the
  masked 24 x 24 (575) goes before the full 23 x 24 (552, 96.0 %); on the
  30 x 38 plate with 5 mm corners the masked 248 is first.
- **Symmetric faces** (the user's request of 2026-10-25,
  P5-diagonal-bus.md section 22: "if the geometric face is symmetric, make
  the sensor symmetric too, as far as possible").  Per exit, the axis runs
  through the midpoint of the exit's chord (a straight side's ends, an
  arc's ends), perpendicular to it; the face is symmetric about it when
  its outline and holes, mirrored about it, lie within 0.05 mm of
  themselves (sampled at every vertex and every 1 mm along each segment,
  so sides split into several segments, a faceted arc and flattening
  noise pass; `fieldfit.exit_symmetry`; with a border the border's part
  on the surface, [CAD_BORDER.md](CAD_BORDER.md)).  On such an exit the search adds
  lattices centred on the axis, a column on it (odd column counts) or the
  axis between two columns (even ones), with as many columns on each side,
  at the coarse row phases on every pitch and the quarter and centred row
  phases at the exit's best pitch, and finds the largest field whose every
  row is its own mirror image (first + last = C + 1) exactly: such runs
  about one centre are always row-convex, and the field is column-convex
  when their half widths first rise, then fall, so a dynamic program over
  rows and half widths (prefix and suffix maxima, the same free runs,
  filler bands and corner zones as the other fields) finds it in time
  linear in both, outside the work budget and the other fields' pruning;
  the best readout per exit and one other within 3 % are kept.  An exit
  whose symmetric field holds within 20 % of its best unturned field is
  not turned (a turned field breaks the symmetry), so none of its turned
  fields is searched, however large: a turned field leads a symmetric
  exit only where its unturned fields already pass the threshold (the
  lead's decision of 2026-10-28, which the user may override: turned
  fields get no tip pass; the MakerMods Metal's turned fields at
  +-30 degrees, 20.3-23.6 % larger than its symmetric field, are not
  searched).  **Symmetric first** (the user's decisions of 2026-10-27,
  P5-diagonal-bus.md section 26.17: "widownx这种对称面也居中" [sic], faces
  symmetric like the WidowX's take a centred sensor too; and section
  26.19: "可以加个门槛", a threshold can be added, its 20 % the lead's example):
  a symmetric exit's best symmetric field goes before the exit's other
  fields unless one of them holds at least 1.2 times its taxels
  (`SYMMETRY_GAIN`; with `max_area` its area; at exactly 20 % more it
  does); once one does, the fields keep their order, so a field with less,
  on that exit or another, may come before it too.  Each symmetric exit's
  best symmetric field that holds within 20 % of the most taxels of all
  the fields is proposed first, the narrow tip choosing among several
  (within its tolerance of the best of them, the narrowest tip first);
  then the other fields in order, each exit's best symmetric field before
  that exit's other fields when it holds within 20 % of their best.  The
  comparison is made on the search's fields, before the tip step, so the
  tip never flips it: symmetry costs under 20 % (but where the symmetric
  group's tip pass finds a bigger symmetric field after the decision, 3 of
  264 named grid fits: P5-diagonal-bus.md section 26.19), the tip at most
  3 % more of the best symmetric field.  With a cap the exits are those of
  the fit without the caps (section 23), where the symmetry is judged.
  Section 22 had the same rule with 3 % (the turned fields' share),
  section 26.17 none (a symmetric field first, an exit with one never
  turned).
  A larger asymmetric field stays an alternative: one
  proposal per readout and kind, full or masked, symmetric or not.  A
  symmetric field that leaves the surface in the build loses both end
  cells of a row.  Measured (pitch 2 mm, proposal 1; before -> now): the
  fin-gripper face 569 at its mount end, 0.2 mm off its axis -> 568
  symmetric there (ROW_01 4 taxels, tip 10.8 mm), the 569 second; the soft
  finger's 708 now centred on its face (0.70 mm off before; the bands'
  overhang 7.65 / 6.37 -> 6.98 / 7.10 mm beside it), with the 48x48 or
  `auto` reader 620 turned 30 degrees -> 576 (48 x 12) symmetric, with
  `max_rows` 32 418 turned -> 384; the 150 mm face tapering from 40 to
  20 mm 937 along a long side -> 924 symmetric at its 40 mm end (tip 20.5
  mm), the 937 second; the equilateral plate 341 -> 342 symmetric, the
  isosceles triangle (base 50, height 60 mm) 327 on a leg -> 318 symmetric
  on its base, the disk 440, the 30 x 38 plates 252 / 252 / 252 / 248
  symmetric, the right triangle (legs 70 mm: an isosceles right triangle)
  562 on a leg -> 552 symmetric on its hypotenuse (1.8 % fewer).  The
  crank pad, the parallelogram and the bitten square (no symmetric exit)
  keep their fields.  Until section 26.17 the holed plate (its symmetric
  fields reach 247 around the central hole), the isosceles triangle and
  the right triangle kept a larger field breaking the symmetry first;
  section 26.17 put the symmetric field first on all three; since section
  26.19 (pitch 2 mm) the holed plates' turned 31 x 32 = 396 and 30 x 32 =
  344 first again (their symmetric 247 and 209 hold 62 % and 61 % of them;
  not among the five proposals, all larger), the isosceles triangle's base
  328 (its leg's 341 next, 3.96 % more; since section 26.18 its tip-first
  322 first, the 328 next), the right triangle's hypotenuse 576 (its leg's
  595 next, 3.3 % more).  On a 44 mm plate with a 2 mm hole on its axis
  the symmetric 420 leads an asymmetric 500 (19.0 % more, 58 mm long) and
  follows a 510 (21.4 % more, 59 mm long).  The symmetric lattices
  also find fields the others miss: on the 30 x 38 plate with 5 mm corners
  the full 17 x 14 = 238, centred (224 before; shape rectangle's first
  until section 26.16), the fin's tip end 570.
- **Tip first** (the user's request of 2026-10-26, P5-diagonal-bus.md
  section 26: "I want the taxels to stack starting from the fingertip as
  far as possible"; `tip_first`, on by default).  On a gripper the
  fingertip, the end of the face opposite the exit where the tails leave,
  is where contact matters.  After the order above (the exits, the narrow
  tip, symmetric first and the caps' exits are chosen exactly as before),
  each of the first `proposals` fields the fit would propose (one per
  readout and kind, none dominated) leads its group, its exit, pitch and
  symmetry kind, when it is unturned.  The group's tip pass looks again at
  the lead's lattices (its frame at its pitch: the quarter phases and the
  centred one; a symmetric lead's symmetric lattices of both parities at
  the eighth row phases k p/8 and the centred one, since
  P5-diagonal-bus.md section 26.18: its columns are fixed by the axis, so
  the row phase alone moves it toward the tip), within the caps,
  section 23's window and its tails' reach, and takes per lattice and top
  row the best field whose top run lies in that row (the dynamic
  programs' row maxima at the floor, exact; a masked or asymmetric lead
  the shaped fields, a symmetric one the symmetric fields, a full one
  full rectangles only, so a full rectangle never turns into a notched
  field for a fraction of a millimetre).  The floor is the lead's taxels
  or 97 % of the most taxels on the exit at that pitch, whichever is less:
  an asymmetric lead's of both symmetry kinds, a symmetric lead's of the
  symmetric fields there (the user's decision of 2026-10-27,
  P5-diagonal-bus.md section 26.17: the tip costs at most 3 % of the best
  symmetric field, symmetry itself under 20 % since section 26.19).  A
  field's reach is its top row's far edge from the exit (integer
  nanometres); of the fields reaching within half a row phase's step of
  the farthest (p/8 for the quarter phases, a symmetric lead's p/16), the
  one with the most taxels (then `field_rank`, fields alike reaching
  farther first) goes first, flagged in the proposal key, and the lead
  follows it.
  **Reach first** (the user's decision of 2026-10-26, P5-diagonal-bus.md
  section 26.16: "if the gripper is very pointed, it can stick out just
  one taxel"): at a pointed tip the tip-first field may end in a single
  taxel, whatever it leaves bare beside it (the tip-zone guard of section
  26.15 is gone).  Between the tip-first field and the lead (section
  26.15) the lead's own zero-cost tie: of the fields with at least its
  taxels, the one reaching within p/8 of the farthest of them (what the
  field with the most taxels looks like when it also reaches for the
  fingertip); it takes the lead's place (P5-diagonal-bus.md section
  26.17): the lead follows it only to be proposed should no field in its
  place be proposed with at least its taxels (the tie not built, or
  peeled under them), and when the tip-first field is that tie itself it
  takes the place.  With `tip_first: false` the lead gives its place only
  to its tie (coverage first, never a taxel given up): the proposals are
  those of coverage alone (sections 21-24: their number and their exits,
  frames, pitches and symmetry kinds in order) but for the leads' places
  (all 147 named fits of section 26.17's check, 146 since section 26.18,
  where a tie with more taxels on an eighth row phase dominates a later
  field of its readout; round 3c proposed the lead beside a tie of another
  readout and differed from coverage alone on 16, pushing another exit's
  field out of the five on 6).  A tip-first field that
  cannot be built, or whose peel takes it below the floor, out of its lead
  or (from a full lead) into a notched field, gives the slot back to the
  lead.  Each pass has its own work meter (3 million cells,
  `TIP_WORK_BUDGET`; the search's untouched); past it the pass keeps what
  it found (`tip_complete` false in its exit's record of `bases`, which
  also gives `tip_work`).  The fingertip is the end of the face opposite
  the exit: with `base: auto` the fit chooses the exit, so on a gripper
  give the gripper's back edge as the exit.  Measured (pitch 2 mm,
  proposal 1, before -> now): the crank pad 696 -> 688 (98.9 %, its tip
  gap 1.2 -> 0.7 mm, the 696 second), the 150 mm long taper 844 -> 842 (64
  x 18, 2.1 -> 0.6 mm; the 844's tie second, 0.5 mm nearer the tip than
  the 844 the search kept, and the 846's likewise), the disk 448 as 24 x
  24 (24 x 23 before, 1.3 -> 0.6 mm; the 24 x 23 no longer proposed since
  section 26.17: the 24 x 24 is its tie and takes its place), the rounded
  plates' full 252 / 252 / 252 and r5's masked 248 (18 x 14 less 4 corner
  cells), nearer their far side (1.3 / 1.6 / 1.3 / 1.3 -> 0.6 / 1.1 / 1.3
  / 0.6 mm, the corner tolerance used by r2 and r5 now: 0.18 and 0.34
  mm), the soft finger 708, the fin 572 (its long side's tip-first 560
  before that side's 570), the isosceles 341, the equilateral 353, the
  holed plate 396 (turned: untouched), the right triangle 595, the cut
  square 577, every exit as before (since section 26.17 the isosceles
  triangle's base 328 and the right triangle's hypotenuse 576 first, the
  holed plate's 247 from section 26.17 to 26.19: **Symmetric faces**
  above); the fin with
  `max_rows: 16` 104 first (then the 106's tie in the 106's place; its
  tails 103.025 mm, 103.275 mm since section 26.18, 103.271 mm with section
  27's centred Row tail).  Since section 26.18
  a symmetric lead's tip-first field takes the eighth row phases: the
  isosceles triangle's base a 322 reaching 57.15 mm first, 2.85 mm short
  of its apex (its 328 3.3 mm short before, 1.65 pitches: severe), the
  equilateral's 349 an eighth phase nearer its apex before its 353, the
  soft finger's and the fin's symmetric fields 0.25 mm nearer their tips;
  on the 732 gripper frames the mean tip gap of proposal #1 1.14 -> 1.07
  mm, no gap longer.  With `tip_first: false` the proposals are coverage
  alone's (sections 21-24), a lead's tie in its place: the crank with
  `base: auto` on its side 5 a 374 (that side's tie of its 361, with more
  taxels), the disk's 448 as 24 x 24, the rounded plates' fields 0.5-0.7
  mm nearer their far side, the long taper's 844 and 846 0.5 mm nearer
  the tip.  On
  the gripper video's 732 frames (proposal 1): severe / moderate / ok 13 /
  139 / 580 before section 26 -> 0 / 100 / 632 at -0.90 % taxels (no field
  under 97 %; the quick fix of main 0 / 120 / 612, `tip_first: false` 0 /
  117 / 615); the video's own pick (the most taxels) 1 / 118 / 613, none
  worse than main.  Since section 26.17 (symmetric faces centred; measured
  on the video's recipes of 2026-10-27): 0 / 99 / 633 at -1.16 % (the
  lowest 92.1 % of 55ae8fe's, on the WidowX at 2.65 mm, its symmetric 82
  first; at 3.35-3.5 mm its symmetric 7 x 7 = 49 where the asymmetric 9 x
  7 = 53 was; every WidowX frame's first proposal symmetric and ok),
  `tip_first: false` 1 / 118 / 613, the video's former pick (the most
  taxels; the video tool shows proposal 1 now) unchanged; the 744 file's
  fill cases 0 / 68 / 448 at -1.16 %.  Since section 26.18 (a symmetric
  lead's eighth row phases): 0 / 98 / 634 at -1.15 %, the mean tip gap
  1.14 -> 1.07 mm (no frame's longer; the WidowX's 0.86 -> 0.65 mm); the
  744 file's fill cases 0 / 66 / 450.  Section 26.19's threshold changes
  no proposal on the 732 frames or the 744 file (the largest excess of an
  asymmetric field on a symmetric face, the WidowX's 53 against its
  symmetric 50, 6 %).  That day's video
  was rendered with a quick fix (section 26.14: fields alike ranked by
  their reach in `field_rank`, the
  filler between rows left to F's check), which this replaces:
  `field_rank` is as before, so the tip never chooses an exit.
- **Realize.**  Each winner is built with default routing and `rows_top`
  first (the other routing and role mapping only when the engine refuses
  one), its tails long enough that both end on one line across the boards,
  square to the tails, so the stacked contacts line up (the user's request
  of 2026-10-27, P5-diagonal-bus.md section 27.3): the nearest line on
  which each tail is at least the shortest tail (7.5 mm) long and ends at
  least `tail_extension_mm` beyond the surface's lowest edge under it
  (section 27.4; as first built the line also went as far as the deepest
  root's shortest tail reached past its edge).  So the nearer end lies just
  that far past its edge, or farther where the shortest tail sets the line,
  and on an arc, a slanted exit or a turned field (whose exit is slanted
  across the boards) the tail over the higher edge ends farther.  The bus's
  two tails leave one bottom edge, so they are as long, and the 7.5-200 mm
  template limits hold (no tail longer than before).  Before section 27.3
  each tail ended the extension past the edge under its own width (the
  slanted plate's 16 x 12: 1.732 mm apart).  The other containments (whole
  board, the straight Row channel) keep each tail's own end: their tails
  lie side by side, not stacked.  The usual DRC and registration with the
  bus's stack keys.  Its F less the corner zones is checked exactly (the
  exit a wall): P with its margin across x and P with its margin across y,
  each short of the zones; a field that leaves the surface loses the end
  cell of a row nearest the failure, at most 3 builds.  One proposal per
  readout, none that an earlier one dominates.  Where a masked field misses
  cells at a corner, both boards cross the notch on a chamfer
  (diagonal-bus/6, [LAYOUT_SCHEMA.md](LAYOUT_SCHEMA.md#diagonal-row-bus)).
- **No rectangle shape** (since the user's decision of 2026-10-26,
  P5-diagonal-bus.md section 26.16): `shape: rectangle` with field-only
  containment (full rectangles only, P5-diagonal-bus.md section 16) and
  the generic template's whole-board rectangles were CAD options; a fit
  naming them is now `E_SURFACE_REQUEST` (the reason names the rectangular
  mode).  A rectangular selection still takes a full field (the 40 x 24
  mm plate: 19 x 11 = 209, no mask), since a full rectangle is a field
  with every position.  A placement saved before that names them maps as
  fitted: the map fits nothing (the design's `template_id` picks the
  template) and takes any value of `shape`, `template` and
  `rectangle_preference_pct` that a fit then accepted (rectangle or fill,
  surface or generic, 0-100 %; anything else is `E_SURFACE_REQUEST`, since
  P5-diagonal-bus.md section 26.17; and since section 26.18 not, on the
  generic template, `shape: fill`, `containment: field` or more than 32
  `max_columns` named, which that fit refused with the messages it still
  gives); `shape: rectangle` or `template: generic` in options that name no
  `containment` defaults the map's to `board`, as such a fit had it.
- **Metrics.**  Besides those of **Masked fields**: `containment: field`,
  `min_clearance_mm` the clearance of F less its corner zones, `tail_reach_mm`
  (how far the nearer of the tails' ends lies beyond the surface's lowest edge
  under it; both end on one line, the nearest on which each tail is at least
  the shortest tail long and ends at least the extension past its edge:
  farther than asked only where the shortest tail sets it), `row_bus`
  (`sides`, `tip_width_mm`, `tip_excess_mm`, `band_mm`, `widest_mm`,
  `tail_position` where the Row tail lies (`centred`: on the field in every
  side mode, `diagonal-bus/10`), `tails` `stacked` (the Row tail on the Column
  tail, both centred), `shared_outline_below_field_mm` (how far below the
  field both boards have one outline: F's bottom, 0.5 mm), `row_contact_order`
  the Row nets at the tail's contact positions, `row_pin_order` the Row nets
  by pin from the pads), and `tip` (unless `max_area`; with `tip_first: false`
  too, no field then a lead: `reach_mm` an unturned field's reach from the
  exit, None turned, `lead` whether it is a tip-first field in its group's
  lead's slot, and for a lead `farthest_mm` the farthest reach of its pool,
  `displaced` the rank of the proposal in the place of the field it displaced
  (that field's own, its tie's that took its place, or the lead's own when it
  is that tie itself; None only when none was proposed: section 26.17),
  `taxels_given` (what the tip cost: how many taxels fewer than the lead it
  displaced, or than a larger field of its own pass; never negative, and at
  most the lead's taxels less the floor unless the pass found more; since
  section 26.18, counted from the share's measure before, which could be
  another readout's field never proposed in the lead's place) and `complete`),
  `symmetry` (`face`: whether the selection is symmetric about the exit's
  axis, `deviation_mm` how far its mirror image lies from it, None beyond 1
  mm, `axis_mm` where the axis crosses the exit from its start, `field`:
  whether every row of the field is its own mirror image about it,
  `field_offset_mm` the field's centre from the axis; the card's Symmetry line
  on a symmetric face), and `routing_on_surface`: per board its `on_surface`
  share of area (the holes are not surface) and its `overhang_mm` (`left` and
  `right`: the farthest corner off the surface beside it, not past the exit
  under it and not below the surface's lowest point, so the tails and the bus
  past the base edge do not count; `exit`: how far the board above its tail
  root reaches beyond the exit, at its corners and where it crosses the root's
  level, beside the surface beyond the base side's line continued: on the soft
  finger with `both` 7.5 mm for both FPCs, whose outline is one down to the
  tails' roots: 7.2 mm for the Row FPC's funnel and 2.1 mm for the Column
  fan-out before section 20; the crank's 6.3 mm, 9.9 and 3.8 mm before).  The
  proposal card shows the one outline down to the tails' roots (its Outline
  line), where the Row tail lies and that the tails are stacked, the top FPC's
  over the bottom FPC's, and part to their own connectors (on the soft finger
  with `both` a 40.2 mm wide Row FPC, its 12.5 mm tail under the funnel, and a
  Column FPC as wide down to the tails' roots, its 12.5 mm tail centred under
  the face and on the Row tail, as with one side; both FPCs 138.4 mm long,
  each tail ending 20 mm past the base edge).  Sharing the outline puts the
  Column FPC's blank film under the bands off the surface too: on the soft
  finger 73 % of the Column FPC lies on the surface (95 % before the shared
  outline, 77 % with it over the face only), and it overhangs the sides 7.6
  and 6.4 mm as the Row FPC does (none before); on the crank 77 % (87 %,
  81 %).
- **Map.**  A map request whose options (or the placement's) name no
  `containment` takes the design's own: `field` for a diagonal Row bus
  (only field-only fits build one), `board` otherwise, so a placement saved
  before the option maps as it was fitted.  An explicit `field` maps a
  straight-channel design too (F of its full field is its active region).
- **Measured** (default pitch 2 mm, fill 0.7, the default fill until 2026-11-06; `containment: board` in
  brackets; since the user's correction of 2026-10-25, coverage first,
  P5-diagonal-bus.md section 21, and symmetric faces, section 22): the
  soft finger's contact face through its mount end 708 as 59 x 12,
  centred on the face (470, a masked 50 x 12; the 44 x 8 rectangle 352
  before), with the 48x48 reader 48 x 12 = 576 (620 of 48 x 38 turned 30
  degrees with section 21 alone), and 384 with the FlexiTac; the crank pad
  with its exit on the 70 mm leg 688 of 34 x 34 (546), the tip-first field
  of section 26 (696 before it, now second), and with `base: auto` the
  same field (666 of 32 x 32 before section 21, 683 before section 24);
  the fin-gripper face 572 of 59 x 12 at its mount end,
  symmetric (568 before section 24, 569 0.2 mm off its axis with section
  21 alone; 8 x 47 = 376 along a long side before); right-triangle plate
  (legs 70 mm) the symmetric 576 on its hypotenuse, then 595 on a leg
  (451; 552 symmetric first before section 24, 595 first from section 24
  to 26.17); equilateral plate (60 mm) 353 symmetric (196; the tip-first
  349 first since section 26.18, the 353 second); disk (r 25 mm) 448
  (261); holed plate the turned 31 x 32 = 396 (the symmetric 13 x 19 =
  247 first from section 26.17 to 26.19, its turned fields not searched)
  (330)
  (with the corner tolerance at every convex corner, section 24; with it at
  the field's four corners 562, 342, 440, 375; before it 559, 340, 436,
  375).  0.3-2.6 s
  per part on Python 3.12 and 0.8-3.5 s on 3.9.6 at the default pitch
  (the crank 1.3 -> 0.8 s and the fin 2.9 -> 1.2 s with the larger caps:
  fewer windows); the pitch ladders of `max_taxels` and `max_area`
  0.3-3.3 s on 3.12 and 0.4-3.7 s on 3.9 (measured before section 21).
  The slow inputs, bounded by the work budget: a 60 x 40 plate with a
  round hole (r 6 mm) at 1.5 mm 588 in 3.0 s (532 at 32 x 32), the board
  fit 453 in 2.2 s (411); long faces at 2 mm 2.6-4.3 s (a 150 x 30 mm strip,
  a 150 mm face tapering from 40 to 20 mm, a 140 mm square, a disk of r
  70 mm; 0.5-6.7 s before).

## Readers

The fit option `reader` sizes both tails for a tactile reader (either
electrode set on either connector, unused positions as isolated NC
contacts) and the map reports its lines.  A reader is named by its two
connectors' line counts, the larger first (`32x16`: 32 drive lines and 16
sense lines):

| `reader` | Sense lines (FPC1) | Drive lines (FPC2) | Frame index |
| --- | --- | --- | --- |
| `16x16` | 16 | 16 | `(SC - 1) x 16 + (SR - 1)` |
| `32x16` (`flexitac`) | 16 | 32 | `(SC - 1) x 16 + (SR - 1)` (the FlexiTac RevB.1) |
| `32x32` | 32 | 32 | `(SC - 1) x 32 + (SR - 1)` |
| `48x48` | 48 | 48 | `(SC - 1) x 48 + (SR - 1)` |

The Row lines take the sense connector when they fit it and the Column
lines fit the drive one (on a square reader always), otherwise the other
way round.  `auto` takes the smallest reader that holds the readout (by its
crossings: 16x16, 32x16, 32x32, 48x48); a readout no reader holds is
dropped.  `none` gives each tail one contact per line; tails of 16 and 32
pins (a 16 x 32 or 32 x 16 readout) are then read as the FlexiTac, as
before.  The proposal's `metrics.reader` and the taxel map's `reader` name
the same reader (the one the tails fit).  A named reader caps the masked
search at its lines (see **Masked fields**), so `16x16` finds what
`max_rows: 16, max_columns: 16` finds.

## HTTP

POST `/api/surface/inspect`, `/api/surface/select`, `/api/surface/fit`
and `/api/surface/map` take a framed body,
`Content-Type: application/x-tactile-surface`:

- a 4-byte big-endian length L;
- a strict JSON header of L bytes;
- the mesh file bytes.

Rules:

- The limit is 64 MiB per request.  The JSON routes keep their own 128 KiB
  limit.
- A header number of more than 4300 digits is refused before parsing.
- Each request carries the mesh and is answered from it alone.  The server
  keeps the last four parsed meshes (at most 1.5 million facets in all, two
  of a mesh's per-edge bend measurements counting as one facet) and
  the last eight charts in memory, keyed by SHA-256 and unit, and writes
  nothing to disk.
- CAD-mode requests run one at a time in a slot of their own (503 when
  busy), so the rectangular mode always keeps its two generation slots.
- Problems are answered with 422 and an `E_SURFACE_*` code.  The codes are
  listed in `/api/schema` under `x-surface-error-codes`.

| Route | Header | Reply |
| --- | --- | --- |
| `inspect` | `unit?`, `name?` | mesh facts, hidden facets, candidate surfaces per preset |
| `select` | `selection: {ops}` | facets, `facets_uv` (each facet's three corners in the chart, aligned with `facets`), area, kind (`planar`, `developable`, `curved`), outline in the chart and in 3D, boundary sides (base-edge candidates), stretch statistics |
| `fit` | `selection`, `base` (`auto`, `{side}`, `{point_xyz}`, `{arc: {point_xyz, half_length_mm?}}`; with a border `auto` or `{border_edge}`), `border?` (`{uv}`, the taxels' border, [CAD_BORDER.md](CAD_BORDER.md#the-request)), `options` | ranked proposals: design, build id, placement, metrics, outlines in the chart; plus the bases tried and the rejection reasons; with a border its echo, `metrics.border_area_mm2` and `metrics.border_on_surface_share`, `E_SURFACE_BORDER` for an invalid one |
| `map` | `placement`, `design`, `selection?` (the placement's own by default), `options?` (the placement's) | taxel map, overlay polylines, verification records, wrap template, the placement updated to the mapped design; `E_SURFACE_PLACEMENT_MISMATCH` when the mesh, the selection or the design's template, matrix (its mask included), role mapping, routing or connector differ from the fit's; `E_SURFACE_REQUEST` for a damaged placement (a missing or non-numeric field, a coordinate beyond 1e7 mm, an inward vector that is not of unit length, exit segments beyond the outline of the selection's chart, or objects and arrays nested more than 32 levels deep) |

## Command line

```text
python3 cli.py surface inspect PART.stl
python3 cli.py surface select PART.stl --pick X,Y,Z [--preset surface|flat|smooth]
python3 cli.py surface fit PART.stl --pick X,Y,Z [--base auto|N|X,Y,Z] [--options FIT.json] [--out DIR]
python3 cli.py surface map PART.stl --placement PLACEMENT.json [--options FIT.json]
```

`--pick` grows the selection from the facet nearest a point (mm, in the
STL's frame); `--ops FILE` replays a selection saved by the browser; `map`
uses the placement's own selection without either, and the placement's
fit options unless `--options` gives others (as `options` does over HTTP).
A `--base` side index of more than 4300 digits is an argument error
(exit 2), as over HTTP.  `map` exits 1 when a
verification record fails.  With `--out`, `fit` writes the chosen
proposal's files:

- `<build id>.design.json`;
- `<build id>.placement.json`;
- `<build id>.taxels.json`;
- `<build id>.wrap.svg`;
- the two Gerber ZIPs and the project review ZIP.

## Outputs

- **Placement** (`tactile-surface-placement/v1`): the design and its build
  id, the mesh hash and unit, the selection operations, the fit options,
  the base side and angle, and the field origin in the base frame and in
  the chart.  The browser keeps it and sends it back to `map`.
- **Taxel map** (`tactile-taxel-map/v1`).  Per taxel:
  - row and column, nets and contact pins;
  - chart position, `xyz_mm` and the outward normal in the STL frame;
  - the facet;
  - with a reader (see **Readers**), its sense line `SR<n>` (pin n of the
    sense tail), drive line `SC<n>` (pin n of the drive tail) and frame
    index `(SC - 1) x sense lines + (SR - 1)`; the pins follow the channel
    order.

  The map's `reader` names the reader (`name`, `sense_lines`,
  `drive_lines`, the connectors, `sense_board`, `frame_values`,
  `frame_index`) or is null.  A masked field lists only its active
  crossings (the Row and Column electrodes whose copper overlaps in the
  stack) and adds `readout`: `{rows, columns, positions, active,
  row_spans, inactive: "always 0"}`, the matrix the reader scans.
  The board glued to the part is the bottom board of the role mapping; the
  sensor's outer surface lies about 0.47 mm further out along the normal.
- **Verification** records, in the style of the DRC records (a missing
  measurement is `null`):
  - `taxels_on_surface`: every taxel maps onto the selection;
  - `taxel_surface_distance`: each taxel's distance to the selected facet
    it maps onto, recomputed in 3D from the facet's corners (an upper bound
    of its distance to the surface);
  - `neighbour_spacing_error`: neighbour spacing along the surface against
    the pitch, within 0.5% or, when larger, the strain limit plus 0.2%;
  - `board_clearance`: the fit's containment check on the real outlines;
  - `strain_under_boards`: the stretch of every facet a board overlaps;
  - `field_bend_radius`, `board_bend_radius`: the bend model above, under
    the field (4.7 mm) and under the boards (1.1 mm);
  - `tail_top_length_mm`, `tail_bottom_length_mm`: within the template's
    limits;
  - `row_tail_reach`, `column_tail_reach`: at least 6.5 mm of each tail
    beyond the exit;
  - `taxel_mask_matches_design` (masked fields only): the crossings of the
    stacked electrodes are exactly the design's mask (0 mismatches);
  - `taxels_inside_border` (a fit with a border only,
    [CAD_BORDER.md](CAD_BORDER.md)): every taxel square (the crossing of
    its Row and Column electrodes) lies inside the border (0 outside).

  A masked field's `taxels_on_surface` counts its active positions, and
  its `field_bend_radius` is measured under P.  With `containment: field`
  the records are about F: `board_clearance` becomes `field_clearance`
  (F less its four corner zones, the taxels and the margin along F's
  sides, on the surface, clear of its edge, the exit included, of holes and
  obstacles by the edge margin: required at least `edge_margin_mm`), then
  `field_corner_overhang` (how far F's corner zones leave the surface less
  the edge margin, across x and across y, sampled every eighth of a zone:
  required at most 0.5 mm, 0 for a field wholly on it), `strain_under_boards`
  becomes `strain_under_field` and `field_bend_radius` is measured under
  F less its corner zones,
  `board_bend_radius` moves to the report, and `row_tail_reach` and
  `column_tail_reach` ask for each tail's end 6.5 mm beyond the surface
  below it (beside the surface, beyond the base side's line continued).
- **Routing on the surface** (`routing_on_surface`, with
  `containment: field`; reported, not checked): per board `on_surface` and
  `overhang_mm` as in the fit's metrics, `strain_max` and
  `bend_radius_min_mm` under the boards, and `warnings`:
  `W_BAND_EDGE_RADIUS` per board that crosses an edge of the surface, a
  side or the base edge, that bends tighter than a single FPC may
  (10 x 0.11 mm; a plate's square edge is 0): `side_mm` and `base_mm` the
  tightest of each kind it crosses (null for none), measured on the mesh
  edge across the boundary and up to 3 facets beyond it (a R0.8 fillet's
  first edge measures 1.59 mm, its inner ones 0.795 mm), with what to do
  in the message (keep the board flat where it leaves the surface, or
  round the part's edge); `W_ROUTING_HOLE` and `W_ROUTING_COVERED` over a
  hole or a covered wall, `W_ROUTING_BEND` over a bend tighter than
  1.1 mm, `W_ROUTING_STRAIN` over facets stretched beyond the strain
  limit.
- **Readout.**  A diagonal Row bus folds its Row pins (ROW_01, 03, ...,
  04, 02 with `both`): its map's `readout` (also for a full field) lists
  `row_contact_order`, the Row nets at the tail's contact positions 1..N,
  and `row_pin_order`, the Row nets by pin from the pads (the scan order
  numbers the pins: with `channel_order.rows: descending` pin 1 is the last
  contact, ROW_02); the taxels' Row pins come from the pads.

## Limits

- A flat sheet covers a doubly curved surface only over a small disk, of
  radius about `sqrt(8 x strain / |K|)`: about 9 mm on a 60 mm sphere at
  0.3%.  Measured on welded test domes: 8.2 mm on a 32-segment cap, 7.1 mm
  on a fine one of 2900 vertices (a finer mesh measures the stretch more
  truly).  On domes and fingertips CAD mode therefore fits small arrays.
  Slit (comb) boards that follow geodesics are the planned way to cover
  domes (see the plan).
- With `containment: board` masked fields are of the straight
  construction classes only: a staircase follows one side of the field (the
  far side, receding going up) and the lane taper the Row channel's side,
  so equilateral and isosceles triangles, disks and V shapes are
  approximated by those staircases; with `containment: field` any row- and
  column-convex field (the diagonal Row bus).  Masked fields are at most
  `max_rows` x `max_columns` (64 x 64), as the rectangles.
- Inactive positions read 0 only while the stack's misregistration stays
  below the registration's `inactive_crossing_separation_mm` (0.8 mm at the
  2 mm default pitch and the default fill 0.5; 0.4 mm at fill 0.7).
- With `containment: board` everything above the tail roots must lie on
  the selected surface, so on narrow faces the Row channel and the Column
  fan-out take a large share of the width, and the tails must cross the
  exit (a straight side or an arc of the outer boundary) within its
  length.  With `containment: field` the bands, the fan-out and the tails
  wrap over the surface's edges (warned where an edge is sharper than a
  single FPC bends), and both boards reach beyond the exit edge (their
  shared body 2.9-7.5 mm on the named fixtures) before their tails.  The
  tails end `tail_extension_mm` past it, farther only where the shortest
  tail (7.5 mm) sets their line: where the roots lie past the edge, or so
  little above it that 7.5 mm of tail reaches farther than the extension
  (P5-diagonal-bus.md section 27.4).
- The field-only search is exact over its lattices (every exit, the
  quarter phases, the turns) within its work budget; beyond it (large
  non-convex faces at fine pitches) it keeps the best fields found, a few
  percent under the exhaustive optimum.  At sparse pitches (the gap
  between rows wider than twice the 0.5 mm margin) it holds the filler
  between two rows over their common extent, as the engine builds it
  (exactly since P5-diagonal-bus.md section 26b; over the lower row's
  whole run before, so a field near a receding edge could hold a taxel
  less than one grown cell by cell).  `max_taxels` breaks a tie by the larger pitch
  only among its four 0.01 mm steps, the quarter phases at its best pitch.
- Curved patches are flattened up to 3000 vertices (pure Python: about
  1.5 s to select and 3 s more for a strain-limited fit at 2900 vertices
  on Python 3.9).  Select a smaller area on large dense meshes.
- The meshes are taken as they are.  A coarse tessellation of a curved
  part flattens exactly (its facets are flat) and hides the real curvature;
  the chart then reports the spread of its normals as a warning.
- A face buried inside another shell (interpenetrating bodies, not merely
  touching ones) is not detected.

## The browser

One step to a sensor (the user's requests of 2026-11-02; main.js
`quickMode`, `autoSelect`, `oneStep`, `renderQuick`): the default part's
sensor is generated as the page opens (below).  After that the user's
changes only choose, and **Generate sensor** under the view makes the
sensor: a model loaded, the user's own file or a sample, has no face
selected (the user's request of 2026-11-06; until then the user's own
file had its largest flat face, the server's first flat candidate,
selected in quick mode), and with "Advanced Customization" folded a click
on the part selects the face under it alone (the face already selected:
nothing to do); Generate sensor fits the inputs as they are when the fit is
missing or stale (Undo, a base edge or border from the view's tools, the
options changed in Advanced Customization all make it stale) and generates the chosen
proposal (#1 of a new fit), mapped onto the part, after the proposal's
preview (one surface request at a time).  It is off when the sensor on
the part is the inputs' own, and it is alone under the view (the user's
request of 2026-11-02; the Gerber ZIPs are the downloads'): its title says
what the sensor is ("32 × 12 = 384 taxels · 2.0 mm pitch · all 12 checks
pass on the part"), or what to do next ("Face selected (1823.0 mm²):
Generate sensor to put the sensor on it", "Settings changed: …",
"Proposal #1 (…) fitted: …"), under way or wrong.  Opened,
Advanced Customization holds the base edge, the resolution and Fit, the
proposals and the flattened map, Generate and the checks on the part, and
a click toggles a surface as before.  (The first version of the day
generated on every click; the user asked for the button.)  The flattened
map's window keeps its place and size whatever it shows: empty, it says
"Fitting the sensor…" while a fit runs, or what comes first (main.js
`renderFlatEmpty`), so the settings beside it never widen and narrow
again.

The page (titled "FlexiTac-Gen") opens in CAD mode, which it calls "Gen by
Surface" and never "CAD" (the user's requests of 2026-10-30: its workspace
is "Pick a surface on a 3D model"); the
"Rectangular" switch beside the title (on one line with it and, at the
header's right, the look's toggle (light by default, dark once turned on:
2026-11-06), then FlexiTac's GitHub, with the repository's stars and forks,
and Discord, as on flexitac.github.io:
2026-11-02), or `#rect` in the address, shows the
rectangular form, and `#cad` still names CAD mode.  CAD mode shows the
CAD workspace in place of the rectangular form (Generate still writes the
chosen design into it, out of sight); the results below (status, previews,
design checks, downloads) appear once CAD mode has generated a build, and
go again while a model loaded after it (a file, a sample) has had no
Generate of its own (main.js `cad.newPart`; Remove model leaves them; a
build of the part before that lands meanwhile is not mapped onto the new
part's proposal).  The
basic options are in sight; the file's unit and facts (File details), the
grow settings (Selection settings), the other fit options (More options),
the proposal's card (Proposal details) and the checks on the part (Check
details) are folded.  On the page's left, in sight from its top to its end,
the order of work (the user's requests of 2026-10-30; three steps since
2026-11-02): "Design a FlexiTac sensor for your own robot", 1 Load your
gripper, 2 Generate the sensor and 3 Send to manufacture, each with one
short line, marked done or next and the one whose part is in view lit
(main.js `renderGuide`, `markGuideHere`); a step scrolls to its part on the
right (the workspace, Generate sensor under the view, the downloads).
Under step 2 a small "Advanced Customization" switch (so named at the
user's request of 2026-11-04; "Customize the sensor" before) is one with the fold on
the right (main.js `syncGuideCustomize`): either one opens both, the
guide then listing step 2's own steps, Fit and Generate, each done or next
and scrolling to its part.  Under
980 px the guide stands above the workspace.  Under its steps, "Try a
sample" (the user's request of 2026-11-06; `index.html` `#samplePalette`,
`web/samples/samples.json`) holds eight tiles in two columns: two of the UMI
finger's tapered tips, four other Library fingers and two whole grippers.
The palette moves nothing else (the review of 2026-11-06): on a desktop
window under 920 px high (a laptop's) its tiles are compact, each picture
beside its name, so it fits the guide's window-high column down to 720 px;
over 980 px the guide is a flex column whose palette, its grid then
scrolling inside it, gives way before the steps (Advanced Customization's
steps open, a shorter window); from 760 to 980 px it stands beside the
steps (they keep their own width, the guide its height, so the workspace
and the page's scroll after the first build stay where they were); under
760 px it is one row that scrolls sideways under the steps, about 70 px
high.  A tile dragged onto the 3D view's window (its id in the drag's
`application/x-flexitac-sample` data; the listeners on `.cad-view-wrap`, so
over the tools drawn on the view too, the surface menu, the camera row and
the status; the view lit as for a file until the drag leaves the window,
the dashed frame drawn over the part too) or pressed
(a click, Enter, Space, a tap; the view brought into sight when less than
half of it is) loads its part as the default part is and nothing more
(main.js `loadSample`; the user's later request of 2026-11-06, "测试用的
sensor,不要托进去之后直接就生成好了,包括新拖进去的cad,不要直接显示哪个面被选择;
只有最开始default的umi finger需要这样"): no face selected, no border, no fit,
nothing generated, the options as they are (the Library sensor's are not
applied); the 3D view frames the whole mesh as for any file, the status
says it loaded ("<file>: N facets. Click the face the sensor goes on." on
hover), the guide's step 2 is next and step 1's note names the sample (a
finger "Sample: <name>", a whole gripper "Sample: <name>, whole gripper":
no pitch, since no sensor of the Library's is built for it).  The visitor clicks the face and presses Generate sensor,
fitted by the server as for their own file (no shipped fit is a sample's).
A whole gripper is one STL, its Library finger's facets first: a selection
on that finger is framed from the sample's `camera` (main.js `sampleView`,
in place of `lookAtSelection`'s own: along the face's normal the camera
would stand in the other finger, which faces it across the open jaws), and
its 3D markers (the exit's and the border's tubes, the boards' end markers)
are sized as on that finger alone (`viewer.js` `setMarkScale`: they go with
the model's size, and a whole hand's had covered the sensor's corners).
The stacked card's sensor on the part draws that finger alone while the
fit's selection lies on its facets (main.js `figurePart`; the review of
2026-11-06: drawn whole, the other finger and the hand's body stood
between the figure's camera and the stack, Franka Hand's a wall of grey);
the rest of the gripper stays in the 3D view.  A sample loaded after a
build hides that build below as the user's own file does (the review of
2026-11-06: its status, boards, checks and Gerber ZIPs had stayed under the
new part, ready to download): the results come back with the new part's
own Generate.  The address becomes
`./?sample=<id>` (`?part` goes; a reload, or the page opened at it, shows
the sample's part alone again; an unknown id the UMI finger with a
warning); the user's own file and Remove model drop it, as they drop
`?part` with the options a Library sensor set.  The newest press wins:
another sample, a file or Remove model on the way stops it, but the part
shown keeps its sensor and its build until the sample's mesh is in hand,
so a sample that cannot be loaded (its files refused, Rectangular chosen
meanwhile) leaves the page as it was, with a warning (said again once a
build under way, the default part's or the visitor's Generate sensor,
lands).  The sample on its way is not asked again until its part is
loaded; the one shown, pressed again, is framed again (the visitor's
selection, else the whole part), not reloaded (the visitor's changes
stay).  `buildDefaultSensor`, the default part's and a Library sensor's
build, settles its own state, done or stopped however it ends, so a build
superseded never leaves Generate sensor busy.  The tile of the
sample shown is edged (`aria-current`), the one on its way busy.  In Rectangular mode the guide,
and so the palette, is hidden.  In the view's top right the
camera (Fit, Selection, the six axes); the camera frames the part, the
selection and the sensor clear of these tools (viewer.js `setClearance`:
the bands they cover at the view's top and sides; farther than before by as
much); on the view's left, a column of tools: Select a surface,
Base edge, Edit border, Undo, Clear and Remove model (the model off the
view with its selection, border, proposals and map; a build already
generated stays, the default part does not come back); under the view the
sensor's line and its Gerber ZIPs, then Advanced Customization with the base
edge's choices across its top.  The file step hints that an STL can also
be dragged onto the view.  While a model loads, a veil over the view says
"Loading name…"; CAD mode's status sits at the view's bottom right (the
user's requests of 2026-10-31; the workspace's header has none): "name
loaded" after a success (its full report on hover), a warning, an error or
the work under way in full (main.js `setStatus`, `setLoading`).  There is no candidate list since 2026-10-30 (the
server's candidates stay in the inspect reply; the default part's sensor
uses its first flat one, and the Diagnostics fold's "Select a surface by its
seed facet" picks one for the browser checks), and no Clean up.  The 3D
view is lit as the sensor on the part is (the user's request of
2026-11-05: every 3D view in the same light; `web/cad/studio.js`, which
both draw with): a product shot's lights hung on the camera (a large key
from the upper left, a bright ceiling over a cooler floor, a rim from
behind), the faint reflection of a studio built in code and Khronos PBR
Neutral tone mapping.  The part's facets keep their meaning colours (its
grey, the selected area's orange, a refused selection's red, the hidden
facets' darker grey), lit as a matte surface; the selection's outline, the
base edge, the border and its handles, the hover, the overlay and the axes
are drawn unlit in their own colours, and the view stays light in the dark
scheme.  Where a device draws no half-float render target the part is lit
by the lights alone (one console warning); on a software renderer (no
GPU) a drag's frames show the part's diffuse light alone, the look again as
the drag ends.  The steps:

1. **Load.**  Drop or open an STL; until then the UMI fin-ray finger is
   loaded (`web/vendor/umi/UMI-Soft-Gripper-Finger.stl`, the HandUMI mesh,
   Apache 2.0; a file chosen before it arrives is kept), the file step
   names it, and its sensor is already generated as if clicked (main.js
   `buildDefaultSensor`: its first flat candidate, the contact face of
   3088.6 mm2; a border of 65 mm of that face from the tip (side 2; side 0
   is the mount end), its full width of 25.8 mm, the exit Auto (it takes
   border edge 0, across the face toward the mount); Fit with the options as
   they are; Generate of the first proposal, 32 x 12 at Max rows / columns
   32), unless another file, a selection, a fit, an option or the
   Rectangular mode comes first.  Its fit is shipped
   (`web/vendor/umi/default-fit.json`: the request the page sends and the
   server's reply, taken when the page's request is that one, key by key),
   so the sensor shows at once (about 0.4 s on this host against 3.5 s with
   the whole face fitted by the server); `tools/browser/write_default_fit.py`
   writes it and `tests/test_surface_web.py` checks it against
   `surface.api.fit`.  The browser parses it for the 3D view
   (vendored three.js), and the server inspects it.  The mesh facts include
   what was repaired (repeated facets, bridged cracks, facets turned
   outward) and any warning.
2. **Surface.**  Click the part: a click on a surface selects it, a click
   on a selected one deselects it (it removes the operation that added it;
   there is no Add / Subtract switch since 2026-10-30), and Undo steps back
   through these changes.  A surface apart
   from the selection (or one the sheet cannot take) is refused and the
   selection kept.  A preset or custom angles (Selection settings; a
   click grows with Surface, 30° and no blend under 4 mm radius, by default
   since 2026-11-02, so it takes a curved face too; the default part's
   face keeps the flat preset it was found with).  The
   browser has no Disk tool since 2026-10-30 (the API's `disk` operation
   stays).
3. **Base edge.**  Click a side or a rounded edge of the selection's
   outline, or leave `auto`; the candidate exits are listed under the view,
   longest first.  **Edit border** draws a border of the taxels on the surface,
   whose edges are then the exits (see [CAD_BORDER.md](CAD_BORDER.md)).
4. **Configure** (the page's "Find best resolution").  The resolution (pitch) and the fit options of the
   table above; the browser's Max rows and Max columns start at 32 (the
   user's default of 2026-10-30; the server's default and their maximum
   stay 64).  Containment is Field only (the default) or Whole board;
   there is no Field shape and no Board rules control (the field follows
   the selected area on the surface template, P5-diagonal-bus.md section
   26.16).  With Field only the hint also says that the field's
   corners may leave the surface by up to 0.5 mm, never the taxels.  Row traces (Both, Left, Right; seen from outside, so
   the Row FPC's copper-side preview shows them mirrored) apply to Field
   only: under Whole board the select shows Straight channel, disabled.
   Changing any option after a fit makes the proposals stale: Generate
   waits for a new fit (its label says so) until the settings are the
   fitted ones again.
5. **Fit.**  (On the page the settings, two a row, Fit and the proposals
   stand on the left and the chosen proposal's flattened map on the right,
   in a window of a fixed size whatever the proposal, in sight while the
   left scrolls; under 1100 px the map comes below.  The fit's account
   below is under Proposal details, and the map's caption is for screen
   readers; the note under the proposals only says what needs doing: the
   settings changed since the fit, or why it found nothing.)  The
   proposals, best first, drawn on the part: the readout
   rows x columns, the taxels ("N of R x C" for a masked field), the
   sampled share, the coverage, the Row bus's tip, the reader.  The chosen
   proposal's card gives its containment, its Row traces, the one outline
   of both FPCs down to the tails' roots, the tip (the Row
   board's width at ROW_01 and its excess over the field), the bands beside
   the field, the Row pins by pin (folded with Both), where both tails end
   past the base edge (and why farther than asked), each board's share of
   its area on the surface and its overhang (left and right of the
   surface, past the base edge above its tail).  The fit note names the
   base edges tried and, with fewer proposals than asked for, why.  The
   flat view draws the field outline P and names its positions; each board
   is drawn solid where it lies on the surface and dotted where it leaves
   it (the bands, fan-out and tails of a field-only proposal; the tails
   past the base edge).  On the part the overlay shows the boards' parts on
   the surface, with a large dark marker where a board's outline leaves
   it, and a note under the view gives the share of each board off the
   surface.
6. **Generate** (the page's "Click to generate"; Generate on the left and
   the build on the part with its four files on the right, stacked under
   1100 px).  The chosen proposal goes into the form and is generated
   and checked as in the rectangular mode; the exports are the usual ones.
   A masked proposal's mask goes with the form (the summary reads "N of
   R x C taxels active", the form's note names the masked field, the
   assembly view draws P).  A rows or columns edit clears it with a note
   ("Masked field from CAD mode cleared"); a switch to the Rectangular mode
   keeps it for CAD mode.  When the server reports an issue at
   `matrix.mask` (a pitch or trace edit the mask no longer fits), the note
   lists it and "Use the full field" drops the mask.  A field-only
   proposal's `routing.row_sides` goes with the form too, in its Row
   traces select (Fan-out traces, shown in both modes: Straight channel,
   sent as `channel`, Diagonal both sides, left or right), so the build id
   is the proposal's (a whole-board proposal's Straight channel is
   normalized away on the surface template); an edit of it builds another
   design (fit again).  The Rectangular mode shows and sends it too (the
   generic template's default is Diagonal both sides; the value stays
   through a mode switch, like every form value).  The
   stacked view names the Row bus, the one outline both boards share over
   the field (they align by their edges), the stacked tails (the top FPC's
   tail over the bottom FPC's, how much of their width overlaps; they part
   to their own connectors) and the Row pin order.
7. **Map.**  The taxel map, the overlay and the wrap template of the
   generated build, with its verification records (with Field only, the
   records about F, then the routing report: each board's share on the
   surface and its warnings as advice, and the Row pins by pin).  Choosing
   a proposal whose build is already shown maps that build only (one CAD
   request at a time).  The placement can be
   downloaded and mapped again with `cli.py surface map --placement` or a
   `/api/surface/map` request (the browser has no placement upload).  The
   taxel map JSON of a masked field (and of a diagonal Row bus) carries its
   `readout`; the CSV of a masked field lists every readout position with
   its pins, reader lines and `active` (0: no crossing, always reads 0; the
   geometry only for the taxels), that of a full field its taxels as
   before.  Once the build is mapped, the stacked card shows the **sensor
   on the part** beside the registration (2026-11-05, the user's request).
   The part is drawn with the bottom FPC, the film (velostat, black, over
   the taxel field or the masked outline) and the top FPC draped on its
   surface where the map puts them, exploded along the face's normal.  The
   spacing is visual only (**Assembled** lays them on the part).  Where a
   board leaves the surface (a tail past the base edge, a band past a side)
   it runs flat on the plane of the nearest facet.  The figure is drawn in
   the browser from the map, the fit's chart and the board SVGs, with no
   request of its own (see [INTEGRATION.md](INTEGRATION.md#the-sensor-on-the-part-cad-mode)).
   Since the review of 2026-11-05 the view frames the part whole up to
   three times the sensor's size, and **Assembled** opens nearly face-on;
   since its second review the figure has the same room above as below
   and no light seam round the outlines over the part.  Since its look of
   2026-11-05 it has lights and a studio of its own (the film a satin
   black, not a hole; the boards a faint amber sweep; each layer an edge),
   and **Assembled** a soft contact shade where the stack meets the part;
   since the user's request of the same day the film has a lamp of its
   own, aimed for each drawing, so at the home described below it still
   catches a soft highlight at its top.
   Since the user's decision of 2026-11-05 it opens exploded as the
   registration beside it opens: 57 degrees off the face, turned 20
   degrees about its normal, the tails toward the lower right (one pair
   of angles for both figures: `app.js`'s `ORBIT_HOME`, `drape.js`'s
   `HOME_TILT_DEG` and `HOME_SPIN_DEG`).  A drag turns the stack about its
   normal and tilts it, and the arrow keys turn it, as on the left;
   **Assembled** opens at the same turn, 35 degrees off the face (29
   before, from the tails' side).  The 3D view of step 1 keeps framing the
   mapped sensor, for a Library sensor too (the user's decision of the
   same day): the part's far end may leave it there, where the figure
   beside the registration shows the part whole.  The figure is also the
   Library's (its pictures and its sensor pages' 3D view, the user's
   requests of 2026-11-05): `onpart.js`'s `createOnPartView` takes an
   optional `stage`, a function given the figure's own objects that may
   add a scene (the gripper drawn whole) and set each mode's home
   (`view.homes`); `main.js` passes none, so Gen by Surface's figure and
   its homes are the ones described here, the fingertip only
   ([LIBRARY_VIEW.md](LIBRARY_VIEW.md); `tests/test_surface_web.py` pins
   that `main.js` passes no stage).

The browser checks are `tools/browser/cad_checks.py` (see
[tools/browser/README.md](../tools/browser/README.md)).

