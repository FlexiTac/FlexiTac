"""Border-model checks (web/cad/border.js): every pure function of the CAD border editor against exact values.

The script serves the app itself (``PYTHONPATH=. python3.12 -B app.py --port 18833`` from the project directory;
FPC_BORDER_PORT changes the port, never 8008, 18821 or 18880; ``--external`` uses an app already running there), imports
/static/cad/border.js into the page and checks:
- the module: its exports, no DOM, no import, no console error;
- createBorder / surfaceOutline: a rectangle outline with collinear points (4 corners), a clockwise outline (made
  counter-clockwise from the same first vertex), an L outline, server-shaped sides (their from_uv), a side list that
  is not a closed chain (the outline is used), a 2 nm sliver side merged (MERGE_MM) so every edge still moves; on the
  soft finger's and the crank's selections (asset/, skipped when absent) the sides' from_uv, counter-clockwise and
  valid;
- moveVertex: any quadrilateral; a crossing or a collapsed edge refused; an index out of range refused;
- moveEdge: a rectangle's edge moved out by 2 mm grows it; a trapezoid's edge keeps the neighbours' lines (exact
  ends); moves crossing the opposite edge, collapsing the edge, turning it round or making the polygon non-simple
  are refused; moveEdgeBy; at a soft corner (a 3.8-degree bend, a faceted arc's 7.5-degree step) the end moves
  square to the edge, and a 45-degree chamfer shorter than the move turns about its far end instead of turning round;
- insertVertex (on the edge, refused at its ends) and deleteVertex (back to the shape; a triangle and a crossing
  refused);
- inset: rectangle, L, a 3-4-5 triangle (homothety about the incentre), collapse refused, a chamfer dropped,
  outset;
- snap: onto an outline vertex and an outline edge, a dragged corner back to the rectangle, a parallelogram to a
  rectangle, options.indices, nothing to snap; snapEdge;
- outsideParts and overlapArea: a border beyond one side, beyond two sides (two runs), inside, disjoint (closed),
  across a hole; validate's messages;
- rankEdges, densify, surfacePath, uvToXyz / uvToXyzNearest / xyzToUv on a folded pair of facets (every vertex
  form, the scale, outside, extrapolation, a point off the plane), borderToXyz and borderHandles; on the asset
  meshes a round trip of every selected facet's points through the browser's parseStl positions, and the border
  traced on the part lying on the selected facets;
- History: push, undo, redo, a push after undo dropping the redo states, duplicates ignored, copies, the limit.

Then the editor in the app (web/cad/main.js, Chromium with SwiftShader for WebGL), driven with the mouse:
- the soft finger's contact face: after the selection the border is the outline, drawn on the part; the default
  exit edge is named under Auto (side 1, the longest); the candidate list is ranked by length (Auto first); a hovered
  row and the Base edge tool's hover highlight the edge (with its length); a click selects the visible side; Edit
  border shows the 8 handles; a corner drag gives any quadrilateral; an edge drag moves it parallel with its
  neighbours extended along their lines; an edge dragged beyond the surface (dashed there); Undo / Redo; Containment
  Field only forced and disabled with a border (no Board rules since P5-diagonal-bus.md section 26.16); the fit request carries the border and base
  auto, every previewed taxel lies inside the border and on the surface and the map's taxels_inside_border passes;
  the flat preview shows the border; a border edge chosen from the list is sent as {border_edge} and is the
  proposal's exit; Generate and the build's map (taxels_inside_border in the verification table); an edit after the
  fit makes the proposals stale; Surface outline; Inset (no Largest rectangle since section 26.16); a double click adds a
  corner, Delete and Ctrl+Z, a clicked corner and Delete corner; Done editing;
- a plate written here: on its bottom face seen from the iso view a click where the hidden back side projects
  (the old pick's side) selects nothing, near a corner the visible side wins over the hidden one projecting closer,
  the visible front side is selected; on its top face an outset border with a corner dragged in is fitted with every
  taxel on the plate and inside the border;
- a fin written here (a long plate with a faceted round tip and a 2 um sliver side, as a flattened fin gripper's
  face has): no border edge under MERGE_MM, overlapping handles at the tip not drawn, its longest edge dragged both
  ways by its diamond, dragged by its line, dragged with the Base edge tool on, and a click on the line picking it as
  the exit with the border unchanged.
Screenshots go to FPC_BORDER_SHOTS (default: fpc-browser-checks/border-shots in the system temp directory).
``--only model`` or ``--only ui`` runs one half.
Each check prints PASS/FAIL; the exit status is non-zero when one fails.
"""
from __future__ import annotations

import argparse
import base64
import json
import math
import os
import struct
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.dont_write_bytecode = True  # no __pycache__ next to the scripts
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PORT = int(os.environ.get("FPC_BORDER_PORT", "18833"))
if PORT in (8008, 18821, 18880):
    raise SystemExit(f"Port {PORT} is reserved for other servers; set FPC_BORDER_PORT to another port.")
os.environ["FPC_PORT"] = str(PORT)  # rp.py reads it at import
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))
from playwright.sync_api import sync_playwright  # noqa: E402

from rp import check, summary, unfold  # noqa: E402

URL = f"http://127.0.0.1:{PORT}/"
MODULE = "/static/cad/border.js"
ASSETS = Path(os.environ.get("FPC_ASSETS", str(ROOT / "asset")))
SOFT = ASSETS / "soft_gripper_finger.stl"
CRANK = ASSETS / "crank_gripper" / "tip_left.stl"
EXPORTS = {
    "MIN_AREA_MM2", "MIN_EDGE_MM", "SIDE_ANGLE_DEG", "RIGHT_ANGLE_DEG", "SOFT_CORNER_DEG", "MERGE_MM", "signedArea", "isSimple", "validate",
    "normalize", "surfaceOutline", "createBorder", "moveVertex", "moveEdge", "moveEdgeBy", "insertVertex",
    "deleteVertex", "inset", "snap", "snapEdge", "outsideParts", "overlapArea", "rankEdges",
    "densify", "surfacePath", "uvToXyz", "uvToXyzNearest", "xyzToUv", "borderToXyz", "borderHandles", "History",
}

RECT = [[0, 0], [20, 0], [20, 10], [0, 10]]
L_SHAPE = [[0, 0], [20, 0], [20, 10], [10, 10], [10, 30], [0, 30]]
TRAPEZOID = [[0, 0], [20, 0], [15, 10], [5, 10]]
NOTCH = [[0, 0], [40, 0], [40, 10], [25, 10], [20, 4], [15, 10], [0, 10]]


# --------------------------------------------------------------------------
# The server and the page
# --------------------------------------------------------------------------


def answers(timeout=1.0):
    try:
        with urllib.request.urlopen(URL, timeout=timeout) as response:
            return response.status == 200
    except (urllib.error.URLError, OSError):
        return False


def start_server():
    python = os.environ.get("FPC_SERVER_PYTHON", "python3.12")
    env = {**os.environ, "PYTHONPATH": "."}
    # --no-github: the checks' own server reads nothing from GitHub (the header's counts are ui_checks.py's).
    process = subprocess.Popen([python, "-B", "app.py", "--port", str(PORT), "--no-github"], cwd=ROOT, env=env,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    end = time.monotonic() + 30
    while time.monotonic() < end:
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout else ""
            raise SystemExit(f"app.py exited ({process.returncode}): {output.strip()}")
        if answers():
            return process
        time.sleep(0.1)
    process.terminate()
    raise SystemExit(f"app.py did not answer on port {PORT} within 30 s.")


def post_surface(route, header, mesh_bytes):
    encoded = json.dumps(header, separators=(",", ":")).encode()
    body = struct.pack(">I", len(encoded)) + encoded + mesh_bytes
    request = urllib.request.Request(f"{URL}api/surface/{route}", data=body, method="POST",
                                     headers={"Content-Type": "application/x-tactile-surface"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read())


class Page:
    """The app page with the module imported as window.__border."""

    def __init__(self, page):
        self.page = page

    def call(self, name, *args):
        return self.page.evaluate("([name, args]) => window.__border[name](...args)", [name, list(args)])

    def run(self, body, *args):
        """Evaluate `body`, a function (B, ...args) => value, with the module as B."""
        return self.page.evaluate(f"(args) => ({body})(window.__border, ...args)", list(args))


# --------------------------------------------------------------------------
# Python references
# --------------------------------------------------------------------------


def close(a, b, tol=1e-9):
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, (list, tuple)):
        return isinstance(b, (list, tuple)) and len(a) == len(b) and all(close(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, dict):
        return isinstance(b, dict) and a.keys() == b.keys() and all(close(a[k], b[k], tol) for k in a)
    if isinstance(a, bool) or isinstance(b, bool) or isinstance(a, str):
        return a == b
    return abs(a - b) <= tol


def line_distance(p, a, b):
    """The distance from p to the line through a and b."""
    return abs((b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])) / math.hypot(b[0] - a[0], b[1] - a[1])


def area(poly):
    return sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly))) / 2


def regular(count, radius=10.0, phase=0.0, center=(0.0, 0.0)):
    return [[center[0] + radius * math.cos(phase + 2 * math.pi * k / count), center[1] + radius * math.sin(phase + 2 * math.pi * k / count)]
            for k in range(count)]


def segment_distance(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    l2 = dx * dx + dy * dy
    t = 0.0 if l2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l2))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def in_rings(p, rings, tol=1e-7):
    """Inside the region (outline minus holes), the boundary within tol included."""
    for ring in rings:
        for k in range(len(ring)):
            if segment_distance(p, ring[k], ring[(k + 1) % len(ring)]) <= tol:
                return True
    odd = False
    for ring in rings:
        for k in range(len(ring)):
            a, b = ring[k], ring[(k + 1) % len(ring)]
            if (a[1] > p[1]) != (b[1] > p[1]) and p[0] < a[0] + (p[1] - a[1]) * (b[0] - a[0]) / (b[1] - a[1]):
                odd = not odd
    return odd


