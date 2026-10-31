#!/usr/bin/env python3
"""Compare the Gerber ZIP EasyEDA Pro exports from our .epro2 with our own Direct Gerber ZIP.

Usage (from the project directory)::

    python3 tools/compare_easyeda_gerbers.py EASYEDA_GERBER.zip OUR_DIRECT_GERBER.zip [--step 0.01] [--json report.json]

Both ZIPs describe one board: EasyEDA's export of an ``.epro2`` of
``exporters/easyeda_pro.py`` (Export > PCB Fabrication File (Gerber)) and our
``<build>-<side>-<role>-direct-gerber.zip`` of the same board; the second may
also be that ``.epro2`` itself (its tracks, pads, fills, outline and
stiffeners, read by ``exporters.easyeda_pro.pcb_geometry``).  Each
layer is read from its RS-274X file and filled by scanlines (rows ``--step``
mm apart, at the same heights for both files), then compared:

* copper: the Top Layer (``*.GTL``): tracks, pads and regions;
* coverlay: the Top Solder Mask (``*.GTS``): the openings;
* outline: the Board Outline (``*.GKO``): every drawn segment, filled
  even-odd, so routed cutouts are holes (the stroke width is ignored);
* stiffener: the stiffener layers (``*StiffenerLayer*.G?SL``);

each with its area, bounding box and the area of the symmetric difference
(XOR).  A layer agrees when the XOR is at most ``--tolerance-mm2`` plus
``--relative`` of the larger area.  ``jlcpcb.json`` is compared too: the
count, layer, material and thickness of the FPC stiffeners.  When the outline
of EasyEDA's export is shifted against ours (``--align auto``, the default),
its layers are moved back by that offset first, and the offset is reported.

The reader covers what both writers use: ``%FS``/``%MO``, circle,
rectangle, obround and polygon apertures, aperture macros (primitives 1, 4,
5, 20, 21, as EasyEDA's ``RoundRect``), flashes, linear and circular
interpolation, regions and dark polarity (clear objects are counted and
reported, not subtracted).  Standard library only; exit status 0 when every
layer agrees, 1 when one does not, 2 for unreadable input.
"""

from __future__ import annotations

import argparse
import io
import json
import math
import re
import sys
import zipfile
from pathlib import Path
from typing import Any, Iterable, Sequence

_PROJECT = Path(__file__).resolve().parents[1]

LAYERS = ("copper", "coverlay", "outline", "stiffener")
_PATTERNS = {
    "copper": re.compile(r"\.gtl\Z", re.I),
    "coverlay": re.compile(r"\.gts\Z", re.I),
    "outline": re.compile(r"\.gko\Z", re.I),
    "stiffener": re.compile(r"stiffener.*\.g[tb]sl\Z", re.I),
}
_ARC_STEP_RAD = math.radians(2.0)
_TOKEN = re.compile(r"%[^%]*%|[^*%]+\*", re.S)
_COORD = re.compile(r"([XYIJD])([+-]?\d+(?:\.\d*)?)")


class GerberError(ValueError):
    """An RS-274X construct this reader does not understand."""


# --------------------------------------------------------------------------
# Shapes.  Each is a tuple: ("poly", ring), ("capsule", x0, y0, x1, y1, r), ("rect", x0, y0, x1, y1),
# ("segment", x0, y0, x1, y1) (outline layers only, filled even-odd).
# --------------------------------------------------------------------------


def _rotate(points: Iterable[Sequence[float]], degrees: float) -> list[tuple[float, float]]:
    if not degrees:
        return [(float(x), float(y)) for x, y in points]
    angle = math.radians(degrees)
    cos, sin = math.cos(angle), math.sin(angle)
    return [(x * cos - y * sin, x * sin + y * cos) for x, y in points]


def _moved(shape: tuple, dx: float, dy: float) -> tuple:
    kind = shape[0]
    if kind == "poly":
        return ("poly", [(x + dx, y + dy) for x, y in shape[1]])
    if kind == "capsule":
        return ("capsule", shape[1] + dx, shape[2] + dy, shape[3] + dx, shape[4] + dy, shape[5])
    return (kind, shape[1] + dx, shape[2] + dy, shape[3] + dx, shape[4] + dy)


