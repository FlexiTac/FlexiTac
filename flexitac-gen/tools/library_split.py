#!/usr/bin/env python3
"""Share a gripper's bodies out by material and give each its look: tools/library_looks/<part>.json -> the part's
component files (web/library/bodies/<part>/<component>.stl), its scene's bodies, looks, part_look and smooth_deg, and
its bodies' rows of web/library/NOTICE.md.

The Library draws every gripper after photos of the real product (the user's request of 2026-11-12, docs/LIBRARY_VIEW.md
"The looks"): one STL file is one component and has one look.  The scenes' bodies come from the project's scene
builder (private, numpy and trimesh): one decimated body per upstream mesh, whatever it is made of.  This tool is the
step after it: standard library only, deterministic, driven by ONE look file per part (so two parts never meet in a
file), a pure function of the committed decimated bodies and that file.

A look file (tools/library_looks/<part>.json, FORMAT):

    {"format": "flexitac-library-look/v1", "part": "arx-x5", "smooth_deg": 35, "part_look": "print-black",
     "about": "words added to the scene's about (what is drawn after which photo; what the project drew itself)",
     "looks": {"rail-steel": {"base": "steel-ground", "roughness": 0.25, "evidence": "photo 6: the rail mirrors ..."}},
     "bodies": {"bodies/arx-x5/link6.stl": {"sha256": "...", "facets_sha256": "...", "weld_mm": 0.01, "components": [
         {"name": "link6-rail", "look": "rail-steel", "pick": [{"box": [[71.5, -85.05, -4.55], [78.12, 85.05, 4.55]]}]},
         {"name": "link6-pinion", "look": "steel-ground",
          "pick": [{"component": {"box": [[58, -17.23, -17.55], [71, 16.22, 13.64]], "triangles": 792}}]},
         {"name": "link6-screws", "look": "steel-polished", "draw": [{"cylinder": {"from": [78, 0, 0], "to": [79, 0, 0], "radius": 2}}]},
         {"name": "link6-body", "look": "anodized-black", "pick": "rest"}]},
               "bodies/arx-x5/other.stl": {"sha256": "...", "look": "anodized-black"}},
     "drawn": [{"name": "strip", "look": "steel-ground", "draw": [{"box": [[0, 0, 0], [1, 2, 3]]}], "finger": null}]}

- "bodies" names every body of the part's scene as the scene builder wrote it (its path and the SHA-256 of that
  file): kept whole with one look ("look": a name, or null: the part's grey), or shared out into "components".
- A component takes triangles ("pick") or is drawn by the project ("draw").  The components are read in order and a
  triangle goes to the first that takes it; "pick": "rest" takes what is left.  Every triangle must be taken, every
  picked component must take one.  The rules:
    {"box": [[lo], [hi]]}                      the triangles whose three corners lie in the closed box (mm, the body's
                                               file frame);
    {"component": {"box": [[lo], [hi]], "triangles": n, "tol_mm": 0.05}}
                                               the one connected component (the triangles joined through shared
                                               corners after welding at "weld_mm", 0.01 mm by default) whose bounding
                                               box is that box within tol_mm (and whose triangle count is n, if given);
    {"components_inside": [[lo], [hi]]}        every connected component whose bounding box lies in the box (one at
                                               least).
- "draw": plain shapes for a component the model lacks (the photos show it and it matters for the look): {"box":
  [[lo], [hi]]}, {"cylinder": {"from", "to", "radius", "segments": 24}} or {"prism": {"axis": "x", "from": a, "to": b,
  "profile": [[p, q], ...]}} (a convex polygon of 3 to 32 corners, counter-clockwise seen from the axis's positive end,
  drawn from a to b along the axis: a chamfered block, a rail's rounded section; its corners are (y, z) about x, (z, x)
  about y and (x, y) about z), in the frame of the body they are listed
  under (so they stand on every copy of that body: both fingers), or, under "drawn", in the part's frame ("matrix",
  the identity by default; "finger").  A drawn file is bodies/<part>/drawn-<name>.stl, the project's own (no NOTICE
  row; its header says so, library_write.own_body()); say so in "about" too.
- "looks": the part's own looks, each a base look of tools/library_looks/base.json ("base") with the numbers that
  differ, and "evidence": the photo that shows the difference.  A look named in "look" or "part_look" that is not in
  "looks" is the base look of that name, unchanged; a part's own look may not take a base look's name, so in a scene a
  base name always means the base's numbers.

What is written (and what --check compares, byte for byte):

- bodies/<part>/<name>.stl for each component: binary STL, mm.  A picked one holds its triangles' 50-byte records as
  the body's file has them (nothing recomputed), sorted, under the body's header with "; split" added ("modified
  (decimated, m to mm; split) by FlexiTac-Gen 2026, see NOTICE.md": split_header()); a body kept whole keeps its file.  The
  unsplit file of a body that is shared out leaves web/library/ (the scene no longer names it).
- scenes/<part>.json: each body's entry replaced by its components' (the same matrix and finger; "look" added), the
  drawn ones after them, then "looks" (the ones used, with their numbers), "part_look", "smooth_deg", and the look
  file's "about" after the scene's own (LOOK_MARK); every other key and byte of the scene as it was.
- NOTICE.md: the row of a body that is shared out replaced by one row per picked component (its source, licence and
  change, with SPLIT_NOTE and the new SHA-256).

The unsplit body stays pinned: "sha256" is the file the scene builder wrote (the scene's record before the split, the
row NOTICE.md had, git's history), "facets_sha256" the SHA-256 of its facet records sorted (--pin prints both).  With
the unsplit file at hand (in web/library/bodies/, or --source DIR laid out like web/library/) the tool checks "sha256"
and splits it (a file there of other bytes is refused: a body made anew is pinned anew, on purpose); without it, it
takes the committed components' records together, checks "facets_sha256" and splits those: the same triangles, so the
same files.  So --check needs nothing but the committed files, and a changed rule is applied without the scene builder.

--check also reads every scene of the library (unless --only): a scene that has a look, a crease angle or a body the
project drew (bodies/<part>/drawn-<name>.stl), a drawn file in a part's folder, or a NOTICE row of a split body, each
without a look file for its part, is refused (unowned()): a drawn body's header only labels it, its look file's
numbers are what draws it again, and a scene's looks are the base table's or its look file's own, never loose (the
showcase's scene, scenes/flexitac-g1.json, has its looks and the shapes drawn for it from tools/library_showcase.py,
whose --check holds them: its drawn bodies are pinned by SHA-256 in tools/library_write.py, and one that is not pinned
there is refused all the same).  Run the scene builder first when the geometry changes (it writes unsplit bodies
and a scene without looks), then this tool, then tools/library_write.py and the shoot.

    python3 tools/library_split.py                       # every look file; or --only franka-hand,arx-x5
    python3 tools/library_split.py --check               # the committed files are what the look files give
    python3 tools/library_split.py --pin bodies/arx-x5/link6.stl          # a body's sha256 and facets_sha256
    python3 tools/library_split.py --components bodies/arx-x5/link6.stl   # its connected components (to write rules)
    python3 tools/library_split.py --only arx-x5 --out <dir>              # a dry run into another folder

A part without a look file is not touched.  Python 3.9, standard library.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import library_write  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = library_write.LIBRARY
LOOKS = ROOT / "tools" / "library_looks"
FORMAT = "flexitac-library-look/v1"
BASE_FORMAT = "flexitac-library-looks/v1"
BASE_FILE = "base.json"
WELD_MM = 0.01
TOL_MM = 0.05
SEGMENTS = 24
# A prism's axis and the order of its profile's two numbers about it (right-handed: the profile counter-clockwise seen
# from the axis's positive end faces outward), and its most corners.
PRISM_AXES = {"x": (1, 2), "y": (2, 0), "z": (0, 1)}
PRISM_CORNERS = 32
RECORD = struct.Struct("<12fH")
NAME = re.compile(r"[a-z0-9]+(?:[_-][a-z0-9]+)*")
PART_KEYS = {"format", "part", "about", "smooth_deg", "part_look", "looks", "bodies", "drawn"}
HEADER = re.compile(r"modified \((.*)\) by FlexiTac-Gen 2026, see NOTICE\.md")
SPLIT_HEADER = "modified (split by look) by FlexiTac-Gen 2026, see NOTICE.md"
# The words a split body's NOTICE row adds to its change ({count} files, of {stem}: the body's file name): how its
# rows are found again.
SPLIT_NOTE = "; split by look, its triangles unchanged (one of the {count} files of {stem}'s)"
# A body whose triangles all stay in one file, its other components drawn (the Franka's finger): not "one of the 1 files"
# (the verification of 2026-11-13).
SPLIT_NOTE_ONE = "; split by look, its triangles unchanged (the one file of {stem}'s)"
SPLIT_FOUND = re.compile(r"; split by look, its triangles unchanged \((?:one of the \d+ files|the one file) of ([\w.-]+\.stl)'s\)")
# The look file's "about" follows the scene's own after this mark (the scene's own may not hold it).
LOOK_MARK = "  The looks: "
IDENTITY = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]


class SplitError(Exception):
    pass


# -- binary STL ----------------------------------------------------------------------------------------------------------

def facets(data: bytes, name: str = "the file") -> list:
    """The 50-byte facet records of a binary STL."""

    if library_write.stl_triangles(data) is None:
        raise SplitError(f"{name} is not a binary STL")
    return [data[84 + 50 * k:134 + 50 * k] for k in range((len(data) - 84) // 50)]


def stl(header: str, records: list) -> bytes:
    """A binary STL of ``records`` under ``header`` (ASCII, 80 bytes at most, padded with spaces)."""

    text = header.encode("ascii")
    if len(text) > 80:
        raise SplitError(f"the header {header!r} is {len(text)} bytes, an STL's holds 80")
    return text.ljust(80, b" ") + struct.pack("<I", len(records)) + b"".join(records)


def facets_sha256(records: list) -> str:
    """The SHA-256 of a body's facet records sorted: the same for the unsplit file and for its components together."""

    return hashlib.sha256(b"".join(sorted(records))).hexdigest()


