"""Golden values of the default build (audit H4: no golden values; M6 identity).

The default 12 x 32 design is the reviewed reference build: since
claude/specs/masked-field/P5-diagonal-bus.md section 18 the diagonal Row bus
with both sides (the generic template's default; ``diagonal-bus/8`` since
section 20: CAD mode's rule set and construction, so its profile is the
surface one; ``diagonal-bus/9`` since section 24, ``diagonal-bus/10`` since
section 27, ``diagonal-bus/11`` since section 27.8).  Its straight Row channel
(``routing.row_sides`` ``channel``, with the generic profile's 7.0 mm bottom tail) keeps the golden
geometry pinned before then (``CHANNEL_LAYOUT_SHA256``, ``CHANNEL_BOARDS``).  These constants
pin its identity, its geometry in numbers a reviewer can read, its DRC
measurements and the exact bytes of the three archives, which are the same
on Python 3.9 to 3.13 and under any hash seed.  A deliberate change of the
geometry, the profile, the generator or the exporter changes them: review
the difference, bump the version that owns it (the profile ``revision`` for
a profile change; the generator version for a change of the order-requirement
wording of ``engine.profile.order_requirements``, which reaches the archives
but not the build identity), then refresh the constants with
``python3 -B tools/golden_values.py`` and update the build id quoted in
README.md, docs/ and claude/APP_HANDOFF.md (tests/test_docs_consistency.py
checks those).
"""

from __future__ import annotations

import hashlib
import io
import json
import unittest
import zipfile

from engine import check_design, default_design, generate_design
from exporters import artifact_filenames, build_exports

