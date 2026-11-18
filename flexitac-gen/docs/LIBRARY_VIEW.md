# The Library's 3D view: the formats

The user's requests of 2026-11-05: for the grippers that are not UMI
fingers (seven then; eight since the Robotiq 2F-85 of 2026-11-16, "The
Robotiq 2F-85" below, and more since, each with its section below), the Library shows the **whole gripper** with a sensor on both
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
  sensor's pad; since 2026-11-16 `part_homes` `{part or family: {approach,
  explode_share}}`, the grippers' homes for them (see "Parts without a
  scene").

`library/scenes/<part>.json` (`"format": "flexitac-library-scene/v1"`):

| Key | What it is |
| --- | --- |
| `part` | the part id |
| `part_mesh_sha256` | the part's mesh, `parts.json`'s `mesh.sha256` |
| `about` | the scene's sources (each at its commit), the opening, how the mate was found; an override's reason |
| `frame` | `"the part's file axes, mm"`: every matrix and vector below is in it |
| `approach` | a unit vector: the fingers' approach axis (the camera's up) |
| `opening` | `{q_mm, limit_mm, joint, source}`: each finger's stroke, fully open (the LeFlexiTac's rotary jaw 39 degrees of its 100, its `about` says why: "The LeFlexiTac" below; the YUBI Gripper's rotary fingers 11 of the 38.5 degrees from its assembly's pose, 2026-11-17: its `about` says why, "The YUBI Gripper" below) |
| `mate` | `{kind: "turned" or "mirror", matrix, part}`: `matrix` takes the sensor finger onto the other one (`kind` is its determinant's sign); `part` true draws the part's own mesh there, false a body whose `finger` is `"mate"` |
| `bodies` | `[{mesh: "bodies/<part>/<name>.stl", sha256, bytes, triangles, matrix, finger}]`: `matrix` takes the body's file into the part's frame; `finger` is `"sensor"`, `"mate"` or `null` (or, since 2026-11-17, `"extra<k>"`, k 1 to the scene's `extra_fingers`: a further finger's own body, opaque, which that finger's stack is not held apart from; a hand's links); optional `look`: a name of `looks` (without it the body is the part's grey) |
| `see_through` | a subset of `["sensor", "mate"]`: the fingers drawn see-through, in the rules' `see_through_modes` (the near finger, `["mate"]`, on every gripper: the user's decision of 2026-11-06) |
| `picture` | the words after the label in the pictures' alt text (`"on both fingers of the open gripper"`) |
| `camera` | optional: `{exploded or assembled: {tilt_deg, elevation_deg, front}}` over the rules' (tilt 45 to 70, elevation 15 to 45), its reason in `about` |
| `explode` | optional: `{gap_share}` over the rules' (0.25 to 0.45), its reason in `about` |
| `looks` | optional: `{name: look}`, the scene's looks (below); each one used by a body or by `part_look` |
| `part_look` | optional: a name of `looks`, the look of the part (the sensor finger's own mesh) and of its mate where the mate is the part; no clear coat |
| `smooth_deg` | optional: the crease angle of smooth normals, 1 to 90 degrees (35 where a scene has looks); absent: flat facets |
| `extra_fingers` | optional (2026-11-17, a hand): 1 to 4 `{kind, matrix}`, each `matrix` taking the sensor finger onto a further finger (`kind` its determinant's sign, as the mate's); the stage draws the part there, opaque in both modes, with a still copy of the stack, and measures it ("Hands: a sensor on every finger") |
| `checks` | optional (2026-11-17): `{card_min_px}` over the rules' (12 to 20), its reason in `about`, in a hand's scene alone (one with `extra_fingers`); no other check may be overridden |

Every matrix is a 4 x 4 array of rows, applied to column vectors, its last
row `[0, 0, 0, 1]`, its upper 3 x 3 orthonormal.

## The Robotiq 2F-85

The user's request of 2026-11-16 ("是不是可以加一个 robotiq的gripper card",
pointing at their own `asset/2F85_Opened.stl`) and, asked which model to
use, their decision: "Menagerie model".  The Library's eighth gripper is
MuJoCo Menagerie's `robotiq_2f85`, at the commit of the other Menagerie
grippers (`f3b6013629c7b94f8ee93fd977b161fa8350f9bc`).  This lifts the
decision of 2026-11-05 ("Robotiq 2F-85, Robotiq 3F and xArm stay off the
public site", made because Robotiq's own CAD files are Robotiq's) for that
one model only.

- The source and its licence.  The folder's own `LICENSE` is the
  BSD-2-Clause text, "Copyright (c) 2013, ROS-Industrial"
  (`library/licenses/mujoco_menagerie-robotiq_2f85.txt`, byte for byte);
  its README says "This model is released under a BSD-2-Clause License" and
  that the model is derived from the publicly available URDF description,
  ros-industrial/robotiq's `robotiq_2f_85_gripper_visualization`, whose
  `package.xml` names the BSD licence and a Robotiq maintainer; its
  CHANGELOG has one entry, the initial release of 2022-09-07.  The meshes
  are binary STL in millimetres (`2f85.xml` scales them by 0.001).  So the
  meshes are redistributable under a permissive licence, and
  `tools/library_write.py`'s `OPEN_LICENCES` takes BSD-2-Clause.
- The deny-list.  `DENIED_NAME` refuses "robotiq" unless "2F-85" follows it
  (`robotiq(?![ _-]?2f-?85)`: 'Robotiq 2F-85', `robotiq-2f-85`,
  `robotiq_2f85` pass; the 3F's `ROBOTIQ_AGS-001-XXXX.stl`, 'Robotiq
  3-Finger', `robotiq_3f`, a 2F-140 or a Hand-E do not), and since this day
  the user's own file by its name too (`2f-?85[ _-]?opened`); its SHA-256
  and the 3F's stay in `DENIED_SHA256`.  `test_library`'s
  `test_the_menagerie_robotiq_alone_carries_its_name` holds both sides.
  Since the review of 2026-11-16 the name is held too: with "robotiq" taken
  before "2F-85", a copy of the user's file under another 80-byte header
  (another SHA-256) and a 2F-85 name passed both the name and the hash, and
  its triangles are not hashed (the file is never read).  So a 3D model
  anywhere under `web/` whose path names the 2F-85 (`robotiq[ _-]?2f-?85`;
  STL, OBJ, PLY, 3MF, glTF or STEP) is one of `MENAGERIE_2F85_MODELS`, the
  pad and the 14 bodies at their SHA-256, or `showcase()`'s walk of `web/`
  refuses it (so `library_write.py --check` and the site build);
  `test_a_model_under_the_2f85_name_is_one_the_library_pins` holds it.  A
  body built anew from the Menagerie's files is pinned anew there.  The
  part's id is `robotiq-2f-85`, the product's own name, so the recipe-key
  check (a part's id with underscores, `robotiq_2f_85`) does not meet the
  Menagerie folder's name `robotiq_2f85`, which the scene's `about` and
  `NOTICE.md` name at its commit; the multi-gripper video's private
  `robotiq_2f85` recipe (the user's file) is never read for it: the part is
  in `parts.json` by hand.
- The part (`meshes/robotiq-2f-85.stl`): the right finger's
  `silicone_pad.stl`, unchanged (300 facets, 22 x 1.6 x 37.5 mm, its tip's
  corners rounded 5 mm), the pad the gripper grips with.  Its contact face is
  the plane y = -6.6 mm, outward -y, 22 x 37.5 mm, symmetric across x = 0:
  the selection grows flat from facet 232 (`surface.select.nearest_facet`'s
  direction is the view ray, so the face's own facet is found looking along
  +y; facet 14, found along -y, is the back face against the fingertip's
  plate, which the first shoot refused: the jaws' gap -89.1 mm), and the
  base point `[0, -6.6, 0]`, the middle of the face's edge toward the palm,
  where the tails leave.  Four pitches as on four other grippers, 1, 1.5, 2
  and 3 mm at fill 0.5 (every gripper's fill since 2026-11-06): 32 x 21
  lines at 1 mm (the 32 lines' cap; 662 taxels), 24 x 14 (330), 18 x 10
  (178) and 12 x 7 (82), every field centred on the symmetric face, the
  tails 20.0, 17.1, 17.9 and 19.1 mm, centred and ending together; the
  design checks clean.  On the card "1 to 3 mm" and "Pick your pitch".
- The scene (`tools/library_scenes.py` `robotiq()`): the model at qpos 0,
  every joint at 0, each driver at the open end of its range 0..0.8 rad,
  the silicone pads' faces 85.4 mm apart (`opening` `q_mm` 42.7, each face
  from the mid-plane; the product's stroke is 85 mm).  The other finger is
  `2f85.xml`'s left one, the same links turned 180 degrees about the
  gripper's axis (`quat 0 0 0 1`): `mate` `turned`, the part drawn there, so
  its sensor is the same board.  The bodies: `base_mount` and `base` (no
  finger) and on each finger its four-bar linkage, `driver`, `coupler`,
  `spring_link`, `follower` and `pad` (the fingertip's plate under the
  silicone), `finger` `sensor` or `mate`, so the near finger's whole linkage
  is see-through.  Each decimated within 0.5 mm (base 34248 to 7186
  triangles, 0.44 mm; base_mount 21834 to 1790), 0.58 MB in all (579,288
  bytes; 0.61 MB, 608,676 bytes, as published, after the split and the
  drawn pins: the review of 2026-11-16).  The
  approach is +z of the pad's file and its face lies along it
  (`face_tilt_deg` 0); the scene overrides no camera, so the rules' homes are
  its homes, as every gripper's.
- The look (`tools/library_looks/robotiq-2f-85.json`), drawn after Robotiq's
  studio photos of the 2F-85 (robotiq.com's 2F-85 and 2F-140 page:
  `2F_Adaptive_Grippers_White.png`, the open grippers side by side, and
  `2F-84 2F-140 montage.png`, seen from below): the housing and coupling a
  satin black (`housing-black`, the base anodised black with less metal and
  more of the room: the photo's #202020 to #585858; with the base look the
  housing's lower faces read 16 at the 2nd percentile, darker than the film,
  with these 25, median 55), the palm block between the fingers
  bead-blasted aluminium with its four screws polished steel (the base's
  connected components, picked by box and triangle count), the links black
  anodised, the driver inside them aluminium (the model's own grey), the
  fingertip (`follower.stl` but its two pins, and the pad's plate) bright
  machined aluminium (`tip-aluminium`: #b8b9ba to #d1d2d3 in the photo, with
  sharp dark bands), the follower's and the inner link's far pins polished
  steel, the silicone pad (the part) black rubber.  The project draws the
  pins' heads in the outer link's pivots and a dark cap with a pin's head
  in the inner link's bore at the housing, plain cylinders where the model
  leaves the holes open (`drawn-coupler-pins.stl`, `drawn-spring-link-caps.stl`,
  `drawn-spring-link-pins.stl`): the photos show a bright pin at every
  pivot.  Not modelled: the ROBOTIQ lettering, the coupling's status light,
  the outer links' bright machined edges, the links' face screws.  The
  edges are the photo's most visible metal (a silver bevel round each outer
  link), but the model has no chamfer to pick (the review of 2026-11-16,
  measured on Menagerie's `coupler.stl` at f3b6013: 2302 mm² of faces within
  10 degrees of the link's ±x, 2474 mm² of walls at 80 to 90 degrees, 32
  triangles, 159 mm², between), so a pick by normal finds no bevel; only a
  band the project drew round each face could show it, the user's to ask.
- The shoot (2026-11-16, the four sensors): `jaw_gap_mm` 84.9,
  `visible_min` 0.86 to 0.92, `opaque_max` and `assembled_opaque` 0,
  `near_seen` 1, `ghost_cover` 0.98 to 0.99, the clearances past the reach
  (> 12 mm), `stacks_apart_px` 136 to 146, `card_px` 26 to 27 x 88 to 89 px;
  the drawing 593 px of the picture's 1280 wide Exploded and 538 px
  Assembled (the grippers' 570 to 840 Exploded), its height bound as theirs
  (margins of 49 to 50 px of 800).
- The card: the parts' order is the multi-gripper video's, in which the
  Robotiq 2F-85 is second, after the UMI finger, so its card is the first of
  the grippers' grid; the heading reads "Grippers. Eight, each fitted at
  four pitches." (the page writes it from the data), the grid two full rows
  of four (four rows of two on a phone).  Its page is every gripper's: the
  Pitch switch, Exploded | Assembled, the site build's Gerber ZIPs, the part
  STL, the licence and the source ("mujoco_menagerie at f3b6013").
- What it moved: 62 sensors (58), eight gripper cards and 14 in the grid,
  `web/library/` 17.31 MB (its budget 18 MB, 17 before), its bodies 3.07 MB
  (2.46 MB before, the 2F-85's 0.61 MB as published; budget 3.1 MB, 1.2 %
  to spare, 2.5 before), its art 0.61 MB (budget 650 kB, 600 before),
  the pictures 4.83 MB (budget 8 MB).

### The Galaxea R1 Lite (2026-11-17)

The user's request of 2026-11-17 (more gripper cards, each on a line of its
own): the Galaxea R1 Lite's G1 parallel gripper, last in the Grippers grid on
its line (the lead orders the cards at the merge), the heading "Grippers.
Eight, each fitted at four pitches."

- Source: GalaxeaManipSim (`https://github.com/OpenGalaxea/GalaxeaManipSim`)
  at `abe7f5161eeaa150e6eaffdf443af5df7f23f356`, its newest commit
  (2025-08-18), `galaxea_sim/assets/r1_lite/`.  Its `LICENSE` is the Apache
  License 2.0, Copyright 2025 Galaxea (`licenses/galaxeamanipsim.txt`, byte
  for byte); the README's badge and last section say MIT, but the licence
  file is the grant, and NOTICE.md names it.  `tools/library_scenes.py`
  fetches the URDF, the gripper link and the licence at that commit, each
  pinned by its SHA-256.  Since the review of 2026-11-17 the repository's
  `NOTICE` too (added with the licence by `b72f4b0`; 1287 bytes): portions
  of the project derive from MIT-licensed software, Copyright (c) 2025
  Tianxing Chen (RoboTwin, which the README credits), which is what the
  README's MIT refers to; it most likely covers code, not the R1 Lite's
  meshes, but it is carried byte for byte as
  `licenses/galaxeamanipsim-NOTICE.txt` (Apache-2.0 section 4(d)), pinned
  beside the licence and named by the finger's row and the source's
  paragraph in NOTICE.md.
- The part: `meshes/left_gripper_finger_link1.STL` unchanged (metres, 5128
  facets: the finger with its carriage), the real finger rather than
  HandUMI's printed replica of its tip, since its contact face is flat and
  whole (70 mm long, 26.2 mm wide at its base to 8.9 mm at the tip, 1048.2 mm2
  selected, its normal 0.45 degrees off the jaw axis): nothing to register.
- The scene: `robot.urdf`'s prismatic `left_gripper_finger_joint1` (0 to
  0.05 m) and `joint2` (-0.05 to 0), each at 50 mm, the faces 100 mm apart.
  `left_gripper_finger_link2` is `link1` turned 180 degrees about the
  approach axis (0.00002 mm), so `mate` is `turned` with the part's own mesh
  and the same board.  The body is `left_gripper_link.STL`, decimated (2708
  to 1542 triangles, 0.43 mm) and shared out by
  `tools/library_looks/galaxea-r1-lite.json` into its motor can (by its
  box, 592 triangles) and the plate the fingers' rails run on; no wrist
  link (the gripper reads whole without it).
