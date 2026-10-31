"""Necked routing (2026-10-15): adjustable bundle traces, bus-style bends, wide tail pieces.

The traces leave the electrodes thin (``routing.trace_width_mm``), converge
into a bundle at the pitch ``trace width + trace space``, expand to the
0.5 mm contact pitch and widen to the finger width
(``routing.finger_trace_width_mm``) below every bend.  These tests measure
that on generated boards with the independent predicates of
``geometry_checks`` (exact segment distances), and check the inputs: the
defaults, the JLC-derived ranges with field errors whose bounds work, the
aliases and the agreement of the schema, the form limits and the browser form.
"""

from __future__ import annotations

import math
import re
import unittest
from pathlib import Path

from engine import check_design as _engine_check_design, default_design, design_schema, generate_design as _engine_generate_design, input_limits, load_profile
from engine.profile import fabrication_minimum

try:
    import geometry_checks as gc
except ImportError:  # run as a package
    from tests import geometry_checks as gc

try:
    from geometry_checks import straight_channel
except ImportError:  # run as a package
    from tests.geometry_checks import straight_channel


def generate_design(design=None, *args, **kwargs):
    """``engine.generate_design`` on the straight Row channel, which these tests measure (the generic template's default is
    the diagonal Row bus since claude/specs/masked-field/P5-diagonal-bus.md section 18; geometry_checks.straight_channel)."""

    return _engine_generate_design(straight_channel(design), *args, **kwargs)


def check_design(design=None, *args, **kwargs):
    """``engine.check_design`` on the straight Row channel, which these tests measure (the generic template's default is
    the diagonal Row bus since claude/specs/masked-field/P5-diagonal-bus.md section 18; geometry_checks.straight_channel)."""

    return _engine_check_design(straight_channel(design), *args, **kwargs)

ROOT = Path(__file__).resolve().parents[1]
EPS = 1e-6
TURNS = {"bottom": 0, "right": 1, "top": 2, "left": 3}
# Designs that exercise both lane modes, odd and even counts, the narrowest
# and widest bundle, a spread two-lane fan-out, many rows, NC contacts,
# intermediate bundle widths and a bundle pitch just below the contact pitch
# (its expansion diagonals are only 1e-4 mm wide).
DESIGNS = (
    {},
    {"matrix": {"rows": 16, "columns": 17, "pitch_x_mm": 0.6, "pitch_y_mm": 0.6, "taxel_width_mm": 0.35, "taxel_height_mm": 0.35}},
    {"matrix": {"rows": 16, "columns": 17, "pitch_x_mm": 0.6, "pitch_y_mm": 0.6, "taxel_width_mm": 0.35, "taxel_height_mm": 0.35},
     "routing": {"trace_width_mm": 0.254, "trace_space_mm": 0.246}},
    {"matrix": {"rows": 64, "columns": 15, "pitch_x_mm": 0.7, "pitch_y_mm": 0.6, "taxel_width_mm": 0.3, "taxel_height_mm": 0.1016},
     "routing": {"trace_width_mm": 0.1016, "trace_space_mm": 0.1016}},
    {"matrix": {"rows": 5, "columns": 9, "pitch_x_mm": 3.3, "pitch_y_mm": 1.7}, "connector": {"row_pins": 9, "column_pins": 20},
     "routing": {"trace_width_mm": 0.1801234, "trace_space_mm": 0.2140009}, "connector_side": "left"},
    {"matrix": {"rows": 2, "columns": 32, "pitch_x_mm": 0.6, "taxel_width_mm": 0.35}, "routing": {"trace_width_mm": 0.2, "trace_space_mm": 0.15},
     "tail": {"row_side": "top", "column_side": "bottom"}, "role_mapping": {"top": "columns", "bottom": "rows"}},
    {"matrix": {"rows": 3, "columns": 3}, "routing": {"trace_width_mm": 0.254, "trace_space_mm": 0.2459}},
)


def _canonical(board):
    """The board's points turned back into the build frame (tail down)."""

    turns = (4 - TURNS[board["tail"]["side"]]) % 4

    def turn(point):
        x, y = float(point[0]), float(point[1])
        for _ in range(turns):
            x, y = -y, x
        return (x, y)

    return turn


