"""IPC-D-356A bare-board netlist records (fixed 80-column text).

Only the subset the exporter needs: comment and parameter records, SMD test
records (``327``) in SI units (``P  UNITS CUST 1``: millimetres at 0.001 mm
resolution, degrees) and the ``999`` end-of-job record, plus a strict reader
of the same subset for the exporter's read-back check.  Test-record columns
follow IPC-D-356A, which is also what third-party readers such as gerbonara
expect: net name 4-17, reference designator 21-26, ``-`` 27, pin 28-31,
mid-net flag 32, hole 33-38, access 39-41, X/Y 42-57, feature size 58-67,
rotation 68-71, soldermask 73-74.
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

UNITS = "CUST 1"
# Every test point is a land on the primary (top copper) side, exposed there
# and covered on the secondary side (``S2``, as KiCad and Altium write top
# SMD pads).
_RECORD = "327"
_ACCESS = "A01"
_SOLDERMASK = "S2"
_LINE_LIMIT = 80
_STEP_MM = 0.001
_MAX_LOCATION = 999_999  # sign + 6 digits of 0.001 mm
_MAX_SIZE = 9_999  # 4 digits of 0.001 mm
_FIELD = re.compile(r"[A-Za-z0-9_+./-]+\Z")
_FIELD_WIDTHS = {"net": 14, "refdes": 6, "pin": 4}


def netlist_text(comments: Sequence[str], parameters: Sequence[tuple[str, str]], points: Sequence[Mapping[str, Any]]) -> str:
    """The netlist as text: comments, parameters, one test record per point, ``999``.

    Each point has ``net``, ``refdes``, ``pin``, the land centre ``x``/``y``
    and its ``width``/``height`` in millimetres.  A field that does not fit
    its columns raises ``ValueError``; nothing is truncated.
    """

    lines = [f"C  {comment}".rstrip() for comment in comments]
    lines += [f"P  {name:<5} {value}" for name, value in parameters]
    if ("UNITS", UNITS) not in parameters:
        raise ValueError(f"the netlist must declare UNITS {UNITS}")
    lines += [_test_record(point) for point in points]
    lines.append("999")
    for line in lines:
        if len(line) > _LINE_LIMIT or not line.isascii() or not line.isprintable():
            raise ValueError(f"netlist line is not printable ASCII of at most {_LINE_LIMIT} columns: {line!r}")
    return "\n".join(lines) + "\n"


def read_netlist(text: str) -> tuple[dict[str, str], list[dict[str, Any]]]:
    """Parameters and test records of a netlist in the subset written here.

    Anything else (other record types, misplaced columns, a missing end
    record or unit) raises ``ValueError``.
    """

    if not text.endswith("\n"):
        raise ValueError("the netlist does not end with a newline")
    lines = text[:-1].split("\n")
    if lines[-1] != "999":
        raise ValueError("the netlist does not end with the 999 end-of-job record")
    parameters: dict[str, str] = {}
    records: list[dict[str, Any]] = []
    for line in lines[:-1]:
        if len(line) > _LINE_LIMIT or not line.isascii():
            raise ValueError(f"netlist line longer than {_LINE_LIMIT} columns or not ASCII: {line!r}")
        if line.startswith("C"):
            continue
        if line.startswith("P  "):
            name, _, value = line[3:].partition(" ")
            parameters[name] = value.strip()
        elif line.startswith(_RECORD):
            records.append(_parse_test_record(line))
        else:
            raise ValueError(f"unexpected netlist record: {line!r}")
    if parameters.get("UNITS") != UNITS:
        raise ValueError(f"the netlist does not declare UNITS {UNITS}")
    return parameters, records


def _test_record(point: Mapping[str, Any]) -> str:
    text = {key: str(point[key]) for key in _FIELD_WIDTHS}
    for key, width in _FIELD_WIDTHS.items():
        if not _FIELD.fullmatch(text[key]) or len(text[key]) > width:
            raise ValueError(f"test point {key} {text[key]!r} is not 1-{width} characters of [A-Za-z0-9_+./-]")
    x, y = (_steps(point[key], _MAX_LOCATION, signed=True) for key in ("x", "y"))
    width, height = (_steps(point[key], _MAX_SIZE, signed=False) for key in ("width", "height"))
    return (
        f"{_RECORD}{text['net']:<14}   {text['refdes']:<6}-{text['pin']:<4} {'':6}{_ACCESS}"
        f"X{x:+07d}Y{y:+07d}X{width:04d}Y{height:04d}R000 {_SOLDERMASK}"
    )


def _parse_test_record(line: str) -> dict[str, Any]:
    fixed = ((17, 20, "   "), (26, 27, "-"), (31, 38, " " * 7), (38, 41, _ACCESS), (41, 42, "X"), (49, 50, "Y"),
             (57, 58, "X"), (62, 63, "Y"), (67, 72, "R000 "), (72, 74, _SOLDERMASK))
    if len(line) != 74 or any(line[start:end] != value for start, end, value in fixed):
        raise ValueError(f"test record does not follow the IPC-D-356A columns: {line!r}")
    try:
        x, y = int(line[42:49]) * _STEP_MM, int(line[50:57]) * _STEP_MM
        width, height = int(line[58:62]) * _STEP_MM, int(line[63:67]) * _STEP_MM
    except ValueError as error:
        raise ValueError(f"test record has a malformed number: {line!r}") from error
    return {
        "net": line[3:17].strip(),
        "refdes": line[20:26].strip(),
        "pin": line[27:31].strip(),
        "x": x,
        "y": y,
        "width": width,
        "height": height,
    }


def _steps(value: Any, limit: int, *, signed: bool) -> int:
    steps = int(round(float(value) / _STEP_MM))
    if abs(steps) > limit or (not signed and steps <= 0):
        raise ValueError(f"{value!r} mm does not fit an IPC-D-356A field of {limit} x {_STEP_MM} mm")
    return steps
