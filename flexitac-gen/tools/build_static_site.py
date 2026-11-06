#!/usr/bin/env python3
"""Build the static site: the whole app as plain files, for GitHub Pages or any static host.

The page is web/index.html; its API is answered in the visitor's browser, by app.py itself running in Pyodide
(CPython compiled to WebAssembly) in a Web Worker (web/backend.js, web/py/worker.js, web/py/bridge.py), so the
site needs no server and no design or mesh leaves the visitor's computer.  The answers are app.answer's: the same
replies, build ids and file bytes as app.py's (tools/browser/static_checks.py compares them).

    python3 tools/build_static_site.py --out site/            # downloads Pyodide, checks its SHA-256
    python3 tools/build_static_site.py --out site/ --pyodide-archive pyodide-core-0.27.8.tar.bz2

The output:

    index.html                 web/index.html, with a Content-Security-Policy meta and the browser-backend flag, and the
                               FlexiTac repository's star and fork counts from GitHub's API (none with --no-github or
                               when it does not answer; the page refreshes them, web/backend.js)
    library.html               web/library.html (the Library, 2026-11-05), with the same head tags and counts (it loads
                               no backend.js: its counts are the build's)
    .nojekyll                  GitHub Pages serves the files as they are
    static/                    web/ (the page's scripts, styles and vendored files), as app.py serves it
    static/library/files/      each Library sensor's Top and Bottom FPC Gerber ZIPs, app.answer's exports of its design
    static/library/files.json  their names, sizes, SHA-256s and build ids (library.html links them)
    static/library/shots/      the sensors' pictures (web/library/shots/, tools/browser/library_shots.py), with web/
    static/library/art/, scenes/, bodies/
                               each sensor's 3D view: its boards' art, the grippers' scenes and their bodies (web/library/,
                               docs/LIBRARY_VIEW.md), with web/
    static/py/engine.zip      app.py, engine/, exporters/, surface/, profiles/ and bridge.py (byte-reproducible)
    static/py/pyodide/         the Pyodide core files the worker loads, from the pinned release
    static/py/BUILD.json       versions and SHA-256s of the above

Every URL in the page is relative, so the site works under any path (https://<org>.github.io/<repo>/).  An
existing output folder is replaced only when an earlier build wrote it (it holds BUILD_MARKER).

The Library's gate: every sensor of web/library/entries.json is fitted again (surface.api.fit of its fit's request)
and must give the committed reply with the entry's build id, and that request must still be the one the page sends
(library_write.compose of parts.json and index.html's defaults: else Gen by Surface would fit it again in place of
the shipped fit, while the Library offered the old build's ZIPs), else the build fails ("the library is stale: run
tools/library_write.py") and nothing is published; then its two Gerber ZIPs are built (the gate with its 84 ZIPs about
11 s for the 42 sensors with --jobs 8, in parallel processes; about 40 s in one).  The ZIPs are deterministic: an
unchanged library rebuilds the same bytes.  Its pictures (shots/manifest.json, library_write.pictures) are checked
first: a picture of another fit (the wrong sensor pictured), a broken file or an "image" in entries.json that is not
its shot's fails the build too; a picture of older figure sources is published with a warning (re-shoot it with
tools/browser/library_shots.py: this build runs no browser).  So are each sensor's 3D view (the user's request of
2026-11-05, docs/LIBRARY_VIEW.md): an art or a gripper's stage that is not the sensor's own, a "view" in entries.json
that is not the one the manifest gives, or a gripper's scene that library_write.scenes refuses fails the build; a
picture with no 3D view yet (before the shoot that writes every sensor's art) is published with a warning, its page
showing the picture only.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import shutil
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import app  # noqa: E402
from engine import GENERATOR_VERSION, BuildCache  # noqa: E402

WEB = ROOT / "web"
# The two pages: the generator and the Library (2026-11-05); every other file of web/ is copied under static/.
PAGES = ("index.html", "library.html")
LIBRARY_FILES_FORMAT = "flexitac-library-files/v1"
LIBRARY_KINDS = ("top-gerber", "bottom-gerber")
PYODIDE_VERSION = "0.27.8"
PYODIDE_URL = f"https://github.com/pyodide/pyodide/releases/download/{PYODIDE_VERSION}/pyodide-core-{PYODIDE_VERSION}.tar.bz2"
PYODIDE_SHA256 = "b7ed9d0eb44499578403d9c67935510f76c4534de3cac2fef03da4ac274ac294"
# What the worker loads: the loader, the interpreter, the standard library and the lock file (no packages are used).
PYODIDE_FILES = ("pyodide.js", "pyodide.asm.js", "pyodide.asm.wasm", "python_stdlib.zip", "pyodide-lock.json")
ENGINE_SOURCES = ("app.py", "engine", "exporters", "surface", "profiles")
BUILD_MARKER = ".flexitac-static-site"
# The server's policy (app.SECURITY_HEADERS) as a meta tag, with WebAssembly allowed and GitHub's API for the header's
# star and fork counts (web/backend.js refreshes them here; app.py's page is served with them and asks no other host).
GITHUB_REPO = app.GITHUB_REPO
GITHUB_API = app.GITHUB_API
CSP = dict(app.SECURITY_HEADERS)["Content-Security-Policy"].replace(
    "default-src 'self';", "default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; connect-src 'self' https://api.github.com;", 1)
HEAD_ANCHOR = '    <meta charset="utf-8" />\n'
HEAD_TAGS = (
    f'    <meta http-equiv="Content-Security-Policy" content="{CSP}" />\n'
    '    <meta name="referrer" content="no-referrer" />\n'
    '    <meta name="flexitac-backend" content="browser" />\n'
)
ZIP_TIME = (1980, 1, 1, 0, 0, 0)


class BuildError(Exception):
    pass


def pyodide_archive(path: Path | None) -> bytes:
    """The pinned Pyodide core archive (a local copy or the release download), checked by its SHA-256."""

    if path is None:
        print(f"downloading {PYODIDE_URL}", flush=True)
        with urllib.request.urlopen(PYODIDE_URL, timeout=120) as reply:
            data = reply.read()
    else:
        data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != PYODIDE_SHA256:
        raise BuildError(f"the Pyodide archive's SHA-256 is {digest}, not the pinned {PYODIDE_SHA256} (pyodide-core-{PYODIDE_VERSION})")
    return data


def pyodide_files(archive: bytes) -> dict[str, bytes]:
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:bz2") as tar:
        files = {}
        for name in PYODIDE_FILES:
            member = tar.extractfile(f"pyodide/{name}")
            if member is None:
                raise BuildError(f"pyodide/{name} is missing from the archive")
            files[name] = member.read()
    return files


def engine_zip() -> bytes:
    """app.py and the packages it imports, plus the worker's bridge.py, with fixed dates: the same sources give the same bytes."""

    entries = []
    for source in ENGINE_SOURCES:
        path = ROOT / source
        files = [path] if path.is_file() else sorted(f for f in path.rglob("*") if f.is_file() and "__pycache__" not in f.parts and f.suffix != ".pyc")
        entries += [(f.relative_to(ROOT).as_posix(), f) for f in files]
    entries.append(("bridge.py", WEB / "py" / "bridge.py"))
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, path in sorted(entries):
            info = zipfile.ZipInfo(name, ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())
    return buffer.getvalue()


