"""The tactile readers CAD mode sizes the tails for (fit option ``reader``).

A reader scans a matrix of *sense* lines against *drive* lines through two
0.5 mm ZIF connectors, FPC1 (the sense lines ``SR<n>``) and FPC2 (the drive
lines ``SC<n>``).  Either electrode set may take either connector; each
tail is then sized to its connector's pin count (``connector.row_pins`` and
``connector.column_pins``), and the unused positions get isolated NC
contacts.  A reader is named by its two connectors' line counts, the
larger first (``32x16``: 32 drive lines, 16 sense lines):

========  =======  =======  =====================================
name      sense    drive    frame
========  =======  =======  =====================================
16x16     16       16       ``payload[(SC - 1) * 16 + (SR - 1)]``
32x16     16       32       ``payload[(SC - 1) * 16 + (SR - 1)]`` (the FlexiTac RevB.1)
32x32     32       32       ``payload[(SC - 1) * 32 + (SR - 1)]``
48x48     48       48       ``payload[(SC - 1) * 48 + (SR - 1)]``
========  =======  =======  =====================================

``32x16`` is the FlexiTac reader (``flexitac`` is accepted as its name, and
the legacy fit option ``connector: flexitac`` means it): 16 sense lines on
a 16-pin tail and 32 drive lines on a 32-pin tail.  On a square reader the
Row lines take the sense connector.  ``none`` sizes each tail to its own
lines (one contact per line) and ``auto`` takes the smallest reader that
holds the readout (by its number of crossings).
"""

from __future__ import annotations

from typing import Any, Mapping

# name -> (sense lines, drive lines), smallest first (by sense x drive).
READERS = {"16x16": (16, 16), "32x16": (16, 32), "32x32": (32, 32), "48x48": (48, 48)}
READER_CHOICES = ("none", "auto", *READERS)
READER_ALIASES = {"flexitac": "32x16"}
# The legacy fit option ``connector`` (before the reader option): its values as readers.
LEGACY_CONNECTOR = {"channels": "none", "flexitac": "32x16"}
FLEXITAC = "32x16"


def holds(rows: int, columns: int, name: str) -> bool:
    """Whether the reader takes a rows x columns readout (either electrode set on either connector)."""

    sense, drive = READERS[name]
    return (rows <= sense and columns <= drive) or (rows <= drive and columns <= sense)


def choose(rows: int, columns: int, option: str) -> Any:
    """The reader of a readout for the fit option: a reader name, or None (``none``, or nothing holds it)."""

    if option == "none":
        return None
    if option == "auto":
        return next((name for name in READERS if holds(rows, columns, name)), None)
    return option if holds(rows, columns, option) else None


def connector(rows: int, columns: int, option: str) -> dict:
    """``connector`` of the engine design: the reader's pin counts, or null pins (one contact per line)."""

    name = choose(rows, columns, option)
    if name is None:
        return {"row_pins": None, "column_pins": None}
    sense, drive = READERS[name]
    # The Row lines take the sense connector when they fit it and the Column lines fit the drive one.
    if rows <= sense and columns <= drive:
        return {"row_pins": sense, "column_pins": drive}
    return {"row_pins": drive, "column_pins": sense}


def rejection(rows: int, columns: int, option: str) -> Any:
    """Why the fit drops a rows x columns candidate for the reader option, or None when it takes it."""

    if option == "none" or choose(rows, columns, option) is not None:
        return None
    if option == FLEXITAC:
        return "more lines than the FlexiTac reader (16 + 32)"
    if option == "auto":
        return "more lines than the largest reader (48 x 48)"
    sense, drive = READERS[option]
    return f"more lines than the {sense} x {drive} reader"


def of_design(option: str, row_pins: Any, column_pins: Any) -> Any:
    """The reader a built design's tails fit, for the fit option the placement was fitted with.

    ``none`` keeps the map's rule from before the reader option: tails of 16
    and 32 pins are read as the FlexiTac.  A named reader holds when the tails
    have its pin counts; ``auto`` finds the reader with those pin counts.
    """

    pins = sorted((row_pins, column_pins))
    if option == "none":
        return FLEXITAC if pins == [16, 32] else None
    names = list(READERS) if option == "auto" else [option]
    for name in names:
        if pins == sorted(READERS[name]):
            return name
    return None


