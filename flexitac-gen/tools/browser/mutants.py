"""Discrimination check: serve mutated app.js/styles.css; the targeted checks must fail (KILLED).

The "cad" kind (the sensor on the part, 2026-11-05) serves a mutated web/cad/drape.js or web/cad/onpart.js (the review
of 2026-11-05; its look of 2026-11-05: the film, the contact shade, the edge bands, since the user's of 2026-11-05 the
film's own lamp; the look's fix round: a lost context's objects, an empty contact footprint, the shade along the stack's
edge; the user's decision of 2026-11-05: its home, camera up and keys the left figure's), or since the 3D view's look
of 2026-11-05 web/cad/viewer.js (the studio, the tone mapping, the lights, the markers, a drag's material, a lost
context's studio) to a part of cad_checks.py
(part_on_part, part_crank_fill, part_on_part_studio, part_on_part_patches, part_on_part_contact, part_view_look) in a
browser with WebGL (SwiftShader), web/cad/studio.js served with them: first,
for each part, the unmutated files through the same routes, which must pass every check (else that part's results are
INVALID), then each mutant; a run that crashes or never draws the figure is INVALID, not KILLED.
"""
from __future__ import annotations

import contextlib
import io
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # no __pycache__ next to the scripts
sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright.sync_api import sync_playwright  # noqa: E402

import cad_checks  # noqa: E402
import orient  # noqa: E402
import rp  # noqa: E402
import ui_checks  # noqa: E402

