# The Library's 3D view: the formats

The user's requests of 2026-11-05: for the seven grippers that are not UMI
fingers, the Library shows the **whole gripper** with a sensor on both
fingers, the jaws fully open; and on each sensor's page in the Library
(`./#<id>`, the site's first page since 2026-11-16, "The first page"
below; `library.html#<id>` before; since 2026-11-15 a window over the grid,
"The details window" below) the picture becomes a 3D view the visitor can
**turn**, for every sensor (the grippers' whole-gripper scenes, the UMI
finger's and its tapered tips' fingertip scene).  The grid's cards stay
static WebP pictures.  Gen by Surface stays as visitors know it: its sensor
on the part draws the fingertip only.

This document freezes the files and interfaces that the work is built on
(they change only with a new format string; the one amendment, of
2026-11-06, was made before anything in these formats shipped).  That
amendment is the one exploding stack: the rules' `explode_stacks` and
`see_through_modes`, the checks `stacks_apart_min_mm`, `stacks_apart_min_px`
and `near_seen_min`, the numbers `near_seen` and `stacks_apart_px`, and
`see_through` drawn in both views; both formats stay v1.  A second
amendment, of 2026-11-12, adds the looks (the user's request that every
gripper be coloured after photos of the real product, with a metal's
lustre): optional keys only (a scene's `looks`, `part_look` and
`smooth_deg`, a body's `look`, the rules' `looks`, `part_looks` and
`part_smooth_deg`, a record's `part_look_sha256`), so a file written before
it is still a v1 file and is drawn as it was, pixel for pixel; see "The
looks" below.  The rules' optional `part_pad` (2026-11-14, the UMI pad's
tint) is one more such key.  Paths are relative to `web/` unless they start with `tools/`
or `tests/`.

## One renderer

- The sensor page's 3D view and the Library's pictures are drawn by Gen by
  Surface's figure, `cad/onpart.js` (`createOnPartView`), from files the
  Library ships: no engine runs and nothing asks the server's API.
- `createOnPartView(host, {onViewChange, onContext, probe, stage})` takes an
  optional `stage`: `null` (the default; Gen by Surface, `cad/main.js`,
  passes none, and the figure is the object it was) or a function
  `(internals, figure) => figure`, called once at the end of
  `createOnPartView`, whose return is the view.  `internals` is
  `{scene, camera, controls, renderer, canvas, look, partLook, view, place,
  render, requestRender, filmMaterial}`, the figure's own objects.
- `view.homes`, unset by the figure, may be set by a stage to
  `{exploded: [x, y, z], assembled: [x, y, z]}` (unit directions toward the
  camera in the figure's world frame): each mode's home is then that
  direction, else `drape.js` `homeDirection(mode)` as before.
- `cad/library_stage.js` is the Library's whole-gripper stage;
  `cad/library_view.js` is the Library's 3D view (it loads the files below,
  builds the stack with `drape.js` `buildStack` and draws it with
  `createOnPartView`).  `library.js` imports `cad/library_view.js` (and so
  three.js) on a sensor's page only, never on the grid.
- Turned (a drag, the arrow keys), the Library's view keeps the whole
  drawing on its canvas (`library_view.js` `fitLens`, since the
  verification of 2026-11-13: a turn keeps the home's distance, and a third
  of a turn round the YAM's base and the Franka's fingertips had left the
  canvas): at every change of the camera the lens widens just enough that
  every point the home frames (the stack's home points, `frameView`'s)
  lies within the frame's margin (`drape.js` `FRAME_MARGIN`) where the lens
  shift puts it, never narrower than `FOV_DEG`, and `FOV_DEG` at a home.
  The camera stays where it is, so its lamp, near and far and the edge
  bands are those of the home; the homes, the pictures and the shots
  tool's views are as they were.  Gen by Surface's figure keeps its lens.
  `library_checks.py` `part_view` turns the view 120, 180 and 240 degrees
  in both modes and finds no drawn pixel on the canvas's edge.
