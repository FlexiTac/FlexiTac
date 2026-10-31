"""Repair check: top-view orientation, pin-1 marker/ring, assembly stacking, turn-over axis and registration.

For 4 connector sides x 2 role mappings (+ reverse scan order on two cases):
- 2D previews: least-squares layout->screen fit over pad/electrode centres is a Y-flipped similarity;
  tail pads on the selected side; pin-1 marker beyond the tip on the pin-1 pad axis, topmost at its
  centroid; the ring is centred on it, >= 17 px across and fully inside the pane.
- Assembly (plan view): taxel-field rects of both boards coincide (< 0.05 mm); every electrode of both
  boards sits on the lower board's taxel grid; BOTH tails exit the selected side; the upper board's
  layout->screen map is the top view mirrored about its tail axis; the lower board is the top view.
- Assembly (exploded): physical-side classes, translateZ on the upper board, face transform =
  rotateY(180) for bottom/top tails and rotateX(180) for left/right; with translateZ removed the
  projected taxel fields coincide (CDP content quads).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # no __pycache__ next to the scripts
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rp import SHOTS, browser_page, capture_generate, check, generate, open_app, summary  # noqa: E402

OVERHANG_MM = 0.2
TOL_MM = 0.05


def fit(src, dst):
    """Least squares dst = [[a b],[d e]] src + [c f]; returns a, b, c, d, e, f, max residual."""
    n = len(src)

    def solve(target):
        sxx = sum(x * x for x, _ in src); sxy = sum(x * y for x, y in src); syy = sum(y * y for _, y in src)
        sx = sum(x for x, _ in src); sy = sum(y for _, y in src)
        tx = sum(x * t for (x, _), t in zip(src, target)); ty = sum(y * t for (_, y), t in zip(src, target)); tt = sum(target)
        m = [[sxx, sxy, sx], [sxy, syy, sy], [sx, sy, n]]
        v = [tx, ty, tt]
        for i in range(3):
            p = max(range(i, 3), key=lambda r: abs(m[r][i]))
            m[i], m[p] = m[p], m[i]; v[i], v[p] = v[p], v[i]
            for r in range(3):
                if r != i and m[i][i]:
                    f = m[r][i] / m[i][i]
                    m[r] = [m[r][k] - f * m[i][k] for k in range(3)]
                    v[r] -= f * v[i]
        return [v[i] / m[i][i] for i in range(3)]

    a, b, c = solve([p[0] for p in dst])
    d, e, f = solve([p[1] for p in dst])
    res = max(math.hypot(a * x + b * y + c - X, d * x + e * y + f - Y) for (x, y), (X, Y) in zip(src, dst))
    return a, b, c, d, e, f, res


# Layout centre (rect attributes are layout coordinates inside the flip group) and screen centre per rect.
RECTS = """(svg, cls) => [...svg.querySelectorAll('rect.' + cls)].map(r => {
  const b = r.getBoundingClientRect();
  const x = +r.getAttribute('x'), y = +r.getAttribute('y'), w = +r.getAttribute('width'), h = +r.getAttribute('height');
  return {layout: [x + w / 2, y + h / 2], size: [w, h], screen: [(b.left + b.right) / 2, (b.top + b.bottom) / 2], box: [b.left, b.top, b.right, b.bottom]};
})"""

MEASURE_2D = """key => {
  const rects = """ + RECTS + """;
  const pane = document.querySelector('#' + key + 'Preview');
  pane.scrollIntoView({block: 'center'});
  const svg = pane.querySelector('svg');
  const r = e => { const b = e.getBoundingClientRect(); return [b.left, b.top, b.right, b.bottom]; };
  const marker = svg.querySelector('.pin1-marker');
  const pts = marker.getAttribute('points').trim().split(/\\s+/).map(p => p.split(',').map(Number));
  const ctm = marker.getScreenCTM();
  const scr = pts.map(([x, y]) => { const q = new DOMPoint(x, y).matrixTransform(ctm); return [q.x, q.y]; });
  const cx = scr.reduce((s, p) => s + p[0], 0) / scr.length, cy = scr.reduce((s, p) => s + p[1], 0) / scr.length;
  const hit = document.elementFromPoint(cx, cy);
  const ring = svg.querySelector('.pin1-ring');
  const flip = svg.querySelector('g[transform]').getScreenCTM();
  return {pane: r(pane), outline: r(svg.querySelector('polygon.outline')), marker: r(marker), markerCentre: [cx, cy],
          hit: hit ? (hit.getAttribute('class') || hit.tagName) : null, ring: ring ? r(ring) : null,
          ringStroke: ring ? getComputedStyle(ring).stroke : null,
          flip: [flip.a, flip.b, flip.c, flip.d, flip.e, flip.f],
          pads: rects(svg, 'pad'), electrodes: rects(svg, 'electrode'), label: svg.getAttribute('aria-label')};
}"""

MEASURE_PLAN = """() => {
  const rects = """ + RECTS + """;
  const out = {};
  for (const box of document.querySelectorAll('#stackedPreview .assembly-board')) {
    const svg = box.querySelector('svg');
    const f = svg.querySelector('rect.taxel-field').getBoundingClientRect();
    out[box.dataset.physicalSide] = {
      role: box.dataset.role, cls: box.className, field: [f.left, f.top, f.right, f.bottom],
      fieldAttr: ['x', 'y', 'width', 'height'].map(k => +svg.querySelector('rect.taxel-field').getAttribute(k)),
      pads: rects(svg, 'pad'), electrodes: rects(svg, 'electrode'),
      ring: (() => { const g = svg.querySelector('.pin1-ring').getBoundingClientRect(); return [g.left, g.top, g.right, g.bottom]; })(),
      titles: svg.querySelectorAll('title').length,
      labelDisplay: getComputedStyle(svg.querySelector('.view-label')).display,
    };
  }
  return out;
}"""

TRANSFORMS = """() => {
  const out = {};
  for (const box of document.querySelectorAll('#stackedPreview .assembly-board')) {
    out[box.dataset.physicalSide] = {board: getComputedStyle(box).transform, face: getComputedStyle(box.querySelector('.assembly-face')).transform,
                                     index: [...box.parentNode.children].indexOf(box)};
  }
  return out;
}"""


def matrix3d(text):
    if not text or text == "none":
        return None
    values = [float(v) for v in text[text.index("(") + 1:-1].split(",")]
    if len(values) == 6:  # 2D matrix(a, b, c, d, e, f)
        a, b, c, d, e, f = values
        return [a, b, 0, 0, c, d, 0, 0, 0, 0, 1, 0, e, f, 0, 1]
    return values


def side_of(points, box):
    """Which side of box [l, t, r, b] the mean of the points lies beyond (screen axes)."""
    mx = sum(p[0] for p in points) / len(points); my = sum(p[1] for p in points) / len(points)
    l, t, r, b = box
    beyond = {"left": l - mx, "right": mx - r, "top": t - my, "bottom": my - b}
    return max(beyond, key=beyond.get), beyond


def check_2d(page, key, board, case):
    data = page.evaluate(MEASURE_2D, key)
    items = data["pads"] + data["electrodes"]
    a, b, c, d, e, f, res = fit([i["layout"] for i in items], [i["screen"] for i in items])
    check(f"{case} {key}: 2D view is a Y-flipped top view (similarity, no shear)",
          a > 0 and e < 0 and abs(a + e) < 1e-3 * a and abs(b) < 1e-3 * a and abs(d) < 1e-3 * a and res < 0.6,
          f"a={a:.4f} e={e:.4f} b={b:.2e} d={d:.2e} residual={res:.3f}px")
    side = board["tail"]["side"]
    pad_side, beyond = side_of([p["screen"] for p in data["pads"]], data["outline"])
    # pads lie inside the outline; use their position within the outline box instead
    l, t, r, btm = data["outline"]
    mx = sum(p["screen"][0] for p in data["pads"]) / len(data["pads"]); my = sum(p["screen"][1] for p in data["pads"]) / len(data["pads"])
    fx = (mx - l) / (r - l); fy = (my - t) / (btm - t)
    expect = {"bottom": fy > 0.85, "top": fy < 0.15, "left": fx < 0.15, "right": fx > 0.85}[side]
    check(f"{case} {key}: tail pads drawn on the {side} of the 2D preview", expect, f"pad centroid at x {fx:.3f}, y {fy:.3f} of the outline box")
    # pin-1 marker beyond the tip on the axis of the pin-1 pad
    pad = next(p for p in board["layers"]["top_copper"]["pads"] if p.get("pin") == 1)
    fl = data["flip"]
    px = fl[0] * pad["x"] + fl[2] * pad["y"] + fl[4]; py = fl[1] * pad["x"] + fl[3] * pad["y"] + fl[5]
    mx, my = data["markerCentre"]
    scale = abs(a)
    if side in ("bottom", "top"):
        aligned = abs(mx - px) < 0.5; beyond_tip = (my > py) if side == "bottom" else (my < py)
    else:
        aligned = abs(my - py) < 0.5; beyond_tip = (mx < px) if side == "left" else (mx > px)
    check(f"{case} {key}: pin-1 marker beyond the tip, on the pin-1 pad axis ({pad['net']})", aligned and beyond_tip,
          f"marker ({mx:.1f},{my:.1f}) pad ({px:.1f},{py:.1f})")
    check(f"{case} {key}: pin-1 marker is the topmost element at its centre", data["hit"] == "pin1-marker", data["hit"])
    ring = data["ring"]; pane = data["pane"]
    rcx = (ring[0] + ring[2]) / 2; rcy = (ring[1] + ring[3]) / 2; dia = ring[2] - ring[0]
    inside = ring[0] >= pane[0] and ring[1] >= pane[1] and ring[2] <= pane[2] and ring[3] <= pane[3]
    check(f"{case} {key}: pin-1 ring centred on the marker, >= 17 px across, fully inside the pane",
          abs(rcx - mx) < 0.6 and abs(rcy - my) < 0.6 and dia >= 17 and inside,
          f"ring {dia:.1f}px centre off by ({rcx - mx:.2f},{rcy - my:.2f}); clip {max(pane[0] - ring[0], pane[1] - ring[1], ring[2] - pane[2], ring[3] - pane[3], 0):.1f}px; {scale:.2f}px/mm")
    return data


def check_assembly(page, result, case, cdp):
    boards = result["boards"]
    upper = next(b for b in boards.values() if b["physical_side"] == "top")
    lower = next(b for b in boards.values() if b["physical_side"] == "bottom")
    side = upper["tail"]["side"]
    axis = "x" if side in ("left", "right") else "y"
    page.evaluate("() => document.querySelector('#stackedPreview').scrollIntoView({block: 'center'})")
    page.click('[data-assembly-mode="exploded"]')
    page.wait_for_timeout(80)
    tr = page.evaluate(TRANSFORMS)
    up_board = matrix3d(tr["top"]["board"]); up_face = matrix3d(tr["top"]["face"]); low_face = matrix3d(tr["bottom"]["face"])
    check(f"{case}: physical top board is the upper element (translateZ 96px, drawn after the lower board)",
          up_board is not None and abs(up_board[14] - 96) < 1e-6 and tr["top"]["index"] > tr["bottom"]["index"]
          and matrix3d(tr["bottom"]["board"]) in (None, [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]),
          f"upper {tr['top']['board']} lower {tr['bottom']['board']}")
    if axis == "y":
        ok = up_face and abs(up_face[0] + 1) < 1e-9 and abs(up_face[5] - 1) < 1e-9 and abs(up_face[10] + 1) < 1e-9
    else:
        ok = up_face and abs(up_face[0] - 1) < 1e-9 and abs(up_face[5] + 1) < 1e-9 and abs(up_face[10] + 1) < 1e-9
    check(f"{case}: upper face turned over about its tail axis ({'rotateY' if axis == 'y' else 'rotateX'}(180deg)); lower face up",
          ok and low_face is None, f"upper face {tr['top']['face']}; lower face {tr['bottom']['face']}")
    # draw order: recolour (lower green, upper blue, opaque) and sample inside the exact projected upper field quad
    obj = cdp.send("Runtime.evaluate", {"expression": "document.querySelector('#stackedPreview .is-upper rect.taxel-field')"})["result"]["objectId"]
    quad = cdp.send("DOM.getContentQuads", {"objectId": obj})["quads"][0]
    style = page.add_style_tag(content=(
        ".is-lower svg *{fill:#00ff00 !important;stroke:#00ff00 !important;opacity:1 !important}"
        ".is-upper svg *{fill:#0000ff !important;stroke:#0000ff !important;opacity:1 !important}"
        ".is-upper svg{opacity:1 !important}.assembly-board svg{filter:none !important}.taxel-field,.pin1-ring{visibility:hidden !important}"))
    page.wait_for_timeout(80)
    from PIL import Image
    import io
    image = Image.open(io.BytesIO(page.screenshot())).convert("RGB")
    corners = [(quad[i], quad[i + 1]) for i in range(0, 8, 2)]
    samples = []
    for i in range(1, 8):
        for j in range(1, 5):
            u, v = i / 8, j / 5  # bilinear inside the quad
            x = (1 - u) * (1 - v) * corners[0][0] + u * (1 - v) * corners[1][0] + u * v * corners[2][0] + (1 - u) * v * corners[3][0]
            y = (1 - u) * (1 - v) * corners[0][1] + u * (1 - v) * corners[1][1] + u * v * corners[2][1] + (1 - u) * v * corners[3][1]
            samples.append(image.getpixel((int(x), int(y))))
    page.evaluate("s => s.remove()", style)
    blue = sum(1 for q in samples if q[2] > 200 and q[1] < 80); green = sum(1 for q in samples if q[1] > 200 and q[2] < 80)
    check(f"{case}: exploded view draws the upper board in front inside its projected taxel field", green == 0 and blue >= len(samples) - 2,
          f"blue {blue}/{len(samples)}, green {green}")
    # exploded registration: drop the visual Z spacing, compare projected field quads
    page.evaluate("() => { document.querySelector('#stackedPreview .assembly-board.is-upper').style.transform = 'none'; }")
    page.wait_for_timeout(50)
    quads = {}
    for name in ("is-upper", "is-lower"):
        obj = cdp.send("Runtime.evaluate", {"expression": f"document.querySelector('#stackedPreview .{name} rect.taxel-field')"})["result"]["objectId"]
        quads[name] = cdp.send("DOM.getContentQuads", {"objectId": obj})["quads"][0]
    page.evaluate("() => { document.querySelector('#stackedPreview .assembly-board.is-upper').style.transform = ''; }")
    qu, ql = quads["is-upper"], quads["is-lower"]
    # match corners irrespective of order (the upper rect is mirrored)
    cu = [(qu[i], qu[i + 1]) for i in range(0, 8, 2)]; cl = [(ql[i], ql[i + 1]) for i in range(0, 8, 2)]
    worst_px = max(min(math.hypot(x - X, y - Y) for X, Y in cl) for x, y in cu)
    edge_px = max(math.hypot(cl[1][0] - cl[0][0], cl[1][1] - cl[0][1]), math.hypot(cl[2][0] - cl[1][0], cl[2][1] - cl[1][1]))
    field = lower["grid_registration"]["active_region"]
    mm_per_px = max(field["width"], field["height"]) / edge_px
    check(f"{case}: exploded view registers the taxel fields once the visual spacing is removed (< {TOL_MM} mm)",
          worst_px * mm_per_px < TOL_MM, f"worst corner {worst_px:.3f}px = {worst_px * mm_per_px:.4f} mm")
    # plan view
    page.click('[data-assembly-mode="plan"]')
    page.wait_for_timeout(120)
    plan = page.evaluate(MEASURE_PLAN)
    up, low = plan["top"], plan["bottom"]
    check(f"{case}: physical sides and roles of the assembly boxes", up["role"] == upper["role"] and low["role"] == lower["role"]
          and "is-upper" in up["cls"] and "is-lower" in low["cls"], f"{up['cls']} / {low['cls']}")
    s = (low["field"][2] - low["field"][0]) / low["fieldAttr"][2]  # px per mm
    err_mm = max(abs(u - v) for u, v in zip(up["field"], low["field"])) / s
    check(f"{case}: plan view taxel fields coincide (< {TOL_MM} mm)", err_mm < TOL_MM, f"max edge error {err_mm:.4f} mm at {s:.2f}px/mm")
    L, T, R, B = low["field"]
    pitch_x = lower["grid_registration"]["pitch_x_mm"]; pitch_y = lower["grid_registration"]["pitch_y_mm"]
    worst = 0.0
    for who, data in (("upper", up), ("lower", low)):
        # Row electrodes step by pitch_y and Column electrodes by pitch_x, whichever
        # screen axis the tail side turns them to.
        pitch = pitch_y if data["role"] == "rows" else pitch_x
        for el in data["electrodes"]:
            w, h = el["size"]
            bx = el["box"]
            if w >= h:  # horizontal electrode: centre on the grid across it, spans the field + overhang in X
                width_mm = h; k = round(((el["screen"][1] - T) / s - width_mm / 2) / pitch)
                exp_c = T + (width_mm / 2 + k * pitch) * s
                dev = max(abs(el["screen"][1] - exp_c), abs(bx[0] - (L - OVERHANG_MM * s)), abs(bx[2] - (R + OVERHANG_MM * s))) / s
            else:
                width_mm = w; k = round(((el["screen"][0] - L) / s - width_mm / 2) / pitch)
                exp_c = L + (width_mm / 2 + k * pitch) * s
                dev = max(abs(el["screen"][0] - exp_c), abs(bx[1] - (T - OVERHANG_MM * s)), abs(bx[3] - (B + OVERHANG_MM * s))) / s
            worst = max(worst, dev)
    check(f"{case}: every electrode of both boards on the taxel grid (< {TOL_MM} mm)", worst < TOL_MM, f"worst {worst:.4f} mm")
    # orthogonal electrode sets
    def orient(data):
        hs = {el["size"][0] >= el["size"][1] for el in data["electrodes"]}
        return hs.pop() if len(hs) == 1 else None
    check(f"{case}: upper and lower electrodes cross (orthogonal)", orient(up) is not None and orient(low) is not None and orient(up) != orient(low))
    for who, data, board in (("upper", up, upper), ("lower", low, lower)):
        got, beyond = side_of([p["screen"] for p in data["pads"]], low["field"])
        check(f"{case}: {who} board ({board['role']}) tail exits the {board['tail']['side']} side of the stack", got == board["tail"]["side"],
              f"pads beyond the field: {', '.join(f'{k} {v / s:.1f}mm' for k, v in beyond.items())}")
    # handedness: the lower board is the top view; the upper board is the top view mirrored about its tail axis
    for who, data in (("upper", up), ("lower", low)):
        items = data["pads"] + data["electrodes"]
        a, b, c, d, e, f, res = fit([i["layout"] for i in items], [i["screen"] for i in items])
        if who == "lower" or True:
            expect = (a > 0 and e < 0) if who == "lower" else ((a < 0 and e < 0) if axis == "y" else (a > 0 and e > 0))
        check(f"{case}: {who} board map is {'the top view' if who == 'lower' else 'the top view mirrored ' + ('left-right' if axis == 'y' else 'top-bottom')}",
              expect and abs(abs(a) - abs(e)) < 1e-3 * abs(a) and abs(b) < 1e-3 * abs(a) and abs(d) < 1e-3 * abs(a) and res < 0.6,
              f"a={a:.4f} e={e:.4f} residual={res:.3f}px")
    ring_ok = all((d["ring"][2] - d["ring"][0]) >= 10 for d in (up, low))
    check(f"{case}: assembly copies: pin-1 rings drawn, labels hidden, no <title> tooltips",
          ring_ok and up["labelDisplay"] == "none" and low["labelDisplay"] == "none" and up["titles"] == 0 and low["titles"] == 0,
          f"rings {[round(d['ring'][2] - d['ring'][0], 1) for d in (up, low)]}px")
    legend = page.inner_text("#assemblyLegend")
    check(f"{case}: legend states both tail exits and the roles",
          f"tail exits {upper['tail']['side']}" in legend and f"tail exits {lower['tail']['side']}" in legend
          and ("Row FPC" in legend and "Column FPC" in legend) and "tail axis" in legend, legend.replace("\n", " | ")[:220])
    return plan


CASES = [(side, mapping, "forward") for side in ("bottom", "top", "left", "right") for mapping in ("top", "bottom")]
CASES += [("bottom", "top", "reverse"), ("left", "bottom", "reverse")]


def run_cases(page, cases, shots=True):
    seen = capture_generate(page)
    open_app(page)
    cdp = page.context.new_cdp_session(page)
    cdp.send("DOM.enable"); cdp.send("Runtime.enable")
    for side, mapping, order in cases:
        generate(page, connectorSide=side, rowLayer=mapping, scanOrder=order)
        body, result = seen[-1]
        case = f"[{side}/rows-{mapping}/{order}]"
        check(f"{case}: request carries the form choice and the result is ok",
              body["connector_side"] == side and body["row_fpc_position"] == mapping and result.get("ok") is True,
              result["manifest"]["build_id"])
        for key in ("row", "column"):
            check_2d(page, key, result["boards"][key], case)
        check_assembly(page, result, case, cdp)
        if shots and order == "forward":
            page.locator(".stacked-review").screenshot(path=f"{SHOTS}/asm_plan_{side}_rows-{mapping}.png")
            page.click('[data-assembly-mode="exploded"]'); page.wait_for_timeout(80)
            page.locator(".stacked-review").screenshot(path=f"{SHOTS}/asm_3d_{side}_rows-{mapping}.png")
            page.locator(".previews").screenshot(path=f"{SHOTS}/previews_{side}_rows-{mapping}.png")


def main():
    with browser_page(width=1600, height=1000) as page:
        run_cases(page, CASES)
        errors = [entry for entry in page.logs if entry[0] in ("error", "pageerror")]
        check("no console errors during the orientation run", not errors, errors[:3])
    return summary()


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