- The looks, after Galaxea's own pictures (the G1 Gripper's and the R1
  Lite's product pictures on galaxea-dynamics.com, the G1's drawings in the
  A1 hardware guide; not committed): the can and the plate black anodised
  aluminium (the base `anodized-black`), the fingers a grained matt grey
  (`#6e7074`, metalness 0, roughness 0.8), lighter than the body as in the
  photos.  Not drawn: the fingers' and the plate's screws.  No page or
  guide of Galaxea's read gives the fingers' material (the A1 hardware
  guide gives the G1's sizes, stroke and rated force), so none is claimed
  (the review of 2026-11-17: 'a printed nylon's' had been).
- The carriage (the review of 2026-11-17): the finger's mesh holds, beside
  the finger, its carriage (a block standing on the plate at the finger's
  root, a bar in the notch at the base of the face, a fillet between them)
  and its rack under the plate's slot, which wore the finger's grey: a grey
  block at the root and two light strips along the black plate.  Galaxea's
  G1 picture shows the carriage black.  On the sensor's finger
  `bodies/galaxea-r1-lite/drawn-carriage-sensor.stl` (five plain boxes,
  `carriage-black`, the base `anodized-black`) holds all of the carriage
  and the rack wherever the slot through the plate's 3 mm top shows it,
  0.06 mm proud of what it covers; the rack's box fills the slot's opening,
  its top 1.5 mm under the plate's top.  The other finger is always
  see-through, so it keeps its ghost as before: black boxes there only
  doubled it (a lighter block on the plate), and a box just under the
  plate's top showed through it in that ghost.  The stage's numbers are the
  same as without the boxes (the 2 mm sensor's clearances 7.8, 12 and
  57.5 mm, ghost_cover 0.99).
- The homes: the scene overrides no camera.  `library_checks.py
  part_aligned` reads its 2 mm sensor at elevation 30, 65 (Exploded) and 57
  (Assembled) degrees off the face's normal, front 1, left 0.87 and 0.78,
  upright 0.87 (the face's tilt 0), the Franka Hand's and the WidowX 250's
  numbers.
- The sensors: the face grown flat from a seed facing the other finger; the
  border (`uv` -15 to 15 by -40 to 17.5 mm) stops 0.4 mm short of the
  carriage's notch at the face's base and reaches past the face elsewhere,
  so the taxels lie on the face beyond the notch and the tails leave across
  the border's base edge, over the notch, toward the plate.  1, 1.5, 2 and
  3 mm at fill 0.5 ("Four pitches, 1 to 3 mm."): 32 x 16 (362 taxels), 32 x
  12 (280), 27 x 11 (183), 18 x 7 (82), each a symmetric face's centred
  field, the tails centred and ending together, a clean build; reader none
  (one tail pin per line).
- The card's title is the maker's product name, "Galaxea R1 Lite": one line
  at 1440 px, two on a phone (as "MakerMods Metal Arm").

### The Seeed reBot DevArm (2026-11-17)

The user's request of 2026-11-17 (grippers to add, each on its own line;
this one `fpc-int-n-rebot`): the reBot DevArm's two-finger parallel
gripper, the eighth gripper card, last in the grid.

- Source and licence.  mujoco_menagerie `f3b6013`, `seeed_rebot_devarm/`,
  unchanged since its first release (2026-08-09): its `LICENSE` is the MIT
  License, Copyright (c) 2026 Seeed Studio
  (`licenses/mujoco_menagerie-seeed_rebot_devarm.txt`, byte for byte).  The
  chain, as the review of 2026-11-17 traced it:
  - Seeed's CAD and URDF, in its hardware repository
    `Seeed-Projects/reBot-DevArm` (`eda479d`, `Rebot_Arm_description/RS/`):
    "CC BY-SA NC" for its first five months, CERN-OHL-W-2.0 since its
    `LICENSE` of 2026-05-11 (commit `b738018`, commercial use allowed).  A
    reseller's CC BY-NC-SA 4.0 is these terms before that day.
  - `Seeed-Projects/reBot-Isaacsim` (`51aa876`): `urdf/00-arm-rs_asm-v3/`,
    from whose URDF the menagerie's README derives the model, and `urdf/RS/`,
    whose README gives the hardware repository as its source and whose
    `UPSTREAM_LICENSE` (2026-11-06, by a member of Seeed's organisation) is
    the CERN-OHL-W-2.0 text.  `cnc7`, `cnc_left` and `pla7_green` are one
    git blob in the hardware repository, both Isaacsim folders and the
    menagerie; the menagerie's `pla_left` is Seeed's finger meshed coarser
    (5144 facets to 14 702: the same extents, its face and pockets the same
    areas).  Isaacsim's top-level `LICENSE` is the menagerie's MIT text (one
    blob), added on 2026-07-30 by an outside contributor's pull request (#17,
    "Seeed Studio releases the reBot DevArm assets under the MIT License")
    that Seeed's open-source maintainer merged.
  - The menagerie (MIT).  Isaacsim's `mjcf/rebot_devarm/` is a copy of the
    menagerie's folder (its README: vendored at `da76818`), so its files
    matching the menagerie's byte for byte say nothing of where the meshes
    came from (this block said so before the review).

  The files are taken here under MIT, as the menagerie publishes them, and
  `NOTICE.md` records Seeed's CERN-OHL-W-2.0 on the same meshes; since the
  merge of 2026-11-17 (the lead's decision) that text, reBot-DevArm's
  `LICENSE` at `eda479d`, ships beside the MIT one as
  `licenses/seeed-rebot_devarm.txt`, which the part's row names (`tools/library_scenes.py`
  fetches it, pinned, and writes it with the bodies' texts).  Neither licence is
  non-commercial.
- The part: `gripper_left`'s `pla_left.STL` (the printed finger on its
  MGN9 carriage, four screws), in metres.  Its contact face, the file's
  plane z = 0, is a triangle 38.4 mm wide at its base and 64.8 mm to its
  tip with two pockets 1.85 mm deep (a slot 9.4 x 30.4 mm up its middle,
  one 30.4 x 9.4 mm across its base): as a selection they are holes the
  field may not cross, which leaves no field.  They seat the gripper's
  silicone grip pads (30 x 9 x 2 mm in Seeed's bill of materials, about
  0.15 mm proud of the face); with the pads out a laminated sensor bridges
  them, as the Franka pad's grooves, so the part is the finger with each
  pocket's floor and walls taken out and its rim capped flush
  (`tools/library_scenes.py` `rebot_finger()`, the other 5028 triangles the
  upstream ones in order, in mm: `meshes/seeed-rebot.stl`, 5068 facets).
  The face is then one flat triangle of 1440.8 mm2, symmetric (deviation
  0), grown flat from facet 152, its base edge the tails' (y 22.87).
- The sensors: 1, 1.5, 2 and 3 mm at fill 0.5 (the page's default; at 1 mm
  0.65 builds clean too, 32 x 20): 32 x 22, 32 x 20, 32 x 19 and 21 x 11
  taxels, each field centred on the face's axis, the tails centred and
  ending together (46.6, 29.5, 15.1 and 16.0 mm), clean builds.
- The scene: `joint_left` at its upper limit, 50 mm (the faces 100.15 mm
  apart, the stage's `jaw_gap_mm` 99.647 between the boards); the other
  finger `gripper_right`, which is `gripper_left` turned 180 degrees about
  the approach axis to 0.000 mm (`pla_right` and `cnc_right`), so the mate
  is the part turned, the same board.  The bodies: `cnc7` (the bracket's
  plate and the MGN9 rail, shared out by look), `pla7_green` (the printed
  rail supports and end stops) and `cnc_left` on both fingers (the slider
  extension and its rack), 196 KB.  `motor_7`, the RS-00 actuator, keeps
  20 629 of its 26 480 triangles within 0.5 mm (1.03 MB, where the bodies
  had 44 KB of their 2.5 MB left), so it is drawn by the project as plain
  shapes to its sizes on `cnc7`'s frame (a can 57 mm across, its 63 mm
  base ring, its two plug housings: `drawn-motor-*.stl`, 20 KB); `link6`,
  the arm's wrist flange behind it, is not drawn.
- The look (`tools/library_looks/seeed-rebot.json`), after Seeed's photos
  (the wiki's B601-RS guides) and the hardware's bill of materials: the
  fingers black ABS print (`abs-black`), the supports lime PLA
  (`pla-lime`, `#c2d446`), the plate and the slider extensions bead-blasted
  aluminium (`alu-blasted`), the rail ground steel (`rail-steel`), the
  actuator a matte black can (`motor-black`, the Dex1's numbers).
- The homes: `library_checks.py part_aligned` reads elevation 30, tilt 65
  (Exploded) and 57 (Assembled), front 1, left 0.87 and 0.78, upright 0.87,
  the WidowX 250's numbers.  The stage's: clearance 9.3 to 9.6 mm from the
  bodies and 12 from the other finger, nothing opaque over a layer,
  `near_seen` 1, the card's sensor 42 x 146 px at 2 mm.
- Budgets: the line raises `test_library`'s bodies' to 2.7 MB, the art's to
  0.65 MB and `web/library/`'s to 17.25 MB (the reBot's 216 KB, 47 KB and
  0.74 MB: 2.67 MB, 0.62 MB and 17.15 MB); the merge sets the sums.

### The xArm Gripper (2026-11-17)

The user's word of 2026-11-17 ("xarm原装夹爪", the xArm's own gripper) adds
an eighth gripper card, last in the grid: UFACTORY's xArm Gripper as MuJoCo
Menagerie's `ufactory_xarm7` draws it (at `f3b6013`, BSD-3-Clause,
Copyright (c) 2018, UFACTORY Inc., its `LICENSE` read; its README: derived
from `xarm_ros`' public URDF).  It is a generated sensor on the stock
finger; the showcase (UFACTORY's G1 file with the UMI fingers and the
hand-designed pad, `scenes/flexitac-g1.json`) is untouched.

- Its names.  `tools/library_write.py` `DENIED_NAME` refused every xarm and
  ufactory name; it lets this card's alone pass: the part's id and its
  files' and sensors' (`ufactory-xarm`, `ufactory-xarm-<pitch>mm`, then the
  end, `/` or one of the extensions the Library writes: `.stl`, `.json`,
  `.json.gz`, `.exploded.webp`, `.assembled.webp`, `.exploded.card.webp`),
  its title (the whole name `xArm Gripper`) and Menagerie's folder
  (`ufactory_xarm7`, then `/` in its sources' addresses or `.txt` ending its
  licence text's name).  Every other name stays refused (e.g. `UFACTORY
  xArm Gripper`, `xarm-gripper`, `xArm Gripper G1`, `ufactory-xarm.g1.stl`,
  `ufactory-g1`); `test_library` holds both sides.  The Robotiq names are
  the list's first line alone, so the Robotiq card's narrowing of that line
  joins this one at the merge.
- The part is `left_finger.stl` byte for byte (metres, 4852 facets), the
  finger bar with its pad.  The pad's face is flat, 29.5 x 37.5 mm with
  3 mm corners (1098 mm2), symmetric both ways; the tails leave its edge
  toward the housing.  Four pitches, as on the grippers of its size: 1,
  1.5, 2 and 3 mm (32 x 28, 24 x 19, 18 x 14 and 12 x 9 taxels at fill
  0.5), each centred with its tails ending together.
- Its title is "xArm Gripper", its maker UFACTORY (on its page): "UFACTORY
  xArm Gripper, 1.5 mm" is 29 characters, one over `LABEL_MAX`, and 4 mm in
  place of 1.5 mm would leave the face 7 x 9 taxels at its coarsest.
- The scene: `hand.xml`'s parallel four-bar linkage at its drivers' 0 of
  0..0.85 rad, fully open, where every body is a pure translation; each
  finger's stroke 43.64 mm (its origin's travel to the range's other end),
  the pads' faces 88.9 mm apart (the boards' 88.4, `jaw_gap_mm`).  The
  bodies are `base_link.stl` (the housing with its flange, screws, chassis
  and side connector) and each side's outer and inner knuckle, decimated within
  0.5 mm (0.61 MB); the other finger is the part turned 180 degrees about
  the approach axis (`right_finger.stl` is so: median 0.00 mm, about 1.0 mm
  at most, away from the pad, whose face matches), with the same board.
  The arm's last link is not drawn.
- Its look (`tools/library_looks/ufactory-xarm.json`), after UFACTORY's
  manual cover, shop renders and photos of the gripper on an xArm: the
  glossy white shell (`#eceef0` with 1.6 of the studio: its broad face reads
  `#dbdfe2` at the Exploded home, `#b8b9bd` under the base look), the black
  anodised links and finger (`#2e2e31`, satin), the steel pins, the dark
  Phillips screws, the black flange and chassis.  Not drawn: the hexagon
  logo (the model has none).  The showcase draws the same housing (the G1
  file) with numbers of its own, tuned on 2026-11-12/13 beside the
  hand-designed pad (its shell `#e2e4e6` at 0.7 of the studio, its screws
  matte black, its pins `#a0a2a4` at roughness 0.7); this card's follow the
  photo notes of the stock unit (`claude/specs/library-look/notes/photos-xarm-g1.md`:
  pins `#C9CACD` at 0.22, links `#2E2E31`), and side by side the two read
  close.  The model is the first xArm Gripper (G1); UFACTORY's current one
  is the G2, another design.
- Its pad light grey (the user's word of 2026-11-17, "xarm grey pad"): the
  finger and its pad are one file, the part, drawn in the finger's black,
  so on each finger a prism of the project's own
  (`bodies/ufactory-xarm/drawn-pad-sensor.stl`, `drawn-pad-mate.stl`, the
  look file's `drawn`; credited in `NOTICE.md`) covers the model's pad in
  `pad-grey` (`#a2a3a6`, rubber's roughness 0.92, 1.2 of the studio): the
  pad's own outline and thickness (its connected component, the part's
  facets 2900 to 2991: a 29.5 x 37.5 mm rectangle with 3 mm round corners,
  3 mm thick, 2 mm of it proud of the plate) 0.02 mm larger on every side,
  the other finger's under the mate's matrix and ghosted with it.  Its face
  reads `#aaabaf` at the Exploded home, after UFACTORY's shop renders
  (`#a7a7a7` lit, `#bababa` from the front) and the rose photo (the pads'
  edges `#9ea0a7` by a `#e1e0e5` wall).  The part's file, the fits, the
  build ids and the stage's code are unchanged; the four sensors' pictures
  were shot again (`--only`), no other picture changed, and the two bodies
  more take the housing's share of the frame's samples, so the drawing is
  under 1 % smaller in the frame (margins 2 to 3 px wider).  A look on the
  part's own facets (a scene's runs of them drawn in groups) was tried
  first and set aside: it changes `library_stage.js`, one of every
  picture's view sources, so every sensor's and the showcase's pictures
  would have to be shot again.
- At the grippers' homes (`library_checks.py` `part_aligned`: elevation 30,
  tilt 65 and 57, front 1, the face to the left 0.87 and 0.78, upright
  0.87, the WidowX 250's numbers; its face along the approach,
  `face_tilt_deg` 0).  The 2 mm sensor's stage: `visible_min` 0.733,
  `clearance_mm` 7.4 / 12 / 51, `stacks_apart_px` 130, `near_seen` 1,
  `card_px` 35 x 91 (with the grey pads; 0.732 and 132 before).
- The review of 2026-11-17 (sound-with-fixes): the deny-list's test holds no
  Robotiq 2F-85 name now (the Robotiq line lets them pass) and its mutants
  are anchored on its xArm lines alone; after the card's id or the model
  folder only the Library's extensions (`ufactory-xarm.g1.stl` refused; a
  file under `bodies/ufactory-xarm/` passes by name, and the G1's known
  pieces are refused there by their SHA-256 and the showcase's copy check); the
  other finger's distance measured again (0.998 mm over every vertex,
  triangle centre and 100 000 surface samples both ways: 0.79 was 3000
  samples' most); NOTICE's source line with its commit and without the
  chat's words; the mutants under `S/`.

### The Rainbow RB-Y1 (2026-11-17)

The user's request of 2026-11-17 (the Rainbow RB-Y1 among that day's
grippers), the eighth gripper, its card last in the grid on its line (the
merge of that day's lines orders the cards).  Its gripper is the
menagerie's 1.2 model's since the lead's decision of the same day (the
line's review found the v1.3 model's drawn much shorter than the real
gripper and the user said "you decide"; why, below).

- Sources: MuJoCo Menagerie at `f3b6013`, `rainbow_robotics_rby1` (Apache
  License 2.0, Copyright 2024 Rainbow Robotics; its `LICENSE` read whole
  and committed byte for byte), its 1.2 model `rby1m_1.2.xml` (last
  changed upstream at `ac6b2b0`, 2026-05-18, before the pin): the gripper
  `EE_BODY.obj` (at `43b5e62`, the same day), the finger `EE_FINGER_1.obj`
  and its pad `EE_FINGER_0.obj` (both models' own), each pinned by its
  SHA-256 in `tools/library_scenes.py`.  The folder's files came to the
  menagerie at `bef9f83` (pull request 238, 2026-05-08); its README says
  its models are derived from Rainbow Robotics' public resources, the
  RB-Y1 URDF of `rby1-sdk` among them, whose gripper is `EE_BODY` and
  `EE_FINGER` too.  No video recipe holds this gripper, so
  `library_scenes.py` also writes its Library mesh (`library_mesh()`: the
  pad in millimetres, its 76 facets as the file has them,
  `meshes/rainbow-rby1.stl`).
- The part is the pad, the finger's contact face: a flat face of 32 mm at
  the gripper tapering to 20 mm at the tip (rounded to 16.5 mm), 60 mm
  long and symmetric about its middle.  The selection is that face but its
  top 10 mm strip (facets 34 and 35), which runs to 1.5 mm under the
  gripper's rail block (0.5 mm under the v1.3 gripper's rail plate):
  without it the field stands 11.2 to 11.6 mm clear of the gripper and the
  tails leave the face's straight 32 mm edge there.  Four pitches at fill
  0.5: 1 mm 32 x 26 (25.5 x 31.5 mm, the 32 lines' cap), 1.5 mm 32 x 20,
  2 mm 25 x 15 (29 x 49 mm), 3 mm 16 x 9; each centred, its tails centred
  and ending together.  The pad is the same file in both models, so the
  fits and their art did not change with the gripper.
- The pose: each finger at its range's open end (50 mm out from the
  middle, the two coupled one to one by the model's equality), the pads'
  faces 100 mm apart (the stage's `jaw_gap_mm` 99.5; 93.5 on the v1.3
  gripper); the gripper where the model's `EE_BODY_R` places it, its rail
  block 1 mm above the fingers' frames (1.5 mm above the pads' roots).
  The mate is the same finger turned 180 degrees about the wrist's axis,
  with the same board, where the model opens `ee_finger_r2`'s frame to:
  the model leaves that frame unturned (the wrist's, as `ee_finger_r1`'s),
  which would face its pad away and, the fingers 13 mm thick from 3 mm off
  the middle, pass it through the other finger as they close.  Rainbow
  Robotics' own URDF turns it so (`rby1-sdk` at `300a585`,
  `models/rby1a/urdf/model.urdf`: `gripper_finger_r2` at `rpy 0 0 pi`, 53
  mm out at its open end), as the v1.3 model does; the builder checks the
  model's frame and place and stops otherwise.  The wrist's last link is
  not drawn, and nothing stands in for it: `EE_BODY` closes its own top (a
  boss 56 mm across, its middle recessed 8 mm, on a block 65 mm square; a
  ray from above anywhere within the housing meets it).  The plain ring
  the project drew on the v1.3 gripper, whose top was open
  (`drawn-top-ring.stl` and its note in `NOTICE.md`), is gone.