WEB = str(Path(__file__).resolve().parents[2] / "web")
APP = open(f"{WEB}/app.js", encoding="utf-8").read()
CSS = open(f"{WEB}/styles.css", encoding="utf-8").read()
DRAPE = open(f"{WEB}/cad/drape.js", encoding="utf-8").read()
ONPART = open(f"{WEB}/cad/onpart.js", encoding="utf-8").read()
VIEWER = open(f"{WEB}/cad/viewer.js", encoding="utf-8").read()
STUDIO = open(f"{WEB}/cad/studio.js", encoding="utf-8").read()
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
    ("stacked pin-1 rings: moved apart along the line through them only (the 12 / 11.5 mm plan view's rings off their triangles with the tails leaving left)", "js",
     TURNS, "    const turns = [0];", "part_stacked_pin1"),
    ("stacked pin-1 rings in one colour", "css", ".pin1-ring.is-upper { stroke:#087e8b; }.pin1-ring.is-lower { stroke:#d7771f; }", "", "part_stacked_pin1"),
    # 27.8: both rings drawn above both boards (the bottom FPC's ring had lain under the top FPC's translucent face).
    ("stacked pin-1 rings drawn inside their boards, the bottom one under the top FPC's face (baf053c's)", "css",
     ".assembly-board .pin1-ring { visibility:hidden; }", ".pin1-overlay { display:none; }", "part_stacked_pin1"),
    # 27.9: each drawn as its ring lies on screen (61d450c drew it at the ring's box on screen: 1.28 times the ring in the
    # exploded view, the boards turned in their plane before the tilt).
    ("stacked pin-1 rings drawn at their rings' boxes on screen (61d450c's: 1.28 times the ring in the exploded view)", "js",
     "      const shape = projectedRing(ring) || {", "      const shape = null || {", "part_stacked_pin1"),
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
    # The 3D views' light (app.js lightBoard, lightView; the user's request of 2026-11-05: the light of the sensor on the part
    # in every 3D view): off; the veils over their whole view box, not the outline; the shadows turning with the board as
    # before; the walls one colour whatever way they face.
    ("the 3D views' light off (the boards flat as before)", "js", '    if (!target || target.classList.contains("is-plan")) return;\n    const {tilt, spin} = orbitView(target);\n',
     '    return;\n    const {tilt, spin} = orbitView(target);\n', "part_view_light"),
    ("the light's veils over their whole view box, not clipped to the outline", "js",
     '      const d = rings.map(ring => `M${ring.map(([x, y]) => `${round6(x)} ${round6(y)}`).join("L")}Z`).join("");\n',
     '      const d = `M${box[0]} ${box[1]}h${box[2]}v${box[3]}h${-box[2]}Z`;\n', "part_view_light"),
    ("the shadows turning with the board again (their offset fixed in its plane)", "js",
     "    let [u, v] = Math.abs(ct) > 1e-3 ? [cs * dx + ss * dy / ct, -ss * dx + cs * dy / ct] : [0, 0];\n", "    let [u, v] = [0.033, 1.544];\n", "part_view_light"),
    ("the walls one colour whatever way they face", "css", "  stroke:color-mix(in srgb, var(--edge-paint) var(--wall-light,60%), #000); }",
     "  stroke:color-mix(in srgb, var(--edge-paint) 60%, #000); }", "part_view_light"),
    # The sensor on the part's geometry (web/cad/drape.js; tools/mutation_check.py's browser-only F/on-part-*).
    ("the top FPC laid on the part unmirrored (F/on-part-mirror)", "cad", "  const bx = isTop(art) ? ox + (Rx + Rw - sx) : ox + (sx - Rx);\n",
     "  const bx = isTop(art) ? ox + (sx - Rx) : ox + (sx - Rx);\n", "part_on_part"),
    ("the boards' art upside down on their sheets (F/on-part-texture-rows)", "cad", "  return [(sx - vx) / vw, 1 - (sy - vy) / vh];\n",
     "  return [(sx - vx) / vw, (sy - vy) / vh];\n", "part_on_part"),
    # Its review of 2026-11-05: the outlines' alpha test as coverage (onpart.js), the part framed whole (drape.js).
    ("the sheets' outlines in hard steps (F/on-part-coverage)", "cad", "function coverage(material) {\n  material.alphaToCoverage = true;\n",
     "function coverage(material) {\n  return material;\n  material.alphaToCoverage = true;\n", "part_on_part"),
    ("the crank's tip framed within 1.3 times the sheets' radius (F/on-part-framing)", "cad", "export const PART_FRAME_SHARE = 3;\n",
     "export const PART_FRAME_SHARE = 1.3;\n", "part_crank_fill"),
    # Its second review: the coverage's alpha kept from lowering what lies behind an outline (onpart.js).
    ("the pane seen through the outlines over the part (F/on-part-seams)", "cad", "  Object.assign(material, {blending: THREE.CustomBlending,",
     "  Object.assign(material, {blending: THREE.NormalBlending,", "part_on_part"),
    # Its look of 2026-11-05 (onpart.js): the film a satin sheet, the contact shade in Assembled only, the edge bands.
    ("the film a flat unlit black again (F/on-part-film-flat)", "cad",
     "coverage(new THREE.MeshPhysicalMaterial({color: new THREE.Color(...rgb), map, alphaTest: ALPHA_TEST, side: THREE.DoubleSide, ...film,\n"
     "    sheenColor: new THREE.Color(...sheenRGB)}))",
     "coverage(new THREE.MeshBasicMaterial({color: new THREE.Color(...rgb), map, alphaTest: ALPHA_TEST, side: THREE.DoubleSide}))", "part_on_part"),
    # The film's own lamp (onpart.js FILM_LAMP; the user's of 2026-11-05, 再调一下你说的黑色压阻膜): out, the film at the left
    # figure's home mirrors the room between the studio's softboxes, nearly a flat black (on_part_film's levels).
    ("the film's own lamp out: nearly a flat black at the left figure's home (F/on-part-film-unlit)", "cad",
     "const FILM_LAMP = {aim: 1.5, out: 0.3, intensity: 0.2};", "const FILM_LAMP = {aim: 1.5, out: 0.3, intensity: 0};", "part_on_part"),
    ("the contact shade never drawn (F/on-part-contact-never)", "cad", "strength: [0.85, 0.4], most: 0.85};", "strength: [0, 0], most: 0.85};", "part_on_part"),
    ("the contact shade drawn in Exploded too, once Assembled made it (M/web-on-part-contact-mode)", "cad",
     '    if (view.mode === "assembled" && view.contact && !view.shadeOff) contact', "    if (view.contact && !view.shadeOff) contact", "part_on_part"),
    ("the layers' edge bands not drawn (F/on-part-bands-off)", "cad", "    if (band?.geometry) {\n", "    if (false) {\n", "part_on_part"),
    # The look's fix round of 2026-11-05 (onpart.js; the catalogue's M/web-on-part-*, which the pixels and the console
    # catch as well): a lost context's objects disposed when it comes back, an empty contact footprint looked for at
    # every Assembled, the contact shade's core outside the footprint only.
    ("the lost context's studio disposed when it comes back (M/web-on-part-restore-dispose)", "cad",
     "    look.environment = studioFor(renderer);\n    clear({lost: true});\n",
     "    look.environment?.dispose();\n    look.environment = studioFor(renderer);\n    clear({lost: true});\n", "part_on_part_studio"),
    ("the lost context's sheets and part disposed when it comes back (M/web-on-part-restore-sheets)", "cad", "    clear({lost: true});\n", "    clear();\n",
     "part_on_part_studio"),
    ("a stack without a contact footprint looked for again at every Assembled (M/web-on-part-contact-none)", "cad",
     '    if (view.contact !== null || view.mode !== "assembled"', '    if (view.contact || view.mode !== "assembled"', "part_on_part_patches"),
    ("the contact shade's core outside the footprint only again: the WXAI sock's light line (M/web-on-part-contact-inner)", "cad",
     "Math.max(0, core[t] - Math.min(cover[t], inner[t]))", "Math.max(0, core[t] - cover[t])", "part_on_part_contact"),
    # The user's decision of 2026-11-05: the Exploded home the left figure's as it opens (cad_checks on_part_aligned and
    # part_on_part's turns; tools/mutation_check.py's M/web-on-part-home-spin, -camera-up and -keys).
    ("the sensor on the part's home turned the other way about the stack's normal: the spin's sign (M/web-on-part-home-spin)", "cad",
     "  return [Math.sin(spin) * Math.sin(tilt), -Math.cos(spin) * Math.sin(tilt), Math.cos(tilt)];\n",
     "  return [-Math.sin(spin) * Math.sin(tilt), -Math.cos(spin) * Math.sin(tilt), Math.cos(tilt)];\n", "part_on_part"),
    ("the sensor on the part's camera up the world's y again: the left figure's roll out of reach (M/web-on-part-camera-up)", "cad",
     "  camera.up.set(...HOME_UP);\n", "  camera.up.set(0, 1, 0);\n", "part_on_part"),
    ("the sensor on the part's arrow keys the other way from the left figure's (M/web-on-part-keys)", "cad",
     "    const turn = {ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1]}[event.key];\n",
     "    const turn = {ArrowLeft: [1, 0], ArrowRight: [-1, 0], ArrowUp: [0, 1], ArrowDown: [0, -1]}[event.key];\n", "part_on_part"),
    # The 3D view in the studio's light (viewer.js, 2026-11-05; the catalogue's M/web-view-*, and the studio off).
    ("the 3D view's studio off: its part matte under the lights alone", "cad", "    envMap: look.environment?.texture || null, side: THREE.DoubleSide,",
     "    envMap: null, side: THREE.DoubleSide,", "part_view_look"),
    ("the 3D view without the tone mapping (M/web-view-tone)", "cad", '  toneMap(renderer);\n  renderer.domElement.className = "cad-canvas";\n',
     '  renderer.domElement.className = "cad-canvas";\n', "part_view_look"),
    ("the 3D view's old lights, a hemisphere and a sun (M/web-view-own-lights)", "cad", "  camera.up.set(0, 0, 1);\n  const lights = studioLights(scene, camera);\n",
     "  camera.up.set(0, 0, 1);\n  scene.add(new THREE.HemisphereLight(0xffffff, 0x8899aa, 1.7));\n  const sun = new THREE.DirectionalLight(0xffffff, 1.3);\n"
     "  sun.position.set(0.3, 0.6, 1);\n  camera.add(sun);\n  scene.add(camera);\n  const lights = {place() {}, turn() {}};\n", "part_view_look"),
    ("the 3D view's markers tone mapped (M/web-view-markers-lit)", "cad", "const markerMaterial = parameters => new THREE.MeshBasicMaterial({...parameters, toneMapped: false});",
     "const markerMaterial = parameters => new THREE.MeshBasicMaterial({...parameters});", "part_view_look"),
    ("a drag's diffuse material left on the part after the drag", "cad", "    part.material = on ? dragMaterial : part.userData.look;\n",
     "    part.material = dragMaterial;\n", "part_view_look"),
    ("the 3D view's studio made again with each model (M/web-view-studio-per-model)", "cad", "    const mesh = new THREE.Mesh(geometry, partMaterial(look));\n",
     "    look.environment = studioFor(renderer);\n    const mesh = new THREE.Mesh(geometry, partMaterial(look));\n", "part_view_look"),
    ("the 3D view's studio not made again when a lost context comes back (M/web-view-restore-none)", "cad",
     "    look.environment = studioFor(renderer);\n    if (groups.mesh) groups.mesh.userData.look.envMap = look.environment?.texture || null;\n", "", "part_view_look"),
]
# The cad kind's files: each mutant's text is in exactly one of them.
CAD_FILES = {"**/static/cad/drape.js": DRAPE, "**/static/cad/onpart.js": ONPART, "**/static/cad/viewer.js": VIEWER, "**/static/cad/studio.js": STUDIO}