def shape_bounds(shape: tuple) -> tuple[float, float, float, float]:
    kind = shape[0]
    if kind == "poly":
        xs = [point[0] for point in shape[1]]
        ys = [point[1] for point in shape[1]]
        return (min(xs), min(ys), max(xs), max(ys))
    if kind == "capsule":
        _, x0, y0, x1, y1, radius = shape
        return (min(x0, x1) - radius, min(y0, y1) - radius, max(x0, x1) + radius, max(y0, y1) + radius)
    _, x0, y0, x1, y1 = shape
    return (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))


# --------------------------------------------------------------------------
# RS-274X reader.
# --------------------------------------------------------------------------


def _evaluate(expression: str, variables: dict[int, float]) -> float:
    """An aperture-macro expression: numbers, $n, + - x / and parentheses."""

    text = expression.replace("X", "x")
    tokens = re.findall(r"\$\d+|\d+\.?\d*|\.\d+|[-+x/()]", text)
    if "".join(tokens) != text.replace(" ", ""):
        raise GerberError(f"unsupported macro expression {expression!r}")
    position = 0

    def atom() -> float:
        nonlocal position
        token = tokens[position]
        position += 1
        if token == "(":
            value = add()
            position += 1
            return value
        if token == "-":
            return -atom()
        if token == "+":
            return atom()
        if token.startswith("$"):
            return variables.get(int(token[1:]), 0.0)
        return float(token)

    def multiply() -> float:
        nonlocal position
        value = atom()
        while position < len(tokens) and tokens[position] in ("x", "/"):
            operator = tokens[position]
            position += 1
            right = atom()
            value = value * right if operator == "x" else value / right
        return value

    def add() -> float:
        nonlocal position
        value = multiply()
        while position < len(tokens) and tokens[position] in ("+", "-"):
            operator = tokens[position]
            position += 1
            right = multiply()
            value = value + right if operator == "+" else value - right
        return value

    return add()


def _macro_shapes(body: list[str], parameters: Sequence[float]) -> list[tuple]:
    variables = {index: value for index, value in enumerate(parameters, start=1)}
    shapes: list[tuple] = []
    for statement in body:
        statement = statement.strip()
        if not statement or statement.startswith("0"):
            continue
        assignment = re.fullmatch(r"\$(\d+)=(.+)", statement)
        if assignment:
            variables[int(assignment.group(1))] = _evaluate(assignment.group(2), variables)
            continue
        values = [_evaluate(part, variables) for part in statement.split(",")]
        code = int(values[0])
        if code == 1:  # circle: exposure, diameter, x, y[, rotation]
            exposure, diameter, x, y = values[1:5]
            rotation = values[5] if len(values) > 5 else 0.0
            (x, y), = _rotate([(x, y)], rotation)
            if exposure:
                shapes.append(("capsule", x, y, x, y, diameter / 2))
        elif code == 20:  # vector line: exposure, width, x1, y1, x2, y2, rotation
            exposure, width, x1, y1, x2, y2, rotation = values[1:8]
            length = math.hypot(x2 - x1, y2 - y1)
            if exposure and length > 0:
                nx, ny = -(y2 - y1) / length * width / 2, (x2 - x1) / length * width / 2
                shapes.append(("poly", _rotate([(x1 + nx, y1 + ny), (x2 + nx, y2 + ny), (x2 - nx, y2 - ny), (x1 - nx, y1 - ny)], rotation)))
        elif code == 21:  # center line: exposure, width, height, x, y, rotation
            exposure, width, height, x, y, rotation = values[1:7]
            if exposure:
                corners = [(x - width / 2, y - height / 2), (x + width / 2, y - height / 2), (x + width / 2, y + height / 2), (x - width / 2, y + height / 2)]
                shapes.append(("poly", _rotate(corners, rotation)))
        elif code == 4:  # outline: exposure, n, x0, y0, ..., xn, yn, rotation
            exposure, count = values[1], int(values[2])
            points = [(values[3 + 2 * index], values[4 + 2 * index]) for index in range(count + 1)]
            rotation = values[5 + 2 * count] if len(values) > 5 + 2 * count else 0.0
            if exposure:
                shapes.append(("poly", _rotate(points[:-1] if points[0] == points[-1] else points, rotation)))
        elif code == 5:  # polygon: exposure, vertices, x, y, diameter, rotation
            exposure, vertices, x, y, diameter, rotation = values[1:7]
            if exposure:
                ring = [(x + diameter / 2 * math.cos(2 * math.pi * k / int(vertices)), y + diameter / 2 * math.sin(2 * math.pi * k / int(vertices))) for k in range(int(vertices))]
                shapes.append(("poly", _rotate(ring, rotation)))
        else:
            raise GerberError(f"unsupported aperture macro primitive {code}")
    return shapes