def corners(record: bytes) -> tuple:
    values = RECORD.unpack(record)
    return values[3:6], values[6:9], values[9:12]


def split_header(header: bytes) -> str:
    """A component's header from its body's: "; split" added to what was changed ("modified (m to mm; split) by
    FlexiTac-Gen 2026, see NOTICE.md"); where that does not fit an STL's 80 bytes, without the decimation's bound
    ("decimated <= 0.5 mm" as "decimated": NOTICE.md has it); SPLIT_HEADER where the body's header is not the bodies'
    convention or is still too long.  A component's own header is kept, SPLIT_HEADER too (the review of 2026-11-12: read
    back from its components, a body of another header had been given "split by look; split", so --check failed on
    the files the tool had just written)."""

    text = header.rstrip(b" \0").decode("ascii", "replace")
    match = HEADER.fullmatch(text)
    if not match:
        return SPLIT_HEADER
    if text == SPLIT_HEADER or match.group(1).endswith("; split"):
        return text
    for inner in (match.group(1), re.sub(r" <= [\d.]+ mm", "", match.group(1))):
        made = f"modified ({inner}; split) by FlexiTac-Gen 2026, see NOTICE.md"
        if len(made) <= 80:
            return made
    return SPLIT_HEADER


# -- the rules -------------------------------------------------------------------------------------------------------------

