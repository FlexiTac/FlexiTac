#!/usr/bin/env python3
"""The FlexiTac hardware's own order files, served by the site (the user's request of 2026-11-17: "把instruction里面的fpc
gerber也都放到这边可以直接download ... reading board download：你可以把instruction里面对应gerber也放在这下载"; his answer
to the plan: "copy into site, reading board可以打包成一个zip：gerber，bom，pick and place").

    python3 -I tools/flexitac_downloads.py SOURCE_DIR            # copy the FPC ZIPs, write the reading boards' ZIPs
    python3 -I tools/flexitac_downloads.py --check               # the served files are the pinned ones, re-derived
    python3 -I tools/flexitac_downloads.py --check SOURCE_DIR    # and the sources are the pinned ones and give them

SOURCE_DIR holds the files of the FlexiTac Hardware Fabrication Guide's table "PCB Related Files" under their own names
(FPC_FILES and each board's BOARDS files), as Google Drive serves them; they are read as bytes only, never extracted
or run (run this tool with ``python3 -I``).  Every file is pinned by its SHA-256 and size, so another file is refused.

- web/vendor/flexitac-v2/: the original pad's two Gerber ZIPs, unchanged (the ZIPs tools/flexitac_v2.py reads; the
  showcase's window links them).
- web/vendor/flexitac-reader/: one ZIP per reading board (bundle()), its Gerber ZIP, its BOM and its pick-and-place
  unchanged, stored in name order with fixed metadata (the engine's Gerber ZIPs' convention), so its bytes depend on
  its members' bytes alone; the bundles' SHA-256s are pinned too.  --check re-derives each bundle from the members it
  holds (each at its pin) and compares the served bytes; the site build runs the same check (tools/build_static_site.py).

Both folders are FlexiTac's hardware, CC BY-NC 4.0 material of Columbia University (each folder's NOTICE.md), not
Apache-2.0.  The page's rule (web/boards.js) names a sensor's reading board by its lines: the larger of rows and
columns at most 32 and the smaller at most 16, the 32 x 16 board; the larger at most 32, the 32 x 32; else none.

Standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "web" / "vendor"
FPC_FOLDER = "flexitac-v2"
READER_FOLDER = "flexitac-reader"
# The original pad's two FPCs (EasyEDA Pro exports of 2026-03-02; tools/flexitac_v2.py pins the same two).
FPC_FILES = {
    "Gerber_Top_FPC_2026-03-02.zip": ("496c348c6fc236b03d23ba3f84d6a2c70ae3e66efba570a7889a990db171b621", 52816),
    "Gerber_Bottom_FPC_2026-03-02.zip": ("a2e0da2e0e36dc194c09db6e6f207d0508f7f3e9634666cdfa4ab48846397f6a", 66670),
}
# The reading boards (the guide: "Reading Board 32x16 ... This one is enough for reading above sensor"; "Reading Board
# 32x32 ... Develop purpose"): each bundle's name, its pinned SHA-256 and size, and its members' (Gerber, BOM,
# pick-and-place; not the schematic).
BOARDS = {
    "32x16": {
        "bundle": ("FlexiTac_reading_board_32x16.zip", "af488c7f85845d8b03daf58327a6cd0209268a47a97c748dbf09e05867e889a5", 50257),
        "files": {
            "Gerber_16_32.zip": ("53f9f9014d84066678e2b69d501b885ad4680ca8e9ee2d180887078db43416a0", 46875),
            "BOM_05mm_FFC_16_32_1mux_4sr_2025-11-01.csv": ("fe735edb181e4945091afa5095ae9263d9c42355f01f84ae753a34e075762349", 1116),
            "PickAndPlace_PCB_05mm_FFC_16_32_1mux_4sr_2025-11-01.csv": ("e72a32b9ed10d738f2fb837612f19c8dfec1fa6d7d3899207b731cac0ab4b228", 1790),
        },
    },
    "32x32": {
        "bundle": ("FlexiTac_reading_board_32x32.zip", "5e8fa8ed642346b943077272a72509bb622e4dc8de60f7bfef88cbbf98194aba", 92579),
        "files": {
            "Gerber_32_32.zip": ("07cee864e337fddbbf488b52f03c7c46d0753b5bed8953306dde035ca4f2180d", 80128),
            "BOM_32_32.xlsx": ("6836d7a8fed496a1d761e6ac19bc0128a96b6db8a7b4931299c70ed22ab21b13", 5819),
            "PickAndPlace_32_32.xlsx": ("300d2076fd740d85d8500a97bb7561bc1c57a5f408e703993e98d73d8dee23f8", 6276),
        },
    },
}
# The bundles' fixed metadata (exporters/direct_gerber.py's): stored members, 1980-01-01, Unix, -rw-r--r--.
ZIP_TIME = (1980, 1, 1, 0, 0, 0)
# The byte budgets of the two folders (their files and notices; flexitac-v2's art, geometry and placed record too).
BUDGETS = {FPC_FOLDER: 160_000, READER_FOLDER: 160_000}


class DownloadsError(Exception):
    pass


def bundle(files: dict) -> bytes:
    """A reading board's ZIP: ``files`` {name: bytes} stored in name order with fixed metadata."""

    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_STORED, strict_timestamps=True) as archive:
        for name in sorted(files):
            info = zipfile.ZipInfo(filename=name, date_time=ZIP_TIME)
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, files[name])
    return stream.getvalue()