def _aperture_shapes(definition: tuple, x: float, y: float) -> list[tuple]:
    kind = definition[0]
    if kind == "C":
        return [("capsule", x, y, x, y, definition[1] / 2)]
    if kind == "R":
        width, height = definition[1], definition[2]
        return [("rect", x - width / 2, y - height / 2, x + width / 2, y + height / 2)]
    if kind == "O":
        width, height = definition[1], definition[2]
        if width >= height:
            return [("capsule", x - (width - height) / 2, y, x + (width - height) / 2, y, height / 2)]
        return [("capsule", x, y - (height - width) / 2, x, y + (height - width) / 2, width / 2)]
    if kind == "P":
        diameter, vertices, rotation = definition[1], int(definition[2]), definition[3]
        ring = [(diameter / 2 * math.cos(2 * math.pi * k / vertices), diameter / 2 * math.sin(2 * math.pi * k / vertices)) for k in range(vertices)]
        return [("poly", [(px + x, py + y) for px, py in _rotate(ring, rotation)])]
    if kind == "M":
        return [_moved(shape, x, y) for shape in definition[1]]
    raise GerberError(f"unsupported aperture {definition!r}")


def _stroke_shapes(definition: tuple, x0: float, y0: float, x1: float, y1: float) -> list[tuple]:
    if definition[0] == "C":
        return [("capsule", x0, y0, x1, y1, definition[1] / 2)]
    # Another aperture drawn along a line: the hull of its outline at both ends (exact for convex apertures).
    points = []
    for shape in _aperture_shapes(definition, 0.0, 0.0):
        if shape[0] == "rect":
            points.extend([(shape[1], shape[2]), (shape[3], shape[2]), (shape[3], shape[4]), (shape[1], shape[4])])
        elif shape[0] == "poly":
            points.extend(shape[1])
        else:
            radius = shape[5]
            points.extend((radius * math.cos(k * math.pi / 8), radius * math.sin(k * math.pi / 8)) for k in range(16))
    hull = _convex_hull([(px + x0, py + y0) for px, py in points] + [(px + x1, py + y1) for px, py in points])
    return [("poly", hull)]


def _convex_hull(points: Sequence[tuple[float, float]]) -> list[tuple[float, float]]:
    points = sorted(set(points))
    if len(points) < 3:
        return list(points)

    def cross(o: tuple, a: tuple, b: tuple) -> float:
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower: list = []
    for point in points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)
    upper: list = []
    for point in reversed(points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)
    return lower[:-1] + upper[:-1]


def _arc_points(start: tuple[float, float], end: tuple[float, float], center: tuple[float, float], clockwise: bool) -> list[tuple[float, float]]:
    radius = math.hypot(start[0] - center[0], start[1] - center[1])
    a0 = math.atan2(start[1] - center[1], start[0] - center[0])
    a1 = math.atan2(end[1] - center[1], end[0] - center[0])
    sweep = a1 - a0
    if clockwise:
        while sweep >= 0:
            sweep -= 2 * math.pi
    else:
        while sweep <= 0:
            sweep += 2 * math.pi
    if math.hypot(end[0] - start[0], end[1] - start[1]) < 1e-9:
        sweep = -2 * math.pi if clockwise else 2 * math.pi
    steps = max(1, int(math.ceil(abs(sweep) / _ARC_STEP_RAD)))
    points = [(center[0] + radius * math.cos(a0 + sweep * k / steps), center[1] + radius * math.sin(a0 + sweep * k / steps)) for k in range(1, steps)]
    return [*points, end]