def components(records: list, weld_mm: float = WELD_MM) -> list:
    """The connected components of a triangle soup: the triangles joined through corners that fall in the same cell of
    ``weld_mm`` (each coordinate divided by it and rounded), as lists of record indices, each in order, the components
    by their first triangle.  Deterministic: no set or dict order enters."""

    if not (isinstance(weld_mm, (int, float)) and weld_mm > 0):
        raise SplitError(f"weld_mm ({weld_mm!r}) is not a positive number")
    ids: dict = {}
    faces = []
    for record in records:
        face = []
        for point in corners(record):
            key = (round(point[0] / weld_mm), round(point[1] / weld_mm), round(point[2] / weld_mm))
            face.append(ids.setdefault(key, len(ids)))
        faces.append(face)
    parent = list(range(len(ids)))

    def find(a: int) -> int:
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for a, b, c in faces:
        for other in (b, c):
            ra, ro = find(a), find(other)
            if ra != ro:
                parent[max(ra, ro)] = min(ra, ro)
    groups: dict = {}
    for index, face in enumerate(faces):
        groups.setdefault(find(face[0]), []).append(index)
    return sorted(groups.values(), key=lambda group: group[0])


def bounds(records: list, indices=None) -> tuple:
    """([lo], [hi]) of the corners of ``records`` (those of ``indices``)."""

    low, high = [math.inf] * 3, [-math.inf] * 3
    for index in range(len(records)) if indices is None else indices:
        for point in corners(records[index]):
            for axis in range(3):
                low[axis] = min(low[axis], point[axis])
                high[axis] = max(high[axis], point[axis])
    return low, high


def _box(value, what: str) -> tuple:
    if not (isinstance(value, list) and len(value) == 2 and all(
            isinstance(corner, list) and len(corner) == 3 and all(library_write._number(v) for v in corner) for corner in value)
            and all(value[0][axis] <= value[1][axis] for axis in range(3))):
        raise SplitError(f"{what}: {value!r} is not a box [[lo x, y, z], [hi x, y, z]]")
    return value[0], value[1]


def _inside(point, low, high, slack: float = 0.0) -> bool:
    return all(low[axis] - slack <= point[axis] <= high[axis] + slack for axis in range(3))


def picked(rule, records: list, groups: list, what: str) -> set:
    """The record indices one "pick" rule takes (see the module's docstring)."""

    if not isinstance(rule, dict) or len(rule) != 1:
        raise SplitError(f"{what}: {rule!r} is not one rule (box, component or components_inside)")
    kind, value = next(iter(rule.items()))
    if kind == "box":
        low, high = _box(value, what)
        return {index for index, record in enumerate(records) if all(_inside(point, low, high) for point in corners(record))}
    if kind == "components_inside":
        low, high = _box(value, what)
        found = [group for group in groups if all(_inside(point, low, high) for point in bounds(records, group))]
        if not found:
            raise SplitError(f"{what}: no connected component lies in the box {value!r}")
        return {index for group in found for index in group}
    if kind == "component":
        if not isinstance(value, dict) or not {"box"} <= set(value) <= {"box", "triangles", "tol_mm"}:
            raise SplitError(f"{what}: a component rule is {{box, triangles, tol_mm}}, not {value!r}")
        low, high = _box(value["box"], what)
        tol = value.get("tol_mm", TOL_MM)
        count = value.get("triangles")
        found = []
        for group in groups:
            glow, ghigh = bounds(records, group)
            if all(abs(glow[axis] - low[axis]) <= tol and abs(ghigh[axis] - high[axis]) <= tol for axis in range(3)) \
                    and (count is None or len(group) == count):
                found.append(group)
        if len(found) != 1:
            raise SplitError(f"{what}: {len(found)} connected components have the box {value['box']!r} within {tol} mm"
                             + (f" and {count} triangles" if count is not None else "") + ", not one")
        return set(found[0])
    raise SplitError(f"{what}: {kind!r} is not a rule (box, component or components_inside)")


# -- the shapes the project draws ------------------------------------------------------------------------------------------

def _facet(a, b, c) -> bytes:
    """One facet a, b, c (counter-clockwise seen from outside), its corners rounded to 0.1 um and stored as float32,
    its normal theirs."""

    points = [[round(float(v), 4) + 0.0 for v in point] for point in (a, b, c)]
    u = [points[1][axis] - points[0][axis] for axis in range(3)]
    v = [points[2][axis] - points[0][axis] for axis in range(3)]
    normal = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
    length = math.sqrt(math.fsum(component * component for component in normal))
    normal = [round(component / length, 6) + 0.0 for component in normal] if length > 0 else [0.0, 0.0, 0.0]
    return RECORD.pack(*normal, *points[0], *points[1], *points[2], 0)