def pinned(name: str, data: bytes, pin: tuple) -> list:
    """What is wrong with ``data`` against its pin (SHA-256, size): none, []."""

    digest = hashlib.sha256(data).hexdigest()
    if (digest, len(data)) != tuple(pin):
        return [f"{name} is {len(data)} bytes with the SHA-256 {digest}, not the pinned {pin[1]} bytes {pin[0]}"]
    return []


def members(data: bytes, board: str) -> dict:
    """The members of a reading board's served ZIP, {name: bytes}, each read in memory; DownloadsError when it is no
    ZIP, holds another list of names or a member not at its pin."""

    wanted = BOARDS[board]["files"]
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            names = [info.filename for info in archive.infolist()]
            if names != sorted(wanted):
                raise DownloadsError(f"the {board} bundle holds {names}, not {sorted(wanted)}")
            files = {name: archive.read(name) for name in names}
    except zipfile.BadZipFile as error:
        raise DownloadsError(f"the {board} bundle is no ZIP: {error}") from None
    problems = [problem for name, payload in files.items() for problem in pinned(f"{BOARDS[board]['bundle'][0]}: {name}", payload, wanted[name])]
    if problems:
        raise DownloadsError("; ".join(problems))
    return files


def check(sources: Path | None = None, vendor: Path = VENDOR) -> list:
    """What is wrong with the served files (none: []): an FPC ZIP not at its pin; a bundle missing, not re-derived
    byte for byte from its members (each at its pin) or not at its own pin; a folder over its budget; with
    ``sources``, a source missing or not at its pin."""

    problems = []
    for name, pin in FPC_FILES.items():
        path = vendor / FPC_FOLDER / name
        problems += pinned(f"web/vendor/{FPC_FOLDER}/{name}", path.read_bytes(), pin) if path.is_file() else [f"web/vendor/{FPC_FOLDER}/{name} is missing"]
    for board, record in BOARDS.items():
        name, digest, size = record["bundle"]
        path = vendor / READER_FOLDER / name
        if not path.is_file():
            problems.append(f"web/vendor/{READER_FOLDER}/{name} is missing")
            continue
        data = path.read_bytes()
        try:
            if bundle(members(data, board)) != data:
                problems.append(f"web/vendor/{READER_FOLDER}/{name} is not the bundle its members give (sorted, stored, fixed metadata)")
        except DownloadsError as error:
            problems.append(f"web/vendor/{READER_FOLDER}/{name}: {error}")
        problems += pinned(f"web/vendor/{READER_FOLDER}/{name}", data, (digest, size))
    for folder, budget in BUDGETS.items():
        size = sum(path.stat().st_size for path in (vendor / folder).rglob("*") if path.is_file()) if (vendor / folder).is_dir() else 0
        if size > budget:
            problems.append(f"web/vendor/{folder}/ is {size} bytes, over its budget of {budget}")
    if sources is not None:
        try:
            read(sources)
        except DownloadsError as error:
            problems.append(str(error))
    return problems


def read(sources: Path) -> dict:
    """Every source file in ``sources`` by its own name, {name: bytes}, each at its pin; DownloadsError otherwise."""

    wanted = dict(FPC_FILES)
    for record in BOARDS.values():
        wanted.update(record["files"])
    files, problems = {}, []
    for name, pin in wanted.items():
        path = sources / name
        if not path.is_file():
            problems.append(f"the source {name} is missing in {sources}")
            continue
        files[name] = path.read_bytes()
        problems += pinned(f"the source {name}", files[name], pin)
    if problems:
        raise DownloadsError("; ".join(problems))
    return files


def write(sources: Path, vendor: Path = VENDOR) -> list:
    """The served files from ``sources`` (read()): the FPC ZIPs copied, the bundles written; the lines to print."""

    files = read(sources)
    said = []
    outputs = {f"{FPC_FOLDER}/{name}": files[name] for name in FPC_FILES}
    for record in BOARDS.values():
        outputs[f"{READER_FOLDER}/{record['bundle'][0]}"] = bundle({name: files[name] for name in record["files"]})
    for relative, data in outputs.items():
        path = vendor / relative
        if path.is_file() and path.read_bytes() == data:
            said.append(f"web/vendor/{relative} is unchanged ({len(data)} bytes, SHA-256 {hashlib.sha256(data).hexdigest()})")
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        said.append(f"wrote web/vendor/{relative} ({len(data)} bytes, SHA-256 {hashlib.sha256(data).hexdigest()})")
    return said


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("sources", nargs="?", type=Path, help="the folder holding the guide's files under their own names")
    parser.add_argument("--check", action="store_true", help="write nothing: the served files are the pinned ones (and, with a "
                        "folder, the sources' own)")
    args = parser.parse_args(argv)
    if args.check:
        problems = check(args.sources)
        for problem in problems:
            print(f"flexitac_downloads: {problem}", file=sys.stderr)
        if not problems:
            print("flexitac_downloads: the two FPC ZIPs and the reading boards' bundles are the pinned ones, each bundle "
                  "re-derived from its members" + (", and the sources give them" if args.sources else ""))
        return 1 if problems else 0
    if args.sources is None:
        parser.error("give the folder holding the guide's files (or --check)")
    try:
        said = write(args.sources)
    except DownloadsError as error:
        print(f"flexitac_downloads: {error}", file=sys.stderr)
        return 2
    print("\n".join(f"flexitac_downloads: {line}" for line in said))
    problems = check()
    for problem in problems:
        print(f"flexitac_downloads: {problem}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