def read_gerber(text: str, outline: bool = False) -> dict[str, Any]:
    """The shapes (mm) of an RS-274X layer: ``{"shapes", "clear_objects", "units"}``.

    With ``outline`` every drawn segment is kept as a ``segment`` (the
    aperture ignored) and flashes are dropped, for an even-odd fill.
    """

    integer, decimal = 4, 6
    scale = 1.0
    apertures: dict[int, tuple] = {}
    macros: dict[str, list[str]] = {}
    current = None
    x = y = 0.0
    mode = "G01"
    multi_quadrant = True
    region: list[list[tuple[float, float]]] | None = None
    shapes: list[tuple] = []
    clear = 0
    dark = True

    def number(token: str, value: str) -> float:
        if "." in value:
            return float(value) * scale
        sign = -1.0 if value.startswith("-") else 1.0
        digits = value.lstrip("+-")
        return sign * int(digits) / 10 ** decimal * scale

    for match in _TOKEN.finditer(text):
        token = match.group(0).strip()
        if token.startswith("%"):
            for block in [part for part in token.strip("%").split("*") if part.strip()]:
                block = block.strip()
                if block.startswith("FS"):
                    found = re.search(r"X(\d)(\d)Y(\d)(\d)", block)
                    if not found or "I" in block[2:4]:
                        raise GerberError(f"unsupported format {block!r}")
                    integer, decimal = int(found.group(1)), int(found.group(2))
                elif block.startswith("MO"):
                    scale = 25.4 if block == "MOIN" else 1.0
                elif block.startswith("AD"):
                    found = re.fullmatch(r"ADD(\d+)([A-Za-z_][\w.$]*)(?:,(.*))?", block)
                    if not found:
                        raise GerberError(f"unsupported aperture definition {block!r}")
                    code, name, arguments = int(found.group(1)), found.group(2), found.group(3)
                    values = [float(value) * scale for value in arguments.split("X")] if arguments else []
                    if name == "C":
                        apertures[code] = ("C", values[0])
                    elif name in ("R", "O"):
                        apertures[code] = (name, values[0], values[1])
                    elif name == "P":
                        apertures[code] = ("P", values[0], values[1] / scale, values[2] / scale if len(values) > 2 else 0.0)
                    elif name in macros:
                        raw = [float(value) for value in arguments.split("X")] if arguments else []
                        apertures[code] = ("M", [_scaled(shape, scale) for shape in _macro_shapes(macros[name], raw)])
                    else:
                        raise GerberError(f"unknown aperture {name!r}")
                elif block.startswith("AM"):
                    name = block[2:]
                    statements = [part.strip() for part in token.strip("%").split("*")[1:] if part.strip()]
                    macros[name] = statements
                    break
                elif block.startswith("LP"):
                    dark = block == "LPD"
                elif block.startswith(("IP", "OF", "SF", "MI", "IR", "TF", "TA", "TO", "TD", "LN")):
                    continue
                else:
                    continue
            continue
        token = token[:-1]
        if not token or token.startswith("G04"):
            continue
        if token in ("M02", "M00", "M01"):
            break
        if token == "G36":
            region = []
            continue
        if token == "G37":
            for contour in region or []:
                if len(contour) > 2 and not outline:
                    shapes.append(("poly", contour[:-1] if contour[0] == contour[-1] else contour))
            region = None
            continue
        if token in ("G74", "G75"):
            multi_quadrant = token == "G75"
            continue
        gcode = re.match(r"G0?([123])(?!\d)", token)
        if gcode:
            mode = f"G0{gcode.group(1)}"
            token = token[gcode.end():]
        token = re.sub(r"^G5[45]", "", token)
        select = re.fullmatch(r"D(\d+)", token)
        if select and int(select.group(1)) >= 10:
            current = int(select.group(1))
            continue
        if not token:
            continue
        fields = dict((key, value) for key, value in _COORD.findall(token))
        new_x = number("X", fields["X"]) if "X" in fields else x
        new_y = number("Y", fields["Y"]) if "Y" in fields else y
        operation = int(fields["D"]) if "D" in fields else 1
        if operation == 2:
            if region is not None:
                region.append([(new_x, new_y)])
            x, y = new_x, new_y
            continue
        if operation == 3:
            if not outline:
                if current not in apertures:
                    raise GerberError(f"flash without a defined aperture (D{current})")
                if dark:
                    shapes.extend(_aperture_shapes(apertures[current], new_x, new_y))
                else:
                    clear += 1
            x, y = new_x, new_y
            continue
        if operation != 1:
            raise GerberError(f"unsupported operation D{operation:02d}")
        if mode == "G01":
            path = [(new_x, new_y)]
        else:
            if not multi_quadrant:
                raise GerberError("single-quadrant arcs (G74) are not read")
            i = number("I", fields["I"]) if "I" in fields else 0.0
            j = number("J", fields["J"]) if "J" in fields else 0.0
            path = _arc_points((x, y), (new_x, new_y), (x + i, y + j), mode == "G02")
        if region is not None:
            if not region:
                region.append([(x, y)])
            region[-1].extend(path)
        else:
            previous = (x, y)
            for point in path:
                if outline:
                    shapes.append(("segment", previous[0], previous[1], point[0], point[1]))
                elif not dark:
                    clear += 1
                else:
                    if current not in apertures:
                        raise GerberError(f"stroke without a defined aperture (D{current})")
                    shapes.extend(_stroke_shapes(apertures[current], previous[0], previous[1], point[0], point[1]))
                previous = point
        x, y = new_x, new_y
    return {"shapes": shapes, "clear_objects": clear}