def drawn(shape, what: str) -> list:
    """The facet records of one shape of a "draw" list: a box, a cylinder or a prism, closed, facing outward."""

    if not isinstance(shape, dict) or len(shape) != 1:
        raise SplitError(f"{what}: {shape!r} is not one shape (box, cylinder or prism)")
    kind, value = next(iter(shape.items()))
    if kind == "box":
        (x0, y0, z0), (x1, y1, z1) = _box(value, what)
        if not (x0 < x1 and y0 < y1 and z0 < z1):
            raise SplitError(f"{what}: the box {value!r} is flat")
        p = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        quads = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        return [facet for a, b, c, d in quads for facet in (_facet(p[a], p[b], p[c]), _facet(p[a], p[c], p[d]))]
    if kind == "cylinder":
        if not isinstance(value, dict) or not {"from", "to", "radius"} <= set(value) <= {"from", "to", "radius", "segments"}:
            raise SplitError(f"{what}: a cylinder is {{from, to, radius, segments}}, not {value!r}")
        start, end, radius, segments = value["from"], value["to"], value["radius"], value.get("segments", SEGMENTS)
        if not (all(isinstance(point, list) and len(point) == 3 and all(library_write._number(v) for v in point) for point in (start, end))
                and library_write._number(radius) and radius > 0 and isinstance(segments, int) and 3 <= segments <= 96):
            raise SplitError(f"{what}: the cylinder {value!r} has not two points, a positive radius and 3 to 96 segments")
        axis = [end[k] - start[k] for k in range(3)]
        length = math.sqrt(math.fsum(component * component for component in axis))
        if length <= 0:
            raise SplitError(f"{what}: the cylinder {value!r} has no length")
        axis = [component / length for component in axis]
        # Two unit vectors across the axis: from the world axis the cylinder's leans on least.
        least = min(range(3), key=lambda k: (abs(axis[k]), k))
        seed = [1.0 if k == least else 0.0 for k in range(3)]
        u = [axis[1] * seed[2] - axis[2] * seed[1], axis[2] * seed[0] - axis[0] * seed[2], axis[0] * seed[1] - axis[1] * seed[0]]
        norm = math.sqrt(math.fsum(component * component for component in u))
        u = [component / norm for component in u]
        v = [axis[1] * u[2] - axis[2] * u[1], axis[2] * u[0] - axis[0] * u[2], axis[0] * u[1] - axis[1] * u[0]]
        ring = []
        for k in range(segments):
            angle = 2 * math.pi * k / segments
            ring.append([radius * (math.cos(angle) * u[i] + math.sin(angle) * v[i]) for i in range(3)])
        low = [[start[i] + offset[i] for i in range(3)] for offset in ring]
        high = [[end[i] + offset[i] for i in range(3)] for offset in ring]
        out = []
        for k in range(segments):
            j = (k + 1) % segments
            out += [_facet(low[k], low[j], high[j]), _facet(low[k], high[j], high[k]),
                    _facet(start, low[j], low[k]), _facet(end, high[k], high[j])]
        return out
    if kind == "prism":
        if not isinstance(value, dict) or set(value) != {"axis", "from", "to", "profile"}:
            raise SplitError(f"{what}: a prism is {{axis, from, to, profile}}, not {value!r}")
        axis, start, end, profile = value["axis"], value["from"], value["to"], value["profile"]
        if axis not in PRISM_AXES or not (library_write._number(start) and library_write._number(end) and start < end):
            raise SplitError(f"{what}: the prism {value!r} has not an axis x, y or z and a from below its to")
        if not (isinstance(profile, list) and 3 <= len(profile) <= PRISM_CORNERS
                and all(isinstance(point, list) and len(point) == 2 and all(library_write._number(v) for v in point) for point in profile)):
            raise SplitError(f"{what}: the prism's profile is not 3 to {PRISM_CORNERS} corners [p, q]")
        # Convex and counter-clockwise: a left turn at every corner, and the turns one revolution together (a star's
        # corners turn left too, twice round).
        count = len(profile)
        turns = []
        for k in range(count):
            a, b, c = profile[k - 1], profile[k], profile[(k + 1) % count]
            u = (b[0] - a[0], b[1] - a[1])
            v = (c[0] - b[0], c[1] - b[1])
            cross = u[0] * v[1] - u[1] * v[0]
            if cross <= 0:
                raise SplitError(f"{what}: the prism's profile does not turn left at its corner {k + 1} {b!r} "
                                 "(convex, counter-clockwise seen from the axis's positive end, no corner twice or in line)")
            turns.append(math.atan2(cross, u[0] * v[0] + u[1] * v[1]))
        if abs(math.fsum(turns) - 2 * math.pi) > 1e-6:
            raise SplitError(f"{what}: the prism's profile goes round more than once (a star, not a convex polygon)")
        across = PRISM_AXES[axis]
        along = "xyz".index(axis)

        def point(corner, level):
            out = [0.0, 0.0, 0.0]
            out[across[0]], out[across[1]], out[along] = corner[0], corner[1], level
            return out

        low = [point(corner, start) for corner in profile]
        high = [point(corner, end) for corner in profile]
        out = []
        for k in range(count):
            j = (k + 1) % count
            out += [_facet(low[k], low[j], high[j]), _facet(low[k], high[j], high[k])]
        for k in range(1, count - 1):
            out += [_facet(low[0], low[k + 1], low[k]), _facet(high[0], high[k], high[k + 1])]
        return out
    raise SplitError(f"{what}: {kind!r} is not a shape (box, cylinder or prism)")


def own_header(name: str) -> str:
    """A drawn file's header (library_write.own_body() reads it)."""

    return f"FlexiTac-Gen: {name}, drawn by the project, not a vendor's part, mm"


# -- the look files ----------------------------------------------------------------------------------------------------------

def _ordered(text: str):
    return json.loads(text)


def scene_text(document: dict) -> str:
    """A scene's JSON as the scene builder writes it (indent 1, ASCII, a newline at its end)."""

    return json.dumps(document, indent=1, ensure_ascii=True, allow_nan=False) + "\n"


def base_looks(looks: Path = LOOKS) -> dict:
    """The base looks {name: look} of tools/library_looks/base.json (docs/LIBRARY_VIEW.md's table), each checked."""

    path = looks / BASE_FILE
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise SplitError(f"{path.name}: {error}")
    if not isinstance(document, dict) or document.get("format") != BASE_FORMAT or not isinstance(document.get("looks"), dict):
        raise SplitError(f"{path.name} is not a {BASE_FORMAT} document with looks")
    out = {}
    for name, entry in document["looks"].items():
        if not (isinstance(entry, dict) and isinstance(entry.get("for"), str) and entry["for"].strip()):
            raise SplitError(f"{path.name}: the look {name!r} does not say what it is for")
        look = {key: value for key, value in entry.items() if key != "for"}
        problem = None if library_write.LOOK_NAME.fullmatch(name) else "is not named in lower case, digits and hyphens"
        problem = problem or library_write.look_problem(look)
        if problem:
            raise SplitError(f"{path.name}: the look {name!r} {problem}")
        out[name] = look
    return out