- The look, from Rainbow Robotics' photos of the RB-Y1 (which do not say
  which version of the gripper they show): the housing, its rail block and
  the fingers black anodised (a satin black with soft highlights); the pad
  black rubber (the base look `rubber-black`, matte as the model's own
  pad), as every photo shows the fingers black, their inner faces too (the
  review of 2026-11-17: it was the model's light grey, a bright slab on the
  card); no lettering.  At the grippers' homes the stage reads
  `face_tilt_deg` 0, `visible_min` 0.863, `opaque_max` 0, `near_seen` 1 and
  `ghost_cover` 0.984 on the 2 mm sensor, its card's sensor 40 x 138 px
  (38 x 133 on the v1.3 gripper).
- Why the 1.2 gripper.  Rainbow Robotics' own drawing of the RB-Y1's
  standard gripper (its developer documentation, Options, Gripper: 126 x
  55 x 133 mm, 92.2 mm from the top of its 88 mm flange to the fingers'
  root, fingers of 60.5 mm, a stroke of 100 mm) against the two models'
  grippers, measured on their files in mm:

  | | drawing | 1.2 `EE_BODY` | v1.3 `EE_GR_TF` |
  | --- | --- | --- | --- |
  | length along the stroke | 126 | 126 | 120 |
  | width across, at the rail | 55 | 55 | 65 |
  | the fingers' root to the top | 92.2 | 73 | 54 (66.4 to the bracket in its ring) |
  | the pads' faces apart, open | 100 | 100 | 94 |

  Drawn at one scale from the front and the side (above the fingers'
  root), `EE_BODY` is the drawing's gripper up to its housing's top (the
  rail block, the housing 86 mm wide up to about 62 mm, the drawing's
  about 63), and its 65 mm block and 56 mm boss stand where the drawing's
  neck, 65 mm wide, does, up to 73 mm where the neck goes to about 79; the
  drawing's 88 mm flange on that neck (about 79 to 92.2 mm) is not in it,
  19 mm in all with the neck's last 6 (the model draws an 88 mm cylinder
  there as the wrist's, `LINK_13_1_V1.1.obj`, from 73 mm up, which the
  Library leaves out).  The v1.3 gripper's housing stands 54 mm, its rail
  plate 65 mm across and its stroke 94 mm.  The photos' black stack
  between the fingers and the white wrist (about 160 mm) is taller than
  either, the wrist's ring among it.
- The size: the RB-Y1's bodies are 104 368 bytes, `ee_body.stl` 92 484
  (1 848 triangles within 0.39 mm of the 3 500 of `EE_BODY.obj`) and
  `ee_finger_1.stl` 11 884.  With the v1.3 gripper they were the Library's
  heaviest, 1 294 852 bytes (`ee_gr_tf.stl` 1 270 084, 25 400 triangles of
  a model of 676 parts, and the drawn ring 12 884).  The bodies come to
  2.56 MB with them (the budget 2.6 MB; 3.8 MB was asked with the v1.3
  gripper) and `web/library/` without its pictures to 16.72 MB, within its
  17 MB again (17.91 MB with the v1.3 gripper).

The OpenArm (2026-11-17, the user's request of that day: Enactic's OpenArm
1.0 gripper, the grippers' eighth scene, in the same format; the card is
titled "OpenArm 1.0" since its review the same day: OpenArm 2.0's default
end effector is another gripper, its `pinch_gripper`).  Its model,
openarm_description at `81fe647` (Apache-2.0, Enactic, Inc.), draws in
Collada: the scene builder reads `<triangles>` under each node's
`<matrix>` (any other primitive or transform refused, and since the review
a unit other than the metre or an up axis other than `Z_UP`: `dae_frame()`)
and may take of a file its materials (the finger's carriage block, `mat_0.009` of
`finger.dae`) or its components wholly above a height (of `link7.dae` the
gripper's motor, above z 590 mm, not the arm's wrist bracket); each such
body's change says so in its `NOTICE.md` row and note.  The bodies sit
where the generated v1 URDF of the right arm places them, the jaws at
`finger_joint1/2`'s 44 mm, 86 mm apart at the field (Enactic gives 88 mm
between the jaws).  The sensor's face (the user's correction of
2026-11-17, "openarm你选的面不对，我们可以只选取finger tip那个小圆弧三角的部分")
is the small flat rounded pad at the fingertip alone, where the jaws
meet: 170 mm2, 21.9 mm across its straight root edge and 11.2 mm to its
rounded end, symmetric, the tails across the root edge toward the mount;
not the curved cradle behind it (1644 mm2, the first build's) nor the
30-degree ramp between them.  A small face: 1 to 2.5 mm (3 mm would leave
3 rows of 14 taxels).  The part is HandUMI's
replica of the OpenArm finger (`OpenArmv1/OpenArm-left.stl`, unchanged),
registered on `finger.dae`'s finger (`OPENARM_TIP_ON_FINGER`: its vertices
beyond the mount within 0.001 mm median, 0.10 mm p90, 0.68 mm max): the same
surface as one closed printable mesh, where `finger.dae` joins the finger
to its carriage.  The other finger is the URDF's right one, the same finger
turned half a turn about the approach axis (`mate.kind` `turned`), so it
carries the same board.  The three meshes are byte for byte the same at
openarm_description's newest commit of 2026-11-16 (`8dbfcc9`; `link7.dae`
moved, unchanged); its v1 URDF changed after `81fe647` (its pull request
129 centres the V1 joint frames, keeping the parts' placement, by its
title), and the scene keeps the pinned one.

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
  brightness (since the grippers' homes of 2026-11-16, the Assembled
  home 57 degrees off the face's normal where it had been 35, the tinted
  pixels' median in the 3D view reads hue 43.7, value 0.35, the amber
  board's under them hue 32.9, value 0.66: `library_checks.py`
  `PAD_LOOK` holds the amber at 0.6, 0.7 before).  The photo's traces are
  stronger than the tint leaves
  them (its copper bright between dark stripes of film; here the
  board's art, whose copper reads a little darker than its polyimide,
  at a third of its contrast).  Gen by
  Surface draws no pad: its figure is its own, and `--check-generator`
  holds the tint to the Assembled sheets (below).
