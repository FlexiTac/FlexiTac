# CAD mode: the border of the taxels and the exit edge

In CAD mode the taxels can be kept inside a **border** that you draw on the
selected surface.  The plan and the user's decisions are in
`claude/specs/cad-mode/BORDER-EDITOR-PLAN.md` (sections 2 and 6).  This page
covers what the app does, what the client sends, and how it is checked.

| Part | File |
| --- | --- |
| The border model: the polygon in uv, the edits, the automatic shapes, snapping, uv to 3D | `web/cad/border.js` |
| The 3D view: occlusion-aware picking, the hover highlight, the border, its handles and their drags | `web/cad/viewer.js` |
| The wiring: the panel, the toolbar, the fit request, staleness | `web/cad/main.js`, `web/index.html`, `web/styles.css` |
| The server: validation, the fit inside the border, its edges as exits, the map record | `surface/border.py`, `surface/fit.py`, `surface/fill.py`, `surface/fieldfit.py`, `surface/place.py` |
| The checks | `tests/test_border.py`, `tools/browser/border_checks.py` |

## What you see

**After a selection.**

- The border is drawn on the part in blue.  It starts as the surface's
  outline: one corner per straight side of the outline (`createBorder`).
  Corners closer than 0.01 mm (`MERGE_MM`) are merged: a flattened
  outline can hold a side a few nanometres long, which would leave an edge
  that no drag could keep.  Edge *e* of the untouched border is the side
  whose ends it shares (usually side *e*), and a side chosen as the exit
  stays the exit when the border is first edited.
- The **default exit edge** is drawn in magenta.  The panel names it under
  Auto ("first tried: Side 1"; after a fit, "chosen: …").  Before a fit it
  is the longest listed edge, which the automatic search tries first (among
  the longer edges the search prefers the narrow tip).  After a fit under
  Auto it is the chosen proposal's exit.
- Step 3 lists the **candidate exit edges**, longest first, with Auto
  first.  Hovering or focusing a row highlights its edge on the part.
  Clicking a row selects that edge.  Edges too short for the tails are not
  listed, and a note says how many were left out:
  - for the outline, sides with a chord under 3 mm;
  - for an edited border, edges under 3 mm (`surface/border.py
    MIN_EDGE_MM`).

**The Base edge tool.**

- Picking is occlusion-aware (`viewer.nearestVisiblePoint`): an edge counts
  only where the camera sees it.  An edge behind the part never wins over
  the one under the cursor, even when it projects closer on screen.
- Near a corner (edges within 2 px of each other on screen) the longer edge
  wins.
- Before you click, the edge under the cursor is highlighted, and a label
  gives its name and length.
- On the untouched outline, a click on a rounded edge (sides under 20 mm)
  still picks an arc exit around the clicked point.  With an edited border
  the exit is always one of its edges.