def resolved_looks(recipe: dict, base: dict, where: str) -> dict:
    """{name: look} a look file may use: the base looks, and its own (each a base look with its differences and the
    evidence for them; never under a base look's name)."""

    out = dict(base)
    own = recipe.get("looks", {})
    if not isinstance(own, dict):
        raise SplitError(f"{where}: its looks are not a map of names to looks")
    for name, entry in own.items():
        if not (isinstance(name, str) and library_write.LOOK_NAME.fullmatch(name)):
            raise SplitError(f"{where}: its look {name!r} is not named in lower case, digits and hyphens")
        if name in base:
            raise SplitError(f"{where}: its look {name!r} takes a base look's name: a base name means the base's numbers "
                             "(give the part's own look another name and name the base in \"base\")")
        if not (isinstance(entry, dict) and isinstance(entry.get("evidence"), str) and entry["evidence"].strip()):
            raise SplitError(f"{where}: its look {name!r} has no evidence (the photo that shows how it differs from a base look)")
        look = {}
        if "base" in entry:
            if entry["base"] not in base:
                raise SplitError(f"{where}: its look {name!r} is based on {entry['base']!r}, which is no base look")
            look.update(base[entry["base"]])
        look.update({key: value for key, value in entry.items() if key not in ("base", "evidence")})
        for key in [key for key, value in look.items() if value is None]:
            del look[key]
        problem = library_write.look_problem(look)
        if problem:
            raise SplitError(f"{where}: its look {name!r} {problem}")
        out[name] = look
    return out


def recipes(looks: Path = LOOKS, only=None) -> dict:
    """{part: (path, document)} of the look files (every *.json but the base looks), each named after its part."""

    out = {}
    for path in sorted(looks.glob("*.json")) if looks.is_dir() else []:
        if path.name == BASE_FILE:
            continue
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except ValueError as error:
            raise SplitError(f"{path.name} is not JSON: {error}")
        if not isinstance(document, dict) or document.get("format") != FORMAT or not set(document) <= PART_KEYS:
            raise SplitError(f"{path.name} is not a {FORMAT} document of {', '.join(sorted(PART_KEYS))}")
        if document.get("part") != path.stem:
            raise SplitError(f"{path.name} is the look file of {document.get('part')!r}: name it after its part")
        out[path.stem] = (path, document)
    for part in only or ():
        if part not in out:
            raise SplitError(f"no look file {looks.name}/{part}.json")
    return {part: value for part, value in out.items() if only is None or part in only}


# -- one part ----------------------------------------------------------------------------------------------------------------

def _component_names(entry: dict, source: str, where: str) -> list:
    """The components of one body's entry, each checked: [(name, look, pick or None, draw or None)]."""

    out = []
    listed = entry["components"]
    if not (isinstance(listed, list) and listed):
        raise SplitError(f"{where}: the components of {source} are not a list")
    for component in listed:
        if not isinstance(component, dict) or not {"name", "look"} <= set(component) <= {"name", "look", "pick", "draw"} \
                or ("pick" in component) == ("draw" in component):
            raise SplitError(f"{where}: a component of {source} is {{name, look, pick or draw}}, not {component!r}")
        name = component["name"]
        if not (isinstance(name, str) and NAME.fullmatch(name)):
            raise SplitError(f"{where}: the component {name!r} of {source} is not named in lower case, digits, hyphens and underscores")
        out.append((name, component["look"], component.get("pick"), component.get("draw")))
    return out


def registry(notice: str) -> dict:
    """{an unsplit body's path: [its components' paths]} as NOTICE.md's rows record them (SPLIT_NOTE): which committed
    files hold a split body's triangles, whatever the look file calls its components now."""

    out: dict = {}
    for row in library_write.NOTICE_ROW.findall(notice):
        found = SPLIT_FOUND.search(row[3])
        if found:
            out.setdefault(f"{Path(row[0]).parent.as_posix()}/{found.group(1)}", []).append(row[0])
    return out