def _scaled(shape: tuple, scale: float) -> tuple:
    if scale == 1.0:
        return shape
    kind = shape[0]
    if kind == "poly":
        return ("poly", [(x * scale, y * scale) for x, y in shape[1]])
    if kind == "capsule":
        return ("capsule", *(value * scale for value in shape[1:]))
    return (kind, *(value * scale for value in shape[1:]))


# --------------------------------------------------------------------------
# Scanline fill and comparison.
# --------------------------------------------------------------------------


def _rows(low: float, high: float, step: float) -> range:
    """Row indices k whose centre (k + 0.5) * step lies in [low, high]."""

    return range(int(math.ceil(low / step - 0.5)), int(math.floor(high / step - 0.5)) + 1)


def _ring_crossings(ring: Sequence[tuple[float, float]], step: float, rows: dict[int, list[float]]) -> None:
    count = len(ring)
    for index in range(count):
        (x0, y0), (x1, y1) = ring[index], ring[(index + 1) % count]
        if y0 == y1:
            continue
        low, high = (y0, y1) if y0 < y1 else (y1, y0)
        for k in _rows(low, high, step):
            y = (k + 0.5) * step
            if low <= y < high:  # half-open: a vertex on the row counts once
                rows.setdefault(k, []).append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))


def _pairs(crossings: dict[int, list[float]], out: dict[int, list[tuple[float, float]]]) -> None:
    for k, xs in crossings.items():
        xs.sort()
        out.setdefault(k, []).extend((xs[index], xs[index + 1]) for index in range(0, len(xs) - 1, 2))


def _capsule_interval(x0: float, y0: float, x1: float, y1: float, radius: float, y: float) -> tuple[float, float] | None:
    low, high = math.inf, -math.inf
    for cx, cy in ((x0, y0), (x1, y1)):
        dy = y - cy
        if abs(dy) <= radius:
            half = math.sqrt(radius * radius - dy * dy)
            low, high = min(low, cx - half), max(high, cx + half)
    length = math.hypot(x1 - x0, y1 - y0)
    if length > 0:
        nx, ny = -(y1 - y0) / length * radius, (x1 - x0) / length * radius
        quad = ((x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x0 - nx, y0 - ny))
        for index in range(4):
            (ax, ay), (bx, by) = quad[index], quad[(index + 1) % 4]
            if ay == by:
                if ay == y:
                    low, high = min(low, ax, bx), max(high, ax, bx)
                continue
            if min(ay, by) <= y <= max(ay, by):
                cx = ax + (y - ay) * (bx - ax) / (by - ay)
                low, high = min(low, cx), max(high, cx)
    return (low, high) if low <= high else None


