# The Library's 3D view: the formats

The user's requests of 2026-11-05: for the seven grippers that are not UMI
fingers, the Library shows the **whole gripper** with a sensor on both
fingers, the jaws fully open; and on each sensor's page in the Library
(`library.html#<id>`) the picture becomes a 3D view the visitor can
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
`see_through` drawn in both views; both formats stay v1.  Paths are relative
to `web/` unless they start with `tools/` or `tests/`.

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

## Files

| Path | Written by | What it is |
| --- | --- | --- |
| `library/art/<id>.json.gz` | `tools/browser/library_shots.py` (the shoot) | the generator's art of the sensor's two boards (below) |
| `library/scenes/scenes.json` | by hand; its `scenes` map by `tools/library_scenes.py` | the index of the grippers' scenes and the rules |
| `library/scenes/<part>.json` | `tools/library_scenes.py` (private) | one gripper's scene |
| `library/bodies/<part>/<name>.stl` | `tools/library_scenes.py` (private) | the scene's bodies: binary STL, mm |
| `library/shots/manifest.json` | `tools/browser/library_shots.py` | the pictures' manifest, with the records below |
| `library/entries.json` | `tools/library_write.py` | each variant's `view` (below) |

The bodies are third-party files (each one a row of `library/NOTICE.md`'s
tables, its licence text in `library/licenses/`, modified as its row says)
or the project's own (`bodies/makermods-metal/rail.stl`: a plain rail drawn
by the project, not MakerMods hardware).  No MakerMods body is ever
committed (`tools/library_write.py` `DENIED_SHA256`).

## The art: `library/art/<id>.json.gz`

The gzip (level 9, no name, time 0) of one JSON document written canonically
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
| `bodies` | `[{mesh: "bodies/<part>/<name>.stl", sha256, bytes, triangles, matrix, finger}]`: `matrix` takes the body's file into the part's frame; `finger` is `"sensor"`, `"mate"` or `null` |
| `see_through` | a subset of `["sensor", "mate"]`: the fingers drawn see-through, in the rules' `see_through_modes` (the near finger, `["mate"]`, on every gripper: the user's decision of 2026-11-06) |
| `picture` | the words after the label in the pictures' alt text (`"on both fingers of the open gripper"`) |
| `camera` | optional: `{exploded or assembled: {tilt_deg, elevation_deg, front}}` over the rules' (tilt 45 to 70, elevation 15 to 45), its reason in `about` |
| `explode` | optional: `{gap_share}` over the rules' (0.25 to 0.45), its reason in `about` |

Every matrix is a 4 x 4 array of rows, applied to column vectors, its last
row `[0, 0, 0, 1]`, its upper 3 x 3 orthonormal.

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

## The page's reads (checks only)

With `?probe` in the address, `library.js` keeps `<pre id="libViewState"
hidden>`, a JSON `{state, note, id, build_id, mode, drawn_mode, moved,
gripper, offset, buffer, ms, stage}`: `state` one of `off`, `loading`,
`drawn`, `failed`, `unavailable` and `lost`; `offset` the drawing's move to
the middle at its home in device pixels; `stage` the stage's numbers.  With
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
  its scene's and rules', a UMI record with `stage`, or recorded numbers
  that break the rules' `checks`.
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
  none); `see_through` and `picture`; the overrides within their bounds
  with "reason" in `about`; a file of `scenes/` or `bodies/` no scene
  names; `DENIED_SHA256` over every body and every hash `NOTICE.md` names,
  `DENIED_NAME` over every body's file; and no text of the private
  importer's inputs (`asset/`, `outputs/`, `gripper_recipes`, the word
  recipe, a part's id with underscores, an absolute path) in a scene,
  `scenes.json` or a body's row.
- `run()`: `--check` refuses the pictures' and the scenes' problems, warns
  of the pictures with no 3D view and says how many sensors have one;
  writing reports them and writes each sensor's `view`.

`tools/build_static_site.py` stops on the same problems (the scenes of the
parts it builds and the index's), on a `view` in `entries.json` other than
`pictures()`' and warns as the writer does; `BUILD.json`'s library record
counts the sensors `viewed`.
