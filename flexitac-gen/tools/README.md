# Development tools

None of these is part of the unittest suite, and none writes into the
project.

- `mutation_check.py`: applies known defects to scratch copies of the
  project and runs the suite on each; every mutant must be killed unless the
  catalogue marks it as equivalent or out of scope (with the reason).  The
  catalogue holds the 2026-10-12 audit's 36 baseline mutants and the C1
  extras re-expressed for the current code, mutants of every fix stage and
  mutants of the figures and tables the documents quote.  Each copy has the
  CI workflow beside it, as at the repository root, because a document test
  reads it.  `--check` only verifies that every edit still applies (CI runs
  it, and the suite's `test_every_catalogue_edit_still_applies` checks the
  same); `--list` prints the catalogue; `--only audit/ T/` selects by id
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
  (or `--pyodide-archive FILE`) and checked by their SHA-256; it replaces an
  output folder only when an earlier build wrote it.  See the README, "As a
  static website".
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
- `browser/`: Playwright checks of the browser UI (their own virtual
  environment; see `browser/README.md`).