# The counts as app.py reads and writes them for its own page; the build sends GITHUB_TOKEN when set (the site's workflow).
count_text = app.count_text


def github_counts(timeout: float = 15) -> dict | None:
    return app.github_counts(timeout, token=os.environ.get("GITHUB_TOKEN"))


def page(counts: dict | None = None, name: str = "index.html") -> str:
    """A page of web/ (index.html, or library.html) with the site's head tags and, given, the repository's counts in the
    header's GitHub card (the two pages share the header)."""

    text = (WEB / name).read_text(encoding="utf-8")
    if text.count(HEAD_ANCHOR) != 1:
        raise BuildError(f"web/{name}: the charset meta tag the site's head tags follow was not found once")
    text = text.replace(HEAD_ANCHOR, HEAD_ANCHOR + HEAD_TAGS, 1)
    if counts:
        try:
            text = app.fill_github_counts(text, counts)
        except ValueError as error:
            raise BuildError(f"web/{name}: {error}") from None
    return text


def copy_web(static: Path) -> None:
    """web/ under static/ as app.py serves it: not the pages (the site's own, with its head tags), no Python."""

    shutil.copytree(WEB, static, ignore=shutil.ignore_patterns(*PAGES, "*.py", "__pycache__"))


def _library_write():
    """tools/library_write.py (the request the page sends, the fit), imported from beside this file."""

    if str(ROOT / "tools") not in sys.path:
        sys.path.insert(0, str(ROOT / "tools"))
    import library_write

    return library_write