def fill(shapes: Iterable[tuple], step: float) -> dict[int, list[tuple[float, float]]]:
    """Row -> merged x intervals of the union of ``shapes`` (``segment`` shapes filled even-odd together)."""

    intervals: dict[int, list[tuple[float, float]]] = {}
    segments: dict[int, list[float]] = {}
    for shape in shapes:
        kind = shape[0]
        if kind == "poly":
            crossings: dict[int, list[float]] = {}
            _ring_crossings(shape[1], step, crossings)
            _pairs(crossings, intervals)
        elif kind == "rect":
            _, x0, y0, x1, y1 = shape
            for k in _rows(y0, y1, step):
                intervals.setdefault(k, []).append((x0, x1))
        elif kind == "capsule":
            _, x0, y0, x1, y1, radius = shape
            for k in _rows(min(y0, y1) - radius, max(y0, y1) + radius, step):
                found = _capsule_interval(x0, y0, x1, y1, radius, (k + 0.5) * step)
                if found is not None:
                    intervals.setdefault(k, []).append(found)
        elif kind == "segment":
            _, x0, y0, x1, y1 = shape
            if y0 == y1:
                continue
            low, high = (y0, y1) if y0 < y1 else (y1, y0)
            for k in _rows(low, high, step):
                y = (k + 0.5) * step
                if low <= y < high:
                    segments.setdefault(k, []).append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
        else:
            raise ValueError(f"unknown shape {kind}")
    _pairs(segments, intervals)
    return {k: _merge(spans) for k, spans in intervals.items()}


def _merge(spans: list[tuple[float, float]]) -> list[tuple[float, float]]:
    merged: list[list[float]] = []
    for low, high in sorted(spans):
        if merged and low <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], high)
        else:
            merged.append([low, high])
    return [(low, high) for low, high in merged]


def _length(spans: Sequence[tuple[float, float]]) -> float:
    return math.fsum(high - low for low, high in spans)


def _xor_length(first: Sequence[tuple[float, float]], second: Sequence[tuple[float, float]]) -> float:
    events = sorted([(low, 1, 0) for low, _ in first] + [(high, -1, 0) for _, high in first] + [(low, 0, 1) for low, _ in second] + [(high, 0, -1) for _, high in second])
    a = b = 0
    previous = None
    pieces = []
    for x, da, db in events:
        if previous is not None and (a > 0) != (b > 0):
            pieces.append(x - previous)
        a += da
        b += db
        previous = x
    return math.fsum(pieces)


def layer_summary(rows: dict[int, list[tuple[float, float]]], step: float) -> dict[str, Any]:
    if not rows:
        return {"area_mm2": 0.0, "bbox_mm": None}
    keys = sorted(rows)
    area = math.fsum(_length(rows[k]) for k in keys) * step
    xs = [span[0] for k in keys for span in rows[k][:1]] + [span[1] for k in keys for span in rows[k][-1:]]
    return {"area_mm2": round(area, 6), "bbox_mm": [round(min(xs), 4), round(keys[0] * step, 4), round(max(xs), 4), round((keys[-1] + 1) * step, 4)]}


def compare_rows(first: dict[int, list], second: dict[int, list], step: float) -> float:
    keys = set(first) | set(second)
    return math.fsum(_xor_length(first.get(k, []), second.get(k, [])) for k in keys) * step


# --------------------------------------------------------------------------
# ZIPs.
# --------------------------------------------------------------------------


def layer_files(names: Iterable[str]) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {layer: [] for layer in LAYERS}
    for name in names:
        base = name.rsplit("/", 1)[-1]
        for layer, pattern in _PATTERNS.items():
            if pattern.search(base):
                found[layer].append(name)
    return found


def read_zip(data: bytes) -> dict[str, Any]:
    """Every compared layer of a Gerber ZIP as shapes, and its ``jlcpcb.json`` (or None)."""

    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = archive.namelist()
        files = layer_files(names)
        layers = {}
        clear = {}
        for layer, members in files.items():
            shapes: list[tuple] = []
            count = 0
            for member in sorted(members):
                parsed = read_gerber(archive.read(member).decode("ascii", "replace"), outline=layer == "outline")
                shapes.extend(parsed["shapes"])
                count += parsed["clear_objects"]
            layers[layer] = shapes
            clear[layer] = count
        metadata = None
        for name in names:
            if name.rsplit("/", 1)[-1] == "jlcpcb.json":
                metadata = json.loads(archive.read(name).decode("utf-8"))
    return {"layers": layers, "files": files, "clear_objects": clear, "jlcpcb": metadata}


