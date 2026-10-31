#!/usr/bin/env python3
"""Command-line access to the deterministic Tactile FPC generator (stdlib only).

  python3 cli.py schema                          JSON Schema of the design input
  python3 cli.py validate DESIGN.json ...        normalization, input rules, feasibility (no geometry)
  python3 cli.py generate DESIGN.json ... [--compact]
  python3 cli.py export DESIGN.json ... --out DIR
  python3 cli.py surface inspect|select|fit|map MESH.stl ...   CAD mode (see surface --help)

DESIGN is a JSON file (``-`` reads standard input) holding one design object,
in the same strict format as the HTTP API body: ``null``, arrays and other
non-objects are rejected, never read as "use the defaults".  The output is
one JSON document on standard output: the result itself for one input, or
``{"ok": ..., "results": [{"input": ..., ...}]}`` for several (a batch).
``export`` writes the Gerber ZIPs and the project-review ZIP of every valid
design into DIR under build-id file names.  ``--pretty`` indents the output.

``surface`` runs CAD mode on an STL: ``inspect`` (mesh facts and candidate
surfaces), ``select`` (``--pick X,Y,Z`` in mm or ``--ops FILE``), ``fit``
(proposals; with ``--out DIR`` the best one's design, placement, taxel map,
wrap template and Gerber ZIPs) and ``map`` (``--placement FILE`` from a fit;
its own selection is used when neither ``--pick`` nor ``--ops`` is given).

Exit status: 0 when every design is valid, 1 when a design does not validate
(or cannot be exported, or CAD mode rejects the mesh, selection or fit), 2 for
unreadable input or unwritable output, 3 for an unexpected error in a CAD-mode
command.  Input
and output failures are ``{"ok": false, "code": ..., "error": ...}`` with the
codes in :data:`CLI_ERROR_CODES` (also listed by ``schema`` as
``x-cli-error-codes``); design problems carry the engine's issue codes.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

from engine import BuildCache, DesignJSONError, check_design, design_schema, generate_design, load_design_json, result_view
from exporters import ExportError, artifact_filenames, build_exports

CLI_ERROR_CODES = {
    "E_CLI_INPUT": "2: the design file cannot be read.",
    "E_CLI_INVALID_JSON": "2: the file is not strict UTF-8 JSON (NaN/Infinity, duplicate keys, too deep, number too long).",
    "E_CLI_NOT_OBJECT": "2: the document is not one JSON object (null, an array, a string or a number).",
    "E_CLI_OUTPUT": "2: the export directory or an archive cannot be written.",
    "E_EXPORT_BLOCKED": "1: the design does not validate; the entry carries validation.",
    "E_EXPORT_FAILED": "1: the exporter rejected the generated geometry.",
    "E_SURFACE": "1: CAD mode rejected the mesh, the selection or the fit; the code is one of x-surface-error-codes.",
    "E_CLI_INTERNAL": "3: an unexpected error in a CAD-mode command (a bug; the message names the exception).",
}


def main(argv: list[str] | None = None) -> int:
    # --pretty is accepted before or after the command; SUPPRESS keeps a value given before it.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--pretty", action="store_true", default=argparse.SUPPRESS, help="indent the JSON output")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pretty", action="store_true", help="indent the JSON output")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("schema", parents=[common], help="print the JSON Schema (draft 2020-12) of a design")
    validate = commands.add_parser("validate", parents=[common], help="normalize and validate designs without generating geometry")
    generate = commands.add_parser("generate", parents=[common], help="generate designs (full result without the duplicated derived_layout)")
    generate.add_argument("--compact", action="store_true", help="summary only: ok, design, validation, manifest, board metrics and DRC")
    export = commands.add_parser("export", parents=[common], help="write the Gerber and review ZIPs of valid designs")
    export.add_argument("--out", required=True, type=Path, help="output directory (created if missing)")
    for command in (validate, generate, export):
        command.add_argument("inputs", nargs="+", metavar="DESIGN", help="design JSON file, or - for standard input")
    surface = commands.add_parser("surface", parents=[common], help="CAD mode: fit the sensor to a surface of an STL")
    surface.add_argument("action", choices=("inspect", "select", "fit", "map"))
    surface.add_argument("mesh", metavar="MESH", help="STL file (binary or ASCII)")
    surface.add_argument("--unit", choices=("m", "cm", "mm", "in"), help="unit of the STL coordinates (default: guessed)")
    surface.add_argument("--pick", help="X,Y,Z (mm, STL frame): grow the selection from the facet nearest this point")
    surface.add_argument("--preset", choices=("surface", "flat", "smooth"), default="surface", help="selection preset for --pick")
    surface.add_argument("--ops", type=Path, help="JSON file with the selection operations (instead of --pick)")
    surface.add_argument("--base", default="auto", help="tail exit side: auto, a side index, or X,Y,Z (mm) near the side")
    surface.add_argument("--options", type=Path, help="JSON file with fit options (pitch_mm, objective, ...)")
    surface.add_argument("--proposal", type=int, default=1, help="proposal rank written by --out (default 1)")
    surface.add_argument("--placement", type=Path, help="placement JSON of a fit proposal (for map)")
    surface.add_argument("--out", type=Path, help="fit: write the chosen proposal's files and Gerber ZIPs here")
    args = parser.parse_args(argv)

    if args.command == "schema":
        _print(dict(design_schema(), **{"x-cli-error-codes": dict(CLI_ERROR_CODES)}), args.pretty)
        return 0
    if args.command == "surface":
        status, document = _surface(args)
        try:
            text = _dumps(document, args.pretty)
        except (RecursionError, ValueError) as error:  # a reply that is not JSON: a bug, still one JSON document
            status, text = 3, _dumps(_failure("E_CLI_INTERNAL", f"unexpected {type(error).__name__}: {error}"), args.pretty)
        sys.stdout.write(text + "\n")
        return status
    if args.inputs.count("-") > 1:
        parser.error("standard input (-) can be read only once")
    cache = BuildCache()
    outcomes = []
    for name in args.inputs:
        data, problem = _read(name)
        if problem is not None:
            outcomes.append((2, problem))
        elif args.command == "validate":
            result = check_design(data)
            outcomes.append((0 if result["ok"] else 1, result))
        elif args.command == "generate":
            result = generate_design(data, cache=cache)
            outcomes.append((0 if result["ok"] else 1, result_view(result, "compact" if args.compact else "full")))
        else:
            outcomes.append(_export(data, args.out, cache))
    status = max(code for code, _ in outcomes)
    if len(outcomes) == 1:
        _print(outcomes[0][1], args.pretty)
    else:
        results = [{"input": name, **document} for name, (_, document) in zip(args.inputs, outcomes)]
        _print({"ok": status == 0, "results": results}, args.pretty)
    return status


def _read(name: str) -> tuple[Any, dict[str, Any] | None]:
    """The design object of a file (or stdin), else ``(None, error document)``."""

    label = "standard input" if name == "-" else name
    try:
        raw = sys.stdin.buffer.read() if name == "-" else Path(name).read_bytes()
    except OSError as error:
        return None, _failure("E_CLI_INPUT", f"cannot read {label}: {error.strerror or error}")
    try:
        data = load_design_json(raw)
    except DesignJSONError as error:
        return None, _failure("E_CLI_INVALID_JSON", f"{label} is not strict JSON: {error}")
    if not isinstance(data, dict):
        # The engine reads a missing design as "use the defaults"; a file never means that.
        kinds = ((type(None), "null"), (list, "an array"), (str, "a string"), (bool, "a boolean"))
        kind = next((text for kind, text in kinds if isinstance(data, kind)), "a number")
        return None, _failure("E_CLI_NOT_OBJECT", f"{label} must contain one JSON object (the design), not {kind}.", field="$")
    return data, None


def _export(data: dict[str, Any], directory: Path, cache: BuildCache) -> tuple[int, dict[str, Any]]:
    result = generate_design(data, cache=cache)
    summary: dict[str, Any] = {"ok": result["ok"], "build_id": result["manifest"]["build_id"]}
    if not result["ok"]:
        return 1, {**summary, "code": "E_EXPORT_BLOCKED", "validation": result["validation"]}
    try:
        artifacts = build_exports(result, cache=cache)
        names = artifact_filenames(result)
    except ExportError as error:
        return 1, {**summary, "ok": False, "code": "E_EXPORT_FAILED", "error": str(error)}
    files = {}
    try:
        directory.mkdir(parents=True, exist_ok=True)
        for key, filename in names.items():
            path = directory / filename
            path.write_bytes(artifacts[key])
            files[key] = str(path.resolve())
    except OSError as error:
        return 2, {**summary, **_failure("E_CLI_OUTPUT", f"cannot write to {directory}: {error.strerror or error}"), "files": files}
    return 0, {**summary, "manifest": result["manifest"], "files": files}


def _surface(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    """One CAD-mode command; returns (exit status, JSON document)."""

    from surface import fit, place
    from surface.api import inspect, load_mesh, select_surface
    from surface.errors import SurfaceError
    from surface.select import nearest_facet

    try:
        data = Path(args.mesh).read_bytes()
    except OSError as error:
        return 2, _failure("E_CLI_INPUT", f"cannot read {args.mesh}: {error.strerror or error}")
    header: dict[str, Any] = {"name": Path(args.mesh).name}
    if args.unit:
        header["unit"] = args.unit
    try:
        if args.action == "inspect":
            return 0, inspect(header, data)
        placement = None
        if args.action == "map":
            if args.placement is None:
                return 2, _failure("E_CLI_INPUT", "map needs --placement FILE (a proposal's placement).")
            placement = _json_file(args.placement)
            if not isinstance(placement, dict):
                return 2, _failure("E_CLI_NOT_OBJECT", f"{args.placement} must contain one JSON object (the placement).")
        if args.ops is not None:
            raw = _json_file(args.ops)
            ops = raw.get("ops") if isinstance(raw, dict) else raw
            header["selection"] = {"ops": ops}
        elif args.pick is not None:
            point = _point(args.pick)
            # Through the routes' mesh cache, so the route below does not parse the file again.
            mesh = load_mesh(header, data)
            header["selection"] = {"ops": [{"op": "grow", "seed_facet": nearest_facet(mesh, point), "preset": args.preset}]}
        elif placement is not None and isinstance(placement.get("selection"), dict):
            header["selection"] = placement["selection"]  # the selection the placement was fitted on
        else:
            return 2, _failure("E_CLI_INPUT", "select, fit and map need --pick X,Y,Z or --ops FILE.")
        if args.action == "select":
            return 0, select_surface(header, data)
        options = {}
        if args.options is not None:
            options = _json_file(args.options)
            if not isinstance(options, dict):
                return 2, _failure("E_CLI_NOT_OBJECT", f"{args.options} must contain one JSON object (the fit options).")
        if args.action == "map":
            header.update(placement=placement, design=placement.get("design"))
            if args.options is not None:
                header["options"] = options  # as over HTTP: given options win over the placement's own
            mapped = place.map_route(header, data)
            mapped.pop("wrap_svg", None)
            return 0 if mapped["ok"] else 1, mapped
        header.update(base=_base(args.base), options=options)
        result = fit.fit_route(header, data)
        if args.out is None:
            return 0, result
        return _surface_export(header, data, result, args.proposal, args.out)
    except SurfaceError as error:
        return 1, {"ok": False, "code": error.code, "error": error.message, **({"details": error.details} if error.details else {})}
    except _CliFailure as failure:
        return failure.status, failure.document
    except OSError as error:
        return 2, _failure("E_CLI_INPUT", str(error))
    except Exception as error:  # a bug: still one JSON document, with its own status
        return 3, _failure("E_CLI_INTERNAL", f"unexpected {type(error).__name__}: {error}")


class _CliFailure(Exception):
    def __init__(self, status: int, document: dict[str, Any]) -> None:
        super().__init__(document["error"])
        self.status = status
        self.document = document


def _json_file(path: Path) -> Any:
    """A JSON input file of a CAD-mode command (strict JSON, as for designs)."""

    try:
        raw = path.read_bytes()
    except OSError as error:
        raise _CliFailure(2, _failure("E_CLI_INPUT", f"cannot read {path}: {error.strerror or error}")) from error
    try:
        return load_design_json(raw)
    except DesignJSONError as error:
        raise _CliFailure(2, _failure("E_CLI_INVALID_JSON", f"{path} is not strict JSON: {error}")) from error


def _surface_export(header: dict[str, Any], data: bytes, result: dict[str, Any], rank: int, directory: Path) -> tuple[int, dict[str, Any]]:
    from surface import place

    proposals = result["proposals"]
    if not 1 <= rank <= len(proposals):
        return 2, _failure("E_CLI_INPUT", f"--proposal must be 1..{len(proposals)}.")
    proposal = proposals[rank - 1]
    map_header = {key: header[key] for key in ("unit", "name", "selection") if key in header}
    map_header.update(placement=proposal["placement"], design=proposal["design"], options=proposal["placement"]["options"])
    mapped = place.map_route(map_header, data)
    status, exported = _export(proposal["design"], directory, BuildCache())
    stem = proposal["build_id"]
    files = dict(exported.get("files", {}))
    try:
        directory.mkdir(parents=True, exist_ok=True)
        documents = {
            "design": (f"{stem}.design.json", json.dumps(proposal["design"], indent=2, sort_keys=True)),
            "placement": (f"{stem}.placement.json", json.dumps(proposal["placement"], indent=2, sort_keys=True)),
            "taxel_map": (f"{stem}.taxels.json", json.dumps({k: v for k, v in mapped.items() if k != "wrap_svg"}, indent=2)),
            "wrap_template": (f"{stem}.wrap.svg", mapped["wrap_svg"]),
        }
        for key, (filename, text) in documents.items():
            path = directory / filename
            path.write_text(text + "\n", encoding="utf-8")
            files[key] = str(path.resolve())
    except OSError as error:
        return 2, _failure("E_CLI_OUTPUT", f"cannot write to {directory}: {error.strerror or error}")
    ok = status == 0 and mapped["ok"]
    return (0 if ok else max(status, 1)), {
        "ok": ok,
        "build_id": stem,
        "metrics": proposal["metrics"],
        "verification": mapped["verification"],
        "files": files,
    }


def _point(text: str) -> tuple[float, float, float]:
    try:
        parts = [float(part) for part in text.split(",")]
    except ValueError:
        parts = []
    if len(parts) != 3 or not all(math.isfinite(part) for part in parts):
        # An argument error, not a ValueError: those come from bugs and are exit status 3.
        raise _CliFailure(2, _failure("E_CLI_INPUT", f"{text!r} is not X,Y,Z (three finite numbers in mm)"))
    return parts[0], parts[1], parts[2]


def _base(text: str) -> Any:
    """--base: auto, a side index (ASCII digits) or X,Y,Z near the side."""

    if text == "auto":
        return text
    if text.isascii() and text.isdigit():
        from surface.api import MAX_NUMBER_DIGITS

        # int() raises ValueError beyond 4300 digits on 3.11+ (or a lower PYTHONINTMAXSTRDIGITS):
        # an argument error on every Python, as the HTTP header guard refuses such a number.
        if len(text) <= MAX_NUMBER_DIGITS:
            try:
                return {"side": int(text)}
            except ValueError:
                pass
        raise _CliFailure(2, _failure("E_CLI_INPUT", f"--base is a side index of {len(text)} digits; give a side index, X,Y,Z or auto."))
    return {"point_xyz": list(_point(text))}


def _failure(code: str, message: str, **extra: Any) -> dict[str, Any]:
    return {"ok": False, "code": code, "error": message, **extra}


def _print(document: Any, pretty: bool) -> None:
    sys.stdout.write(_dumps(document, pretty) + "\n")


def _dumps(document: Any, pretty: bool) -> str:
    try:
        return json.dumps(document, ensure_ascii=True, allow_nan=False, indent=2 if pretty else None)
    except RecursionError:
        if not pretty:
            raise
        # Indenting runs the pure-Python encoder, which stops at the interpreter's recursion
        # limit (about a thousand levels); the compact C encoder goes deeper on 3.12.  map
        # refuses placements nested beyond place.MAX_PLACEMENT_DEPTH, so its echo never gets here.
        return json.dumps(document, ensure_ascii=True, allow_nan=False)


if __name__ == "__main__":
    raise SystemExit(main())
