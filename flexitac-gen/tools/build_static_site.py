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
    .nojekyll                  GitHub Pages serves the files as they are
    static/                    web/ (the page's scripts, styles and vendored files), as app.py serves it
    static/py/engine.zip       app.py, engine/, exporters/, surface/, profiles/ and bridge.py (byte-reproducible)
    static/py/pyodide/         the Pyodide core files the worker loads, from the pinned release
    static/py/BUILD.json       versions and SHA-256s of the above

Every URL in the page is relative, so the site works under any path (https://<org>.github.io/<repo>/).  An
existing output folder is replaced only when an earlier build wrote it (it holds BUILD_MARKER).
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import shutil
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import app  # noqa: E402
from engine import GENERATOR_VERSION  # noqa: E402

WEB = ROOT / "web"
PYODIDE_VERSION = "0.27.8"
PYODIDE_URL = f"https://github.com/pyodide/pyodide/releases/download/{PYODIDE_VERSION}/pyodide-core-{PYODIDE_VERSION}.tar.bz2"
PYODIDE_SHA256 = "b7ed9d0eb44499578403d9c67935510f76c4534de3cac2fef03da4ac274ac294"
# What the worker loads: the loader, the interpreter, the standard library and the lock file (no packages are used).
PYODIDE_FILES = ("pyodide.js", "pyodide.asm.js", "pyodide.asm.wasm", "python_stdlib.zip", "pyodide-lock.json")
ENGINE_SOURCES = ("app.py", "engine", "exporters", "surface", "profiles")
BUILD_MARKER = ".flexitac-static-site"
# The server's policy (app.SECURITY_HEADERS) as a meta tag, with WebAssembly allowed and GitHub's API for the header's
# star and fork counts (web/backend.js; app.py's page asks nothing of other hosts).
GITHUB_REPO = "FlexiTac/FlexiTac"
GITHUB_API = f"https://api.github.com/repos/{GITHUB_REPO}"
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


def github_counts(timeout: float = 15) -> dict | None:
    """The FlexiTac repository's stars and forks from GitHub's API, or None (offline, rate-limited, anything else).
    GITHUB_TOKEN, when set (the site's workflow), raises the hourly limit; the request is read-only either way."""

    headers = {"Accept": "application/vnd.github+json", "User-Agent": "flexitac-gen-site-build"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    request = urllib.request.Request(GITHUB_API, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as reply:
            data = json.loads(reply.read())
        stars, forks = data["stargazers_count"], data["forks_count"]
    except Exception:  # noqa: BLE001 - the counts are optional: the page shows the name alone
        return None
    return {"stars": stars, "forks": forks} if isinstance(stars, int) and isinstance(forks, int) else None


def count_text(number: int) -> str:
    """As web/backend.js writes it: 1.2k from a thousand, 12k from ten thousand."""

    if number < 1000:
        return str(number)
    text = f"{number / 1000:.{0 if number >= 10000 else 1}f}"
    return (text[:-2] if text.endswith(".0") else text) + "k"


def page(counts: dict | None = None) -> str:
    """web/index.html with the site's head tags and, given, the repository's counts in the header's GitHub card."""

    text = (WEB / "index.html").read_text(encoding="utf-8")
    if text.count(HEAD_ANCHOR) != 1:
        raise BuildError("web/index.html: the charset meta tag the site's head tags follow was not found once")
    text = text.replace(HEAD_ANCHOR, HEAD_ANCHOR + HEAD_TAGS, 1)
    if counts:
        fills = (
            ("<span data-gh-stars></span>", f"<span data-gh-stars>{count_text(counts['stars'])}</span>"),
            ("<span data-gh-forks></span>", f"<span data-gh-forks>{count_text(counts['forks'])}</span>"),
            ("data-gh-stats hidden>", "data-gh-stats>"),
            ('aria-label="FlexiTac on GitHub" data-gh-badge>', f'aria-label="FlexiTac on GitHub: {counts["stars"]} stars, {counts["forks"]} forks" data-gh-badge>'),
        )
        for old, new in fills:
            if text.count(old) != 1:
                raise BuildError(f"web/index.html: the GitHub card's {old!r} was not found once")
            text = text.replace(old, new)
    return text


def prepare(out: Path) -> None:
    if out.exists():
        if not out.is_dir():
            raise BuildError(f"{out} is not a folder")
        if any(out.iterdir()):
            if not (out / BUILD_MARKER).is_file():
                raise BuildError(f"{out} is not empty and was not written by this tool ({BUILD_MARKER} is missing); choose another --out")
            shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)


def build(out: Path, archive: Path | None = None, github: bool = True) -> dict:
    pyodide = pyodide_files(pyodide_archive(archive))
    engine = engine_zip()
    counts = github_counts() if github else None
    prepare(out)
    (out / BUILD_MARKER).write_text("Written by tools/build_static_site.py; the next build replaces this folder.\n", encoding="utf-8")
    (out / ".nojekyll").write_bytes(b"")
    (out / "index.html").write_text(page(counts), encoding="utf-8")
    static = out / "static"
    shutil.copytree(WEB, static, ignore=shutil.ignore_patterns("index.html", "*.py", "__pycache__"))
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
    args = parser.parse_args(argv)
    try:
        record = build(args.out.resolve(), args.pyodide_archive, github=not args.no_github)
    except (BuildError, OSError) as error:
        print(f"build_static_site: {error}", file=sys.stderr)
        return 1
    size = sum(f.stat().st_size for f in args.out.rglob("*") if f.is_file())
    counts = record["github"]
    github = f"{counts['stars']} stars, {counts['forks']} forks" if counts else "counts left to the page"
    print(f"built {args.out} ({size / 1048576:.1f} MiB): generator {record['generator_version']}, "
          f"Pyodide {PYODIDE_VERSION}, engine.zip {record['engine_zip_sha256'][:12]}, GitHub {github}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