def _pieces(board):
    """``{net: {segment: (width, points in the build frame)}}`` and the nets in contact order."""

    turn = _canonical(board)
    copper = board["layers"]["top_copper"]
    pieces = {}
    for route in copper["routes"]:
        pieces.setdefault(route["net"], {})[route["segment"]] = (route["width_mm"], [turn(point) for point in route["points"]])
    position = {pad["net"]: pad["position"] for pad in copper["pads"]}
    return pieces, sorted(pieces, key=position.get)


def _parallel_neighbour_distances(first, second):
    """Distances between parallel, overlapping segments of two fan-out pieces: (straight, diagonal) lists."""

    straight, diagonal = [], []
    for a0, a1 in zip(first, first[1:]):
        for b0, b1 in zip(second, second[1:]):
            da, db = (a1[0] - a0[0], a1[1] - a0[1]), (b1[0] - b0[0], b1[1] - b0[1])
            la, lb = math.hypot(*da), math.hypot(*db)
            if la < 1e-9 or lb < 1e-9:
                continue
            ua, ub = (da[0] / la, da[1] / la), (db[0] / lb, db[1] / lb)
            if abs(ua[0] * ub[1] - ua[1] * ub[0]) > 1e-4 or ua[0] * ub[0] + ua[1] * ub[1] < 0:
                continue
            projected_a = sorted((a0[0] * ua[0] + a0[1] * ua[1], a1[0] * ua[0] + a1[1] * ua[1]))
            projected_b = sorted((b0[0] * ua[0] + b0[1] * ua[1], b1[0] * ua[0] + b1[1] * ua[1]))
            if min(projected_a[1], projected_b[1]) - max(projected_a[0], projected_b[0]) <= 1e-6:
                continue
            distance = gc.segment_distance(a0, a1, b0, b1)
            (straight if abs(ua[0]) < 1e-12 or abs(ua[1]) < 1e-12 else diagonal).append(distance)
    return straight, diagonal


def _vertical_x(points, y):
    """x of a polyline where a vertical segment spans height ``y`` (None elsewhere)."""

    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if min(y0, y1) < y < max(y0, y1):
            return x0 if abs(x1 - x0) < 1e-9 else None
    return None


def _close_pairs(segments, reach):
    """Index pairs of ``segments`` ((net, piece, radius, a, b), ...) whose x ranges come within ``reach``."""

    order = sorted(range(len(segments)), key=lambda index: min(segments[index][3][0], segments[index][4][0]))
    active = []
    for index in order:
        low = min(segments[index][3][0], segments[index][4][0])
        active = [other for other in active if max(segments[other][3][0], segments[other][4][0]) + reach >= low]
        for other in active:
            yield other, index
        active.append(index)


def _bundle_cross_sections(pieces, nets):
    """Heights where every fan-out piece runs straight up in its bundle, with the
    spacings of neighbours there: the lanes and decks closer than the contact
    pitch (a two-lane slot gap and the stubs at the electrode pitch excluded)."""

    levels = sorted({round(y, 6) for net in nets for _, y in pieces[net]["fanout"][1]})
    answer = []
    for low, high in zip(levels, levels[1:]):
        y = (low + high) / 2
        xs = [_vertical_x(pieces[net]["fanout"][1], y) for net in nets]
        if None in xs:
            continue
        gaps = [b - a for a, b in zip(xs, xs[1:])]
        close = [gap for gap in gaps if gap < 0.5 - EPS]
        if close and len(close) >= len(gaps) - 1:  # one slot gap at most
            answer.append((y, close))
    return answer


class BundleGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_profile()
        cls.results = [generate_design(design) for design in DESIGNS]

    def test_every_design_generates_with_every_record_passing(self) -> None:
        for design, result in zip(DESIGNS, self.results):
            with self.subTest(design=design):
                self.assertTrue(result["ok"], result["validation"]["errors"])
                for board in result["boards"].values():
                    self.assertEqual(len(board["verification"]["checks"]), 30)
                    self.assertTrue(board["verification"]["all_checks_passed"], board["id"])

    def test_two_route_pieces_per_net_with_their_widths(self) -> None:
        finger = self.profile["routing"]["finger_trace_width_mm"]
        for design, result in zip(DESIGNS, self.results):
            width = result["design"]["routing"]["trace_width_mm"]
            for board in result["boards"].values():
                pieces, nets = _pieces(board)
                with self.subTest(design=design, board=board["id"]):
                    self.assertEqual(len(nets), board["tail"]["connector_channels"])
                    for net in nets:
                        self.assertEqual(set(pieces[net]), {"tail", "fanout"}, net)
                        (tail_width, tail), (fanout_width, fanout) = pieces[net]["tail"], pieces[net]["fanout"]
                        self.assertEqual((tail_width, fanout_width), (finger, width), net)
                        self.assertEqual(tail[-1], fanout[0], net)  # the shared junction
                    kinds = [route["segment"] for route in board["layers"]["top_copper"]["routes"]]
                    self.assertEqual(kinds, ["tail", "fanout"] * len(nets))  # per net: from the contact end

    def test_straight_bundle_sections_are_exactly_one_bundle_pitch_apart(self) -> None:
        # T-D3/T-D4 and acceptance 3: where the routes run straight in their bundle
        # (the Row lanes, the Column decks) neighbours are exactly q = width +
        # space apart; no straight neighbours come closer than q (a route still on
        # its stub may run beside a bundle where two runs meet), and parallel
        # diagonals keep q, plus at most a few grid steps, between them.
        pitch = self.profile["connector"]["pad_pitch_mm"]
        for design, result in zip(DESIGNS, self.results):
            routing = result["design"]["routing"]
            q = round(routing["trace_width_mm"] + routing["trace_space_mm"], 6)
            for board in result["boards"].values():
                pieces, nets = _pieces(board)
                straight, diagonal = [], []
                for first, second in zip(nets, nets[1:]):
                    found = _parallel_neighbour_distances(pieces[first]["fanout"][1], pieces[second]["fanout"][1])
                    straight += found[0]
                    diagonal += found[1]
                with self.subTest(design=design, board=board["id"]):
                    for distance in straight + diagonal:
                        self.assertGreaterEqual(distance, q - EPS)
                    close = [distance for distance in straight if distance < pitch - EPS]
                    if len(nets) > 1 and q < pitch - EPS:
                        self.assertAlmostEqual(min(close), q, delta=EPS)
                        sections = _bundle_cross_sections(pieces, nets)
                        self.assertTrue(sections, "no height where every route runs in its bundle")
                        for _, gaps in sections:
                            for gap in gaps:
                                self.assertAlmostEqual(gap, q, delta=EPS)
                    near = [distance for distance in diagonal if distance < q + 0.01]
                    if near:
                        self.assertLessEqual(max(near), q + 5 * EPS)
                    self.assertEqual(board["construction"]["fanout_bundle_pitch_mm"], q)

    def test_every_gap_keeps_the_trace_space_and_the_finger_section_its_spacing(self) -> None:
        # T-D3: every pair of different nets keeps the trace space, and every pair
        # with a wide tail piece the finger-section spacing (contact pitch less
        # finger width), on every design, intermediate bundle widths included;
        # the DRC's route_route_clearance measures the same finger-section gap.
        finger_space = round(self.profile["connector"]["pad_pitch_mm"] - self.profile["routing"]["finger_trace_width_mm"], 6)
        for design, result in zip(DESIGNS, self.results):
            space = result["design"]["routing"]["trace_space_mm"]
            for board in result["boards"].values():
                pieces, nets = _pieces(board)
                segments = [
                    (net, kind, width / 2, a, b)
                    for net in nets for kind, (width, points) in pieces[net].items() for a, b in zip(points, points[1:])
                ]
                smallest, smallest_finger = math.inf, math.inf
                for first, second in _close_pairs(segments, 2.0):
                    net, kind, radius, a, b = segments[first]
                    other, other_kind, other_radius, c, d = segments[second]
                    if other == net:
                        continue
                    gap = gc.segment_distance(a, b, c, d) - radius - other_radius
                    smallest = min(smallest, gap)
                    if "tail" in (kind, other_kind):
                        smallest_finger = min(smallest_finger, gap)
                record = board["verification"]["checks"]["route_route_clearance"]
                with self.subTest(design=design, board=board["id"]):
                    self.assertGreaterEqual(smallest, space - EPS)
                    self.assertAlmostEqual(smallest, space, delta=EPS)  # the bundle sets the minimum
                    self.assertGreaterEqual(smallest_finger, finger_space - EPS)
                    self.assertAlmostEqual(smallest_finger, finger_space, delta=EPS)  # neighbouring tail pieces
                    self.assertEqual(record["finger_section"]["required_mm"], finger_space)
                    self.assertAlmostEqual(record["finger_section"]["measured_mm"], smallest_finger, delta=EPS)
                    self.assertEqual(record["finger_section"]["violation_count"], 0)

    def test_the_traces_widen_in_the_tail_below_every_bend(self) -> None:
        # T-D3: the width changes only at the contact pitch, below every bend
        # of the fan-out, at one level per board, in the tail above the
        # stiffener edge (the wide traces cross the edge the stiffener flexes).
        stiffener = self.profile["tail"]["stiffener_length_mm"]
        for design, result in zip(DESIGNS, self.results):
            for board in result["boards"].values():
                pieces, nets = _pieces(board)
                turn = _canonical(board)
                contacts = {pad["net"]: turn((pad["x"], pad["y"]))[0] for pad in board["layers"]["top_copper"]["pads"]}
                tip = min(turn(point)[1] for point in board["outline"]["points"])
                levels, bends = set(), []
                with self.subTest(design=design, board=board["id"]):
                    for net in nets:
                        tail, fanout = pieces[net]["tail"][1], pieces[net]["fanout"][1]
                        self.assertEqual(len(tail), 2, net)
                        self.assertTrue(all(abs(x - contacts[net]) < EPS for x, _ in tail), net)
                        self.assertLess(abs(fanout[1][0] - contacts[net]), EPS, net)  # straight on from the junction
                        levels.add(round(tail[-1][1], 6))
                        bends += [y for _, y in fanout[1:-1]]
                    self.assertEqual(len(levels), 1)
                    (junction,) = levels
                    self.assertGreater(min(bends), junction + EPS)
                    self.assertGreater(junction - tip, stiffener)

    def test_row_channel_lanes_and_expansion(self) -> None:
        # T-D6: lanes at the bundle pitch, lane 1 straight above contact 1, the
        # channel width and the field position from q, the expansion in the body
        # below the field (with the active margin) and above the tail root.
        margin = self.profile["routing"]["active_edge_clearance_mm"]
        side = self.profile["connector"]["contact_center_to_side_edge_mm"]
        for design, result in zip(DESIGNS, self.results):
            board = result["boards"]["row"]
            routing = result["design"]["routing"]
            q = round(routing["trace_width_mm"] + routing["trace_space_mm"], 6)
            rows = result["design"]["matrix"]["rows"]
            pieces, nets = _pieces(board)
            turn = _canonical(board)
            active = board["grid_registration"]["active_region"]
            corners = [turn((active["x"], active["y"])), turn((active["x"] + active["width"], active["y"] + active["height"]))]
            field_x, field_y = min(x for x, _ in corners), min(y for _, y in corners)
            outline = [turn(point) for point in board["outline"]["points"]]
            left = min(x for x, _ in outline)
            with self.subTest(design=design):
                channel = round((rows - 1) * q + 2 * side, 6)
                self.assertEqual(board["construction"]["channel_width_mm"], channel)
                self.assertAlmostEqual(field_x - left, channel + margin, delta=EPS)
                first = pieces["ROW_01"]["fanout"][1]
                self.assertLess(abs(first[0][0] - first[1][0]), EPS)  # lane 1 needs no lateral move
                self.assertAlmostEqual(first[0][0] - left, side, delta=EPS)
                for index, net in enumerate(nets):
                    fanout = pieces[net]["fanout"][1]
                    lane = fanout[-2][0]  # the lane, then the stub to the electrode
                    self.assertAlmostEqual(lane - left, side + index * q, delta=EPS)
                    for _, y in fanout[1:-2]:
                        self.assertLessEqual(y, field_y - margin + EPS)  # below the field
                        self.assertGreater(y, fanout[0][1])  # above the tail root

    def test_bend_stagger_and_angle(self) -> None:
        # T-D4: bundle-side bends of neighbours that move the same way are
        # staggered by the grid-rounded q * tan(cap / 2), and every diagonal
        # runs at that bus angle, at most the profile's taper cap: also the
        # shortest ones, whose ends the 1e-6 mm grid would tilt past the cap if
        # their far bends were rounded to the nearest grid value.
        cap = self.profile["fanout"]["maximum_taper_angle_deg"]
        for design, result in zip(DESIGNS, self.results):
            routing = result["design"]["routing"]
            q = round(routing["trace_width_mm"] + routing["trace_space_mm"], 6)
            stagger = math.floor(q * math.tan(math.radians(cap) / 2) * 1e6 + 1e-6) / 1e6
            for board in result["boards"].values():
                pieces, nets = _pieces(board)
                with self.subTest(design=design, board=board["id"]):
                    self.assertAlmostEqual(board["construction"]["bend_stagger_mm"], stagger, delta=1e-9)
                    bus = max(board["construction"].get("entry_taper_angle_deg", 0.0), board["construction"]["merger_taper_angle_deg"])
                    angles, long_angles = [], []
                    for net in nets:
                        points = pieces[net]["fanout"][1]
                        for (x0, y0), (x1, y1) in zip(points, points[1:]):
                            if abs(x1 - x0) > 1e-9 and abs(y1 - y0) > 1e-9:
                                angle = math.degrees(math.atan2(abs(x1 - x0), abs(y1 - y0)))
                                angles.append(angle)
                                if abs(x1 - x0) > 1e-3 and abs(y1 - y0) > 1e-3:
                                    long_angles.append(angle)
                    if angles:
                        self.assertLessEqual(max(angles), cap)
                        self.assertLessEqual(max(angles), bus + 1e-6)
                    if long_angles:
                        self.assertGreater(min(long_angles), cap - 0.05)


