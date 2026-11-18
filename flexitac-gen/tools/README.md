# Development tools

None of these is part of the unittest suite, and none writes into the
project but `library_write.py` (the Library's data, `web/library/`),
`library_split.py` (the grippers' bodies by material, their scenes' looks
and their rows of `web/library/NOTICE.md`),
`browser/library_shots.py` (the Library's pictures, `web/library/shots/`,
each sensor's art, `web/library/art/`, and with `--showcase` the
showcase's pictures, `web/library/showcase/`, and `showcase.json`'s
records of them) and `library_showcase.py` (the showcase's meshes, drawn
shapes and scene, `web/vendor/ufactory-g1/` and `web/library/`).

- `mutation_check.py`: applies known defects to scratch copies of the
  project and runs the suite on each; every mutant must be killed unless the
  catalogue marks it as equivalent or out of scope (with the reason).  The
  catalogue holds the 2026-10-12 audit's 36 baseline mutants and the C1
  extras re-expressed for the current code, mutants of every fix stage and
  mutants of the figures and tables the documents quote.  Each copy has the
  CI workflow beside it, as at the repository root, because a document test
  reads it.  `--check` only verifies that every edit still applies (CI runs
  it, and the suite's `test_every_catalogue_edit_still_applies` checks the
  same, and that every edited file is public, since the public copy's CI
  runs it too); `--list` prints the catalogue; `--only audit/ T/` selects by id
  prefix.  Each mutant's suite runs with `FPC_MUTANT=<id>`, so that test
  skips itself in the mutated copy; if it fails there anyway, the run counts
  as a false alarm.  The copies leave out the caches, `.git` and what a run
  wrote under `outputs/`, never the committed `outputs/.gitkeep`, which
  `test_static_site`'s public export asks for (the review of 2026-11-06:
  without it the baseline failed and every kill read as a false alarm); a
  kill whose failing tests all fail in the unmutated copy too is reported
  `SURVIVED (baseline failures only)`.  Each mutant is one run of the whole
  suite: on 2026-11-06 one run took 670 to 1900 s on the development host
  (the baseline 1393 s) and about 1700 s on a GitHub runner (931 to 1723 s
  in the public copy's site workflow of 2026-11-04 to 2026-11-06), the
  longer runs on a loaded host, so the default `--timeout` is 5400 s per run
  (at the 900 s of before every mutant read `KILLED` by its timeout).  A
  full run of the catalogue is some 850 suite
  runs: about 20 hours at `--jobs 16` (the 17 minutes of 2026-10-21 were 369
  mutants against a suite of 460 tests).  In CI it is a manual job that runs
  the mutants named in its `only` input (`--only`), as many as fit the hosted
  runner's 6 hours.
- `golden_values.py`: prints the default-build values pinned by
  `tests/test_golden_default.py`, for review after a deliberate change.
- `compare_easyeda_gerbers.py`: compares the Gerber ZIP EasyEDA Pro exports
  from one of our `.epro2` projects (docs/EASYEDA_EXPORT.md) with our Direct
  Gerber ZIP of the same board, or with the `.epro2` itself: the copper,
  coverlay, outline and stiffener layers filled by scanlines (areas,
  bounding boxes, the area of their symmetric difference) and the
  stiffeners of both `jlcpcb.json` files; exit status 0 when every layer
  agrees.  `tests/test_easyeda_export.py` uses its reader.
- `build_static_site.py`: writes the static site (`--out DIR`): the page
  with a Content-Security-Policy meta tag and the browser-backend flag,
  `web/` as `static/`, `static/py/engine.zip` (`app.py` and the packages it
  imports, byte-reproducible) and the Pyodide 0.27.8 core files, downloaded
  (or `--pyodide-archive FILE`) and checked by their SHA-256, and the
  FlexiTac repository's star and fork counts from GitHub's API written into
  the header (`GITHUB_TOKEN` when set; none with `--no-github` or when the
  API does not answer: both pages refresh them, `web/counts.js`); it replaces an output
  folder only when an earlier build wrote it.  It writes the three pages
  (since the user's decision of 2026-11-16: `index.html`, the Library, the
  first page; `gen.html`, the generator; `library.html`, a forwarding page,
  with the head tags alone) and is the Library's
  gate: every sensor of `web/library/entries.json` is fitted again and must
  give its committed reply and build id, and its fit's request must still be
  the one the page sends (`library_write.compose` of `parts.json` and
  `gen.html`'s defaults), else the build fails ("the library is stale: run
  tools/library_write.py"); each sensor's Top and Bottom FPC Gerber ZIPs
  (`app.answer`'s exports of its design) go to `static/library/files/<id>/`
  with `static/library/files.json`: the gate with its 84 ZIPs takes about
  11 s with `--jobs 8` (the default on 8 cores or more), about 40 s in one
  process.  The Library's pictures (`web/library/shots/`) are published
  with `web/` as `static/library/shots/`; a picture of another fit (the
  wrong sensor pictured), a broken one or an `image` in `entries.json` that
  is not its picture's stops the build, and one of older figure sources is
  published with a warning (the build runs no browser to shoot it again).
  So is each sensor's 3D view (the user's request of 2026-11-05,
  `docs/LIBRARY_VIEW.md`): its art, the grippers' scenes and their bodies
  are published with `web/` as `static/library/art/`, `scenes/` and
  `bodies/`; an art or a gripper's stage that `library_write.pictures`
  refuses, a scene `library_write.scenes` refuses (of the parts built) or a
  `view` in `entries.json` that is not the manifest's stops the build, so
  does a picture with no 3D view (its record without its art, a gripper's
  without its stage: `VIEW_REQUIRED`, since the shoot of 2026-11-06; before
  it such a picture was published with a warning), and `BUILD.json`'s
  library record counts the sensors viewed.  Since the review of 2026-11-17
  a Library holding files whose source states no licence and whose authors'
  permission is not recorded (`library_write.unlicensed()`: a
  `PENDING_LICENCES` entry's) is refused before anything is written, the
  files named, unless `--allow-pending-licences` asks for a local preview
  (the pages workflow never does; `browser/static_checks.py` does for the
  site it serves); files shared with their authors' permission
  (`PERMITTED_LICENCES`: the LeFlexiTac's since 2026-11-17) are built.
  library record counts the sensors viewed.  Since 2026-11-17 it also
  checks the FlexiTac hardware's files as published (`flexitac_downloads.py
  --check` on `static/vendor/`: the pad's two Gerber ZIPs and the reading
  boards' bundles at their pins, each bundle re-derived), a file of other
  bytes stopping the build, and records their SHA-256s (`hardware`).
  See the README, "As a static website" and "The Library".
- `export_public.py`: writes the public part of the project from a commit
  (`git archive`, so only committed files) into a clone of FlexiTac/FlexiTac
  (`--repo DIR`): its `flexitac-gen/` folder (the generator, page, documents,
  tests and tools, with `claude/APP_HANDOFF.md` and the audit files of
  `claude/verification/` the documents link to; no session notes, plans,
  assets or video tools) and
  `.github/workflows/flexitac-gen.yml` (`public/pages-workflow.yml`: the
  tests, then the static site built and published to
  `https://flexitac.github.io/flexitac-gen/`).  It commits and pushes
  nothing, and exports nothing of a commit whose `web/library/` holds files
  whose source states no licence and whose authors' permission is not
  recorded (the review of 2026-11-17: a `PENDING_LICENCES` entry's; the
  LeFlexiTac's, `PERMITTED_LICENCES` since 2026-11-17, are exported).
- The samples of Gen by Surface ("Try a sample" under the step guide, the
  user's request of 2026-11-06; `web/samples/`): `samples.json` is kept by
  hand (each sample's Library sensor, a whole gripper's mesh record and the
  thumbnails' views); the two whole grippers' STLs come from a private
  assembly tool (stdlib, outside the public copy) that writes each one from
  the Library's scene of that gripper and the bodies it names, its finger's
  facets first and byte for byte, and checks every input's SHA-256 against
  the scene; `browser/sample_thumbs.py` draws the thumbnails, into
  `web/samples/thumbs/` (with `library_write.py` and
  `browser/library_shots.py` the tools that write into the project).
  `tests/test_samples.py` checks the files, their notice and budget, and
  that each whole gripper's Library selection is its finger's face and fits
  to the Library's sensor.
- `library_write.py`: fits the Library's sensors (the Library, `./`, and Gen
  by Surface at `gen.html?part=<id>`; the user's requests of 2026-11-05) as the
  page asks for them: for each variant of `web/library/parts.json` the
  request the page sends (its selection, base and border, the Resolution
  step's defaults read from `web/gen.html` with the variant's pitch and
  fill, the mesh's file name, no unit; the strain limit the one the page
  sends after the select, `part_options()`: data-flat's 0.3 % off a doubly
  curved face, the select's own 1 % on one, the Unitree Dex3-1's dome since
  2026-11-18, where it had refused such a face, and a click's
  `stretch_budget` the select's own, `stretch_problem()`), `surface.api.fit`'s reply, and the
  product rules on its proposal #1 (one tail pin per line, field-only
  containment, the tails centred and ending together, a symmetric face's
  sensor centred, a build with no error or warning); a variant that breaks
  one is rejected and nothing is written.  It writes `web/library/fits/<id>.json`
  and `web/library/entries.json` (only what changed; the UMI finger's 2 mm
  sensor is `web/vendor/umi/default-fit.json`, checked only); `--only
  ID,...` fits some, `--check` writes nothing and exits 1 listing the stale
  ids.  About 10 s for the 42 sensors with `--jobs 8` (15 s for the 58 of
  2026-11-16, 18 s for the 62 with the Robotiq 2F-85; `--check` 41 s for the 62 of 2026-11-17 with `--jobs 4` on a
  loaded host, the Galaxea R1 Lite's line); re-run it after any
  change that moves a build id.  `tests/test_library.py` checks its files.
  It writes each sensor's `image` (the cards' and the sensor page's
  picture: the generator's sensor on the part, the user's request of
  2026-11-05) from `web/library/shots/manifest.json`, which
  `browser/library_shots.py` writes with the pictures: null without one,
  and null for a picture of another fit (the wrong sensor pictured), which
  `--check` refuses with a broken picture, and with none (every sensor has
  its picture since 2026-11-05); a picture of older figure
  sources (`web/cad/onpart.js` and the modules it imports) is kept with a
  warning (re-shoot it: the public CI runs no browser).  After a re-fit
  or a new sensor, write, shoot the changed sensors, then write again.
  A family of parts (`parts.json` families: the UMI finger's tapered tips)
  is one card closing its shelf's part, its grid of choices checked
  complete.  Each sensor's 3D view (`docs/LIBRARY_VIEW.md`; the user's
  request of 2026-11-05: each sensor's page turns in 3D, the grippers drawn
  whole) is its `view` in `entries.json`, its art and, for a gripper, its
  scene, written for a sensor whose record in the manifest is current with
  its art and (a gripper's) its stage; `--check` and the site build refuse
  an art that is not the record's bytes and document, of another sensor or
  build or at another raster, a stage of another scene or rules
  (`scene_sha256`), breaking the scenes' rules (the shot's measured numbers:
  every exploding layer visible, the other finger and the bodies clear of
  the field, the exploded stack apart from the other finger's in mm and on
  screen, the near stack seen through its see-through finger, the card's
  sensor large enough) or recorded for the UMI
  finger or a tapered tip, and a record without its art or a gripper's
  without its stage (`VIEW_REQUIRED`, set by the shoot of 2026-11-06 that
  wrote every sensor's; before it such a picture was kept with no 3D view,
  a warning); a picture of
  older view modules (`web/cad/library_view.js`, `library_stage.js`,
  `stl.js`) is a warning, as one of older figure sources.  `scenes()` checks
  the grippers' scenes (`web/library/scenes/`, `bodies/`): every gripper
  part but the UMI finger and its tips with one, their format, the part's
  mesh, rigid matrices and the mate's kind by its determinant (turned: the
  same board on the other finger; mirror: the mirror-image board), each
  body's file, triangles and notice row with an open licence (the MakerMods
  rail, the project's own, none), the overrides' bounds and reasons, the
  deny-list over the bodies and the hashes `NOTICE.md` names, and no
  private input named; `--check` refuses its problems and reports how many
  sensors have a 3D view.  Each shelf's heading is written here in one wording, the
  count and the range of its pitches ("Four pitches, 1 to 3 mm."; the
  user's decision of 2026-11-05); since 2026-11-06 the page shows the UMI
  finger's alone, after the other grippers' cards, one each, and since the
  user's request of 2026-11-16 its heading names its shapes ("Six finger
  shapes, straight to pointed."): the straight finger's card, then each card
  of the tapered tips' family (`card_record()`: one per finger shape, its
  axes, grid, picture's sensor and two lines).  It also holds the deny-list (vendor models that never go into
  the Library, by SHA-256 and name; since the user's word of 2026-11-17, "xarm原装夹爪", its names let the
  xArm Gripper card's alone pass, MuJoCo Menagerie's BSD-3-Clause `ufactory_xarm7`), the one the private importer takes;
  since the user's decision of 2026-11-16 ("Menagerie model") its name lets
  MuJoCo Menagerie's Robotiq 2F-85 (BSD-2-Clause) through, the user's own
  2F-85 file and every other Robotiq model still refused; and since 2026-11-16 the sources
  that state no licence, taken only through a dated entry, its rows `NOASSERTION` with the project's note
  and, since the review of 2026-11-17, the credit of the SO-ARM100 part each file is remodelled
  from with its Apache-2.0 text (`remodelled()`): `PENDING_LICENCES`, an entry pending its authors' word
  (none now; `pending_note()` is the site build's warning for their sensors), and `PERMITTED_LICENCES`,
  an entry shared with its authors' permission (LeFlexiTac's two STL downloads, by a co-author's word of
  2026-11-17: its rows and its part's licence say `permission()`, dated; an entry without its day and who gave
  it is no permission); `unlicensed()` is the files the
  site build and the public export refuse, every such file but a permitted entry's).
  (`parts.json` was written once by a private importer from the
  multi-gripper video's recipes, and is edited by hand since, a new gripper
  imported with `--only <part>` beside it (the LeFlexiTac, 2026-11-16, its
  recipe the importer's own since the review of 2026-11-17, its mesh the
  Library's copy where the source tree holds no download); the tapered
  tips' parts and meshes come from a private cutting tool, which needs
  trimesh and manifold3d; the grippers' scenes and bodies from a private
  scene builder, `tools/library_scenes.py`, which needs numpy and trimesh
  (and scipy for the Unitree Dex3-1's fingertip hull)
  and fills `scenes.json`'s `scenes` map, never its rules.  Since
  2026-11-17 the AgileX Piper's part, `agilex-piper`, is added by hand
  (its finger menagerie `agilex_piper`'s `link7.stl` unchanged); the scene
  builder stages it from `piper.xml`, squaring its quats' quarter turns;
  since 2026-11-17 it also builds the Galaxea R1 Lite's from GalaxeaManipSim at `abe7f51`,
  Apache-2.0 (its `NOTICE` pinned beside the licence since the review of
  2026-11-17): `--only galaxea-r1-lite`, then `library_split.py`, gives the
  committed files again; since the Seeed
  reBot DevArm of 2026-11-17 it also writes that part's mesh,
  `meshes/seeed-rebot.stl`, the menagerie's finger with its contact face's
  pockets capped (`PART_MESHES`, checked against `parts.json`'s mesh), and,
  for a gripper no video recipe holds, the Rainbow RB-Y1 of 2026-11-17, its
  Library mesh too (`library_mesh()`, in `PART_MESHES` since the merge of
  that day): the pad in millimetres, its facets as the upstream file has
  them, checked by `--check` as the bodies are; since the
  OpenArm of 2026-11-17 it reads Collada files too, with a reader of its
  own (`dae_triangles()`: the visual scene's `<triangles>` under each
  node's `<matrix>`, any other primitive or transform refused, and since
  its review the same day a unit other than the metre or an up axis other
  than `Z_UP`: `dae_frame()`), a body
  taking of one its materials or its components above a height; since the YUBI
  Gripper of 2026-11-17 it also reads a flat AP214 assembly STEP's
  placements as text, `step_placements()`, and CATIA's ASCII STL; and
  since 2026-11-17 the LEAP Hand's Library mesh is in `PART_MESHES` too
  (one table since the merge of that day): its white fingertip, menagerie
  `leap_hand`'s `distal.obj`'s OBJ object
  `fingertip_W` alone (a body's `object` draws a file's other object); it
  poses the hand with `hinge_turn()` and writes its matrices rounded
  so that they stay orthonormal (`snap()`'s `squared_off()`).  The Allegro
  Hand's builder, `allegro()`, went with that hand at the user's word of
  2026-11-17: restore it from `bff728c`.  The Unitree Dex3-1's, `dex3()`
  with `dex3_links()`, `dex3_components()` and `dex3_tip()` (its Library
  mesh, the fingertip's cap replaced by its mirror-symmetric hull: scipy's
  `ConvexHull`), went too and came back from `bff728c` with the hand on
  2026-11-18, its face's normal and centre the dome's stretch patch's and
  its card override 19 px: `--only unitree-dex3`, then `library_split.py`,
  gives the committed files again.)  Since the three hands of 2026-11-17 (a sensor on every
  finger; one mechanism since their merge, docs/LIBRARY_VIEW.md "Hands: a
  sensor on every finger"; the LEAP Hand alone since the Allegro Hand and
  the Unitree Dex3-1 were removed that day, the Dex3-1 again since
  2026-11-18) `scenes()` also takes a scene's `extra_fingers` (1 to
  4 rigid `{kind, matrix}`, the kind the determinant's sign: the part
  drawn again with a still stack, measured), a body's finger `extra<k>`
  (a further finger's own link, k 1 to their count) and, in a hand's
  scene alone, its own `checks` override (`card_min_px` within 12 to 20,
  its reason in `about`); a record of a hand's stage carries `extra_seen`
  (its further stacks' top FPCs seen, held to `near_seen_min`) and is held
  to the rules' checks with that override over them (`scene_checks()`, the
  shots tool's too).  BSD-2-Clause is an open licence (the Robotiq 2F-85's,
  MuJoCo Menagerie's `robotiq_2f85`), and `compose()` refuses a border the page refuses
  before it fits (`border_problem()`: border.js `validate()`, simple, no
  edge under 0.001 mm, 1 mm2, counter-clockwise, and runFit's exit of 3
  mm and 2048 corners at most; the Allegro Hand's border, removed since,
  had run clockwise, which the server fits).
- `library_split.py`: gives each Library gripper its looks (the user's
  request of 2026-11-12: every gripper coloured after photos of the real
  product; `docs/LIBRARY_VIEW.md`, "The looks").  One look file per part,
  `library_looks/<part>.json`, names the look of each body of the part's
  scene, or shares a body out into components by rule (a connected
  component after welding at 0.01 mm, recognised by its box and triangle
  count; the triangles inside a box; the rest) or draws a plain shape the
  model lacks (a box, a cylinder, or a prism: a convex profile drawn along
  an axis, as the MakerMods Metal Arm's body drawn by eye after the maker's
  photos, 2026-11-14; the Galaxea R1 Lite's gripper link shared by a box
  into its motor can and plate, 2026-11-17, and since its review that day
  boxes in the carriage's black over the carriage and rack its finger's
  mesh holds); `library_looks/base.json` holds the base looks every part
  starts from.  It writes `web/library/bodies/<part>/<component>.stl`, the
  scene's bodies, `looks`, `part_look` and `smooth_deg`, and the bodies'
  rows of `NOTICE.md`; the same input gives the same bytes, from the
  unsplit body (its SHA-256 pinned) or from its components (their facets'
  hash pinned; an unsplit file of other bytes is refused).  `--check` proves
  the committed files are what the look files give and that no scene has
  a look, a crease angle or a drawn body without a look file (the
  showcase's scene has its looks and its drawn shapes from
  `library_showcase.py`, each shape pinned in `library_write.py`)
  (`tests/test_library_split.py` runs it); `--pin` and
  `--components` help write a look file; `--out` is a dry run.  Standard
  library only.  A part without a look file is not touched.  After it:
  `library_write.py`, the shoot of that part, `library_write.py` again.
- `library_showcase.py`: builds the Library's showcase (the project
  owner's decision of 2026-11-12: the hand-designed FlexiTac sensor on
  UFACTORY's xArm Gripper G1 with UMI soft fingers): the vendor's 3D model
  `Gripper G1 3D File (With).stl` split as the FlexiTac Tactile Demo splits
  it (the shell, the frame, the flange, the pivot pins, the four links, each
  finger's coupler, cut where the UMI holder sits, and its pins) and each
  piece decimated to within 0.1 mm, into `web/vendor/ufactory-g1/` (twelve
  binary STL in millimetres whose headers say what was changed); HandUMI's
  finger holder, decimated the same way, into
  `web/library/bodies/flexitac-g1/`; beside it seven plain shapes the
  project draws where the owner's photo of the gripper shows them, or the
  model has their wells (`drawn-<name>.stl`, `library_split.py`'s boxes
  and cylinders, no vendor's geometry: a shell screw's head, a holder
  bolt's head and nut, the black block in the shell's top slot, and behind
  each finger the extender board laid along the pad's tails, its two
  sockets round the tails' ends and a stub of the flat cable), drawn again
  on every run; and the showcase's scene,
  `web/library/scenes/flexitac-g1.json`, the gripper at the Tactile Demo's
  pose (the sensors' centres 55 mm apart) about the Library's UMI finger as
  its left finger (the pad's straps toward the shell's face without the
  logo, as built), each body in a base look or one of the showcase's own
  (the shell's gloss white, the printed parts' white, the pins' brushed
  steel, the screws' matte black, the fingers' orange TPU, the UMI rows'
  own `umi-tpu-orange`, the boards' yellow, the cables' white),
  chosen after photos of the real gripper and judged from both sides of
  it, at the rules' camera (the grippers' homes, since 2026-11-16) with its
  near finger see-through as every gripper's (since the review of that
  day).  The sources are read
  from a folder given on the command line (`--sources DIR`) and never
  copied; a file that is not the pinned one (by SHA-256) is refused.  Every
  mesh it writes and every shape it draws is pinned by SHA-256 in
  `library_write.py`, so `--check` proves the committed files without the
  sources (and with `--sources`, that the sources build them byte for
  byte); a build of other bytes writes nothing without `--repin`;
  `--notice` prints the notices' rows.  After a change of the scene, shoot
  the showcase's pictures again (`browser/library_shots.py --showcase`):
  `--check` reports them stale until then.  The
  guards are `library_write.py`'s `showcase()`: the vendor's folder holds
  exactly those files at those hashes and its notice, within a byte budget
  of its own; the notice says whose the model is; only the showcase's scene
  names the folder (no part, entry, fit, sample or other scene); the
  vendor's own file, unsplit and undecimated (under any header), its
  undecimated pieces (the deny-list) and a copy of one of the folder's
  meshes anywhere else are refused under `web/`; and `showcase_page()`,
  the showcase's page's document (`web/library/showcase.json`: its words,
  its placed record, its three pictures in `web/library/showcase/` and
  what they were shot from, the stage's numbers of that shoot within the
  rules' checks and the showcase's own bounds; `docs/LIBRARY_VIEW.md`).
  Standard library only, public.
- `mesh_decimate.py`: the decimation the showcase's meshes are made with,
  in the standard library and to the same bytes on every run and Python:
  quadric error metrics with half-edge collapses (a vertex moves onto a
  neighbour, so every vertex kept is a vertex of the input), the cheapest
  first, none past the tolerance, across an open or non-manifold edge, or
  turning a face more than 15 degrees; then the gate: the two-way deviation
  is measured (the exact distance from every vertex, edge middle, triangle
  centre and a grid about 0.5 mm apart on each surface to the other) and,
  where it exceeds the tolerance, the longest prefix of the collapses
  within it is kept.  `python3 tools/mesh_decimate.py in.stl out.stl
  --tolerance 0.1`.  `tests/test_mesh_decimate.py` pins the bytes of small
  fixtures.
- `flexitac_v2.py`: the original, hand-designed FlexiTac sensor (FlexiTac
  V2, 12 x 32 taxels at 2 mm) as data, for the Library's showcase (the
  user's request of 2026-11-12): it reads the two Gerber ZIPs of the
  FlexiTac hardware tutorial from a folder given on the command line (never
  committed; read in memory, run it with `python3 -I`) into
  `web/vendor/flexitac-v2/geometry.json`: each FPC's outline, the slots
  between its electrodes and the window of the A-shaped tail, its
  electrodes, traces, gold fingers, coverlay openings and stiffeners, every
  length as the Gerber writes it.  The ZIPs' SHA-256s and the JSON's are
  pinned: `--check` says whether the committed file is the pinned one and,
  with the folder, whether the ZIPs give it again.  `engine_boards()` gives
  the two boards in the engine's layout mapping for its SVG writer
  (`browser/flexitac_v2_art.py` makes the showcase's art from them), with
  the 0.2 mm stiffeners under the gold ends only: the 0.1 mm ones would be
  painted as a connector's dark stiffener where the real pad is amber.  The
  geometry and the art are CC BY-NC 4.0 material of Columbia University
  (`web/vendor/flexitac-v2/NOTICE.md`), not Apache-2.0.  (Since 2026-11-17
  the two ZIPs are served in that folder too, unchanged, for the showcase's
  window: `flexitac_downloads.py` below.)
- `flexitac_downloads.py`: the FlexiTac hardware's own order files that the
  site serves (the user's request of 2026-11-17: the original pad's FPC
  Gerbers downloadable in the showcase's window; every sensor's window and
  Gen's step 3 "Ordering and fabrication" and its reading board): the two
  FPC Gerber ZIPs unchanged in `web/vendor/flexitac-v2/` and one ZIP per
  reading board in `web/vendor/flexitac-reader/`
  (`FlexiTac_reading_board_32x16.zip`, 50,257 bytes, and `_32x32.zip`,
  92,579 bytes), each holding that board's Gerber ZIP, BOM and
  pick-and-place file unchanged (the user's three; not the schematic),
  stored in name order with the engine's fixed ZIP metadata.  Every file,
  each bundle and each bundle's member are pinned by SHA-256 and size;
  `python3 -I tools/flexitac_downloads.py DIR` writes them from the guide's
  files under their own names (read as bytes, never extracted or run),
  `--check` re-derives each bundle from the members it holds and compares
  the served bytes, and the two folders' budgets (160 kB each); `--check
  DIR` checks the sources too.  The site build runs the same check on the
  published copy and records the four files' SHA-256s in `BUILD.json`
  (`hardware`).  The rule naming a sensor's board lives in `web/boards.js`
  (the larger of rows and columns at most 32 and the smaller at most 16:
  32 x 16; the larger at most 32: 32 x 32; else none), with, for Gen's
  step 3, the board a design's tails plug into (`tailsBoard`, the review of
  2026-11-17: tails sized to a reader's connectors take the board with
  those connectors, 16 and 32 pins or 32 and 32, else none).
  `tests/test_flexitac_downloads.py` checks the files, the tool, the notices,
  the rule under node (against `surface/reader.py`'s readers and the
  boards' BOMs) and the pages.  Standard library only, public.
  `tests/test_showcase.py` checks the file, the reader, the boards, the art
  and the placed record ([docs/LIBRARY_VIEW.md](../docs/LIBRARY_VIEW.md),
  "A placed sensor").
- `browser/`: Playwright checks of the browser UI (their own virtual
  environment; see `browser/README.md`).