- The drag hint (2026-11-15, the user's request: "箭头能不能做成像schetchfab一样
  的动画", after the turn's mark of that day, a still chip in the corner,
  which it replaces): Sketchfab's "click & hold to rotate" made for this
  page.  In the view's host (`.lib-live`, so on every sensor's page and the
  showcase's; `library.js` `dragHint`, none on the shots tool's `?probe=shoot`
  page), a pointing hand between two block arrows over "Drag to rotate",
  drawn in `library.js` (Sketchfab's picture is theirs), at the bottom
  centre of the view, inside it.  Three treatments were tried on the real
  views at 1440 and 390 px: Sketchfab's own (a white hand on a soft dark
  halo, the label white with a dark glow), a frosted chip with the label
  inside, and the one kept: Sketchfab's is for a dark viewer, and on this
  page's light box (`#f5f5f7` in either scheme) its halo was a grey smudge
  and its white label faint, the chip a box sliding to and fro; the mirror
  of Sketchfab's for a light box, the hand and both arrows one white cursor
  edged in the page's ink (`#1d1d1f`), a hairline of white glow and a soft
  shadow, the label the ink at 85 % with a white glow, reads on the box and
  on white, orange and black parts alike, with no box of its own.  Its
  colours are fixed, not the palette's tokens: the box is light in the dark
  scheme too.  (Built with the ink's arrows at 72 %; the review of
  2026-11-15 found them grey on black over the black bases the hint mostly
  lies on, legible only through the glow, a smudge on a phone: of three
  arrows tried over WidowX AI, I2RT YAM, Dex1, ARX X5, UMI and Franka at
  1440 and 390 px (white block arrows edged in ink, slimmer ones, an ink
  shaft over a white under-stroke with white heads), the block arrows in
  the hand's material read best, as Sketchfab's do.)
  - Its size is the view's, not the window's (the review of 2026-11-15: by
    the window's width, below 900 px, a tablet's 3:1 view 685 x 228 px and
    the showcase's 338 x 423 px view on a phone had the small hint without
    its label, a 900 px window's 355 x 222 px view the full one over its
    whole base).  The host is a size container (`container:lib-live /
    size`), the drawing 13.4 % of its height (`--lib-hint`, `clamp(28px,
    13.4cqh, 44px)`, its width the viewBox's 84:44): 84 x 44 px from a view
    328 px tall (98 x 62 px with its label; a 1440 x 900 window's view is
    330 px tall, the showcase's 335 to 548 px at every width), never under
    54 x 28 px (from a view 209 px tall down: the 3:1 view is 113 px tall on
    a 390 px phone, 89 px on a 320 px one).  Its distance from the bottom (14 px at most) and its
    sway (30 px either way at most) are in proportion to the drawing; its
    label shows on a view 270 px tall or more (`@container lib-live
    (max-height:269px)` hides it: a 1024 x 768 window's 255 px view, every
    3:1 view), so a short view keeps its gripper in sight.  The hint then
    takes 18 to 24 % of the view's height from its bottom, but for a phone's
    3:1 view, 29 to 42 %, where the drawing's 28 px floor keeps it legible.
  - It shows once the view is drawn (`.lib-stage.is-live`; never over the
    picture or its placeholder), fading in (opacity, 0.2 s), and while shown
    it sways either way as a drag would, Sketchfab's motion (5 s,
    ease-in-out, for ever).
  - At the visitor's first use of the drawn view on its page (`used()`) it
    fades out (0.5 s after 0.5 s, still swaying: `.lib-live.is-used`), then
    its sway stops (`is-gone`, set on the fade's `transitionend`), so nothing
    moves unseen.  A use is a press of a mouse's or a pen's main button on
    the view, a key that turns it (the arrows), a double click (a mouse's
    first press, a touch screen's double tap), and a touch once it has
    turned the view (`viewNews`, at the turn's end).  A right or a middle
    click turns nothing and leaves it, and so does a touch that scrolls the
    window (the review of 2026-11-15: on a phone the view is the first thing
    in the window, and a vertical swipe over it, which scrolls the window's
    page, had hidden the hint for the page, the view never turned).
  - It stays hidden on that page: 0, Exploded | Assembled, and another
    pitch, shape or tip of the same gripper (a new variant is a new drawing,
    but the same page the visitor has just turned: showing the sway again on
    each pitch would be motion they did not ask for) keep it hidden.  The
    page is the gripper's (`pageOf`: the showcase's id, a part's, the
    tapered tips' family's).  Another gripper's page, or the window opened
    again (`rest()` forgets the page; Back then Forward too), shows it again.
    A lost WebGL context hides it with the view (the picture shown); once
    the context is back, the view drawn again, it shows if the view was not
    used yet.
  - The pointer passes through it (`pointer-events:none`: a drag begun on it
    turns the view); it is for the eye alone (`aria-hidden`; the host's hint
    says it in words).
  - Under `prefers-reduced-motion` it neither sways nor fades: shown still,
    hidden at once.  It is the page's one motion of its own, the dated
    exception to `library.css`'s rule that nothing moves on its own
    (`tests/test_library.py` allows exactly its transitions and its one
    `@keyframes`, each off under reduced motion, and nothing else).
  - The shots tool reads the canvas alone (and its page has no hint), so no
    picture changes.  `library_checks.py` `part_view` checks it at 1440 and
    390 px for a gripper and the UMI finger: never shown while the view
    loads, shown once drawn, its box and its sway in proportion to the view,
    its sway running and its reach (paused at its start, a quarter and a
    half), a right click leaving it, a drag begun on it turning the view and
    hiding it (its sway stopped), hidden through 0, the keys and a double
    click, on the phone a vertical swipe leaving it and a sideways one
    hiding it, hidden through a lost and restored context, after Back and
    Forward shown again, hidden for another pitch, shown again on another
    gripper's page and hidden by a turning key, and under reduced motion
    (`emulate_media`) shown still and hidden at once; `part_view_hint_sizes`
    measures it at nine windows from 1440 x 900 to 320 x 640, a gripper's
    view and the showcase's.

## The details window

The user's request of 2026-11-15: "after we click for all cards to details,
we may not jump to a new page. lets bump our to a large window, and if you
click the "x" of right top conrner, it will close and back show lib".
Since then a sensor's page and the showcase's page are no page of their own
that replaces the grid: every card's details (a gripper's card, a UMI
shelf's card (a pitch's and the Tapered tips card until 2026-11-16, a
finger shape's since: "The UMI shelf's shapes" below), the showcase's
picture and Details) open in a large window over the Library.

- The window is the Library page's (`index.html`, `library.html` until
  2026-11-16) `dialog#libWindow` (named by the page's
  title), which `library.js` opens with `showModal()` (`raise()`): the top
  layer, the page behind it inert, the focus kept inside it, Escape its
  cancel.  Its X (`button#libClose`, named "Close": the header's toggle's
  round grey button, its grey laid on the window's white) stands at its
  top right outside its scroller (`#libWindowBody`, which holds
  `#libDetail`), so it stays in sight while the page scrolls under it.
  Inside, everything is the page of before: the picture and its 3D view
  with Exploded | Assembled, the title, the line, the Pitch (or Shape and
  Tip width), the facts, Open in Gen by Surface, the downloads, the links;
  the showcase's label, line of detail, tutorial and sources.  Two columns
  from 900 px, one below with the phone's rules (the 3:1 picture, the
  showcase's 4:5 box).  The back link is gone.  A sensor's two columns are
  even (7 to 5 from 1280 px as a page of its own until then): in a window
  of at most 1200 px its facts' column was 440 px at 1440 px, its two
  Gerber pills stacked from 1024 to 1440 px and more of its facts and
  titles wrapped (the review of 2026-11-15); evenly, with the window's
  sides at most 40 px, it is 540 px there and 520 px at 1280 px, the page's
  520 and 460 px of before.  The pills are side by side from about 1100 px
  (the page's from about 1020 px).
- Its size: `min(1200px, 100vw - 2 x the page's gutter)` wide, as tall as
  its page up to the window less two gutters, its top a gutter below the
  window's (a pitch that changes its height never moves its top); its page
  scrolls inside it.  Below 735 px, and on a screen less than 501 px tall
  (a phone held sideways, where a card within the gutters had been 306 px
  tall: the review of 2026-11-15), it is a sheet over the whole screen,
  with no shadow (in the dark scheme the window's hairline had framed the
  phone's screen).  The cards' look: white (the dark card with its hairline
  in the dark scheme), 18 px corners, the theme's floating shadow; the
  backdrop `rgba(0,0,0,.45)` in both schemes; no blue but Open in Gen by
  Surface.
- The grid stays where it was under it, dimmed: opening the window moves
  no card and scrolls nothing, and the page does not scroll while it is
  open (`:root` `overflow: hidden`).  The width a scroll bar takes is
  measured as the window opens (`--lib-bar`, 0 for an overlay bar: a
  phone's, a Mac's) and made up on the page's right while it is open, so
  the grid keeps its width and place and the backdrop dims the whole
  screen.  (Until the review of 2026-11-15 `scrollbar-gutter: stable` kept
  the bar's room: in Chromium that room stayed bright beside the backdrop
  in the light scheme, and 100vw, the page's gutter with it, shrank by the
  bar's width, so the grid moved.)
- The address is the page's, as before: a card's link goes to `#<id>`, and
  that route opens the window, so Back closes it, Forward opens it again
  and `./#<id>` opened anew (a shared link, a reload) shows the
  Library with the window over it.  The Pitch, Shape and Tip width replace
  the address (no history entry) with the window open.  The tab names the
  sensor while the window is open and the Library when it closes.
- Its X, Escape (and Android's Back, a close request while a modal dialog
  is open) and a press and release on the backdrop (both on it: a drag of
  the 3D view, or of a selection, released over the backdrop never closes
  it, nor the second click of a double-click, as on a card where the
  backdrop then lies) close it (`closeWindow()`) to the grid's place of its
  sensor, the back link's address of before (`#gripper-<part>`,
  `#shelf-umi-finray`, `#showcase`), the card that opened it focused (the
  showcase's Details for its picture too); a window opened anew closes to
  its gripper's place, as the back link went.  No native jump, so the
  grid does not move.
- Closing makes no history entry (since the review of 2026-11-15: the
  first version pushed the place, as the back link had, and with Android's
  Back a close request while the window is open, each Back closed it and
  the next opened it again, for ever, from the grid and from a shared
  link).  `route()` marks each entry it comes to with this visit (the
  document's life) and its depth: a window's entry reached from the grid
  1, from a window's entry of depth n n + 1, else 0; the Pitch's, Shape's
  and Tip width's replaced address keeps the mark.  A window of depth n
  closes by `history.go(-n)`, back over the window's entries to the
  grid's, whose address then becomes the window's place, the grid shown
  as the back link showed it (its opener focused where the place holds
  it, else the place's card); one of depth 0 (opened at its own address,
  or reached from one, or marked before a reload) replaces its entry by
  that place.  A close on its way is asked once (a cancel the browser does
  not let be cancelled, then its close event).  So Back after a close goes
  where it went before the window opened, and Forward opens it again.
- One 3D view for the page (one WebGL context), its host moved into the
  window; three.js loads only when a window with a view opens, never on
  the grid.  The shots tool's `?probe=shoot#<id>` is a window
  too; its pane (the view's host fixed at 640 x 400, or 640 x 800 for the
  showcase, CSS px) and so the pictures are as before: on 2026-11-15
  `library_shots.py --check` found 0 of the 42 sensors differing,
  `--showcase --check` the showcase the same and `--check-generator` 0 of
  the 14 differing.
- Checks: `tests/test_library.py`
  `test_a_card_s_details_open_in_a_window_over_the_library` and the
  `LIBRARY_WINDOW` mutants; `tools/browser/library_checks.py` `part_window`
  (at 1440 x 900, 900 x 900 and 390 x 844, light and dark: each opener, the
  grid unmoved, the box and the look, the page held, the X in sight, the
  focus kept, the X, Escape, the backdrop, a double-click, Back and
  Forward, an address opened anew, and the window's history after an
  earlier page: close requests, a shared link, two windows' entries, a
  reload), `part_window_edges` (scroll bars that take room, landscape
  phones, the dark sheet) and `part_routes` (the even columns at 1280 and
  1440 px); `showcase_checks.py` `part_page`.

## Files

| Path | Written by | What it is |
| --- | --- | --- |
| `library/art/<id>.json.gz` | `tools/browser/library_shots.py` (the shoot) | the generator's art of the sensor's two boards (below) |
| `library/scenes/scenes.json` | by hand; its `scenes` map by `tools/library_scenes.py` | the index of the grippers' scenes and the rules |
| `library/scenes/<part>.json` | `tools/library_scenes.py` (private) | one gripper's scene |
| `library/bodies/<part>/<name>.stl` | `tools/library_scenes.py` (private), then `tools/library_split.py` | the scene's bodies: binary STL, mm; with looks, one file per component (one look each) |
| `tools/library_looks/<part>.json`, `base.json` | by hand | a gripper's look file (what `tools/library_split.py` writes its components, looks and scene from) and the base looks |
| `library/shots/manifest.json` | `tools/browser/library_shots.py` | the pictures' manifest, with the records below |
| `tools/browser/generator_figure.json` | `tools/browser/library_shots.py --pin-generator` | Gen by Surface's figure of each sensor of a part without a scene, pinned ("Parts without a scene") |
| `library/entries.json` | `tools/library_write.py` | each variant's `view` (below) |
| `vendor/flexitac-v2/geometry.json` | `tools/flexitac_v2.py` | the original FlexiTac pad's two FPCs, read from its official Gerbers ("A placed sensor") |
| `vendor/flexitac-v2/art.json.gz` | `tools/browser/flexitac_v2_art.py` | the art of that pad's two boards, of no build |
| `vendor/flexitac-v2/umi-finray.placed.json` | by hand | where that pad lies on the UMI finger: a placed record |
| `library/showcase.json` | by hand (its words); `tools/browser/library_shots.py --showcase` (its `placed`, `image` and `shot`) | the showcase's page's document ("The showcase's page") |
| `library/showcase/flexitac-g1.{exploded,assembled,card}.webp` | `tools/browser/library_shots.py --showcase` | the showcase's three pictures |
| `library/bodies/flexitac-g1/drawn-<name>.stl` | `tools/library_showcase.py` | the plain shapes the project draws for the showcase (screw and bolt heads, nuts, the block in the top slot, the extender boards, cable stubs) |

The bodies are third-party files (each one a row of `library/NOTICE.md`'s
tables, its licence text in `library/licenses/`, modified as its row says)
or the project's own (`bodies/makermods-metal/rail.stl`: a plain rail drawn
by the project, not MakerMods hardware, 158 mm long, no longer than the
open jaws need; and any `bodies/<part>/drawn-<name>.stl`: a plain shape
`tools/library_split.py` draws where a model lacks a component the photos
show, its STL header saying so, as the MakerMods Metal Arm's body drawn by
eye after the maker's photos round that rail since the user's decision of
2026-11-14: the beam's walls and end stops, the steel guide rail and its
holes, the housing and motor can, the camera's mount and lens).  No
MakerMods file is ever committed or drawn from (`tools/library_write.py`
`DENIED_SHA256`).

## The art: `library/art/<id>.json.gz`

The gzip (level 9, no name, time 0, OS byte 3 on every Python) of one JSON document written canonically
(sorted keys, `,` and `:` without spaces, ASCII):

```json
{"format": "flexitac-library-art/v1", "id": "widowx-250-2mm", "build_id": "...",
 "look": "photo", "px_per_mm": 12, "max_px": 4096,
 "boards": {"row": {"role": "rows", "physical_side": "bottom", "view_box": [0, 0, 1, 1], "region": [0, 0, 1, 1],
                    "active_outline": [[0, 0], [1, 0], [1, 1]], "px": [386, 609], "front": "<svg ...>", "back": "<svg ...>",
                    "outline": {"points": [[0, 0], [1, 0], [1, 1]], "cutouts": []}},
            "column": {"...": "the same keys"}}}
```

- Each board's first eight keys are, byte for byte, what `app.js` answers
  to `"fpc:board-art"` `{boards, px_per_mm: 12, max_px: 4096}` for the
  sensor's build in the page's default look (Photo): the art Gen by
  Surface's figure draws.  `outline` is the build's board outline (its
  `points` and `cutouts`, as `/api/generate` gives them).
- `build_id` is the variant's; `px_per_mm` and `max_px` are `main.js`
  `ON_PART_PX_PER_MM` and `onpart.js`'s texture cap
  (`tools/library_write.py` `ART_PX_PER_MM`, `ART_MAX_PX`).
- The page reads it with `DecompressionStream("gzip")` (a server that sent
  it inflated is read as it is); `tools/library_write.py` `art_bytes()` and
  `read_art()` write and read it.

## The scenes

`library/scenes/scenes.json`:

```json
{"format": "flexitac-library-scenes/v1", "about": "...",
 "rules": {"gap_share": 0.42, "min_step_mm": 2, "ghost_opacity": 0.28, "measure_px": [1280, 800], "depth_tol_mm": 0.1,
           "explode_stacks": ["sensor"], "see_through_modes": ["exploded", "assembled"],
           "camera": {"exploded": {"tilt_deg": 65, "elevation_deg": 30, "front": 1},
                      "assembled": {"tilt_deg": 57, "elevation_deg": 30, "front": 1}},
           "checks": {"opaque_cover_max": 0.10, "layer_visible_min": 0.25, "clearance_min_mm": 3,
                      "stacks_apart_min_g": 0.20, "stacks_apart_min_mm": 3, "stacks_apart_min_px": 20,
                      "near_seen_min": 0.50, "card_min_px": 20, "ghost_cover_min": 0.02}},
 "scenes": {"franka-hand": "scenes/franka-hand.json"}}
```

`scenes` maps each gripper part (every part that is neither the UMI finger
nor one of its tapered tips) to its scene, a path relative to `library/`.

The user's decision of 2026-11-06 ("每一个夹爪只用爆炸一个sensor, 靠近外面的
finger透明, 夹爪不爆炸; 靠近里面的finger不透明, 夹爪爆炸"): on every gripper
one stack explodes.

- `explode_stacks` names the fingers whose stacks explode in Exploded:
  `["sensor"]` (the decision: the far finger's, the sensor finger whose
  face the camera sees, explodes into the jaws' gap; the near finger's stays
  assembled on it in both modes) or `["sensor", "mate"]` (both, as before
  the decision; the stage still draws it).  The roles are the scene's,
  fixed while the view turns.
- `see_through_modes` names the modes in which a scene's `see_through`
  fingers are drawn see-through (`ghost_opacity`): `["exploded",
  "assembled"]`, the near finger see-through in both views.
- The stage has no defaults: without either key it draws no gripper.
- Optional, since 2026-11-12 (see "The looks"): `looks` `{name: look}`,
  `part_looks` `{part or family: a name of looks, or a look}` and
  `part_smooth_deg`, the look of the parts that have no scene; since
  2026-11-14 `part_pad` `{color, opacity}`, the tint of their assembled
  sensor's pad (see "Parts without a scene").

`library/scenes/<part>.json` (`"format": "flexitac-library-scene/v1"`):

| Key | What it is |
| --- | --- |
| `part` | the part id |
| `part_mesh_sha256` | the part's mesh, `parts.json`'s `mesh.sha256` |
| `about` | the scene's sources (each at its commit), the opening, how the mate was found; an override's reason |
| `frame` | `"the part's file axes, mm"`: every matrix and vector below is in it |
| `approach` | a unit vector: the fingers' approach axis (the camera's up) |
| `opening` | `{q_mm, limit_mm, joint, source}`: each finger's stroke, fully open |
| `mate` | `{kind: "turned" or "mirror", matrix, part}`: `matrix` takes the sensor finger onto the other one (`kind` is its determinant's sign); `part` true draws the part's own mesh there, false a body whose `finger` is `"mate"` |
| `bodies` | `[{mesh: "bodies/<part>/<name>.stl", sha256, bytes, triangles, matrix, finger}]`: `matrix` takes the body's file into the part's frame; `finger` is `"sensor"`, `"mate"` or `null`; optional `look`: a name of `looks` (without it the body is the part's grey) |
| `see_through` | a subset of `["sensor", "mate"]`: the fingers drawn see-through, in the rules' `see_through_modes` (the near finger, `["mate"]`, on every gripper: the user's decision of 2026-11-06) |
| `picture` | the words after the label in the pictures' alt text (`"on both fingers of the open gripper"`) |
| `camera` | optional: `{exploded or assembled: {tilt_deg, elevation_deg, front}}` over the rules' (tilt 45 to 70, elevation 15 to 45), its reason in `about` |
| `explode` | optional: `{gap_share}` over the rules' (0.25 to 0.45), its reason in `about` |
| `looks` | optional: `{name: look}`, the scene's looks (below); each one used by a body or by `part_look` |
| `part_look` | optional: a name of `looks`, the look of the part (the sensor finger's own mesh) and of its mate where the mate is the part; no clear coat |
| `smooth_deg` | optional: the crease angle of smooth normals, 1 to 90 degrees (35 where a scene has looks); absent: flat facets |

Every matrix is a 4 x 4 array of rows, applied to column vectors, its last
row `[0, 0, 0, 1]`, its upper 3 x 3 orthonormal.

## The looks

The user's request of 2026-11-12: every gripper coloured after photos of
the real product, in the 3D view and in the pictures, with a metal's
lustre.  Gen by Surface is not part of it: its figure, its 3D view and its
files are as they were.

A look is

```json
{"color": "#c9ccd0", "metalness": 1, "roughness": 0.45,
 "clearcoat": 0.6, "clearcoat_roughness": 0.15, "env_intensity": 1.5}
```

`color` an sRGB `#rrggbb` in lower case (the base colour, picked from a
photo), `metalness` and `roughness` 0 to 1; optional `clearcoat` and
`clearcoat_roughness` 0 to 1 (a clear coat makes the body a
`MeshPhysicalMaterial`, about 1.6 times a standard body's cost on a
software renderer: only where a part truly has one), and `env_intensity`,
0 or more, the strength of the studio's reflections on it (1 without it).
A name is lower case letters, digits and hyphens.

- One STL file is one component and has one look:
  `bodies/<part>/<component>.stl`, its entry's `look`.
- `part_look` is the look of the part and of its mate.  The part keeps the
  figure's own material (the contact shade lives in its shader), so its
  look cannot have a clear coat.
- `smooth_deg`: at each corner the stage sums, weighted by area, the
  normals of the facets that share the point (to 1 um) and face within
  that angle of the corner's own facet.  The bodies' files are in mm; the
  part's own file may be in metres (the Unitree Dex1's, the I2RT YAM's,
  the MakerMods finger's), so the stage welds its corners in the fit's
  unit times its scale to mm (the review of 2026-11-12: at 1 mm cells the
  YAM's tip had 11258 of 24000 corners more than 5 degrees off).  The
  bodies were decimated to within 15 degrees of the upstream normals, so
  35 degrees smooths every curved face and keeps the real edges.
- Every key is optional and a scene without them is drawn as before the
  amendment, pixel for pixel (`tools/browser/library_shots.py --check` on
  the scenes that have none; for a part without a scene,
  `--check-generator`'s view with the rules' looks served away).
- A finger's see-through copy takes its look's colour as a matte
  dielectric (never lighter than the part's own grey: a white ghost is
  lost on the card), at the rules' `ghost_opacity`.

### How the stage draws them (`cad/library_stage.js`)

- A material per look and drawing; the part's own material wears
  `part_look` for the drawing and is put back when the scene goes, so a
  UMI finger drawn after a gripper is as on a fresh page.  The sheets
  (film, boards) keep their own look; the one exception is the UMI pad's
  tint in Assembled (the rules' `part_pad`, "Parts without a scene"),
  drawn over them, never into their materials.
- The **gripper studio** (`GRIPPER_STUDIO`): a second environment, built in
  the stage with `studio.js`'s recipe and its own numbers, made on the
  first drawing that has a look and again when a lost WebGL context comes
  back.  `studio.js`'s `STUDIO`, `LIGHTS` and tone mapping are untouched
  (they light the sheets and Gen by Surface).  It is a darker room above
  the horizon (radiance 0.22 overhead, 0.10 at the horizon: the flags) with
  softboxes and rim strips at 1.6 to 5 where `STUDIO`'s stand, a lighter
  floor (0.6) and a front bounce (2.2) low behind the camera: at the
  Library's homes every upright face of a metal mirrors the room below and
  behind the camera, and with a dark floor aluminium fingers were black.
  No panel is above 5 (a blown highlight is a hole in a drawing on a light
  card).  128 px a cube face.
- The looks mirror it and take 0.45 of its diffuse light
  (`GRIPPER_STUDIO.diffuse`) on top of the lights': with the lights alone
  a white shell's faces turned from the key were a mid grey, with all of
  it the shell was lost in the card's ground.
- The floor, the front bounce and the diffuse share were raised after the
  reviews of 2026-11-12 (0.38, 1.3 and 0.3 before).  On the Franka Hand
  the shell's broad face, turned from the key at the homes, had read
  `#b1b3b7` (the photos: `#cfcfd7` to `#eeeeee`), the fingers `#9b9ea1`
  (`#c1c3d0` to `#d8d5d4`) and the black pad's side `#08090c`, darker than
  the film beside it; now `#cdd0d4`, `#c6c9cd` and `#272729`.  These
  numbers are every gripper's: a look that reads too dark or too light on
  one body is that part's own look with its `env_intensity`, never a
  change of the studio.
- Where the studio cannot be made (no half-float render target, a later
  three.js whose shader text changed) the looks are lit by the lights
  alone: the colours stay, the lustre goes.

### The base looks

One convention for every gripper, tuned on real bodies in the stage (the
Unitree Dex1, the ARX X5 and the Franka Hand, 2026-11-12, in the page's
light and dark scheme; the picture's box is the same light `#f5f5f7` in
both).  The data is `tools/library_looks/base.json`; a test keeps this
table equal to it.

| Name | Colour | Metalness | Roughness | Clear coat / its roughness | env_intensity | For |
| --- | --- | --- | --- | --- | --- | --- |
| `anodized-black` | `#232428` | 0.6 | 0.45 | - | 2.4 | black anodised aluminium: a dark metal with a soft sheen |
| `anodized-natural` | `#c9ccd0` | 1 | 0.45 | - | - | natural or clear-anodised aluminium, milled or bead-blasted |
| `steel-ground` | `#b4b7ba` | 1 | 0.35 | - | - | ground or zinc-plated steel: a rail, a shaft, a screw head |
| `steel-polished` | `#c8cacc` | 1 | 0.18 | - | - | polished or stainless steel: sharp reflections |
| `plastic-black-satin` | `#222224` | 0 | 0.4 | - | 1.8 | black moulded plastic with a satin skin |
| `plastic-black-matte` | `#262628` | 0 | 0.75 | - | 1.8 | matte black plastic, a cable's jacket |
| `plastic-white-gloss` | `#e2e4e6` | 0 | 0.3 | 0.6 / 0.15 | - | glossy white shell under a clear coat |
| `plastic-white-satin` | `#e6e8ea` | 0 | 0.45 | - | - | satin white shell or white printed part |
| `rubber-black` | `#232325` | 0 | 0.92 | - | 2.2 | black rubber: the flattest black |
| `print-black` | `#2a2a2c` | 0 | 0.65 | - | 1.5 | black FDM or SLS print |
| `tpu-orange` | `#f2601c` | 0 | 0.6 | - | - | orange printed TPU (the UMI soft finger) |
| `brass` | `#c9a45c` | 1 | 0.35 | - | - | brass: an insert, a bushing |
| `pcb-green` | `#1f6b3a` | 0 | 0.5 | - | - | green solder mask |

- The blacks.  Real grippers are mostly black, and the film is near black
  (linear 0.014, about `#1e1e1f`; `#323335` under its lamp at the Exploded
  home).  A faithful `#101012` body next to it would be one black shape,
  so no black of the table is darker than `#1c1c1c` (a part's own looks
  too: `tests/test_library_split.py`), and every black carries an
  `env_intensity` above 1: a black's base colour gives it almost nothing
  under the lights (a face turned from the key was `#08080a`, the review
  of 2026-11-12), so what a black shows is what it mirrors of the room,
  as a product photo's black does.  They differ by sheen, not by level
  alone: anodised aluminium is part metal with stronger reflections (its
  edges and curved faces catch the softboxes), satin plastic has a broad
  soft highlight, matte plastic and print almost none, rubber none.
  Measured on the ARX X5, all of it in one look, at the Assembled home
  (the sRGB luminance of the pane's pixels that are not its ground or the
  amber boards: the solids, the see-through finger's veil among them), in
  the table's order of the blacks: median 64, 69, 56, 49 and 57; the 2nd
  percentile 19, 22, 31, 30 and 30; the share below the film's 30: 11 %,
  8 %, 0.5 %, 2 % and 2 %; highlights up to about 180.  On the Franka Hand
  the rubber pad reads `#3c3c3e` on its face and `#272729` on its side
  next to the film's `#323335`.
- The metals.  Aluminium and steel read as bright metal with dark bands:
  on the Dex1 at the Exploded home natural aluminium spans 35 to 243
  (2nd to 98th percentile; median 172, 4 % of the pixels at 240 or more),
  polished steel 35 to 250 (median 138, 7 % at 240 or more).
- The whites sit close to the card's ground; the shading that separates
  them is the lights' (a near-white top, `#eef0f3` on the Franka Hand's
  shell, over faces at about `#cdd0d4`): an edge against the card's
  `#f5f5f7` is faint where a top face meets it.

### Overriding a base look

A gripper's look file (`tools/library_looks/<part>.json`) names base looks
directly (`"look": "anodized-black"`).  Where a photo shows that a
component differs, the file defines a look of its own:

```json
"looks": {"inlay-brushed": {"base": "anodized-natural", "color": "#c6c9cd", "roughness": 0.4, "env_intensity": 1.5,
                            "evidence": "the FR3 close-up: lengthwise brush lines, a wide streaked highlight"}}
```

`base` is the base look it starts from, the other keys are the numbers
that differ (a key set to `null` is dropped), and `evidence` (required)
says which photo shows it.  A part's own look may not take a base look's
name, so in every scene a base name means the table's numbers.  The scenes
hold the numbers themselves (the page reads only the scene): changing
`base.json` changes no scene until `tools/library_split.py` is run and the
part is shot again.

### Sharing a body out by material (`tools/library_split.py`)

The scene builder (`tools/library_scenes.py`, private, numpy and trimesh)
writes one decimated body per upstream mesh.  `tools/library_split.py`
(standard library, deterministic, public) is the step after it, driven by
one look file per part (an example; the committed
`tools/library_looks/arx-x5.json` shares that body into four components
with looks of its own):

```json
{"format": "flexitac-library-look/v1", "part": "arx-x5", "smooth_deg": 35, "part_look": "print-black",
 "about": "drawn after ...",
 "looks": {},
 "bodies": {"bodies/arx-x5/link6.stl": {"sha256": "...", "facets_sha256": "...", "weld_mm": 0.01, "components": [
   {"name": "link6-rail", "look": "steel-ground",
    "pick": [{"component": {"box": [[71.57, -85, -4.5], [78.07, 85, 4.5]], "triangles": 1294}}]},
   {"name": "link6-body", "look": "anodized-black", "pick": "rest"}]}}}
```

- `bodies` names every body of the scene as the scene builder wrote it,
  with the SHA-256 of that file: kept whole (`{"sha256", "look"}`; `look`
  may be `null`) or shared out into `components`, read in order; a
  triangle goes to the first component that takes it.
- `pick` rules: `{"component": {"box", "triangles", "tol_mm"}}`, the one
  connected component (triangles joined through corners welded at
  `weld_mm`, 0.01 mm by default) whose bounding box is that box within
  `tol_mm` (0.05) and whose triangle count is `triangles` if given;
  `{"components_inside": box}`, every connected component inside the box;
  `{"box": box}`, the triangles whose three corners are in the box;
  `"rest"`.  Every triangle must be taken; no component may be empty.
- `draw` instead of `pick`: plain shapes the project draws for a component
  the model lacks (`{"box": box}`, `{"cylinder": {"from", "to", "radius",
  "segments"}}` or, since 2026-11-14, `{"prism": {"axis", "from", "to",
  "profile"}}`: a convex polygon of 3 to 32 corners, counter-clockwise seen
  from the positive end of `axis` (`"x"`, `"y"` or `"z"`), drawn from `from`
  to `to` along it, its corners `(y, z)` about x, `(z, x)` about y and
  `(x, y)` about z: a chamfered block or a rail's rounded section in one
  shape), in the frame of the body they are listed under, so they
  stand on every copy of it; or under the file's `drawn` list, in the
  part's frame.  They are written as `bodies/<part>/drawn-<name>.stl`,
  the project's own (no row in `NOTICE.md`; say so in the file's `about`,
  which the tool puts after the scene's own `about`).
- It writes the component files (a picked one holds its triangles' facet
  records as the body's file has them, sorted, under the body's header
  with "; split"), the part's scene (each body's entry by its components'
  with the same matrix and finger, then `looks`, `part_look`,
  `smooth_deg`; every other key and byte as it was) and the bodies' rows
  of `library/NOTICE.md` (a split body's row by one row per component).
- The unsplit body stays pinned: `sha256` is the scene builder's file
  (also the scene's record before the split and git's history),
  `facets_sha256` the hash of its facet records sorted.  With the unsplit
  file at hand the tool splits it; without it, it splits the committed
  components' records together, which must have that hash: the same
  triangles give the same files.  So `--check` needs only committed files,
  and it proves that they are what the look files give.  An unsplit file
  of other bytes than `sha256` is refused, never passed over for the
  components of the split before: a body the scene builder made anew is
  pinned anew (`--pin`), on purpose.
- `--check` also reads every scene (the reviews of 2026-11-12): a look, a
  `part_look`, a `smooth_deg`, a body the project drew, a drawn file in a
  part's folder or a split body's `NOTICE.md` row, of a part that has no
  look file, fails it.  A drawn body's header only labels it; its look
  file's numbers are what draws it again, so a mesh under a drawn body's
  name cannot stay in the Library without a look file that draws exactly
  it.  One scene's looks are another tool's: the showcase's
  (`scenes/flexitac-g1.json`, below), written by
  `tools/library_showcase.py` from its own copy of the base looks and held
  to it by that tool's `--check`; so are the shapes that tool draws for
  it, each pinned by its SHA-256 (`tools/library_write.py`
  `SHOWCASE_BODIES`, which `showcase()` holds the files to) and drawn again
  by that tool on every run: a drawn body of the showcase's that is not
  pinned there is refused as any other.  `tests/test_library_split.py`
  runs the check on the committed library.
- A part without a look file is not touched.  `--pin FILE` prints a
  body's two hashes, `--components FILE` its connected components,
  `--out DIR` writes a dry run elsewhere.
- Order after a change: (the scene builder, when the geometry changes,)
  `tools/library_split.py`, `tools/library_write.py`, the shoot of that
  part's sensors, `tools/library_write.py`, `--check` of all three.

### Parts without a scene

The UMI finger and its tapered tips have no scene.  `scenes.json`'s rules
give them their look, the real finger's orange TPU (2026-11-12, with the
user's request that every gripper be coloured after photos of the real
product; Gen by Surface keeps its grey part):

```json
"rules": {"looks": {"umi-tpu-orange": {"color": "#e85a1c", "metalness": 0, "roughness": 0.85, "env_intensity": 0.3}},
          "part_looks": {"umi-finray": "umi-tpu-orange", "umi-tapers": "umi-tpu-orange"},
          "part_pad": {"color": "#545a3a", "opacity": 0.65}}
```

- `part_looks` maps a part's id, or its family's (`parts.json`), to a name
  of the rules' `looks` or to a look itself; the part's id wins over its
  family.  No clear coat.  A gripper is not named there (its look is its
  scene's).  A base name means the base's numbers here too
  (`tests/test_library.py` compares them with `base.json`); a look of the
  rules' own has another name, as `umi-tpu-orange` has.
- The orange (`umi-tpu-orange`, the rules' own look, tuned on the UMI
  finger itself in the stage, 2026-11-12).  The photos of the real finger
  (UMI's hardware guide, FlexiTac's own pictures, the owner's photo of
  the xArm gripper; Polymaker TPU 95A "Orange") read `#ec660e` where lit
  (from `#dc531c` to `#fd7301`), `#c14809` in the mid-tones and `#9c3802`
  to `#833205` in the ribs' shadow.  A saturated colour must take little
  of the room: the base look `tpu-orange` (`#f2601c` with all of the
  studio) drew the finger's lit face `#f56e42`, a salmon, the white of
  the studio's reflections and of its diffuse light added to the orange
  and the tone mapping pulling the bright red toward white.  With
  `env_intensity` 0.3 and `#e85a1c` the finger's pixels (those of the
  pane that the look changes) at the Exploded home are `#e65814` (the
  brightest quarter's median), `#c0480f` (the middle half) and `#973604`
  (the darkest quarter); at the Assembled home `#db5416`, `#c74b0e` and
  `#8f3304`.  The sensor lies on it: the amber boards (`#d07404`, hue 33
  degrees) are of the same lightness as the lit orange (hue 19),
  so they stand apart by hue and by their dark edges, not by lightness (a
  luminance ratio of 1.07 to 1.10 on the lit face, 1.3 to 1.5 on the
  rest); the film is far darker (2.4 to 3.7).  Exploded, as the sheets
  apart are; assembled, the real sensor's pad is far darker than its
  finger, and the pad's tint (`part_pad`, below) draws it so.  That is why the orange is at the red end of the
  photos' range: `#ee6606`, nearer the photos' mean, drew the boards and
  the finger in one hue (23 against 33 degrees).  The base look
  `tpu-orange` keeps its numbers: the base table is not the rules' to
  change.  The showcase's fingers wear the same numbers under the same
  name, as a look of the showcase's own (since the merge of 2026-11-13;
  `tests/test_library_showcase.py` holds the two equal), so the showcase
  and the UMI rows below it are one orange.  Its roughness is 0.85 since
  the verification of 2026-11-13: at 0.6 the faces turned up to the
  lights took their white sheen, a washed salmon (the showcase's near
  finger's back `#cb654a`, saturation 0.64, beside the photo's `#d44a1b`,
  0.87; the UMI finger's fin windows a third of a turn round), and a
  printed TPU is matte; now that back is `#c44b17` (0.88) and the
  salmon pixels of those two views a ninth and a twentieth of what they
  were, the homes' other pixels as they were.
- `part_smooth_deg` is the crease angle for those parts (absent: flat
  facets).  The committed rules have none: the finger is a printed prism,
  flat faces and sharp ribs with a few small fillets, and 35 degrees
  changes almost nothing.  Measured on the finger and a convex tip,
  Exploded and Assembled, at the home and turned left, right, behind and
  above (twenty views of the pane at twice the CSS size; the flat view
  shot twice is the same pixels): under 0.46 % of the pane's pixels
  change at all, in sixteen of the views none by more than 14 of 255,
  and in the four turned to the right under 0.05 % by more, at most 28:
  a highlight along the mount block's rounded corner.  Side by side the
  two are the same picture.  Flat, the part's geometry and normals are
  exactly Gen by Surface's.
- `part_pad` is the tint of the assembled sensor's pad on those parts
  (the user's decision of 2026-11-14 on the UMI pad, "you can do it
  darken"): `{"color": "#rrggbb", "opacity": above 0 and at most 1}`,
  only with `part_looks`.  The final visual check of the stage-2 Library
  found every Assembled picture of the UMI rows and the tapered tips one
  orange block: the top board's art alone over the field, a bright amber
  (`#cc7103`, hue 34 degrees, value 0.80) on the orange finger
  (`#d95317`, hue 19) at the same brightness, where every photo of the
  built sensor shows a dark olive-brown pad on the orange finger: the
  black film seen through the top board's amber polyimide between its
  copper (FlexiTac's own photo of the sensor on a UMI finger:
  the pad `#725013` to `#665318`, hue 39 to 45, value 0.40 to 0.45; the
  finger `#e84407` to `#ea4501`).  The stage lays the film's own sheet
  once more, its assembled place lifted one nest and 0.02 mm along its
  normals (just over the top board), its outline the film's texture's
  alpha, in the tint's colour at its opacity, lit by the figure's
  lights, satin as the boards' coverlay (roughness 0.45), shown in
  Assembled only (`library_stage.js` `layPad`, `PAD`).  So the field
  reads the photos' olive-brown, the top board's traces still faintly
  seen through it, while the board's border round the field, its tails,
  the edges and the whole of Exploded (the sheets apart, the film between)
  keep the sheets' own look.  The committed tint, `#545a3a` at 0.65,
  was tuned in the stage on the 2 mm finger against that photo; at the
  Assembled home the pad's pixels (those the tint changes) read
  `#6f5413` (hue 42, saturation 0.83, value 0.44; `#ca7003`, hue 33,
  value 0.79, without it) and the finger's orange pixels `#ba4709`
  (hue 21, value 0.73) as before; turned a third of a turn either way
  `#6e5310` and `#735719` (hue 41 to 43, value 0.43 to 0.45); the same
  in the light and the dark scheme (the view's pane is light in both),
  and the same on the tapered tips (the 5.8 mm trapezoid, the 13.8 mm
  convex tip, whose masked field the film's outline follows).  In the
  fourteen committed Assembled pictures the pad's pixels are `#705512`
  to `#715612` (hue 42 to 43 degrees, value 0.44; `#cb7103`, hue 33,
  value 0.80, before), 13 to 27 % of the drawing (the 1 mm finger's
  the least, the 2 mm finger's the most), and the finger's orange
  `#bc4709` (its lit quarter `#da520b`, hue 21, value 0.85) as before:
  the photo's gap of about 21 degrees of hue and half the
  brightness.  The photo's traces are stronger than the tint leaves
  them (its copper bright between dark stripes of film; here the
  board's art, whose copper reads a little darker than its polyimide,
  at a third of its contrast).  Gen by
  Surface draws no pad: its figure is its own, and `--check-generator`
  holds the tint to the Assembled sheets (below).
- `cad/library_view.js` reads the rules for such a part and hands the
  stage `{look, smooth_deg, pad}`; the stage draws the part's own
  material in it for that drawing, and the pad's tint where there is one.
  Without a rule the part is Gen by Surface's grey.
- The rules are hashed into every gripper's `scene_sha256`, and a record
  of such a part keeps `part_look_sha256`
  (`tools/library_write.py` `part_look_sha256(part_look(...))`, the pad's
  tint among it where the rules give one): a changed look or tint makes
  the pictures stale.

Until the look, the Library's pictures of these sensors were Gen by
Surface's figure byte for byte, and `library_shots.py --check-generator`
held the two together.  They differ now by design, so the check holds what
still holds (for each sensor of a part without a scene, in a browser,
writing nothing):

1. Gen by Surface's figure (`gen.html?part=<id>`; `./?part=<id>` until
   2026-11-16) is the picture pinned for it:
   `tools/browser/generator_figure.json`
   (`"format": "flexitac-generator-figure/v1"`; per sensor the fit and the
   build it is of, and the bytes and SHA-256 of its three pictures as the
   shots tool encodes them).  The pin was written from the figure on
   2026-11-12 and is, record for record, the Library's manifest of before
   the look: the figure of today is the figure of then.
   `--pin-generator` writes it anew, only for a deliberate change of the
   figure or a sensor's new build.
2. The Library's view with the rules' looks served away is that figure,
   pixel for pixel: without a look, the Library's view of such a part is
   Gen by Surface's (the same part, sheets, lights, camera and frame).
3. The Library's view as the rules are gives the committed pictures, byte
   for byte.
4. The look touches the part alone.  The view is shot once more with the
   look in another colour (every channel half the range off).  Its alpha
   is the figure's at every pixel (the same outline), and every drawn
   pixel that is the same in both colours (what the part's colour does
   not reach: the sheets, and their edges on the ground) is the figure's
   pixel.  The pixels the colour does reach, and the others, must each be
   a share of the drawing (0.1 and 0.25 at least), so neither statement
   is about nothing; on the fourteen sensors the part's are 44 to 52 % of
   the Exploded drawing and 26 to 41 % of the Assembled one.  Where the
   rules give the pad a tint, this comparison is of the view with the
   tint served away (`unpadded()`).
5. The pad's tint touches the Assembled sheets alone (since 2026-11-14;
   `pad_differences()`, `pad_problems()`): the view with the tint (the
   pictures') against the view without it has the same alpha at every
   pixel, changes nothing in Exploded, and in Assembled changes only
   pixels the part's colour does not reach (by the fourth comparison's
   witness in the other colour), `PAD_SHARE_MIN` (0.05) of the drawing at
   least.  Five drawings a sensor then.

`tests/test_library.py` holds, without a browser, that the pin is of
exactly these sensors and their builds, and that the committed pictures
are the pinned files where the rules give no look and other files where
they give one.

## The showcase's scene and files

The Library's first section is a showcase (the project owner's decision of
2026-11-12): the hand-designed FlexiTac sensor on the xArm Gripper G1 with
UMI soft fingers, as the FlexiTac Tactile Demo shows the gripper and as the
owner's photo of the gripper as built shows it.  It is not a part or an
entry: no fit, no build, none of the generator's downloads.  Its geometry
is written by `tools/library_showcase.py`:

| Path | What it is |
| --- | --- |
| `library/scenes/flexitac-g1.json` | the showcase's scene: a scene as above, about the UMI finger (`part` is `umi-finray`), with looks and a camera of its own; not in `scenes.json`'s `scenes` map |
| `library/bodies/flexitac-g1/umi-right-finger-holder.stl` | HandUMI's finger holder (Apache-2.0, a row of `library/NOTICE.md`), decimated to within 0.1 mm; drawn twice, the left one by a mirror matrix |
| `library/bodies/flexitac-g1/drawn-<name>.stl` | seven plain shapes the project draws (below): no vendor's geometry, no row of `NOTICE.md` |
| `vendor/ufactory-g1/<name>.stl` | twelve meshes made from UFACTORY's 3D model of the Gripper G1 (split, decimated to within 0.1 mm), in the model's own axes, mm; the property of UFACTORY, not under the repository's licence |
| `vendor/ufactory-g1/NOTICE.md` | whose they are, why they are here, what was changed, each file's SHA-256 |

- A body of the showcase's scene is a file of `bodies/flexitac-g1/` or, for
  the vendor's meshes, `"../vendor/ufactory-g1/<name>.stl"`: every `mesh`
  stays a path relative to `library/`, as `parts.json` gives the UMI
  finger's (`"../vendor/umi/..."`).  No other scene may hold a path that
  leaves `library/`.
- The scene lists the two holders first (the sensor finger's, then the
  mate's), then the vendor's twelve: `body_shell`, `body_frame`,
  `body_flange`, `body_pins`, `link_{r,l}_{outer,inner}`,
  `finger_{r,l}_coupler`, `finger_{r,l}_pins`; then the drawn shapes, each
  file once for every place it stands in.
- **The part is the gripper's left finger** (`PART_SIDE`): the UMI finger's
  file placed as the right finger and turned half a turn about the
  gripper's axis (the finger is its own mirror image through the middle of
  its thickness, to 1e-9 mm, so it is the same finger there).  The pad's
  placed record rolls its tails over the finger's side face at file
  y -25.8, as the FlexiTac team mount it (the tails to the viewer's left
  with the fingertip up); on the left finger that face looks the way of
  the shell's face **without** the logo.  The owner's photo, taken from
  the logo's side, shows both fingers' straps on the far side, through the
  fin's windows: so they are here.  `finger` is `"sensor"` for the left
  finger's coupler, pins and holder, `"mate"` for the right one's, `null`
  for the body and the links.
- The pose: the links turned until the two sensors' centres are 55 mm apart
  (24.35 degrees of 45; `opening.q_mm` 22.905 of `limit_mm` 39.699, each
  finger's shift across the jaws: the showcase is not fully open).  The
  mate is drawn as the mirror image across the gripper's middle plane (the
  lead's decision of 2026-11-12), so both fingers' straps are on the same
  side, as in the photo, and the mate carries the mirror-image pad.  (The
  gripper as built differs in its holders: two plain printed blocks that
  read as one part used twice, the second turned half a turn about the
  gripper's axis, not HandUMI's tapered holder and its mirror image.)
- **Its camera is its own** (`camera`, a scene's override of the rules'
  within their bounds, its reason in `about`): 60 degrees off the pad's
  normal, 20 degrees up, `front` -1 (with this part: the side of the
  shell's face without the logo); Exploded from the same side 70 degrees
  off and 40 up (since the verification of 2026-11-13: at the Assembled
  camera the lifted layers stood edge-on, a column 90 px wide, and 8 % of
  the drawing told the two modes apart).  At the rules' camera the
  far finger's pad was edge-on and its straps on its far side; from here
  the pad's face, the straps crossing both fingers' side faces, the near
  finger's back and the gripper's body are all seen.  The logo, on the
  shell's other face, is not drawn.
- **No finger is see-through** (`see_through` `[]`): the jaws are 55 mm
  apart and from this camera the near finger hides nothing of the far
  one's pad, in either mode; the showcase is the gripper as built.  (Every
  generated gripper keeps the near finger see-through, the user's decision
  of 2026-11-06.)
- What the project draws (`tools/library_showcase.py` `DRAWN`; each a file
  `bodies/flexitac-g1/drawn-<name>.stl` of `tools/library_split.py`'s boxes
  and cylinders under its header of a shape the project drew): what the
  owner's photo shows and the models have only as holes, or not at all.
  `shell-screw`: a black screw head in each of the shell's twelve wells
  (six a face; found in the vendor's mesh at x 41.25 / 41.25 / 33.5,
  y 38.5 / 12.0 or 3.75 / -15.0 mm).  The six on the logo's face are where
  the owner's photo shows them; the six on the face without the logo,
  which the home camera shows and no photo does, are in the wells the
  model has there.  `holder-bolt` and `holder-nut`: each
  holder's three socket heads in its counterbores and three hex nuts in its
  pockets, through the soft finger's own three holes.  `slot-block`: the
  black block with its round cap in the shell's top slot (the frame behind
  it is white, as the photo's channel is).  `extender`, `extender-sockets`
  and `cable-stub`, behind each finger, placed by eye on the pad's tails:
  the yellow extender board, its two white sockets, and a short stub of
  the white flat cable.  Past the roll over the side face both tails lie
  in one plane that leaves the fin's sloping back (`TAILS_PLANE`, 21.7
  degrees to the finger's length, within 0.3 mm); the board lies along it
  (`board_place()`), over the Top FPC's strap, with each tail's end in one
  of its sockets: the wide tail's stiffened end (`TAIL_END`) in the upper
  one at the board's edge, the Top FPC's tab (`TAB_END`) in the lower one,
  through the board; the stub runs from the lower socket down the finger's
  back between the holder's flanges and ends above the finger's base
  (`cable_place()`).  The ends are where the Library's view lays the placed
  pad: `tests/test_library_showcase.py` holds the sockets round them and
  `tools/browser/showcase_checks.py` `part_tails` measures them in the
  view.  The gripper as built has one small board for each tail; here one
  board stands for both.  16 KB in all.
  They need no source: the tool draws them again on every run, their
  SHA-256 pinned with the holder's (`library_write.SHOWCASE_BODIES`).
- It carries the optional keys of the amendment of 2026-11-12: `looks`,
  each body's `look`, `part_look` and `smooth_deg` (35).  Its looks are
  base looks under their base names with the base's numbers
  (`tools/library_showcase.py` `BASE_LOOKS`; a base name always means the
  base's numbers): `anodized-black` (the links, the flange, the slot's
  block); and seven of its own (`OWN_LOOKS`, a base look with the numbers
  that differ and its evidence).  The four
  of the gripper's own bodies were judged at the home and turned 60, 120,
  180, 240 and 300 degrees, half-way round being the logo's side the
  owner's photo was taken from (sRGB medians of each body's own pixels,
  found by drawing the bodies once in flat colours; the base looks, tuned
  at the home only, had left the shell `#e9ebee` and a holder `#e4e6e9`
  there, all but lost in the card's `#f5f5f7`, the pins' flat ends white
  discs `#f6f8fa` and the screws a mid grey `#6c6d72`):
  `shell-white-gloss` (the shell, the one clear coat: the base
  `plastic-white-gloss` with a smoother skin, roughness 0.1, under a full,
  sharper coat, 1 at 0.02, with seven tenths of the studio; its face
  `#c3c5c8` at the home and `#dbdddf` half-way round, its rounded edges
  carrying a bright line, as the photo's shell, `#c4bfbb` on its face,
  carries the windows' streak on its top edge), `print-white` (the
  frame's channel, the printed couplers and holders: the base
  `plastic-white-satin` at `#d8dadc`; a holder `#c8cace` and `#d9dbde`,
  the photo's `#c8c9ca`), `steel-pin` (the pivot pins: the base
  `steel-polished` brushed, roughness 0.7, at `#a0a2a4` with half of the
  studio; the flat ends `#7a7c7e` from the logo's side, the photo's
  brushed mid-grey discs, and the Phillips heads `#585a5c` at the home)
  and `screw-black` (the drawn screws, bolts and nuts: the base
  `anodized-black`'s colour as a matte black, no metal, roughness 0.9,
  the studio at 1.9; `#25262b` at the home, `#2e2f33` half-way round,
  where the anodized metal mirrored the studio); `umi-tpu-orange` (the
  soft fingers: the base `tpu-orange` at `#e85a1c` with three tenths of
  the studio, the UMI rows' look of the rules, number for number; chosen
  by the merge of 2026-11-13 next to the owner's photo, whose fingers read
  `#d85623` / `#c94917` / `#8f1601` (sRGB medians of the brightest quarter,
  the middle half and the darkest quarter of their orange pixels): the
  base orange drew them `#f17c5b` / `#e15c28` / `#d2571b` in the Assembled
  picture, the near finger's lit back a salmon `#f08265`, and this look
  draws them `#cd5d3c` / `#ba460b` / `#a53e0a`, at roughness 0.85 since
  the verification of 2026-11-13, the lit back no longer salmon); and two of what the
  project draws: `pcb-yellow` (the extender boards: the base `pcb-green`
  in the photo's yellow) and `ffc-white` (the sockets and cable stubs:
  the base `plastic-white-satin`, warmer).  The blacks: at its homes the
  pixels of the `anodized-black` bodies (then the links, the flange, the
  screws, bolts and block; found by drawing them once in another colour)
  had a median sRGB luminance of 40, the 2nd percentile 17, the 90th 122
  and the 98th 164, and 4.8 % of them were below the film's 30 (the
  convention's own measure on the ARX X5: 11 %); at the rules' camera a
  link's face had sampled `#181a20`.  The photo's links are a deep black
  with a sheen, so the base look stands for them.  `showcase()` checks the
  looks over all its bodies with
  `scene_look_problems()`, the grippers' scenes' own check, and
  `tests/test_library_showcase.py` holds `BASE_LOOKS` to
  `tools/library_looks/base.json` and the own looks to their numbers.
- What still differs from the photo: the holders' shape (above); one
  extender board for both tails; the polyimide tape, the laminating
  sheets, the silkscreen, the second adapter board on a holder's face and
  the cables' run to the reading boards are not drawn; the screws are
  plain discs; the tails' gold ends read dark brown, not gold (the pad's
  art, as on every sensor); the near finger's lit back (`#cc6346`) is a
  little pinker than the photo's lit orange (`#d85623`).

`tools/library_write.py` `showcase()` is its guard, and `scenes()` reports
its problems with no part (so `--check`, the site build and the tests stop
on them): the vendor's folder holds exactly its twelve meshes, each at its
pinned SHA-256 (`SHOWCASE_VENDOR_FILES`), and its notice, within
`SHOWCASE_VENDOR_BUDGET_BYTES`; the notice has the decision's wording
(`SHOWCASE_WORDS`), never "CAD", and a row for each file; the vendor's own
file, unsplit and undecimated (`SHOWCASE_SOURCE`: by its SHA-256, or by its
size and the SHA-256 of its triangles under another header), is nowhere
under `web/`, nor is a model of the deny-list (the file's undecimated
pieces are on it), nor a byte copy of one of the folder's meshes outside
its place (every file under `web/` is hashed);
no part, entry, fit, picture record, sample or other scene names the folder;
the scene is a scene of the UMI finger whose own bodies are tabled with an
open licence as every body or are shapes the project drew, each at its
pinned SHA-256 (`SHOWCASE_BODIES`), whose vendor bodies are files of the
folder with their bytes, SHA-256 and triangles, and which draws every file
of the folder; and the showcase's page's document is sound
(`showcase_page()`, below).  `tools/library_showcase.py --check` adds that
the drawn shapes and the scene are the ones the tool writes from the
committed meshes.

## The showcase's page

The user's request of 2026-11-12: at the top of the Library, the original
version, hand-designed and not auto-generated (worded on 2026-11-15 as the
original FlexiTac, hand-designed, pre-agent).  `library/showcase.json`
(`"format": "flexitac-library-showcase/v1"`) is its document, beside
`entries.json`; `library.js` reads both as the page opens, and a Library
without it (or with a document of another format, or whose `id` is an
entry's) is the Library of before.

| Key | What it is |
| --- | --- |
| `id` | `"flexitac-g1"`: the page's address (`./#flexitac-g1`; `library.html#flexitac-g1` until 2026-11-16, which forwards there); no part's, variant's or family's |
| `title`, `label`, `text` | the card's and the page's words, one line each: "FlexiTac on xArm"; "Original FlexiTac · Hand-designed, pre-agent" (the label must say original, hand-designed and pre-agent; it said "Hand-designed, not auto-generated" until 2026-11-15); "Using flexible PCB to make tactile sensors accessible, reliable and standardized." (the flexible PCB technology FlexiTac is built on; the user's choice of 2026-11-15, after "FlexiTac PCBs make ..." said FlexiTac twice) |
| `detail` | the page's line of detail under its line, one line: the sensor's size and fingers ("The original FlexiTac sensor, 12 × 32 taxels at 2 mm, on the xArm gripper's soft fingers."), which the card no longer says (2026-11-15) |
| `sensor` | `{rows, columns, pitch_mm, field_mm}`: the pad (32 x 12 at 2 mm, the art's 23 x 63 mm field), for the picture's placeholder |
| `placed` | the pad's placed record (`vendor/flexitac-v2/umi-finray.placed.json`, "A placed sensor") with `"scene": "scenes/flexitac-g1.json"`: what the 3D view draws |
| `image` | `{exploded, assembled, card: {src, width, height, bytes, sha256}, alt}`: the three pictures, paths relative to `library/` |
| `shot` | what the pictures were shot from: `scene`, `scene_sha256` (the scene file and the rules, as a gripper's record), `art_sha256`, `placed_sha256` (the placed record's canonical JSON), `figure_sha256`, `view_sha256`, and the shoot's `look`, `margins_px` and the stage's `numbers` (held by `showcase_numbers()`: four to the rules' checks, three to the showcase's own bounds, below) |
| `tutorial` | `{label, href}`: the FlexiTac hardware tutorial, for the Gerbers; `href` is the address `vendor/flexitac-v2/NOTICE.md` records |
| `sources` | `[{text, notice}]`: UFACTORY's 3D model by the owner's decision (`../vendor/ufactory-g1/NOTICE.md`), then the FlexiTac V2 design, CC BY-NC 4.0 (`../vendor/flexitac-v2/NOTICE.md`) |
| `about` | what the file is and who writes which key |

- The pictures are 4:5 (1280 x 1600; the card 800 x 1000, the Assembled
  drawing downscaled): the gripper stands upright, and in a 16:10 picture
  four fifths were empty.  `tools/browser/library_shots.py --showcase`
  shoots them from the showcase's own page
  (`?probe=shoot#flexitac-g1`, the view's pane 640 x 800 CSS px
  at a pixel ratio of 2), each drawing checked whole and moved to the
  middle as a sensor's, and writes the files with `placed`, `image` and
  `shot` (nothing when the stage's numbers are not sound, below);
  `--check` shoots again and compares every byte.
- The grid: its first section is the showcase's one card
  (`div.lib-card.lib-showcase#showcase`), as wide as the row: its picture
  (`slot()`'s third kind, `"showcase"`: the card file, loaded at once; a
  picture, as every card: no 3D on the grid) on the left of its label, its
  title, its line and Details from 735 px, the words just beside it (on
  the right of them until 2026-11-15), above them below.  Since the
  user's request of 2026-11-15 ("xarm can be smaller ... make only the image
  that can click to the details ... a button called details") the card is no
  link and does not lift when hovered: its picture (`a.lib-showcase-pic`, a
  fifth of the row within 220 to 300 px, 60 % of a phone's card) and its
  Details (`a.lib-pill.lib-showcase-details`, a grey pill) open the page.
  The picture's link repeats Details', so it is out of the Tab order and
  hidden from assistive technology; Details is the card's first stop, and
  the page's back link came back to it (since 2026-11-15 the window's X,
  Escape and the backdrop focus it).
- Design your own (the user's decisions of 2026-11-15 and 2026-11-16: "在
  flexitac on xarm的details 后面，多一个按钮，generate sensor by yourself with
  cad file", its name chosen: "Design your own"): right after Details on the
  card, `a.lib-pill.lib-design`, a link to Gen by Surface (`gen.html`) in
  the same tab, where the visitor loads their own 3D model; named "Design
  your own sensor in Gen by Surface" for a screen reader.  Details' pill,
  size (36 px, 15 px type), roundness and focus ring in the page's action
  blue with white words, hovered and pressed as Open in Gen by Surface: the
  blue's one other use on the Library (both lead to Gen by Surface; the
  rule "the action blue only on Open in Gen by Surface" has this dated
  exception, held by `test_library`, `library_checks.py`'s `blues()` and
  `theme_checks.py`'s `LIBRARY_BLUE`).  The pills wrap: beside Details at
  1440, 390 and 360 px, under it on the left at 320 px, each its own width.
  The card's Tab order: the picture out of it, Details, then Design your
  own.  It is the card's only: no Design your own on the showcase's page
  or a sensor's.
- The page (in the window over the grid since 2026-11-15, "The details
  window"): the picture in its frame with the Exploded | Assembled control,
  the 3D view drawn over it from `placed`
  (`show({base, id, placed, mode})`, the one dynamic import), opening
  Assembled, the view its card shows; beside it the label, the title, the
  line, the line of detail, a grey pill to the tutorial and the sources
  with their notices.
  No pitch, no Open in Gen by Surface, no generator download.  Its box is
  4:5 at every width (a sensor's is 3:1 in one column, to keep Open in a
  phone's first screen: this page has no such action).
- `tools/library_write.py` `showcase_page(parts, library)` returns
  `(problems, older)`: the file missing or not JSON, its keys, format and
  id; the words (one line each, the label's two claims, never "CAD", no
  host path); the placed record other than the pad's own with the
  showcase's scene, or about another mesh than the UMI finger's; the
  sensor's field other than the art's; a tutorial address the pad's notice
  does not record; sources other than the two notices in order, each a
  file, each text with its words; the vendor's folder named anywhere but
  as that notice; a picture missing, not the bytes named, not a WebP with
  alpha of its size, or a stray file of `showcase/`; and pictures of
  another scene, rules, art or placed record than the files now (stale:
  shoot again), or whose stage's numbers are not sound
  (`showcase_numbers(numbers, rules)`: `visible_min`, `clearance_mm`,
  `stacks_apart_px` and `card_px` at least the rules' checks, as any
  gripper's; `assembled_opaque` below 0.25, `opaque_max` below 0.75 and
  `near_seen` at least 0.25, `SHOWCASE_BOUNDS`, the showcase's own: both
  its fingers are solid, so its own tails behind its finger and the near
  finger's pad behind the near finger count as covered; each bound a
  little past what was measured, 0.19, 0.679 and 0.321, so that a scene
  or a camera that hides more of the pad is refused).  `older`: pictures
  of older figure or view sources, a warning as a sensor's.  `showcase()`
  carries the problems, so `scenes()`, `library_write --check`,
  `tools/library_showcase.py --check` and the site build stop on them;
  `library_write --check` closes a problem of the showcase alone with the
  showcase's own fixes (`SHOWCASE_STALE`), not the scene builder's.
- Order after a change of the scene: `tools/library_showcase.py`,
  `tools/browser/library_shots.py --showcase`, then the three `--check`s.

## The first page

The user's decisions of 2026-11-15 and 2026-11-16 ("我觉得之后可以让lib作为
第一次点击进入时候使用的界面", then "是的 be first page"): the Library is the
site's first page.  `web/index.html` is the Library's page (`library.html`
before) and `web/gen.html` the generator's (`index.html` before): Gen by
Surface at `gen.html`, Rectangular at `gen.html#rect`, a Library sensor at
`gen.html?part=<id>`.  `app.py` serves `/` and `/index.html` the Library and
`/gen.html` the generator, each with its security headers and the header's
counts, and `/library.html` the forwarding page (no header, no counts);
`tools/build_static_site.py` writes the three pages (`PAGES`; the
forwarding page, `FORWARD`, with the site's head tags only) and reads the
request a sensor's fit must be of from `gen.html` (`library_write.INDEX`).

The addresses of before keep working.  `web/forward.js`, the first script
of the Library's `<head>` and of the forwarding page's (the pages' CSP
allows no inline script, hence a file), runs only on those two pages (their
`<meta name="flexitac-page">`, `library` or `forward`) and sends:

- on the Library, a generator's address of before to `gen.html` with the
  same query and hash: a query naming one of `GEN_KEYS` (`part`, `sample`,
  `debug`: `./?part=<id>`, `./?sample=<id>`, `?debug`) or a hash of
  `GEN_HASHES` (`#rect`; `#cad`, CAD mode's name before 2026-10-30, still
  Gen by Surface; the generator's own anchors, its design checks' links
  `#drc-row`, `#drc-column` and `#maskNote`);
- on the forwarding page, everything to `./` with the same query and hash
  (`library.html#<id>` to `./#<id>`, the Library with that window over the
  grid), or a generator's address straight to `gen.html`.

It forwards with `location.replace` (no history entry: Back goes where it
went before), marks `<html data-forward>` and hides the page by
`visibility` (the canvas keeps the body's background, the page's grey or
the dark look's black; Chromium paints nothing of a page that forwards
from `<head>` at all), and `library.js` does nothing on a page so marked.
The Library's own addresses stay: its sensors, parts and families, its
places (`#gripper-<part>`, `#shelf-<part>`, `#shelf-start`, `#grippers`,
`#showcase`) and the showcase's id are none of `GEN_HASHES`, and `?probe`,
the checks' reads on both pages, is the Library's at `./` (the generator's
at `gen.html?probe`), so it alone forwards nothing.  `test_library`'s
`FirstPageTests` run `forward.js` under node on every kind of address and
hold `GEN_KEYS` and `GEN_HASHES` to what the generator reads and the
Library's ids apart from them; `library_checks.py`'s `part_first_page`
(app.py or `--site`) and `static_checks.py`'s `part_first_page` open each
address of `rp.FORWARDS` after an earlier page with its target held 0.6 s:
where it ends, one history entry, Back the earlier page, nothing of the
old address's page painted.

Since the review of 2026-11-16: with the Library already open, an address of
before reached by its hash alone (`./#rect` typed over `./`, an old bookmark
of it or a link to it followed from the Library: a navigation within the
page, which runs no script again) had stayed on the Library, saying "No
sensor in the library is named rect.", where Rectangular had opened before.
`forward.js` listens to the Library's `hashchange` too (registered in
`<head>`, before `library.js`'s, whose `route()` does nothing on a page
marked `data-forward`) and sends it on as at a load, its entry replaced (the
hash's own: Back is the Library where it was).  A Library kept by the
browser's back-forward cache while it was being sent on is shown again at
its `pageshow` and sent on only if its address asks (Chromium keeps no page
it left by `location.replace`; another browser might).  `app.py` sends the
forwarding page as it is by its name (`FORWARD_PAGE`, the site build's
`FORWARD`), not because `fill_github_counts` finds no card in it.  On the
static site the header's star and fork counts are refreshed on both pages by
`web/counts.js` (`backend.js` before, which the Library does not load: the
site's first page had kept the build's counts).  The checks:
`FirstPageTests`' hash and `pageshow` cases, `test_static_site`'s
`CountsTests`, `library_checks.py part_first_page` (a hash over the open
Library, three cases; with `--site` the Library's counts) and
`static_checks.py part_first_page` (the counts at the site's folder).

Every link follows: the Library's header (Rectangular `gen.html#rect`, Gen
by Surface `gen.html`, Library `./`, the current page), the generator's
Library link `./` and step 1's file note `./#<id>`, Open in Gen by Surface
`gen.html?part=<id>`, the showcase's Design your own `gen.html`; the browser
checks open the generator at `rp.GEN_URL` and the Library at the server's
root.  The data files that record where a picture was shot keep the
addresses of their shoots (`shots/manifest.json`'s and
`tools/browser/generator_figure.json`'s `about`), which still forward.

## The UMI shelf's shapes

The user's request of 2026-11-16, of the UMI shelf's 1, 1.5, 2 and 3 mm
cards: "后面这三种不是重复了吗，在第一个umi 1mm点进去，config就可以选择毫米数量；
我在这里更多想要体现umi不同shape我们都可以fit,你现在只有一个shape变体" (the pitch is
chosen on the page; the shelf should show that the UMI finger's shapes
fit), and the shapes then chosen: a concave arc tip, a pointed tip and a
short taper.  The shelf ("UMI Fin-Ray Gripper. Six finger shapes, straight
to pointed.") is one card per finger shape, from blunt to sharp (not by how
much of the face the taper takes, which the point's is less than the
trapezoid's: its review, below):

| Card | Its lines | Its sensors (2 mm pitch) | Its picture and page |
| --- | --- | --- | --- |
| Straight finger | 1 to 3 mm · Pick your pitch | `umi-finray-<p>mm`, 1, 1.5, 2, 3 mm | 2 mm; Pitch |
| Short taper | 5.8 to 21.8 mm · Pick shape and width | `umi-short-{trap,convex}-tip<w>-2mm`: the last 40 mm a trapezoid or a convex arc | the 9.8 mm trapezoid; Shape, Tip width |
| Convex arc tip | 5.8 to 21.8 mm · Pick your tip width | `umi-convex-tip<w>-2mm`: the last 75 mm | 9.8 mm; Tip width |
| Trapezoid tip | 5.8 to 21.8 mm · Pick your tip width | `umi-trap-tip<w>-2mm`: the last 75 mm | 9.8 mm; Tip width |
| Concave arc tip | 5.8 to 21.8 mm · Pick your tip width | `umi-concave-tip<w>-2mm`: the last 75 mm, arcs tangent to the axis at the tip | 9.8 mm; Tip width |
| Pointed tip | 2 mm tip · 2 mm pitch | `umi-pointed-tip2-2mm`: two arcs over the last 50 mm meeting at a 2 mm point | no control |

`<w>` is 21.8, 17.8, 13.8, 9.8 or 5.8 mm: 58 sensors in all (16 new).  The
straight finger's card is a gripper's card (`gripperCard(part, true)`: its
name the part's `card`, its range and "Pick your pitch", its 2 mm page,
no grid id: its place is the shelf); each shape's card (`shapeCard()`) the
picture of its sensor, its title and its two lines, a link to that
sensor's page.  A shape's page shows its card's axes of more than one
choice, and its Tip fact ("Concave arc, 9.8 mm at the tip, over the last
75 mm") is over its card's height.  The pictures show each taper at one
tip width, 9.8 mm, where the profiles differ most on a card's picture (at
13.8 mm the three long ones were hard to tell apart there); the point is a
tangent ogive over 50 mm, the convex profile carried on to a 2 mm point, of
four drawn and shot (ogives over 30, 50 and 75 mm, a 75 mm wedge: the
wedge read as the 5.8 mm trapezoid, the 75 mm ogive as the 5.8 mm convex
arc, the 30 mm one as a rounded nose).

The shelf's cards show their sensor **Assembled** (`library.js`
`SHELF_VIEW`; the lead's review of the same day): from the Exploded home the
fingertip's tapered end is foreshortened at the top of the picture and
partly covered by the exploded layers, so the six shapes looked alike on
their cards; assembled, the contact face's outline is the shape.  Of the
options compared on a sheet (the Exploded card file, the Assembled home, the
Assembled view tilted 20 degrees toward the face) the tilted one read a
little better but is no home of the 3D view, so its picture would not be
the view's (`part_view`) nor held to Gen by Surface's figure
(`--check-generator`); the Assembled home is.  A shelf's card loads the
Assembled picture itself (`shots/<id>.assembled.webp`, 1280 x 800, about
26 KB; there is no Assembled card file), lazily as every card; the grid's
13 pictures come to 315 KB as the page opens (the first screen's budget
1 MB).  No picture changed for it.  The grippers' cards keep their
Exploded card file.  (A shape's page opened Exploded until the review
below, where the tapered end lies under the exploded layers.)

The review of the same day (sound with fixes; each finding reproduced
first) found the shapes still hard to compare, and the shelf now shows
them so:

- **A grid, not a row.**  In the row that scrolled sideways four cards
  were in view at 1440 px (the fifth cut at the window's edge, the sixth
  behind the arrows), three from 768 to 1100 px and one on a phone, so two
  of the three shapes the user asked for were off the screen at every
  width.  The shelf is now the grippers' grid (`.lib-cards`), three to a
  row from 735 px (two rows of three: four to a row would leave the second
  two thirds empty), two below: its cards a third of the row (418 px at
  1440 px, the grippers' 309 px), half on a phone.  The row's scroller,
  its arrows, their scroll listener and resize handler, the rows' snapping
  and the cards' widths for it are gone: nothing on the page scrolls
  sideways.  On a phone a card's name or line may take two balanced lines
  ("Concave / arc tip", "Pick shape / and width"), as a gripper's name
  does; from 735 px each is one line.
- **Framed on the fingertip.**  At the Assembled home the whole finger
  stands at an angle and the taper is a region of about 40 x 60 px of a
  card's picture, foreshortened at its top edge: the convex arc and the
  point, the trapezoid and the concave arc, looked alike.  A shelf's card's
  picture (`tipShot()`, `.lib-shot-tip`) is the same Assembled file scaled
  2.2 times about 41 % across and 3 % down its box, which clips it: the
  tapered end and the sensor on it fill the card, the tip clear of its
  top.  No picture is new and none changed: the card is still the 3D
  view's home, and the first screen's bytes are the same.  At 1440 px the
  picture is drawn 893 px wide from its 1280 (a little soft on a 2x
  screen).  A face-on picture of each card's tip would read more plainly
  still, but is no home of the 3D view (the objection to the tilted view
  above).
- **The heading** keeps its count of shapes whole (`keep()`: at 390 px it
  had broken as "Six / finger shapes,"): "UMI Fin-Ray Gripper. / Six finger
  shapes, / straight to pointed."
- **A shape's page** is titled by its card ("UMI Fin-Ray Gripper, concave
  arc tip"; every tip's part is "UMI Fin-Ray Gripper, tapered tip"), and
  every page of the UMI shelf (the straight finger's pitches too) opens in
  its card's view, Assembled (`showDetail()`: `SHELF_VIEW` where the
  sensor's gripper is shelved), a gripper's Exploded as before.  The
  shots tool sets each view itself, so no picture changed with it.
- **The meshes' outlines** are pinned by the stdlib suite:
  `test_library`'s `test_each_tip_is_cut_by_its_profile` measures each of
  the 26 tips (its binary STL, where a plane at a height cuts it) 1, 5 and
  20 mm above the tip, halfway up the taper and just above it against
  the profile of its kind (`tools/library_tips.py`'s three, copied into
  the test; where the private tool is, its `half_width()`, read from its
  source and run on floats, must equal the copy: the tool needs numpy and
  trimesh and is never imported), within 0.05 mm and centred; the hashes
  alone had let a concave file cut as the convex arc, or two tips' files
  swapped, pass.
- **The point kept.**  Its 50 mm ogive is close to the short convex arc at
  5.8 mm (a sensor of the Short taper's page: 4 mm wider at 5 to 10 mm from
  the tip, 296 against 322 taxels), but the shelf shows the Short taper's
  9.8 mm trapezoid, and framed on its tip the point reads beside the
  convex arc's round nose; a longer point was not cut.

The addresses stay: every sensor's (`#umi-finray-1mm` and the other
pitches whose cards went open their pages), each part's, and the family's
own, `#umi-tapers` (and `gen.html?part=umi-tapers`): its default, the
13.8 mm trapezoid, as before.  All tips stay one family, `umi-tapers`,
whose look the rules' `part_looks` give (so `scenes.json` is unchanged,
and no gripper's stage or picture with it).  `entries.json` stays
`flexitac-library/v1`; its family record is now `{shelf, default, cards}`,
each card `{key, title, h_mm, axes, grid, default, lines}` (its `axes`
Shape and Tip width, its complete grid of their choices to sensor ids;
`library_write.card_record()` checks it and writes `lines`), every sensor
of the family on one card once (`family_record()`); a part's record gains
`card` (the name of a shelved part's own card, else null).  Until
2026-11-16 a family was one card, its `title` ("Tapered tips"), `h_mm`,
`axes`, `grid` and `lines` its own.  The meshes are `tools/library_tips.py`'s
kinds (a profile over a height; `NOTICE.md` names each), its `--check`
cutting the ten of 2026-11-05 again byte for byte; `web/library/` without
its pictures grew from 11.66 to 16.41 MB (`test_library`'s budget 17 MB),
the pictures to 4.74 MB.  The checks: `test_library`'s `FamilyTests` and
`test_the_umi_shelf_is_one_card_per_shape` (`SHELF_VIEW`, `shelf_cards()`, since
its review the grid, the frame, the heading and the page's title),
`test_each_tip_is_cut_by_its_profile`, the `UMI_SHAPES` and
`UMI_SHAPES_REVIEW` mutants, `library_checks.py` `part_layout` (since the
review: three to a row and two, every card inside the content's edges,
nothing scrolling, each Tabbed to whole in the window), `part_grid`,
`part_family` (the pages' titles and first view), `part_pictures` (the
frame, its box clipping it), `part_first_screen` and `part_window`.

## The pictures' manifest

`library/shots/manifest.json` stays `flexitac-library-shots/v1`.  A record
shot from the Library's 3D view adds:

```json
{"view_sha256": "...",
 "art": {"path": "art/widowx-250-2mm.json.gz", "bytes": 6386, "sha256": "...", "json_sha256": "...", "build_id": "..."},
 "stage": {"scene": "scenes/widowx-250.json", "scene_sha256": "...",
           "numbers": {"jaw_gap_mm": 55.6, "near_seen": 1.0, "stacks_apart_px": 100.5}}}
```

- `view_sha256`: `tools/library_write.py` `view_sha256()`, the hash of the
  Library view's own modules (`VIEW_SOURCES`), as `figure_sha256` is of the
  figure's.
- `art`: the art file shot with (`sha256` of the file, `json_sha256` of its
  document's canonical JSON).
- `stage`, for a part of `scenes.json` only: `scene_sha256()` of the scene
  file and the rules, and the stage's measured numbers (the shot's checks).
- `part_look_sha256`, only for a part without a scene that the rules give
  a look ("The looks").

The numbers are exactly these (measured by the stage with `?probe=shoot`;
distances capped at 12 mm), each kept by the rule of `rules.checks` beside
it (`tools/library_write.py` `stage_problems()`):

| Number | What it is | Its rule |
| --- | --- | --- |
| `jaw_gap_mm` | the gap between the fingers' faces, G | a positive number |
| `step_mm`, `drape_step_mm` | the explode step drawn and the drape's | - |
| `face_tilt_deg` | the face normal's tilt off the plane across the approach axis | - |
| `visible_min` | the least visible share of any exploding layer (the sensor finger's stack) in Exploded | at least `layer_visible_min` |
| `opaque_max` | the most of a layer the bodies and an unlisted finger cover in Exploded (every layer drawn there, both stacks) | less than `opaque_cover_max` |
| `assembled_opaque` | the same for stack 1's top FPC in Assembled (the bodies and any finger not see-through there: the near finger, see-through in Assembled too, does not count) | less than `opaque_cover_max` |
| `ghost_cover` | the most of a layer a see-through finger veils in Exploded (with one stack exploding: the near finger's veil of its own assembled stack); `null` with no see-through finger | at least `ghost_cover_min` when `see_through` is not empty, else `null` |
| `near_seen` | the least share of the still stack's bottom FPC (its face toward the camera) that nothing opaque and no other layer hides, over Exploded and Assembled; `null` exactly when the mate's stack explodes | at least `near_seen_min` when `"mate"` is not in `explode_stacks`, else `null` |
| `clearance_mm` | `{bodies, other_finger, stacks}`: the least distances from the field over both modes (`stacks`: the exploded stack's fields to the other finger's assembled stack, Exploded) | `bodies` and `other_finger` at least `clearance_min_mm`; `stacks` at least `stacks_apart_min_g` x G and `stacks_apart_min_mm` |
| `stacks_apart_px` | the exploded stack's silhouette to the other stack's on screen, Exploded, px of the measure | at least `stacks_apart_min_px` |
| `card_px` | stack 1's top FPC's box in the card, `[w, h]` px | its smaller side at least `card_min_px` |
| `band_css` | `{contain, cover}`: that box in the 390 px phone band, CSS px | - (reported) |

## entries.json

Each variant gains `view`: `null` (the page shows the picture only) or
`{"art": "art/<id>.json.gz", "scene": "scenes/<part>.json" or null}`,
written by `tools/library_write.py` for a sensor whose record is current.
The alt text of a sensor whose record has `stage` is its label and the
scene's `picture`; of any other, its label and "on the part".

## A placed sensor

The user's request of 2026-11-12: the top of the Library shows the
original, hand-designed FlexiTac sensor (FlexiTac V2, 12 x 32 taxels at
2 mm), labelled as hand-designed, not auto-generated.  No fit of the
generator places that pad and no build of the engine made its boards, so
the 3D view takes it from a **placed record** in place of a variant:
`createLibraryView(host, options).show({base, id, placed, mode})`, with
`placed` the parsed record and `base` the Library's folder as for a
variant.  `variant` and `part` are not given; `id` is whatever the page
calls the drawing (the probe state's `id`), and the state's `build_id` is
`null`.  Every sensor of `entries.json` is drawn as before: the stack
builder's `mapper` argument below is the placed stack's alone
(`tests/test_showcase.py` reads that from the sources, and the pictures of
the generated sensors are byte for byte the ones they were).

`vendor/flexitac-v2/umi-finray.placed.json`
(`"format": "flexitac-library-placed/v1"`, `drape.js` `PLACED_FORMAT`):

| Key | What it is |
| --- | --- |
| `id`, `about` | the record's name and its words (how the real pad is mounted) |
| `sensor` | the art's `id` (`"flexitac-v2"`) |
| `art` | the art's file, relative to `library/` as a variant's `view.art` (`"../vendor/flexitac-v2/art.json.gz"`) |
| `mesh` | `{file, sha256, unit}`: the part's STL, relative to `library/` (`"../vendor/umi/UMI-Soft-Gripper-Finger.stl"`), and its unit (one of `surface/mesh.py` `UNIT_SCALES_MM`: `show()` refuses a record of another) |
| `frame` | `"the mesh's file axes, mm"`: the face's vectors are in it |
| `face` | `{origin, x, y}`: the field's centre on the part's flat face and the boards' x and y there, seen from outside (unit vectors at right angles; the outward normal is x cross y).  On the UMI finger: the middle of its 25.8 mm width, 37 mm from the fingertip, y toward the tip |
| `wrap` | `{side: "left" or "right", radius_mm}`: the side edge the sheet rolls over (left: toward -x, the viewer's left with y up) and how far off the part it bends |
| `scene` | `null`, or a scene's path as a variant's `view.scene`: its `part_mesh_sha256` must be the record's `mesh.sha256`.  With a scene the part is drawn in the scene's `part_look`; without one as Gen by Surface draws it (the rules' `part_looks` go by a part's id or family, which a record has not, and are not read for it) |

The art (`vendor/flexitac-v2/art.json.gz`) is a `flexitac-library-art/v1`
document as above with `"id": "flexitac-v2"` and `"build_id": null`.
`tools/flexitac_v2.py` reads the pad's two Gerber ZIPs (a folder given on
its command line; their SHA-256s and the result's are pinned, `--check`)
into `vendor/flexitac-v2/geometry.json`: each FPC's outline, its slots and
window, electrodes, traces, gold fingers, coverlay openings and
stiffeners.  `tools/browser/flexitac_v2_art.py` gives those two boards, in
the engine's layout mapping (`flexitac_v2.engine_boards`), to the engine's
SVG writer and the generator's page (`"fpc:board-art"`, the Photo look), as
the shots tool does for a build, so the pad is drawn exactly as a
generated board is; the slots and the window are the boards' `cutouts`.
Of the stiffeners the boards carry only the 0.2 mm ones under the two gold
ends (`flexitac_v2.DRAWN_STIFFENER_MIN_MM`): the writer and the Photo look
paint a stiffener as a connector's, opaque and dark, and the pad's 0.1 mm
ones (the strip under the Top FPC's traces below the field, the patches at
the A's corners) are thin polyimide through which the real pad stays
amber; `geometry.json` keeps them all.  The art is made for the 3D view,
which cuts the slots out of the sheets itself (`outline.cutouts`).  Shown
flat, a board's copper side (`front`) would lack its slots: the writer
draws the coverlay's openings after the cut-outs, and this pad's openings
span the whole field (the Top FPC's all 22 slots and 30 of the Bottom
FPC's 31 are painted over; the `back` documents show every one).  A page
that shows this art flat must draw the cut-outs last.
`column` is the Top FPC (12 sense lines along the finger, `physical_side`
`"bottom"`: against the finger, its copper outward) and `row` the Bottom
FPC (32 drive lines across it, `"top"`: the outer layer, turned over), as
the pad is mounted and as a generated sensor's boards are named.  The
folder's `NOTICE.md` states the design's licence (CC BY-NC 4.0, Columbia
University): these files are not Apache-2.0.

How `drape.js` lays it (pure functions, as the rest of the module):

- `wrapMapper(placed, vertices)` is `chartMapper`'s kind of map,
  `{xyz(uv) -> {xyz, on}, outward(uv)}`, with `uv` in mm on the face from
  its origin.  On the face it is the face's plane to the last bit.  Past
  the wrap's side edge (the part's farthest corner that way) each height
  of the sheet rolls round the part's section in the plane across y,
  keeping its length: a quarter turn of `radius_mm`, down the side
  `radius_mm` off it as far as the **fold line**, a quarter turn about it,
  then across the back.  The fold line is the part's own section seen
  from that side: the concave majorant of its corners' depth behind the
  face against their height (on the fin-ray finger its slanted, curved
  back, bridging the dip under the screw boss as a taut strap does).  So
  the A's two arms and the Top FPC's tail cross the finger's side face as
  level straps and the gold ends lie behind the finger, 66 to 81 mm from
  its tip.  Up to the fold line the sheet is laid rigidly; on the back a
  slanted fold line shears it.  It also gives `width_mm` (the part's width
  across the fold), `wrap` (`{edge_mm, radius_mm, fold}`) and `lifted(h)`:
  the same map of the sheet held `h` mm off the face, its tail coming back
  round the fold line by `h`.
- `buildStack({..., mapper})`: with a mapper (never for a generated
  sensor) the stack's `explode` is `"lift"`: each layer's sheet is the
  mapper's `lifted(layer x step)`, the step `EXPLODE_SHARE` of `width_mm`
  (14.19 mm on the finger): the layers stand apart along the face's
  normal and their tails hang from them, never through the part, nothing
  stretched.  Its sheets carry `liftedNormals` (their normals so exploded;
  `onpart.js` draws an exploded sheet with them), and the stack
  `respace(step)`, which lays the exploded sheets again for another step:
  `library_stage.js` calls it where it spaces a gripper's stack between
  the jaws.
- `placedStack({placed, vertices, arts, boards, partBox})` is the stack of
  a placed record: the field's centre on the face's origin, the boards'
  axes the face's.  It sets `film_seen` where a board is cut out over the
  field (the pad's slots): `onpart.js` then draws the film's face in
  Assembled too, the dark stripes of the real pad.

What changed in the shared modules for it, all behind keys only a placed
stack has: `onpart.js` (the film's face shown assembled for `film_seen`;
a sheet's normal buffer the mode's where it has `liftedNormals`, and its
edge band then across those normals when exploded, `bandOf`'s `lifted`),
`library_stage.js` (two lines: `stack.respace(step)` where a stack has it,
and the still stack's film face shown for `film_seen`),
`library_view.js` (`show()`'s `placed`).  `tools/library_write.py` knows
nothing of placed records: the showcase is no entry, and its files live
outside `library/`.

The showcase's page draws it on the gripper ("The showcase's page" above).
For the pad alone on its finger, `tools/browser/showcase_checks.py`
serves a probe of the server's origin that mounts the view as that
page does (the Library's style sheets, a sensor page's `.lib-stage`,
`show({base: "library/", id, placed, mode})`), checks the wrap
(`tools/browser/wrap_checks.js`, which `tests/test_showcase.py` runs under
node where there is one: the face, the folds, the lift, the exploded
sheets' normals against the lifted sheet's own, a part thinner than the
bend) and shoots it Exploded and Assembled from five sides in both
schemes; its `part_page` checks the showcase's card and page on the
Library itself (on a built static site too, `--url`).  What the pad's
drawing leaves out of the real assembly: the laminating sheets, the
polyimide tape over the fingertip and the silkscreen; the extender boards
and stubs of the flat cables, the second finger and the gripper are the
showcase's scene's.

## The page's reads (checks only)

With `?probe` in the address, `library.js` keeps `<pre id="libViewState"
hidden>`, a JSON `{state, note, id, build_id, mode, drawn_mode, moved,
gripper, offset, buffer, ms, stage}`: `state` one of `off`, `loading`,
`drawn`, `failed`, `unavailable` and `lost`; `offset` the drawing's move to
the middle at its home in device pixels; `stage` the stage's numbers and,
as `stage.looks`, what of the scene's looks is drawn (`{bodies: the looks'
names, part: the part's look or null, smooth_deg, part_points: how many
points the part's corners share at that angle}`).  With
`?probe=shoot` the view also leaves the drawing where the figure frames it
(the shots tool moves the picture to the middle, by whole pixels) and the
stage measures its numbers.  A visitor's page does neither.

## Staleness

- A record whose `art` is missing is pictured without a 3D view (its
  `view` null) while `tools/library_write.py` `VIEW_REQUIRED` is false; the
  shoot that writes every sensor's art sets it true (the shoot of
  2026-11-06 did), and from then on it is a problem.
- An art file that is not the manifest's bytes, or of another build than
  the variant's, is a problem; so is a gripper's `scene_sha256` other than
  its scene's and rules', a UMI record with `stage`, recorded numbers
  that break the rules' `checks`, or a `part_look_sha256` other than the
  rules' look of the part now (none where they give none).
- A `view_sha256` other than the served modules' is a warning (re-shoot),
  as an older `figure_sha256` is.
- `tools/library_write.py --check`, the site build and `tests/` refuse the
  problems.

## The checks

`tools/library_write.py` (stdlib; its public helpers are the shots tool's
and the tests' too):

- `pictures(variants, library, figure, view, require_view)` returns
  `(images, problems, older, views)`: each record's pictures as before, its
  art (`art_problems()`: the file, the record's bytes and SHA-256, a gzip of
  JSON, the record's `json_sha256`, an art document of the sensor and the
  variant's build, at `ART_PX_PER_MM` and `ART_MAX_PX`, the two boards with
  their outlines), a file of `art/` no record names, a gripper's stage
  (`staging()`: its part's scene, `scene_sha256()` of the scene and the
  rules now, `stage_problems()`), a stage of a part with no scene (the UMI
  finger and its tapered tips: `gripper_parts()` are the others), and with
  `require_view` (default `VIEW_REQUIRED`) a record without its art or a
  gripper's without its stage.  `views` holds `view_record(id, scene)` for
  each current record with its art (and a gripper's stage); a picture
  without one, while `require_view` is false, is a warning
  (`view_note()`), as an older `view_sha256` or `figure_sha256` is
  (`older_note()`).  A record with its stage takes its alt text from its
  scene's `picture` (`image_record(id, label, picture)`).
- `scenes(parts, library)` returns `(index, problems)`: `scenes.json`'s
  keys, format and rules (every number; each camera's `tilt_deg` 45 to 70,
  `elevation_deg` 15 to 45, `front` 1 or -1; `explode_stacks`, `"sensor"`
  and at most `"mate"`, distinct; `see_through_modes`, distinct, within the
  camera modes, at least one); every gripper part with its
  scene at `scenes/<part>.json` and no other part with one; each scene's
  keys, format, part, `part_mesh_sha256`, frame, a unit approach (to
  1e-9), an opening with `0 < q_mm <= limit_mm`, rigid matrices (their
  upper 3 x 3 orthonormal to 1e-6), the mate's `kind` its determinant's
  sign and, with `part` false, a body of the mate's finger; each body's
  file in `bodies/<part>/` with its bytes, SHA-256 and triangles (a binary
  STL), its finger, a row of `NOTICE.md` with its SHA-256, an open licence
  (Apache-2.0, MIT, BSD-3-Clause) and its text (`OWN_BODIES`, the rail,
  none; a `drawn-` shape whose header says it is the project's); the looks
  (each name a look of the scene, each look used and in range, the part's
  without a clear coat; the rules' `part_looks` naming only parts without
  a scene or their families, their `part_pad` a tint with them);
  `see_through` and `picture`; the overrides
  within their bounds
  with "reason" in `about`; a file of `scenes/` or `bodies/` no scene
  names; `DENIED_SHA256` over every body and every hash `NOTICE.md` names,
  `DENIED_NAME` over every body's file; and no text of the private
  importer's inputs (`asset/`, `outputs/`, `gripper_recipes`, the word
  recipe, a part's id with underscores, an absolute path) in a scene,
  `scenes.json` or a body's row.
- `run()`: `--check` refuses the pictures' and the scenes' problems
  (since the shoot of 2026-11-06, `VIEW_REQUIRED`, a picture with no 3D
  view among them; while it is false, a warning) and says how many sensors
  have one; writing reports them and writes each sensor's `view`.

`tools/build_static_site.py` stops on the same problems (the scenes of the
parts it builds and the index's, the showcase's among them), on a `view` in
`entries.json` other than `pictures()`' and warns as the writer does (of
the showcase's pictures of older sources too); `BUILD.json`'s library
record counts the sensors `viewed` and names the `showcase`.