def triangle_distance3(p, a, b, c):
    """Distance from p to triangle abc in 3D (sampling-free: plane projection, else the nearest edge)."""
    def sub(u, v):
        return [u[i] - v[i] for i in range(3)]

    def dot(u, v):
        return sum(u[i] * v[i] for i in range(3))

    def crossp(u, v):
        return [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
    nrm = crossp(sub(b, a), sub(c, a))
    nl = math.sqrt(dot(nrm, nrm))
    if nl > 0:
        nrm = [x / nl for x in nrm]
        h = dot(sub(p, a), nrm)
        q = [p[i] - h * nrm[i] for i in range(3)]
        signs = [dot(crossp(sub(y, x), sub(q, x)), nrm) for x, y in ((a, b), (b, c), (c, a))]
        if all(s >= -1e-12 for s in signs):
            return abs(h)

    def seg(p, x, y):
        d = sub(y, x)
        l2 = dot(d, d)
        t = 0.0 if l2 == 0 else max(0.0, min(1.0, dot(sub(p, x), d) / l2))
        return math.sqrt(dot(sub(p, [x[i] + t * d[i] for i in range(3)]), sub(p, [x[i] + t * d[i] for i in range(3)])))
    return min(seg(p, a, b), seg(p, b, c), seg(p, c, a))


# --------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------


def module_checks(B, page):
    names = set(page.evaluate("() => Object.keys(window.__border)"))
    check("border: module exports", EXPORTS <= names, sorted(EXPORTS - names))
    source = (ROOT / "web" / "cad" / "border.js").read_text(encoding="utf-8")
    code = "\n".join(line for line in source.splitlines() if not line.lstrip().startswith(("//", "/*", "*")))
    banned = [word for word in ("document.", "window.", "import ", "require(", "fetch(", "localStorage") if word in code]
    check("border: pure module (no DOM, no import, no fetch)", not banned, banned)
    check("border: constants", B.run("B => [B.MIN_AREA_MM2, B.MIN_EDGE_MM, B.SIDE_ANGLE_DEG, B.RIGHT_ANGLE_DEG]") == [1, 0.001, 1, 3])
    check("border: the soft corner and merge constants", B.run("B => [B.SOFT_CORNER_DEG, B.MERGE_MM]") == [20, 0.01])


def create_checks(B):
    rectangle = [[0, 0], [5, 0], [10, 0], [20, 0], [20, 5], [20, 10], [10, 10], [0, 10], [0, 5]]
    check("createBorder: a rectangle outline with collinear points gives its 4 corners",
          B.call("createBorder", rectangle) == RECT, B.call("createBorder", rectangle))
    clockwise = [[0, 0], [0, 10], [20, 10], [20, 0]]
    check("createBorder: a clockwise outline runs counter-clockwise from the same vertex",
          B.call("createBorder", clockwise) == RECT, B.call("createBorder", clockwise))
    l_outline = [[0, 0], [10, 0], [20, 0], [20, 10], [15, 10], [10, 10], [10, 20], [10, 30], [0, 30], [0, 15]]
    check("createBorder: an L outline gives its 6 corners", B.call("createBorder", l_outline) == L_SHAPE, B.call("createBorder", l_outline))
    # Server-shaped sides: from the first corner, each side's from_uv/to_uv chained.
    sides = [{"index": k, "from_uv": L_SHAPE[k], "to_uv": L_SHAPE[(k + 1) % 6], "edges": [k]} for k in range(6)]
    rotated = sides[2:] + sides[:2]
    check("createBorder: server sides give their from_uv in order", B.call("createBorder", l_outline, rotated) == L_SHAPE[2:] + L_SHAPE[:2],
          B.call("createBorder", l_outline, rotated))
    broken = [side for side in sides if side["index"] != 3]
    check("createBorder: sides that are not a closed chain fall back to the outline", B.call("createBorder", l_outline, broken) == L_SHAPE)
    check("surfaceOutline: the reset equals the initial border", B.call("surfaceOutline", l_outline, rotated) == B.call("createBorder", l_outline, rotated))
    curve = regular(48, 10.0)
    check("createBorder: a polygonal disk keeps its 48 sides (each turns 7.5 degrees)", close(B.call("createBorder", curve), curve))
    gentle = [[20 * math.cos(math.radians(a / 10)), 20 * math.sin(math.radians(a / 10))] for a in range(0, 9, 2)] + [[0, 0]]
    created = B.call("createBorder", gentle)
    check("createBorder: segments within 1 degree of a side's first make one side (an arc of 0.8 degrees)",
          close(created, [gentle[0], gentle[-2], [0, 0]], 1e-12), created)
    # The server's own rule (surface/api.py boundary_sides) on outlines whose sides end by drift, not only at corners.
    from types import SimpleNamespace

    from surface.api import boundary_sides
    fillet = []
    for cx, cy, start in ((17, 3, -90), (17, 7, 0), (3, 7, 90), (3, 3, 180)):
        fillet += [[cx + 3 * math.cos(math.radians(start + 15 * k)), cy + 3 * math.sin(math.radians(start + 15 * k))] for k in range(7)]
    outlines = {
        "an arc of 4 degrees in 0.5-degree steps": [[20 * math.cos(math.radians(a / 2)), 20 * math.sin(math.radians(a / 2))] for a in range(9)] + [[0, 0]],
        "a rectangle with 3 mm fillets": fillet,
        "a wavy 200-gon": [[(30 + math.sin(5 * 2 * math.pi * k / 200)) * math.cos(2 * math.pi * k / 200),
                            (30 + math.sin(5 * 2 * math.pi * k / 200)) * math.sin(2 * math.pi * k / 200)] for k in range(200)],
    }
    for name, outline in outlines.items():
        chart = SimpleNamespace(loops=[list(range(len(outline)))], outer=0, uv={i: tuple(p) for i, p in enumerate(outline)})
        mesh = SimpleNamespace(vertices=[(p[0], p[1], 0.0) for p in outline])
        sides = boundary_sides(mesh, chart)
        starts = [side["from_uv"] for side in sides]
        from_outline = B.call("createBorder", outline)
        from_sides = B.call("createBorder", outline, sides)
        check(f"createBorder: {name}: the server's sides ({len(sides)}), from the outline alone and from the sides",
              close(from_outline, starts, 1e-6) and from_sides == starts, [len(from_outline or []), len(from_sides or [])])
    check("createBorder: no outline gives null", B.call("createBorder", [[0, 0], [1, 0]]) is None)
    # A flattened outline's sliver: a side 2 nm long (the fin gripper's face had one); kept, it left an edge every
    # edit had to keep above MIN_EDGE_MM, so almost every drag was refused.
    sliver = [[0, 0], [20, 0], [20, 10], [20, 10.000002], [0, 10.000002]]
    sliver_sides = [{"from_uv": sliver[k], "to_uv": sliver[(k + 1) % 5]} for k in range(5)]
    merged = B.call("createBorder", sliver, sliver_sides)
    check("createBorder: corners closer than MERGE_MM merge (a 2 nm sliver side), the first kept",
          merged == [[0, 0], [20, 0], [20, 10], [0, 10.000002]], merged)
    if merged:
        moves = [B.call("moveEdgeBy", merged, k, mm) is not None for k in range(4) for mm in (-2, 2)]
        check("createBorder: after the merge every edge moves 2 mm in and out", all(moves), moves)


def edit_checks(B):
    check("moveVertex: a corner dragged anywhere gives a free quadrilateral",
          B.call("moveVertex", RECT, 2, [26, 14]) == [[0, 0], [20, 0], [26, 14], [0, 10]])
    check("moveVertex: vertex 0 dragged outside", B.call("moveVertex", RECT, 0, [3, -4]) == [[3, -4], [20, 0], [20, 10], [0, 10]])
    check("moveVertex: a crossing (bow tie) is refused", B.call("moveVertex", RECT, 2, [-5, 5]) is None)
    check("moveVertex: onto its neighbour (a collapsed edge) is refused", B.call("moveVertex", RECT, 1, [20, 10]) is None)
    check("moveVertex: a polygon under 1 mm2 is refused", B.call("moveVertex", [[0, 0], [1, 0], [0, 1]], 1, [1.5, 0]) is None)
    check("moveVertex: an index out of range is refused", B.call("moveVertex", RECT, 4, [1, 1]) is None and B.call("moveVertex", RECT, -1, [1, 1]) is None)
    check("moveVertex: the argument is left unchanged", B.run("B => { const r = [[0,0],[20,0],[20,10],[0,10]]; B.moveVertex(r, 2, [26, 14]); return r; }") == RECT)

    grown = B.call("moveEdge", RECT, 1, [22, 5])
    check("moveEdge: a rectangle's edge moved out by 2 mm grows the rectangle", grown == [[0, 0], [22, 0], [22, 10], [0, 10]], grown)
    check("moveEdge: moved in by 3 mm (the cursor anywhere on the new line)", B.call("moveEdge", RECT, 2, [-50, 7]) == [[0, 0], [20, 0], [20, 7], [0, 7]])
    trapezoid = B.call("moveEdge", TRAPEZOID, 2, [10, 12])
    check("moveEdge: a trapezoid's top moved up keeps the neighbours' directions", close(trapezoid, [[0, 0], [20, 0], [14, 12], [6, 12]]), trapezoid)
    if trapezoid:
        directions = [(trapezoid[2][0] - trapezoid[1][0]) / (trapezoid[2][1] - trapezoid[1][1]), (trapezoid[3][0] - trapezoid[0][0]) / (trapezoid[3][1] - trapezoid[0][1])]
        check("moveEdge: the trapezoid's sides keep their slopes -0.5 and 0.5", close(directions, [-0.5, 0.5]), directions)
    bottom = B.call("moveEdge", TRAPEZOID, 0, [7, -4])
    check("moveEdge: a trapezoid's base moved down extends the sides", close(bottom, [[-2, -4], [22, -4], [15, 10], [5, 10]]), bottom)
    check("moveEdge: a rectangle's top moved below the bottom (crossing the opposite edge) is refused", B.call("moveEdge", RECT, 2, [10, -1]) is None)
    check("moveEdge: onto the opposite edge (no area) is refused", B.call("moveEdge", RECT, 2, [10, 0]) is None)
    check("moveEdge: the trapezoid's top to the sides' meeting point (a collapsed edge) is refused", B.call("moveEdge", TRAPEZOID, 2, [10, 20]) is None)
    check("moveEdge: beyond the meeting point (the edge turned round) is refused", B.call("moveEdge", TRAPEZOID, 2, [10, 25]) is None)
    check("moveEdge: the base swept over a notch's apex (not simple) is refused", B.call("moveEdge", NOTCH, 0, [10, 6]) is None)
    check("moveEdge: the base below the notch's apex is kept", close(B.call("moveEdge", NOTCH, 0, [10, 3]), [[0, 3], [40, 3]] + NOTCH[2:]))
    triangle = B.call("moveEdge", [[0, 0], [10, 0], [0, 10]], 1, [7, 7])
    check("moveEdge: a triangle's hypotenuse moved out scales it", close(triangle, [[0, 0], [14, 0], [0, 14]]), triangle)
    check("moveEdgeBy: 2 mm outward", B.call("moveEdgeBy", RECT, 0, 2) == [[0, -2], [20, -2], [20, 10], [0, 10]])
    check("moveEdgeBy: 4 mm inward", B.call("moveEdgeBy", RECT, 3, -4) == [[4, 0], [20, 0], [20, 10], [4, 10]])
    # Soft corners (under SOFT_CORNER_DEG): the end moves square to the edge, the neighbour turns about its far end.
    bent = [[0, 0], [60, 0], [60, 10], [30, 12], [0, 12]]
    raised = B.call("moveEdge", bent, 3, [10, 14])
    check("moveEdge: across a 3.8-degree bend the end moves square to the edge (the neighbour's line would meet the edge's far end)",
          raised == [[0, 0], [60, 0], [60, 10], [30, 14], [0, 14]], raised)
    fin = [[0, -10], [50, -10]] + [[50 + 10 * math.cos(math.radians(-90 + 7.5 * k)), 10 * math.sin(math.radians(-90 + 7.5 * k))] for k in range(1, 24)] + [[50, 10], [0, 10]]
    out = B.call("moveEdgeBy", fin, 0, 5)
    inward = B.call("moveEdgeBy", fin, 0, -5)
    check("moveEdgeBy: a long side beside a faceted arc (7.5-degree steps) moves 5 mm out and in, its arc end square to it",
          out is not None and inward is not None and close(out[:2], [[0, -15], [50, -15]]) and close(inward[:2], [[0, -5], [50, -5]])
          and close(out[2:], fin[2:]) and close(inward[2:], fin[2:]), (out and out[:3], inward and inward[:3]))
    chamfered = [[0, 0], [30, 0], [30, 20], [29, 21], [1, 21], [0, 20]]
    check("moveEdge: a 45-degree chamfer longer than the move is extended along its line",
          close(B.call("moveEdge", chamfered, 3, [15, 20.5]), [[0, 0], [30, 0], [30, 20], [29.5, 20.5], [0.5, 20.5], [0, 20]]))
    lowered = B.call("moveEdge", chamfered, 3, [15, 18])
    check("moveEdge: a chamfer shorter than the move (it would turn round) turns about its far end instead",
          lowered == [[0, 0], [30, 0], [30, 20], [29, 18], [1, 18], [0, 20]], lowered)

    inserted = B.call("insertVertex", RECT, 0, [5, 0.3])
    check("insertVertex: on edge 0 at the point nearest the cursor (vertex 1)", inserted == [[0, 0], [5, 0], [20, 0], [20, 10], [0, 10]], inserted)
    check("insertVertex: the last edge (wrapping to vertex 0)", B.call("insertVertex", RECT, 3, [-1, 4]) == [[0, 0], [20, 0], [20, 10], [0, 10], [0, 4]])
    check("insertVertex: {onEdge: false} inserts the point itself", B.call("insertVertex", RECT, 0, [10, -3], {"onEdge": False}) == [[0, 0], [10, -3], [20, 0], [20, 10], [0, 10]])
    check("insertVertex: at an end of the edge is refused", B.call("insertVertex", RECT, 0, [0.0001, 0]) is None and B.call("insertVertex", RECT, 0, [25, 0]) is None)
    check("deleteVertex: removing the inserted vertex restores the rectangle", B.call("deleteVertex", inserted, 1) == RECT)
    check("deleteVertex: the L's inner corner", B.call("deleteVertex", L_SHAPE, 3) == [[0, 0], [20, 0], [20, 10], [10, 30], [0, 30]])
    house = [[0, 0], [20, 0], [20, 10], [10, 15], [0, 10]]
    check("deleteVertex: vertex 0 (the closing edge joins the last vertex to vertex 1)", B.call("deleteVertex", house, 0) == house[1:])
    check("deleteVertex: the L's vertex 0 (the new edge crosses the inner corner) is refused", B.call("deleteVertex", L_SHAPE, 0) is None)
    check("deleteVertex: a triangle keeps 3 vertices (refused)", B.call("deleteVertex", [[0, 0], [4, 0], [0, 3]], 1) is None)
    deep = [[0, 0], [40, 0], [40, 10], [25, 10], [20, 2], [15, 10], [0, 10]]
    check("deleteVertex: a new edge crossing the notch is refused", B.call("deleteVertex", deep, 1) is None)


def inset_checks(B):
    check("inset: a rectangle by 1 mm", B.call("inset", RECT, 1) == [[1, 1], [19, 1], [19, 9], [1, 9]])
    check("inset: an L by 1 mm", B.call("inset", L_SHAPE, 1) == [[1, 1], [19, 1], [19, 9], [9, 9], [9, 29], [1, 29]])
    result = B.call("inset", [[0, 0], [4, 0], [0, 3]], 0.5)
    check("inset: a 3-4-5 triangle by half its inradius (homothety 1/2 about the incentre (1, 1))",
          close(result, [[0.5, 0.5], [2.5, 0.5], [0.5, 2.0]], 1e-12), result)
    check("inset: by the inradius (nothing left) is refused", B.call("inset", [[0, 0], [4, 0], [0, 3]], 1) is None)
    check("inset: a rectangle by half its height is refused", B.call("inset", RECT, 5) is None)
    result = B.call("inset", [[0, 0], [20, 0], [20, 9], [19, 10], [0, 10]], 3)
    check("inset: a 1 mm chamfer under a 3 mm inset is dropped", close(result, [[3, 3], [17, 3], [17, 7], [3, 7]], 1e-12), result)
    check("inset: negative is an outset", B.call("inset", RECT, -1) == [[-1, -1], [21, -1], [21, 11], [-1, 11]])
    check("inset: 0 keeps the border", B.call("inset", L_SHAPE, 0) == L_SHAPE)


def snap_checks(B):
    check("snap: a corner within 0.5 mm of an outline vertex goes onto it",
          B.call("snap", [[0.3, -0.2], [20, 0], [20, 10], [0, 10]], RECT, 0.5) == RECT)
    check("snap: vertices within 0.5 mm of an outline edge go onto it",
          B.call("snap", [[2, 0.3], [18, 0.3], [18, 8], [2, 8]], RECT, 0.5) == [[2, 0], [18, 0], [18, 8], [2, 8]])
    check("snap: a dragged corner returns to the rectangle (right angles at its neighbours)",
          B.call("snap", [[0, 0], [20, 0], [20.3, 10.2], [0, 10]], None, 0.5) == RECT)
    result = B.call("snap", [[0, 0], [20, 0], [20.35, 10], [0.35, 10]], None, 0.5)
    check("snap: a parallelogram (88/92 degrees) becomes a rectangle",
          close(result, [[0.35, 0.68775], [20.35, 0.68775], [20.35, 10], [0.35, 10]], 1e-9), result)
    result = B.call("snap", [[0, 0], [20, 0], [20.3, 10.2], [0.2, 10.1]], None, 0.5, {"indices": [2]})
    check("snap: options.indices moves only vertex 2 (right angles at vertices 1 and 3)",
          close(result, [[0, 0], [20, 0], [20, 10.1 - 0.2 * 19.8 / 10.1], [0.2, 10.1]], 1e-12), result)
    check("snap: angles beyond the tolerance stay", B.call("snap", [[0, 0], [20, 0], [21, 10], [0, 10]], None, 0.5) == [[0, 0], [20, 0], [21, 10], [0, 10]])
    # 84.3 degrees at vertices 1 and 2: equal scores, so the lower index moves (onto x = 21, y = 0).
    check("snap: options.angleDeg widens it (equal scores: the lower index moves)",
          B.call("snap", [[0, 0], [20, 0], [21, 10], [0, 10]], None, 0.5, {"angleDeg": 6}) == [[0, 0], [21, 0], [21, 10], [0, 10]])
    check("snap: options.indices picks the dragged corner instead",
          B.call("snap", [[0, 0], [20, 0], [21, 10], [0, 10]], None, 0.5, {"angleDeg": 6, "indices": [2]}) == RECT)
    check("snap: angleDeg 0 turns the right angles off",
          B.call("snap", [[0, 0], [20, 0], [20.3, 10.2], [0, 10]], None, 0.5, {"angleDeg": 0}) == [[0, 0], [20, 0], [20.3, 10.2], [0, 10]])
    equilateral = [[0, 0], [10, 0], [5, 8.660254037844386]]
    check("snap: nothing near (an equilateral triangle far from the outline) is unchanged", B.call("snap", equilateral, [[50, 50], [60, 50], [60, 60]], 0.5) == equilateral)
    check("snap: an outline vertex wins over an edge point", B.call("snap", [[19.7, 0.2], [30, 0], [30, 10]], RECT, 0.5) == [[20, 0], [30, 0], [30, 10]])
    result = B.call("snapEdge", [[0, 0], [19.6, 0], [19.6, 10], [0, 10]], 1, RECT, 0.5)
    check("snapEdge: an edge 0.4 mm from the outline's parallel side goes onto it", close(result, RECT), result)
    check("snapEdge: out of reach the border is unchanged", B.call("snapEdge", [[0, 0], [18, 0], [18, 10], [0, 10]], 1, RECT, 0.5) == [[0, 0], [18, 0], [18, 10], [0, 10]])


def surface_checks(B):
    beyond = [[0, 0], [30, 0], [30, 10], [0, 10]]
    result = B.call("outsideParts", beyond, RECT)
    check("outsideParts: a border 10 mm beyond one side gives that part", close(result, [[[20, 0], [30, 0], [30, 10], [20, 10]]], 1e-12), result)
    across = [[-5, 2], [25, 2], [25, 8], [-5, 8]]
    result = B.call("outsideParts", across, RECT)
    check("outsideParts: beyond two sides gives two runs in the border's order",
          close(result, [[[20, 2], [25, 2], [25, 8], [20, 8]], [[0, 8], [-5, 8], [-5, 2], [0, 2]]], 1e-12), result)
    check("outsideParts: a border inside (and one on the outline) gives none",
          B.call("outsideParts", [[1, 1], [2, 1], [2, 2]], RECT) == [] and B.call("outsideParts", RECT, RECT) == [])
    check("outsideParts: a disjoint border is one closed run",
          B.call("outsideParts", [[30, 0], [40, 0], [40, 5]], RECT) == [[[30, 0], [40, 0], [40, 5], [30, 0]]])
    hole = [[8, 4], [12, 4], [12, 0], [8, 0]]
    check("outsideParts: the part across a hole counts as beyond the surface",
          close(B.call("outsideParts", [[2, 2], [18, 2], [18, 8], [2, 8]], RECT, [hole]), [[[8, 2], [12, 2]]], 1e-12))
    check("overlapArea: 200 of the 300 mm2 border", B.call("overlapArea", beyond, RECT) == 200)
    check("overlapArea: 120 across two sides, 112 with a 4 x 2 hole",
          close([B.call("overlapArea", across, RECT), B.call("overlapArea", across, RECT, [[[8, 4], [12, 4], [12, 6], [8, 6]]])], [120, 112], 1e-9))
    # The square |u - 10| + |v - 5| <= 10 (200 mm2) loses a 10 x 5 triangle below v = 0 and one above v = 10.
    tilted = B.call("overlapArea", [[10, -5], [20, 5], [10, 15], [0, 5]], RECT)
    check("overlapArea: a tilted square over the rectangle (exact, by slabs)", close(tilted, 150, 1e-9), tilted)
    check("overlapArea: a tilted square covering the rectangle", B.call("overlapArea", [[10, -10], [30, 10], [10, 30], [-10, 10]], RECT) == 200)
    check("overlapArea: disjoint is 0", B.call("overlapArea", [[30, 0], [40, 0], [40, 5]], RECT) == 0)
    messages = [B.call("validate", border, *rest)["message"] for border, *rest in (
        ([[0, 0], [10, 0], [0, 10], [10, 10]],), ([[0, 0], [1, 0]],), ([[0, 0], [0.5, 0], [0, 0.5]],),
        ([[0, 0], [0, 10], [10, 0]],), ([[30, 0], [40, 0], [40, 5]], RECT))]
    check("validate: not simple, fewer than 3 vertices, under 1 mm2, clockwise, no overlap", messages == [
        "The border is not a simple polygon: its edges cross or touch.", "The border needs at least 3 vertices.",
        "The border's area is under 1 mm².", "The border runs clockwise; it must run counter-clockwise.",
        "The border does not overlap the surface."], messages)
    check("validate: a border partly beyond the surface is valid", B.call("validate", beyond, RECT) == {"ok": True, "message": ""})
    check("isSimple / signedArea / normalize",
          B.call("isSimple", RECT) and not B.call("isSimple", [[0, 0], [10, 0], [0, 10], [10, 10]]) and B.call("signedArea", RECT) == 200
          and B.call("normalize", [[0, 0], [0, 10], [20, 10], [20, 0], [0, 0]]) == RECT)


def misc_checks(B):
    check("rankEdges: longest first, ties by index", B.call("rankEdges", RECT) == [
        {"index": 0, "length": 20}, {"index": 2, "length": 20}, {"index": 1, "length": 10}, {"index": 3, "length": 10}])
    ranked = B.call("rankEdges", TRAPEZOID)
    check("rankEdges: a trapezoid", close(ranked, [{"index": 0, "length": 20}, {"index": 1, "length": math.hypot(5, 10)},
                                                   {"index": 3, "length": math.hypot(5, 10)}, {"index": 2, "length": 10}], 1e-12), ranked)
    check("densify: no segment longer than the step", B.call("densify", [[0, 0], [10, 0]], 3) == [[0, 0], [2.5, 0], [5, 0], [7.5, 0], [10, 0]])
    closed = B.call("densify", [[0, 0], [4, 0], [4, 2]], 2, True)
    check("densify: a closed polyline returns to its start (not repeated)", close(closed, [[0, 0], [2, 0], [4, 0], [4, 2], [8 / 3, 4 / 3], [4 / 3, 2 / 3]], 1e-12), closed)

    history = B.run("""B => {
        const h = new B.History([[0, 0], [20, 0], [20, 10], [0, 10]], {limit: 3});
        const out = {start: [h.size, h.canUndo, h.canRedo]};
        out.duplicate = h.push([[0, 0], [20, 0], [20, 10], [0, 10]]);
        h.push([[0, 0], [22, 0], [22, 10], [0, 10]]);
        h.push([[0, 0], [24, 0], [24, 10], [0, 10]]);
        out.undo1 = h.undo(); out.undo2 = h.undo(); out.undo3 = h.undo();
        out.redo1 = h.redo();
        const copyOf = h.current; copyOf[0][0] = 99; out.current = h.current;
        h.push([[0, 0], [30, 0], [30, 10], [0, 10]]);
        out.afterPush = [h.size, h.canRedo, h.redo()];
        h.push([[1, 1], [30, 0], [30, 10], [0, 10]]); h.push([[2, 2], [30, 0], [30, 10], [0, 10]]);
        out.limited = [h.size, h.undo(), h.undo(), h.undo()];
        h.reset([[5, 5], [6, 5], [6, 6]]);
        out.reset = [h.size, h.current, h.canUndo];
        return out;
    }""")
    check("History: the initial state, nothing to undo or redo", history["start"] == [1, False, False])
    check("History: a push equal to the current state is ignored", history["duplicate"] is False)
    check("History: undo steps back, then null at the start",
          history["undo1"] == [[0, 0], [22, 0], [22, 10], [0, 10]] and history["undo2"] == RECT and history["undo3"] is None, history)
    check("History: redo steps forward; the states returned are copies",
          history["redo1"] == [[0, 0], [22, 0], [22, 10], [0, 10]] and history["current"] == [[0, 0], [22, 0], [22, 10], [0, 10]])
    check("History: a push after undo drops the redo states", history["afterPush"] == [3, False, None], history["afterPush"])
    check("History: at most `limit` states (the oldest dropped)",
          history["limited"] == [3, [[1, 1], [30, 0], [30, 10], [0, 10]], [[0, 0], [30, 0], [30, 10], [0, 10]], None], history["limited"])
    check("History: reset", history["reset"] == [1, [[5, 5], [6, 5], [6, 6]], False])
    branch = B.run("""B => {
        const h = new B.History('A');
        h.push('B'); h.push('C');
        const steps = [h.undo()];
        h.push('D');
        steps.push(h.size, h.undo(), h.undo(), h.undo(), h.redo(), h.redo(), h.redo());
        return steps;
    }""")
    check("History: after undo, a new state replaces the undone ones (A B D, never C)",
          branch == ["B", 3, "B", "A", None, "B", "D", None], branch)


def mapping_checks(B):
    # Two facets folded 90 degrees about the diagonal of the uv square [0, 10]^2 (mesh facets 7 and 3).
    h = 5 * math.sqrt(2)
    facets = [7, 3]
    facets_uv = [[[0, 0], [10, 0], [10, 10]], [[0, 0], [10, 10], [0, 10]]]
    by_id = [None] * 8
    by_id[7] = [[0, 0, 0], [10, 0, 0], [10, 10, 0]]
    by_id[3] = [[0, 0, 0], [10, 10, 0], [5, 5, h]]
    flat_cm = [0.0] * 72
    for facet in facets:
        for k, value in enumerate(c for corner in by_id[facet] for c in corner):
            flat_cm[9 * facet + k] = value / 10
    forms = B.run("""(B, uv, facetsUv, facets, byId, flat) => {
        const f32 = new Float32Array(flat);
        return [B.uvToXyz(uv, facetsUv, facets, byId), B.uvToXyz(uv, facetsUv, facets, flat, 10),
                B.uvToXyz(uv, facetsUv, facets, f32, 10), B.uvToXyz(uv, facetsUv, facets, {positions: f32, scale: 10}),
                B.uvToXyz(uv, facetsUv, facets, id => byId[id])];
    }""", [2, 6], facets_uv, facets, by_id, flat_cm)
    expected = [4, 4, 2 * math.sqrt(2)]
    check("uvToXyz: barycentric on the folded facet, every vertex form (triples, positions x scale, Float32, {positions, scale}, function)",
          close(forms[0], expected, 1e-12) and close(forms[1], expected, 1e-12) and close(forms[4], expected, 1e-12)
          and close(forms[2], expected, 1e-6) and close(forms[3], expected, 1e-6), forms)
    check("uvToXyz: on the flat facet", B.call("uvToXyz", [6, 2], facets_uv, facets, by_id) == [6, 2, 0])
    check("uvToXyz: on the fold (shared edge)", B.call("uvToXyz", [5, 5], facets_uv, facets, by_id) == [5, 5, 0])
    check("uvToXyz: a vertex", close(B.call("uvToXyz", [0, 10], facets_uv, facets, by_id), [5, 5, h], 1e-12))
    check("uvToXyz: outside every facet is null", B.call("uvToXyz", [12, 5], facets_uv, facets, by_id) is None
          and B.call("uvToXyz", [-0.001, 5], facets_uv, facets, by_id) is None)
    near = B.call("uvToXyzNearest", [12, 5], facets_uv, facets, by_id)
    check("uvToXyzNearest: beyond the surface, on the nearest facet's plane", near == {"xyz": [12, 5, 0], "facet": 7, "inside": False}, near)
    # (-2, 6) is 2 mm beyond the folded facet (u = 0) and 5.7 mm from the flat one: in the folded facet's
    # weights (0,0) 0.4, (10,10) -0.2, (0,10) 0.8, so on its plane at (-2 + 4, -2 + 4, 0.8 h).
    near = B.call("uvToXyzNearest", [-2, 6], facets_uv, facets, by_id)
    expected_far = [2.0, 2.0, 0.8 * h]
    check("uvToXyzNearest: beyond the folded facet, extrapolated on its plane (its affine map)",
          near is not None and near["facet"] == 3 and near["inside"] is False and close(near["xyz"], expected_far, 1e-12), [near, expected_far])
    check("xyzToUv: round trips on both facets",
          B.call("xyzToUv", [6, 2, 0], 7, facets_uv, facets, by_id) == [6, 2]
          and close(B.call("xyzToUv", [4, 4, 2 * math.sqrt(2)], 3, facets_uv, facets, by_id), [2, 6], 1e-12))
    check("xyzToUv: a point off the plane is projected onto it", B.call("xyzToUv", [6, 2, 0.5], 7, facets_uv, facets, by_id) == [6, 2])
    check("xyzToUv: facet null (beyond the surface) uses the nearest facet", B.call("xyzToUv", [12, 5, 0], None, facets_uv, facets, by_id) == [12, 5])
    # 0.14 mm off the folded facet's plane (2.8 mm above the flat one): projected onto the folded facet.
    off = B.call("xyzToUv", [4.1, 3.9, 2 * math.sqrt(2)], 99, facets_uv, facets, by_id)
    check("xyzToUv: a facet outside the selection uses the nearest facet", close(off, [2, 6], 1e-12), off)
    far = B.call("xyzToUv", expected_far, None, facets_uv, facets, by_id)
    check("xyzToUv: the inverse of uvToXyzNearest beyond the surface", close(far, [-2, 6], 1e-12), far)
    trips = B.run("""(B, facetsUv, facets, byId) => {
        const out = [];
        for (const [k, w] of [[0, [0.2, 0.3, 0.5]], [1, [0.6, 0.3, 0.1]], [1, [0.05, 0.05, 0.9]], [0, [1, 0, 0]]]) {
            const tri = facetsUv[k];
            const uv = [0, 1].map(axis => w[0] * tri[0][axis] + w[1] * tri[1][axis] + w[2] * tri[2][axis]);
            const xyz = B.uvToXyz(uv, facetsUv, facets, byId);
            out.push([uv, B.xyzToUv(xyz, facets[k], facetsUv, facets, byId)]);
        }
        return out;
    }""", facets_uv, facets, by_id)
    check("uvToXyz -> xyzToUv: round trips at barycentric points", all(close(a, b_, 1e-12) for a, b_ in trips), trips)

    path = B.call("surfacePath", [[2, 1], [8, 1], [8, 4], [2, 7]], facets_uv, 100, True)
    check("surfacePath: a point where the border crosses the fold (and where it returns)",
          close(path, [[2, 1], [8, 1], [8, 4], [16 / 3, 16 / 3], [2, 7], [2, 2]], 1e-12), path)
    traced = B.call("borderToXyz", [[2, 1], [8, 1], [8, 4], [2, 7]], facets_uv, facets, by_id, {"stepMm": 100})
    check("borderToXyz: the loop follows both facets (z = 0 on the fold)", close(traced["loop"], [
        [2, 1, 0], [8, 1, 0], [8, 4, 0], [16 / 3, 16 / 3, 0], [4.5, 4.5, 0.5 * h], [2, 2, 0]], 1e-12) and traced["outsideRuns"] == [], traced)
    traced = B.call("borderToXyz", [[6, 1], [14, 1], [14, 4], [6, 4]], facets_uv, facets, by_id, {"stepMm": 2, "outlineUv": [[0, 0], [10, 0], [10, 10], [0, 10]]})
    check("borderToXyz: the part beyond the surface as an outside run on the plane", close(traced["outsideRuns"], [[
        [10, 1, 0], [12, 1, 0], [14, 1, 0], [14, 2.5, 0], [14, 4, 0], [12, 4, 0], [10, 4, 0]]], 1e-12), traced["outsideRuns"])
    handles = B.call("borderHandles", [[1, 1], [9, 1], [9, 5]], facets_uv, facets, by_id)
    check("borderHandles: a vertex handle per vertex and an edge handle per edge middle", handles == [
        {"kind": "vertex", "index": 0, "uv": [1, 1], "xyz": [1, 1, 0]}, {"kind": "vertex", "index": 1, "uv": [9, 1], "xyz": [9, 1, 0]},
        {"kind": "vertex", "index": 2, "uv": [9, 5], "xyz": [9, 5, 0]}, {"kind": "edge", "index": 0, "uv": [5, 1], "xyz": [5, 1, 0]},
        {"kind": "edge", "index": 1, "uv": [9, 3], "xyz": [9, 3, 0]}, {"kind": "edge", "index": 2, "uv": [5, 3], "xyz": [5, 3, 0]}], handles)


def asset_selections():
    """The selection replies (and facets' uv) of the example meshes' first Surface candidate; {} without asset/."""
    found = {}
    for name, path in (("soft finger", SOFT), ("crank", CRANK)):
        if not path.is_file():
            print(f"SKIP {name}: {path} is absent")
            continue
        data = path.read_bytes()
        inspect = post_surface("inspect", {}, data)
        candidate = inspect["candidates"]["surface"][0]
        ops = [{"op": "grow", "mode": "add", "seed_facet": candidate["seed_facet"], "preset": "surface"}]
        selection = post_surface("select", {"selection": {"ops": ops}}, data)["selection"]
        # The facets' uv (selection.facets_uv once the server sends it): the chart's uv of each facet's vertices.
        from surface import api as surface_api
        from surface.mesh import read_stl
        mesh = read_stl(data)
        facets, chart = surface_api.selection_chart(mesh, {"ops": ops})
        ids = sorted(facets)
        facets_uv = [[list(chart.uv[v]) for v in mesh.facets[f]] for f in ids]
        if "facets_uv" in selection:
            check(f"facets_uv: the {name}'s reply matches the chart", close(selection["facets_uv"], facets_uv, 2e-6))
        found[name] = {**selection, "facets_uv": facets_uv, "ids": ids, "bytes": data, "scale": inspect["mesh"]["scale_to_mm"],
                       "centroids": [list(mesh.centroids[f]) for f in ids], "corners": [[list(p) for p in mesh.facet_points(f)] for f in ids]}
    return found


def asset_checks(B, page, assets):
    for name, selection in assets.items():
        sides = selection["sides"]
        border = B.call("createBorder", selection["outline_uv"], sides)
        check(f"createBorder: the {name}'s border is its sides' from_uv ({len(sides)} sides)",
              border == [side["from_uv"] for side in sides] and area(border) > 0 and B.call("validate", border, selection["outline_uv"], selection["holes_uv"])["ok"],
              border)
        if name == "soft finger":
            check("createBorder: the soft finger's face has 4 sides", len(border) == 4)
        # The browser's own positions (parseStl, file units) times the mesh's scale_to_mm.
        result = page.evaluate("""async ([b64, facetsUv, ids, scale]) => {
            const {parseStl} = await import('/static/cad/stl.js');
            const bytes = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
            const {positions} = parseStl(bytes.buffer);
            const B = window.__border;
            const out = {forward: [], back: [], inner: []};
            facetsUv.forEach((tri, k) => {
                for (const w of [[1 / 3, 1 / 3, 1 / 3], [0.6, 0.3, 0.1], [0.1, 0.1, 0.8]]) {
                    const uv = [0, 1].map(axis => w[0] * tri[0][axis] + w[1] * tri[1][axis] + w[2] * tri[2][axis]);
                    const xyz = B.uvToXyz(uv, facetsUv, ids, positions, scale);
                    const back = xyz && B.xyzToUv(xyz, ids[k], facetsUv, ids, positions, scale);
                    out.forward.push([k, w, xyz]);
                    out.back.push([uv, back]);
                }
            });
            return out;
        }""", [base64.b64encode(selection["bytes"]).decode(), selection["facets_uv"], selection["ids"], selection["scale"]])
        worst_xyz = 0.0
        for k, w, xyz in result["forward"]:
            corners = selection["corners"][k]
            want = [w[0] * corners[0][i] + w[1] * corners[1][i] + w[2] * corners[2][i] for i in range(3)]
            worst_xyz = max(worst_xyz, max(abs(xyz[i] - want[i]) for i in range(3)) if xyz else math.inf)
        worst_uv = max((max(abs(a - b) for a, b in zip(uv, back)) if back else math.inf) for uv, back in result["back"])
        check(f"uvToXyz/xyzToUv: the {name}'s {len(selection['ids'])} facets round trip through parseStl's positions",
              worst_xyz <= 1e-4 and worst_uv <= 1e-4, f"xyz {worst_xyz:.2e} mm, uv {worst_uv:.2e} mm")
        inner = B.call("inset", border, 2)
        traced = page.evaluate("""async ([b64, border, facetsUv, ids, scale, outline]) => {
            const {parseStl} = await import('/static/cad/stl.js');
            const bytes = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
            const {positions} = parseStl(bytes.buffer);
            return window.__border.borderToXyz(border, facetsUv, ids, positions, {scale, stepMm: 2, outlineUv: outline});
        }""", [base64.b64encode(selection["bytes"]).decode(), inner, selection["facets_uv"], selection["ids"], selection["scale"], selection["outline_uv"]])
        worst = 0.0
        for point in traced["loop"]:
            worst = max(worst, min(triangle_distance3(point, *corners) for corners in selection["corners"]))
        check(f"borderToXyz: the {name}'s border inset by 2 mm lies on the selected facets ({len(traced['loop'])} points)",
              inner is not None and worst <= 1e-4 and traced["outsideRuns"] == [], f"{worst:.2e} mm")


# --------------------------------------------------------------------------
# The editor in the app (web/cad/main.js): UI flows with WebGL (SwiftShader)
# --------------------------------------------------------------------------

WEBGL_ARGS = ["--enable-unsafe-swiftshader", "--use-angle=swiftshader"]
SHOTS = Path(os.environ.get("FPC_BORDER_SHOTS", str(Path(tempfile.gettempdir()) / "fpc-browser-checks" / "border-shots")))
STATE = "() => JSON.parse(document.getElementById('cadState').textContent)"
IDLE = "() => JSON.parse(document.getElementById('cadState').textContent).busy.length === 0"


def wait_until(page, expression, timeout=60.0, arg=None):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if page.evaluate(expression) if arg is None else page.evaluate(expression, arg):
            return True
        page.wait_for_timeout(40)
    raise TimeoutError(expression)


# The fit requests' JSON headers, read from the framed Blob body (Playwright does not see a Blob's bytes): the test
# page's fetch records them in window.__fitHeaders (the app's code never patches fetch).
RECORD_FITS = """(() => {
  const original = window.fetch;
  window.__fitHeaders = [];
  window.fetch = function (url, init) {
    if (String(url).endsWith('/api/surface/fit') && init && init.body instanceof Blob) {
      const body = init.body;
      body.slice(0, 4).arrayBuffer().then(buffer => body.slice(4, 4 + new DataView(buffer).getUint32(0, false)).text())
        .then(text => window.__fitHeaders.push(JSON.parse(text)));
    }
    return original.apply(this, arguments);
  };
})();"""


def fit_header(page):
    """The JSON header of the last fit request."""
    wait_until(page, "() => window.__fitHeaders.length > 0", 10)
    return page.evaluate("() => window.__fitHeaders[window.__fitHeaders.length - 1]")


def ui_page(browser, width=1440, height=900):
    """A page that records the console, the fit requests' headers and the map replies."""
    page = browser.new_page(viewport={"width": width, "height": height})
    page.logs = []
    page.maps = []
    # Without CAD mode's default part (the checks were written before it): its request answered 404, its console line dropped.
    page.route(DEFAULT_PART, lambda route: route.fulfill(status=404, content_type="text/plain", body="not in this check"))
    page.on("console", lambda m: None if (m.location or {}).get("url", "").endswith(DEFAULT_PART_PATH) else page.logs.append((m.type, m.text)))
    page.on("pageerror", lambda e: page.logs.append(("pageerror", str(e))))
    page.add_init_script(RECORD_FITS)
    unfold(page)

    def on_response(response):
        if response.url.endswith("/api/surface/map") and response.status == 200:
            try:
                page.maps.append(response.json())
            except Exception as error:  # noqa: BLE001 - diagnostics only
                page.maps.append({"error": str(error)})
    page.on("response", on_response)
    page.goto(URL + "#cad")
    wait_until(page, "() => document.getElementById('cadState') && JSON.parse(document.getElementById('cadState').textContent).webgl !== 'not loaded'")
    # Without the default part (refused above), then Max rows / columns at 64 as a user sets them (the checks were written
    # before the user's default of 32).
    wait_until(page, """() => { const s = JSON.parse(document.getElementById('cadState').textContent);
        return s.default_part === 'failed' && s.busy.length === 0 && s.limits_served !== null; }""")
    page.evaluate("""() => ['cadMaxRows', 'cadMaxColumns'].forEach(id => { const c = document.getElementById(id);
        c.value = '64'; c.dispatchEvent(new Event('input', {bubbles: true})); })""")
    return page


DEFAULT_PART_PATH = "/static/vendor/umi/UMI-Soft-Gripper-Finger.stl"
DEFAULT_PART = "**" + DEFAULT_PART_PATH


def ui_state(page):
    return page.evaluate(STATE)


def ui_pick(page, seed, preset="flat"):
    # A click on the surface of a seed facet, through the diagnostics input (main.js pickSurface; the page lists no
    # candidates since 2026-10-30, and a pick adds to the selection, a pick of a selected one removes it).
    page.evaluate("""([seed, preset]) => { const input = document.getElementById('cadPick'); input.value = `${seed}:${preset}`;
        input.dispatchEvent(new Event('change', {bubbles: true})); }""", [seed, preset])


def settle(page, timeout=180):
    page.wait_for_timeout(60)
    wait_until(page, IDLE, timeout)
    page.wait_for_timeout(60)


def ui_load(page, path):
    # Loaded once the state names the file (the default part may be the mesh until then).
    page.set_input_files("#cadFile", str(path))
    wait_until(page, "(name) => { const s = JSON.parse(document.getElementById('cadState').textContent); return s.mesh !== null && s.mesh.name === name && s.busy.length === 0; }",
               arg=Path(path).name)
    page.wait_for_timeout(150)


def view_in_sight(page):
    """The 3D view scrolled to the window's middle when part of it is out of the window (the 1280 x 720 page holds it
    below the file and the workspace's header since 2026-10-30), as a user would scroll before clicking on the part."""
    if page.evaluate("() => { const r = document.getElementById('cadView').getBoundingClientRect(); return r.top < 0 || r.bottom > innerHeight; }"):
        page.evaluate("() => document.getElementById('cadView').scrollIntoView({block: 'center'})")
        page.wait_for_timeout(150)


def probe(page, point):
    """The screen position (client px) of an STL point (mm), by the diagnostics probe, the view in sight first."""
    view_in_sight(page)
    text = page.evaluate("""text => { const input = document.getElementById('cadProbe'); input.value = text;
        input.dispatchEvent(new Event('input', {bubbles: true})); return document.getElementById('cadProbeOut').textContent; }""",
                         ", ".join(f"{value:.6f}" for value in point))
    return [float(value) for value in text.split(",")] if text else None


def handle_at(page, kind, index):
    """The screen position of a border handle, when it lies in the 3D view (else None)."""
    view_in_sight(page)  # before the view's box is taken (probe would scroll it later)
    box = page.locator("#cadView").bounding_box()
    for handle in ui_state(page)["border"]["handles"] or []:
        if handle["kind"] == kind and handle["index"] == index:
            at = probe(page, handle["xyz"])
            inside = at and box["x"] + 4 < at[0] < box["x"] + box["width"] - 4 and box["y"] + 4 < at[1] < box["y"] + box["height"] - 4
            return at if inside else None
    return None


def drag(page, start, delta, steps=12):
    """A left drag from start by delta (client px); nothing when the handle is out of sight (start None)."""
    if not start:
        print("  (no handle in sight to drag)")
        return
    page.mouse.move(*start)
    page.mouse.down()
    page.mouse.move(start[0] + delta[0], start[1] + delta[1], steps=steps)
    page.mouse.up()
    page.wait_for_timeout(250)


def side_ends(page):
    """{value: (from_xyz, to_xyz)} of the listed exit edges (the radios' data attributes)."""
    return page.evaluate("""() => Object.fromEntries([...document.querySelectorAll('input[name=cadSide]')].filter(i => i.dataset.from)
        .map(i => [i.value, [i.dataset.from.split(',').map(Number), i.dataset.to.split(',').map(Number)]]))""")


def turn_deg(poly, k):
    """The angle (degrees) at vertex k between its two edges."""
    a, p, b = poly[k - 1], poly[k], poly[(k + 1) % len(poly)]
    u, v = (a[0] - p[0], a[1] - p[1]), (b[0] - p[0], b[1] - p[1])
    return math.degrees(math.acos(max(-1.0, min(1.0, (u[0] * v[0] + u[1] * v[1]) / (math.hypot(*u) * math.hypot(*v))))))


def line_distance(p, a, b):
    """Distance from p to the line through a and b."""
    return abs((b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])) / math.hypot(b[0] - a[0], b[1] - a[1])