def _library_job(job: tuple) -> tuple:
    """One Library sensor: (id, its problem or None, {kind: (name, ZIP bytes)}): fitted again, compared with the
    committed reply, then its two Gerber ZIPs exported by app.answer (a worker process's job)."""

    identifier, variant, fit_path, mesh_path, mesh_sha256, sent = job
    library_write = _library_write()
    stale = f"the library is stale ({identifier}): run tools/library_write.py"
    data = Path(fit_path).read_bytes()
    mesh = Path(mesh_path).read_bytes()
    if hashlib.sha256(data).hexdigest() != variant["fit_sha256"]:
        return identifier, f"{stale} (its fit is not the one entries.json names)", {}
    document = json.loads(data.decode("utf-8"))
    if hashlib.sha256(mesh).hexdigest() != mesh_sha256 or document.get("mesh_sha256") != mesh_sha256:
        return identifier, f"{stale} (its mesh is not the one its fit was made of)", {}
    # The request the page sends now (``sent``, canonical): a fit of another request is not the page's shipped fit
    # (the review of 2026-11-05: a changed page default passed the gate while library_write --check flagged it).
    if library_write.canonical(document["request"]) != sent:
        return identifier, f"{stale} (its request is not the one the page sends)", {}
    reply = library_write.fit(document["request"], mesh)
    proposals = document["reply"].get("proposals") or []
    if reply != document["reply"] or not proposals or proposals[0]["build_id"] != variant["build_id"]:
        return identifier, stale, {}
    design = json.dumps(proposals[0]["design"], ensure_ascii=True, allow_nan=False).encode("ascii")
    cache = BuildCache(2)  # the two exports of one build
    files = {}
    for kind in LIBRARY_KINDS:
        answer = app.answer("POST", f"/api/export/{kind}", "application/json", design, cache=cache)
        headers = dict(answer.headers)
        name = re.fullmatch(r'attachment; filename="([^"/\\]+)"', headers.get("Content-Disposition", ""))
        if answer.status != 200 or headers.get("X-Build-Id") != variant["build_id"] or not name:
            return identifier, f"{identifier}: the {kind} export answered {answer.status} for build {headers.get('X-Build-Id')}, not {variant['build_id']}", {}
        files[kind] = (name.group(1), answer.body)
    return identifier, None, files