class RoutingInputTests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = load_profile()
        self.limits = input_limits(self.profile)

    def test_defaults_and_ranges_come_from_the_profile(self) -> None:
        design = default_design()
        # routing.row_sides: the generic template's Row traces, the diagonal Row bus by default (section 18).
        self.assertEqual(design["routing"], {"trace_width_mm": 0.127, "trace_space_mm": 0.127, "row_sides": "both"})
        self.assertEqual(list(design), ["schema_version", "template_id", "project_name", "matrix", "tail", "connector", "role_mapping", "channel_order", "routing"])
        width, space = fabrication_minimum(self.profile)
        limits = self.profile["limits"]
        self.assertEqual((limits["minimum_trace_width_mm"], limits["minimum_trace_space_mm"]), (width, space))  # JLC 1 oz: 4/4 mil
        self.assertEqual(width, 0.1016)
        self.assertEqual(limits["maximum_trace_width_mm"], self.profile["routing"]["finger_trace_width_mm"])
        self.assertEqual(round(limits["maximum_trace_width_mm"] + limits["maximum_trace_space_mm"], 6), self.profile["connector"]["pad_pitch_mm"])
        schema = design_schema(self.profile)["properties"]
        for kind in ("width", "space"):
            field = f"routing.trace_{kind}_mm"
            spec = self.limits[field]
            with self.subTest(field=field):
                self.assertEqual((spec["minimum"], spec["maximum"], spec["default"]), (limits[f"minimum_trace_{kind}_mm"], limits[f"maximum_trace_{kind}_mm"], 0.127))
                self.assertEqual(spec["aliases"], [f"trace_{kind}_mm"])
                nested = schema["routing"]["properties"][f"trace_{kind}_mm"]
                self.assertEqual((nested["minimum"], nested["maximum"], nested["default"]), (spec["minimum"], spec["maximum"], spec["default"]))
                self.assertEqual((schema[f"trace_{kind}_mm"]["minimum"], schema[f"trace_{kind}_mm"]["maximum"]), (spec["minimum"], spec["maximum"]))
                self.assertIn("0.1016 mm", spec["description"])
        self.assertIn("4/4 mil", self.limits["routing.trace_width_mm"]["description"])
        self.assertIn("0.254 mm", self.limits["routing.trace_width_mm"]["description"])

    def test_out_of_range_values_are_field_errors_with_working_bounds(self) -> None:
        for kind, code in (("width", "E_TRACE_WIDTH"), ("space", "E_TRACE_SPACE")):
            field = f"routing.trace_{kind}_mm"
            low, high = self.limits[field]["minimum"], self.limits[field]["maximum"]
            for value in (round(low - 1e-6, 6), 0.0889, round(high + 1e-6, 6), 0.5, -0.1):
                checked = check_design({"routing": {f"trace_{kind}_mm": value}})
                with self.subTest(field=field, value=value):
                    self.assertFalse(checked["ok"])
                    self.assertEqual([(e["code"], e["field"]) for e in checked["validation"]["errors"]], [(code, field)])
                    message = checked["validation"]["errors"][0]["message"]
                    bounds = [float(number) for number in re.findall(r"between ([0-9.]+) and ([0-9.]+) mm", message)[0]]
                    self.assertEqual(bounds, [low, high])
                    for bound in bounds:
                        self.assertTrue(generate_design({"routing": {f"trace_{kind}_mm": bound}})["ok"])
            for value in ("0.127", None, True, [0.127]):
                checked = check_design({"routing": {f"trace_{kind}_mm": value}})
                with self.subTest(field=field, value=value):
                    self.assertEqual([(e["code"], e["field"]) for e in checked["validation"]["errors"]], [("E_NUMERIC", field)])
        checked = check_design({"routing": [0.127, 0.127]})
        self.assertEqual([(e["code"], e["field"]) for e in checked["validation"]["errors"]], [("E_ROUTING_OBJECT", "routing")])
        unknown = check_design({"routing": {"trace_width": 0.127}})
        self.assertEqual([(e["code"], e["field"]) for e in unknown["validation"]["errors"]], [("E_UNKNOWN_FIELD", "routing.trace_width")])
        self.assertIn("did you mean routing.trace_width_mm?", unknown["validation"]["errors"][0]["message"])

    def test_aliases_precedence_and_the_grid(self) -> None:
        flat = check_design({"trace_width_mm": 0.15, "trace_space_mm": 0.2})
        self.assertTrue(flat["ok"], flat["validation"]["errors"])
        self.assertEqual(flat["design"]["routing"], {"trace_width_mm": 0.15, "trace_space_mm": 0.2, "row_sides": "channel"})
        nested = check_design({"routing": {"trace_width_mm": 0.15, "trace_space_mm": 0.2}})
        self.assertEqual(flat["identity"]["build_id"], nested["identity"]["build_id"])
        applied = {(entry["alias"], entry["field"]) for entry in flat["validation"]["normalization"]["aliases_applied"]}
        self.assertEqual(applied, {("trace_width_mm", "routing.trace_width_mm"), ("trace_space_mm", "routing.trace_space_mm")})
        shadowed = check_design({"trace_width_mm": 0.2, "routing": {"trace_width_mm": 0.15}})
        self.assertEqual(shadowed["design"]["routing"]["trace_width_mm"], 0.15)
        self.assertEqual([w["code"] for w in shadowed["validation"]["warnings"] if w["field"] == "trace_width_mm"], ["W_ALIAS_SHADOWED"])
        rounded = check_design({"routing": {"trace_width_mm": 0.1270004, "trace_space_mm": 0.1269996}})
        self.assertEqual(rounded["design"]["routing"], {"trace_width_mm": 0.127, "trace_space_mm": 0.127, "row_sides": "channel"})
        self.assertEqual(rounded["identity"]["build_id"], check_design({})["identity"]["build_id"])
        defaulted = check_design({"matrix": {"rows": 4}})
        self.assertIn("routing.trace_width_mm", defaulted["validation"]["normalization"]["defaults_applied"])

    def test_the_browser_form_sends_both_fields_with_the_profile_limits(self) -> None:
        page = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        script = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
        for label, control, name, field in (("Trace width", "traceWidth", "trace_width_mm", "routing.trace_width_mm"), ("Trace spacing", "traceSpace", "trace_space_mm", "routing.trace_space_mm")):
            with self.subTest(field=field):
                self.assertRegex(page, rf'<label for="{control}">{label}</label>')
                tag = re.search(rf'<input id="{control}"[^>]*>', page).group(0)
                self.assertIn(f'name="{name}"', tag)
                self.assertIn(f'data-field="{field}"', tag)
                self.assertIn('type="number"', tag)
                self.assertNotRegex(tag, r'\b(min|max|step)=')  # applied from /api/default profile.limits
                self.assertIn(f'{name}: value("{control}")', script)


if __name__ == "__main__":
    unittest.main()
