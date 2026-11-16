"""The art of the original FlexiTac sensor for the Library's showcase: web/vendor/flexitac-v2/art.json.gz, a
flexitac-library-art/v1 document (docs/LIBRARY_VIEW.md) of the hand-designed FlexiTac V2 pad's two FPCs, drawn as a
generated sensor's boards are (the user's request of 2026-11-12: the original version at the top of the Library, shown
as hand-designed, not auto-generated).

    FPC_PORT=18801 /tmp/fpc-browser-venv/bin/python tools/browser/flexitac_v2_art.py            # write the art
    ... flexitac_v2_art.py --check                                                              # make it again, compare
    ... flexitac_v2_art.py --out /tmp/art.json.gz                                               # elsewhere

Against a running app.py (--port, else FPC_PORT) that serves this project, in headless Chromium, as
tools/browser/library_shots.py makes each generated sensor's art:
1. web/vendor/flexitac-v2/geometry.json (tools/flexitac_v2.py: the two FPCs read from the official Gerbers; its pinned
   SHA-256 is checked first) gives the two boards in the engine's layout mapping (flexitac_v2.engine_boards), and the
   engine's own SVG writer (engine/core.py _svg_for_board) draws each: the copper-side top view a generated board has,
   with the slots between the electrodes and the window of the A-shaped tail as its cut-outs;
2. the generator's page (gen.html#rect, index.html#rect until 2026-11-16, loaded anew) answers "fpc:board-art" {boards, px_per_mm, max_px} for them in
   its default look (Photo), as it answers for a build: each board's eight keys (its copper and polyimide sides as SVG
   documents, the look's styles inlined), to which the board's outline is added;
3. the document {format, id "flexitac-v2", build_id null (no build of the generator), look, px_per_mm, max_px, boards}
   is written by library_write.art_bytes() (canonical JSON, gzip with no name and time 0).
The same code gives the same document: --check makes it again and compares its canonical JSON's SHA-256 with the
committed file's (never the gzip bytes, which another zlib may write otherwise), writing nothing.  The art is CC BY-NC
4.0 material (web/vendor/flexitac-v2/NOTICE.md: its row's SHA-256 is the file's).  Needs Playwright.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # no __pycache__ next to the scripts
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import flexitac_v2  # noqa: E402
import library_shots  # noqa: E402
import library_write  # noqa: E402
from engine import core  # noqa: E402

OUT = ROOT / "web" / "vendor" / "flexitac-v2" / "art.json.gz"
SENSOR = "flexitac-v2"


def boards() -> dict:
    """The two boards of the committed geometry as the page takes a build's: the engine's mapping with its SVG."""

    problems = flexitac_v2.check()
    if problems:
        raise library_shots.ShotError("; ".join(problems))
    made = flexitac_v2.engine_boards(json.loads(flexitac_v2.GEOMETRY.read_text(encoding="ascii")))
    for board in made.values():
        board["svg"] = core._svg_for_board(board)
    return made


def art_document(page, url: str) -> dict:
    """The showcase's art document: the generator's page, loaded anew, answers "fpc:board-art" for the two boards."""

    made = boards()
    library_shots.open_art_page(page, url)
    errors = len(page.art_errors)
    answer = page.evaluate(library_shots.ART, {"boards": made, "px_per_mm": library_write.ART_PX_PER_MM, "max_px": library_write.ART_MAX_PX})
    if "error" in answer or len(page.art_errors) > errors:
        raise library_shots.ShotError(f"the generator's page gave no art: {answer.get('error') or page.art_errors[errors:][:3]}")
    art = json.loads(answer["text"])
    document = {"format": library_write.ART_FORMAT, "id": SENSOR, "build_id": None, "look": art.get("look"),
                "px_per_mm": library_write.ART_PX_PER_MM, "max_px": library_write.ART_MAX_PX, "boards": {}}
    for key in library_shots.BOARD_KEYS:
        board = (art.get("boards") or {}).get(key) or {}
        if sorted(board) != sorted(library_shots.ART_KEYS):
            raise library_shots.ShotError(f"the {key} board's art has the keys {sorted(board)}, not {sorted(library_shots.ART_KEYS)}")
        document["boards"][key] = dict(board, outline={"points": made[key]["outline"]["points"], "cutouts": made[key]["outline"]["cutouts"]})
    if document["look"] != "photo":
        raise library_shots.ShotError(f"the art's look is {document['look']!r}, not the page's default (photo)")
    return document


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, default=int(os.environ["FPC_PORT"]) if os.environ.get("FPC_PORT") else None,
                        help="the port of a running app.py serving this project (default FPC_PORT)")
    parser.add_argument("--out", type=Path, default=OUT, help=f"the art file (default {OUT.relative_to(ROOT)})")
    parser.add_argument("--check", action="store_true", help="make the art again and compare it with the file; write nothing")
    args = parser.parse_args(argv)
    if args.port is None:
        parser.error("give --port (or FPC_PORT): the port of a running app.py serving this project")
    url = f"http://127.0.0.1:{args.port}/"
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(args=library_shots.WEBGL_ARGS)
        try:
            page = library_shots.art_page(browser)
            document = art_document(page, url)
        except (library_shots.ShotError, PlaywrightError, OSError) as error:
            print(f"flexitac_v2_art: {error}", file=sys.stderr)
            return 2
        finally:
            browser.close()
    data = library_write.art_bytes(document)
    digest = library_shots.json_sha256(document)
    sizes = ", ".join(f"{key} {document['boards'][key]['px'][0]} x {document['boards'][key]['px'][1]} px" for key in library_shots.BOARD_KEYS)
    out = args.out.resolve()
    if args.check:
        same = out.is_file() and library_shots.json_sha256(library_write.read_art(out.read_bytes())) == digest
        print(f"flexitac_v2_art: {'same' if same else 'DIFFERS'}: the art made again ({sizes}; json_sha256 {digest}) "
              f"{'is' if same else 'is not'} {out.name}'s")
        return 0 if same else 1
    if not out.is_file() or out.read_bytes() != data:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
    print(f"flexitac_v2_art: wrote {out.name}: {len(data)} bytes, SHA-256 {hashlib.sha256(data).hexdigest()}, json_sha256 {digest}; {sizes}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
