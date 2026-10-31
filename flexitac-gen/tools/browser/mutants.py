"""Discrimination check: serve mutated app.js/styles.css; the targeted checks must fail (KILLED)."""
from __future__ import annotations

import contextlib
import io
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # no __pycache__ next to the scripts
sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright.sync_api import sync_playwright  # noqa: E402

import orient  # noqa: E402
import rp  # noqa: E402
import ui_checks  # noqa: E402

WEB = str(Path(__file__).resolve().parents[2] / "web")
APP = open(f"{WEB}/app.js", encoding="utf-8").read()
CSS = open(f"{WEB}/styles.css", encoding="utf-8").read()
ORIENT_CASES = [("bottom", "top", "forward"), ("left", "bottom", "forward")]
# The stacked view's pin-1 rings of app.js (P5-diagonal-bus.md sections 27.3-27.5), the mutants' text to replace: the
# placement chosen, and the moves apart tried.
CHOSEN = "    const [, , top, bottom] = chosen || placed.find(candidate => fits(candidate)) || placed.find(([upper, lower]) => apart(upper, lower)) || placed[0];"
SHARES = "      for (const [up, down] of [[0.5, 0.5], [1, 0], [0, 1]]) {"
TURNS = "    const turns = [0, -15, 15, -30, 30, -45, 45, -60, 60, -75, 75, -90, 90];"

