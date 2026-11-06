# Development tools

None of these is part of the unittest suite, and none writes into the
project but `library_write.py` (the Library's data, `web/library/`) and
`browser/library_shots.py` (the Library's pictures, `web/library/shots/`,
and each sensor's art, `web/library/art/`).

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
  as a false alarm.  A full run takes about 17 minutes with `--jobs 16` on
  a 48-core host; in CI it is a manual job.
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
  API does not answer: the page refreshes them); it replaces an output
  folder only when an earlier build wrote it.  It writes `library.html`
  (the Library, 2026-11-05) with the same head tags and is the Library's
  gate: every sensor of `web/library/entries.json` is fitted again and must
  give its committed reply and build id, and its fit's request must still be
  the one the page sends (`library_write.compose` of `parts.json` and
  `index.html`'s defaults), else the build fails ("the library is stale: run
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
  `view` in `entries.json` that is not the manifest's stops the build, a
  picture with no 3D view yet is published with a warning, and
  `BUILD.json`'s library record counts the sensors viewed.
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
  nothing.
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
- `library_write.py`: fits the Library's sensors (`library.html`, and Gen
  by Surface at `./?part=<id>`; the user's requests of 2026-11-05) as the
  page asks for them: for each variant of `web/library/parts.json` the
  request the page sends (its selection, base and border, the Resolution
  step's defaults read from `web/index.html` with the variant's pitch and
  fill, the mesh's file name, no unit), `surface.api.fit`'s reply, and the
  product rules on its proposal #1 (one tail pin per line, field-only
  containment, the tails centred and ending together, a symmetric face's
  sensor centred, a build with no error or warning); a variant that breaks
  one is rejected and nothing is written.  It writes `web/library/fits/<id>.json`
  and `web/library/entries.json` (only what changed; the UMI finger's 2 mm
  sensor is `web/vendor/umi/default-fit.json`, checked only); `--only
  ID,...` fits some, `--check` writes nothing and exits 1 listing the stale
  ids.  About 10 s for the 42 sensors with `--jobs 8`; re-run it after any
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
  count and the range of its pitches and its families after it ("Four
  pitches, 1 to 3 mm, and tapered tips."; the user's decision of
  2026-11-05); since 2026-11-06 the page shows the UMI finger's alone,
  after the other grippers' cards, one each.  It also holds the deny-list (vendor models that never go into
  the Library, by SHA-256 and name), the one the private importer takes.
  (`parts.json` was written once by a private importer from the
  multi-gripper video's recipes, and is edited by hand since; the tapered
  tips' parts and meshes come from a private cutting tool, which needs
  trimesh and manifold3d; the grippers' scenes and bodies from a private
  scene builder, `tools/library_scenes.py`, which needs numpy and trimesh
  and fills `scenes.json`'s `scenes` map, never its rules.)
- `browser/`: Playwright checks of the browser UI (their own virtual
  environment; see `browser/README.md`).
