#!/usr/bin/env python3
"""Write the public part of the project into a clone of FlexiTac/FlexiTac, from a commit.

    python3 tools/export_public.py --repo ../FlexiTac              # HEAD into ../FlexiTac/flexitac-gen/
    python3 tools/export_public.py --repo ../FlexiTac --rev HEAD~1

The public part (PUBLIC) is the generator, its page, documents, tests and tools, with the development handoff and the
audit files it links to; the other development notes (claude/sessions, claude/specs), the large assets (asset/),
outputs and the video tools stay out.  Only committed files are written (git archive of the commit), so uncommitted work never leaves.  The
folder flexitac-gen/ is replaced as a whole (only when an earlier export wrote it: it holds SOURCE_COMMIT), and
.github/workflows/flexitac-gen.yml (tools/public/pages-workflow.yml) tests the copy, builds the static site and
publishes it to https://flexitac.github.io/flexitac-gen/.  Nothing is committed or pushed: review, commit and push
the clone yourself.
"""
from __future__ import annotations

import argparse
import io
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = "flexitac-gen"
WORKFLOW = ".github/workflows/flexitac-gen.yml"
MARKER = "SOURCE_COMMIT"
PUBLIC = (
    "LICENSE", "README.md", "pyproject.toml", ".gitignore", "app.py", "cli.py",
    "engine", "exporters", "surface", "profiles", "web", "docs", "tests", "outputs/.gitkeep",
    # The development documents the public documents link to (and the suite checks).
    "claude/APP_HANDOFF.md", "claude/verification",
    "tools/README.md", "tools/build_static_site.py", "tools/export_public.py", "tools/public",
    "tools/mutation_check.py", "tools/golden_values.py", "tools/compare_easyeda_gerbers.py", "tools/browser",
)


class ExportError(Exception):
    pass


def git(source: Path, *args: str) -> bytes:
    done = subprocess.run(["git", "-C", str(source), *args], capture_output=True)
    if done.returncode != 0:
        raise ExportError(f"git {' '.join(args)}: {done.stderr.decode(errors='replace').strip()}")
    return done.stdout


def export(repo: Path, rev: str = "HEAD", source: Path = ROOT) -> str:
    """Write the public files of ``source`` (this project) at ``rev`` into ``repo``/flexitac-gen and the workflow;
    the commit's SHA."""

    if not (repo / ".git").exists():
        raise ExportError(f"{repo} is not a git clone (of FlexiTac/FlexiTac)")
    commit = git(source, "rev-parse", "--verify", f"{rev}^{{commit}}").decode().strip()
    prefix = git(source, "rev-parse", "--show-prefix").decode().strip()
    # From the top level: git archive reads the paths in the commit's tree of this folder.
    top = Path(git(source, "rev-parse", "--show-toplevel").decode().strip())
    archive = git(top, "archive", "--format=tar", f"{commit}:{prefix}", *PUBLIC)
    target = repo / FOLDER
    if target.exists():
        if not (target / MARKER).is_file():
            raise ExportError(f"{target} exists and was not written by this tool ({MARKER} is missing)")
        shutil.rmtree(target)
    target.mkdir()
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        for member in tar.getmembers():
            name = Path(member.name)
            if name.is_absolute() or ".." in name.parts or not (member.isfile() or member.isdir()):
                raise ExportError(f"unexpected archive member {member.name!r}")
            path = target / name
            if member.isdir():
                path.mkdir(parents=True, exist_ok=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(tar.extractfile(member).read())
                if member.mode & 0o111:
                    path.chmod(0o755)
    (target / MARKER).write_text(f"{commit}\n", encoding="utf-8")
    workflow = repo / WORKFLOW
    workflow.parent.mkdir(parents=True, exist_ok=True)
    workflow.write_bytes((target / "tools" / "public" / "pages-workflow.yml").read_bytes())
    return commit


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--repo", type=Path, required=True, help="a clone of FlexiTac/FlexiTac")
    parser.add_argument("--rev", default="HEAD", help="the commit to export (default HEAD)")
    args = parser.parse_args(argv)
    try:
        commit = export(args.repo.resolve(), args.rev)
    except (ExportError, OSError) as error:
        print(f"export_public: {error}", file=sys.stderr)
        return 1
    print(f"wrote {args.repo / FOLDER} and {args.repo / WORKFLOW} from {commit[:12]}; review, commit and push them yourself")
    return 0


if __name__ == "__main__":
    sys.exit(main())