MUTANTS = [
    ("turn over about the electrode axis (D19 literal)", "js", "const axis = turnOverAxis(upper);",
     'const axis = (upper.role === "rows") === ["bottom", "top"].includes(upper.tail.side) ? "x" : "y";', "orient"),
    ("no mirror in the placement", "js", 'if (flipAxis === "y") left = field[2] - (left + box[2]);', "", "orient"),
    ("stack order swapped", "js", 'const upper = boards.find(board => board.physical_side === "top"); const lower = boards.find(board => board.physical_side === "bottom");',
     'const upper = boards.find(board => board.physical_side === "bottom"); const lower = boards.find(board => board.physical_side === "top");', "orient"),
    ("engine-frame active region (old bug)", "js", 'const field = numbers(svg.getAttribute("data-active-region"));',
     'const field = numbers(svg.getAttribute("data-active-region")); if (field) field[1] = box[1] + box[3] - field[1] - field[3] + box[1];', "orient"),
    ("upper board shifted 0.1 mm", "js", "const [fieldW, fieldH] = [lowerPlace.field[2], lowerPlace.field[3]];",
     "upperPlace.left += 0.1; const [fieldW, fieldH] = [lowerPlace.field[2], lowerPlace.field[3]];", "orient"),
    ("pin-1 ring fixed at 1 mm", "js", "const radius = Math.max(PIN1_RING_MIN_MM, PIN1_RING_PX / scale);", "const radius = PIN1_RING_MIN_MM;", "orient"),
    # The stacked view's pin-1 rings (P5-diagonal-bus.md section 27.3: the stacked tails end together; 27.5: moved apart,
    # each still round its own triangle).
    ("stacked pin-1 rings not moved apart", "js", CHOSEN, "    const [, , top, bottom] = placed[0];", "part_stacked_pin1"),
    ("stacked pin-1 rings: the top one always stepped inward (d281bc4's)", "js", CHOSEN, "    const [, , top, bottom] = placed[1];", "part_stacked_pin1"),
    ("stacked pin-1 rings: only the top one moves (the 2 x 2's plan view then steps them off their triangles, 27.4's)", "js", SHARES,
     "      for (const [up, down] of [[1, 0]]) {", "part_stacked_pin1"),
    ("stacked pin-1 rings: moved apart along the line through them only (the 12 / 11.5 mm plan view's top ring under the caption)", "js",
     TURNS, "    const turns = [0];", "part_stacked_pin1"),
    ("stacked pin-1 rings in one colour", "css", ".pin1-ring.is-upper { stroke:#087e8b; }.pin1-ring.is-lower { stroke:#d7771f; }", "", "part_stacked_pin1"),
    # 27.8: both rings drawn above both boards (the bottom FPC's ring had lain under the top FPC's translucent face).
    ("stacked pin-1 rings drawn inside their boards, the bottom one under the top FPC's face (baf053c's)", "css",
     ".assembly-board .pin1-ring { visibility:hidden; }", ".pin1-overlay { display:none; }", "part_stacked_pin1"),
    # 27.9: each drawn as its ring lies on screen (61d450c drew it at the ring's box on screen: 1.28 times the ring in the
    # exploded view, the boards turned in their plane before the tilt).
    ("stacked pin-1 rings drawn at their rings' boxes on screen (61d450c's: 1.28 times the ring in the exploded view)", "js",
     "      const shape = projectedRing(ring) || {", "      const shape = null || {", "part_stacked_pin1"),
    ("the stacked view's notes at the layout grid's six decimals (1.893896 mm beside 1.500)", "js",
     "  const micrometres = number => round6(number).toFixed(3);", "  const micrometres = fixed;", "part_stacked_pin1"),
    ("no ring room around the 2D view box", "css", "height:430px; padding:12px;", "height:430px;", "orient"),
    ("flip-y drawn as rotateX", "css", ".assembly-board.flip-y .assembly-face { transform:rotateY(180deg); }",
     ".assembly-board.flip-y .assembly-face { transform:rotateX(180deg); }", "orient"),
    # The looks.
    ("Diagram the default look", "js", 'const LOOKS = ["photo", "diagram"];', 'const LOOKS = ["diagram", "photo"];', "part_looks"),
    ("view labels shown in the assembly", "css", ".assembly-board .view-label { display:none; }", "", "orient"),
    ("wheel always prevents default (scroll trap)", "js", "WHEEL_ZOOM_RATE), event.clientX, event.clientY) || event.ctrlKey) event.preventDefault();",
     "WHEEL_ZOOM_RATE), event.clientX, event.clientY) || true) event.preventDefault();", "part_zoom"),
    ("cross-field advice blocks Generate", "js", 'control.setCustomValidity(control.type === "text"',
     'control.setCustomValidity(crossFieldAdvice(control) || control.type === "text"', "part_nudges_and_advice"),
    ("no arrow-key nudge", "js", '["ArrowUp", "ArrowDown"].includes(event.key)', '["NoSuchKey"].includes(event.key)', "part_nudges_and_advice"),
    ("late export overwrites the newer status", "js", "else if (!shown()) setStatus(", "else if (false) setStatus(", "part_downloads_and_http"),
    ("derived layout carries one board", "js", 'units: "mm", boards: result.boards}', 'units: "mm", boards: result.boards.row}', "part_downloads_and_http"),
    ("downloads ignore the stale state", "js", "const downloadsReady = () => Boolean(state.result?.ok) && !state.busy && !isStale();",
     "const downloadsReady = () => Boolean(state.result?.ok) && !state.busy;", "part_stale"),
    ("oblique view not fitted", "js", "if (!board || !panel.getClientRects().length) return;\n    board.style.width = \"\";",
     "return;", "part_aria"),
    ("native spinner left on mm inputs", "css", "input.fine-step { appearance:textfield; -moz-appearance:textfield; }", "", "part_boot_and_limits"),
    ("manufacturing note not rendered (G/ui-order-note)", "js", "      renderOrderRequirements(data.profile.order_requirements);\n", "", "part_boot_and_limits"),
    ("review notes listed as order options", "js", '$("orderOptions").replaceChildren(...items.filter(entry => entry.kind === "order_option").map(item));',
     '$("orderOptions").replaceChildren(...items.map(item));', "part_boot_and_limits"),
    # The browser-only mutants of tools/mutation_check.py (F/*), which the stdlib suite cannot see.
    ("stale banner never shown (F/stale-banner)", "js", '$("staleBanner").hidden = !stale;', '$("staleBanner").hidden = true;', "part_stale"),
    ("turn-over axis swapped (F/turn-over-axis)", "js", 'return board.tail?.side === "left" || board.tail?.side === "right" ? "x" : "y";',
     'return board.tail?.side === "left" || board.tail?.side === "right" ? "y" : "x";', "orient"),
]


def main():
    selected = [m for m in MUTANTS if len(sys.argv) < 2 or any(arg in m[0] for arg in sys.argv[1:])]
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, kind, old, new, target in selected:
            source = APP if kind == "js" else CSS
            assert source.count(old) == 1, (name, source.count(old))
            body = source.replace(old, new)
            route = ("**/static/app.js", "text/javascript", body) if kind == "js" else ("**/static/styles.css", "text/css", body)
            rp.RESULTS.update({"pass": 0, "fail": 0, "failures": []})
            ui_checks.ROUTES[:] = [route]
            with contextlib.redirect_stdout(io.StringIO()):
                try:
                    if target == "orient":
                        page = ui_checks.new_page(browser)
                        orient.run_cases(page, ORIENT_CASES, shots=False)
                        page.close()
                    else:
                        getattr(ui_checks, target)(browser)
                except Exception as error:  # a broken page also counts as detected
                    rp.check(f"{target} crashed: {type(error).__name__}", False)
            failures = rp.RESULTS["failures"]
            print(f"{'KILLED  ' if failures else 'SURVIVED'} {name}: {len(failures)} failing checks; e.g. {failures[:2]}", flush=True)
        browser.close()


if __name__ == "__main__":
    main()