def library(static: Path, source: Path = WEB / "library", only=None, jobs: int = 1, index: Path = WEB / "index.html") -> dict:
    """The Library's gate and downloads: every sensor of ``source``/entries.json (or the ids ``only``) fitted again,
    its reply the committed one and its request the one the page (``index``) sends (else BuildError, the library is
    stale), and its Top and Bottom FPC Gerber ZIPs written to ``static``/library/files/<id>/<the exporter's name> with
    files.json; returns BUILD.json's record of it."""

    library_write = _library_write()
    entries = json.loads((source / "entries.json").read_text(encoding="utf-8"))
    chosen = list(entries["variants"]) if only is None else list(only)
    unknown = [identifier for identifier in chosen if identifier not in entries["variants"]]
    if unknown:
        raise BuildError(f"the library has no sensor named {', '.join(unknown)}")
    # Each sensor's request as the page sends it now: parts.json's setup and variant over index.html's defaults.
    options = library_write.page_options(index.read_text(encoding="utf-8"))
    parts = json.loads((source / "parts.json").read_text(encoding="utf-8"))
    try:
        sent = {identifier: library_write.canonical(library_write.compose(part, variant, options))
                for identifier, _, part, variant in library_write.plan(parts)}
    except library_write.LibraryError as error:
        # A setup the page would send otherwise (compose refuses it): the writer says the same.
        raise BuildError(f"the library is stale ({error}): run tools/library_write.py") from error
    missing = [identifier for identifier in chosen if identifier not in sent]
    if missing:
        raise BuildError(f"the library is stale ({', '.join(missing)}: not in parts.json): run tools/library_write.py")
    # The pictures (shots/, tools/browser/library_shots.py; the user's request of 2026-11-05: the cards show the sensor
    # on its part): none of another fit (the wrong sensor pictured) or broken, each sensor's "image" the one its shot
    # gives (null without one), else the build fails; a shot of older figure sources is published with a warning only
    # (this build runs no browser to shoot it again).  copy_web publishes shots/ with the rest of web/.
    images, unpictured, older, views = library_write.pictures(entries["variants"], source)
    unpictured = [problem for identifier, problem in unpictured if identifier is None or identifier in chosen]
    if unpictured:
        raise BuildError(f"the library's pictures are stale ({'; '.join(unpictured)})")
    # The grippers' scenes the 3D view draws (scenes/, bodies/; library_write.scenes, the user's request of 2026-11-05):
    # those of the chosen sensors' parts, and the index's own, else the build fails (copy_web publishes them).
    shown = {entries["variants"][identifier]["part"] for identifier in chosen}
    _, unscened = library_write.scenes(parts, source)
    unscened = [problem for part, problem in unscened if part is None or part in shown]
    if unscened:
        raise BuildError(f"the library's scenes are stale ({'; '.join(unscened)})")
    unwritten = [identifier for identifier in chosen if entries["variants"][identifier].get("image") != images[identifier]]
    if unwritten:
        raise BuildError(f"the library is stale ({', '.join(unwritten)}: its image is not the one {library_write.SHOTS_MANIFEST} "
                         "gives): run tools/library_write.py")
    unwritten = [identifier for identifier in chosen if entries["variants"][identifier].get("view") != views[identifier]]
    if unwritten:
        raise BuildError(f"the library is stale ({', '.join(unwritten)}: its 3D view is not the one {library_write.SHOTS_MANIFEST} "
                         "gives): run tools/library_write.py")
    older = [identifier for identifier in older if identifier in chosen]
    if older:
        print(f"build_static_site: warning: {library_write.older_note(older)}", file=sys.stderr, flush=True)
    unviewed = [identifier for identifier in chosen if images[identifier] is not None and views[identifier] is None]
    if unviewed:
        print(f"build_static_site: warning: {library_write.view_note(unviewed)}", file=sys.stderr, flush=True)
    work = []
    for identifier in chosen:
        variant = entries["variants"][identifier]
        mesh = entries["parts"][variant["part"]]["mesh"]
        work.append((identifier, variant, str(source / variant["fit"]), str(source / mesh["file"]), mesh["sha256"], sent[identifier]))
    if jobs > 1 and len(work) > 1:
        with ProcessPoolExecutor(max_workers=jobs) as pool:
            results = list(pool.map(_library_job, work))
    else:
        results = [_library_job(job) for job in work]
    problems = [problem for _, problem, _ in results if problem]
    if problems:
        raise BuildError("; ".join(problems))
    folder = static / "library"
    records = {}
    for identifier, _, files in results:
        record = {"build_id": entries["variants"][identifier]["build_id"]}
        for kind, (name, data) in files.items():
            path = f"files/{identifier}/{name}"
            (folder / path).parent.mkdir(parents=True, exist_ok=True)
            (folder / path).write_bytes(data)
            record[kind] = {"path": path, "name": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        records[identifier] = record
    document = {"format": LIBRARY_FILES_FORMAT, "generator_version": GENERATOR_VERSION, "variants": records}
    text = json.dumps(document, indent=1, sort_keys=True, ensure_ascii=True) + "\n"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "files.json").write_text(text, encoding="utf-8")
    return {"variants": len(records), "files_json_sha256": hashlib.sha256(text.encode("ascii")).hexdigest(),
            "pictured": len([identifier for identifier in chosen if images[identifier]]),
            "viewed": len([identifier for identifier in chosen if views[identifier]])}