def build(part: str, recipe: dict, library: Path, base: dict, sources: Path | None = None) -> dict:
    """What one look file gives: {"files": {path relative to the library: bytes} (the component files; a body kept
    whole is not among them), "kept": [the whole bodies' paths], "gone": [the unsplit paths that leave], "scene": the
    scene's text, "rows": {an unsplit body's path: [(component path, sha256)]} (NOTICE.md's rows to write)}."""

    where = f"{part}.json"
    scene_path = library / "scenes" / f"{part}.json"
    try:
        text = scene_path.read_text(encoding="utf-8")
    except OSError:
        raise SplitError(f"{where}: the part has no scene (scenes/{part}.json)")
    scene = _ordered(text)
    if scene_text(scene) != text:
        raise SplitError(f"scenes/{part}.json is not written as the scene builder writes it (indent 1, ASCII): not rewritten")
    looks = resolved_looks(recipe, base, where)
    notice_path = library / "NOTICE.md"
    before = registry(notice_path.read_text(encoding="utf-8") if notice_path.is_file() else "")
    entries = recipe.get("bodies")
    if not isinstance(entries, dict) or not entries:
        raise SplitError(f"{where}: its bodies are not a map of the scene's bodies")
    used: dict = {}

    def look_of(name, what: str):
        if name is None:
            return None
        if name not in looks:
            raise SplitError(f"{where}: {what} names the look {name!r}, neither one of its looks nor a base look")
        used[name] = looks[name]
        return name

    # Each body of the look file: its components' files, or the file kept whole.
    made: dict = {}      # source path -> [(mesh path, bytes or None (kept whole), look)]
    files, kept, gone, rows = {}, [], [], {}
    taken_names: dict = {}
    for source, entry in entries.items():
        if not (isinstance(source, str) and re.fullmatch(rf"bodies/{re.escape(part)}/[\w.-]+\.stl", source)):
            raise SplitError(f"{where}: {source!r} is not a body of bodies/{part}/")
        if not isinstance(entry, dict) or not isinstance(entry.get("sha256"), str):
            raise SplitError(f"{where}: {source} has no sha256 (the unsplit file's: --pin)")
        if "components" not in entry:
            if not set(entry) <= {"sha256", "look"} or "look" not in entry:
                raise SplitError(f"{where}: {source} is {{sha256, look}} (kept whole) or {{sha256, facets_sha256, weld_mm, components}}")
            target = library / source
            if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != entry["sha256"]:
                raise SplitError(f"{where}: {source} is not the file its sha256 pins")
            made[source] = [(source, None, look_of(entry["look"], source))]
            kept.append(source)
            taken_names[source] = source
            continue
        if not set(entry) <= {"sha256", "facets_sha256", "weld_mm", "components"}:
            raise SplitError(f"{where}: {source} is {{sha256, facets_sha256, weld_mm, components}}")
        listed = _component_names(entry, source, where)
        paths = [f"bodies/{part}/{'drawn-' if draw is not None else ''}{name}.stl" for name, _, _, draw in listed]
        for path in paths:
            if path in taken_names or path in entries:
                raise SplitError(f"{where}: {path} is written twice (by {source} and {taken_names.get(path, 'a body kept whole')})")
            taken_names[path] = source
        # The body's records: the unsplit file (in the library, or among the sources), else its components together.  An
        # unsplit file of other bytes is refused, never passed over for the components of the split before (the review
        # of 2026-11-12: a body the scene builder had made anew was split as the old one and removed as a stray).
        header = None
        records = None
        for folder in (library, sources):
            target = folder / source if folder is not None else None
            if target is None or not target.is_file():
                continue
            data = target.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            if digest != entry["sha256"]:
                raise SplitError(f"{where}: {source}{'' if folder is library else f' of {folder}'} is not the file its sha256 pins "
                                 f"(it is {digest[:12]}, the look file pins {entry['sha256'][:12]}): a body made anew is pinned anew "
                                 "(--pin prints its sha256 and facets_sha256; look at its rules again)")
            records, header = facets(data, source), data[:80]
            break
        if records is None:
            records = []
            for path in before.get(source) or [path for path, (_, _, _, draw) in zip(paths, listed) if draw is None]:
                target = library / path
                if not target.is_file():
                    raise SplitError(f"{where}: neither {source} (sha256 {entry['sha256'][:12]}) nor its component {path} is here: "
                                     "give the unsplit body (--source DIR, or the scene builder's)")
                data = target.read_bytes()
                records += facets(data, path)
                header = data[:80]
        digest = facets_sha256(records)
        if entry.get("facets_sha256") != digest:
            raise SplitError(f"{where}: the facets of {source} are not the ones pinned: \"facets_sha256\": \"{digest}\" "
                             f"is what is here ({len(records)} triangles)")
        groups = components(records, entry.get("weld_mm", WELD_MM))
        left = set(range(len(records)))
        parts_made = []
        for path, (name, look, pick, draw) in zip(paths, listed):
            what = f"{where}: {source}: {name}"
            look = look_of(look, name)
            if draw is not None:
                if not (isinstance(draw, list) and draw):
                    raise SplitError(f"{what}: its draw is not a list of shapes")
                data = stl(own_header(name), [record for shape in draw for record in drawn(shape, what)])
            else:
                if pick == "rest":
                    taken = set(left)
                elif isinstance(pick, list) and pick:
                    taken = set()
                    for rule in pick:
                        taken |= picked(rule, records, groups, what)
                    taken &= left
                else:
                    raise SplitError(f"{what}: its pick is not a list of rules or \"rest\"")
                if not taken:
                    raise SplitError(f"{what}: takes no triangle")
                left -= taken
                data = stl(split_header(header), sorted(records[index] for index in taken))
            files[path] = data
            parts_made.append((path, data, look))
        if left:
            raise SplitError(f"{where}: {source}: {len(left)} triangles are taken by no component (end with \"pick\": \"rest\")")
        made[source] = parts_made
        gone.append(source)
        rows[source] = [(path, hashlib.sha256(data).hexdigest()) for (path, data, _), (_, _, _, draw) in zip(parts_made, listed) if draw is None]
    owner = {path: source for source in made for path in before.get(source, ())}
    owner.update({path: source for source, items in made.items() for path, _, _ in items})
    owner.update({source: source for source in made})

    # The scene's bodies: each entry of a body (the unsplit one, or a run of its components from a split before) by
    # its components now; the drawn ones of a split before dropped.
    drawn_before = re.compile(rf"bodies/{re.escape(part)}/drawn-[\w.-]+\.stl")
    bodies, last = [], None
    for body in scene["bodies"]:
        mesh = body.get("mesh")
        source = owner.get(mesh)
        if source is None:
            if isinstance(mesh, str) and drawn_before.fullmatch(mesh):
                continue
            raise SplitError(f"{where}: the scene's body {mesh} is not in the look file (name every body, or \"look\": null)")
        key = (source, json.dumps(body["matrix"]), body["finger"])
        if key == last and mesh != source:
            continue  # the next component of the same copy (copies of a body differ by their matrix or finger)
        last = key
        for path, data, look in made[source]:
            data = (library / path).read_bytes() if data is None else data
            entry = {"mesh": path, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data), "triangles": library_write.stl_triangles(data),
                     "matrix": body["matrix"], "finger": body["finger"]}
            if look is not None:
                entry["look"] = look
            bodies.append(entry)
    missing = sorted(set(made) - {owner[body["mesh"]] for body in bodies})
    if missing:
        raise SplitError(f"{where}: {', '.join(missing)} is no body of the scene")
    # The shapes drawn in the part's frame.
    listed = recipe.get("drawn", [])
    if not isinstance(listed, list):
        raise SplitError(f"{where}: its drawn is not a list")
    for item in listed:
        if not isinstance(item, dict) or not {"name", "look", "draw"} <= set(item) <= {"name", "look", "draw", "matrix", "finger"}:
            raise SplitError(f"{where}: a drawn body is {{name, look, draw, matrix, finger}}, not {item!r}")
        name = item["name"]
        path = f"bodies/{part}/drawn-{name}.stl"
        if not (isinstance(name, str) and NAME.fullmatch(name)) or path in taken_names:
            raise SplitError(f"{where}: the drawn body {name!r} is not named in lower case, digits and hyphens, or is written twice")
        if not (isinstance(item["draw"], list) and item["draw"]):
            raise SplitError(f"{where}: {name}: its draw is not a list of shapes")
        taken_names[path] = "drawn"
        data = stl(own_header(name), [record for shape in item["draw"] for record in drawn(shape, f"{where}: {name}")])
        files[path] = data
        look = look_of(item["look"], name)
        entry = {"mesh": path, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data), "triangles": library_write.stl_triangles(data),
                 "matrix": item.get("matrix", IDENTITY), "finger": item.get("finger")}
        if look is not None:
            entry["look"] = look
        bodies.append(entry)
    part_look = look_of(recipe.get("part_look"), "part_look")
    # The scene: its own keys in their order, the looks' after its bodies.
    extra = {}
    if used:
        extra["looks"] = {name: used[name] for name in sorted(used)}
    if part_look is not None:
        extra["part_look"] = part_look
    if recipe.get("smooth_deg") is not None:
        extra["smooth_deg"] = recipe["smooth_deg"]
    about = scene["about"].split(LOOK_MARK)[0]
    if recipe.get("about"):
        if not isinstance(recipe["about"], str) or LOOK_MARK in recipe["about"]:
            raise SplitError(f"{where}: its about is not a text")
        about += LOOK_MARK + recipe["about"].strip()
    document = {}
    for key, value in scene.items():
        if key in ("looks", "part_look", "smooth_deg"):
            continue
        document[key] = about if key == "about" else bodies if key == "bodies" else value
        if key == "bodies":
            document.update(extra)
    return {"files": files, "kept": kept, "gone": gone, "scene": scene_text(document), "rows": rows}


