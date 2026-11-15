#!/usr/bin/env python3
"""The original, hand-designed FlexiTac sensor (FlexiTac V2, 12 x 32 taxels at 2 mm) as data: its two FPCs' geometry
read from the official Gerber ZIPs into web/vendor/flexitac-v2/geometry.json, for the Library's showcase (the user's
request of 2026-11-12: "在lib最上面一栏放置flexitac+xarm gripper的原始版本的visualization; 这个版本是人手design的不是
autogenerate").

    python3 -I tools/flexitac_v2.py GERBER_DIR            # read the two ZIPs in GERBER_DIR, write geometry.json
    python3 -I tools/flexitac_v2.py --check               # the committed geometry.json is the pinned one
    python3 -I tools/flexitac_v2.py --check GERBER_DIR    # and the ZIPs are the pinned ones and give it again

GERBER_DIR holds Gerber_Top_FPC_2026-03-02.zip and Gerber_Bottom_FPC_2026-03-02.zip, the two files the FlexiTac
hardware tutorial links (web/vendor/flexitac-v2/NOTICE.md names it); they are never committed, extracted or run: each
member is read in memory with zipfile (run this tool with ``python3 -I``).  Their SHA-256s are pinned here (SOURCES),
and so is the SHA-256 of the geometry they give (GEOMETRY_SHA256): another ZIP is refused, and a deliberate change of
this reader is a change of that pin.

The ZIPs are EasyEDA Pro's "one-click" Gerbers (RS-274X, millimetres, FSLAX45Y45, only G01 strokes, D03 flashes and
G36/G37 regions), single-sided boards (the bottom copper layer is empty).  From each:

- the Board Outline (GKO): its closed rings; the largest is the outline, the others are cut-outs: the rectangles are
  the slots between the electrodes, any other ring a window (the hole of the Bottom FPC's A-shaped tail);
- the Top Layer (GTL): the rectangles flashed are the electrodes (the long ones) and the gold fingers; the strokes of
  the round aperture, joined where they meet, are the traces, each written from its electrode to its finger;
- the Top Solder Mask (GTS): the coverlay's openings, its regions and the rounded rectangle flashed over each pad
  (the pad and half the aperture's corner diameter round it);
- the stiffener layers (Gerber_BottomStiffenerLayer_pib_<mm>.GBSL): each region a polyimide stiffener of that thickness
  on the side without copper.

Every length is kept as the Gerber writes it (to 1e-6 mm: half a rectangle's side of 2.99999 mm is 1.499995), in each
board's own Gerber frame: seen from its copper side, x to the right, y up, the origin the centre of the electrode
array, the same point of the pad on both boards.

engine_boards() gives the two boards in the engine's own layout mapping (engine/core.py), so that the engine's SVG
writer draws them as it draws a generated board (tools/browser/flexitac_v2_art.py makes the showcase's art from them
with the page's Photo look): "column" is the Top FPC (its 12 sense lines along the finger; physical_side "bottom": on
the finger it lies under the film, its copper outward), "row" the Bottom FPC (its 32 drive lines across the finger;
physical_side "top": the outer layer, turned over, its polyimide outward), as the real pad is mounted and as a
generated sensor's boards are named.

Standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
import zipfile
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEOMETRY = ROOT / "web" / "vendor" / "flexitac-v2" / "geometry.json"
FORMAT = "flexitac-v2-geometry/v1"
# The two Gerber ZIPs of the FlexiTac hardware tutorial (2026-03-02) and the geometry they give.
SOURCES = {
    "top": ("Gerber_Top_FPC_2026-03-02.zip", "496c348c6fc236b03d23ba3f84d6a2c70ae3e66efba570a7889a990db171b621"),
    "bottom": ("Gerber_Bottom_FPC_2026-03-02.zip", "a2e0da2e0e36dc194c09db6e6f207d0508f7f3e9634666cdfa4ab48846397f6a"),
}
GEOMETRY_SHA256 = "f472ddc1ad3a5ca2002a556feac38af4bf642a0f954eadbcca329c64ac226b81"
BOARDS = {"top": {"name": "Top FPC", "role": "sense", "lines": 12}, "bottom": {"name": "Bottom FPC", "role": "drive", "lines": 32}}
PITCH_MM = 2.0
FINGER_PITCH_MM = 0.5
LAYERS = {"outline": "Gerber_BoardOutlineLayer.GKO", "copper": "Gerber_TopLayer.GTL", "coverlay": "Gerber_TopSolderMaskLayer.GTS",
          "back_copper": "Gerber_BottomLayer.GBL"}
STIFFENER = re.compile(r"^Gerber_BottomStiffenerLayer_pib_(\d+(?:\.\d+)?)\.GBSL$")
# A rectangle flashed on the copper is an electrode when its longer side is at least this long (mm), else a gold finger.
ELECTRODE_MIN_MM = 10
NM = 1_000_000  # the reader's unit: 1e-6 mm
JOIN_NM = 10_000  # two stroke ends this near (0.01 mm) are one point
_TOKEN = re.compile(r"%[^%]*%|[^*%]+\*", re.S)
_WORD = re.compile(r"([XYD])([+-]?\d+)")


class GeometryError(Exception):
    pass


# -- the reader ---------------------------------------------------------------------------------------------------------

def read_layer(text: str) -> dict:
    """An EasyEDA Pro Gerber layer: {"apertures": {code: (name, [parameters, 1e-6 mm])}, "strokes": [(code, [points])],
    "flashes": [(code, point)], "regions": [[points]]}, every point (x, y) in 1e-6 mm.  Refuses what these files do not
    use (inches, another number format, arcs, clear polarity)."""

    apertures, strokes, flashes, regions = {}, [], [], []
    scale = None
    current, point, path, region = None, (0, 0), None, None
    for match in _TOKEN.finditer(text):
        token = match.group(0).strip()
        if token.startswith("%"):
            body = token.strip("%")
            if body.startswith("FS"):
                if body.rstrip("*") != "FSLAX45Y45":
                    raise GeometryError(f"unsupported number format {body!r}")
                scale = NM // 100_000
            elif body.startswith("MO"):
                if body.rstrip("*") != "MOMM":
                    raise GeometryError(f"unsupported unit {body!r}")
            elif body.startswith("ADD"):
                found = re.fullmatch(r"ADD(\d+)([A-Za-z_]\w*)(?:,([^*]*))?\*", body)
                if not found:
                    raise GeometryError(f"unsupported aperture {body!r}")
                values = [int((Decimal(value) * NM).to_integral_exact()) for value in (found.group(3) or "").split("X") if value]
                apertures[int(found.group(1))] = (found.group(2), tuple(values))
            elif body.startswith("LP") and body.rstrip("*") != "LPD":
                raise GeometryError("clear polarity is not read")
            continue
        token = token[:-1].strip()
        if not token or token.startswith("G04") or token == "G75":
            continue
        if token == "M02":
            break
        if token == "G36":
            region = []
            continue
        if token == "G37":
            regions.extend(ring for ring in region or [] if len(ring) > 2)
            region = None
            continue
        if re.match(r"G0?[23](?!\d)", token):
            raise GeometryError("arcs are not read")
        token = re.sub(r"^G0?1(?!\d)", "", token)
        select = re.fullmatch(r"(?:G54)?D(\d+)", token)
        if select and int(select.group(1)) >= 10:
            current, path = int(select.group(1)), None
            continue
        words = dict(_WORD.findall(token))
        if not words or scale is None:
            raise GeometryError(f"unsupported block {token!r}")
        new = (int(words["X"]) * scale if "X" in words else point[0], int(words["Y"]) * scale if "Y" in words else point[1])
        operation = int(words.get("D", 1))
        if operation == 2:
            path = None
            if region is not None:
                region.append([new])
        elif operation == 3:
            if region is None:
                flashes.append((current, new))
            path = None
        elif operation == 1:
            if region is not None:
                if not region:
                    region.append([point])
                region[-1].append(new)
            else:
                if path is None:
                    path = [point]
                    strokes.append((current, path))
                path.append(new)
        else:
            raise GeometryError(f"unsupported operation D{operation:02d}")
        point = new
    return {"apertures": apertures, "strokes": strokes, "flashes": flashes, "regions": regions}


def _near(first: tuple, second: tuple, reach: int = JOIN_NM) -> bool:
    return max(abs(first[0] - second[0]), abs(first[1] - second[1])) <= reach


def _joined(paths: list, reach: int = JOIN_NM) -> list:
    """Open polylines joined end to end where they meet (a trace or an outline EasyEDA writes in several pieces), in
    their order.  Two ends within JOIN_NM are one point (the Bottom FPC's outline is drawn with 0.004 mm between two of
    its strokes): the join keeps the point of the piece joined to, and a polyline whose own ends meet so is closed there.
    Two ends within ``reach`` (a trace's half width: the strokes' copper overlaps) are joined too, both points kept
    (one of the Bottom FPC's traces is drawn in two strokes 0.127 mm apart)."""

    paths = [list(path) for path in paths if len(path) > 1]
    closed = lambda path: _near(path[0], path[-1])  # noqa: E731
    joined = True
    while joined:
        joined = False
        for i, first in enumerate(paths):
            for j, second in enumerate(paths):
                if i == j or closed(first) or closed(second):
                    continue
                if _near(first[-1], second[0], reach):
                    head, tail = first, second
                elif _near(first[-1], second[-1], reach):
                    head, tail = first, second[::-1]
                elif _near(first[0], second[0], reach):
                    head, tail = first[::-1], second
                else:
                    continue
                paths[i] = head + tail[1 if _near(head[-1], tail[0]) else 0:]
                del paths[j]
                joined = True
                break
            if joined:
                break
    return [path[:-1] + path[:1] if closed(path) else path for path in paths]


def _area2(ring: list) -> int:
    twice = 0  # integers: exact
    for k, (x, y) in enumerate(ring):
        after = ring[(k + 1) % len(ring)]
        twice += x * after[1] - after[0] * y
    return twice


def _ring(points: list) -> list:
    """A closed ring without its closing point or a point on a straight run, counter-clockwise from its least point."""

    ring = list(points[:-1]) if points[0] == points[-1] else list(points)
    kept = []
    for k, point in enumerate(ring):
        before, after = ring[k - 1], ring[(k + 1) % len(ring)]
        if point != before and (point[0] - before[0]) * (after[1] - point[1]) != (point[1] - before[1]) * (after[0] - point[0]):
            kept.append(point)
    if len(kept) < 3:
        raise GeometryError("a ring of fewer than three corners")
    if _area2(kept) < 0:
        kept.reverse()
    start = kept.index(min(kept))
    return kept[start:] + kept[:start]


def _box(ring: list):
    """(x0, y0, x1, y1) of a ring that is an axis-parallel rectangle, else None."""

    xs, ys = sorted({point[0] for point in ring}), sorted({point[1] for point in ring})
    if len(ring) == 4 and len(xs) == 2 and len(ys) == 2:
        return (xs[0], ys[0], xs[1], ys[1])
    return None


def _flashed(aperture: tuple, centre: tuple) -> tuple:
    """(x0, y0, x1, y1) of a rectangle aperture flashed at ``centre``: R (width, height) or EasyEDA's RoundRect macro
    (the corner circles' diameter, then two corners of the rectangle through their centres)."""

    name, values = aperture
    if name == "R" and len(values) == 2:
        half = (Decimal(values[0]) / 2, Decimal(values[1]) / 2)
    elif name == "RoundRect" and len(values) == 5:
        half = (max(abs(values[1]), abs(values[3])) + Decimal(values[0]) / 2, max(abs(values[2]), abs(values[4])) + Decimal(values[0]) / 2)
    else:
        raise GeometryError(f"a flash of the aperture {name} {values}")
    if any(side != side.to_integral_value() for side in half):
        raise GeometryError(f"an aperture finer than 1e-6 mm: {name} {values}")
    return (centre[0] - int(half[0]), centre[1] - int(half[1]), centre[0] + int(half[0]), centre[1] + int(half[1]))


def _inside(box: tuple, point: tuple) -> bool:
    return box[0] <= point[0] <= box[2] and box[1] <= point[1] <= box[3]


def board_geometry(key: str, data: bytes) -> dict:
    """One FPC's geometry (1e-6 mm integers) from its Gerber ZIP's bytes."""

    facts = BOARDS[key]
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = set(archive.namelist())
        missing = [name for name in LAYERS.values() if name not in names]
        if missing:
            raise GeometryError(f"the {facts['name']}'s ZIP has no {', '.join(missing)}")
        layers = {layer: read_layer(archive.read(name).decode("ascii")) for layer, name in LAYERS.items()}
        stiffeners = []
        for name in sorted(names):
            found = STIFFENER.match(name)
            if found:
                thickness = int((Decimal(found.group(1)) * NM).to_integral_exact())
                stiffeners += [{"thickness": thickness, "points": _ring(ring)} for ring in read_layer(archive.read(name).decode("ascii"))["regions"]]
    if layers["back_copper"]["strokes"] or layers["back_copper"]["flashes"] or layers["back_copper"]["regions"]:
        raise GeometryError(f"the {facts['name']} has copper on its other side")
    # The outline's rings: the layer's strokes, joined where they meet, each close on themselves.
    rings = []
    for path in _joined([path for _, path in layers["outline"]["strokes"]]):
        if path[0] != path[-1]:
            raise GeometryError(f"the {facts['name']}'s outline has an open stroke")
        rings.append(_ring(path))
    rings.sort(key=lambda ring: -_area2(ring))
    outline, cuts = rings[0], rings[1:]
    slots = sorted(box for box in map(_box, cuts) if box)
    windows = sorted(ring for ring in cuts if not _box(ring))
    # The copper: rectangles flashed, and the round aperture's strokes.
    copper = layers["copper"]
    pads = sorted(_flashed(copper["apertures"][code], centre) for code, centre in copper["flashes"])
    long = [box for box in pads if max(box[2] - box[0], box[3] - box[1]) >= ELECTRODE_MIN_MM * NM]
    fingers = [box for box in pads if box not in long]
    widths = {copper["apertures"][code] for code, _ in copper["strokes"]}
    if len(widths) != 1 or next(iter(widths))[0] != "C":
        raise GeometryError(f"the {facts['name']}'s traces are not of one round aperture: {sorted(widths)}")
    traces = []
    for path in _joined([path for _, path in copper["strokes"]], next(iter(widths))[1][0] // 2):
        starts = [any(_inside(box, end) for box in long) for end in (path[0], path[-1])]
        ends = [any(_inside(box, end) for box in fingers) for end in (path[0], path[-1])]
        if starts == [False, True] and ends == [True, False]:
            path = path[::-1]
        elif not (starts == [True, False] and ends == [False, True]):
            raise GeometryError(f"a trace of the {facts['name']} does not run from an electrode to a gold finger")
        traces.append(path)
    traces.sort(key=lambda path: (path[0], path[-1]))
    coverlay = layers["coverlay"]
    openings = sorted(_box(_ring(ring)) or tuple() for ring in coverlay["regions"]) + sorted(
        _flashed(coverlay["apertures"][code], centre) for code, centre in coverlay["flashes"])
    if not all(openings):
        raise GeometryError(f"a coverlay opening of the {facts['name']} is not a rectangle")
    stiffeners.sort(key=lambda item: (item["thickness"], item["points"]))
    counts = (len(long), len(fingers), len(traces))
    if counts != (facts["lines"],) * 3:
        raise GeometryError(f"the {facts['name']} has {counts[0]} electrodes, {counts[1]} gold fingers and {counts[2]} traces, not {facts['lines']} of each")
    return {"name": facts["name"], "role": facts["role"], "lines": facts["lines"], "outline": outline, "slots": slots, "windows": windows,
            "electrodes": long, "fingers": fingers, "trace_width": next(iter(widths))[1][0], "traces": traces, "openings": openings,
            "stiffeners": stiffeners}


def _mm(value):
    """The reader's integers (1e-6 mm) as millimetres, through lists, tuples and mappings (a name stays as it is)."""

    if isinstance(value, bool) or isinstance(value, str):
        return value
    if isinstance(value, int):
        return value / NM
    if isinstance(value, dict):
        return {key: (item if key == "lines" else _mm(item)) for key, item in value.items()}
    return [_mm(item) for item in value]


def geometry(zips: dict) -> dict:
    """The geometry document of the two ZIPs' bytes ({"top": ..., "bottom": ...})."""

    return {
        "format": FORMAT,
        "name": "FlexiTac V2 tactile sensor pad, 12 x 32 taxels at 2 mm",
        "units": "mm",
        "frame": "each board's own Gerber frame: seen from its copper side, x to the right, y up; the origin is the centre of the "
                 "electrode array, the same point of the pad on both boards",
        "keys": "outline, windows and stiffeners' points: [x, y] rings; slots, electrodes, fingers and openings (the coverlay's): "
                "[x0, y0, x1, y1] rectangles; traces: polylines of trace_width, each from its electrode to its gold finger",
        "source": {key: {"file": SOURCES[key][0], "sha256": hashlib.sha256(zips[key]).hexdigest()} for key in ("top", "bottom")},
        "boards": {key: _mm(board_geometry(key, zips[key])) for key in ("top", "bottom")},
    }


def geometry_text(document: dict) -> str:
    """The file's text: canonical JSON (sorted keys, compact, ASCII) and a newline."""

    return json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False) + "\n"


def read_zips(directory: Path) -> dict:
    """The two pinned ZIPs' bytes from ``directory``; another file under their names is refused."""

    zips = {}
    for key, (name, pinned) in SOURCES.items():
        path = directory / name
        if not path.is_file():
            raise GeometryError(f"{name} is not in the folder given")
        zips[key] = path.read_bytes()
        digest = hashlib.sha256(zips[key]).hexdigest()
        if digest != pinned:
            raise GeometryError(f"{name} has the SHA-256 {digest}, not the pinned {pinned}")
    return zips


# -- the boards as the engine draws them --------------------------------------------------------------------------------

# Which FPC is which board of a sensor in the Library (docs/LIBRARY_VIEW.md): as the real pad lies on the finger.
ENGINE_BOARDS = {"column": ("top", "columns", "bottom"), "row": ("bottom", "rows", "top")}
# The stiffeners the boards are drawn with: those at least this thick (mm), the two under each gold end.  The engine's
# writer and the Photo look paint a stiffener as the one under a connector, opaque and dark; the pad's 0.1 mm ones (the
# strip under the Top FPC's traces below the field, the patches at the A's corners) are thin polyimide through which the
# real pad stays amber (the tutorial's photo of the assembled sensor), and so painted the base strip and the straps'
# roots were near-black blocks (the review of 2026-11-12).  geometry.json keeps every stiffener.
DRAWN_STIFFENER_MIN_MM = 0.2


def _rect(box: list) -> dict:
    return {"x": box[0], "y": box[1], "width_mm": round(box[2] - box[0], 6), "height_mm": round(box[3] - box[1], 6), "anchor": "lower_left"}


def field(document: dict) -> dict:
    """The taxel field of the pad, the same on both boards: the box of both boards' electrodes about the origin (23 x 63
    mm: 12 sense lines 0.6 mm wide at 2 mm across, 63 mm long; 32 drive lines along it, 23 mm long)."""

    boxes = [box for board in document["boards"].values() for box in board["electrodes"]]
    x0, y0 = min(box[0] for box in boxes), min(box[1] for box in boxes)
    x1, y1 = max(box[2] for box in boxes), max(box[3] for box in boxes)
    return {"x": x0, "y": y0, "width": round(x1 - x0, 6), "height": round(y1 - y0, 6)}


def engine_boards(document: dict) -> dict:
    """{"row", "column"}: the two FPCs in the engine's layout mapping, as far as its SVG writer (engine/core.py
    _svg_for_board) and the Library's art read it: role, physical_side, outline {points, cutouts}, layers
    {bottom_stiffener, top_coverlay_openings, top_copper {electrodes, routes, pads}} and grid_registration.active_region
    (field()).  bottom_stiffener holds the stiffeners under the gold ends only (DRAWN_STIFFENER_MIN_MM).  No pin is
    numbered (the art carries no pin-1 marker)."""

    region = field(document)
    boards = {}
    for key, (source, role, side) in ENGINE_BOARDS.items():
        board = document["boards"][source]
        slots = [[[x0, y0], [x1, y0], [x1, y1], [x0, y1]] for x0, y0, x1, y1 in board["slots"]]
        boards[key] = {
            "id": f"flexitac-v2-{source}", "role": role, "physical_side": side, "units": "mm",
            "outline": {"points": board["outline"], "cutouts": slots + board["windows"]},
            "layers": {
                "bottom_stiffener": [{"points": item["points"], "thickness_mm": item["thickness"]} for item in board["stiffeners"]
                                     if item["thickness"] >= DRAWN_STIFFENER_MIN_MM],
                "top_coverlay_openings": [_rect(box) for box in board["openings"]],
                "top_copper": {
                    "electrodes": [_rect(box) for box in board["electrodes"]],
                    "routes": [{"width_mm": board["trace_width"], "points": points} for points in board["traces"]],
                    "pads": [_rect(box) for box in board["fingers"]],
                },
            },
            "grid_registration": {"active_region": dict(region)},
        }
    return boards


# -- the command --------------------------------------------------------------------------------------------------------

def check(directory: Path | None = None, path: Path = GEOMETRY) -> list:
    """What is wrong with the committed geometry (none: []): its SHA-256 is not the pinned one; with ``directory``, the
    ZIPs there are not the pinned ones or give another geometry."""

    problems = []
    if not path.is_file():
        return [f"{path.name} is missing"]
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != GEOMETRY_SHA256:
        problems.append(f"{path.name} has the SHA-256 {digest}, not the pinned {GEOMETRY_SHA256}")
    if directory is not None:
        try:
            if geometry_text(geometry(read_zips(directory))).encode("ascii") != data:
                problems.append(f"the Gerber ZIPs give another geometry than {path.name}")
        except (GeometryError, zipfile.BadZipFile, UnicodeDecodeError, KeyError) as error:
            problems.append(str(error))
    return problems


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("directory", nargs="?", type=Path, help="the folder holding the two Gerber ZIPs")
    parser.add_argument("--check", action="store_true", help="write nothing: the committed geometry is the pinned one (and, with a "
                        "folder, the ZIPs' own)")
    args = parser.parse_args(argv)
    if args.check:
        problems = check(args.directory)
        for problem in problems:
            print(f"flexitac_v2: {problem}", file=sys.stderr)
        if not problems:
            print(f"flexitac_v2: {GEOMETRY.relative_to(ROOT).as_posix()} is the pinned geometry" + (" and the ZIPs give it again" if args.directory else ""))
        return 1 if problems else 0
    if args.directory is None:
        parser.error("give the folder holding the two Gerber ZIPs (or --check)")
    try:
        text = geometry_text(geometry(read_zips(args.directory)))
    except (GeometryError, zipfile.BadZipFile, UnicodeDecodeError, KeyError) as error:
        print(f"flexitac_v2: {error}", file=sys.stderr)
        return 2
    digest = hashlib.sha256(text.encode("ascii")).hexdigest()
    if not GEOMETRY.is_file() or GEOMETRY.read_text(encoding="ascii") != text:
        GEOMETRY.parent.mkdir(parents=True, exist_ok=True)
        GEOMETRY.write_text(text, encoding="ascii")
        print(f"flexitac_v2: wrote {GEOMETRY.relative_to(ROOT).as_posix()} ({len(text)} bytes, SHA-256 {digest})")
    else:
        print(f"flexitac_v2: {GEOMETRY.relative_to(ROOT).as_posix()} is unchanged ({len(text)} bytes, SHA-256 {digest})")
    if digest != GEOMETRY_SHA256:
        print(f"flexitac_v2: that is not the pinned SHA-256 {GEOMETRY_SHA256}: pin it (GEOMETRY_SHA256) if the change is meant", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
