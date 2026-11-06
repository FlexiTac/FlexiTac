# Integration: the two FPCs, the stack and the reader connectors

What the generated boards mean physically: where pin 1 and the first row and
column are, how the two boards are stacked, how the assembly preview shows
the stack, and how the tails meet the reader board's connectors (product
decision D23).  `tests/test_docs_consistency.py` compares the tables here
and the dimensions quoted for the generated boards and the reader connectors
with generated boards and the profile, and `tests/test_chirality.py` tests
the geometry behind the prose (handedness on every side, pin 1 in the
emitted files, the turned-over stack view); the prose itself is not
machine-checked.  The reader-board facts come from the
FlexiTac reader BOMs and connector drawings recorded in the profile's
`sources` block, not from this application.

## Each board on its own

Every board is built with its tail pointing down and then turned as a whole
(never mirrored) so that its tail exits `tail.row_side` / `tail.column_side`.
Seen from the **copper side** with the tail pointing down (rotate any view so
that it does):

- the contact row runs left to right; contact **position 1** is the leftmost;
- **pin 1** is position 1 with `channel_order` `ascending` and position P
  (the rightmost) with `descending`; pins run monotonically along the row;
- channel *k* sits at position *k* (except on the Row board of a
  [diagonal Row bus](#the-diagonal-row-bus), whose contacts follow
  `tail.row_contact_order`); positions N+1..P of a connector
  larger than the channel count are isolated `NC_<pin>` contacts;
- `ROW_01` is the Row electrode **farthest from the tail**, and the Row tail
  sits at the left end of the Row board, flush with its left side, on the
  straight Row channel (`routing.row_sides` `channel`; the table below is
  that board's); the diagonal Row bus, the rectangular mode's default,
  centres it under the field in every side mode, stacked on the Column
  tail;
- `COL_01` is the **leftmost** Column electrode, and the Column tail is
  centred under the taxel field.

The traces run thin from the electrodes, 0.127 mm wide at 0.127 mm spacing
by default (`routing`), as a bundle at their width plus spacing, and expand
again to the 0.5 mm contact pitch; below every bend, in the tail, they widen
to 0.254 mm (`routing.finger_trace_width_mm`) and run straight into the
contacts.  The wide traces cross the stiffener edge, where the tail flexes
most; the thin bundle stays in the board body and the fan-out.  JLCPCB holds
trace widths to +/-20%, so a 0.127 mm trace may come out at 0.1016 mm, its
minimum for the ordered 1 oz copper; JLC sets no rule on necking or on the
trace width near bends or stiffener edges.

The previews and every export use the copper-side view in each board's
Gerber frame (Y up).  On screen, per tail side:

| Tail side | Tail | Pin 1 (`ascending`) | `ROW_01` | `COL_01` | Row tail |
| --- | --- | --- | --- | --- | --- |
| `bottom` | bottom edge | left end of the contact row | top edge | left edge | lower-left corner |
| `right` | right edge | bottom end | left edge | bottom edge | right edge, lower end |
| `top` | top edge | right end | bottom edge | right edge | upper-right corner |
| `left` | left edge | top end | right edge | top edge | left edge, upper end |

Pin 1 is defined by the exported data, not by the drawing: `pinout.csv` in
the review bundle (pin, net, role, logical index, contact centre, physical
side) and the `J1-<pin>` test points of each board's `netlist.ipc`.  The
previews mark it with a red triangle beyond the tail tip in line with the
pin-1 contact (the browser adds a ring around it; in the stacked view each
ring takes its board's colour, the top FPC's teal and the bottom FPC's
orange, and where the two would meet as the stacked tails end together
they move apart, away from each other, each still round its own
triangle's centre, so in both views they never overlap and each marks its
own pin 1; where the two triangles lie on each other, a 2 x 2's in the
plan view, each ring holds its own at its rim nearest the other).

`channel_order` is the pin assignment recorded in the netlist and the
pinout: it does **not** move copper.  The Gerber layers and `jlcpcb.json` of
an ascending and a descending build are byte-identical apart from the build
id that every Gerber header names; what differs is the pin numbers (in the
layout, `netlist.ipc` and `pinout.csv`), the pin-1 marker of the previews,
the manifests and the build id.

## The stack

The two FPCs are separate boards stacked copper to copper: the **physical
top FPC** (`role_mapping.top`, rows by default) lies on top with its copper
facing **down**; the **physical bottom FPC** lies below with its copper
facing **up**.  Their electrodes cross; each crossing of `ROW_r` and `COL_c`
is taxel (r, c).  The sensing layer, spacer and adhesives between them are
not part of this application.  `tail.top_length_mm` belongs to the physical
top FPC and `tail.bottom_length_mm` to the physical bottom one (defaults 12
and 12 mm; 7 mm with the straight Row channel; alike since
P5-diagonal-bus.md section 27.7, so the stacked tails end together, 12 and
7.5 mm before), whichever role it carries.

The boards are registered on their taxel crossing fields
(`grid_registration.active_region`, identical in size on both boards and
checked by the registration record).  Neither board carries fiducials or
alignment holes (audit I1): the registration has no manufactured reference
yet.

On the straight Row channel (`channel`; with the diagonal Row bus the
Column board converges in one V, without a slot, in both modes), with
more than 16 columns, a wide bundle and a narrow field, the Column
board's two-lane fan-out can be wider than the sensor below the taxel field
(see [LAYOUT_SCHEMA.md](LAYOUT_SCHEMA.md#column-fan-out)).  With the default
0.254 mm bundle pitch both bundles fit every legal field (an odd column
count can still widen one body side by up to one fillet radius, 0.5 mm);
with 0.254 mm traces at 0.246 mm spacing (the widest bundle, at the contact
pitch), 17 columns at 0.6 mm pitch with 0.35 mm electrodes make a 13.86 mm
wide board under an 11.45 mm sensor: about 1.45 mm beyond the side of
COL_01-COL_09 and 0.95 mm beyond the other, because with an odd column
count the COL_01 lane carries one route more.  Leave room
for such a fan-out next to the sensor, and check it against the other
board's tail and the reader board when the tails share a side.

### The assembly preview

The browser's stacked view draws the physical bottom board face up and the
physical top board **turned over about its tail axis** (copper facing down),
so both tails exit the shared connector side; it registers both on their
taxel fields.  Its exploded 3D view turns with the mouse: drag across to turn
the stack in its plane and down or up to tilt it (from straight above to under
the stack); the arrow keys turn it by 5 degrees, and a double click, 0 or
**Reset view** (over its top right, 2026-11-06) sets it back; each board
card's oblique view turns the same way.  The plan view keeps still.  Its
switch, **3D view** and **2D view**, sits over the figure's top left (the
board cards' tabs too, and their 2D view's zoom; the user's request of
2026-11-06), and the plan view's scene shrinks where its boards would reach
under it.  Both 3D views draw each single-sided board's two sides: its
copper side where that faces the camera, else its polyimide, with the copper
seen through it and the PI stiffener outermost (no coverlay window, no ENIG);
so from above the turned-over top board shows its polyimide side.  Each board
is as thick as its result's stack-up (`fpc.stackup`: 0.11 mm of core PI,
copper, coverlay adhesive and coverlay, and the 0.225 mm PI stiffener below),
behind its copper side, which stays in place; at the views' scale 0.11 mm is
under a pixel, so the FPC is drawn at least 2 px thick and the stiffener in
proportion (the oblique views' caption says so; the stacked view has no
caption since 2026-11-06); the walls run along the edges only, so the
top board stays see-through over the field.  A coin for
scale (a US quarter, 24.26 mm and 1.75 mm thick, drawn to scale, its face the
US Mint's photo) lies on the table 56 px below the bottom board, right of the
stack and level with its bottom, so no board covers it; each board card has
one beside its board, at least 2 mm clear of the outline (the 2D view puts
it at its window's bottom right, the board centred, and shrinks the board a
little where it would be under the coin there; the oblique view lays it 28 px
below the board).  The exploded view and the oblique views are lit as the
sensor on the part is (2026-11-05): its lights, fixed to the viewer, shade
each board's side by the way it faces them (as drawn at the exploded view's
home), a faint satin sweep of the studio's softboxes slides over the
coverlay as the view turns, each wall is lit by the way it faces, and the
shadows fall away from the key, down and to the right on screen, whatever
the turn; nothing is painted outside a board's outline and the plan view
stays unlit.  Seen from
above, through the top board:

- the bottom board looks exactly like its own top view;
- the top board is its top view **mirrored across the tail axis**
  (left-right for bottom and top tails, top-bottom for left and right tails).

With **rows on top** and the tails at the bottom (the straight Row channel;
on the diagonal Row bus the Row tail lies under the field, see
[below](#the-diagonal-row-bus)):

- the Row FPC is mirrored left-right: its tail moves from the lower-left to
  the **lower-right** corner, the row order is unchanged (`ROW_01` stays the
  row farthest from the tails), and its contacts read **reversed** from above:
  pin 1 is the rightmost Row contact;
- the Column FPC is face up: `COL_01` on the left, pin 1 its leftmost contact;
- taxel (1, 1) is the upper-left crossing as seen from above.

With **columns on top**:

- the Column FPC is mirrored: **`COL_01` appears on the right** and pin 1 is
  its rightmost contact; taxel (1, 1) is the upper-right crossing;
- the Row FPC is face up with its tail at the lower-left and pin 1 its
  leftmost contact.

In short, seen from above with the tails at the bottom and `ascending`
order:

| `role_mapping.top` | Row FPC | Column FPC | Taxel (1, 1) |
| --- | --- | --- | --- |
| `rows` (default) | turned over: tail lower-right, `ROW_01` at the top, pin 1 rightmost | face up: `COL_01` on the left, pin 1 leftmost | upper-left |
| `columns` | face up: tail lower-left, `ROW_01` at the top, pin 1 leftmost | turned over: `COL_01` on the right, pin 1 rightmost | upper-right |

`channel_order` cannot move `COL_01` to the other side; only the role
mapping (which board is mirrored) does.  The browser offers one shared
connector side.  The API also accepts tail sides half a turn apart (the
boards stay orthogonal and register; one board's index direction then runs
the other way in the shared frame, and the tails exit opposite edges), and
rejects sides a quarter turn apart (`E_TAIL_SIDE_PARALLEL`, the electrodes
would be parallel).

#### The sensor on the part (CAD mode)

Added 2026-11-05 at the user's request: in CAD mode ("Gen by Surface") the
stacked card has a second figure beside the registration, the **sensor on the
part** (`web/cad/drape.js` computes it, `web/cad/onpart.js` draws it with
three.js).  The loaded part is drawn in a matte light grey.  Outward from it
along the face's mean normal come the bottom FPC (copper out, glued to the
part), the film (velostat, satin black, over the taxel field: the Row
board's `active_outline` when the field is masked) and the top FPC (turned
over: polyimide out, its copper toward the film).  Seen from outside, this is
what the finished sensor looks like.  Rectangular mode shows the registration
alone, as before.

It needs no request of its own.  Once the build is mapped (`cad.map` of the
shown build: the same `build_id`, mesh and unit) it is built from what the
page holds:

- the fit's chart (`selection.facets` and `facets_uv` of the fit reply,
  the strain-limited disk's when limited);
- the STL's corners;
- the mapped placement's field frame (`field_origin_base`, `field_origin_uv`,
  `field_x_uv`, `field_y_uv`);
- each board SVG's view box and `data-active-region`.

A point of a board SVG (root units `(sx, sy)` after its Y flip, taxel field
`R = (Rx, Ry, Rw, Rh)`) lies in the base frame as `surface.fit.board_outlines_base`
places it:

- the bottom board: `bx = ox + (sx - Rx)`;
- the top board, turned over about its tail axis: `bx = ox + (Rx + Rw - sx)`;
- both: `by = oy + (Ry + Rh - sy)`.

Then `uv = field_origin_uv + (bx - ox) field_x_uv + (by - oy) field_y_uv`, and
the 3D point follows barycentrically on the chart's facets, as the map's
overlay does.  Each board is a grid laid over its SVG's view box; its texture
coordinate is the point's share of the view box.  Each grid point goes through
the formulas above, so the copper and the outlines land where
`/api/surface/map` puts them.  The browser checks hold them within 5 µm of the
overlay, the field and the taxels.  Beyond the chart (a tail past the face, a
band over an edge) a board runs flat on the plane of the nearest boundary
facet.

The art comes from the page (`app.js` answers `fpc:board-art`): each board's
copper side and polyimide side as standalone SVGs in the page's look, with the
look's CSS rules and paints inlined.  An SVG drawn as an image sees neither
the page's CSS nor its `<defs>`.  The SVGs are rasterised through `data:`
URLs, as the page's CSP (`img-src 'self' data:`) allows.

The exploded spacing is visual only: on the part the stack is
`stack.contact_offset_mm` (0.47 mm) thick.  The layers are shifted rigidly
along the normal (on a face whose normals spread more than 60 degrees, along
their own normals), and **Assembled** lays them on the part.  The figure turns
with the mouse.  The arrow keys turn it by 5 degrees; 0, a double click or
**Reset view** (over the view's top right) bring it home.  The wheel scrolls
the page.  **Exploded** and **Assembled** sit over its top left (no title
since 2026-11-06: the frame shows the part), and its pane keeps its top
40 px for them and Reset view, the canvas below.

It opens exploded as the registration's figure beside it opens (the user's
decision of 2026-11-05): 57 degrees off the stack's normal and turned 20
degrees about it, one pair of angles for both figures (`app.js`'s
`ORBIT_HOME`, `styles.css`'s `.assembly-camera` and `drape.js`'s
`HOME_TILT_DEG` and `HOME_SPIN_DEG`, which `tests/test_surface_web.py` reads
as one).  The camera's up is the stack's normal, so the screen's up and the
roll are the left figure's, a drag across turns the stack about its normal
and a drag down tilts it toward the view from above, and the arrow keys turn
it the left figure's way.  The two cameras turn alike (their screen
directions of the board's axes and of the normal agree to 0.01 degrees);
each figure's lens, 30 degrees high in both, adds its own perspective where
the field's centre lies in its pane, which the part's framing sets on the
right: at the field's centre the board's x agrees within 1 degree, its y
(the tails' direction, the most foreshortened) and the explode within 2.5
and 0.3 degrees on the UMI finger and up to 9 and 5 degrees on the I2RT
YAM's 1 mm sensor, whose part puts the stack at the pane's right
(`cad_checks.py` prints them).

After the review of 2026-11-05:

- The camera frames the sheets and the part within three times the sheets'
  radius, so a finger or a gripper's tip is shown whole.  A larger part is
  cut where it reaches farther.
- **Assembled** has its own home, nearer the face's normal, so the finished
  sensor's field is seen nearly face-on (since the look of 2026-11-05: 22
  degrees round and 20 degrees toward the tails, 29.4 degrees off the
  normal; 25 and 10 before, 26.8 degrees off).  Since the user's decision
  of 2026-11-05 above, 35 degrees off at the left figure's turn.
- The sheets' outlines are the art's alpha, which the materials turn into
  coverage, so the renderer's multisampling antialiases them.
- The checks' measurements run only with `?probe` in the page's URL:
  reading the drawn pixels back, and comparing the drape with the map.
  The browser checks open the page with it.  A visitor's page draws the
  figure and does no more.

After its second review (2026-11-05):

- A covered sample of an outline keeps the larger of its alpha and what is
  already there (custom blending: the colour replaces, the alpha takes the
  maximum), and the sheets are drawn after the part and back to front as
  the camera sees them.  The coverage's alpha had been written as it was,
  so the pane's grey showed through round every outline over the part.
- The camera sits where the sheets and the part just fit the lens with
  FRAME_MARGIN (1.15) to spare, its line of sight midway between the
  extremes, so the figure has the same room on both sides of the axis that
  binds (about 6.5 % of the pane).
- The figure's cursor is grab (grabbing while it turns), as over the left
  figure.
- In the split the registration's caption had run to two lines over the
  pin-1 rings past the tails' end; it kept 12 px off the pane's right, and
  the plan view's scene sat 15 px higher (400 px tall at most in the
  480 px pane).  Since 2026-11-06 the registration has no caption (the
  user's request), and its plan view is centred in its pane as in the
  whole card.

The look of 2026-11-05 (the user's feedback: light and shade, not only
shadows; the flat black film had read as a hole cut in the stack) was built
in a look lab on a copy of the figure, chosen by two judges and then merged
into `onpart.js`.  Its parts are sections of their own:

- **Lights** (`studioLights`): the figure's own, no longer the 3D view's
  old ones; since the 3D view's look of 2026-11-05 they, the studio and the
  tone mapping are `studio.js`'s, which the 3D view (`viewer.js`) draws in
  too (its old `addViewLights` gone).  A hemisphere (a
  bright ceiling and a darker, cooler floor that models the part's faces),
  a key from the upper left as in the left figure, a rim from behind and a
  dim sheen lamp, all hung on the camera: a turn turns the sensor under
  fixed lights, as on a turntable, and nothing jumps on a mode switch.
- **Environment** (`studio`, `studioFor`): a studio built in code (a grey
  room, softboxes and rim strips; no image, which the CSP would refuse),
  prefiltered once by three.js's `PMREMGenerator` and turned with the
  camera.  The film and the boards take only its reflections; their
  diffuse light is the lights', as the part's.  Without half-float render
  targets, or where three.js's shader text has changed, or where making it
  fails, the sheets are lit by the lights alone, with one console warning.
  A lost WebGL context that comes back gets the studio made again, and
  what it drew is dropped without a dispose (see the fix round below).
- **Tone mapping**: Khronos PBR Neutral, which keeps the art's colours and
  only rolls off highlights.  The canvas stays transparent over the pane's
  light gradient, which stays light in dark mode.
- **Materials**: the part a matte light grey (the 3D view's times 0.9, so
  its lit faces stand off the pane); the film a satin black with a frosted
  sheen, a soft gradient from its top to its foot at the Exploded home
  (about sRGB 85 down to 55 on the default part); since the Exploded home
  became the left figure's (2026-11-05) the film mirrors the room between
  the studio's back softbox and sheen lamp there, which were set for the
  home before, so it has a lamp of its own (`FILM_LAMP`, the user's request
  of the same day): a light only the film's shader takes, aimed for each
  drawing where the film seen from the Exploded home mirrors it just past
  its top, then hung on the camera, about sRGB 88 down to 64 on the default
  part (44 down to 38 without it); the boards, the part and the 3D view
  draw as before; the boards their art
  under a satin coverlay whose weak reflection is tinted toward the art's
  hue (a faint amber sweep, never a white veil; the top FPC's median stays
  near the left figure's orange).  At the shared home the left figure
  draws its upper board at 78 % opacity (the registration shows the lower
  one through it), so there the top FPC reads lighter: on the default part
  at 1440 px its face's mean sRGB is 202, 111, 4 on the part and 209, 141,
  69 on the left, which the same art lit here and laid at 78 % over the
  left's pane matches within 2 levels in red and green (210, 139, 57).
- **Edges**: each layer an edge band along its outline and cutouts, wound
  outward and drawn from the front only, 2.5 CSS px deep at least when
  exploded; assembled each band reaches down to the layer under it, so the
  three tile one stack edge standing on the part.
- **Contact shade**: in Assembled only, the stack's footprint seen along
  the normal, baked once per drawing into a small texture (a tight line
  and a soft halo, only on the part's surface near the stack's underside)
  that darkens the part's light.  There is no shadow map and nothing per
  frame.  The tight line also reaches one texel (0.25 mm) inside the
  footprint's edge where that edge faces the camera, so it starts at the
  stack's edge band.  Assembled also skips the film's face, which both
  boards cover.

What the merge kept from the figure's reviews, and the choices it made:

- The outlines stay coverage with the custom blending, and the sheets are
  drawn after the part and back to front: with the edge bands the browser
  checks still find no seam round the outlines, exploded or assembled, and
  the film's outline about half antialiased (measured on its face alone,
  since the band's own edges are smoothed by the multisampling in any case).
- Each sheet keeps one position buffer, drawn dynamic, into which a mode
  switch copies the other mode's positions (the look lab had found that a
  new attribute made the reflective sheets vanish on SwiftShader).
- The framing is unchanged: the bands lie on the outlines and the shade on
  the part, so the margins are the same (about 6 % of the pane).
- Drawing one turn costs 1.7 to 2.3 times what it did on SwiftShader (the
  studio's reflections and the physically based materials; at a device
  pixel ratio of 2 the default part 22 to 47 ms, the crank's tip 44 to
  78 ms).  The studio costs about 30 ms once, and the contact shade 35 to
  60 ms of JavaScript on the first Assembled of a drawing.  A frame with
  nothing turned costs what it did.

The look's fix round (2026-11-05, the minor findings of its review):

- A lost WebGL context that comes back: three.js has rebuilt its state
  for the new context by the time the figure hears of it, so disposing
  the old studio, sheets or part then deleted the lost context's objects
  in the new one.  Chrome logged 40 `WebGL: INVALID_OPERATION` warnings
  after one loss.  The figure now drops them without a dispose, and the
  page draws it again; `part_on_part_studio` counts the warnings (none,
  also after a drawing on the restored context).
- The User Timing measures (`on-part studio`, `on-part contact`) sit
  outside the studio's build and never throw: in a browser whose
  `performance.measure` refuses an options object, a measure inside the
  build's `try` had thrown away a studio that was made, with a wrong
  warning, and the contact shade's had broken the Assembled click.
- A stack without a contact footprint keeps that result until its next
  drawing, so it is not computed again at every Assembled.
- The unit suite checks every shader edit against the vendored three.js:
  each anchor occurs once in the text it edits, and every name the
  inserted GLSL uses (`outgoingLight`, `reflectedLight`'s specular terms,
  `diffuseColor`, `alphaTest`, `transformed`, `modelMatrix`,
  `cameraPosition`) is declared before it runs.  A three.js upgrade that
  renames one fails there first, not as a compile error in a visitor's
  browser.  `part_on_part_patches` serves the figure with one anchor
  broken: it is still drawn, with one warning and no seam.
- On a curved part the stack's footprint can end a texel or so beyond its
  edge band.  On the Trossen WXAI sock this left a light line about
  2 device px wide between the band and the contact shade: across its
  right edge `53 48 70 | 195 195 185 174 163 151 147`.  The core now
  starts one texel inside the footprint's rings, on the edges facing the
  camera only (the shader follows the halo's gradient outward), and not
  round a strip of cells turned from the normal.  The same edge now reads
  `53 48 70 | 156 150 149 148 147 146 147`.  Beside the soft finger's
  knuckle in its wrap the part is seen inside the footprint past an edge
  facing away, and there the light strip keeps its look: 38 of its 2,550
  device px darker by more than 24 levels, where a core inside every edge
  had framed it with 836.  The boards and the Exploded view are unchanged
  pixel for pixel, and on the part only pixels beside the stack's edge
  change (on the wrap also 32 beside the knuckle's strip, 35 levels at
  most).  `part_on_part_contact` checks the sock: two fifths or more of
  the part's pixels along the stack's edge darkened (0.32 before, 0.49).

## The diagonal Row bus

A design whose `routing.row_sides` is `left`, `right` or `both` (seen from
outside the stack with the tails down;
[API.md](API.md#diagonal-row-bus-routingrow_sides)), on either template and
the rectangular mode's default (`both`; `channel` keeps the straight Row
channel), routes every row as a slant from its electrode's end instead of up
the straight Row channel
([LAYOUT_SCHEMA.md](LAYOUT_SCHEMA.md#diagonal-row-bus)).  For the assembly
and the reader this changes:

- **The Row pin order.**  "Channel *k* at position *k*" no longer holds on
  the Row board: its contacts take the order of the lanes,
  `tail.row_contact_order`.  With `both` that is ROW_01, 03, 05, ..., 06,
  04, 02 from position 1 (the near band from outside in, then the far band
  from inside out); with one side ROW_01..ROW_R, or ROW_R..ROW_01 on the
  side opposite ROW_01's with both.  `channel_order` still numbers
  the pins along the contact row, and the Column board is unchanged.  The
  firmware must take each row's pin from `pinout.csv` (or `taxels.csv`,
  which gives both pins of every position), never assume pin *k* = ROW_k.
  The Row board's `ORDER_NOTES.txt` states the folded pins too, and CAD
  mode's taxel map lists them in its `readout`: `row_pin_order`, the Row
  nets by pin from the pads (with `channel_order.rows: descending` pin 1
  is the last contact, ROW_02), beside `row_contact_order`, the nets by
  contact position.
- **One outline down to the tail roots: align the films by it.**  From
  the tip down to the tails' roots
  (`construction.row_bus.shared_outline_below_field_mm` below the taxel
  field: 5.87 mm on the default 12 x 32) both boards have one outline seen
  from outside the stack (the top board turned over): the union of the
  two, the field with the Row bands and funnel and the Column fan-out
  (each board carries blank film where only the other has copper).  Both
  tails leave its bottom edge.  Laid copper to copper with the film
  between them, the two FPCs register when their edges coincide: align
  them by that common outline (a fixture that holds both edges, or one
  edge sighted on the other), not by the tails.  The registration checks
  the common outline on every build (`outlines_coincide_over_field`; the
  boards carry no other alignment features).  Below that level only the
  tails differ, each its own width, position and length (CAD mode's
  `tail_extension_mm` is measured from that edge).
- **The tails stacked.**  Both tails leave on one side (opposite tails
  are `E_ROW_BUS_TAILS`, and the registration fails a pair whose tails
  leave on two sides, `tail_sides_match`) and lie one on the other where
  they meet (`construction.row_bus.tails` `stacked`): the Column board has
  the straight one's copper (one V straight into its contacts: one lane,
  no slot, the same in both modes), its tail centred under the taxel field
  as without the bus and rooted on the shared bottom edge, and the Row tail
  is centred on the field too, in every side mode (`diagonal-bus/10`,
  P5-diagonal-bus.md section 27: within the sensor's width wherever it is
  narrower than the field, centred on it where wider), where the two bands
  converge in a funnel with `both` and one side's bundle fans in, so the
  narrower tail lies wholly on the wider (`tail_overlap_width_mm` of the
  registration says how much of their width overlaps: the narrower one's).
  Until `diagonal-bus/9` one side's Row tail lay under the band, beyond the
  field, and the funnel's split drifted off the field's centre on
  asymmetric fields.  The top board's tail lies over the bottom board's
  (the Row tail over the Column tail with the rows on top), each with its
  own coverlay and stiffener; nothing keeps them apart, and their contact
  columns (both at the 0.5 mm pitch) may lie on each other.  At the
  connectors the integrator must part them: the two tails are separate FPCs
  of different widths and, in general, different lengths, each ending at
  its own connector, so the reader board needs the two ZIF connectors one
  behind the other, or facing each other, at the two tail ends, or a
  flexible run that spreads the tails apart before them (side-by-side
  connectors need about 4 mm between the FPC edges).  CAD mode ends both
  tails together, on one line across the boards (P5-diagonal-bus.md
  sections 27.3 and 27.4: the nearer end `tail_extension_mm` past the base
  edge, or farther where the 7.5 mm shortest tail sets the line), so where
  the tails overlap their stiffened ends and their contacts lie on each
  other: lengthen one tail (`tail.top_length_mm` or
  `tail.bottom_length_mm`) to put its connector behind the other's.  The
  tails do not bond to each other: keep the film and any adhesive off them,
  and let each flex on its own; the
  [turned-over tail](#which-tail-is-turned-over) takes its half twist where
  the tails have parted, so its flexible length must reach past that point.
  Above the tail roots the boards overlap freely too: they are separate
  FPCs on either side of the film.
- **Both boards reach past the exit edge.**  On the plan's named fields at
  2 mm pitch the tails' roots lie 3.9-6.5 mm below the field with `both`
  (5.5-12.7 mm with one side, whose whole bundle fans in under the field to
  the centred Row tail; 3.9-8.4 mm with the tail under the band, before
  `diagonal-bus/10`), both boards' at one level; the design
  workflow judge's 400 seeded designs measured 1.4-11.5 mm with `both` and
  1.6-8.8 mm one-sided (`diagonal-bus/7`, each board its own root: the Row
  roots 1.0-16.2 mm and 1.0-8.8 mm, the Column roots 1.4-11.4 mm and
  1.3-7.1 mm; `diagonal-bus/1`, with its corridor under the field, 2.4-38.1
  mm and 1.5-24.3 mm).  The Row board
  also widens beyond the field's 0.5 mm margin by its lane bands (3.46 and
  3.36 mm on the two sides of a 32 x 12 rectangle with both); on a
  receding shape such as a disk the lanes follow the field inward, but the
  stack keeps its widest width down to the field's bottom (the Column
  board's body, whose traces drop straight down beside the lower rows, and
  the one outline); down to the tails' roots the Column board is as wide
  as the Row board, and the Row board as wide as the Column fan-out.  Both
  outlines are regular (no corner flatter than 5 degrees but on a fillet):
  a run of the outline bending by less than that is one straight edge
  outside it, a few tenths of a millimetre wider where it ends (0.3-0.4 mm
  at the field's bottom on the named fields with both).  The
  housing and the tail budget must allow for this.
- **At most two bends per Row trace below the field.**  Each lane turns
  down on the field's bottom edge (or above it), off its band into a fan
  and into its contact, then runs straight down the tail (a lane straight
  above its contact does not bend): with `both` the two sides' fans meet in
  a V under the field, with one side they fan in under the field.  The fans
  run at 60-85 degrees from the vertical, never within 5 degrees of the
  Column fan-out's entry angle, so no fan runs along the Column fan-out's
  diagonals.  The Column traces bend at most twice below the field too
  (one V in both modes, at most 80 degrees where that roots the tails no
  deeper, so the fans keep 85): with the default 12 x 32 design the V runs
  at 80 degrees, the Row fans at 85 and both tails root 5.87 mm below the
  field (`diagonal-bus/7` in the rectangular mode: the Column root 21.84 mm
  below it with two lanes, the Row root 4.99 mm).
- **Crossings below the field.**  The Row fans cross the Column fan-out at
  5 degrees or more, and the Row contact columns may lie on the Column
  board's in the stacked tails and above them up to the traces' last
  bends, under coverlay;
  inside the taxel field no Row trace passes over a Column electrode or the
  Column board's field window, nor a Column trace over the Row board's, and
  the registration fails one that does (`trace_over_other_window_count`).
  The crossings outside the field are reported (`trace_crossing_count`,
  `trace_overlap_mm`); whether they couple measurably through the film is
  a question for the film vendor.

## The reader connectors

| Role | Reader connector | Pins | Contact | FPC drawing |
| --- | --- | --- | --- | --- |
| rows | TXGA FFC05001-16SBB124W5M (FlexiTac reader FPC1) | 16 | bottom contact, 0.5 mm pitch | width 0.5 x (n + 1), contacts 0.30 +/- 0.05 mm, exposed contact >= 3.00 mm, 0.30 +/- 0.03 mm thick |
| columns | THD THD0515-32CL-SN (FlexiTac reader FPC2) | 32 | bottom contact, 0.5 mm pitch | width 0.5 x (N + 1) +/- 0.07, contacts 0.30 mm over 4.00 mm from the tip, 2-R0.30 tip corners, 0.30 mm thick zone 6.00 mm long |

Each tail is sized for a P-position connector (`connector.row_pins`,
`connector.column_pins`; null means one position per channel): width
(P + 1) x 0.5 mm, contacts 0.30 x 4.00 mm starting 0.30 mm from the tip, the
outer contact centres 0.5 mm from the tail sides, R0.30 tip corners, one
coverlay window over all contacts from the tip edge, and a 6.0 mm bottom PI
stiffener flush with the tip and both sides.

- The default Column tail (32 pins) is 16.5 mm wide, the THD0515-32 width.
- The default Row tail has 12 positions (12 rows): 6.5 mm wide, like the
  approved 12-pin reference tail, but **not** the reader's 16-pin TXGA
  connector.  For that reader set `connector.row_pins` to 16: the tail
  becomes 8.5 mm wide with contacts 13-16 as isolated `NC_13`..`NC_16`
  (ascending).  The default stays 12 positions by product decision.
- The contacts start 0.30 mm from the tip (the JLC copper-to-edge rule; the
  gold-finger rule is 0.2 mm), so 4.00 mm of exposed contact spans 0.30-4.30
  mm from the tip.
- The contact zone is about 0.025 (core PI) + 0.035 (copper) + 0.225 (PI
  stiffener) = 0.285 mm thick, since the coverlay is open over the contacts,
  within the connectors' 0.30 +/- 0.03 mm (approved 2026-10-14: JLC
  recommends this PI thickness for a 0.3 mm connector on its 0.11 mm FPC).
  JLC holds the gold-finger area to +/- 0.03 mm, so measure the delivered
  tails.  The 0.2 mm JLC PI option, the default before, would give about
  0.26 mm, which the profile check rejects.  The stiffener is a profile
  value (`stackup.stiffener_thickness_mm`), not a form input.

### Masked fields and the other readers (CAD mode)

A masked field (`matrix.mask`, from CAD mode, whose fields follow the
selected area) is wired like any other: every `ROW_k` and `COL_k` has its
electrode, trace and contact pin,
and the reader scans the whole R x C matrix.  The positions outside the
mask have no copper crossing, so they always read 0; the CAD taxel map
lists only the active ones and its `readout` gives the row spans
(`inactive: "always 0"`), and the review bundle's `taxels.csv` lists every
position with `active`.  They stay 0 while the stack's misregistration is
below the registration's `inactive_crossing_separation_mm` (0.8 mm at the
2 mm pitch and the default fill 0.5, 0.4 mm at fill 0.7, 0.05 mm at the
tightest 0.6 mm pitch).

CAD mode's fit option `reader` sizes both tails for a reader of 16 x 16,
32 x 16 (the FlexiTac above: 16 sense lines on FPC1, 32 drive lines on
FPC2), 32 x 32 or 48 x 48 lines, either electrode set on either connector
(`connector.row_pins`, `connector.column_pins`), and the taxel map gives
each taxel's sense line `SR<n>`, drive line `SC<n>` and frame index
`(SC - 1) x sense lines + (SR - 1)` (docs/CAD_MODE.md, "Readers").  Only the
FlexiTac's connectors are recorded in the profile; for the other readers,
check their connectors against the tail drawing above (0.5 mm pitch, the
same contacts and stiffened zone).

### Which tail is turned over

Both reader connectors are bottom-contact and sit on the same face of the
reader board.  A bottom-contact connector touches the FPC face that lies
against the reader board, so both tails must arrive with their contacts
facing the reader board.  The stacked FPCs face each other copper to copper,
so their tails arrive with opposite copper orientations: **exactly one tail
must be turned over** before it is inserted.

With the reader board below or beside the sensor and its connectors on its
upper face (the arrangement assumed by D23), the physical top FPC's tail
(copper down) goes straight in and **the physical bottom FPC's tail must be
turned over**.  Give it a half twist about its own long axis, in the flexible
part between the stiffener and the board body (the stiffened 6 mm zone is
rigid).  Turning the tail over mirrors its contact row: seen from above, its
pin 1 moves from the left end to the right end, the same end as the top
FPC's pin 1.  With the reader board above the sensor and its connectors
facing down, it is the other way round.

The twist needs flexible length.  The default 12 mm bottom tail leaves
6.0 mm of straight, flexible Column tail beyond its 6 mm stiffener (the
`stiffener_end_clearance` record; 5.5 mm if the Row board is at the bottom),
still short for twisting a 16.5 mm wide tail (the 7.5 mm bottom tail of
before section 27.7 left 1.5 and 1.0 mm).  Lengthen `tail.bottom_length_mm`
(up to 80 mm) for the turned-over tail; how much length a twist needs is an
open mechanical decision.

### Ordering for the reader connectors

Order each board as a 1-layer, 0.11 mm FPC with 1 oz copper and a 0.225 mm
PI stiffener at the contacts, a +/-0.05 mm outline tolerance (a special
request) and ENIG, and check that the 0.3 mm gold fingers come out within
+/-0.05 mm (JLC's trace tolerance is +/-20%).  On the order form set Gold
Fingers to Yes and Gold Fingers Thickness to 0.3 mm, the stiffened contact
zone in total: JLC gives that total the highest priority when it chooses the
stiffener under the gold fingers (its PI calculator may take another PI
there than the 0.225 mm stiffener option).  These are the profile's
order requirements (`ORDER_NOTES.txt` in each ZIP lists them with their
reasons and sources): the tolerance holds the THD0515-32CL-SN tail width
0.5 x (N + 1) +/- 0.07 mm, which JLC's default laser-outline tolerance of
+/-0.1 mm does not guarantee; the core, the copper and the stiffener give the
contact zone above, inside the 0.30 +/- 0.03 mm the connectors take; the
finger width is the TXGA drawing's 0.30 +/- 0.05 mm.

The profile's stack-up (`stackup`) is the ordered build: a 0.025 mm PI core,
0.035 mm (1 oz) copper and a 0.025 mm PI + 0.025 mm adhesive coverlay make
the 0.11 mm FPC.  That is JLC's 25 um-dielectric 1-layer FPC with the
coverlay JLC puts on 1 oz copper (its 0.07 mm 1-layer FPC is the 0.5 oz
build, its 0.12 mm one the 50 um dielectric), derived from JLC's
finished-thickness and coverlay tables; confirm the copper weight on the
order form.  The profile check rejects a stack-up that does not add up to
the ordered thickness, a copper weight JLC does not offer and a contact zone
outside the connectors' 0.30 +/- 0.03 mm.

The design rules are checked against JLC's minimum for the ordered 1 oz
copper, 4/4 mil (0.1016 mm; 3.5/3.5 mil applies to 18 um copper only): the
bundle traces and their spacing, the electrodes (`routing.min_electrode_width_mm`,
0.1016 mm since 2026-10-15, 0.1 mm before) and the gap of the gold-finger
traces, which the whole-board DRC also holds between every tail piece and
the routes beside it.  At JLC's +/-20% a 0.127 mm bundle trace may come out
at 0.1016 mm; choose a wider `routing.trace_width_mm` (up to 0.254 mm) if
that margin is too small for the application (a bundle pitch above about
0.25 mm makes the expansion below the Row field taller, see
[LAYOUT_SCHEMA.md](LAYOUT_SCHEMA.md#row-channel)).  Each board's lines of
`ORDER_NOTES.txt` give its trace widths and what -20% makes of its fan-out
traces.

### Matching pin 1 to the connector

The connector's terminal 1 is fixed by the reader board's footprint, which
this application does not model.  For each tail, as it will be inserted
(contacts facing the reader board), find which end carries the contact
marked pin 1 in the preview (with the default ascending order and the tails
at the bottom of the stack as seen from above: the right end, for both tails,
after the turn-over above).  If that is
not the end of the connector's terminal 1, generate that role with the other
`channel_order`: pin 1 moves to the other end of the contact row, the copper
does not change, and `pinout.csv` and `netlist.ipc` then name the connector
pin each channel lands on.  The scan firmware reads channel `ROW_k` or `COL_k`
at the connector pin `pinout.csv` lists for it; on a
[diagonal Row bus](#the-diagonal-row-bus) the Row pins fold, so that pin is
not *k*.

## A sensor from the Library

The Library (`library.html`, 2026-11-05) holds sensors already fitted to
open-source gripper fingers, each with an address that does not change:
`library.html#<id>` shows it (its picture on the part, exploded or
assembled, and over it the same scene in 3D to turn; its facts, Gerber
ZIPs, part STL and licence)
and `./?part=<id>` opens it in Gen by Surface, its part loaded and its sensor
built from its shipped fit (`web/library/fits/<id>.json`, the request the
page sends for it and the engine's reply), as the default part is.  `<id>` is
`<part>-<pitch>mm` (for example `widowx-250-1mm`, `umi-finray-1.5mm`, and
for the UMI finger's tapered tips `umi-trap-tip13.8-2mm` or
`umi-convex-tip5.8-2mm`: the shape, the tip width in mm, the pitch); a
part's id alone (`./?part=widowx-250`) opens its 2 mm sensor and a family's
(`./?part=umi-tapers`, the tapered tips) its default tip, as
`library.html#<id>` does, `?debug` may follow, and an unknown id opens the
UMI finger with a warning.  The tapered tips' card is
`library.html#umi-tapers`.  Generating
from there is the usual flow: every setting stays editable, and the user's
own file or Remove model leaves the Library sensor (`?part` goes from the
address, the pitch, fill and rotation it set go back to the page's
defaults).  The 3D view frames the mapped sensor (`main.js`
`lookAtTaxels`), as for the default part, and the far end of a large part
may leave it (the user's decision of 2026-11-05: the camera on the
sensor); the sensor on the part beside the registration shows the part
whole.  The Library's pictures and its sensor pages' 3D views are that
figure (`web/cad/onpart.js`), drawn from the Library's own files with no
engine or API (the user's requests of 2026-11-05;
[LIBRARY_VIEW.md](LIBRARY_VIEW.md)): the sensor's fit and part, the art of
its two boards (`web/library/art/<id>.json.gz`) and, for the seven
grippers, the gripper drawn whole (`web/library/scenes/<part>.json`, its
bodies in `web/library/bodies/`): a sensor on both fingers, the jaws fully
open, the far finger's stack exploding into the gap, the near finger
see-through in both views with its stack assembled (the user's decision of
2026-11-06).  On a turned pair (Franka Hand,
WidowX 250, Unitree Dex1, MakerMods) the other finger is the same part and
carries the same boards; on a mirror pair (Trossen WidowX AI, ARX X5, I2RT
YAM) it is the mirror-image part and carries the mirror-image boards,
which are not this sensor's: its Gerber ZIPs are the pictured finger's.
The UMI finger and its tapered tips keep the fingertip, and Gen by
Surface's figure is as it was.  Each picture is that view at its Exploded
and Assembled home, each drawing centred, every sensor's
(`tools/browser/library_shots.py`).  The sensors use reader none (one tail pin per line); for the
FlexiTac reader's connectors set Reader in Advanced Customization and fit
again.

## Integration checklist

1. Set `connector.row_pins` and `connector.column_pins` to the reader's
   connectors (16 and 32 for the FlexiTac reader).  In CAD mode the fit
   option `reader` sets both.
2. Choose `role_mapping` (which FPC is on top) and the shared connector side.
   With `routing.row_sides` the tails are stacked: place the two reader
   connectors so each tail reaches its own (one behind the other, or with a
   flexible run that parts the tails; [above](#the-diagonal-row-bus)).
3. Generate and inspect both copper-side previews (pin-1 markers) and the
   assembly preview (mirrored top board, both tails on the connector side).
4. Decide which tail is turned over (above) and, per role, the
   `channel_order` that puts pin 1 on the connector's terminal 1.
5. Take the channel-to-pin map for the firmware from `pinout.csv`; for a
   masked field (`matrix.mask`), `taxels.csv` in the review bundle also
   lists which ROW x COL positions are taxels (`active` 1) and which have no
   crossing (`active` 0, always read 0).  With `routing.row_sides` the Row
   pins fold (`tail.row_contact_order`), and `taxels.csv` gives both pins
   of every position.
6. Before ordering: set the order options of `ORDER_NOTES.txt` (above;
   Gold Fingers Thickness 0.3 mm among them),
   check the contact-zone thickness against the connector (0.285 mm with the
   0.225 mm PI stiffener), and review in the JLCPCB upload the outline, the
   coverlay windows (the contact window leaves only 0.05 mm of coverlay
   expansion beside the outer contacts, because it may not enter the R0.30
   tip corners, and the windows longer than JLC's general 20 mm for one
   opening, which each board's lines name), the stiffener layer and its
   detected thickness.

## Open items

Product decisions not implemented (D8): the reference design's 0.6 mm
electrodes (the default stays 1.0 mm), slits between electrodes, alignment
holes or fiducials, and the canonical 12 x 32 compatibility template.  Not
verified by this application: a JLCPCB upload of the current outlines,
windows and stiffener; physical insertion into either connector; continuity
per channel; the assembled stack.