def of_readout(rows: int, columns: int, option: str) -> Any:
    """The reader a fitted readout's tails fit: ``metrics.reader`` of a proposal.

    The reader the taxel map reports for the design the fit builds
    (:func:`of_design` of its tails' pin counts), so a proposal and its map
    name the same reader: with ``none`` a 16 x 32 (or 32 x 16) readout has
    tails of 16 and 32 pins, which the map reads as the FlexiTac.
    """

    pins = connector(rows, columns, option)
    row_pins = rows if pins["row_pins"] is None else pins["row_pins"]
    column_pins = columns if pins["column_pins"] is None else pins["column_pins"]
    return of_design(option, row_pins, column_pins)


def walk_caps(option: str, rows_cap: int, columns_cap: int) -> list:
    """The ``(rows, columns)`` caps of a readout within ``rows_cap`` x ``columns_cap`` that the reader option takes.

    A named reader holds a readout in either orientation, so it gives up to
    two caps (``32x16``: 16 x 32 and 32 x 16); ``none`` and ``auto`` give the
    caps themselves (:func:`field_caps` takes ``auto`` at the largest
    reader's lines).  A cap that another one contains is left out.
    """

    if option not in READERS:
        return [(rows_cap, columns_cap)]
    sense, drive = READERS[option]
    caps: list = []
    for rows, columns in ((sense, drive), (drive, sense)):
        cap = (min(rows_cap, rows), min(columns_cap, columns))
        if cap not in caps:
            caps.append(cap)
    return [cap for cap in caps if not any(other != cap and other[0] >= cap[0] and other[1] >= cap[1] for other in caps)]


def field_caps(option: str, rows_cap: int, columns_cap: int) -> list:
    """The ``(rows, columns)`` caps of a CAD fit's fields within ``rows_cap`` x ``columns_cap``, shaped (masked) and full
    alike (the user's decision, P5-diagonal-bus.md section 21): :func:`walk_caps` of a named reader, ``auto`` at the
    largest reader's lines (48 x 48: no reader holds more), ``none`` the caps themselves."""

    if option == "auto":
        option = max(READERS, key=lambda name: (READERS[name][0] * READERS[name][1], name))
    return walk_caps(option, rows_cap, columns_cap)


def sense_board(name: str, row_pins: int) -> str:
    """Which board's lines the reader senses: ``row`` or ``column``."""

    sense, _ = READERS[name]
    return "row" if row_pins == sense else "column"


def lines(name: str, row_pin: Any, column_pin: Any, row_pins: int) -> Any:
    """The reader's lines of a taxel: sense line, drive line, their connectors and the frame index."""

    if row_pin is None or column_pin is None:
        return None
    sense, drive = READERS[name]
    sense_index, drive_index = (row_pin, column_pin) if sense_board(name, row_pins) == "row" else (column_pin, row_pin)
    return {
        "sense_line": f"SR{sense_index}",
        "drive_line": f"SC{drive_index}",
        "sense_connector": f"FPC1 ({sense}-pin)",
        "drive_connector": f"FPC2 ({drive}-pin)",
        "frame_index": (drive_index - 1) * sense + (sense_index - 1),
    }


def summary(name: Any, row_pins: Any) -> Any:
    """The taxel map's ``reader`` record (None without a reader)."""

    if name is None:
        return None
    sense, drive = READERS[name]
    return {
        "name": name,
        "sense_lines": sense,
        "drive_lines": drive,
        "sense_connector": f"FPC1 ({sense}-pin)",
        "drive_connector": f"FPC2 ({drive}-pin)",
        "sense_board": sense_board(name, row_pins),
        "frame_values": sense * drive,
        "frame_index": f"(SC - 1) x {sense} + (SR - 1)",
    }


def normalize(raw: Mapping[str, Any]) -> dict:
    """Fit options with the legacy ``connector`` folded into ``reader`` and reader aliases resolved.

    ``connector: channels`` is ``reader: none`` and ``connector: flexitac``
    ``reader: 32x16`` (placements saved before the reader option keep
    mapping); a request may not give both with different meanings.
    """

    options = dict(raw)
    reader = options.get("reader")
    if isinstance(reader, str) and reader in READER_ALIASES:
        options["reader"] = reader = READER_ALIASES[reader]
    if "connector" in options:
        from .errors import SurfaceError

        legacy = options.pop("connector")
        if not isinstance(legacy, str) or legacy not in LEGACY_CONNECTOR:
            raise SurfaceError("E_SURFACE_REQUEST", "options.connector must be one of channels, flexitac (or use options.reader).")
        if "reader" in options and reader != LEGACY_CONNECTOR[legacy]:
            raise SurfaceError("E_SURFACE_REQUEST", f"options.connector {legacy} and options.reader {reader} disagree: give options.reader only.")
        options["reader"] = LEGACY_CONNECTOR[legacy]
    return options