def _outline_origin(shapes: Sequence[tuple]) -> tuple[float, float] | None:
    if not shapes:
        return None
    bounds = [shape_bounds(shape) for shape in shapes]
    return (min(bound[0] for bound in bounds), min(bound[1] for bound in bounds))


def _stiffener_records(metadata: Any) -> list[tuple[str, str, str]]:
    if not isinstance(metadata, dict):
        return []
    return sorted((str(item.get("layer")), str(item.get("material")), f"{float(item.get('thickness')):g}") for item in metadata.get("fpcStiffeners", []))


def compare_layers(easyeda: dict[str, Any], ours: dict[str, Any], step: float = 0.01, tolerance_mm2: float = 0.02, relative: float = 0.001, align: str = "auto") -> dict[str, Any]:
    """Compare two read ZIPs (:func:`read_zip`) layer by layer; see the module text."""

    offset = (0.0, 0.0)
    if align == "auto":
        a, b = _outline_origin(easyeda["layers"]["outline"]), _outline_origin(ours["layers"]["outline"])
        if a is not None and b is not None and math.hypot(a[0] - b[0], a[1] - b[1]) > 1e-3:
            offset = (b[0] - a[0], b[1] - a[1])
    report: dict[str, Any] = {"step_mm": step, "offset_applied_mm": [round(offset[0], 6), round(offset[1], 6)], "layers": {}, "ok": True}
    for layer in LAYERS:
        theirs = [_moved(shape, *offset) for shape in easyeda["layers"][layer]] if offset != (0.0, 0.0) else easyeda["layers"][layer]
        mine = ours["layers"][layer]
        entry: dict[str, Any] = {"easyeda_files": easyeda["files"][layer], "our_files": ours["files"][layer]}
        if not theirs and not mine:
            entry.update(status="absent in both", ok=True)
        else:
            first, second = fill(theirs, step), fill(mine, step)
            easy, own = layer_summary(first, step), layer_summary(second, step)
            xor = compare_rows(first, second, step)
            limit = tolerance_mm2 + relative * max(easy["area_mm2"], own["area_mm2"])
            entry.update(
                easyeda=easy, ours=own, xor_mm2=round(xor, 6), limit_mm2=round(limit, 6),
                clear_objects={"easyeda": easyeda["clear_objects"][layer], "ours": ours["clear_objects"][layer]},
                ok=bool(theirs) and bool(mine) and xor <= limit,
            )
            entry["status"] = "agrees" if entry["ok"] else ("missing in one ZIP" if not (theirs and mine) else "differs")
        report["layers"][layer] = entry
        report["ok"] = report["ok"] and entry["ok"]
    stiffeners = {"easyeda": _stiffener_records(easyeda["jlcpcb"]), "ours": _stiffener_records(ours["jlcpcb"])}
    stiffeners["ok"] = stiffeners["easyeda"] == stiffeners["ours"]
    report["jlcpcb_stiffeners"] = stiffeners
    report["ok"] = report["ok"] and stiffeners["ok"]
    return report