def parallel(a, b, c, d, tol=1e-6):
    u, v = (b[0] - a[0], b[1] - a[1]), (d[0] - c[0], d[1] - c[1])
    return abs(u[0] * v[1] - u[1] * v[0]) <= tol * math.hypot(*u) * math.hypot(*v) and u[0] * v[0] + u[1] * v[1] > 0


def ui_errors(page, allowed=()):
    return [entry for entry in page.logs if entry[0] in ("error", "pageerror") and not any(text in entry[1] for text in allowed)]


def selection_of(data, seed, preset="flat"):
    """The /select reply of one grow operation (the ops the candidate button sends)."""
    return post_surface("select", {"selection": {"ops": [{"op": "grow", "mode": "add", "seed_facet": seed, "preset": preset}]}}, data)["selection"]


def plate_stl(lx=40.0, ly=30.0, t=1.5):
    """A box plate, facets counter-clockwise seen from outside: top (0, 1), bottom (2, 3), then the four sides."""
    p = [[0, 0, 0], [lx, 0, 0], [lx, ly, 0], [0, ly, 0], [0, 0, t], [lx, 0, t], [lx, ly, t], [0, ly, t]]
    quads = [(4, 5, 6, 7), (0, 3, 2, 1), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    triangles = []
    for a, b, c, d in quads:
        triangles += [(p[a], p[b], p[c]), (p[a], p[c], p[d])]
    out = bytearray(b"border plate".ljust(80, b" ")) + struct.pack("<I", len(triangles))
    for tri in triangles:
        out += struct.pack("<3f", 0, 0, 0) + b"".join(struct.pack("<3f", *corner) for corner in tri) + b"\0\0"
    return bytes(out)


def fin_stl(length=100.0, half=12.9, steps=24, t=2.0, sliver=2e-6):
    """An extruded fin: a plate with a faceted round tip and a sliver side (float32 apart) where the tip meets the long
    side, as a flattened fin gripper's face has.  Top and bottom fanned from (length / 2, 0)."""
    ring = [[0.0, -half], [length, -half]]
    ring += [[length + half * math.cos(math.radians(-90 + 180 * k / steps)), half * math.sin(math.radians(-90 + 180 * k / steps))] for k in range(1, steps)]
    ring += [[length, half], [length, half + sliver], [0.0, half + sliver]]
    centre = [length / 2, 0.0]
    triangles = []
    for k, a in enumerate(ring):
        b = ring[(k + 1) % len(ring)]
        triangles.append(([*centre, t], [*a, t], [*b, t]))
        triangles.append(([*centre, 0.0], [*b, 0.0], [*a, 0.0]))
        triangles += [([*a, 0.0], [*b, 0.0], [*b, t]), ([*a, 0.0], [*b, t], [*a, t])]
    out = bytearray(b"border fin".ljust(80, b" ")) + struct.pack("<I", len(triangles))
    for tri in triangles:
        out += struct.pack("<3f", 0, 0, 0) + b"".join(struct.pack("<3f", *corner) for corner in tri) + b"\0\0"
    return bytes(out)


def ui_soft(browser):
    """The soft finger's contact face: the default edge, the ranked list, hover and click, and the whole editor."""
    if not SOFT.is_file():
        print(f"SKIP ui soft finger: {SOFT} is absent")
        return
    data = SOFT.read_bytes()
    page = ui_page(browser)
    ui_load(page, SOFT)
    seed = ui_state(page)["candidates"]["flat"][0]
    selection = selection_of(data, int(seed))
    outline = selection["outline_uv"]
    ui_pick(page, seed)
    settle(page)
    s = ui_state(page)
    b = s["border"]
    check("ui soft: after the selection the border is the surface outline, drawn on the part (4 corners, no handles)",
          b and b["vertices"] == 4 and not b["edited"] and b["ready"] and b["drawn"]["segments"] > 0 and b["drawn"]["outside_segments"] == 0
          and b["drawn"]["handles"] == 0 and close(b["uv"], [side["from_uv"] for side in selection["sides"]], 1e-6), b)
    auto = page.inner_text('#cadSides label:has(input[value="auto"])')
    check("ui soft: the default exit edge is shown, not a silent auto: Auto names side 1 (119.7 mm, the longest; how it chooses in its tooltip)",
          s["side"] == "auto" and s["default_edge"] == 1 and auto.strip() == "Auto (Side 1)"
          and "first tried: Side 1" in page.get_attribute('#cadSides label:has(input[value="auto"])', "title"), (s["side"], s["default_edge"], auto))
    radios = page.evaluate("() => [...document.querySelectorAll('input[name=cadSide]')].map(i => [i.value, Number(i.dataset.length || 0)])")
    lengths = [length for value, length in radios[1:]]
    check("ui soft: the candidate edges are listed ranked by length, Auto first (1, 3, 0, 2)",
          [value for value, _ in radios] == ["auto", "1", "3", "0", "2"] and lengths == sorted(lengths, reverse=True) and s["edges"] == [1, 3, 0, 2], radios)
    page.hover('#cadSides label:has(input[value="0"])')
    page.wait_for_timeout(120)
    hovered = ui_state(page)
    page.mouse.move(5, 5)
    page.wait_for_timeout(120)
    check("ui soft: hovering a row highlights its edge in 3D; leaving clears it",
          hovered["hover_edge"] == 0 and hovered["border"]["drawn"]["hover"] and ui_state(page)["hover_edge"] is None, (hovered["hover_edge"], ui_state(page)["hover_edge"]))
    # The Base edge tool: hover, then click a visible side.
    page.click('#cadTools label:has(input[value="edge"])')
    page.locator("#cadView").scroll_into_view_if_needed()
    ends = side_ends(page)["0"]
    middle = probe(page, [(a + b) / 2 for a, b in zip(*ends)])
    page.mouse.move(middle[0] + 1, middle[1] + 1)
    page.wait_for_timeout(200)
    s = ui_state(page)
    label = page.evaluate("() => { const l = document.getElementById('cadHoverLabel'); return l.hidden ? null : l.textContent; }")
    check("ui soft: the Base edge tool highlights the edge under the cursor before the click, with its length",
          s["hover_edge"] == 0 and s["border"]["drawn"]["hover"] and label and label.startswith("Side 0 · 25.8 mm"), (s["hover_edge"], label))
    SHOTS.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(SHOTS / "border_soft_hover.png"))
    page.mouse.click(middle[0] + 1, middle[1] + 1)
    page.wait_for_timeout(150)
    check("ui soft: clicking the visible side selects it", ui_state(page)["side"] == 0, ui_state(page)["side"])
    page.check('input[name=cadSide][value="auto"]')
    page.click('#cadTools label:has(input[value="grow"])')
    # The editor.  (Containment Whole board chosen first: the border holds Field only, and Surface outline gives it back.)
    page.select_option("#cadContainment", "board")
    page.click("#cadEditBorder")
    page.wait_for_timeout(250)
    s = ui_state(page)
    check("ui soft: Edit border shows the handles (4 corners, 4 edge diamonds) and the border bar",
          s["border"]["editing"] and s["border"]["drawn"]["editing"] and s["border"]["drawn"]["handles"] == 8 and page.is_visible("#cadBorderBar")
          and page.get_attribute("#cadEditBorder", "aria-pressed") == "true", s["border"]["drawn"])
    page.screenshot(path=str(SHOTS / "border_soft_editing.png"))
    # A corner dragged into the face: any quadrilateral.
    before = s["border"]["uv"]
    corner = handle_at(page, "vertex", 2)
    drag(page, corner, (30, -50))
    s = ui_state(page)
    uv = s["border"]["uv"]
    check("ui soft: dragging a corner moves only that corner, to any quadrilateral (no right angle kept)",
          s["border"]["edited"] and len(uv) == 4 and uv[2] != before[2] and all(close(uv[k], before[k], 1e-9) for k in (0, 1, 3))
          and abs(turn_deg(uv, 2) - 90) > 5 and abs(turn_deg(uv, 1) - 90) > 2, uv)
    check("ui soft: with a border Containment shows Field only, disabled, Row traces free, and the hint says why (no Board rules: section 26.16)",
          page.input_value("#cadContainment") == "field" and page.is_disabled("#cadContainment") and page.locator("#cadTemplate").count() == 0
          and not page.is_disabled("#cadRowSides") and page.input_value("#cadRowSides") == "both"
          and "Your border" in page.inner_text("#cadConfigHint"), page.inner_text("#cadConfigHint")[-200:])
    check("ui soft: the list now offers the border's edges, ranked", page.inner_text("#cadSides").count("Border edge") >= 4 and s["edges"][0] == s["default_edge"], page.inner_text("#cadSides"))
    # An edge dragged parallel: its neighbours keep their lines.
    before = uv
    edge = handle_at(page, "edge", 0)
    drag(page, edge, (0, 40))
    uv = ui_state(page)["border"]["uv"]
    check("ui soft: dragging edge 0 moves it parallel; its neighbours are extended along their own lines",
          uv != before and parallel(uv[0], uv[1], before[0], before[1]) and line_distance(uv[0], before[3], before[0]) < 1e-5
          and line_distance(uv[1], before[1], before[2]) < 1e-5 and close(uv[2:], before[2:], 1e-9), (before, uv))
    # An edge dragged beyond the surface: drawn dashed there, no taxels there.
    before = uv
    edge = handle_at(page, "edge", 3)
    drag(page, edge, (40, 0))
    s = ui_state(page)
    uv = s["border"]["uv"]
    outside_vertices = [p for p in uv if not in_rings(p, [outline], 1e-6)]
    check("ui soft: an edge dragged beyond the surface: the border leaves it (dashed there, the solid part with a gap)",
          parallel(uv[3], uv[0], before[3], before[0]) and outside_vertices and s["border"]["outside_parts"] >= 1
          and s["border"]["drawn"]["outside_segments"] > 0 and s["border"]["drawn"]["segments"] > 0, s["border"]["drawn"])
    drawn = s["border"]["drawn"]
    check("ui soft: the default exit (border edge 3, now beyond the surface) is drawn dashed in magenta, not solid",
          s["default_edge"] == 3 and drawn["exit_outside_segments"] > 0 and drawn["exit_segments"] == 0, (s["default_edge"], drawn))
    page.screenshot(path=str(SHOTS / "border_soft_beyond.png"))
    after_beyond = uv
    page.click("#cadBorderUndo")
    page.wait_for_timeout(150)
    undone = ui_state(page)["border"]["uv"]
    page.click("#cadBorderRedo")
    page.wait_for_timeout(150)
    check("ui soft: Undo restores the border before the last drag, Redo the drag again",
          close(undone, before, 1e-9) and close(ui_state(page)["border"]["uv"], after_beyond, 1e-9), (undone, before))
    # Fit with the border: the request carries it; every taxel inside it and on the surface.
    page.click("#cadFit")
    settle(page, 300)
    wait_until(page, "() => JSON.parse(document.getElementById('cadState').textContent).preview_taxels !== null", 120)
    s = ui_state(page)
    header = fit_header(page)
    check("ui soft: the fit request carries the border (its uv), base auto and Containment field, no template",
          header.get("border") and close(header["border"]["uv"], s["border"]["uv"], 1e-6) and header.get("base") == "auto"
          and header["options"].get("containment") == "field" and "template" not in header["options"], {k: header.get(k) for k in ("border", "base")})
    check("ui soft: the proposals are fitted inside the border (its edge as the exit, its metrics)",
          s["proposals"] >= 1 and s["fit_border"] and s["proposal"]["base_kind"] == "border" and s["proposal"]["border_area_mm2"] > 0
          and 0 < s["proposal"]["border_on_surface"] < 1 and "Inside your border" in page.inner_text("#cadFitFacts") and "Border" in page.inner_text("#cadProposalFacts"), s["proposal"])
    preview = page.maps[-1] if page.maps else {}
    taxels = [taxel["uv_mm"] for taxel in preview.get("taxels", [])]
    record = next((item for item in preview.get("verification", []) if item["rule"] == "taxels_inside_border"), None)
    check("ui soft: every previewed taxel lies inside the border and on the surface (none beyond it), the map's record passes",
          taxels and len(taxels) == s["proposal"]["taxels"] and all(in_rings(p, [uv], 1e-6) and in_rings(p, [outline], 1e-6) for p in taxels)
          and record and record["passed"], (len(taxels), record))
    flat = page.evaluate("() => [document.querySelectorAll('#cadFlat .flat-border').length, document.querySelectorAll('#cadFlat .flat-border-out').length]")
    check("ui soft: the flat preview shows the border (hatched beyond the surface)", flat == [1, 1] and "your border" in page.inner_text("#cadFlatCaption"), flat)
    page.screenshot(path=str(SHOTS / "border_soft_fit.png"))
    page.locator("#cadWorkspace").screenshot(path=str(SHOTS / "border_soft_fit_workspace.png"))
    # The exit: a border edge from the list.
    choice = s["edges"][0]
    page.check(f'input[name=cadSide][value="{choice}"]')
    page.click("#cadFit")
    settle(page, 300)
    wait_until(page, "() => JSON.parse(document.getElementById('cadState').textContent).preview_taxels !== null", 120)
    s = ui_state(page)
    header = fit_header(page)
    check(f"ui soft: border edge {choice} chosen: sent as base {{border_edge: {choice}}}; the proposal's exit is that edge",
          header.get("base") == {"border_edge": choice} and s["proposal"]["base_side"] == choice and s["proposal"]["base_kind"] == "border"
          and f"border edge {choice}" in page.inner_text("#cadFlatCaption"), (header.get("base"), s["proposal"]))
    # Generate keeps the border: the build's map has the record, in the verification table.
    page.click("#cadGenerate")
    wait_until(page, "() => { const s = JSON.parse(document.getElementById('cadState').textContent); return s.busy.length === 0 && s.pending_build === null && (s.verification !== null || s.map_error !== null); }", 240)
    page.wait_for_timeout(200)
    s = ui_state(page)
    row = page.get_attribute('#cadVerifyTable tr[data-rule="taxels_inside_border"]', "class")
    check("ui soft: Generate and the map: every check passes, taxels_inside_border among them in the verification table",
          s["verification"] and s["verification"]["ok"] and row == "is-pass" and "inside the border" in page.inner_text("#cadVerifyTable"), (s["verification"], row))
    page.locator("#cadWorkspace").screenshot(path=str(SHOTS / "border_soft_generated_workspace.png"))
    # An edit after the fit: the proposals are stale.  (The fit looked at the taxels: the whole face in sight again.)
    page.click('[data-cad-view="-x"]')
    page.wait_for_timeout(200)
    corner = handle_at(page, "vertex", 1)
    drag(page, corner, (12, 10))
    s = ui_state(page)
    check("ui soft: editing the border after the fit makes the proposals stale (Generate waits, says why)",
          s["fit_stale"] and page.is_disabled("#cadGenerate") and "border changed" in page.inner_text("#cadGenerate")
          and "The border changed" in page.inner_text("#cadFitNote"), (s["fit_stale"], page.inner_text("#cadGenerate")))
    # Surface outline (reset).
    page.click("#cadBorderReset")
    page.wait_for_timeout(200)
    s = ui_state(page)
    check("ui soft: Surface outline resets the border; Containment comes back (Whole board, as chosen before the border)",
          not s["border"]["edited"] and s["border"]["outside_parts"] == 0 and not page.is_disabled("#cadContainment")
          and page.input_value("#cadContainment") == "board" and page.is_disabled("#cadRowSides")
          and s["fit_stale"] and s["edges"] == [1, 3, 0, 2], (s["border"]["edited"], s["fit_stale"], page.input_value("#cadContainment")))
    # Inset of the outline (Largest rectangle before section 26.16 set a rectangle first): every edge 2 mm inward, each
    # corner 2 mm from both its edges' lines.
    check("ui soft: the border bar has no Largest rectangle (section 26.16)", page.locator("#cadBorderRect").count() == 0)
    quad = s["border"]["uv"]
    page.fill("#cadBorderInsetMm", "2")
    page.click("#cadBorderInset")
    page.wait_for_timeout(200)
    inset = ui_state(page)["border"]["uv"]
    distances = [line_distance(inset[k], quad[j], quad[(j + 1) % 4]) for k in range(len(inset)) for j in ((k - 1) % 4, k)] if len(inset) == 4 == len(quad) else []
    check("ui soft: Inset by 2 mm moves every edge 2 mm inward", distances and all(abs(d - 2.0) < 1e-6 for d in distances) and area(inset) < area(quad), distances)
    # A corner added by a double click on an edge, then removed (Delete key), then back (Ctrl+Z).
    edge = handle_at(page, "edge", 1)
    if edge:
        page.mouse.dblclick(*edge)
    page.wait_for_timeout(250)
    s = ui_state(page)
    added = s["border"]["uv"]
    middle = [(inset[1][0] + inset[2][0]) / 2, (inset[1][1] + inset[2][1]) / 2]
    check("ui soft: double-clicking an edge adds a corner there (selected)", len(added) == 5 and close(added[2], middle, 1e-6) and s["border"]["selected_vertex"] == 2, added)
    page.keyboard.press("Delete")
    page.wait_for_timeout(200)
    removed = ui_state(page)["border"]["uv"]
    page.keyboard.press("Control+z")
    page.wait_for_timeout(200)
    check("ui soft: Delete removes the selected corner; Ctrl+Z brings it back",
          close(removed, inset, 1e-9) and len(ui_state(page)["border"]["uv"]) == 5, (len(removed), len(ui_state(page)["border"]["uv"])))
    corner = handle_at(page, "vertex", 0)
    if corner:
        page.mouse.click(*corner)
    page.wait_for_timeout(150)
    selected = ui_state(page)["border"]["selected_vertex"]
    page.click("#cadBorderDelete")
    page.wait_for_timeout(150)
    check("ui soft: a click on a corner selects it; Delete corner removes it", selected == 0 and len(ui_state(page)["border"]["uv"]) == 4, selected)
    page.click("#cadEditBorder")
    page.wait_for_timeout(150)
    s = ui_state(page)
    check("ui soft: Done editing hides the handles and keeps the border", not s["border"]["editing"] and s["border"]["drawn"]["handles"] == 0
          and s["border"]["drawn"]["segments"] > 0 and s["border"]["edited"], s["border"]["drawn"])
    check("ui soft: no console error", not ui_errors(page), ui_errors(page)[:3])
    page.close()