- `part_homes` (the user's request of 2026-11-16, of the UMI shelf's
  cards: "你这样是重新选择了一个角度，用户需要再完成一次gripper方向的空间转换，这样不好；
  你做成和这个finger一样的空间角度，而且可以做成exploded"): `{part or family:
  {approach, explode_share}}`, the part drawn at the grippers' homes.
  `approach` is the fingers' approach axis in the part's file axes (a unit
  vector, as a scene's `approach`: the UMI finger's length toward its tip,
  `[0, 0, -1]`, its tips' too); the stage (`library_stage.js` `aim()`)
  makes it the camera's up and sets each mode's direction by the rules'
  `camera` about the face's normal with `direction()`, a gripper's own:
  `elevation_deg` (30) above the plane across the approach axis, turned
  from the front (`front` 1) toward the face until it is `tilt_deg` off its
  normal (65 Exploded, 57 Assembled).  So the finger stands as a gripper's
  far finger stands on the cards: upright, its contact face turned to the
  picture's left, its stack exploded to the left, seen from the front-left
  and 30 degrees above.  The grippers' common convention, read from the
  eight scenes (the Rainbow RB-Y1's of 2026-11-17 among them, its face 0
  degrees off): none overrides the rules' camera, every approach is a unit
  axis of its file, and their faces lie 0 to 7.7 degrees off the plane
  along the approach axis (`face_tilt_deg`; the OpenArm's of 2026-11-17,
  the eighth, 0 on its fingertip pad); the UMI face lies along it
  (0).  `explode_share` (0.3 to 1.2; 0.8) spaces its stack that share of the
  boards' narrower side a layer along the normal (a gripper's stack is
  spaced by its jaws' gap, which a lone finger has not): at Gen by
  Surface's 0.55 (18.05 mm a layer on the 2 mm finger, 14.6 to 19.1 mm
  across the 30 sensors; the probe's `drape_step_mm`) the bottom FPC lay
  against the finger's face, seen nearly edge-on from this side, its
  outline lost in the finger's; at 0.8 (26.26 mm on the 2 mm finger, 21.2
  to 27.7 mm across them; `step_mm`) each sheet stands on the ground alone,
  and the drawing is about 550 px of the picture's 1280 wide where it was
  470 (the grippers' 570 to 840), its height bound as theirs (margins of
  48 to 51 px of 800, theirs 49 to 52).  The drawing is framed as a gripper's
  (`prepare()`'s points: the whole part and the sheets, `frameView` at
  the home), the film's lamp and the studio's roll set at the camera as a
  gripper's stack 1 has them (the figure's own lamp is aimed from its own
  home).  The probe's `stage` then reports `{home, up, camera, approach,
  explode_share, step_mm, drape_step_mm, numbers: null}` (no numbers: the
  stage measures a gripper's scene alone; a gripper's report gains `up`).
  Gen by Surface keeps its own figure (`drape.js`, `onpart.js` untouched).
- `cad/library_view.js` reads the rules for such a part and hands the
  stage `{look, smooth_deg, pad}` and its home `{approach, explode_share,
  camera}`; the stage draws the part's own material in it for that
  drawing, the pad's tint where there is one, and at the grippers' homes
  where the rules give one.  Without a rule the part is Gen by Surface's
  grey at its figure's homes.
- The rules are hashed into every gripper's `scene_sha256`, and a record
  of such a part keeps `part_look_sha256`
  (`tools/library_write.py` `part_look_sha256(part_look(...))`, the pad's
  tint among it where the rules give one, and since 2026-11-16 its home,
  `home`, with the rules' camera): a changed look, tint or home makes the
  pictures stale.

Until the look, the Library's pictures of these sensors were Gen by
Surface's figure byte for byte, and `library_shots.py --check-generator`
held the two together.  They differ now by design, so the check holds what
still holds (for each sensor of a part without a scene, in a browser,
writing nothing):

Since 2026-11-16 the Library's pictures of these parts are at the
grippers' homes (`part_homes`, above) and no longer at the figure's angle
(tilt 57 / spin -20 Exploded, the left figure's, the user's decision of
2026-11-05 for the generator, which Gen by Surface keeps): the check now
holds that the Library's view is the figure with three things added, the
look, the tint and the home, each served away to see the figure again.

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
2. The Library's view with the rules' looks and homes served away is that
   figure, pixel for pixel: without a look and a home, the Library's view
   of such a part is Gen by Surface's (the same part, sheets, explode,
   lights, camera and frame).
3. The Library's view as the rules are gives the committed pictures, byte
   for byte (at the grippers' homes).
4. The look touches the part alone, at the figure's homes (the rules' home
   served away: the figure is the witness only there).  The view is shot
   once more with the
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
   `pad_differences()`, `pad_problems()`), at the figure's homes too: the
   view with the tint against the view without it has the same alpha at every
   pixel, changes nothing in Exploded, and in Assembled changes only
   pixels the part's colour does not reach (by the fourth comparison's
   witness in the other colour), `PAD_SHARE_MIN` (0.05) of the drawing at
   least.
6. The fourth and the fifth again at the grippers' homes, the pictures'
   own, which a visitor sees (the review of 2026-11-16: held at the
   figure's homes alone, a fault of the look, the film's lamp, the studio's
   roll or the tint in `aim()`'s branch alone passed both): the witness is
   the part drawn grey there (the rules served with the part's home alone,
   no look: `served_scenes()` of `{"home": ...}`); the view in its look
   without the tint and in the other colour, both at that home, against it
   (`view_differences()`: the same alpha, every pixel the part's colour
   does not reach the witness's), and the view as the rules are (the
   pictures') against the look without the tint (`pad_differences()`).  On
   the 2 mm finger the part's pixels are 52 % of the Exploded drawing and
   56 % of the Assembled one there, the pad's 23 % of the Assembled one.
   Five drawings a sensor then; nine with the home (the look and its tint
   at the figure's homes besides the pictures', and the witness, the look
   alone and the other colour at the grippers' homes): about 25 s a sensor
   on this host.

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
- **Its camera is the rules'** (no `camera` override since the user's
  request of 2026-11-16, "最上面的xarm gripper的空间朝向也要跟下面的这些家爪都对齐":
  the showcase seen as every gripper's card sees its gripper): the body at
  the bottom, the fingers upright, the far finger's pad turned to the left
  with its layers exploded into the jaws' gap, from the front 30 degrees up,
  65 degrees off the pad's normal Exploded and 57 Assembled; with this part
  (the left finger) the front is the logo's side of the shell, the side the
  owner's photo was taken from, and the straps cross the fingers' side faces
  on the far side, seen through the fins' windows as in that photo.  From
  2026-11-12 to 2026-11-16 its camera was its own, an override from the side
  of the shell's face without the logo (Assembled 60 degrees off the
  normal and 20 up, Exploded 70 and 40, `front` -1), which showed the
  straps and turned the gripper another way than the cards below it.  The
  logo is not drawn.
- **The near finger is see-through** (`see_through` `["mate"]`, since the
  review of 2026-11-16), as every gripper's near finger is (the user's
  decision of 2026-11-06, "靠近外面的finger透明"), in both modes at the rules'
  `ghost_opacity`: from the grippers' homes the near finger's own pad faces
  away from the camera, and the builder's solid finger hid it whole
  (`near_seen` 0.002, `opaque_max` 0.996), so the card showed FlexiTac on
  one finger where its alt text says both; seen through it, the near pad's
  field and its straps show (`near_seen` 0.891, held to the rules'
  `near_seen_min` as a gripper's).  Under the showcase's own camera of
  2026-11-12 to 2026-11-16 both fingers were drawn solid: from the other
  side the near finger hid nothing of either pad.
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

- The pictures are 4:5 (1280 x 1600; the card 800 x 1000, the Exploded
  drawing downscaled, as every gripper's card, since the user's decision of
  2026-11-16, "Switch to exploded"; the Assembled one before): the gripper
  stands upright, and in a 16:10 picture four fifths were empty.  `tools/browser/library_shots.py --showcase`
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
  Exploded, the view its card shows (`SHOWCASE_VIEW`, as a gripper's page
  opens; Assembled until 2026-11-16); beside it the label, the title, the
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
  gripper's; `assembled_opaque` below 0.65, `SHOWCASE_BOUNDS`, the
  showcase's own: both its fingers are solid, so the far finger's straps
  on its side face away from the camera and its tails behind it count as
  covered, its field on the face toward the camera seen whole; a little
  past what was measured at the grippers' homes, 0.613, so that a scene or
  a camera that hides more of the pad is refused.  `opaque_max` (0.996)
  and `near_seen` (0.002) measure the near finger's pad, which faces away
  from the camera at those homes behind its solid finger: reported, not
  bounded.  From the showcase's own camera, until 2026-11-16, they had been
  0.19, 0.679 and 0.321, held below 0.25, below 0.75 and at least 0.25).  `older`: pictures
  of older figure or view sources, a warning as a sensor's.  `showcase()`
  carries the problems, so `scenes()`, `library_write --check`,
  `tools/library_showcase.py --check` and the site build stop on them;
  `library_write --check` closes a problem of the showcase alone with the
  showcase's own fixes (`SHOWCASE_STALE`), not the scene builder's.
- Order after a change of the scene: `tools/library_showcase.py`,
  `tools/browser/library_shots.py --showcase`, then the three `--check`s.

## Ordering and the reading boards

The user's request of 2026-11-17 ("这个页面，把instruction里面的fpc gerber也
都放到这边可以直接download；另外 所有的card加上一条：ordering and
fabrication：放上instruction link；reading board download：你可以把instruction
里面对应gerber也放在这下载，小于32x16的sensor用32x16的board，小于32x32大于16
的，用32x32的board") and his answers to the plan ("copy into site, reading
board可以打包成一个zip：gerber，bom，pick and place", tail C: the sensors'
tails stay one pin per line and the page only names the board, "gen也加入
reading board").

- The files are served, not linked (the page's policy stays
  `default-src 'self'`): the original pad's two FPC Gerber ZIPs, unchanged,
  in `vendor/flexitac-v2/`, and one ZIP per reading board in
  `vendor/flexitac-reader/`, each its Gerber ZIP, BOM and pick-and-place
  file unchanged (`FlexiTac_reading_board_32x16.zip`: `Gerber_16_32.zip`
  and its two CSVs; `FlexiTac_reading_board_32x32.zip`: `Gerber_32_32.zip`,
  `BOM_32_32.xlsx`, `PickAndPlace_32_32.xlsx`), all CC BY-NC 4.0 material
  of Columbia University (each folder's `NOTICE.md`; the 32 x 16 board's
  Gerbers are EasyEDA v6.5.51 exports, the 32 x 32 board's EasyEDA Pro
  v3.2.109 ones, as their headers say: the notice had said EasyEDA Pro for
  both until the review of 2026-11-17).
  `tools/flexitac_downloads.py` pins every byte and re-derives each bundle;
  the site build checks the published copy.
- `boards.js` (`window.FlexiTacBoards`, a classic script both pages load
  before their own) holds the guide's address, the files and the rule: a
  sensor of at most 32 lines on its larger side and 16 on its smaller (rows
  and columns, either way round) takes the 32 x 16 board, one of at most 32
  on each the 32 x 32 board, a larger one none.  It is computed in the page
  from a sensor's rows and columns: `entries.json` names no board, so a new
  card has its rows with no work.  On 2026-11-17, 42 of the 58 sensors take
  the 32 x 16 board and 16 the 32 x 32; none is larger.
- A sensor's window: its Reader row (`none (one tail pin per line)`) is
  gone; under its facts two rows in a list of their own (`dl.lib-order`):
  "Ordering and fabrication", the FlexiTac fabrication guide in a new tab,
  and "Reading board", `32 × 16 · ZIP, 50 kB · CC BY-NC 4.0` (the size,
  the bundle's download under its own name, named in full to a screen
  reader, "Reading board 32 × 16, ZIP, 50 kB", and its notice in a new
  tab; `none (more than 32 lines)` past 32).  A no-break space before each
  dot, so a line may end with one but never start with one (at 320 to
  326 px the second dot had started a line); the three pieces never split.
  From 1200 px the facts and the two rows are one table (the review of
  2026-11-17): one labels' column (`.lib-specs` a grid, both lists and the
  facts' rows its subgrids, the column as wide as "Ordering and
  fabrication", at most 40 %), no hairline between them, a row's gap after
  Build, so every value starts at one x (at 1440 px the values had sat at
  828 and 940 px, two tables) and a plain sensor's window fits 1440 x 900
  again: the two rows for the Reader row make it one row taller, 747 px
  of 756 (718 before 2026-11-17; with the rows under their own hairline,
  768, it scrolled by 12).  Of the 58 windows 32 fit at 1440 x 900 (33
  before; the pointed tip's, 735 px before, takes 785 now), and the tapered
  tips' Tip fact ("Concave arc, 13.8 mm at the tip, over the last 75 mm")
  takes two lines from 1200 px, those windows scrolling already.  Below
  1200 px the facts keep their 72 px labels (each fact one line at 900 px)
  and the two rows their own column under a hairline (at 900 px the long
  label two lines).
- The showcase's window: under its tutorial the pad's own two ZIPs in the
  sensors' grey download pills, "Top FPC Gerber ZIP" and "Bottom FPC
  Gerber ZIP", on one line, then its reading board in the sensors' own row
  between two hairlines ("Reading board", `32 × 16 · ZIP, 50 kB · CC BY-NC
  4.0`: its 12 x 32 pad by the rule, from `showcase.json`'s `sensor`), the
  board's licence and notice in the row; its sources line is as before
  2026-11-17.  (The review of 2026-11-17: a third pill, "Reading board
  32 × 16", had wrapped alone under the two at 1440 px, the pills reading
  1-2-1; the three need 681 px, the column has 630, and shorter words
  would not have fitted at 1280 px either.)  `showcase.json` was unchanged
  on the line; since the user's word of 2026-11-17 (the merge) its tutorial
  is "FlexiTac fabrication guide" at the guide's ordering section, the
  address the sensors' rows and Gen's step 3 link (the pad's notice records
  it).
- Gen's step 3 (Gen by Surface and Rectangular share it): the same two rows
  over the Ordering notes, under their hairline (`gen.html`
  `dl#orderBoard`); the Ordering notes' own line linking the guide (2026-11-06)
  went, the row links it (the guide once in the step).  The board is the one
  the design's tails plug into (`boards.js` `tailsBoard`, the review of
  2026-11-17): while each tail is one pin per line (the connector pins empty,
  or each its lines', the Reader None: tail C) the board its lines take, as
  in the Library; tails sized to a reader's connectors (Gen by Surface's
  Reader under Advanced Customization, Rectangular's connector pins) the
  board with those connectors, 16 and 32 pins the 32 x 16 board and 32 and
  32 the 32 x 32 (each board's BOM: FPC1 and FPC2; `surface/reader.py`
  `of_design`), any other pins `none (tails for another reader)` (the
  16 x 16 and 48 x 48 readers'; before the review the 32 x 32 reader's
  tails were named the 32 x 16 board, which has a 16-pin connector).  It
  follows a fit applied and every edit at once (`app.js` `showBoard`, run
  with each refresh of the controls); a pin count under its lines (the
  form's error) shows "—"; never disabled, being no file of the build.
- Checks: `tests/test_flexitac_downloads.py` (the rule against
  `surface/reader.py`'s readers, `tailsBoard` at its edges and on every
  reader's tails, the boards' pins their BOMs', every href `boards.js`
  names published); `library_checks.py` `part_routes` (the two rows, their
  lines, one table from 1200 px and the 1440 x 900 fit, the dots from 320
  px) and `part_downloads` (the bundle as served), `showcase_checks.py`
  `part_page` (the two pills on one line, the board's row, the notices,
  the Tab order), `cad_checks.py` `part_reading_board` (both modes, the
  rule at its edges by edits, the connector pins, Gen by Surface's Reader,
  the guide once, a Library sensor), `static_checks.py`
  `part_library_site` (the files on the built site at their pins).

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

From the lead's review of the same day to the user's request later that
day ("Aligned with the grippers", below), the shelf's cards showed their
sensor **Assembled** (`library.js` `SHELF_VIEW`): from the Exploded home the
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

**Aligned with the grippers** (the user's request later on 2026-11-16, with
a screenshot of the live shelf and a crop of a gripper's card: "图一中umicard图
太大，确保你要和上面的card大小保持一致；另外你这样是重新选择了一个角度，用户需要再完成一次
gripper方向的空间转换，这样不好；你做成和这个finger一样的空间角度，而且可以做成exploded,这样
所有card都是对齐的，大小对齐，空间朝向对齐。最上面的xarm gripper的空间朝向也要跟下面的这些家爪都
对齐").  The three-to-a-row grid, the frame on the fingertip and the
Assembled cards and pages above are gone:

- **The grippers' grid.**  The shelf is `.lib-cards` with no rule of its
  own: four to a row (4 + 2) and two below 735 px, so each UMI card is a
  gripper card's size at every width (cards 309 px wide at 1440 px, their
  pictures 297 x 185.6 px, where the shelf's cards were 418 px; 232.5 px at
  1100, 157.8 at 768, 167 at 390; `library_checks.py` `part_layout`
  measures every card and its picture at every width).  From 735 to 899 px
  and on a phone a card's name or line may take two balanced lines ("Pick
  shape / and width"), as the grippers' names do ("Franka / Hand"), and a
  row is as tall as its words: as the grippers' rows are of two heights
  (246.9 and 268 px at 1100 px, "MakerMods Metal Arm" on two lines), the
  UMI rows are a gripper row's height at 1440, 1100 and 390 px (294.7,
  246.9, 227.1), 20 px taller at 735 to 768 px ("Pick your tip width" on
  two lines, the grippers' lines on one) and in one row at 360 px, 21 px
  lower at 900 px (the grippers' names on two lines, the UMI's on one; the
  review of the same day).  The words are kept: a shorter line would make
  the rows one height at 735 to 768 px, the user's to choose.
- **Exploded, at the grippers' homes.**  Every card is its Exploded card
  file (`slot()`, as a gripper's), and every page opens Exploded
  (`showDetail()`); the pictures, the 3D view's homes, are the grippers'
  (scenes.json's rules' `part_homes`, "Parts without a scene"): the finger
  upright, its face to the left, its stack exploded to the left, from the
  front-left 30 degrees up, as the gripper's far finger the user pointed
  to.  The 30 UMI sensors were shot again (each picture new), the 28 of
  the grippers to the same bytes (their records' `view_sha256` and, the
  rules having changed, `scene_sha256` new).
- **The shapes at a card's size.**  From this side the finger's own
  outline is the same for every shape (its side, the fin-ray's ribs); the
  shape is the sheets' outline, a face seen 65 degrees off its normal (its
  width at cos 65 degrees, 0.42).  At 1440 px on a 2x screen each sheet's
  tip reads: square, a short taper, a round nose, a long straight taper, a
  slender concave point, a sharp point; on a 1x screen at 1440 px, and at
  390 px, the straight finger and the five tapers part plainly, the five
  tapers hardly (the review of the same day: their silhouettes at 297 px
  differ by 5 to 8 % of the drawn pixels).  The explode (0.8 of the boards'
  narrower side a layer, Gen by Surface's 0.55) keeps the bottom FPC's
  outline off the finger's face.  The frame holds the whole drawing, its
  height binding, and the tails take a quarter of that height below the
  finger's base (162 of the 704 px of the 2 mm finger's Exploded picture:
  the finger from 48 to 590 px, the bottom FPC's tail to 752), since the
  explode brings the outer sheets toward the camera, which looks down 30
  degrees.  A frame of the part and the sheets on its face alone
  (`sheetPoints`'s `field`) enlarges the finger 1.09 times (540 to 588 px
  tall; the outer sheet's tail on the face still binds); leaving the tails
  out below 30 mm above the finger's base, 1.27 times (685 px), both tails
  then running off the picture's bottom edge, and at 155 px the five
  tapers still look alike.
  Kept whole (the review's option, not taken): every picture of the Library
  is its drawing whole on its ground (the shots tool refuses one its frame
  cuts), the grippers' as these; the cut, or each taper card's default its
  5.8 mm tip (the narrowest, its silhouette the most its own), is the
  user's to choose.
- **The showcase** at the top is at the grippers' homes too ("The
  showcase's scene and files": its camera the rules'), and since the review
  its near finger is see-through as every gripper's (drawn solid it hid its
  own pad whole from this side).  Its card stayed the Assembled picture
  (`SHOWCASE_VIEW`) until "Zoomed on the tip" below; the grippers' cards
  are Exploded.

**Zoomed on the tip** (the user's decisions later on 2026-11-16, after
seeing the shelf above: "你可以show gripper的angle但是zoom in了，就是方向还是那个方向，
但是用zoom in +exploded,那就可以tell了", then, of the first zoom on the preview,
"你现在zoom in 的太过了，tactile的tail都看不到"; and of the showcase's card, "Switch
to exploded"; and the review of the same day, sound with fixes, each finding
reproduced first).  The direction stays the grippers', the cards get closer:

- **A UMI card is its Exploded home zoomed on the tip.**  For every card of
  the shelf (the straight finger's too, so the shelf is one look), the card
  file is drawn from the 3D view's Exploded home, its camera's direction,
  up, explode and lens exactly the home's (`part_homes`, above), the whole
  drawing framed as the home frames it, but in a pane 1.25 times larger
  (800 x 500 CSS px at a pixel ratio of 2: a real render, 1600 x 1000, no
  crop of the 1280 x 800 picture enlarged), and of that drawing the window
  of 1280 x 800 (1/1.25 of the home's width and height) whose top edge lies
  0.06 of its height (48 px) above the finger's tip and whose middle across
  is the middle of the pixels drawn in its rows; downscaled to the card's
  640 x 400 as every card (Lanczos).  The tip stands 6 % below the card's
  top, the grippers' drawings' own top margin (49 to 52 px of 800), so the
  shelf's tips are on the grippers' cards' top line; the sheets and the
  finger stand 285 to 334 px of 1280 from the window's sides; the tails'
  ends run off its bottom edge, and the finger's base stands 55 to 82 px
  of 800 above it (7 to 10 %, at least the top margin): only the tails run
  off.  The rule is `tools/library_write.py` `CARD_FRAMES` (`{part or
  family: {zoom, top}}`, the UMI finger's and its tips' family's), only
  for a part the rules draw at the grippers' homes (`scenes()` refuses
  another).
- **The zoom.**  2 at first (the tips largest: the five tapers part on a
  phone at 1x, but the window reached only 376 px of the whole drawing's
  704 below the tip, the tails cut at their roots); the user, on the
  preview, asked for the tails.  The fields end and the tails begin about
  370 px below the tip (of the 2 mm finger's Exploded picture, 1280 x 800),
  the top FPC's tail ends at about 610, the bottom FPC's at 700, and the
  finger's base lies 536 to 557 px below the tip across the 30 sensors.
  Compared on a sheet of the six cards at 297 and 155 CSS px at 1x (each
  level a real render): 1.0 (the whole drawing), 1.2 (the window to 627 px
  below the tip: the top FPC's tail whole, the bottom FPC's 78 %), 1.25
  (602: 97 and 70 %), 1.3 (578: 87 and 63 %), 1.35 (557: 78 and 57 %), 1.5
  (501: 55 and 40 %, the bottom tail a stub) and 2 (376: none).  1.35 was
  taken first, the largest that keeps every tail's root and most of its
  length; the review found it put the finger's base on the card's bottom
  edge (0 of 800 px on the Concave arc tip's card and the 3 mm straight
  finger's, at most 28 on the rest: the body grazing the edge, not only
  the tails running off).  1.25 is the largest round level that keeps
  every base at least the top margin above the bottom edge (55 px at the
  least; 1.27 leaves about 45, 1.3 about 28), with the top FPC's tail
  nearly whole and the bottom FPC's 70 % in.  There the tips are 1.25
  times the whole
  drawing's, and at 297 px (a card at 1440 px) the six read as six (the
  straight finger's square end, the short taper's step, the convex arc's
  round nose, the trapezoid's straight flanks, the concave arc's slender
  point, the ogive's point).  At 155 px (a phone at 1x) the five tapers
  remain alike; only the straight finger parts.  No zoom that keeps the
  tails parts them there (even at 2 they barely part): the limit is the
  direction, which shows the outlines in the face seen 65 degrees off its
  normal, at cos 65 degrees (0.42) of their width.  A phone-only remedy
  (the UMI shelf one card to a row below about 600 px, its pictures
  358 px wide, leaving the grippers' two-up alignment there) is the
  user's to choose.  The window's top could have come nearer the tip
  (0.03) for a few per cent more; it keeps the grippers' line instead.
- **The 3D view and the pictures stay whole.**  The view has no zoom
  control (the user's decision), so a zoomed home would hide the tails for
  ever: a UMI sensor's page opens Exploded at the same home, the whole
  drawing, and its Exploded and Assembled pictures are the whole drawing as
  before (every byte the same).  So the rule "the card is the view's home"
  has this one exception, written here: a card of `CARD_FRAMES` is the
  home's direction and explode framed on the tip; the card of every other
  sensor (the grippers') is the home's whole Exploded drawing, byte for byte
  as before.  Opened from its card the page reads as the same object: the
  same direction and explode, the whole drawing round the tip the card
  showed.
- **The shoot.**  `tools/browser/library_shots.py` reads such a sensor's
  Exploded home once more, last, its pane 1.25 times `PANE_CSS`
  (`shoot()`), and `card_window()` takes the card (`card_top()`,
  `card_left()`): the larger drawing must be whole (it is the home), the
  tip at least the window's top margin below its top, and the window's
  record sound (`library_write.card_frame_problems()`).  The card's read is
  held to the Exploded home's direction exactly: the stage's report there
  (the homes' directions, the camera's up, the rules' camera and the
  explode) must be the Exploded read's, word for word (the review: the
  pixel likeness of `library_checks`, below, let a degree of elevation
  through).  `card_base()` reads the finger's base in the window: the
  rightmost run of drawn columns (the finger, its sheets exploded to its
  left and clear of it), its lowest pixel; a sheet's tail under the
  finger's columns would join them and read as a base on the edge, which
  is refused.  The manifest's record keeps the frame as `card_frame`
  (below); `--check` compares it with the pictures, and
  `--check-generator`'s third comparison shoots the pictures as the rules
  are with it.  The 30 UMI sensors' card files were shot again; nothing
  else changed (`--check`: the 28 grippers' and every sensor's Exploded
  and Assembled pictures the same bytes).  The card file is 25.4 to
  27.9 KB at 1.25 (26.6 to 29.4 KB at 1.35; 21.3 to 23.6 KB as the whole
  drawing): more detail in the same 640 x 400.
- **The showcase's card is Exploded**, as every gripper's
  (`SHOWCASE_SHOTS`'s card: the Exploded drawing downscaled to 800 x 1000),
  and its page opens Exploded (`SHOWCASE_VIEW`), the card's view; its
  Exploded and Assembled pictures are the same bytes, its card new.
- The checks: `test_library`'s `test_the_umi_cards_are_zoomed_on_the_tip`
  (`CARD_FRAMES`, every committed record's frame and base,
  `card_frame_problems()`, the window's arithmetic, the shoot's zoomed pane
  and its hold on the home's direction),
  `test_the_card_s_window_is_taken_on_the_tip` (`card_window()` and
  `card_base()` on a drawing made in the test, where Pillow is) and
  `ViewTests`' `test_a_card_framed_otherwise_than_its_part_s_is_refused`;
  the `CARDS_ZOOM` mutants; `library_checks.py` `part_aligned` (each of the
  30 UMI card files the tip framing, its finger's base at least 0.05 of its
  height above the bottom edge and its record's, and the same drawing as
  its Exploded picture enlarged and cut there, every gripper's card whole,
  the cards the grippers' size, each UMI page opened from its card the
  whole drawing Exploded at its home); `showcase_checks.py` `part_page`
  (the card Exploded, the page opening Exploded).  The likeness to the
  Exploded picture is a coarse guard (`LIKENESS_MAX`, a mean colour
  difference under 8 of 255): the enlarged 1x picture is softer than the
  card's render, so the 30 cards score 4.1 to 6.1 as they are, and two
  cards shot with the Exploded camera a degree higher score 5.0 and 6.0, a
  degree less tilted 7.8 and 11.3; no bound tells a degree from the
  softness, and the shoot's word-for-word hold is the exact one.

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

## The LeFlexiTac

The user's request of 2026-11-16: "增加一个leflexitac的 放在最前面，注意
leflexitac的gripper是根据lerobot改了，所以你要先找到lerobot,在找到leflexitac的
gripper model.然后把我们的sensor制作上去，角度之类的和其他夹爪保持一致", then
"放在夹爪部分的最前面，就是franka gripper的最前面".  LeFlexiTac (Columbia
RoboPIL, 2026) is LeRobot's SO-101 arm with FlexiTac touch: its gripper is
the SO-101's, remade.  The Library's part `leflexitac` is the Grippers'
first card, before the Franka Hand (`parts.json`'s order; the importer,
`tools/library_import.py --only leflexitac`, places a new part before the
first part that follows it in its table); its title "LeFlexiTac", a name as
short as the other cards' (its page's line says "Moving jaw, LeFlexiTac ·
LeRobot SO-101 (TheRobotStudio)").

- The sources, each at its commit: LeFlexiTac's project page
  (`TNA001-AI/LeFlexiTac` `b61259f`) links its gripper as two STL
  downloads, `assets/models/Moving_Jaw_08d.stl` (the moving jaw that holds
  the pad: the Library's mesh, unchanged) and `Wrist_Roll_08c.stl` (the
  wrist roll with the static jaw, made for the new jaws and wiring);
  LeFlexiTac's code, `TNA001-AI/lerobot_tactile`, holds no part file.
  SO-ARM100 (`TheRobotStudio/SO-ARM100` `a758567`, Apache-2.0) gives the
  STS3215 servo (`Simulation/SO101/assets/sts3215_03a_v1.stl`) and the
  frames (`Simulation/SO101/so101_new_calib.urdf`).  LeFlexiTac's two files
  are SO-ARM100's `Moving_Jaw_SO101.stl` and `Wrist_Roll_Follower_SO101.stl`
  remodelled in their own file frames (the jaw's hub and the servo's
  cradle lie on the stock parts', 64 and 19 % of their surfaces within
  0.05 mm), which are the URDF's simulation meshes in millimetres (within
  0.07 mm): the URDF places them.
- Their licence: none is stated (no `LICENSE` in the repository, none on
  its pages or in its README).  They entered the Library through
  `tools/library_write.py` `PENDING_LICENCES`, an entry dated 2026-11-16
  and pending the user's word (one of LeFlexiTac's authors): the part's
  `spdx` and their `NOTICE.md` rows `NOASSERTION`, with
  `licenses/leflexitac.txt`, the project's note that says so (not a
  licence); `pending_row()` and `pending_licence()` take no other source.
  Until the user's word of 2026-11-17 (below) the page said "Licence not
  stated", the site build warned for their sensors (`pending_note()`) and
  they were not to be published.
- Both jaws have a flat pad face 28.4 mm wide (the moving jaw's 67.2 mm
  long, its file's plane x -10.3; the static jaw's 79.2 mm), parallel and
  17.8 mm apart at the URDF's q 0.  Our sensor is fitted on the moving
  jaw's face (the tails at its hub end) at 1, 1.5, 2 and 3 mm, fill 0.5:
  32 x 27 (1 mm, 31.5 mm of the face's length: 32 lines), 32 x 18, 32 x 14
  (27 x 63 mm, the whole face) and 22 x 9, each centred on the symmetric
  face with its tails centred and ending together.  LeFlexiTac's own build
  carries one hand-made pad (its assembly video and cover photo put it on
  the static jaw, its docs page on the moving jaw); the Library's rule, a
  sensor on both fingers, puts ours on both jaws.
- The scene (`tools/library_scenes.py` `leflexitac()`): the bodies are the
  servo and the wrist roll in two shares of one decimated body, by their
  triangles' centres in its file, the servo's cradle (`wrist-roll.stl`, a
  body) and the static jaw above z 38 mm (`static-jaw.stl`, the other
  finger: see-through).  The mate is the moving jaw at q 0 turned 180
  degrees about the gripper's axis onto the static face (`turned`, `part`
  false: the static jaw is drawn there), so its sensor is the same board.
  The approach runs from the servo's axis to the middle of the two faces'
  far ends, where the jaws grasp (6.6 degrees off `gripper_link`'s axis);
  the moving face lies 32.4 degrees off its plane (`face_tilt_deg`; the
  parallel grippers' 0 to 7.7).  The camera is the rules', no override:
  `library_checks.py` `part_aligned` reads it as every gripper's.
- The opening and the explode, measured (the 2 mm sensor at the homes,
  with the stage's own measures): a rotary jaw's faces converge at its hub,
  where the field begins, so the gap G across the approach is 33 mm at most
  (the other grippers' 56 to 96), and the camera, set by the moving face,
  turns the static face toward itself as the jaw opens.  With the rules'
  gap share 0.42 the explode's film is at most 0.23 seen (the rules want
  0.25) wherever the static jaw still veils its own sensor; from about 41
  degrees open (0.72 rad) the static face turns toward the camera and its
  veil (`ghost_cover`) is 0, and the URDF's full 100 degrees would lay the
  jaw on its side.  So the jaw is drawn 39 degrees open, not fully, and the
  scene's `explode` is `{"gap_share": 0.45}`, the bound of
  `EXPLODE_BOUNDS`, with its reason in `about`: the scenes' one override.
  Measured: 4.7 mm a layer (the others' 7.5 to 13), the least visible
  layer 0.254 (2 mm) to 0.301 (1 mm), the veil 0.59 to 0.62, the near stack
  seen whole, the stacks 28 to 29 px apart, 18.5 mm (`stacks`), the bodies
  8 mm from the fields.
- The look (`tools/library_looks/leflexitac.json`, after LeFlexiTac's
  cover photo and its videos): the jaws and the wrist roll black PLA
  (`pla-black`, the WidowX 250's printed fingers' numbers, layer lines and
  no highlight), the servo's case a smooth black (`servo-black`); the arm
  beyond the wrist (dark purple in the photos) is not drawn, nor the real
  gripper's grip tape, Kapton and ribbon cable; the servo's horn, under the
  moving jaw's hub, wears the case's black.
- The budgets moved: `web/library/` 17.89 MB of 18 (the jaw's own file
  0.94 MB), the bodies 2.72 MB of 3, the art 0.62 MB of 0.65.
- Checks: `tests/test_library.py` `test_the_leflexitac_s_scene` (the
  bodies, the mate onto the static face, the opening, the explode and its
  reason, the record's numbers) and
  `test_a_source_stating_no_licence_is_taken_only_by_its_dated_entry`,
  the `LEFLEXITAC` mutants; `library_write.py --check` and
  `library_split.py --check`, the shots' `--check`.
- After its independent review (2026-11-17): a warning did not stop the
  files stating no licence from being published, so
  `tools/build_static_site.py` refuses a Library holding them
  (`library_write.unlicensed()`: the parts whose `spdx` is `NOASSERTION`
  and the `NOTICE.md` rows that say it) before writing anything, unless
  `--allow-pending-licences` asks for a local preview (the pages workflow
  never does; `tools/browser/static_checks.py` does for the site it
  serves), and `tools/export_public.py` exports nothing of such a commit.
  LeFlexiTac's files are SO-ARM100's Apache-2.0 parts remodelled, so their
  rows, the part's holder and the project's note credit them
  (`remodelled from SO-ARM100 a758567, STL/SO101/Individual/...`, with
  `licenses/so-arm100.txt`; `PENDING_LICENCES`' `remodelled`,
  `remodelled()`), `pending_row()` and `pending_licence()` take a row or a
  licence only with that credit, and a body's `NOASSERTION` row is taken by
  its pending entry alone, never by the Apache-2.0 it names.  The
  importer's recipe is its own (`LEFLEXITAC_RECIPE`), so `--only
  leflexitac` runs from the user's tree.  Measured for the user, not
  changed: the card's near sensor, on the static jaw, almost edge-on (its
  amber a third of the far one's in the Assembled picture, the other
  grippers' 0.9 to 1.3), and LeFlexiTac's own sources disagree on its
  pad's jaw (its assembly video, its page's step and cover photo: the
  static jaw; its docs page: the moving jaw); both are the handoff's open
  items.
- The user's word (2026-11-17), asked whether LeFlexiTac's two files may
  be published: "leflexitac, i am the author, so its ok to use it in
  public" (a co-author of LeFlexiTac).  The entry is
  `tools/library_write.py` `PERMITTED_LICENCES`' now (`PENDING_LICENCES`
  is empty), dated (`permitted` 2026-11-17, `by` a co-author of
  LeFlexiTac): the files still state no licence (`NOASSERTION`, none is
  invented), their `NOTICE.md` rows and the part's licence (its
  `permission`) say `permission()`, "shared with the authors' permission
  (given by a co-author of LeFlexiTac, 2026-11-17)", the project's note
  says the permission is not a licence, and the page's one link reads
  "Shared with the authors' permission".  The SO-ARM100 credit stays.
  `unlicensed()` holds only what no permitted entry takes, so the site
  build and `tools/export_public.py` take the LeFlexiTac and still refuse a
  pending entry's files (`test_library`'s and `test_static_site`'s pending
  fixture: the same entry made pending again); a pending entry's rows and
  licence never say the permission.  `library_checks.py` `part_downloads`
  checks the page's link; the `LEFLEXITAC` mutants gain 6.  The pictures
  are unchanged (`library_shots.py --check --only` the four sensors and two
  others: 0 differ).
- Its review (2026-11-17): a `PERMITTED_LICENCES` entry without its day
  or without who gave it was taken as a permission all the same (its rows
  and its part's licence saying none, its files published, the page saying
  "Licence not stated"), and one without `by` stopped the gate with a
  `KeyError`.  `permission()` now wants `permitted` a day (YYYY-MM-DD) and
  `by` a name, and an entry without them is no permission: taken by
  neither table, its files held by `unlicensed()`.  The importer's row
  takes the words from `permission()` (one copy); 2 `LEFLEXITAC` mutants
  more.

## The YUBI Gripper

The user's words of 2026-11-17, looking at a card made of a finger pad they
had downloaded (`FINGER_PAD_t30_L.stl` and `_R`): "这个同样也只做fingertip的三角；
名字不要叫genealist, 感觉是 yubi： https://github.com/Toyota/yubi-hw" (this one too:
only the fingertip's triangle; not "Generalist", it is YUBI).  Their two files
are, byte for byte, `STL/gripper/FINGER_PAD_t30_L.stl` and `_R.stl` of
Toyota/yubi-hw.  The Library's part `yubi-gripper` is the Grippers' last card,
after the MakerMods Metal Arm, titled "YUBI Gripper" (the README's name of the
robot-mounted half of YUBI; "YUBI Gripper, 2.5 mm" is 20 characters), its line
"Gripper finger pad · Toyota Motor Corporation" (the Franka Hand's words; until
its review of 2026-11-17 "Finger pad (t30)", the maker's file code).

- The sources: `https://github.com/Toyota/yubi-hw` at
  `dd8bd13d2fd8e5003057243576f88be333d95fc5` (2026-09-21, its newest commit),
  YUBI, "Yielding Universal Bidigital Interface", by the Frontier Research
  Center of Toyota Motor Corporation (the README; the project page
  yubi.airoa.io and the paper, arXiv 2606.10244, with the AI Robot
  Association).  Each file pinned by its SHA-256 in `tools/library_scenes.py`:
  the assembly `STEP/gripper/YUBI Gripper Assy_Dynamixel_ver2.STEP`
  (SolidWorks AP214, mm), and of `STL/gripper/`, `CASE.stl`,
  `BRACKET_DYNAMIXEL.stl`, `UPPER PLATE_CAMERA BKT.stl`, `FINGER
  ATTACHMENT_L.stl`, `FLAP_L.stl`, `FINGER_PAD_t30_L.stl` (the part) and
  `FINGER_PAD_t30_R.stl` (read to check the mirror below); `LICENSE`.
- The licence: CERN-OHL-W-2.0 (the `LICENSE` file, Copyright 2026 Toyota
  Motor Corporation; `COMMERCIAL.md` is a summary of it, and says the Toyota
  name and marks are not granted and no endorsement may be implied).  It
  allows copies and changed copies to be conveyed with their notices, a
  reference to the licence, the source location and, for a changed file, a
  notice of who changed it, when and how (sections 3.1 to 3.3), the changed
  files licensed under it (3.3(d)).  So `licenses/yubi-hw.txt` is the
  `LICENSE` as published; `NOTICE.md` names the repository at its commit,
  says the changed bodies are under CERN-OHL-W-2.0 and not the repository's
  Apache License 2.0, gives each one's change and its date (2026-11-17), and
  names this repository their Source Location; the part is the pad
  unchanged.  `tools/library_write.py` `OPEN_LICENCES` takes CERN-OHL-W-2.0
  (the bodies' rows), `tests/test_library.py` `SPDX` too (the part's).
- Where the parts stand: `step_placements()` reads the assembly STEP as
  text (each NEXT_ASSEMBLY_USAGE_OCCURRENCE's transformation: the part's frame
  in the assembly's; one flat assembly, millimetres in every part, the second
  placement the identity, else refused).  The STL files are CATIA's (ASCII,
  but the pads' and the upper plate's), each in a frame of its own: each was
  registered on its part's B-rep vertices in the STEP (the rotation an
  exchange of axes, the translation by iterative closest point; 41 to 93 %
  of the vertices within 0.01 mm, the rest on curved edges the two exporters
  cut differently), `YUBI_FILE_IN_PART`.  The fingers turn about two parallel
  shafts 30 mm apart, the two spur gears z30 (module 1) meshing them, so
  each turns as much as the other the other way (the scene builder checks
  the gears' axes through the attachments' hinges).  The assembly carries
  PAD_t30_R on the right finger and PAD_t20 on the left; the guide's other
  choice, FINGER PAD_t30_L on FINGER ATTACHMENT_L, is drawn: the left
  finger's attachment and flap are the right finger's mirrored across the
  plane half way between the hinges (0.000 mm), and the t30_L file is the
  t30_R file mirrored across its z 9 mm (0.026 mm both ways, checked on every
  build), so the left pad is PAD_t30_R mirrored across that plane.
- The face: the pad grips with its z- face (its two screws counterbored
  from it, two shallow concave arches across it, between the screws and
  toward the tip).  Its fingertip is a flat trapezoid at
  the tip end of that face, facets 100 and 101 of the file: x 0 to 16.7 mm,
  6.96 mm wide at the tip and 17.03 mm at its root, 201.3 mm2, its normal
  5.6 degrees toward the tip off the pad's -z; a 45-degree chamfer along its
  long edges and a fillet into the small arch at x 16.7 to 17.3 close it.
  The page's `surface` preset grown from facet 101 takes exactly these two
  (the `smooth` preset runs on over the arches, a selection with holes, not
  one piece), the user's triangle; the base the root edge's middle
  (16.709156, 20.081618, 4.533682), the tails toward the mount.  A symmetric
  face (2e-6 mm), so each sensor centred (field offset 0.0), the tails
  centred and ending together, a clean build, at fill 0.5: 1 mm 16 x 14
  lines, 166 taxels (field 13.5 x 15.5 mm, tails 17.4 mm); 1.5 mm 11 x 10,
  74 (14.25 x 15.75); 2 mm 8 x 7, 40 (13.0 x 15.0, tails 18.4); 2.5 mm 6 x 5,
  24 (11.25 x 13.75, 19.6).  3 mm keeps the rules too but makes 5 x 4 lines,
  16 taxels on a 10.5 x 13.5 mm field, so 2.5 mm takes its place, as on the
  Franka Hand's 16 mm pad ("Four pitches, 1 to 2.5 mm.").  A small sensor, as
  the user asked: the fingertip alone.
- The pose (`YUBI_OPEN_DEG`, since its review of 2026-11-17): from the
  assembly's pose the fingers close 6.75 degrees until the pads meet and
  open 38.5 until FINGER ATTACHMENT meets the UPPER PLATE (measured on the
  parts at their placements), 45.25 degrees of travel.  The tip face leans
  toward the tips 5.6 degrees and as much again as the finger opens, and
  the camera of the grippers' homes, 30 degrees up and 65 off the far face
  (57 Assembled), sees the near face from behind at asin(cos 65 -
  sin(lean)): the more the jaws open, the more edge-on the near finger's
  sensor.  First drawn 16 degrees open (the most at which the near finger
  still veils its own sensor: `ghost_cover` 0.365 to 0.384, 0 at 17.5), its
  review found that sensor a thin line in every picture: the camera 3.2
  degrees behind the near face's plane in Exploded and 10.2 Assembled (the
  parallel grippers 25 and 33, the Trossen WidowX AI 32.4 and 41.1), its
  field drawn 0.14 of the far exploding top board's pixels in Exploded and
  0.37 Assembled (the stage's own measures; the Franka Hand, WidowX 250
  and Trossen WidowX AI 0.86 to 1.10 and 1.0 to 1.26).  Measured at 0 to
  16 degrees with the stage: closing raises those numbers (0.80 and 0.87
  at 0) but shrinks the far sensor on the card below the rules'
  `card_min_px` (20): the 2.5 mm sensor 19 px wide at 8 to 10 degrees, 20
  at 11 and 12; the 2 mm one 18 at 0 and 4, 19 at 6, 20 at 8.  So it is
  drawn 11 degrees open, the least opening at which every pitch keeps
  every rule (17.75 from closed; the tip's chord 32.409 of the 80.812 mm
  its parts allow, the scene's `opening`): the camera 7.9 degrees behind
  the near face in Exploded and 15.0 Assembled, its field 0.36 and 0.53 of
  the far one's (2.6 and 1.4 times the 16 degrees'), the tip faces 54.5 mm
  apart (the WidowX 250's jaws 55.6), the face's lean 16.56 degrees
  (`face_tilt_deg`), every layer seen whole (`visible_min` 1), the near
  stack seen whole (`near_seen` 1), the veil 0.80 to 0.83, the stacks 85 to
  89 px apart, 7.4 mm a layer, the card's sensor 20 to 22 by 44 to 48 px.
  The near sensor still reads narrower than on the parallel grippers: the
  rules' card size, not the pose, keeps the fingers from closing further.
  An opening whose matrices, rounded to 6 decimals, stay rigid within 1e-6
  (14 and 15.5 do not; 11 does).  The approach is the gripper's axis,
  across the hinges in their plane: in the pad's file (-cos 11, 0, -sin
  11).  No camera or explode override: `part_aligned` reads it at the
  homes the other seven read (elevation 30, 65 and 57 degrees off the face,
  front 1, upright 0.87; left 0.90 and 0.84, at 16 degrees 0.89 and 0.83).
- The scene: the sensor finger is the left one (the user's pad), the other
  the right one, this one mirrored across the gripper's middle plane (`mirror`,
  `part` true: the part mirrored is FINGER_PAD_t30_R within 0.03 mm; its
  board the mirror-image board), see-through.  The rules' front puts the
  camera on the servo's side of the gripper (the left pad's face turned
  left); the right pad as the part would have shown the upper plate's side.
  The bodies, decimated within 0.5 mm (`case.stl` 3020 to 1354 triangles,
  0.38 mm; `bracket-dynamixel.stl` 1024 to 516, 0.15; `upper-plate.stl` 3620
  to 1440, 0.29; `finger-attachment.stl` 1088 to 460, 0.29; `flap.stl` 1039
  to 257, 0.26; 201 770 bytes): the case, the servo's bracket, the upper
  plate with the camera's bracket, and on each finger its attachment and
  flap (the right finger's the left files mirrored).  Not from the model:
  the DYNAMIXEL XM430-W350-R, a plain box to its published 28.5 x 46.5 x 34
  mm where the STEP places it, and the fisheye camera (USB
  CAMERA_ELP-USBFHD01M-L180): its 32 mm board, lens holder, barrel and glass
  where the STEP places it, 10 degrees down (`drawn-servo.stl`,
  `drawn-camera-board.stl`, `drawn-camera-lens.stl`,
  `drawn-camera-glass.stl`, the project's own).  Not drawn: the gears,
  shafts, bearings, screws, the arm's bracket (BRACKET_GRIPPER, UR5e_FLANGE)
  and the black ribbed rubber sheets the photos show glued over the pads'
  gripping faces (cut to suit, the guide says; the sensor takes the
  fingertip's place, and its tails run down that face toward the mount,
  where a sheet would lie on them or be cut round them: left to the user,
  2026-11-17; STL/gripper/ has no file of it, the STEP's RUBBER SHEET_t30_R
  is the assembly's only one).  Each body made from yubi-hw's files says
  in its own 80-byte header when it was changed (since the review of
  2026-11-17: "modified (decimated <= 0.5 mm, 2026-11-17) by FlexiTac-Gen
  2026, see NOTICE.md", the split ones "(decimated, 2026-11-17; split)",
  CERN-OHL-W-2.0 section 3.3(b) for a file fetched alone; the licence
  itself is NOTICE.md's, 80 bytes holding no more).
- The look (`tools/library_looks/yubi-gripper.json`), after the project's
  photos of the real gripper on the UR5e, the Franka and the ALOHA arms and
  its bill of materials: the case, plates, bracket, attachments and flaps
  black PLA (`print-black`; the photos' black `#1e1e1c`, `#373734` lit), the
  pads red PLA (`pla-red`, `#c42a27`, roughness 0.8, `env_intensity` 0.35:
  the photos' lit pad `#c83e33` to `#d4443a`, `#b91d28` to `#cf2c37`), the
  servo matte black, the camera's board black (`pcb-black`; the guide's
  render draws it blue, the photos black) and its lens's glass glossy.  The
  amber boards (hue 33) stand apart from the red pad (hue 2) by hue.
- The budgets moved, in dated lines of `tests/test_library.py`:
  `web/library/` 17.0 MB of 17.6 (17 before), the bodies 2.67 MB of 2.7
  (2.5), the art 0.60 MB of 0.625 (0.6).
- Checks: `tests/test_library.py`
  `test_the_yubi_gripper_is_drawn_from_its_open_model` (the part the
  published pad unchanged, the fingertip's two facets alone, the four
  pitches centred, the scene's pose and mirror, its bodies and words, no
  "Generalist", `NOTICE.md`'s terms of the licence, the drawn shapes
  credited, the trademarks, the licence text; since its review the pose's
  reason: the camera at the homes 7.9 and 15.0 degrees behind the near
  face, the cards' widths, the page's line, the bodies' dated headers, the
  bodies' section's exception, ELP), the `YUBI` mutants of
  `tools/mutation_check.py` (15, each killed alone by `test_library`);
  `library_write.py --check`, `library_split.py --check`,
  `library_scenes.py --only yubi-gripper --check` (it names only the split
  files and the scene's looks, the difference a look file makes);
  `library_shots.py --check --only` on its four sensors; `library_checks.py`
  `part_layout`, `part_pictures`, `part_aligned`.
- After its independent review (2026-11-17, sound with fixes, six
  findings), each reproduced first: the near finger's sensor a line at 16
  degrees open (measured as above; drawn at 11 now, the least opening the
  rules allow); "full opening" said of every gripper in `NOTICE.md`'s
  bodies' section, this key table's `opening` row and the scene builder's
  notes (each now names the YUBI Gripper's exception); the page's line the
  maker's file code (now "gripper finger pad"); the bodies' headers
  without their change's date (now in each) and ELP, whose camera the
  project drew, not among the trademarks (added).  Left to the user: the
  rubber sheets (above), and the card's sensor the grid's smallest (on the
  Exploded card 2 102 orange pixels of 36 261 drawn at 11 degrees, 1 958
  of 36 783 at 16; the Franka Hand 3 093 of 78 887, the other six 10 652
  to 26 998 of 45 329 to 63 659): the fingertip alone, as asked.

## Hands: a sensor on every finger (2026-11-17)

**The Unitree Dex3-1 back (2026-11-18).**  After trying the gently curved
faces (docs/CAD_MODE.md "Gently curved faces (2026-11-17)") the user
wrote "挺好的，这样你就可以把dex3加回去，然后可以push一版本" (good: put the
Dex3 back, then push a version).  The hand is back
(`fpc-int-n-dex3-back`, from `b5403f3`), restored from `bff728c` and
fitted the way the page now fits its fingertip: its part, mesh (the same
bytes, `9fb4d06c...`, also `tests/fixtures/unitree-dex3.stl`), bodies,
look file and NOTICE.md's sources, notes, rows and Dex3 among the
trademarks as they were; its scene builder (`dex3()` and its helpers,
scipy's hull again) with the face's normal and centre of its new fit; its
card between the Unitree Dex1-1 and the LEAP Hand (18 cards, "Grippers.
Eighteen, each fitted at four pitches.", 102 sensors).  Its face is no
longer the pair of 7 mm disks the old curved handling allowed at 0.3 %
(110, 49, 28 and 18 taxels on 11 to 13.5 mm): it is the dome's patch one
click selects at the curved faces' 1 %, and the writer composes its
request as the page sends it there (`library_write.py`
`page_options(curved=True)`, `part_options()`, `stretch_problem()`;
until that day it refused a doubly curved Library face).  Every other
part's request, reply and build id is the same bytes (`library_write
--check`, 102 current; the 98 others' fits, entries and pictures
unchanged).  The hand's own tests and mutants are back
(`test_library`'s tables, its notice and trademark,
`test_a_doubly_curved_face_is_sent_at_the_curved_limit`;
`mutation_check.py` `UNITREE_DEX3`, 8).  "The Unitree Dex3-1" below.

**Two hands removed, the Dex1-1 moved (2026-11-17).**  At the user's word
the same day ("现在这个版本去掉allegro,去掉dex3；加上unitredex1"; asked whether
the last part meant moving the Unitree Dex1-1, then the eighth card, to
the end beside the LEAP Hand: "1. yes") the Allegro Hand and the Unitree
Dex3-1 are out of the Library (`fpc-int-n-trim-hands`, from `bff728c`):
their parts, fits, pictures and manifest records, art, meshes, bodies,
scenes, looks, the licence text only the Allegro Hand used
(`licenses/mujoco_menagerie-wonik_allegro.txt`), their NOTICE.md sources,
notes, rows and trademarks (Allegro, Dex3, Wonik Robotics), their scene
builders (`tools/library_scenes.py` `allegro()` and `dex3()`), their own
tests and their own mutants.  Git history keeps them: `bff728c` has every
file, and its docs/LIBRARY_VIEW.md the sections "The Allegro Hand" and
"The Unitree Dex3-1" that stood here.  The Unitree Dex1-1's card moved
from after the I2RT YAM to just before the LEAP Hand, the card itself
unchanged (`parts.json`'s order, `scenes.json`'s map, the scene builder's
`GRIPPERS`): 17 cards, "Grippers. Seventeen, each fitted at four
pitches.", 98 sensors; no picture changed.  `licenses/unitree_ros.txt`
stays (the Dex1-1's) and so does BSD-2-Clause in `OPEN_LICENCES` (the
Robotiq 2F-85's).  The mechanism below stays whole, the LEAP Hand its one
user: `extra_fingers`, a body's `extra<k>`, a hand's `checks` override,
the stage's still stacks and their measures; its generic tests hold it with
the LEAP Hand alone (`test_a_hands_further_fingers_are_seen` on
`leap-hand-2mm`, `test_every_border_is_one_the_page_fits` on the AgileX
Piper's border), and its mutants are one group, `mutation_check.py`
`HAND_MECHANISM` (the Dex3-1 line's and the Allegro line's mutants of the
mechanism, their ids kept); `UNITREE_DEX3` and `ALLEGRO_HAND` are retired
with the five mutants whose edits were the two hands' own text.  The
comments of `cad/library_stage.js` still name the two hands: the file is
one of the view's sources (`VIEW_SOURCES`), whose hash every picture's
record carries, so it is left as it is.  Below, the hands' history as it
was written.

The user's requests of 2026-11-17 ("还有一个unitree的三爪也可以加上去"; of
the dexterous hands, "先把这几个做出来，看看每个手指都做出来的效果怎么样": build
them and show how it looks with a sensor on every finger) and decisions of
that day: a hand's card shows the **whole hand** (its sensors small on the
card, a scene's `checks` override the way), and the hands follow the
grippers in the same grid, in the order the Allegro Hand, the LEAP Hand,
the Unitree Dex3-1 (on `fpc-int-n-hands` after the MakerMods Metal Arm,
"Grippers. Ten, each fitted at four pitches."; the counts are
`entries.json`'s: `library_checks.py` `CARDED`, `test_library` `GRIPPERS`).
Three lines built a hand each, each with its own further fingers: the
Unitree Dex3-1's `extra_fingers` (measured still stacks and the card
override), the LEAP Hand's the same key with a further finger's own links,
the Allegro Hand's own key `fingers` (`[{name, matrix, part}]`, named
fingers a body or `see_through` could name, measured apart as
`fingers_seen`).  Their merge keeps **one mechanism**, the first with the
second's links:

- **The scene.**  `extra_fingers`: 1 to 4 (`EXTRA_FINGERS_MAX`)
  `{kind, matrix}`, each `matrix` taking the sensor finger onto a further
  finger, rigid, `kind` its determinant's sign (on all three hands, and on
  the LEAP Hand now, `turned`: the same part, the same board).  A body's `finger` may be
  `extra<k>`, k 1 to the scene's count: that further finger's own link,
  opaque, which its stack is not held apart from (as the sensor finger's
  stack is not from the sensor's links).  `see_through` stays a subset of
  `["sensor", "mate"]`: a further finger is never see-through.  A hand's
  scene (one with `extra_fingers`) alone may carry `checks`,
  `{card_min_px}` within 12 to 20 (`CHECKS_OVERRIDE_BOUNDS`), its reason
  in `about`; `library_write.py` `scene_checks()` puts it over the rules'
  checks for that scene's records, and `library_shots.py` holds a shoot to
  the same.
- **The stage** (`cad/library_stage.js`) draws on each further finger the
  part's mesh, opaque in both modes, with a still copy of the stack
  (assembled in both modes, each layer's face and band its own, the
  film's face hidden but on a placed pad), and frames the homes about
  them.  Its measures take each further fingertip as an opaque body of the
  cover and of the clearances, each still stack (`stack3`, `stack4`, ...)
  as one that covers, as the mate's does; the exploded stack is held apart
  from the nearest of the other stacks in mm (`clearance_mm.stacks`) and on
  screen (`stacks_apart_px`).  Each further stack is measured itself: its
  top FPC (its face toward the camera) in both modes, whose least seen
  share is the record's `extra_seen` (held to `near_seen_min`; a record has
  it exactly when its scene has further fingers), and its field's
  clearance to every body and finger but its own fingertip and its own
  links (`stack3_body`, ..., folded into `clearance_mm.bodies`).
  `info().stage.extra_fingers` counts them; `library_checks.py`
  `part_hands` reads both measures from the stage.  A scene without
  further fingers is drawn and measured as before (`library_shots.py
  --check` 0 differing on `franka-hand-2mm`, `widowx-250-2mm`,
  `umi-finray-2mm` and `i2rt-yam-2mm` after the merge).
- **What the merge changed.**  The Allegro Hand's scene was ported to
  the key: its middle and ring fingers `extra_fingers` (the same two
  matrices), their links `extra1` and `extra2` (they were `middle` and
  `ring`), every body, the thumb's base links solid and the border as its
  review left them.  Its pose too but one joint: held apart on screen from
  the middle finger's stack as well as from the thumb's (its line held it
  from the thumb's alone, 96 to 105 px), its index finger's exploded stack
  was 14 and 19.2 px from the middle finger's at 1 and 1.5 mm, under
  `stacks_apart_min_px` 20, and the shots tool refused those two; with the
  middle finger's first joint 0.1 rad more curled it is 28 to 40 px ("The
  Allegro Hand" in `bff728c`'s copy of this file; a choice the user may
  revisit).  The LEAP Hand's
  and the Unitree Dex3-1's scenes, pictures and numbers are the bytes
  their lines shot (their records' view sources the merged stage's).  The
  three lines' copies of the rule's tests and mutants are one set
  (`test_library` `test_a_hand_s_further_fingers_and_its_card_override`;
  `mutation_check.py` `UNITREE_DEX3` the mechanism's, `LEAP_HAND` and
  `ALLEGRO_HAND` each hand's own; since the two hands' removal
  `HAND_MECHANISM` and `LEAP_HAND`).
- **The cards.**  Each hand framed whole at the grippers' homes (65 and 57
  degrees off the sensor finger's face, 30 up, front +1): the card's top
  FPC 24 to 28 px wide on the Allegro Hand (its face 21.8 mm across; no
  override), 14 to 15 on the LEAP Hand and 14 to 16 on the Unitree Dex3-1
  (their scenes' override, `card_min_px` 14).  The reviews proposed
  framing a hand's card on its fingertips and their stacks (1.36 to 1.5
  times closer, about 19 to 24 px), which cuts the hand at the picture's
  edge (the shots tool refuses it, and the prototype the user approved on
  2026-11-05 draws every gripper whole); the user chose the whole hand.

### The LEAP Hand

Its line `fpc-int-n-leap-hand`; its review the same day (sound-with-fixes)
changed the part, the pose, the home and the further fingers: below as
they are now.

- **Source and licence.**  MuJoCo Menagerie's `leap_hand` at `f3b6013`
  (its last change, `71f066a` of 2026-07-04, is older), the right hand:
  `right_hand.xml` and its visual meshes (OBJ, metres).  Its `LICENSE`,
  read in full, is the MIT License, "Copyright 2023 Ananye Agarwal"
  (`licenses/mujoco_menagerie-leap_hand.txt`, byte for byte).  Its README
  derives the right hand from dex-urdf's `leap_hand` at
  `2ee2f70cfd549857f56ffe13c61fa939f4cb50ba`, whose folder's `LICENSE.txt`
  is the same MIT text and holder (with dex-urdf's note that it modified
  the files), and so from `LEAP_Hand_Sim` (MIT, the same holder;
  `150bc3d`'s `LICENSE.txt` byte for byte Menagerie's).  dex-urdf's README
  table had given the hand "CC BY-NC 4.0" until its commit
  `93505db3c0b29b4a80bd359048de7d39c9ea3218` of 2024-12-05 ("update the
  license of LEAP hand"), which made that row "MIT", as the LICENSE files
  are.  Not used: the `LEAP_Hand_API` (code, CC BY-NC 4.0) and the CAD of
  the request form (CC BY-SA 4.0).
- **The part and its face.**  The white fingertip is the contact surface
  (the paper's photo: white soft tips on black links).  `distal.obj` draws
  two objects: `fingertip` (material `black_metal`: the distal link, its
  horn and six posts, 3.5 x 3.5 x 17.5 mm, that hold the fingertip from
  inside) and `fingertip_W` (material `White_tip`: the white fingertip,
  1450 faces, y 13.386 to 43.386 mm of the file, open at its flange).  The
  part is the white object alone, in mm, its faces in the file's order
  (`meshes/leap-hand.stl`, 72 584 bytes, derived by
  `tools/library_scenes.py` `PART_MESHES`; Menagerie's `tip.obj` is a
  100-triangle copy of it).  Until the review it was the file cut at the
  flange's plane, 2167 facets that took the six posts and a ring of the
  link along into the download and Gen by Surface's mesh.  Its pad is one
  exactly flat face, 26.04 x 13.87 mm, a rounded rectangle (the tip end a
  faceted arc), the fingertip's largest fair face; grown with `flat` and
  `theta_c_deg` 1 from facet 1124 (the preset's 4 degrees take a sliver of
  one curved side, and the face is then 0.11 mm off its mirror image), it
  is its own mirror image within 0.005 mm, so every sensor is centred.
  The sides beyond it fall away 0.03 mm at 8 mm from the middle, 0.3 at
  9, 0.75 at 10 and 1.5 at 11 mm, not alike on the two sides (0.04, 0.08
  and 0.23 mm apart at 9, 10 and 11 mm): a wider face would be off its
  mirror image and its sensors off centre, so the flat face is kept.  The
  thumb's fingertip is the same print: the thumb carries the same face.
- **Pitches.**  1, 1.5, 2 and 3 mm, fill 0.5: 25 x 13 (315 taxels, the tip
  end's corners masked), 17 x 9, 13 x 6 and 8 x 4, the fields 12.5 to 10.5
  mm across the pad and 22.5 to 24.75 mm along it, the tails centred on the
  root edge and ending together (16.6 to 20.0 mm, toward the distal link);
  every build clean.  4 mm would leave three columns: not offered.
- **The scene.**  The hand open and ready to grasp: each finger bent at
  its knuckle (mcp 1.2 rad, pip 0.3, dip 0), the middle and ring spread
  from the index and a little more bent (rot 0.55 and 1.0, pip 0.5), the
  thumb raised out of the palm (th_cmc 1.5, th_mcp 0.1), straight, its pad
  facing the index pad 67.4 mm across (the stage's gap 66.5 mm).  A sensor
  on every finger: the index fingertip is the part, its stack the one
  exploded (the finger whose face the camera sees best: nearest it,
  nothing in front); the thumb is the mate, its fingertip the part turned
  180 degrees about x of its file (every point of `thumb_distal.obj`'s own
  white fingertip within 0.07 mm), see-through with its two outer links
  (its pad faces away from the camera); the middle and ring fingertips are
  the scene's `extra_fingers`, opaque, their stacks assembled, and their
  links are their own (a body's `finger` `extra1`, `extra2`).  The bodies:
  the palm, each finger's base, proximal, medial and distal links and the
  thumb's four, where `right_hand.xml` places them; each distal body is its
  file's black object, posts and all.
- **Its further fingers.**  Its fingertips sit on their links, so a
  further field is 2.7 mm from its own distal link, which the index's is
  never held to (its own links are the sensor's): hence a body's
  `extra<k>` (this hand's line), and the middle and ring fingers' links
  are theirs.  From the grippers' side the camera looks along the row of
  fingers from the index's side: with the three upright side by side the
  index's exploded stack crossed the middle fingertip's on screen
  (`stacks_apart_px` 0), hence the spread above (9 px at rot 0.3 and 0.6,
  21 at 0.45 and 0.85, 30 at 0.55 and 1.0 but 17 at 1 mm; with pip 0.5:
  33.1, 38.5, 46.5 and 62.6 px at 1, 1.5, 2 and 3 mm).  Each further
  stack is seen 0.89 to 0.92 (`extra_seen`), more than 12 mm from every
  other body.
- **The bodies' size.**  At the grippers' 0.5 mm and 15 degrees the eight
  files were 107 288 triangles, 5.37 MB, twice the seven grippers' bodies
  together (sixteen servos' rounded cases and brackets, every face of them
  seen from outside: 96 to 100 % of each body's triangles in sight from 162
  directions).  They are decimated within 1.0 mm, each face facing its way
  within 45 degrees (a body's `decimate`): 43 503 triangles, 2.18 MB.  The
  hand is drawn at about 0.26 mm a pixel on its page; the stage smooths
  its normals at 35 degrees.  The bodies' budget is raised by that share.
- **The home and the card.**  The hand is at the grippers' homes (65
  degrees off the index pad's normal Exploded, 57 Assembled, elevation 30,
  front +1; `part_aligned` holds it as every gripper).  Until the review
  its own camera was 45 degrees in both modes, for its card: there the
  exploded layers half hid each other (`visible_min` 0.41 to 0.46), and
  the card was out of line with the others (the user's rule of
  2026-11-16).  At the homes the whole hand is framed and the pad, 13.87
  mm across, is seen at cos 65: the card's top FPC is 15, 15, 14 and 14 px
  wide at 1, 1.5, 2 and 3 mm, under
  the rules' `card_min_px` 20, so the scene's `checks` override sets 14,
  its reason in its `about`.  The card's drawing is 281 px wide of 640
  (242 before the spread; the WidowX 250's 286, the Dex1-1's 304, the
  others' 361 to 422), the fingertips and their stacks its top third (y 26
  to 133 of 400); framed on them the card would be 1.36 times closer (the
  top FPC about 19 px).
- **The look** (`tools/library_looks/leap-hand.json`), after the paper's
  photo of the hand (RSS 2023, figure 1): black all over but for the four
  white fingertips; the links, servos in their brackets, one satin black,
  the palm a matte black print, the fingertips a cool matte white.  The
  paper's figure 8 shows a build whose fingertips are printed black.
- **The title** "LEAP Hand", the maker's name for it; "Carnegie Mellon
  University" its maker in `parts.json`.

### The Unitree Dex3-1

The user's request of 2026-11-17 ("还有一个unitree的三爪也可以加上去"),
removed at the user's word the same day and back since 2026-11-18 on its
dome's curved fit (above).  The Dex3-1 is the Unitree G1's three-finger
hand: a thumb of three joints opposing two fingers of two.

- The model: unitree_ros `b579bbe`, `robots/dexterous_hand_description/dex3_1`
  (BSD-3-Clause, HangZhou YuShu Technology), its `dex3_1_l.urdf` and the
  left hand's meshes (the same bytes as `g1_description`'s
  `left_hand_*`, last changed upstream on 2024-09-25).  The middle
  fingertip's file is the index fingertip's byte for byte, and the thumb's
  last two links are a finger's two turned 180 degrees about (1, -1, 0)
  (every vertex the same): so one Library part serves all three
  fingertips, and one board all three sensors.
- The pose: each finger 35 and 35 degrees, the thumb 0, 10 and 15 (each
  joint within its limits), `bff728c`'s: surveyed on 2026-11-17 against
  the 7 mm disks' face normal, of the poses whose thumb pad faced the
  fingers' within 8.3 degrees (8.28 at this one), the most open with even
  finger joints.  Kept on the dome's patch (the look as before, not
  surveyed again): its normal 4 degrees round from the disks', the thumb's
  pad faces it within 16.2 degrees (the review of 2026-11-18).  The
  fingertips' pads 76.0 mm apart at the face's centre along its normal
  (74.3 mm at the 7 mm disks' centre until 2026-11-17).  A hand has no
  stroke: the opening is that gap.
- The part: the index fingertip, `meshes/unitree-dex3.stl`, the link with
  its ridged cap (its outer skin up to 0.24 mm under the hull, 0.09 mm at
  the median and 0.16 at the 90th percentile of its facets' centres)
  replaced by the cap's convex hull made mirror-symmetric across the
  link's mid-plane (a laminated sensor bridges the ridges, as on the
  Franka pad's grooves), written by the private scene builder and held to
  `parts.json`'s SHA-256 by it.  The face is a dome, 24 mm wide and 8.8 mm
  deep across the finger.
- The fit (2026-11-18): the selection is one click on the dome, as the
  page sends it (grow, the Surface preset, `stretch_budget` 0.01, from
  facet 9267, the select reply's `centre_facet`); a click inside that
  patch (the dome's middle band, within about 6 mm of the mid-plane, from
  the finger's root to about 45 mm out) selects the same 405.1 mm2 patch
  (788 facets, 0.90 % on the part, its own mirror image across z = 0),
  and a click on the dome's flanks or its tip end, outside it, a smaller
  patch round itself, on its side (`select.stretch_region`'s widest within
  the budget round the click: 152.9 mm2 from facet 11794, 8.9 mm off the
  plane; the review of 2026-11-18); the request's `strain_limit` is
  1 %, the page's on a doubly curved selection; the base auto (its base
  end one side of 10.96 mm across the plane at the finger's root, x 21 mm
  of the part's file, the tails toward the palm).  Pitches 1, 1.5, 2 and
  2.5 mm, fill 0.5: 26 x 15 (332 taxels), 18 x 10 (146), 13 x 8 (82) and
  11 x 6 (52), the fields 14.5 x 25.5, 14.25 x 26.25, 15 x 25 and 13.75 x
  26.25 mm (masked, following the dome's outline), each symmetric and
  centred, the tails centred and ending together (17.6, 18.1, 19.0 and
  18.7 mm), every build clean: about three times the 7 mm disks' taxels.
  3 mm keeps every rule too (9 x 5, 35 taxels, 13.5 x 25.5 mm, tails
  19.2 mm; 3.5 and 4 mm 24 and 20), but a fifth pitch would end the
  grid's "each fitted at four pitches" (`library.js` drops it when the
  cards' counts differ): offered at four, the choice of 3 mm in place of
  2.5 the user's.  The fingers' first links have flat knurled pads (about
  24 x 20 mm), but they do not oppose the thumb's (25 mm apart at best and
  36 mm aside): the fingertips are where it grips.
- The scene: the index fingertip is the sensor finger (its stack explodes
  toward the thumb), the thumb's tip the mate (turned, see-through), the
  middle fingertip the scene's one further finger (`extra_fingers`): its
  stack's top FPC seen whole (`extra_seen` 1.0 on all four sensors), its
  field beyond the 12 mm reach of every other body and finger.  The
  approach is the face's (across the select reply's normal, (0.1843,
  -0.9829, 0), in the fingers' plane, out of the palm; 4 degrees round from
  the disks'), the fields 1.2 to 1.6 degrees off the plane along it
  (`face_tilt_deg`; 0.3 with the disks).  With the larger boards every
  rule holds: the exploded stack 41.4 to 43.1 mm and 118 to 124 px from
  the others (139 px before), `near_seen` 0.99 to 1, `visible_min` 1,
  `ghost_cover` 0.87, `opaque_max` 0.
- The card: framed whole (85.9 mm from the middle of the hand's box to its
  farthest point), the sensor's top FPC is 19 px wide on the card at every
  pitch (16, 16, 14 and 14 px with the disks), one short of the rules'
  `card_min_px` 20: the scene's `checks` override sets 19 (14 until
  2026-11-17), the measured width with no margin, its reason in its
  `about`: the rules' 20 needs the most compact pose a scan of the joints
  found (the fingers 70 and 15 degrees, the thumb 0, -25 and 40), framed
  6 % closer (80.9 mm, about 20 px), a hand no longer open to grasp (the
  review of 2026-11-18; until then the `about` said 20 was out of reach).
  Framed on its fingertips and their stacks the card would be about 1.5
  times closer (the palm and the fingers' first links cut, measured with
  the disks), which the user did not choose (the whole hand, "Hands"
  above).
- The look (`tools/library_looks/unitree-dex3.json`, after Unitree's
  product pictures, the bytes of `bff728c`): the palm satin black
  (`palm-satin`) with the grey metal blocks of the fingers' knuckles
  (`knuckle-grey`, at metalness 0.5 and an environment of 1.6, as the I2RT
  YAM's hub), the fingers' first links black anodised (`link-anodized`)
  with their knurled pads in matt black rubber (`pad-knurled`), the
  fingertips black rubber (`tip-rubber`, the part's look).
- Its share of the Library: 1.59 MB (the mesh 0.78, its four fits 0.47,
  the bodies 0.29, the art 0.03 MB, the scene 9 KB) and 0.32 MB of
  pictures; the budgets raised with a dated note (`tests/test_library.py`:
  29.2, 8.9, 8.3 and 1.02 MB).
- Screenshots: `library-look-work/look/out/dex3-back/` (the grid's last
  row at 1440 and 390 px, its window Exploded and Assembled, its card
  beside the Dex1-1's and the LEAP Hand's, Gen by Surface from its card
  with the dome's field).

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
- `card_frame`, only for a sensor of a part whose cards are zoomed on the
  tip (`library_write.CARD_FRAMES`, "Zoomed on the tip"):
  `{zoom, top, window_px, margins_px, base_px}`, the window's top left
  corner in the drawing `zoom` times larger, the drawing's margins in the
  window (`[left, top, right, bottom]`: the top `top` of its height, the
  bottom 0) and the rows between the finger's base and the window's bottom
  edge.  `card_frame_problems()` refuses a record without it where its
  part's cards are framed, with it where they are not, at another zoom or
  top, a window outside the larger drawing, a drawing off its top, within
  `CARD_SIDE_MIN` (0.04) of its width from a side or whole above its bottom
  edge, or a finger's base within the top margin of that edge (since the
  review of 2026-11-16).

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
| `clearance_mm` | `{bodies, other_finger, stacks}`: the least distances from the field over both modes (`stacks`: the exploded stack's fields to the other finger's assembled stack, Exploded, the nearest of the others on a hand; on a hand `bodies` also each further stack's field to every body and finger but its own fingertip and its own links, `stack3_body`, ...) | `bodies` and `other_finger` at least `clearance_min_mm`; `stacks` at least `stacks_apart_min_g` x G and `stacks_apart_min_mm` |
| `stacks_apart_px` | the exploded stack's silhouette to the other stack's on screen (on a hand the nearest of the others'), Exploded, px of the measure | at least `stacks_apart_min_px` |
| `card_px` | stack 1's top FPC's box in the card, `[w, h]` px | its smaller side at least `card_min_px` (the scene's `checks` override where it has one) |
| `band_css` | `{contain, cover}`: that box in the 390 px phone band, CSS px | - (reported) |
| `extra_seen` | a hand's alone (its scene has `extra_fingers`; the reviews of 2026-11-17): the least share of the further stacks' top FPCs (each one's face toward the camera, assembled in both modes) that nothing opaque and no other layer hides, over Exploded and Assembled | at least `near_seen_min` (a record has it exactly when its scene has further fingers) |

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
  finger and its tapered tips: `gripper_parts()` are the others), a card
  framed otherwise than its part's (`card_frame_problems()`, since
  2026-11-16: "Zoomed on the tip"), and with
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
  `scenes.json` or a body's row; since 2026-11-17 an id with underscores
  followed by "/" or after "-" is an upstream model's folder, not a recipe
  (menagerie's `agilex_piper/` and the licence text
  `mujoco_menagerie-agilex_piper.txt` carry the AgileX Piper's).
- `run()`: `--check` refuses the pictures' and the scenes' problems
  (since the shoot of 2026-11-06, `VIEW_REQUIRED`, a picture with no 3D
  view among them; while it is false, a warning) and says how many sensors
  have one; writing reports them and writes each sensor's `view`.

`tools/build_static_site.py` stops on the same problems (the scenes of the
parts it builds and the index's, the showcase's among them), on a `view` in
`entries.json` other than `pictures()`' and warns as the writer does (of
the showcase's pictures of older sources too); `BUILD.json`'s library
record counts the sensors `viewed` and names the `showcase`.

## The AgileX Piper

The user's request of 2026-11-17 ("AgileX Piper；ALOHA 2 夹爪；Galaxea R1
Lite；OpenArm（Enactic）；Rainbow RB-Y1；Seeed reBot DevArm；xarm原装夹爪；还有一个
unitree的三爪也可以加上去；这些先并行开始做"), built on the line `fpc-int-n-piper`:
an eighth gripper card, `agilex-piper`, last in the grippers' grid (the
heading "Grippers. Eight, each fitted at four pitches." on that branch; the
merge of the parallel lines settles the order and the count).

- **Sources.**  MuJoCo Menagerie's `agilex_piper` at `fb36886` (2026-11-02),
  the newest commit to touch the model, not the other menagerie grippers'
  `f3b6013` (2026-10-23; the review of 2026-11-17: the newest is the rule).
  It moved `piper.xml`'s lights to `scene.xml`: `piper.xml` differs from
  `f3b6013`'s by that one line, `link6.stl`, `link7.stl` and `LICENSE` are
  the same bytes, and the scene, its bodies and the pictures came out the
  same: `piper.xml`, `assets/link6.stl` and `assets/link7.stl`.  Its
  `LICENSE` is the MIT License, Copyright (c) 2024 RosenYin, the same text
  as the model's source, AgileX's `Piper_ros` (its README: derived from
  `piper_description`); `licenses/mujoco_menagerie-agilex_piper.txt` is
  that file byte for byte.
- **The finger.**  The Library mesh is `link7.stl` itself (the left finger,
  in metres, 1838 facets, watertight), not HandUMI's printed replica of its
  tip (a sleeve of 30 036 facets that is not closed): the real finger's
  inner face is one clean face, 72 mm long in its chart (the finger
  76.5 mm), 20 mm wide at its end, 25.4 mm where the tip's flat ends and
  56 mm at the root (a concave flare), flat at the tip (9.9 mm) and over
  the root's plate (36 mm), and rising 2 mm between them in three strips
  (4.9, 3.3 and 0.9 degrees).  `surface` grows it whole from the tip (36
  facets; a developable chart).  Its root is not symmetric: the plate's
  edge is 1 mm longer on one side (y -67.03 against -66.03 of the file)
  and notched by the carriage's two tabs, so the face as selected reads
  asymmetric and its sensors off centre (0.3 to 4.1 mm at 1 to 4 mm).  The
  setup's border,
  a rectangle in the chart's uv (`parts.json`), keeps the face from 3 mm
  above the root's lowest edge (u -27.8112) past the tip, 28.5 mm either
  side of the finger's mid-plane: inside it the face is its own mirror image
  (0.046 um), its one exit the border's root edge, and every sensor centred
  with its tails centred and ending together.
- **Pitches.**  1, 2, 3 and 4 mm at fill 0.5 (the large face of the ARX X5
  and the I2RT YAM: at 1.5 mm the 32 lines already cap it): 32 x 30 (818
  taxels, a 29.5 x 31.5 mm field from the tip), 32 x 24 (508, 47 x 63 mm),
  23 x 17 (253, 49.5 x 67.5 mm) and 17 x 14 (138, 54 x 66 mm), each a
  masked field following the flare, its build clean.
- **The scene.**  `piper.xml` at full opening: joint7 slides 0 to 0.035 m
  along -z of `link7`, joint8 is its mirror (the equality joint8 = -joint7),
  so each finger is 35 mm out and the faces 70 mm apart.  `link8.stl` is
  `link7.stl` turned 180 degrees about its file's z (every point of each
  within 0.067 mm of the other; the mirror y -> -y is 1.0 mm off): the mate
  is that turn, the part itself (`part` true), carrying the same board.
  The body is `link6.stl` (the flange and motor can, the cross plate with
  its guide rail and end blocks) where `piper.xml` places it; its quats
  are a URDF's quarter turns written to six digits (0.707105, 0.707108,
  1.89468e-08 for 0), about 4e-6 off, so each rotation is squared to the
  axes (`tools/library_scenes.py` `squared()`, which refuses one more
  than 1e-5 off).  Approach +y of the finger's file (its tip).  Decimated
  from 13 422 to 7106 triangles within 0.44 mm (355 384 B).
- **The look** (`tools/library_looks/agilex-piper.json`), after AgileX's own
  photo of the PiPER at its zero pose (`Piper_ros`,
  `asserts/pictures/piper_zero.png`) and its product pictures of the
  gripper: the fingers one flat black (`#313637` to `#33383b` in the
  photo, luminance 49 to 57 from the 5th to the 95th percentile, no
  highlight: `finger-black`, the ARX X5's matte finger numbers on the base
  `rubber-black`, since the gripper's listings give its fingers as non-slip
  rubber, a non-metal; the review of 2026-11-17), the cross plate and its
  end blocks as dark but bead-blasted black anodising, a metal with a soft
  edge highlight (`#343a3d`: `frame-blasted`), the motor can a darker, glossier
  black that mirrors the room (`anodized-black`), the ground steel rail the
  one bright part (`#888781` to near white at its end: `rail-ground`).  No
  screw, belt, pulley or lettering is drawn.
- **The card.**  "AgileX Piper", the user's own words (AgileX writes
  "PiPER"; beside "Franka Hand" and "I2RT YAM" the plain capitals read as
  a name, not a typo), one line at every width from 1440 to 390 px; its
  range "1 to 4 mm" and "Pick your pitch".
- **Budgets.**  The Piper adds 0.68 MB to `web/library/` (17.14 MB of the
  17 MB budget), 355 384 B to `bodies/` (2.81 MB of 2.5 MB) and 41 674 B
  to `art/` (0.62 MB of 0.6 MB): `tests/test_library.py` raises each by
  its share in a dated line.
- **Checks** (`tools/browser/library_checks.py`): the grippers' counts
  follow `entries.json` (the cards, the pages opened, the rows: four to a
  row from 735 px, two below, `rows_of_cards()`; the heading's literal is
  "Eight" on the branch).  `tests/test_library.py`'s
  `test_the_agilex_piper_is_menagerie_s_finger_on_its_whole_face` pins the
  part, its licence text, the border, the pitches, each fit's symmetry, the
  scene's approach, opening, mate, bodies and looks, and since the review of
  2026-11-17 the pin (`fb36886` in the part, the scene and its five NOTICE
  rows), the rail one piece as the scene's about names it, the fingers a
  non-metal on a metal plate and the face's numbers above;
  `tools/mutation_check.py` `AGILEX_PIPER` (10 mutants, 6 of that review,
  each killed alone by `test_library`).

## The Library's lines merged (2026-11-17)

The lines of 2026-11-16..17 merged on `fpc-int-n-final` from `2d60728`,
each with `--no-ff` and in this order: the UMI cards zoomed on the tip, the
Robotiq 2F-85, the LeFlexiTac, the AgileX Piper, the Galaxea R1 Lite, the
Seeed reBot DevArm, the xArm Gripper, the Rainbow RB-Y1, OpenArm 1.0, the
YUBI Gripper, the three hands, Gen by Surface's tool menu numbered, and the
FlexiTac order files with the reading boards.  The sections above are each
line's; their counts ("Eight", "62 sensors", "14 cards") are their
branches'.  Merged:

- **The grid.**  `parts.json`'s order is the user's (2026-11-16..17):
  LeFlexiTac, Robotiq 2F-85, Franka Hand, WidowX 250, Trossen WidowX AI,
  ARX X5, I2RT YAM, Unitree Dex1-1, MakerMods Metal Arm, AgileX Piper,
  Galaxea R1 Lite, Seeed reBot DevArm, xArm Gripper, Rainbow RB-Y1, OpenArm
  1.0, YUBI Gripper, then the Allegro Hand, the LEAP Hand and the Unitree
  Dex3-1: 19 cards under "Grippers. Nineteen, each fitted at four pitches."
  (the count a word to twenty and its digits past, as `library.js` writes it),
  then the UMI shelf's six; 106 sensors.  `scenes.json`'s map and
  `tools/library_scenes.py`'s `GRIPPERS` follow it.  Since the same day's
  trim (the user's word; "Hands: a sensor on every finger" above) the
  Allegro Hand and the Unitree Dex3-1 are gone and the Unitree Dex1-1 is
  the card before the LEAP Hand: 17 cards, "Grippers. Seventeen, each
  fitted at four pitches.", 98 sensors.  Since the user's word of
  2026-11-18 the Unitree Dex3-1 is back, between the Dex1-1 and the LEAP
  Hand ("The Unitree Dex3-1" above): 18 cards, "Grippers. Eighteen, each
  fitted at four pitches.", 102 sensors.
- **One of each.**  `library_write.OPEN_LICENCES` is one tuple (Apache-2.0,
  MIT, BSD-3-Clause, BSD-2-Clause, CERN-OHL-W-2.0); `DENIED_NAME` one
  expression, the Robotiq 2F-85's first alternative
  (`robotiq(?![ _-]?2f-?85)|2f-?85[ _-]?opened`) then the xArm Gripper's
  `ufactory` and `xarm` ones (`tests/test_library.py` holds the same); the
  recipe keys the Piper's lookarounds with the LeFlexiTac's one-word skip.
  `tools/library_scenes.py`: its sources, licences, repositories and owners
  one literal each; one `PART_MESHES` for every Library mesh it writes (the
  reBot's capped finger, the RB-Y1's pad, the LEAP Hand's and the Dex3-1's
  fingertips), each held to `parts.json`'s file, SHA-256 and bytes before
  it is written; `build_body()` decimates once a source, a pick, an object
  and a decimation (the LeFlexiTac's wrist roll shared out by `piece()`,
  the OpenArm's Collada picks, the LEAP Hand's OBJ objects apart);
  `load()` reads an OBJ (its objects), a binary or ASCII STL and a Collada
  file (its pick).  Run whole with the downloads' cache, then
  `library_split.py`, it gives every gripper's committed scene and bodies
  byte for byte (32 min on the merge's host).
- **Decided at the merge.**  The Seeed reBot DevArm's meshes are Seeed's
  under CERN-OHL-W-2.0 too: that text, `Seeed-Projects/reBot-DevArm`'s
  `LICENSE` at `eda479d`, ships beside the menagerie's MIT one as
  `licenses/seeed-rebot_devarm.txt`, fetched and pinned by the scene
  builder and named by the part's row.  The Galaxea R1 Lite's border ran
  clockwise, which the page's `border.js` `validate()` refuses (the hands'
  `border_problem()` found it): it runs counter-clockwise now, its top edge
  still the first (the base's side 0), and its four fits' first proposals
  are the same builds.  The showcase's pill is "FlexiTac fabrication
  guide" at the guide's ordering section, the address Gen's step 3 links
  (the user's word of 2026-11-17).  NOTICE.md's trademarks are one sorted
  union of the makers' and products' names, the YUBI's drawn parts after
  them.
- **The pictures.**  Every sensor and the showcase shot once with the
  merged stage: `library_shots.py` (106 sensors in 871 s) then
  `--showcase`.  The pictures and the art came out the same bytes (the
  merged stage draws every two-finger gripper as its line did, and the hands
  were shot with it on theirs); the manifest's and `showcase.json`'s records
  name the merged figure and view sources and the R1 Lite's new fits.
- **Budgets** (`tests/test_library.py`, set once for the merged set):
  `web/library/` 29.5 MB (28.60 MB without its pictures), the pictures
  9.2 MB (8.84 MB), the bodies 8.6 MB (8.27 MB), the art 1.05 MB (1.01 MB),
  3 to 4 % to spare each.  Lowered at the two hands' removal the same day,
  with a dated note: 27.6 MB (26.72), 8.55 MB (8.23: 294 pictures of 98
  sensors and the showcase's three), 8.0 MB (7.68) and 0.985 MB (0.95).
  Raised when the Unitree Dex3-1 came back (2026-11-18): 29.2 MB (28.31),
  8.9 MB (8.56: 306 pictures of 102 sensors and the showcase's three),
  8.3 MB (7.97) and 1.02 MB (0.98).
- **After its verification** (2026-11-17, pass-with-fixes).  The public
  copy's suite reads no private file unasked (`test_library`'s reBot test
  had read `tools/library_scenes.py` and failed there; `test_static_site`
  now asks every private path a test names for `exists()` first).  In Gen
  by Surface the OpenArm 1.0's finger and the YUBI Gripper's pad on its
  base plate run off the sensor-on-the-part figure's bottom at the Exploded
  home (`drape.js` frames the part within 3 times the sheets' radius; these
  reach farther): `cad_checks part_library` holds the cut to that edge
  (`LIBRARY_CUT_BELOW`), and framing them whole is the user's call.
