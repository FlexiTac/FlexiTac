"""The diagonal Row bus's integer-nanometre primitives (``engine/bus.py``, masked-field phase P5a).

Each lane of the ``diagonal-bus/4`` construction is the west convex chain
from its electrode end down to its target around obstacle points, and the
next lane out keeps east of the lane's keep-out: the mitred offset of the
lane and its continuation (cut on the vertical one pitch west of the lane's
inward turn where it follows a receding field), and a box around its start
(claude/specs/masked-field/P5-diagonal-bus.md, sections 2.3 and 14.2).  These tests
check the primitives with exact integer predicates of their own (no
``engine.geometry``): hand cases at 0, 2.9, 45 and 84 degrees; seeded
property tests of the chains (strictly convex with exact orientations,
strictly descending, every point in range on the east side or on the chain,
vertices from the input, blind to the input's order and repeats), of the
offsets (axis-parallel segments at the distance exactly, slanted ones at the
distance + 2 nm, each coordinate rounded away from the chain, never nearer
the chain than the distance, sharp turns included), of the keep-outs (their
west hull holds every point at the distance from the lane and its
continuation, jogs included) and of onions of lanes (each lane at least the
bundle pitch from every lane inside it, the inner lanes' continuations
included; a lane turning inward nests the next one exactly one pitch out at
its turn, which round the mitre would spread); the box helpers; and determinism (a pinned
digest of a seeded corpus, the same on Python 3.9 and 3.12, no float
``sum()``, no set iterated in order, no libm call but ``sqrt``).
"""

from __future__ import annotations

import ast
import hashlib
import inspect
import json
import math
import random
import unittest
from pathlib import Path

from engine import bus
from engine import layout

try:
    from test_mask_layout import _determinism_problems
except ImportError:  # run as tests.test_bus
    from tests.test_mask_layout import _determinism_problems

ROOT = Path(__file__).resolve().parents[1]
BP = 203200  # the bundle pitch at 4 mil trace and space (0.1016 + 0.1016 mm), in nm
MM = 1_000_000
# Lane directions (dx, dy) at 0, 2.9, 45 and 84 degrees from the vertical, heading down and west: the straight side,
# the two-sided bus's widening asin(bp / 2 py) at 2 mm pitch and 4 mil, the 45-degree hypotenuse and the steepest
# lane under the 85-degree taper cap.
ANGLES = {0: (0, -4 * MM), 2.9: (-203200, -4 * MM), 45: (-3 * MM, -3 * MM), 84: (-9514364, -1 * MM)}


# --------------------------------------------------------------------------
# Exact integer predicates (independent of engine.bus and engine.geometry).
# --------------------------------------------------------------------------