def notice_text(notice: str, rows: dict, where: str) -> str:
    """NOTICE.md with each split body's row (or its components' rows of a split before) replaced by one row per
    component: the body's source, licence and change, with SPLIT_NOTE and the component's SHA-256."""

    lines = notice.split("\n")
    for source, components_ in rows.items():
        stem = Path(source).name
        mine = []
        for number, line in enumerate(lines):
            match = library_write.NOTICE_ROW.fullmatch(line)
            if not match:
                continue
            found = SPLIT_FOUND.search(match.group(4))
            if match.group(1) == source or (found and found.group(1) == stem and Path(match.group(1)).parent == Path(source).parent):
                mine.append((number, match))
        if not mine:
            raise SplitError(f"{where}: NOTICE.md has no row of {source} (or of its components) to write its components' rows from")
        first, match = mine[0]
        change = SPLIT_FOUND.sub("", match.group(4)).rstrip()
        note = (SPLIT_NOTE if len(components_) > 1 else SPLIT_NOTE_ONE).format(count=len(components_), stem=stem)
        fresh = [f"| `{path}` |{match.group(2)}|{match.group(3)}|{change}{note} | `{digest}` |" for path, digest in components_]
        drop = {number for number, _ in mine}
        lines = [line for number, line in enumerate(lines[:first]) if number not in drop] + fresh \
            + [line for number, line in enumerate(lines[first:], first) if number not in drop]
    return "\n".join(lines)


def run_part(part: str, recipe: dict, library: Path, base: dict, *, check: bool, out: Path | None, sources: Path | None) -> list:
    """Write (or with ``check`` compare) one part: the lines of what differs or was written."""

    where = f"{part}.json"
    built = build(part, recipe, library, base, sources)
    target = out or library
    notice_path = library / "NOTICE.md"
    notice = notice_path.read_text(encoding="utf-8") if notice_path.is_file() else ""
    fresh_notice = notice_text(notice, built["rows"], where) if built["rows"] else notice
    named = set(built["files"]) | set(built["kept"])
    folder = library / "bodies" / part
    stray = sorted(file.relative_to(library).as_posix() for file in folder.glob("*.stl")
                   if file.relative_to(library).as_posix() not in named) if folder.is_dir() else []
    said = []
    if check:
        for path, data in sorted(built["files"].items()):
            if not (library / path).is_file() or (library / path).read_bytes() != data:
                said.append(f"{path} is not what {where} gives")
        if (library / "scenes" / f"{part}.json").read_text(encoding="utf-8") != built["scene"]:
            said.append(f"scenes/{part}.json is not what {where} gives")
        if fresh_notice != notice:
            said.append(f"NOTICE.md's rows of {part}'s bodies are not what {where} gives")
        said += [f"{path}: a body {where} does not give" for path in stray]
        return said
    for path, data in sorted(built["files"].items()):
        file = target / path
        if not file.is_file() or file.read_bytes() != data:
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(data)
            said.append(f"wrote {path} ({library_write.stl_triangles(data)} triangles)")
    scene_file = target / "scenes" / f"{part}.json"
    if not scene_file.is_file() or scene_file.read_text(encoding="utf-8") != built["scene"]:
        scene_file.parent.mkdir(parents=True, exist_ok=True)
        scene_file.write_text(built["scene"], encoding="utf-8")
        said.append(f"wrote scenes/{part}.json")
    if out is None:
        for path in stray:
            (library / path).unlink()
            said.append(f"removed {path} (no body of the scene now)")
        if fresh_notice != notice:
            notice_path.write_text(fresh_notice, encoding="utf-8")
            said.append(f"wrote NOTICE.md's rows of {part}'s bodies")
    else:
        for path in built["kept"]:
            file = out / path
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes((library / path).read_bytes())
        said.append(f"(a dry run into {out}: the library and NOTICE.md are as they were)")
    return said