# Re-pinned for the profile revision 2026-10-29 (the gold-finger thickness order option and the coverlay-window notes):
# the identity, the profile revision and the archives; the layout and every measurement held.
# Rewritten by the user's request of 2026-11-06 ("ordering node,改成2 layer, 0.2mm"): the profile revision 2026-11-06 orders
# each board as JLC's 2-layer 0.2 mm FPC, the bottom copper empty (order.fpc_layers 2, order.fpc_thickness_mm 0.2, the
# FlexiTac fabrication guide cited): the identity, the profile revision and the archives (ORDER_NOTES.txt); the
# layout and every measurement held.
BUILD_ID = "tactile-fpc-12x32-48b9d43409a6"
IDENTITY = {
    "build_id": BUILD_ID,
    "build_sha256": "48b9d43409a6147adafaf81fee8ba6ef2c7eae85cc726f79c06e32a5c013693f",
    "design_sha256": "1e0001a8705c5453ecb598d34939d9f3123511a34f0b71597c6fc4bed6655a72",
    "profile_sha256": "fb37953c0b7ad8f820ac71fcf4f5e07df946d3ec2943ecd3e1f43be30a2f2448",
    "generator": "deterministic-sensor-core/0.4.0",
    "exporter": "direct-gerber-pure-stdlib/0.3.0",
    "row_bus": "diagonal-bus/11",
    "layout_format": "tactile-fpc-layout/v3",
    "format": "tactile-fpc-manifest/v2",
    "slug": "tactile-fpc-12x32",
    "profile": {"id": "jlc-fpc-surface-v1", "revision": "2026-11-06"},
    "output_status": "geometry_only",
    "geometry_valid": True,
    "production_ready": False,
}
# sha256 of the canonical JSON of {"format", "units", "boards"} (= derived-layout.json without its newline).
LAYOUT_SHA256 = "6e20c9f42212fba7dc318aa97a5d0b2ed6e41f9160bfc098b29b36d780978460"
ARTIFACTS = {
    "top_fpc_gerber_zip": (f"{BUILD_ID}-top-rows-direct-gerber.zip", 30610, "774773c1e7526efc05fd6d70e3b5e74a45878f148c4252736c32d40a81834b36"),
    "bottom_fpc_gerber_zip": (f"{BUILD_ID}-bottom-columns-direct-gerber.zip", 42716, "6871de5732d55c201a77988d6395940c6fac5775ab27e3827a4a85b9520cb4a7"),
    "project_review_bundle_zip": (f"{BUILD_ID}-project-review.zip", 237849, "8c32011b5def58c54fb2a5bb03d86ad2a3ba048bb7b96fc3c18a1789fa708936"),
}
# Since 2026-10-24 (P5-diagonal-bus.md section 18) the default design is the diagonal Row bus with both sides: the Row
# traces leave both ends of their rows (ROW_01, 03, ... on the stack's right), fan into a Row tail centred under the
# field (the folded pins ROW_01, 03, ..., 04, 02), and both boards share one outline.  Since diagonal-bus/8 (section 20)
# the bus is built with CAD mode's rule set (the surface profile: the 0.5 mm field margin, the 7.5 mm default bottom
# tail) and construction: the Column board converges in one V (one lane straight into its contacts, at most 80 degrees:
# 79.999 here, no slot), so the Row fans keep 85 degrees off it, and both boards share one outline down to their tail
# roots, 5.87 mm below the field (the Column V's root lowered below the fillets into the tails): both 67.9 mm wide, the
# Row board 41.8 mm long, the Column board 37.3 (diagonal-bus/7: 41.1 and 53.0 with two Column lanes round a slot).
# Rewritten by section 24 (diagonal-bus/9, convex sides): the construction's version in the identity, the layout and the
# archives (the build id, its hashes, the layout digest, the archives' digests); the boards' geometry, their outlines and
# the archives' sizes are the same (the default's sides have no dent to bridge).  Rewritten by section 27
# (diagonal-bus/10, the user's request "some tails are not within the sensor's width": the Row tail centred on the field
# in every side mode): the Row tail 0.048486 mm east, on the field's centre line (the funnel's split midway between the
# innermost lanes lay that far west of it), its contacts and stiffener with it, the two fans' heights 3.848 -> 3.853 /
# 3.844 mm; the outlines, the widths and the shared level the same; the version in the identity, the layout and the
# archives (the build id, its hashes, the layout digest, the archives' digests and sizes).
# Rewritten by the user's decision of 2026-10-27 (section 27.7: "矩形模式默认 tail 长度是否改成 12/12 ：可以；可以加个门槛", the rectangular
# mode's default tails 12 / 12 mm): the Column tail 7.5 -> 12 mm, so the stacked tails end together (4.5 mm apart
# before); the Column board 4.5 mm longer (37.265841 -> 41.765841 mm, the Row board's length), its field, openings and
# stiffener end clearance (1.5 -> 6.0 mm) with it; the Row board unchanged; the design and with it the build id, its
# hashes, the layout digest and the archives' digests (the bottom board's and the review bundle's sizes).  Rewritten by
# section 27.8 (diagonal-bus/11, one side's convex flank, the multi-gripper video's notch): the construction's version
# in the identity, the layout and the archives (the build id, its hashes, the layout digest, the archives' digests); the
# default has both sides, whose flanks have lanes, so its boards, their outlines and the archives' sizes are the same.
# Rewritten by the user's decision of 2026-11-06 ("默认的pitch/trace大小,现在都是0.7,直接都改成0.5": the default fill, electrode
# width / pitch, 0.7 -> 0.5): the electrodes 1.4 -> 1.0 mm at the 2 mm pitch, so the active region 63.4 x 23.4 -> 63.0 x
# 23.0 mm and both outlines 0.4 mm narrower and shorter (67.919595 x 41.765841 -> 67.520543 x 41.365841 mm), the tails
# with the field's centre; the coverlay bridges between the electrode windows 0.4 -> 0.8 mm, at least the profile's 0.5,
# so each electrode has its own window (12 Row and 32 Column windows of 1.2 mm, one merged field window each before),
# the electrode clearance 0.6 -> 1.0 mm; the design and with it the build id, its hashes, the layout digest and the
# archives' digests and sizes.
BOARDS = {
    "row": {
        "id": 'top_rows_fpc',
        "physical_side": 'top',
        "route_pieces": {'tail': (12, [0.254]), 'fanout': (12, [0.127])},
        "outline_mm": (67.520543, 41.365841),
        "outline_vertices": 80,
        "tail": {"length_mm": 12.0, "width_mm": 6.5, "connector_pins": 12, "bounds": {"x": 30.558639, "y": 0.0, "width": 6.5, "height": 12.0}},
        "pin_1": {"net": "ROW_01", "x": 31.058639, "y": 2.3, "width_mm": 0.3, "height_mm": 4.0},
        "active_region": {"x": 2.308639, "y": 17.865841, "width": 63.0, "height": 23.0},
        "electrode_field": {"x": 2.108639, "y": 17.865841, "width": 63.4, "height": 23.0},
        "stiffener_bbox": (30.558639, 0.0, 37.058639, 6.0),
        "openings": [('sensor_electrode_opening', 2.008639, 17.765841, 63.6, 1.2), ('sensor_electrode_opening', 2.008639, 19.765841, 63.6, 1.2), ('sensor_electrode_opening', 2.008639, 21.765841, 63.6, 1.2), ('sensor_electrode_opening', 2.008639, 23.765841, 63.6, 1.2), ('sensor_electrode_opening', 2.008639, 25.765841, 63.6, 1.2), ('sensor_electrode_opening', 2.008639, 27.765841, 63.6, 1.2), ('sensor_electrode_opening', 2.008639, 29.765841, 63.6, 1.2), ('sensor_electrode_opening', 2.008639, 31.765841, 63.6, 1.2), ('sensor_electrode_opening', 2.008639, 33.765841, 63.6, 1.2), ('sensor_electrode_opening', 2.008639, 35.765841, 63.6, 1.2), ('sensor_electrode_opening', 2.008639, 37.765841, 63.6, 1.2), ('sensor_electrode_opening', 2.008639, 39.765841, 63.6, 1.2), ('connector_contact_opening', 30.858639, 0.0, 5.9, 4.4)],
        "construction": {"minimum_concave_fillet_radius_mm": 0.5, "fanout_bundle_pitch_mm": 0.254, "row_bus": {"kind": "diagonal-bus/11", "sides": "both", "near_side": "right", "split": "alternate", "near_rows": [1, 3, 5, 7, 9, 11], "far_rows": [2, 4, 6, 8, 10, 12], "contact_order": ["ROW_01", "ROW_03", "ROW_05", "ROW_07", "ROW_09", "ROW_11", "ROW_12", "ROW_10", "ROW_08", "ROW_06", "ROW_04", "ROW_02"], "tail_position": "centred", "tails": "stacked", "shared_outline_below_field_mm": 5.865841, "fans": [{"rows": [11, 9, 7, 5, 3, 1], "move": "east", "angle_deg": 85.0, "height_mm": 3.835097}, {"rows": [12, 10, 8, 6, 4, 2], "move": "west", "angle_deg": 85.0, "height_mm": 3.824528}], "tip_width_mm": 64.526246, "tip_excess_mm": 0.526246, "band_mm": {"near": 1.729476, "far": 1.601966}, "lane_angle_deg": {"near": [3.647927, 21.075296], "far": [3.647927, 21.075366]}, "flat_lane_rows": [], "widest_mm": 67.520543, "tip_is_narrowest_relative": True}, "mask_class": {"row": "diagonal", "column": "straight"}},
        "measured": {"route_route_clearance": 0.127, "pad_trace_clearance": 0.223, "pad_pad_clearance": 0.2, "electrode_electrode_clearance": 1.0, "electrode_route_clearance": 0.250001, "copper_to_outline": 0.3, "route_to_outline": 0.300999, "copper_to_cutout": None, "active_field_margin": 0.5, "contact_exposure": 0.05, "neck_width": 6.5, "stiffener_end_clearance": 5.5, "concave_fillet_radius": 0.517862, "route_width": 0.0, "tail_width": 0.0, "board_short_side": 41.365841, "board_long_side": 67.520543},
    },
    "column": {
        "id": 'bottom_columns_fpc',
        "physical_side": 'bottom',
        "route_pieces": {'tail': (32, [0.254]), 'fanout': (32, [0.127])},
        "outline_mm": (67.520543, 41.365841),
        "outline_vertices": 60,
        "tail": {"length_mm": 12.0, "width_mm": 16.5, "connector_pins": 32, "bounds": {"x": 25.461904, "y": 0.0, "width": 16.5, "height": 12.0}},
        "pin_1": {"net": "COL_01", "x": 25.961904, "y": 2.3, "width_mm": 0.3, "height_mm": 4.0},
        "active_region": {"x": 2.211904, "y": 17.865841, "width": 63.0, "height": 23.0},
        "electrode_field": {"x": 2.211904, "y": 17.665841, "width": 63.0, "height": 23.4},
        "stiffener_bbox": (25.461904, 0.0, 41.961904, 6.0),
        "openings": [('sensor_electrode_opening', 2.111904, 17.565841, 1.2, 23.6), ('sensor_electrode_opening', 4.111904, 17.565841, 1.2, 23.6), ('sensor_electrode_opening', 6.111904, 17.565841, 1.2, 23.6), ('sensor_electrode_opening', 8.111904, 17.565841, 1.2, 23.6), ('sensor_electrode_opening', 10.111904, 17.565841, 1.2, 23.6), ('sensor_electrode_opening', 12.111904, 17.565841, 1.2, 23.6), ('sensor_electrode_opening', 14.111904, 17.565841, 1.2, 23.6), ('sensor_electrode_opening', 16.111904, 17.565841, 1.2, 23.6), ('sensor_electrode_opening', 18.111904, 17.565841, 1.2, 23.6), ('sensor_electrode_opening', 20.111904, 17.565841, 1.2, 23.6), ('sensor_electrode_opening', 22.111904, 17.565841, 1.2, 23.6), ('sensor_electrode_opening', 24.111904, 17.565841, 1.2, 23.6), ('sensor_electrode_opening', 26.111904, 17.565841, 1.2, 23.6), ('sensor_electrode_opening', 28.111904, 17.565841, 1.2, 23.6), ('sensor_electrode_opening', 30.111904, 17.565841, 1.2, 23.6), ('sensor_electrode_opening', 32.111904, 17.565841, 1.2, 23.6), ('sensor_electrode_opening', 34.111904, 17.565841, 1.2, 23.6), ('sensor_electrode_opening', 36.111904, 17.565841, 1.2, 23.6), ('sensor_electrode_opening', 38.111904, 17.565841, 1.2, 23.6), ('sensor_electrode_opening', 40.111904, 17.565841, 1.2, 23.6), ('sensor_electrode_opening', 42.111904, 17.565841, 1.2, 23.6), ('sensor_electrode_opening', 44.111904, 17.565841, 1.2, 23.6), ('sensor_electrode_opening', 46.111904, 17.565841, 1.2, 23.6), ('sensor_electrode_opening', 48.111904, 17.565841, 1.2, 23.6), ('sensor_electrode_opening', 50.111904, 17.565841, 1.2, 23.6), ('sensor_electrode_opening', 52.111904, 17.565841, 1.2, 23.6), ('sensor_electrode_opening', 54.111904, 17.565841, 1.2, 23.6), ('sensor_electrode_opening', 56.111904, 17.565841, 1.2, 23.6), ('sensor_electrode_opening', 58.111904, 17.565841, 1.2, 23.6), ('sensor_electrode_opening', 60.111904, 17.565841, 1.2, 23.6), ('sensor_electrode_opening', 62.111904, 17.565841, 1.2, 23.6), ('sensor_electrode_opening', 64.111904, 17.565841, 1.2, 23.6), ('connector_contact_opening', 25.761904, 0.0, 15.9, 4.4)],
        "construction": {"minimum_concave_fillet_radius_mm": 0.5, "fanout_bundle_pitch_mm": 0.254, "bend_stagger_mm": 0.213131, "entry_taper_angle_deg": 79.999381, "entry_transition_height_mm": 4.099862, "merger_taper_angle_deg": 0.0, "merger_height_mm": 0.0, "slot_bounds": None, "mask_class": {"row": "diagonal", "column": "straight"}, "shared_outline_below_field_mm": 5.865841},
        "measured": {"route_route_clearance": 0.169721, "pad_trace_clearance": 0.223, "pad_pad_clearance": 0.2, "electrode_electrode_clearance": 1.0, "electrode_route_clearance": 0.984833, "copper_to_outline": 0.3, "route_to_outline": 0.364499, "copper_to_cutout": None, "active_field_margin": 0.5, "contact_exposure": 0.05, "neck_width": 16.5, "stiffener_end_clearance": 6.0, "concave_fillet_radius": 0.532658, "route_width": 0.0, "tail_width": 0.0, "board_short_side": 41.365841, "board_long_side": 67.520543},
    },
}