def project_layers(data: bytes) -> dict[str, Any]:
    """The layers of an ``.epro2`` of exporters/easyeda_pro.py in the form of :func:`read_zip`.

    Copper: its tracks (round-ended, as EasyEDA draws them) and pads;
    coverlay: the Top Solder Mask fills and the pads (their mask expansion
    is zero); outline: every BOARD_OUTLINE ring as segments; stiffener: the
    FPC_FILL rings; ``jlcpcb.json``: one record per FPC_FILL.
    """

    sys.path.insert(0, str(_PROJECT))
    from exporters.easyeda_pro import pcb_geometry, read_epro2

    geometry = pcb_geometry(read_epro2(data))
    pads = [("poly", list(pad["ring"])) for pad in geometry["pads"] if pad["layer"] == 1]
    copper = [*pads]
    for track in geometry["tracks"]:
        points = track["points"]
        copper.extend(("capsule", a[0], a[1], b[0], b[1], track["width_mm"] / 2) for a, b in zip(points, points[1:]))
    outline = []
    for ring in geometry["outline"]:
        outline.extend(("segment", a[0], a[1], b[0], b[1]) for a, b in zip(ring, [*ring[1:], ring[0]]))
    names = {"Polyimide": "pi", "FR4": "fr4", "Stainless Steel": "gp"}
    stiffeners = [
        {"layer": "top" if item["layer"] == 58 else "bottom", "material": names.get(item["material"], item["material"]), "thickness": f"{float(item['thickness_mm']):g}"}
        for item in geometry["stiffeners"]
    ]
    layers = {
        "copper": copper,
        "coverlay": [("poly", list(ring)) for ring in geometry["coverlay"]] + pads,
        "outline": outline,
        "stiffener": [("poly", list(item["ring"])) for item in geometry["stiffeners"]],
    }
    return {"layers": layers, "files": {layer: ["(.epro2)"] for layer in LAYERS}, "clear_objects": {layer: 0 for layer in LAYERS}, "jlcpcb": {"fpcStiffeners": stiffeners}}


def compare_zips(easyeda_zip: bytes, our_zip: bytes, **options: Any) -> dict[str, Any]:
    """Compare EasyEDA's Gerber ZIP with our Direct Gerber ZIP, or with the ``.epro2`` itself
    (``our_zip`` may be the bytes of either: a project holds ``project2.json``)."""

    with zipfile.ZipFile(io.BytesIO(our_zip)) as archive:
        is_project = "project2.json" in archive.namelist()
    ours = project_layers(our_zip) if is_project else read_zip(our_zip)
    return compare_layers(read_zip(easyeda_zip), ours, **options)


def _print(report: dict[str, Any]) -> None:
    print(f"rows every {report['step_mm']} mm; EasyEDA layers moved by {report['offset_applied_mm']} mm")
    for layer, entry in report["layers"].items():
        if "easyeda" not in entry:
            print(f"{layer:10s} {entry['status']}")
            continue
        easy, own = entry["easyeda"], entry["ours"]
        print(f"{layer:10s} {entry['status']:18s} area {easy['area_mm2']:.4f} / {own['area_mm2']:.4f} mm2, XOR {entry['xor_mm2']:.4f} mm2 (limit {entry['limit_mm2']:.4f})")
        print(f"{'':10s} bbox EasyEDA {easy['bbox_mm']}  ours {own['bbox_mm']}")
    stiffeners = report["jlcpcb_stiffeners"]
    print(f"jlcpcb.json stiffeners: EasyEDA {stiffeners['easyeda']}  ours {stiffeners['ours']}  -> {'same' if stiffeners['ok'] else 'DIFFERENT'}")
    print("RESULT:", "every layer agrees" if report["ok"] else "DIFFERENCES FOUND")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("easyeda_zip", help="the Gerber ZIP EasyEDA Pro exported from our .epro2")
    parser.add_argument("our_zip", help="our Direct Gerber ZIP of the same board, or the .epro2 EasyEDA imported")
    parser.add_argument("--step", type=float, default=0.01, help="scanline spacing in mm (default 0.01)")
    parser.add_argument("--tolerance-mm2", type=float, default=0.02, help="allowed XOR area per layer (default 0.02 mm2)")
    parser.add_argument("--relative", type=float, default=0.001, help="plus this fraction of the layer area (default 0.001)")
    parser.add_argument("--align", choices=("auto", "none"), default="auto", help="move EasyEDA's layers onto our outline (default auto)")
    parser.add_argument("--json", help="also write the report as JSON to this file")
    args = parser.parse_args(argv)
    try:
        with open(args.easyeda_zip, "rb") as handle:
            easyeda = handle.read()
        with open(args.our_zip, "rb") as handle:
            ours = handle.read()
        report = compare_zips(easyeda, ours, step=args.step, tolerance_mm2=args.tolerance_mm2, relative=args.relative, align=args.align)
    except (OSError, zipfile.BadZipFile, GerberError, ValueError, KeyError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    _print(report)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2)
            handle.write("\n")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