def cad_routes(old=None, new=None):
    """The cad kind's routes: every file of CAD_FILES served, ``old`` replaced by ``new`` in the one that holds it."""
    if old is not None:
        assert sum(body.count(old) for body in CAD_FILES.values()) == 1, old
    return [(route, "text/javascript", body.replace(old, new) if old is not None and old in body else body) for route, body in CAD_FILES.items()]


def run_cad(browser, target, routes):
    """cad_checks' ``target`` with ``routes`` (cad_routes) served: (failing checks, whether the run is valid)."""
    rp.RESULTS.update({"pass": 0, "fail": 0, "failures": []})
    cad_checks.ROUTES[:] = routes
    crashed = False
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            getattr(cad_checks, target)(browser)
        except Exception as error:  # noqa: BLE001 - a crash says nothing about the mutant here
            crashed = True
            rp.check(f"{target} crashed: {type(error).__name__}", False)
    cad_checks.ROUTES[:] = []
    failures = list(rp.RESULTS["failures"])
    return failures, not crashed and not any(name.startswith(cad_checks.ON_PART_DRAWN_CHECK) for name in failures)


def main():
    selected = [m for m in MUTANTS if len(sys.argv) < 2 or any(arg in m[0] for arg in sys.argv[1:])]
    with sync_playwright() as p:
        browser = p.chromium.launch()
        cad = [m for m in selected if m[1] == "cad"]
        if cad:
            webgl = p.chromium.launch(args=cad_checks.WEBGL_ARGS)
            cad_checks.SERVED = cad_checks.template_served()
            controls = {}
            for target in dict.fromkeys(m[4] for m in cad):
                failures, valid = run_cad(webgl, target, cad_routes())
                controls[target] = valid and not failures
                print(f"{'CONTROL ' if controls[target] else 'INVALID '} {target}: the cad files unmutated through the routes: {len(failures)} failing checks; "
                      f"e.g. {failures[:2]}", flush=True)
            for name, kind, old, new, target in cad:
                failures, valid = run_cad(webgl, target, cad_routes(old, new)) if controls[target] else ([], False)
                verdict = "INVALID " if not valid else "KILLED  " if failures else "SURVIVED"
                print(f"{verdict} {name}: {len(failures)} failing checks; e.g. {failures[:2]}", flush=True)
            webgl.close()
        for name, kind, old, new, target in selected:
            if kind == "cad":
                continue
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