# The straight Row channel (routing.row_sides "channel") of the default design keeps the golden geometry of before
# section 18 byte for byte: its layout digest and boards are the ones pinned here until then (build
# tactile-fpc-12x32-f978429d47e3, whose id changed with the design's routing.row_sides; its archives' members but the
# identity carriers are pinned in tests/fixtures/generic_channel_exports.json).
CHANNEL_LAYOUT_SHA256 = "b445ed4509f0261fc9042c93ce9d6ce1ffe81e9c345ac3fefd56395682a2993c"
# Since 2026-10-15 every net is a 0.254 mm tail piece and a 0.127 mm fan-out
# piece; the bundle runs at 0.254 mm pitch (0.127 mm gaps) on both boards, so
# the Row board is 11 x 0.246 mm narrower (its channel) and 1.823842 mm taller
# (the expansion below the field), and the Column fan-out 14.1 mm shorter.
CHANNEL_BOARDS = {
    "row": {
        "id": "top_rows_fpc",
        "physical_side": "top",
        "route_pieces": {"tail": (12, [0.254]), "fanout": (12, [0.127])},
        "outline_mm": (68.694, 38.723842),
        "outline_vertices": 31,
        "tail": {"length_mm": 12.0, "width_mm": 6.5, "connector_pins": 12, "bounds": {"x": 0.0, "y": 0.0, "width": 6.5, "height": 12.0}},
        "pin_1": {"net": "ROW_01", "x": 0.5, "y": 2.3, "width_mm": 0.3, "height_mm": 4.0},
        "active_region": {"x": 4.544, "y": 14.573842, "width": 63.4, "height": 23.4},
        "electrode_field": {"x": 4.344, "y": 14.573842, "width": 63.8, "height": 23.4},
        "stiffener_bbox": (0.0, 0.0, 6.5, 6.0),
        "openings": [("electrode_field_opening", 4.244, 14.473842, 64.0, 23.6), ("connector_contact_opening", 0.3, 0.0, 5.9, 4.4)],
        "construction": {
            "minimum_concave_fillet_radius_mm": 0.5, "fanout_bundle_pitch_mm": 0.254, "bend_stagger_mm": 0.146646,
            "channel_width_mm": 3.794, "merger_taper_angle_deg": 59.998891, "merger_height_mm": 1.608495,
        },
        "measured": {
            "route_route_clearance": 0.127, "pad_trace_clearance": 0.223, "pad_pad_clearance": 0.2,
            "electrode_electrode_clearance": 0.6, "electrode_route_clearance": 1.2365, "copper_to_outline": 0.3,
            "route_to_outline": 0.373, "copper_to_cutout": None, "active_field_margin": 0.75, "contact_exposure": 0.05,
            "neck_width": 6.5, "stiffener_end_clearance": 5.5, "concave_fillet_radius": 0.52874, "route_width": 0.0, "tail_width": 0.0,
            "board_short_side": 38.723842, "board_long_side": 68.694,
        },
    },
    "column": {
        "id": "bottom_columns_fpc",
        "physical_side": "bottom",
        "route_pieces": {"tail": (32, [0.254]), "fanout": (32, [0.127])},
        "outline_mm": (64.9, 52.989032),
        "outline_vertices": 94,
        "tail": {"length_mm": 7.0, "width_mm": 16.5, "connector_pins": 32, "bounds": {"x": 24.2, "y": 0.0, "width": 16.5, "height": 7.0}},
        "pin_1": {"net": "COL_01", "x": 24.7, "y": 2.3, "width_mm": 0.3, "height_mm": 4.0},
        "active_region": {"x": 0.75, "y": 28.839032, "width": 63.4, "height": 23.4},
        "electrode_field": {"x": 0.75, "y": 28.639032, "width": 63.4, "height": 23.8},
        "stiffener_bbox": (24.2, 0.0, 40.7, 6.0),
        "openings": [("electrode_field_opening", 0.65, 28.539032, 63.6, 24.0), ("connector_contact_opening", 24.5, 0.0, 15.9, 4.4)],
        "construction": {
            "minimum_concave_fillet_radius_mm": 0.5, "fanout_bundle_pitch_mm": 0.254, "bend_stagger_mm": 0.146646,
            "entry_taper_angle_deg": 59.998891, "entry_transition_height_mm": 11.801568, "merger_taper_angle_deg": 59.998891,
            "merger_height_mm": 3.822117, "slot_bounds": {"x": 26.45, "y": 11.412464, "width": 12.0, "height": 4.0},
        },
        "measured": {
            "route_route_clearance": 0.127, "pad_trace_clearance": 0.223, "pad_pad_clearance": 0.2,
            "electrode_electrode_clearance": 0.6, "electrode_route_clearance": 1.2365, "copper_to_outline": 0.3,
            "route_to_outline": 0.3645, "copper_to_cutout": 0.6865, "active_field_margin": 0.75, "contact_exposure": 0.05,
            "neck_width": 16.5, "stiffener_end_clearance": 0.721149, "concave_fillet_radius": 0.52874, "route_width": 0.0, "tail_width": 0.0,
            "board_short_side": 52.989032, "board_long_side": 64.9,
        },
    },
}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)


class GoldenDefaultBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = generate_design(default_design())
        cls.exports = build_exports(cls.result)

    def test_identity(self) -> None:
        self.assertTrue(self.result["ok"], self.result["validation"]["errors"])
        manifest = self.result["manifest"]
        self.assertEqual({key: manifest[key] for key in IDENTITY}, IDENTITY)
        self.assertEqual(manifest["checks"]["error_count"], 0)
        self.assertEqual(manifest["checks"]["warning_count"], 0)
        self.assertEqual(self.result["validation"]["warnings"], [])
        # The request-free check and an empty request name the same build.
        self.assertEqual(check_design({})["identity"]["build_id"], BUILD_ID)
        self.assertEqual(generate_design({})["manifest"]["build_id"], BUILD_ID)

    def test_layout_digest(self) -> None:
        layout = {"format": IDENTITY["layout_format"], "units": "mm", "boards": self.result["boards"]}
        self.assertEqual(_sha256(_canonical(layout).encode("utf-8")), LAYOUT_SHA256)

    def test_board_geometry_and_drc_measurements(self) -> None:
        self._check_boards(self.result, BOARDS)

    def test_the_straight_channel_keeps_the_golden_geometry_of_before(self) -> None:
        design = default_design()
        design["routing"]["row_sides"] = "channel"
        # The straight channel's default bottom tail is the generic profile's 7.0 mm (the bus's 12 since section 27.7, 7.5
        # from section 20).
        design["tail"]["bottom_length_mm"] = 7.0
        # ... and its electrodes the 1.4 mm of before (the default fill 0.7 until the user's decision of 2026-11-06).
        design["matrix"].update(taxel_width_mm=1.4, taxel_height_mm=1.4)
        result = generate_design(design)
        self.assertTrue(result["ok"], result["validation"]["errors"])
        layout = {"format": IDENTITY["layout_format"], "units": "mm", "boards": result["boards"]}
        self.assertEqual(_sha256(_canonical(layout).encode("utf-8")), CHANNEL_LAYOUT_SHA256)
        self._check_boards(result, CHANNEL_BOARDS)
        self.assertNotIn("row_bus", result["manifest"])
        self.assertNotEqual(result["manifest"]["build_id"], BUILD_ID)

    def _check_boards(self, result, boards) -> None:
        for key, expected in boards.items():
            board = result["boards"][key]
            with self.subTest(board=key):
                self.assertEqual((board["id"], board["physical_side"]), (expected["id"], expected["physical_side"]))
                routes = board["layers"]["top_copper"]["routes"]
                pieces = {
                    segment: (sum(1 for route in routes if route["segment"] == segment), sorted({route["width_mm"] for route in routes if route["segment"] == segment}))
                    for segment in ("tail", "fanout")
                }
                self.assertEqual(pieces, expected["route_pieces"])
                self.assertEqual((board["metrics"]["outline_width_mm"], board["metrics"]["outline_height_mm"]), expected["outline_mm"])
                self.assertEqual(len(board["outline"]["points"]), expected["outline_vertices"])
                self.assertEqual({name: board["tail"][name] for name in expected["tail"]}, expected["tail"])
                pin_1 = next(pad for pad in board["layers"]["top_copper"]["pads"] if pad["pin"] == 1)
                self.assertEqual({name: pin_1[name] for name in expected["pin_1"]}, expected["pin_1"])
                registration = board["grid_registration"]
                self.assertEqual(registration["active_region"], expected["active_region"])
                self.assertEqual(registration["electrode_field"], expected["electrode_field"])
                (stiffener,) = board["layers"]["bottom_stiffener"]
                xs, ys = [point[0] for point in stiffener["points"]], [point[1] for point in stiffener["points"]]
                self.assertEqual((min(xs), min(ys), max(xs), max(ys)), expected["stiffener_bbox"])
                # 0.225 mm PI since 2026-10-14 (JLC's choice for a 0.3 mm connector on a 0.11 mm FPC).
                self.assertEqual((stiffener["side"], stiffener["material"], stiffener["thickness_mm"]), ("bottom", "polyimide", 0.225))
                self.assertEqual(stiffener["thickness_mm"], result["profile"]["stackup"]["stiffener_thickness_mm"])
                openings = [(o["kind"], o["x"], o["y"], o["width_mm"], o["height_mm"]) for o in board["layers"]["top_coverlay_openings"]]
                self.assertEqual(openings, expected["openings"])
                self.assertEqual(board["construction"], expected["construction"])
                checks = board["verification"]["checks"]
                self.assertEqual(len(checks), 30)
                self.assertTrue(all(record["passed"] for record in checks.values()))
                self.assertEqual({name: checks[name]["measured_mm"] for name in expected["measured"]}, expected["measured"])

    def test_artifact_names_sizes_and_digests(self) -> None:
        names = artifact_filenames(self.result)
        for key, (name, size, digest) in ARTIFACTS.items():
            with self.subTest(artifact=key):
                self.assertEqual(names[key], name)
                self.assertEqual(len(self.exports[key]), size)
                self.assertEqual(_sha256(self.exports[key]), digest)
        # The browser exports the canonical design of its result: the same bytes.
        again = build_exports(generate_design(self.result["design"]))
        self.assertEqual(again, self.exports)

    def test_review_bundle_records_the_golden_digests(self) -> None:
        with zipfile.ZipFile(io.BytesIO(self.exports["project_review_bundle_zip"])) as archive:
            manifest = json.loads(archive.read("manifest.json"))
            layout = archive.read("derived-layout.json")
        self.assertEqual(manifest["build_id"], BUILD_ID)
        self.assertEqual(_sha256(layout.rstrip(b"\n")), LAYOUT_SHA256)
        for key, (name, size, digest) in list(ARTIFACTS.items())[:2]:
            self.assertEqual((manifest["artifacts"][key]["filename"], manifest["artifacts"][key]["bytes"], manifest["artifacts"][key]["sha256"]), (name, size, digest))


if __name__ == "__main__":
    unittest.main()