def unowned(library: Path, owned, looks: Path = LOOKS) -> list:
    """What of the looks in ``library`` no look file gives (``owned``: the parts that have one, in ``looks``), one line each: a scene
    with looks, a part_look, a crease angle, a body's look or a body the project drew; a drawn file in a part's folder;
    a NOTICE row of a split body.  Such things are written by this tool from a look file only: a drawn body's header
    (library_write.own_body()) labels it, the look file's numbers draw it again; a look's numbers are the base table's
    or a look file's own with its evidence.  One scene's looks are another tool's: the showcase's
    (library_write.SHOWCASE_SCENE), written by tools/library_showcase.py from its own table of the base looks and held
    to it by that tool's --check; so are the shapes that tool draws for it, each pinned by its SHA-256
    (library_write.SHOWCASE_BODIES, which library_write.showcase() holds the files to) and drawn again by that tool's
    --check.  A drawn body of the showcase's that is not pinned there is refused as any other."""

    said = []
    scenes = library / "scenes"
    for path in sorted(scenes.glob("*.json")) if scenes.is_dir() else []:
        part = path.stem
        if part in owned or path.name == Path(library_write.SCENES_INDEX).name:
            continue
        try:
            scene = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            continue  # library_write's to say
        if not isinstance(scene, dict):
            continue
        bodies = [body for body in scene.get("bodies") or [] if isinstance(body, dict)]
        has = []
        if path.relative_to(library).as_posix() != library_write.SHOWCASE_SCENE:
            has += [key for key in ("looks", "part_look", "smooth_deg") if key in scene]
            has += ["a body's look"] if any("look" in body for body in bodies) else []
        has += sorted({str(body.get("mesh")) for body in bodies if isinstance(body.get("mesh"), str) and library_write.OWN_BODY.fullmatch(body["mesh"])
                       and body["mesh"] not in library_write.SHOWCASE_BODIES})
        if has:
            said.append(f"scenes/{part}.json has {', '.join(has)}, but {part} has no look file ({looks.name}/{part}.json): "
                        "looks and drawn bodies are written from one")
    folder = library / "bodies"
    for file in sorted(folder.glob("*/drawn-*.stl")) if folder.is_dir() else []:
        if file.parent.name not in owned and file.relative_to(library).as_posix() not in library_write.SHOWCASE_BODIES:
            said.append(f"{file.relative_to(library).as_posix()}: a body the project drew, but {file.parent.name} has no look file to draw it from")
    notice_path = library / "NOTICE.md"
    for source in sorted(registry(notice_path.read_text(encoding="utf-8") if notice_path.is_file() else "")):
        part = Path(source).parent.name
        if part not in owned:
            said.append(f"NOTICE.md has rows of {source}'s split, but {part} has no look file")
    return said


def describe(path: Path, weld_mm: float) -> list:
    """--components: a body's connected components, one line each."""

    records = facets(path.read_bytes(), path.name)
    low, high = bounds(records)
    lines = [f"{path.name}: {len(records)} triangles, box {[round(v, 2) for v in low]} to {[round(v, 2) for v in high]}, welded at {weld_mm} mm:"]
    for number, group in enumerate(components(records, weld_mm)):
        glow, ghigh = bounds(records, group)
        lines.append(f"  c{number:02d}: {len(group)} triangles, box [{', '.join(f'{v:.2f}' for v in glow)}] to [{', '.join(f'{v:.2f}' for v in ghigh)}]")
    return lines


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--only", default=None, metavar="PART,...", help="these parts' look files only")
    parser.add_argument("--check", action="store_true", help="compare the committed files with what the look files give; write nothing")
    parser.add_argument("--library", type=Path, default=LIBRARY, help="the library (default web/library)")
    parser.add_argument("--looks", type=Path, default=LOOKS, help="the look files' folder (default tools/library_looks)")
    parser.add_argument("--source", type=Path, default=None, metavar="DIR", help="a folder laid out like the library holding unsplit bodies")
    parser.add_argument("--out", type=Path, default=None, metavar="DIR", help="write the component files and scenes there (a dry run)")
    parser.add_argument("--pin", type=Path, default=None, metavar="STL", help="print a body's sha256 and facets_sha256")
    parser.add_argument("--components", type=Path, default=None, metavar="STL", help="list a body's connected components")
    parser.add_argument("--weld", type=float, default=WELD_MM, help=f"--components' weld in mm (default {WELD_MM})")
    args = parser.parse_args(argv)
    try:
        for given in (args.pin, args.components):
            if given is not None:
                path = given if given.is_file() else args.library / given
                if args.pin is not None:
                    data = path.read_bytes()
                    print(json.dumps({"sha256": hashlib.sha256(data).hexdigest(), "facets_sha256": facets_sha256(facets(data, path.name)),
                                      "triangles": library_write.stl_triangles(data)}, indent=1))
                else:
                    print("\n".join(describe(path, args.weld)))
                return 0
        only = [item for item in re.split(r"[,\s]+", args.only) if item] if args.only else None
        base = base_looks(args.looks)
        found = recipes(args.looks, only)
        differ = 0
        for part, (_, recipe) in found.items():
            said = run_part(part, recipe, args.library, base, check=args.check, out=args.out, sources=args.source)
            for line in said:
                print(f"{part}: {line}")
            differ += bool(said) if args.check else 0
        if args.check:
            loose = unowned(args.library, set(found), args.looks) if only is None else []
            for line in loose:
                print(line)
            print(f"library_split: {len(found)} look files, {differ} with files that differ" + (f", {len(loose)} looks or drawn bodies without a look file" if loose else "")
                  if differ or loose else f"library_split: {len(found)} look files, the bodies, scenes and NOTICE rows are what they give")
            return 1 if differ or loose else 0
        print(f"library_split: {len(found)} look files done; now tools/library_write.py and the shoot (the scenes changed: their pictures are stale)")
        return 0
    except (SplitError, OSError) as error:
        print(f"library_split: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