def _orientation(o, a, b) -> int:
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _ceil_ratio(numerator: int, length2: int) -> int:
    """The smallest integer k >= 0 with k >= numerator / sqrt(length2), exactly (numerator >= 0)."""

    k = math.isqrt(numerator * numerator // length2)
    while k * k * length2 < numerator * numerator:
        k += 1
    while k > 0 and (k - 1) * (k - 1) * length2 >= numerator * numerator:
        k -= 1
    return k


def _west_of_line_by(p, a, b, distance: int) -> bool:
    """``p`` lies at least ``distance`` (> 0) on the west (right-hand) side of the directed line ``a -> b``, exactly."""

    side = -_orientation(a, b, p)  # the right-hand side's signed distance times |b - a|
    length2 = (b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2
    return side >= 0 and side * side >= distance * distance * length2


def _line_distance(p, a, b) -> float:
    """The signed distance of ``p`` west of the directed line ``a -> b`` (diagnostics and upper bounds)."""

    return -_orientation(a, b, p) / math.sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2)


def _point_segment_at_least(p, a, b, distance: int) -> bool:
    vx, vy = b[0] - a[0], b[1] - a[1]
    wx, wy = p[0] - a[0], p[1] - a[1]
    along = wx * vx + wy * vy
    length2 = vx * vx + vy * vy
    if along <= 0:
        return wx * wx + wy * wy >= distance * distance
    if along >= length2:
        return (p[0] - b[0]) ** 2 + (p[1] - b[1]) ** 2 >= distance * distance
    side = _orientation(a, b, p)
    return side * side >= distance * distance * length2


def _segments_meet(a, b, c, d) -> bool:
    def on(p, q, r) -> bool:
        return min(p[0], q[0]) <= r[0] <= max(p[0], q[0]) and min(p[1], q[1]) <= r[1] <= max(p[1], q[1])

    o1, o2, o3, o4 = _orientation(a, b, c), _orientation(a, b, d), _orientation(c, d, a), _orientation(c, d, b)
    if ((o1 > 0) != (o2 > 0)) and o1 != 0 and o2 != 0 and ((o3 > 0) != (o4 > 0)) and o3 != 0 and o4 != 0:
        return True
    return (o1 == 0 and on(a, b, c)) or (o2 == 0 and on(a, b, d)) or (o3 == 0 and on(c, d, a)) or (o4 == 0 and on(c, d, b))


def _segments_at_least(a, b, c, d, distance: int) -> bool:
    """Two segments keep at least ``distance`` apart, exactly."""

    if min(a[0], b[0]) - max(c[0], d[0]) >= distance or min(c[0], d[0]) - max(a[0], b[0]) >= distance:
        return True
    if min(a[1], b[1]) - max(c[1], d[1]) >= distance or min(c[1], d[1]) - max(a[1], b[1]) >= distance:
        return True
    if _segments_meet(a, b, c, d):
        return False
    return all((
        _point_segment_at_least(a, c, d, distance), _point_segment_at_least(b, c, d, distance),
        _point_segment_at_least(c, a, b, distance), _point_segment_at_least(d, a, b, distance),
    ))


def _paths_at_least(one, two, distance: int) -> list:
    """The segment pairs of two polylines that come nearer than ``distance`` (empty when none does)."""

    return [
        (a, b, c, d) for a, b in zip(one, one[1:]) for c, d in zip(two, two[1:])
        if not _segments_at_least(a, b, c, d, distance)
    ]


def _segment_distance(a, b, c, d) -> float:
    """Float distance between two segments, for messages only."""

    def point(p, q, r) -> float:
        vx, vy = r[0] - q[0], r[1] - q[1]
        length2 = vx * vx + vy * vy
        t = 0.0 if length2 == 0 else max(0.0, min(1.0, ((p[0] - q[0]) * vx + (p[1] - q[1]) * vy) / length2))
        return math.sqrt((p[0] - q[0] - t * vx) ** 2 + (p[1] - q[1] - t * vy) ** 2)

    if _segments_meet(a, b, c, d):
        return 0.0
    return min(point(a, c, d), point(b, c, d), point(c, a, b), point(d, a, b))


def _slanted(a, b) -> bool:
    return a[0] != b[0] and a[1] != b[1]


def _check_chain(test: unittest.TestCase, chain, start, target, points) -> None:
    """The west chain's contract, by exact predicates."""

    start, target = tuple(start), tuple(target)
    test.assertEqual(chain[0], start)
    test.assertEqual(chain[-1], target)
    inside = {tuple(p) for p in points if target[1] < p[1] < start[1]}
    test.assertTrue(all(p in inside for p in chain[1:-1]), "every interior vertex is an input point")
    test.assertTrue(all(a[1] > b[1] for a, b in zip(chain, chain[1:])), "the chain descends strictly")
    turns = [_orientation(a, b, c) for a, b, c in zip(chain, chain[1:], chain[2:])]
    test.assertTrue(all(turn > 0 for turn in turns), f"every interior vertex is a strict left turn: {turns}")
    for p in sorted(inside):
        a, b = next((a, b) for a, b in zip(chain, chain[1:]) if b[1] <= p[1] <= a[1])
        test.assertGreaterEqual(_orientation(a, b, p), 0, f"{p} lies west of the chain segment {a}-{b}")


def _random_chain_case(rng: random.Random, grid: int) -> tuple:
    top = rng.randint(4, 30) * MM
    count = rng.randint(0, 14)
    points = [(rng.randint(-20, 20) * grid, rng.randint(1, top // grid - 1) * grid) for _ in range(count)]
    start = (rng.randint(-5, 5) * grid, top)
    west = min([p[0] for p in points] + [start[0]])
    target = (west - rng.choice((0, 0, rng.randint(0, 3 * MM // grid) * grid)), -rng.randint(0, 4) * grid)
    return start, target, points


def _follow(rng: random.Random, chain: list) -> tuple:
    """A continuation below a chain: the descent, a jog outward, the corridor run (east, mirrored) or a jog inward."""

    x, y = chain[-1]
    kind = rng.randint(0, 3)
    if kind == 0:
        return (x, y - rng.randint(1, 5) * MM)
    if kind == 1:
        return (x - rng.randint(1, 3 * MM), y - rng.randint(1, 3 * MM))
    if kind == 2:
        return (x + rng.randint(1, 3) * MM, y)
    return (x + rng.randint(1, 3 * MM), y - rng.randint(1, 3 * MM))


# --------------------------------------------------------------------------
# Conversions and the constants.
# --------------------------------------------------------------------------


class BusConversionTests(unittest.TestCase):
    def test_millimetres_and_nanometres_round_trip_on_the_grid(self) -> None:
        rng = random.Random(7)
        for _ in range(2000):
            value_nm = rng.randint(-500 * MM, 500 * MM)
            self.assertEqual(bus.to_nm(bus.to_mm(value_nm)), value_nm)
            value_mm = round(value_nm / 1e6, 6)
            self.assertEqual(bus.to_mm(bus.to_nm(value_mm)), value_mm)
        self.assertEqual((bus.to_nm(0.1016), bus.to_nm(-0.500801), bus.to_nm(2.0)), (101600, -500801, 2 * MM))
        self.assertEqual((bus.to_mm(203200), bus.to_mm(-1)), (0.2032, -0.000001))
        self.assertEqual(bus.nm_box(-0.2, 0.1, 1.4, 2.0), (-200000, 100000, 1400000, 2000000))

    def test_the_slant_allowance_is_the_layouts_diagonal_allowance(self) -> None:
        self.assertEqual(bus.SLANT_ALLOWANCE_NM, bus.to_nm(layout._DIAGONAL_ALLOWANCE_MM))
        self.assertEqual(bus.NM, 1_000_000)


# --------------------------------------------------------------------------
# The west chain.
# --------------------------------------------------------------------------


class WestChainTests(unittest.TestCase):
    def test_a_lane_with_nothing_west_of_it_is_one_segment(self) -> None:
        for angle, (dx, dy) in ANGLES.items():
            with self.subTest(angle=angle):
                start, target = (0, 10 * MM), (dx * 2, 10 * MM + dy * 2)
                east = [(start[0] + MM, start[1] - MM), (target[0] + MM, target[1] + MM), (0, 5 * MM + 1)]
                if angle:
                    east = [p for p in east if _orientation(start, target, p) > 0]
                chain = bus.west_chain(start, target, east)
                self.assertEqual(chain, [start, target])

    def test_collinear_points_are_dropped(self) -> None:
        # On a 45-degree lane, every grid point of the line between the ends lies on the chain: none is a vertex.
        start, target = (0, 10 * MM), (-10 * MM, 0)
        line = [(-k * MM, 10 * MM - k * MM) for k in range(1, 10)]
        self.assertEqual(bus.west_chain(start, target, line), [start, target])
        # The hull's straight edges keep their ends only: (-1.5, 7.5) is on start-A, (-3.5, 4.5) on A-B.
        a, b = (-3 * MM, 6 * MM), (-4 * MM, 3 * MM)
        points = [a, b, (-1500000, 7500000), (-3500000, 4500000), (-2 * MM, 5 * MM), (-4 * MM, 2 * MM), (-4 * MM, 1 * MM)]
        chain = bus.west_chain((0, 9 * MM), (-4 * MM, 0), points)
        self.assertEqual(chain, [(0, 9 * MM), a, b, (-4 * MM, 0)])
        _check_chain(self, chain, (0, 9 * MM), (-4 * MM, 0), points)
        # A vertical run down the west edges of a column of boxes is one segment.
        column = [(-MM, y * MM) for y in range(1, 9)] + [(0, y * MM) for y in range(1, 9)]
        self.assertEqual(bus.west_chain((-MM, 9 * MM), (-MM, 0), column), [(-MM, 9 * MM), (-MM, 0)])

    def test_only_points_strictly_between_the_ends_take_part(self) -> None:
        start, target = (0, 10 * MM), (0, 0)
        outside = [(-50 * MM, 10 * MM), (-50 * MM, 0), (-50 * MM, 11 * MM), (-50 * MM, -1)]
        self.assertEqual(bus.west_chain(start, target, outside), [start, target])
        self.assertEqual(bus.west_chain(start, target, outside + [(-1, 1)]), [start, (-1, 1), target])
        self.assertEqual(bus.west_chain(start, target, outside + [(-1, 9999999)]), [start, (-1, 9999999), target])

    def test_the_hand_hull_around_a_staircase(self) -> None:
        # Box corners of a field edge that widens ever less going down (a disk's upper left: the west edges at 0, -2,
        # -2.8 and -3 mm, rows 2 mm apart): the taut lane touches the upper outer corner of each widening row, and a
        # receding staircase (1 mm west per row) is one straight diagonal past its corners.
        for edges, vertices in (
            ((0, -2 * MM, -2800000, -3 * MM), [(-2 * MM, 6700000), (-2800000, 4700000), (-3 * MM, 2700000)]),
            ((0, -MM, -2 * MM, -3 * MM), [(-3 * MM, 2700000)]),
        ):
            corners = []
            for row, x0 in enumerate(edges):
                y = (8 - 2 * row) * MM
                corners += bus.box_corners((x0, y - 700000, x0 + 1400000, y + 700000))
            start, target = (0, 9 * MM), (-3 * MM, -MM)
            with self.subTest(edges=edges):
                chain = bus.west_chain(start, target, corners)
                self.assertEqual(chain, [start, *vertices, target])
                _check_chain(self, chain, start, target, corners)

    def test_random_chains_keep_the_contract(self) -> None:
        rng = random.Random(1)
        for index in range(600):
            grid = rng.choice((1, 1000, 250000, MM))  # coarse grids make collinear and repeated points common
            start, target, points = _random_chain_case(rng, grid)
            with self.subTest(case=index, grid=grid):
                chain = bus.west_chain(start, target, points)
                _check_chain(self, chain, start, target, points)
                # Blind to the input's order, repeats and container types.
                shuffled = points * 2
                rng.shuffle(shuffled)
                self.assertEqual(bus.west_chain(list(start), list(target), [list(p) for p in shuffled]), chain)
                self.assertEqual(bus.west_chain(start, target, iter(sorted(set(points)))), chain)

    def test_the_mirrored_frame_gives_the_east_chain(self) -> None:
        rng = random.Random(2)
        for index in range(100):
            start, target, points = _random_chain_case(rng, 1000)
            east = bus.mirror(bus.west_chain(*bus.mirror([start, target]), bus.mirror(points)))
            with self.subTest(case=index):
                self.assertEqual(east[0], start)
                for p in points:
                    if target[1] < p[1] < start[1]:
                        a, b = next((a, b) for a, b in zip(bus.mirror(east), bus.mirror(east)[1:]) if b[1] <= p[1] <= a[1])
                        self.assertGreaterEqual(_orientation(a, b, (-p[0], p[1])), 0)
                turns = [_orientation(a, b, c) for a, b, c in zip(east, east[1:], east[2:])]
                self.assertTrue(all(turn < 0 for turn in turns), "the east chain turns right (clockwise) going down")


# --------------------------------------------------------------------------
# The mitred offset.
# --------------------------------------------------------------------------


def _perpendicular_end(vertex, a, b, distance: int) -> tuple:
    """The exact outward-rounded perpendicular offset of ``vertex`` for the segment ``a -> b`` (independent)."""

    dx, dy = b[0] - a[0], b[1] - a[1]
    length2 = dx * dx + dy * dy
    # The west normal (dy, -dx) / |d|: each coordinate rounded away from the chain, i.e. along its own sign.
    ox = _ceil_ratio(abs(dy) * distance, length2)
    oy = _ceil_ratio(abs(dx) * distance, length2)
    return (vertex[0] + (ox if dy > 0 else -ox), vertex[1] + (-oy if dx > 0 else oy))


class MitredOffsetTests(unittest.TestCase):
    def test_hand_offsets_at_0_2_9_45_and_84_degrees(self) -> None:
        expected = {
            0: [(-BP, 10 * MM), (-BP, 2 * MM)],
            2.9: [(-202941, 10010310), (-609341, 2010310)],
            45: [(-143686, 10143686), (-6143686, 4143686)],
            84: [(-21241, 10202089), (-19049969, 8202089)],
        }
        for angle, (dx, dy) in ANGLES.items():
            start = (0, 10 * MM)
            end = (start[0] + dx * 2, start[1] + dy * 2)
            with self.subTest(angle=angle):
                offset = bus.mitred_offset([start, end], BP)
                distance = BP + (bus.SLANT_ALLOWANCE_NM if angle else 0)
                # Independent: the exact perpendicular ends rounded away from the chain.
                self.assertEqual(offset, [_perpendicular_end(start, start, end, distance), _perpendicular_end(end, start, end, distance)])
                self.assertEqual(offset, expected[angle])
                for vertex in offset:
                    self.assertTrue(_west_of_line_by(vertex, start, end, distance))
                    self.assertLess(_line_distance(vertex, start, end), distance + 1.5)

    def test_axis_parallel_offsets_are_the_distance_exactly(self) -> None:
        # A vertical lane, its corridor turn (east, as on the far side in the mirrored frame) and a vertical descent.
        chain = [(0, 10 * MM), (0, 0), (3 * MM, 0)]
        self.assertEqual(bus.mitred_offset(chain, BP), [(-BP, 10 * MM), (-BP, -BP), (3 * MM, -BP)])
        self.assertEqual(bus.mitred_offset([(5, 7), (5, 3), (5, -2)], BP), [(5 - BP, 7), (5 - BP, 3), (5 - BP, -2)])
        # Straight on along a slant keeps one vertex, at the slanted distance.
        straight = bus.mitred_offset([(0, 0), (-MM, -MM), (-2 * MM, -2 * MM)], BP)
        self.assertEqual(len(straight), 3)
        self.assertEqual(straight[1], _perpendicular_end((-MM, -MM), (0, 0), (-MM, -MM), BP + 2))
        # Repeats are dropped; fewer than two distinct points have no offset.
        self.assertEqual(bus.mitred_offset([(0, 10), (0, 10), (0, 0), (0, 0)], BP), [(-BP, 10), (-BP, 0)])
        self.assertEqual(bus.mitred_offset([(0, 10), (0, 10)], BP), [])
        self.assertEqual(bus.mitred_offset([], BP), [])

    def test_joins_after_a_vertical_run_at_each_angle(self) -> None:
        # The descent bends west (a jog: concave, trimmed) or east (convex, mitred) at each angle; the join vertex lies
        # on the vertical run's offset line exactly and at least the slanted distance from the slanted line.
        for angle, (dx, dy) in ANGLES.items():
            if not angle:
                continue
            for side in (-1, 1):
                top, vertex = (0, 10 * MM), (0, 0)
                end = (side * -dx, dy)
                with self.subTest(angle=angle, side="east (mitre)" if side > 0 else "west (trim)"):
                    offset = bus.mitred_offset([top, vertex, end], BP)
                    self.assertEqual(len(offset), 3)
                    join = offset[1]
                    self.assertEqual(join[0], -BP)
                    self.assertTrue(_west_of_line_by(join, vertex, end, BP + 1))
                    self.assertLess(_line_distance(join, vertex, end), BP + 2 + 1.5)
                    # A trim lies above the vertex, a mitre below it.
                    self.assertEqual(join[1] > 0, side < 0)

    def test_a_sharp_turn_takes_a_square_join_at_the_distance(self) -> None:
        # A lane at 84 degrees, then the corridor run east (a convex turn of 174 degrees), and a reversal: the join
        # never comes nearer the vertex than the distance (a bevel would cut it at about half of it).
        dx, dy = ANGLES[84]
        for chain in ([(0, 10 * MM), (dx, 10 * MM + dy), (dx + 3 * MM, 10 * MM + dy)], [(0, 10 * MM), (0, 0), (0, 5 * MM)]):
            with self.subTest(chain=chain):
                offset = bus.mitred_offset(chain, BP)
                self.assertEqual(len(offset), 4)
                self.assertEqual(_paths_at_least(offset, chain, BP), [])
                vertex = chain[1]
                for point in offset[1:3]:
                    self.assertGreaterEqual((point[0] - vertex[0]) ** 2 + (point[1] - vertex[1]) ** 2, 2 * BP * BP)

    def test_nearly_straight_joins_stay_near_their_vertex(self) -> None:
        # A vertical run, then a slant of 1 nm in 10 mm (the offsets differ by the 2 nm allowance): the offset lines
        # meet 20 m away, so the join steps between the two perpendicular ends instead; at 1 nm in 1 mm both ways.
        for drift, length in ((1, 10 * MM), (-1, 10 * MM), (1, MM), (-1, MM), (1000, MM)):
            chain = [(0, 10 * MM), (0, 0), (drift, -length)]
            with self.subTest(drift=drift, length=length):
                offset = bus.mitred_offset(chain, BP)
                self.assertTrue(all(abs(x) <= BP + 1000 and -length - BP <= y <= 10 * MM + BP for x, y in offset), offset)
                self.assertEqual(_paths_at_least(offset, chain, BP), [])
        # Two slants of equal distance turning by 1e-16 rad: the mitre is the vertex's perpendicular end.
        chain = [(0, 0), (1, -100 * MM), (2, -200 * MM + 1)]
        offset = bus.mitred_offset(chain, BP)
        self.assertEqual(offset[1], _perpendicular_end((1, -100 * MM), (0, 0), (1, -100 * MM), BP + 2))

    def test_random_offsets_keep_their_distances(self) -> None:
        rng = random.Random(3)
        checked_joins = convex = 0
        for index in range(500):
            grid = rng.choice((1, 1000, 250000))
            start, target, points = _random_chain_case(rng, grid)
            chain = bus.west_chain(start, target, points)
            chain = chain + [_follow(rng, chain)]
            distance = rng.choice((BP, 254000, 300000, 400000))
            with self.subTest(case=index):
                offset = bus.mitred_offset(chain, distance)
                # A chain that only turns left (a west chain with its descent or corridor run): the offset polyline
                # never comes nearer the chain than the distance (exactly, every segment pair).  After a right turn
                # (a jog outward) a trim may fall behind a short segment's start, inside the jog's band (the next
                # lane's hull bridges it); it still lies on both offset lines (below).
                if all(_orientation(a, b, c) >= 0 for a, b, c in zip(chain, chain[1:], chain[2:])):
                    self.assertEqual(_paths_at_least(offset, chain, distance), [], "the offset comes nearer than the distance")
                    convex += 1
                # The ends: exact perpendicular offsets rounded away from the chain, at the distance (+ 2 nm slanted).
                for vertex, (a, b) in ((offset[0], chain[:2]), (offset[-1], chain[-2:])):
                    allowance = bus.SLANT_ALLOWANCE_NM if _slanted(a, b) else 0
                    self.assertEqual(vertex, _perpendicular_end(b if vertex is offset[-1] else a, a, b, distance + allowance))
                # Single-vertex joins: on both offset lines, rounded away from the chain (slanted lines keep at least
                # one nanometre of the allowance; axis-parallel ones the distance exactly).
                if len(offset) == len(chain):
                    for vertex, (a, b, c) in zip(offset[1:-1], zip(chain, chain[1:], chain[2:])):
                        for p, q in ((a, b), (b, c)):
                            least = distance + 1 if _slanted(p, q) else distance
                            self.assertTrue(_west_of_line_by(vertex, p, q, least), (vertex, p, q, _line_distance(vertex, p, q)))
                            self.assertLess(_line_distance(vertex, p, q), distance + bus.SLANT_ALLOWANCE_NM + 1.5)
                            checked_joins += 1
        self.assertGreater(checked_joins, 1000)
        self.assertGreater(convex, 250)

    def test_mitres_are_rounded_away_from_the_chain(self) -> None:
        # Each join coordinate moves along the bisector of the two normals, by less than one grid step.
        rng = random.Random(4)
        moved = 0
        for index in range(300):
            start, target, points = _random_chain_case(rng, 1)
            chain = bus.west_chain(start, target, points)
            chain = chain + [_follow(rng, chain)]
            offset = bus.mitred_offset(chain, BP)
            if len(offset) != len(chain):
                continue
            for vertex, (a, b, c) in zip(offset[1:-1], zip(chain, chain[1:], chain[2:])):
                if _orientation(a, b, c) == 0:
                    continue  # straight on: the perpendicular end, checked above
                exact, bisector = _exact_join(a, b, c, BP)
                with self.subTest(case=index, vertex=vertex):
                    for axis in (0, 1):
                        delta = vertex[axis] - exact[axis]
                        self.assertLess(abs(delta), 1 + 1e-6)
                        if abs(bisector[axis]) > 1e-9 and abs(delta) > 1e-6:
                            self.assertGreater(delta * bisector[axis], 0, "rounded toward the chain")
                            moved += 1
        self.assertGreater(moved, 100)


def _exact_join(a, b, c, distance: int) -> tuple:
    """The intersection of the two offset lines at ``b`` by Cramer's rule in floats, and the normals' bisector."""

    def line(p, q):
        dx, dy = q[0] - p[0], q[1] - p[1]
        length = math.sqrt(dx * dx + dy * dy)
        d = distance + (bus.SLANT_ALLOWANCE_NM if dx and dy else 0)
        return dy / length, -dx / length, d  # q . n = d relative to b

    n0x, n0y, d0 = line(a, b)
    n1x, n1y, d1 = line(b, c)
    det = n0x * n1y - n0y * n1x
    qx = (d0 * n1y - n0y * d1) / det
    qy = (n0x * d1 - d0 * n1x) / det
    return (b[0] + qx, b[1] + qy), (n0x + n1x, n0y + n1y)


# --------------------------------------------------------------------------
# Onions: lanes built innermost first, each around the keep-outs of the lanes inside it.
# --------------------------------------------------------------------------


def _onion(rng: random.Random, keepout=bus.lane_keepout) -> tuple:
    """Random rows on a field edge, their lanes from the lowest row up (innermost first), continued straight down to
    a common bottom.  Each lane's target is at least one pitch outside the lane inside it and west of its points,
    and sometimes farther west (as the near band's lanes are held outside the Column copper), so the lane ends on a
    slant; an outer lane's target may lie lower than the inner one's (as at a staggered jog)."""

    pitch = rng.choice((BP, 254000, 300000, 400000))
    row_pitch = rng.choice((600000, 800000, 1250000, 2 * MM, 4 * MM))
    rows = rng.randint(2, 9)
    edge, x = [], 0
    for _ in range(rows):
        x += rng.choice((0, 0, rng.randint(-3 * row_pitch, 3 * row_pitch)))
        edge.append(x)
    obstacles = []
    for row in range(rows):
        gap, height = rng.randint(1, pitch), row_pitch // 2 - rng.randint(1, row_pitch // 4)
        obstacles += bus.box_corners((edge[row] + gap, row * row_pitch - height, edge[row] + gap + 3 * MM, row * row_pitch + height))
    stagger = rng.choice((0, pitch, 3 * pitch, row_pitch))
    first_target = -row_pitch - rng.randint(0, 2 * MM)
    bottom = first_target - rows * stagger - 5 * MM
    lanes, keepouts, previous = [], [], None
    for row in range(rows):
        start = (edge[row], row * row_pitch)
        target_y = first_target - row * stagger
        points = [p for p in obstacles + keepouts if target_y < p[1] < start[1]]
        west = min([p[0] for p in points] + [start[0]] + ([previous - pitch] if previous is not None else []))
        west -= rng.choice((0, 0, rng.randint(1, 3 * MM)))
        chain = bus.west_chain(start, (west, target_y), points)
        lanes.append(chain + [(west, bottom)])
        keepouts = keepouts + keepout(chain, (west, bottom), pitch)
        previous = west
    return pitch, lanes


def _band_points(path, distance: int) -> list:
    """Points at ``distance`` west of a polyline: 21 along each segment's offset line (20 along the last one, whose far
    end is open: the lane goes on beyond its continuation's first point), 11 on each left turn's round join."""

    answer = []
    for index, (a, b) in enumerate(zip(path, path[1:])):
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.sqrt(dx * dx + dy * dy)
        nx, ny = dy / length, -dx / length
        steps = range(20) if index == len(path) - 2 else range(21)
        answer += [(a[0] + step / 20 * dx + nx * distance, a[1] + step / 20 * dy + ny * distance) for step in steps]
    for a, b, c in zip(path, path[1:], path[2:]):
        if _orientation(a, b, c) > 0:
            first = math.atan2(-(b[0] - a[0]), b[1] - a[1])
            last = math.atan2(-(c[0] - b[0]), c[1] - b[1])
            if last < first:
                last += 2 * math.pi
            for step in range(11):
                angle = first + (last - first) * step / 10
                answer.append((b[0] + distance * math.cos(angle), b[1] + distance * math.sin(angle)))
    return answer


class LaneNestingTests(unittest.TestCase):
    def test_hand_lanes_nest_at_the_pitch(self) -> None:
        # An inner lane at each angle, continued straight down; the outer lane from two rows higher, its target lower.
        for angle, (dx, dy) in ANGLES.items():
            inner_start = (0, 10 * MM)
            inner_target = (dx * 2, 10 * MM + dy * 2)
            descent = (inner_target[0], inner_target[1] - 10 * MM)
            inner = [inner_start, inner_target]
            keepout = bus.lane_keepout(inner, descent, BP)
            outer_start = (-3 * BP, 14 * MM)
            target_y = inner_target[1] - 3 * BP
            west = min(p[0] for p in keepout if target_y < p[1] < outer_start[1])
            outer = bus.west_chain(outer_start, (west, target_y), keepout)
            with self.subTest(angle=angle):
                # The descents run exactly one pitch apart; the lanes never come nearer.
                self.assertEqual(west, inner_target[0] - BP)
                self.assertEqual(_paths_at_least(outer + [(west, descent[1])], inner + [descent], BP), [])
                _check_chain(self, outer, outer_start, (west, target_y), keepout)

    def test_the_continuation_belongs_to_the_keepout(self) -> None:
        # A lane at 38.7 degrees, then its descent: the next lane, whose target is lower, passes the mitre of the bend
        # (one pitch west of the descent, above the bend), so it keeps the pitch around the bend.
        inner = [(0, 10 * MM), (-8 * MM, 0)]
        follow = (-8 * MM, -10 * MM)
        keepout = bus.lane_keepout(inner, follow, BP)
        mitre = bus.mitred_offset(inner + [follow], BP)[1]
        self.assertEqual(mitre, (-8 * MM - BP, 71282))
        self.assertEqual(keepout, bus.mitred_offset(inner + [follow], BP) + [(-BP, 10 * MM - BP), (BP, 10 * MM - BP), (-BP, 10 * MM + BP), (BP, 10 * MM + BP)])
        target = (-8 * MM - BP, -5 * MM)
        outer = bus.west_chain((-MM, 12 * MM), target, keepout)
        self.assertIn(mitre, outer)
        self.assertEqual(_paths_at_least(outer + [(target[0], -10 * MM)], inner + [follow], BP), [])
        # Without the continuation the next lane cuts the bend: 0.1598 mm from it at a pitch of 0.2032 mm.
        short = bus.mitred_offset(inner, BP) + keepout[-4:]
        cut = bus.west_chain((-MM, 12 * MM), target, short)
        nearest = min(_segment_distance(a, b, c, d) for a, b in zip(cut, cut[1:]) for c, d in zip(inner + [follow], (inner + [follow])[1:]))
        self.assertAlmostEqual(nearest, 159771, delta=1)

    def test_the_keepouts_hull_holds_every_band(self) -> None:
        # Whatever the continuation (a descent, the corridor run, a jog outward even where its trim falls behind a
        # short segment), the west hull of a lane's keep-out holds every point at the distance west of the lane and its
        # continuation (up to the continuation's open far end): on each segment's offset line and on the round join
        # of each left turn.
        rng = random.Random(8)
        checked = 0
        for index in range(1200):
            start, target, points = _random_chain_case(rng, rng.choice((1, 1000, 250000)))
            chain = bus.west_chain(start, target, points)
            follow = _follow(rng, chain)
            distance = rng.choice((BP, 254000, 300000, 400000))
            keepout = bus.lane_keepout(chain, follow, distance)
            top = max(keepout, key=lambda p: (p[1], -p[0]))
            bottom = min(keepout, key=lambda p: (p[1], p[0]))
            hull = bus.west_chain(top, bottom, keepout)
            with self.subTest(case=index):
                for q in _band_points(chain + [follow], distance):
                    if bottom[1] < q[1] < top[1]:
                        a, b = next((a, b) for a, b in zip(hull, hull[1:]) if b[1] <= q[1] <= a[1])
                        self.assertGreater(-_line_distance(q, a, b), -1e-6, f"{q} lies west of the keep-out's hull")
                        checked += 1
        self.assertGreater(checked, 50000)

    def test_random_onions_nest_at_the_pitch(self) -> None:
        rng = random.Random(5)
        for index in range(300):
            pitch, lanes = _onion(rng)
            with self.subTest(case=index):
                for inner in range(len(lanes)):
                    for outer in range(inner + 1, len(lanes)):
                        near = _paths_at_least(lanes[outer], lanes[inner], pitch)
                        self.assertEqual(near, [], f"lanes {inner} and {outer} at {min((_segment_distance(*pair) for pair in near), default=None)}")
                for lane in lanes:
                    turns = [_orientation(a, b, c) for a, b, c in zip(lane, lane[1:-1], lane[2:-1])]
                    self.assertTrue(all(turn > 0 for turn in turns))

    def test_a_lane_turning_inward_nests_without_spreading(self) -> None:
        # A lane following a receding field: west and down to its westmost corner, east and down to the field's edge,
        # then straight down.  Its offset is cut on the vertical one pitch (and the slant allowance) west of that corner,
        # so the next lane out passes the corner exactly that far west, keeping the pitch from the lane all along; round
        # the mitre it would pass 1 / cos(turn / 2) farther out, and each lane outside it farther again.
        corner = (-6 * MM, 2 * MM)
        inner = [(0, 10 * MM), corner, (-4 * MM, 0)]
        follow = (-4 * MM, -5 * MM)
        reach = BP + bus.SLANT_ALLOWANCE_NM
        offset = bus.lane_offset(inner + [follow], BP)
        self.assertEqual(min(point[0] for point in offset), corner[0] - reach)
        self.assertEqual(bus.lane_keepout(inner, follow, BP)[:-4], offset)
        mitred = bus.mitred_offset(inner + [follow], BP)
        self.assertLess(min(point[0] for point in mitred), corner[0] - reach - 30000)
        # The next lane out, from higher up, round the keep-out down to the edge where the offset crosses it (rounded
        # west), then straight down.
        crossings = [a[0] + (b[0] - a[0]) * (0 - a[1]) // (b[1] - a[1]) for a, b in zip(offset, offset[1:]) if (a[1] > 0) != (b[1] > 0)]
        target = (min(crossings), 0)
        keepout = bus.lane_keepout(inner, follow, BP)
        outer = bus.west_chain((-BP, 12 * MM), target, keepout) + [(target[0], -5 * MM)]
        self.assertEqual(min(point[0] for point in outer), corner[0] - reach)
        self.assertEqual(_paths_at_least(outer, inner + [follow], BP), [])
        # Without the cut the next lane goes round the mitre, farther out.
        spread = bus.west_chain((-BP, 12 * MM), target, mitred + keepout[-4:])
        self.assertLess(min(point[0] for point in spread), corner[0] - reach - 30000)

    def test_lane_offset_is_the_mitred_offset_without_an_inward_turn(self) -> None:
        # Every west chain with its descent (a lane that does not follow a receding field) keeps the mitred offset.
        rng = random.Random(11)
        for index in range(300):
            start, target, points = _random_chain_case(rng, rng.choice((1, 1000, 250000)))
            chain = bus.west_chain(start, target, points)
            descent = (chain[-1][0], chain[-1][1] - rng.randint(1, 5) * MM)
            with self.subTest(case=index):
                self.assertEqual(bus.lane_offset(chain + [descent], BP), bus.mitred_offset(chain + [descent], BP))


# --------------------------------------------------------------------------
# Boxes and the mirror.
# --------------------------------------------------------------------------


def _area(box) -> int:
    return max(0, box[2] - box[0]) * max(0, box[3] - box[1])


def _overlap(one, two) -> int:
    return _area((max(one[0], two[0]), max(one[1], two[1]), min(one[2], two[2]), min(one[3], two[3])))


class BoxTests(unittest.TestCase):
    def test_grow_corners_clip_and_mirror(self) -> None:
        self.assertEqual(bus.grow((0, 1, 2, 3), 5), (-5, -4, 7, 8))
        self.assertEqual(bus.box_corners((0, 1, 2, 3)), [(0, 1), (2, 1), (0, 3), (2, 3)])
        self.assertEqual(bus.clip_y((0, 0, 5, 10), 2, 8), (0, 2, 5, 8))
        self.assertEqual(bus.clip_y((0, 0, 5, 10), 10, 20), (0, 10, 5, 10))  # a line counts
        self.assertIsNone(bus.clip_y((0, 0, 5, 10), 11, 20))
        self.assertEqual(bus.mirror([(1, 2), [3, -4]]), [(-1, 2), (-3, -4)])
        self.assertEqual(bus.mirror_box((1, 2, 5, 7)), (-5, 2, -1, 7))
        box = (-3, 2, 9, 11)
        self.assertEqual(bus.mirror_box(bus.mirror_box(box)), box)
        self.assertEqual(sorted(bus.mirror(bus.box_corners(box))), sorted(bus.box_corners(bus.mirror_box(box))))

    def test_subtract_hand_cases(self) -> None:
        box = (0, 0, 10, 10)
        self.assertEqual(bus.subtract(box, (10, 0, 20, 10)), [box])  # touching leaves the box whole
        self.assertEqual(bus.subtract(box, (3, 3, 6, 6)), [(0, 0, 10, 3), (0, 6, 10, 10), (0, 3, 3, 6), (6, 3, 10, 6)])
        self.assertEqual(bus.subtract(box, (-1, -1, 11, 11)), [])
        self.assertEqual(bus.subtract(box, (-5, 4, 5, 20)), [(0, 0, 10, 4), (5, 4, 10, 10)])

    def test_subtract_partitions_the_box_outside_the_hole(self) -> None:
        rng = random.Random(6)
        for index in range(3000):
            x0, y0 = rng.randint(-20, 20), rng.randint(-20, 20)
            box = (x0, y0, x0 + rng.randint(0, 20), y0 + rng.randint(0, 20))
            h0, k0 = rng.randint(-25, 25), rng.randint(-25, 25)
            hole = (h0, k0, h0 + rng.randint(0, 20), k0 + rng.randint(0, 20))
            parts = bus.subtract(box, hole)
            with self.subTest(case=index, box=box, hole=hole):
                for part in parts:
                    self.assertTrue(box[0] <= part[0] <= part[2] <= box[2] and box[1] <= part[1] <= part[3] <= box[3])
                    self.assertEqual(_overlap(part, hole), 0)
                for one in range(len(parts)):
                    for two in range(one + 1, len(parts)):
                        self.assertEqual(_overlap(parts[one], parts[two]), 0)
                total = 0
                for part in parts:
                    total += _area(part)
                self.assertEqual(total, _area(box) - _overlap(box, hole))


    def test_a_segment_enters_the_open_box_only(self) -> None:
        box = (0, 0, 10, 10)
        for a, b, enters in (
            ((-5, 5), (15, 5), True), ((-5, 0), (15, 0), False), ((5, 5), (5, 5), True), ((0, 0), (0, 10), False),
            ((-5, 15), (15, -5), True), ((-1, 9), (1, 11), False), ((-1, 9), (2, 11), True), ((10, 5), (20, 5), False),
            ((9, 5), (20, 5), True), ((5, 10), (5, 20), False), ((11, 0), (20, 5), False),
        ):
            with self.subTest(a=a, b=b):
                self.assertEqual(bus.segment_enters(a, b, box), enters)
                self.assertEqual(bus.segment_enters(b, a, box), enters)
        # Against a sampled test: a segment enters where one of its points lies strictly inside.
        rng = random.Random(7)
        for index in range(2000):
            a, b = (rng.randint(-15, 25), rng.randint(-15, 25)), (rng.randint(-15, 25), rng.randint(-15, 25))
            samples = [(a[0] * 400 + (b[0] - a[0]) * step, a[1] * 400 + (b[1] - a[1]) * step) for step in range(401)]
            sampled = any(0 < x < 4000 and 0 < y < 4000 for x, y in samples)
            if sampled:
                self.assertTrue(bus.segment_enters(a, b, box), (index, a, b))


# --------------------------------------------------------------------------
# Determinism.
# --------------------------------------------------------------------------

# The digest of the seeded corpus below: chains, offsets and keep-outs.  Measured on Python 3.9.6 and 3.12.12 (and
# the same with any hash seed); a deliberate change of the primitives updates it (diagonal-bus/4's cut at a lane's
# inward turn, lane_offset, changed the keep-outs of the chains continued by a corridor run or a jog inward).
CORPUS_DIGEST = "073d8bd27f82a741472be2e0bbfa638b06ba5b03b414f029a3443208cee98002"


def _corpus() -> list:
    rng = random.Random(2026)
    answer = []
    for _ in range(120):
        start, target, points = _random_chain_case(rng, rng.choice((1, 1000, 250000)))
        chain = bus.west_chain(start, target, points)
        follow = _follow(rng, chain)
        distance = rng.choice((BP, 254000, 400000))
        answer.append([chain, bus.mitred_offset(chain + [follow], distance), bus.lane_keepout(chain, follow, distance)])
    for _ in range(20):
        pitch, lanes = _onion(rng)
        answer.append([pitch, lanes])
    return answer


def _digest(value) -> str:
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode("ascii")).hexdigest()


class BusDeterminismTests(unittest.TestCase):
    def test_the_seeded_corpus_is_pinned(self) -> None:
        first = _corpus()
        self.assertEqual(_corpus(), first)
        self.assertTrue(all(type(value) is int for item in first for value in _integers(item)), "integer nanometres throughout")
        self.assertEqual(_digest(first), CORPUS_DIGEST)

    def test_the_bus_sums_no_floats_iterates_no_sets_and_calls_no_libm_but_sqrt(self) -> None:
        functions = [value for _, value in sorted(vars(bus).items()) if inspect.isfunction(value) and value.__module__ == bus.__name__]
        self.assertGreater(len(functions), 15)
        for function in functions:
            with self.subTest(function=function.__name__):
                self.assertEqual(_determinism_problems(function), [])
        tree = ast.parse((ROOT / "engine" / "bus.py").read_text(encoding="utf-8"))
        used = sorted({node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "math"})
        # hypot and atan2 may differ in the last bit between Python versions and platforms; sqrt is correctly rounded.
        self.assertEqual(used, ["ceil", "floor", "sqrt"])
        imports = sorted(alias.name for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom)) for alias in node.names)
        self.assertEqual(imports, ["Iterable", "NamedTuple", "Optional", "Sequence", "annotations", "math"], "stdlib only, no engine import")


def _integers(value):
    if isinstance(value, (list, tuple)):
        for item in value:
            yield from _integers(item)
    else:
        yield value


if __name__ == "__main__":
    unittest.main()
