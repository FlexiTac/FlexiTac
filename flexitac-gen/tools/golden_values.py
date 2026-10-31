#!/usr/bin/env python3
"""Print the current golden values of the default build for tests/test_golden_default.py.

Run it after a deliberate change of the geometry, the profile or a version,
compare its output with the constants in the test (review every difference
first: the golden values exist to make changes visible), then paste the
new values and update the build id quoted in README.md, docs/ and
claude/APP_HANDOFF.md.

    python3 -B tools/golden_values.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

# Importing the engine must not leave bytecode in the project.
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine import default_design, generate_design  # noqa: E402
from exporters import artifact_filenames, build_exports  # noqa: E402

MEASURED = (
    "route_route_clearance", "pad_trace_clearance", "pad_pad_clearance", "electrode_electrode_clearance",
    "electrode_route_clearance", "copper_to_outline", "route_to_outline", "copper_to_cutout", "active_field_margin",
    "contact_exposure", "neck_width", "stiffener_end_clearance", "concave_fillet_radius", "route_width", "tail_width",
    "board_short_side", "board_long_side",
)


def main() -> int:
    result = generate_design(default_design())
    if not result["ok"]:
        print(json.dumps(result["validation"]["errors"], indent=1))
        return 1
    manifest = result["manifest"]
    exports = build_exports(result)
    names = artifact_filenames(result)
    layout = {"format": manifest["layout_format"], "units": "mm", "boards": result["boards"]}
    canonical = json.dumps(layout, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)
    report = {
        "identity": {key: manifest[key] for key in ("build_id", "build_sha256", "design_sha256", "profile_sha256", "generator", "exporter")},
        "layout_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "artifacts": {key: (names[key], len(data), hashlib.sha256(data).hexdigest()) for key, data in exports.items()},
        "boards": {},
    }
    for key, board in result["boards"].items():
        pin_1 = next(pad for pad in board["layers"]["top_copper"]["pads"] if pad["pin"] == 1)
        stiffener = board["layers"]["bottom_stiffener"][0]["points"]
        routes = board["layers"]["top_copper"]["routes"]
        report["boards"][key] = {
            "id": board["id"],
            # Count and width of the tail and fan-out pieces (two per net).
            "route_pieces": {
                segment: (sum(1 for route in routes if route["segment"] == segment), sorted({route["width_mm"] for route in routes if route["segment"] == segment}))
                for segment in ("tail", "fanout")
            },
            "outline_mm": (board["metrics"]["outline_width_mm"], board["metrics"]["outline_height_mm"]),
            "outline_vertices": len(board["outline"]["points"]),
            "tail": {name: board["tail"][name] for name in ("length_mm", "width_mm", "connector_pins", "bounds")},
            "pin_1": {name: pin_1[name] for name in ("net", "x", "y", "width_mm", "height_mm")},
            "active_region": board["grid_registration"]["active_region"],
            "electrode_field": board["grid_registration"]["electrode_field"],
            "stiffener_bbox": (min(p[0] for p in stiffener), min(p[1] for p in stiffener), max(p[0] for p in stiffener), max(p[1] for p in stiffener)),
            "openings": [(o["kind"], o["x"], o["y"], o["width_mm"], o["height_mm"]) for o in board["layers"]["top_coverlay_openings"]],
            "construction": board["construction"],
            "measured": {name: board["verification"]["checks"][name]["measured_mm"] for name in MEASURED},
        }
    print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