**Edit border** (in the column of tools on the 3D view's left) switches the editor on and off.
While it is on:

- Handles sit on the part: a sphere at each corner and a diamond at the
  middle of each edge.  A handle that the part hides is not drawn and
  cannot be grabbed.  Where handles would overlap on screen (a faceted
  arc's many short edges), only the first is drawn: the corners turning at
  least 20° (sharpest first), then the edges (longest first), then the
  arc's corners; zoom in to reach the others.  A drag never rotates the
  view; dragging anywhere else does.
- **Dragging a corner** moves only that corner.  Any quadrilateral (any
  simple polygon) is allowed.
- **Dragging an edge**, by its diamond or anywhere on its line (within
  8 px, where it is in sight), moves it parallel to itself.  Its two
  neighbours are extended or shortened along their own lines.  At a soft
  corner, one turning less than 20° (`SOFT_CORNER_DEG`: a slight bend, the
  step into a faceted arc), the edge's end moves with it, square to the
  edge, and the neighbour turns about its other end; extending a
  neighbour that runs nearly along the edge would meet the moved edge far
  past the curve.  The same holds where a neighbour is shorter than the
  move, which would otherwise turn it round.  A press on an edge that does
  not move is a click: with the Base edge tool it picks that edge.
- A drag follows the cursor's ray onto the selected facets.  Beyond the
  surface it continues on the plane of the nearest selected facet, and the
  uv there is extrapolated (`border.xyzToUv`).  A move the model refuses
  returns null: an edge turned round, a crossing, a collapsed edge.  The
  border then stays as it was.
- **Snap** (on by default): a dragged corner snaps to an outline corner,
  else to an outline edge, and an angle within 3° of 90° becomes a right
  angle.  A dragged edge stays parallel and snaps through an outline corner
  that lies within reach of its line, alongside it.  The reach is 1.5 % of
  the selection's size, between 0.25 and 3 mm.
- **Double-click an edge** (its diamond or its line) to add a corner there.
  **Click a corner** to select it (it turns red); then **Delete corner** or
  the Delete key removes it.  A border keeps at least 3 corners.
- **Surface outline** resets the border to the surface's outline.
- (**Largest rectangle**, which set the border to the largest rectangle on
  the surface, is gone with the user's decision of 2026-10-26,
  P5-diagonal-bus.md section 26.16: what CAD mode generates depends only on
  the selected area, so it looks for no rectangle in it.)
- **Inset by** *x* mm moves every edge inward by *x* mm; a negative *x*
  moves them outward.
- **Undo** and **Redo** (Ctrl+Z, Ctrl+Shift+Z or Ctrl+Y) step through the
  border's history.  Escape first drops the corner selection, then leaves
  the editor.
- Clicks on the part select nothing while the editor is on.  The Base edge
  tool still picks edges.

**Beyond the surface.**

- A border may reach beyond the surface.  The taxels lie only where the
  surface and the border overlap.
- On the part, the border is solid where it lies on the facets and has
  gaps where it leaves them.  The parts beyond the surface are dashed in
  grey (`border.outsideParts`).
- An exit edge beyond the surface is dashed in magenta.
- The note under the 3D view (with the base edges) gives the border's
  corners, its area and its share on the surface; the status at the view's
  bottom right repeats it on hover.

**Fit, proposals, map.**

- With an edited border, step 4 shows Containment *Field only* and Board
  rules *Surface*, both disabled, and the hint says why: the border
  constrains only the taxels, and the server takes it with these settings
  only.  Your earlier choices come back when the border is the outline
  again.
- The proposals card has a *Border* row: the corners, the area, the share
  on the surface, and the exit edge.  The fit note starts with "Inside your
  border".
- The flat preview under Proposals draws the border in blue, hatched beyond the
  surface.  It is left out on a strain-limited curved fit, whose chart is
  another one.
- On the part, the exit of a border fit is the border's edge
  (`placement.base_kind === "border"`), drawn from the border that was
  fitted.
- Generate keeps the border: the proposal's placement carries it, and the
  map of the build checks it.  The verification table lists **taxels
  inside border**: every taxel square lies inside the border.
- After a fit, any edit of the border makes the proposals stale.  The fit
  note says "The border changed", Generate waits for a new fit, and the
  magenta exit and Auto's name follow the edited border.  A new selection
  or file resets the border and its history.

## The request

**The border is sent once it is edited** (`main.js borderPayload`).
While it equals the untouched outline (vertex for vertex, as
`createBorder` made it) the fit is sent exactly as before, without
`border`:

- it gives the same fit (the whole surface);
- it keeps the outline's exits, including the arcs on rounded outlines,
  which a fit with a border never tries;
- it keeps the containment you chose.

Reset (Surface outline) and an Undo back to the outline therefore send no
border.  A border with the outline's shape but another first corner counts
as edited.

| The border | `border` | `base` | `options` |
| --- | --- | --- | --- |
| The untouched outline | absent | `"auto"`, `{"side": k}` or `{"point_xyz": [x, y, z]}` (an arc) | as set in step 4 |
| Edited | `{"uv": [[u, v], ...]}`: counter-clockwise, in the `/select` chart's uv, full precision | `"auto"` or `{"border_edge": i}` (edge *i* runs from vertex *i* to *i* + 1) | `containment: "field"` forced |

Before sending an edited border the client checks it with
`border.validate`: simple, at least 3 corners and 1 mm², overlapping the
surface.  It also checks that at least one edge is 3 mm or longer and that
the border has at most 2048 corners (`surface/border.py MAX_VERTICES`).
Otherwise it reports `E_CLIENT_BORDER` and sends nothing.

The server refuses with `E_SURFACE_BORDER`:

- an invalid border;
- `{"side"}` or `{"point_xyz"}` with a border;
- `{"border_edge"}` without a border, or naming an edge under 3 mm or one
  with no surface beyond it;
- `containment: "board"` with a border.  (The generic template and
  `shape: rectangle` are refused for every fit since section 26.16, with
  `E_SURFACE_REQUEST`.)

Under Auto with a border, the fit tries the border's edges that are at
least 3 mm long, longest first, at most 6, and skips those with no surface
beyond them.

**Symmetry with a border** (P5-diagonal-bus.md section 22, the fit's
symmetric faces in [CAD_MODE.md](CAD_MODE.md#field-only-containment-containment-field)):
an exit's axis runs through the middle of its border edge, and the region
tested for symmetry is the border's part on the surface.  The border's
edges on the surface must mirror onto the border's edges, and the
surface's outline and holes inside the border onto the surface's, each
within 0.05 mm: each kind of edge keeps its own rule (the taxels only
inside the border; F's margin on the surface).  A symmetric border
wholly on the surface is symmetric whatever the surface; one reaching
beyond the surface's sides is symmetric when the surface is too about
the same axis.  On a symmetric exit the field is centred on the axis,
every row its own mirror image, unless a field that breaks the symmetry
holds at least 20 % more (P5-diagonal-bus.md section 26.19; section 22
let such a field go first with 3 % more, section 26.17 never): an
isosceles trapezoid inside a 60 x 40 plate takes the symmetric tip-first
234 and the 238 on a parallel edge, then a leg's 239 and 243.

The reply:

- echoes the border in `request.border` and in each proposal's
  `placement.border`;
- sets `placement.base_kind` to `"border"` and `placement.base_side` to the
  border edge (`reply.bases[].side` holds border edge indices too);
- adds `metrics.border_area_mm2` and `metrics.border_on_surface_share`.

The map (preview and build) adds the required record
`taxels_inside_border`.  The `/select` reply's `selection.facets_uv` (the
uv of each selected facet's corners, aligned with `selection.facets`) lets
the browser map uv to the part and back.

**Units and charts.**

- `border.js` maps with the mesh's `scale_to_mm`: an STL in metres is
  scaled like the server's mesh.
- The border always lives in the `/select` chart.  A strain-limited fit
  works on a disk's chart of its own; the server carries the border there
  by a least-squares rigid fit.  So the mapped taxels may sit slightly off
  the drawn border.  The map's check uses the carried border.

**Off.**  The border is not drawn and Edit border is disabled in three
cases:

- with a facet mismatch (the browser's facets are not the server's);
- while the last selection operation is refused;
- without `facets_uv` (an older server).

The fit then uses the whole surface.

## Checks

`tools/browser/border_checks.py` checks two things.

**The model.**  Every function of `border.js` against exact values, on the
soft finger and the crank as well (`--only model`).

**The editor in the app** (`--only ui`), driven with the mouse in Chromium
with SwiftShader WebGL.  Screenshots go to `FPC_BORDER_SHOTS`.

The soft finger's contact face:

- the outline drawn as the border;
- the default exit named under Auto, and the ranked list;
- row hover and Base edge hover with the label;
- a click on a visible side;
- the 8 handles;
- a corner drag (any quadrilateral) and an edge drag (the neighbours stay
  on their lines);
- an edge dragged beyond the surface: dashed, the magenta exit dashed;
- Undo and Redo;
- the forced containment, with the Row traces free, and the earlier
  containment choice back after Surface outline;
- the fit request (border, base, options);
- every previewed taxel inside the border and on the surface, the map
  record passing, and the flat preview's border;
- a border edge chosen as `{border_edge}` and taken as the exit;
- Generate, with all 12 records passing;
- the proposals stale after an edit;
- Surface outline and Inset (no Largest rectangle);
- a double-click inserting a corner, Delete, Ctrl+Z and Delete corner;
- Done editing.

A plate written by the script:

- a click where the hidden back side projects selects nothing;
- near a corner, the visible side wins over a hidden one projecting closer;
- a border outset beyond the plate is fitted with every taxel on the plate
  and inside the border.

The server side is covered by `tests/test_border.py`.