def prepare(out: Path) -> None:
    if out.exists():
        if not out.is_dir():
            raise BuildError(f"{out} is not a folder")
        if any(out.iterdir()):
            if not (out / BUILD_MARKER).is_file():
                raise BuildError(f"{out} is not empty and was not written by this tool ({BUILD_MARKER} is missing); choose another --out")
            shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)


def build(out: Path, archive: Path | None = None, github: bool = True, jobs: int = 1) -> dict:
    pyodide = pyodide_files(pyodide_archive(archive))
    engine = engine_zip()
    counts = github_counts() if github else None
    prepare(out)
    (out / BUILD_MARKER).write_text("Written by tools/build_static_site.py; the next build replaces this folder.\n", encoding="utf-8")
    (out / ".nojekyll").write_bytes(b"")
    for name in PAGES:
        (out / name).write_text(page(counts, name), encoding="utf-8")
    static = out / "static"
    copy_web(static)
    shelf = library(static, jobs=jobs)
    (static / "py" / "engine.zip").write_bytes(engine)
    folder = static / "py" / "pyodide"
    folder.mkdir()
    for name, data in pyodide.items():
        (folder / name).write_bytes(data)
    record = {
        "generator_version": GENERATOR_VERSION,
        "engine_zip_sha256": hashlib.sha256(engine).hexdigest(),
        # The header's counts as built (the page refreshes them); null when GitHub's API did not answer.
        "github": counts,
        # The Library's sensors, each fitted again and its Gerber ZIPs built (static/library/files.json), how many
        # pictured and how many with a 3D view (entries.json's image and view).
        "library": shelf,
        "pyodide": {"version": PYODIDE_VERSION, "archive": PYODIDE_URL, "archive_sha256": PYODIDE_SHA256,
                    "files": {name: hashlib.sha256(data).hexdigest() for name, data in pyodide.items()}},
    }
    (static / "py" / "BUILD.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    (folder / "NOTICE.md").write_text(
        f"# Pyodide {PYODIDE_VERSION}\n\nThe core files of the Pyodide release ({PYODIDE_URL}), unchanged; "
        "Mozilla Public License 2.0 (https://github.com/pyodide/pyodide/blob/main/LICENSE). "
        "CPython and its standard library: Python Software Foundation License.\n", encoding="utf-8")
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", type=Path, required=True, help="output folder (replaced when an earlier build wrote it)")
    parser.add_argument("--no-github", action="store_true", help="leave the header's star and fork counts to the page (no request to GitHub's API)")
    parser.add_argument("--pyodide-archive", type=Path, default=None,
                        help=f"a local pyodide-core-{PYODIDE_VERSION}.tar.bz2 (default: download it); checked by its SHA-256 either way")
    parser.add_argument("--jobs", type=int, default=max(1, min(8, os.cpu_count() or 1)), help="the Library's fits in parallel processes")
    args = parser.parse_args(argv)
    try:
        record = build(args.out.resolve(), args.pyodide_archive, github=not args.no_github, jobs=args.jobs)
    except (BuildError, OSError) as error:
        print(f"build_static_site: {error}", file=sys.stderr)
        return 1
    size = sum(f.stat().st_size for f in args.out.rglob("*") if f.is_file())
    counts = record["github"]
    github = f"{counts['stars']} stars, {counts['forks']} forks" if counts else "counts left to the page"
    print(f"built {args.out} ({size / 1048576:.1f} MiB): generator {record['generator_version']}, "
          f"Pyodide {PYODIDE_VERSION}, engine.zip {record['engine_zip_sha256'][:12]}, GitHub {github}, "
          f"the Library's {record['library']['variants']} sensors current, {record['library']['pictured']} pictured, "
          f"{record['library']['viewed']} with a 3D view")
    return 0


if __name__ == "__main__":
    sys.exit(main())