def ui_plate(browser):
    """A flat plate: a click where a hidden edge projects never selects it; a border fitted on the top face."""
    data = plate_stl()
    path = SHOTS / "border_plate.stl"
    SHOTS.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    page = ui_page(browser)
    ui_load(page, path)
    # The bottom face (facets 2, 3): seen from the iso view its back and right sides are behind the plate.
    seeds = ui_state(page)["candidates"]["flat"]
    bottom = next((seed for seed in seeds if seed in (2, 3)), None)
    top = next((seed for seed in seeds if seed in (0, 1)), None)
    check("ui plate: the top and the bottom face are candidates", bottom is not None and top is not None, seeds)
    ui_pick(page, bottom)
    settle(page)
    page.click('[data-cad-view="iso"]')
    page.click('#cadTools label:has(input[value="edge"])')
    page.locator("#cadView").scroll_into_view_if_needed()
    page.wait_for_timeout(200)
    ends = side_ends(page)
    hidden = next(value for value, (a, b) in ends.items() if abs(a[1] - 30) < 1e-6 and abs(b[1] - 30) < 1e-6)  # y = 30: the back
    left = next(value for value, (a, b) in ends.items() if abs(a[0]) < 1e-6 and abs(b[0]) < 1e-6)  # x = 0: seen from the iso view
    front = next(value for value, (a, b) in ends.items() if abs(a[1]) < 1e-6 and abs(b[1]) < 1e-6)
    screen = {value: [probe(page, a), probe(page, b)] for value, (a, b) in ends.items()}

    def nearest(point):
        """The side the old pick (nearest projected side, no occlusion) takes, and each side's distance (px)."""
        found = {value: segment_distance(point, *segment) for value, segment in screen.items()}
        return min(found, key=found.get), found

    a, b = screen[hidden]
    middle = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2]
    old, _ = nearest(middle)
    page.mouse.click(*middle)
    page.wait_for_timeout(150)
    s = ui_state(page)
    check("ui plate: a click on the hidden back side's projection (the old pick's side) selects nothing",
          old == hidden and s["side"] == "auto" and "where you can see it" in page.inner_text("#cadStatus"), (old, hidden, s["side"]))
    # Near the back-left corner: the hidden back side is nearest on screen, the visible left side within the pick distance.
    corner = a if math.dist(a, screen[left][0]) < 1 or math.dist(a, screen[left][1]) < 1 else b
    other = b if corner is a else a
    length = math.dist(corner, other)
    point = [corner[0] + (other[0] - corner[0]) * 6 / length, corner[1] + (other[1] - corner[1]) * 6 / length]
    old, found = nearest(point)
    page.mouse.click(*point)
    page.wait_for_timeout(150)
    s = ui_state(page)
    check(f"ui plate: near a corner the hidden side projects closer ({found[hidden]:.1f} px) than the visible one ({found[left]:.1f} px): the visible one is selected",
          old == hidden and found[left] < 14 and s["side"] == int(left), (old, found, s["side"], left))
    a, b = screen[front]
    page.mouse.click((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    page.wait_for_timeout(150)
    check("ui plate: a click on the visible front side selects it", ui_state(page)["side"] == int(front), ui_state(page)["side"])
    page.screenshot(path=str(SHOTS / "border_plate_bottom_iso.png"))
    # The top face with a border reaching beyond the plate: the taxels stay on the plate and inside the border.
    page.click('#cadTools label:has(input[value="grow"])')
    page.click("#cadClear")
    settle(page)
    ui_pick(page, top)
    settle(page)
    selection = selection_of(data, top)
    page.click("#cadEditBorder")
    page.wait_for_timeout(200)
    page.fill("#cadBorderInsetMm", "-6")
    page.click("#cadBorderInset")
    page.wait_for_timeout(200)
    grown = ui_state(page)["border"]
    corner = handle_at(page, "vertex", 0)
    drag(page, corner, (60, -20))
    s = ui_state(page)
    check("ui plate: an outset border with a corner dragged in: it lies partly beyond the plate (dashed there)",
          len(grown["uv"]) == 4 and area(grown["uv"]) > 1200 and s["border"]["outside_parts"] >= 1 and s["border"]["drawn"]["outside_segments"] > 0, s["border"])
    page.screenshot(path=str(SHOTS / "border_plate_top_beyond.png"))
    page.click("#cadFit")
    settle(page, 300)
    wait_until(page, "() => JSON.parse(document.getElementById('cadState').textContent).preview_taxels !== null", 120)
    s = ui_state(page)
    preview = page.maps[-1] if page.maps else {}
    taxels = [taxel["uv_mm"] for taxel in preview.get("taxels", [])]
    record = next((item for item in preview.get("verification", []) if item["rule"] == "taxels_inside_border"), None)
    check("ui plate: the fit inside the border places every taxel on the plate and inside the border (the map's record passes)",
          s["proposals"] >= 1 and taxels and all(in_rings(p, [s["border"]["uv"]], 1e-6) and in_rings(p, [selection["outline_uv"]], 1e-6) for p in taxels)
          and record and record["passed"], (s["proposals"], len(taxels), record))
    edge = s["proposal"]["base_side"]
    ends = s["border"]["uv"][edge], s["border"]["uv"][(edge + 1) % len(s["border"]["uv"])]
    off = not in_rings([(ends[0][0] + ends[1][0]) / 2, (ends[0][1] + ends[1][1]) / 2], [selection["outline_uv"]], 1e-6)
    drawn = s["border"]["drawn"]
    check(f"ui plate: the exit (border edge {edge}{', beyond the plate' if off else ''}) is drawn {'dashed' if off else 'solid'} in magenta",
          s["proposal"]["base_kind"] == "border" and (drawn["exit_outside_segments"] > 0 if off else drawn["exit_segments"] > 0), (edge, off, drawn))
    page.locator("#cadWorkspace").screenshot(path=str(SHOTS / "border_plate_fit_workspace.png"))
    check("ui plate: no console error", not ui_errors(page), ui_errors(page)[:3])
    page.close()


def ui_fin(browser):
    """A fin with a faceted round tip and a sliver side: every edge drags (diamond, line, Base edge tool), the tip's handles thinned."""
    data = fin_stl()
    path = SHOTS / "border_fin.stl"
    SHOTS.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    page = ui_page(browser)
    ui_load(page, path)
    seed = int(ui_state(page)["candidates"]["flat"][0])
    selection = selection_of(data, seed)
    shortest = min(side["length_mm"] for side in selection["sides"])
    check(f"ui fin: the face's outline holds a sliver side ({shortest:.1e} mm, under MERGE_MM)", shortest < 0.01, shortest)
    ui_pick(page, seed)
    settle(page)
    page.locator("#cadView").scroll_into_view_if_needed()
    page.click("#cadEditBorder")
    page.wait_for_timeout(250)
    s = ui_state(page)
    uv = s["border"]["uv"]
    n = len(uv)
    lengths = [math.dist(uv[k], uv[(k + 1) % n]) for k in range(n)]
    drawn = s["border"]["drawn"]
    check(f"ui fin: no border edge under MERGE_MM ({n} corners for {len(selection['sides'])} sides)", min(lengths) >= 0.01 and n == len(selection["sides"]) - 1, min(lengths))
    check(f"ui fin: overlapping handles at the tip are not drawn ({drawn['shown']} of {drawn['handles']})",
          drawn["shown"] is not None and 4 <= drawn["shown"] < drawn["handles"], drawn)
    page.screenshot(path=str(SHOTS / "border_fin_editing.png"))

    def longest():
        poly = ui_state(page)["border"]["uv"]
        return max(range(len(poly)), key=lambda k: math.dist(poly[k], poly[(k + 1) % len(poly)]))

    def on_line(k, t):
        handles = ui_state(page)["border"]["handles"]
        corners = {h["index"]: h["xyz"] for h in handles if h["kind"] == "vertex"}
        a, b = probe(page, corners[k]), probe(page, corners[(k + 1) % len(corners)])
        return [a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])]

    def across(k, px):
        """px pixels square to edge k on screen."""
        a, b = on_line(k, 0), on_line(k, 1)
        length = math.dist(a, b) or 1
        return (-(b[1] - a[1]) / length * px, (b[0] - a[0]) / length * px)

    for px in (25, -40):
        k = longest()
        before = ui_state(page)["border"]["uv"]
        drag(page, handle_at(page, "edge", k), across(k, px))
        after = ui_state(page)["border"]["uv"]
        check(f"ui fin: the longest edge ({k}) dragged {px:+d} px across by its diamond moves (its arc end square to it)",
              after != before and len(after) == len(before), (k, before == after))
    k = longest()
    before = ui_state(page)["border"]["uv"]
    drag(page, on_line(k, 0.25), across(k, 15))
    check(f"ui fin: edge {k} dragged by its line (no handle there) moves", ui_state(page)["border"]["uv"] != before)
    page.click('#cadTools label:has(input[value="edge"])')
    k = longest()
    before = ui_state(page)["border"]["uv"]
    drag(page, on_line(k, 0.7), across(k, -12))
    check("ui fin: with the Base edge tool on, the line still drags", ui_state(page)["border"]["uv"] != before)
    k = longest()
    before = ui_state(page)["border"]["uv"]
    page.mouse.click(*on_line(k, 0.4))
    page.wait_for_timeout(200)
    s = ui_state(page)
    check(f"ui fin: a click on edge {k}'s line (no move) picks it as the exit, the border unchanged",
          s["side"] == k and s["border"]["uv"] == before, (s["side"], k))
    page.screenshot(path=str(SHOTS / "border_fin_dragged.png"))
    check("ui fin: no console error", not ui_errors(page), ui_errors(page)[:3])
    page.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--external", action="store_true", help=f"use an app already serving port {PORT}")
    parser.add_argument("--only", choices=("model", "ui"), help="run only the model checks or only the UI flows")
    args = parser.parse_args(argv)
    process = None
    if not args.external:
        if answers():
            raise SystemExit(f"Something already answers on port {PORT}; stop it or pass --external.")
        process = start_server()
    try:
        with sync_playwright() as p:
            if args.only != "ui":
                browser = p.chromium.launch()
                page = browser.new_page()
                logs = []
                page.on("console", lambda m: logs.append((m.type, m.text)))
                page.on("pageerror", lambda e: logs.append(("pageerror", str(e))))
                # Rectangular mode: CAD mode would load its default part and build its sensor, whose surface requests
                # take the server's one surface slot while the model checks below send theirs (503).
                page.goto(URL + "#rect")
                page.evaluate(f"async () => {{ window.__border = await import('{MODULE}'); }}")
                B = Page(page)
                module_checks(B, page)
                create_checks(B)
                edit_checks(B)
                assets = asset_selections()
                inset_checks(B)
                snap_checks(B)
                surface_checks(B)
                misc_checks(B)
                mapping_checks(B)
                asset_checks(B, page, assets)
                errors = [entry for entry in logs if entry[0] in ("error", "pageerror")]
                check("border: no console error", not errors, errors[:3])
                browser.close()
            if args.only != "model":
                # The editor in the app needs WebGL: SwiftShader.
                browser = p.chromium.launch(args=WEBGL_ARGS)
                ui_soft(browser)
                ui_plate(browser)
                ui_fin(browser)
                browser.close()
                print(f"Screenshots: {SHOTS}")
    finally:
        if process is not None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
    return 0 if summary() else 1


if __name__ == "__main__":
    sys.exit(main())
