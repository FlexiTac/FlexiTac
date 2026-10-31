"""Repair check: everything in stage F except orientation/assembly (see orient.py), and the Row traces select of the
rectangular mode (P5-diagonal-bus.md section 18: the diagonal Row bus by default, the straight channel one choice away).

Each part opens a fresh page against a running app.py (rp.URL).
"""
from __future__ import annotations

import json
import math
import re
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True  # no __pycache__ next to the scripts
sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright.sync_api import sync_playwright  # noqa: E402

from rp import DONE, RECT_URL, SCRATCH, SHOTS, URL, api, check, pin1_shapes, pin1_strokes, stacked_pin1, summary, unfold, wait_until  # noqa: E402

DOWNLOADS = f"{SCRATCH}/downloads"
ALL_CONTROLS = ["name", "rows", "columns", "pitchX", "pitchY", "rowWidth", "columnWidth", "topTailLength", "bottomTailLength",
                "connectorSide", "rowLayer", "scanOrder", "rowPins", "columnPins"]
DOWNLOAD_SELECTORS = ['[data-download="design"]', '[data-download="layout"]', '[data-download="manifest"]',
                      '[data-export="project"]', '[data-export="top-gerber"]', '[data-export="bottom-gerber"]', '[data-export="easyeda-pro"]']
INJECTED = []  # console errors we caused on purpose (HTTP failures)


ROUTES = []  # (glob, content type, body) served instead of the real file in mutant runs


def _serve(content_type, body):
    def handler(route):
        route.fulfill(status=200, content_type=content_type, body=body)
    return handler


def new_page(browser, width=1600, height=1000, folded=False):
    context = browser.new_context(viewport={"width": width, "height": height}, accept_downloads=True)
    if not folded:
        unfold(context)
    for glob, content_type, body in ROUTES:
        context.route(glob, _serve(content_type, body))
    page = context.new_page()
    page.logs = []
    page.on("console", lambda m: page.logs.append((m.type, m.text)))
    page.on("pageerror", lambda e: page.logs.append(("pageerror", str(e))))
    return page


def settle(page, timeout=60):
    page.wait_for_timeout(60)
    wait_until(page, "() => (" + DONE[6:] + ") && !document.querySelector('#status').textContent.startsWith('Deriving')", timeout)
    page.wait_for_timeout(100)


def boot(page):
    page.goto(RECT_URL)
    settle(page)


def status(page):
    return page.inner_text("#status")


def downloads_disabled(page):
    return page.evaluate(f"() => {json.dumps(DOWNLOAD_SELECTORS)}.map(s => document.querySelector(s).disabled)")


def stale(page):
    return page.evaluate("() => !document.querySelector('#staleBanner').hidden && document.querySelector('#workbench').classList.contains('is-stale')")


def fixed(number):
    text = f"{round(number, 6):.6f}".rstrip("0")
    whole, _, fraction = text.partition(".")
    return f"{whole}.{fraction.ljust(3, '0')}"


def console_errors(page, allowed=()):
    return [entry for entry in page.logs if entry[0] in ("error", "pageerror") and not any(a in entry[1] for a in allowed)]


# ---------------------------------------------------------------------------

def part_boot_and_limits(browser):
    page = new_page(browser)
    bodies = []
    page.on("request", lambda r: bodies.append(json.loads(r.post_data)) if r.url.endswith("/api/generate") and r.method == "POST" else None)
    responses = []
    page.on("response", lambda r: responses.append(r.json()) if r.url.endswith("/api/generate") and r.request.method == "POST" else None)
    boot(page)
    body = bodies[0]; result = responses[0]
    check("boot payload carries schema_version, template_id and the nested connector section",
          body.get("schema_version") == "tactile-fpc-design/v1" and body.get("template_id") == "generic_matrix_v1"
          and body.get("connector") == {"row_pins": None, "column_pins": None}, json.dumps(body)[:200])
    check("boot build has no warnings (no W_SCHEMA_VERSION_DEFAULTED)", result["validation"]["warnings"] == [], result["validation"]["warnings"])
    _, default, _ = api("/api/default")
    _, api_result, _ = api("/api/generate?view=compact", default["design"])
    check("browser default build id equals the /api/default design's build id",
          result["manifest"]["build_id"] == api_result["manifest"]["build_id"], result["manifest"]["build_id"])
    limits = default["profile"]["limits"]
    mismatches = []
    for control in ALL_CONTROLS:
        info = page.evaluate("""id => { const e = document.getElementById(id); return {field: e.dataset.field, type: e.type, tag: e.tagName,
            min: e.getAttribute('min'), max: e.getAttribute('max'), step: e.getAttribute('step'), required: e.required,
            maxlength: e.maxLength, minlength: e.minLength, options: e.tagName === 'SELECT' ? [...e.options].map(o => o.value) : null}; }""", control)
        spec = limits[info["field"].split(" ")[0]]
        if info["type"] == "number":
            got = (float(info["min"]), float(info["max"]), float(info["step"]), info["required"])
            want = (spec["minimum"], spec["maximum"], spec["step"], not spec.get("nullable", False))
            if got != want:
                mismatches.append((control, got, want))
        elif info["tag"] == "INPUT":
            if (info["maxlength"], info["minlength"]) != (spec["max_length"], spec["min_length"]):
                mismatches.append((control, info["maxlength"], spec["max_length"]))
        elif control == "connectorSide" and info["options"] != spec["enum"]:
            mismatches.append((control, info["options"], spec["enum"]))
    check("form min/max/step/required/maxlength and the side options equal /api/default profile.limits", not mismatches, mismatches)
    # The manufacturing note: the profile's order requirements (ORDER_NOTES.txt), rendered from /api/default.
    requirements = default["profile"]["order_requirements"]
    shown = page.evaluate("""() => ({options: [...document.querySelectorAll('#orderOptions li')].map(li => li.textContent),
        notes: [...document.querySelectorAll('#orderNotes li')].map(li => li.textContent)})""")
    expected = {kind: [f"{r['topic']}: {r['requirement']}{r['reason']}" for r in requirements if r["kind"] == kind] for kind in ("order_option", "review_note")}
    check("the manufacturing note lists /api/default profile.order_requirements (order options, review notes, reasons)",
          shown["options"] == expected["order_option"] and shown["notes"] == expected["review_note"], shown)
    note = page.inner_text("#manufacturingNote")
    check("the note shows the approved order: 0.11 mm FPC, 1 oz copper, PI 0.225 mm, +/-0.05 mm outline tolerance, ENIG",
          all(part in note for part in ("0.11 mm FPC thickness", "Copper weight: 1 oz (0.035 mm)", "PI 0.225 mm",
                                        "Outline tolerance: +/-0.05 mm", "Surface finish: ENIG")), note[-600:])
    check("the review notes include the contact-zone thickness (about 0.285 mm, measure on delivery)",
          "Contact-zone thickness: the tail is about 0.285 mm thick at the contacts" in note, note[-600:])
    fine = page.evaluate("() => [...document.querySelectorAll('input.fine-step')].map(e => e.id + ':' + getComputedStyle(e).appearance)")
    check("mm inputs (step 1e-6) have no native spinner", sorted(f.split(":")[0] for f in fine) == sorted(
        ["pitchX", "pitchY", "rowWidth", "columnWidth", "topTailLength", "bottomTailLength", "traceWidth", "traceSpace"])
        and all(f.endswith(":textfield") for f in fine), fine)
    # The fan-out trace fields (2026-10-15): their hint names JLC's 1 oz minimum and the finger width,
    # and the locked-rules panel shows the bundle of the shown build.
    hint = page.inner_text("#traceHint")
    rules = default["profile"]["display_rules"]
    check("the trace hint names JLC's trace minimum and the gold-finger width from the display rules",
          rules["JLC trace minimum"] in hint and rules["Gold-finger traces"] in hint and "0.1016" in hint and "0.254" in hint, hint)
    bundle = page.inner_text('#lockedRules [data-rule="Bundle traces"]')
    check("the locked-rules panel shows the default bundle", bundle == rules["Bundle traces"], bundle)
    page.close()


def part_nudges_and_advice(browser):
    page = new_page(browser)
    boot(page)
    seq = []
    for keys in (["ArrowUp"] * 3, ["Shift+ArrowUp"], ["ArrowDown"], ["Shift+ArrowDown"] * 2):
        page.focus("#pitchX")
        for key in keys:
            page.keyboard.press(key)
        seq.append(page.input_value("#pitchX"))
    check("arrow keys nudge mm inputs by 0.05 mm, Shift by 1 mm (on the nudge grid)", seq == ["2.15", "3", "2.95", "1"], seq)
    check("a nudge marks the result stale", stale(page) and all(downloads_disabled(page)))
    page.fill("#columnWidth", "1.43"); page.focus("#columnWidth"); page.keyboard.press("ArrowUp")
    up = page.input_value("#columnWidth"); page.keyboard.press("ArrowDown"); page.keyboard.press("ArrowDown")
    check("nudges snap to the next multiple of 0.05 mm", up == "1.45" and page.input_value("#columnWidth") == "1.35", [up, page.input_value("#columnWidth")])
    page.fill("#pitchY", "0.6"); page.focus("#pitchY"); page.keyboard.press("ArrowDown")
    page.fill("#topTailLength", "79.99"); page.focus("#topTailLength"); page.keyboard.press("Shift+ArrowUp")
    check("nudges stay inside the profile limits", page.input_value("#pitchY") == "0.6" and page.input_value("#topTailLength") == "80",
          [page.input_value("#pitchY"), page.input_value("#topTailLength")])
    page.fill("#rows", "12"); page.focus("#rows"); page.keyboard.press("ArrowUp")
    check("integer inputs keep the native step of 1", page.input_value("#rows") == "13", page.input_value("#rows"))
    # The trace fields step by 1 mil (0.0254 mm), Shift by 4 mil, inside their limits.
    seq = []
    for keys in (["ArrowUp"], ["Shift+ArrowUp"], ["ArrowDown"], ["Shift+ArrowDown"] * 3):
        page.focus("#traceWidth")
        for key in keys:
            page.keyboard.press(key)
        seq.append(page.input_value("#traceWidth"))
    check("trace fields nudge by 1 mil, Shift by 4 mil, from 0.127 mm, down to JLC's 0.1016 mm", seq == ["0.1524", "0.2032", "0.1778", "0.1016"], seq)
    page.close()

    # Cross-field advice: shown at once, never blocks, replaced by the server's verdict.
    page = new_page(browser)
    sent = []
    page.on("request", lambda r: sent.append(r.url) if "/api/generate" in r.url else None)
    boot(page)
    page.fill("#columnWidth", "1.9")
    first = page.inner_text("#columnWidthMessage")
    check("electrode wider than pitch - 0.25 mm gets immediate advice", "At most 1.75" in first, first)
    page.wait_for_timeout(1200)  # live /api/validate
    live = page.inner_text("#columnWidthMessage")
    check("the live server verdict replaces the advice (E_ELECTRODE_GAP at the field)", "E_ELECTRODE_GAP" in live and "At most 1.75" not in live, live)
    count = len(sent)
    page.click("#generate"); settle(page)
    check("advice does not block Generate; the server rejects with the field error", len(sent) == count + 1
          and "E_ELECTRODE_GAP" in page.inner_text("#columnWidthMessage") and page.get_attribute("#columnWidth", "aria-invalid") == "true",
          status(page))
    page.fill("#columnWidth", "1.4"); page.fill("#columnPins", "8")
    pins = page.inner_text("#columnPinsMessage")
    check("connector pins below the channel count get immediate advice", "At least 32" in pins, pins)
    page.fill("#columnPins", ""); page.fill("#pitchX", "0.5")
    native = page.inner_text("#pitchXMessage")
    count = len(sent)
    page.click("#generate"); page.wait_for_timeout(300)
    check("a single-field limit (pitch 0.5 < 0.6) blocks Generate and focuses the field", "At least 0.6" in native and len(sent) == count
          and page.evaluate("() => document.activeElement.id") == "pitchX", [native, status(page)])
    page.close()

    # Advice derived from the limits is advisory: a wrong inference cannot refuse a valid design.
    page = new_page(browser)

    def tamper(route):
        response = route.fetch()
        data = response.json()
        for key in ("matrix.taxel_width_mm", "matrix.taxel_height_mm"):
            data["profile"]["limits"][key]["maximum"] = 9.0  # inferred gap becomes 1.0 mm instead of 0.25 mm
        route.fulfill(response=response, body=json.dumps(data))
    page.route("**/api/default", tamper)
    boot(page)
    page.fill("#columnWidth", "1.5")
    advice = page.inner_text("#columnWidthMessage")
    page.click("#generate"); settle(page)
    after = page.inner_text("#columnWidthMessage")
    check("with a wrongly inferred gap the advice shows, but Generate runs and the valid build is accepted",
          "At most 1" in advice and page.evaluate("() => document.querySelector('#status').classList.contains('is-ok')")
          and after.strip() == "" and page.get_attribute("#columnWidth", "aria-invalid") == "false", [advice, status(page), after])
    page.close()


def part_row_traces(browser):
    """The Row traces select in Rectangular mode (P5-diagonal-bus.md section 18): shown, Both by default (the diagonal
    Row bus, the generic template's default), sent with the form; Straight channel sends "channel" (no bus); an edit is
    a stale build.  The form's bounds follow the choice (section 20): the bus's rule set (CAD mode's: 64 columns, tails
    from 7.5 mm, its profile's badge), the straight channel's own (each limit's ``channel``: 32 columns, 7.0 mm)."""
    page = new_page(browser)
    bodies = []
    page.on("request", lambda r: bodies.append(json.loads(r.post_data)) if r.url.endswith("/api/generate") and r.method == "POST" else None)
    responses = []
    page.on("response", lambda r: responses.append(r.json()) if r.url.endswith("/api/generate") and r.request.method == "POST" else None)
    boot(page)
    options = page.evaluate("() => [...document.querySelectorAll('#rowSides option')].map(o => [o.value, o.textContent])")
    check("Rectangular mode shows the Row traces select, Both by default, its Straight channel the value channel",
          page.is_visible("#rowSides") and not page.is_disabled("#rowSides") and page.input_value("#rowSides") == "both"
          and [value for value, _ in options] == ["channel", "both", "left", "right"] and options[0][1] == "Straight channel"
          and page.is_visible("#rowSidesHint"), (page.is_visible("#rowSides"), page.input_value("#rowSides"), options))
    body, result = bodies[0], responses[0]
    legend = page.inner_text("#assemblyRowBus") if page.query_selector("#assemblyRowBus") else ""
    check("the boot build is the diagonal Row bus with both: sent with the form, row_bus in the manifest, the folded pins in the stacked view",
          body.get("routing") == {"row_sides": "both"} and result["manifest"].get("row_bus") == "diagonal-bus/11"
          and result["design"]["routing"]["row_sides"] == "both" and "folded" in legend, (body.get("routing"), result["manifest"].get("row_bus"), legend[:160]))
    _, default, _ = api("/api/default")
    check("/api/default's generic design names both", default["design"]["routing"].get("row_sides") == "both", default["design"]["routing"])
    first_id = status(page).split()[2]
    limits = default["profile"]["limits"]
    bounds = "() => ['columns', 'topTailLength', 'bottomTailLength'].map(id => [document.getElementById(id).min, document.getElementById(id).max])"
    # The generic template's bus is diagonal-bus/11 (CAD mode's rule set and construction, P5-diagonal-bus.md sections 20, 24,
    # 27 and 27.8).
    for choice, bus in (("channel", None), ("left", "diagonal-bus/11"), ("both", "diagonal-bus/11")):
        page.select_option("#rowSides", choice)
        page.wait_for_timeout(60)
        edited = stale(page) and all(downloads_disabled(page))
        shown = page.evaluate(bounds)
        columns, top, bottom = (limits[key] for key in ("matrix.columns", "tail.top_length_mm", "tail.bottom_length_mm"))
        if bus is None:
            want = [[str(columns["minimum"]), str(columns["channel"]["maximum"])],
                    [f"{top['channel']['minimum']:g}", f"{top['maximum']:g}"], [f"{bottom['channel']['minimum']:g}", f"{bottom['maximum']:g}"]]
        else:
            want = [[str(columns["minimum"]), str(columns["maximum"])], [f"{top['minimum']:g}", f"{top['maximum']:g}"],
                    [f"{bottom['minimum']:g}", f"{bottom['maximum']:g}"]]
        badge = page.inner_text("#profileBadge")
        check(f"Row traces {choice}: the form's column and tail bounds and the profile badge follow it (bus: 64 columns, tails from 7.5 mm; "
              "straight channel: 32, 7 mm)",
              shown == want and [float(v) for v in shown[0]] == [1.0, 32.0 if bus is None else 64.0]
              and float(shown[2][0]) == (7.0 if bus is None else 7.5)
              and badge == (default["profile"]["name"] if bus is None else default["profile"]["row_bus"]["name"]), (shown, want, badge))
        before = len(bodies)
        page.click("#regenerate" if page.is_visible("#regenerate") else "#generate"); settle(page)
        sent, built = (bodies[-1], responses[-1]) if len(bodies) > before else ({}, {})
        legend = page.inner_text("#assemblyRowBus") if page.query_selector("#assemblyRowBus") else ""
        _, expected, _ = api("/api/generate?view=compact", dict(default["design"], routing=dict(default["design"]["routing"], row_sides=choice)))
        check(f"Row traces {choice}: an edit is stale; Generate sends routing.row_sides {choice} and builds the API's build for it",
              edited and (sent.get("routing") or {}).get("row_sides") == choice and built.get("ok") is True
              and built.get("manifest", {}).get("row_bus") == bus and built["manifest"]["build_id"] == expected["manifest"]["build_id"]
              and not stale(page) and ((bus is None) == (legend == "")) and (choice != "left" or "the left side" in legend),
              (edited, sent.get("routing"), built.get("manifest", {}).get("row_bus"), legend[:120]))
    check("Both again gives the boot build back", status(page).split()[2] == first_id, (status(page), first_id))
    check("row traces part: no console errors", not console_errors(page), console_errors(page))
    page.close()


PIN1_HOME = """() => document.querySelectorAll('#stackedPreview .pin1-ring').forEach(ring => {
    if (ring.dataset.dx) { ring.setAttribute('cx', ring.dataset.x); ring.setAttribute('cy', ring.dataset.y); } })"""


def part_stacked_pin1(browser):
    """The stacked view's pin-1 rings (P5-diagonal-bus.md section 27.3: the user's tails centred and ending together, so
    the two boards' pin-1 contacts may lie side by side at one height), in the exploded view (the default) and the plan
    view, on small fields (a 2 x 2's pin-1 contacts 0.5 mm apart), with both and one side, the form's former default
    tails (12 and 7.5 mm), equal ones (12 and 12, the default since section 27.7; 7.5 and 7.5) and nearly equal ones (12
    and 11.5: the triangles apart on a slant), the tails leaving left, and the default 12 x 32 (first as the form opens:
    both tails 12 mm, ending together): the top FPC's teal ring and the bottom FPC's orange ring
    never overlap, neither takes in the other board's pin-1 triangle and each still rounds its own (its centre within
    one ring radius of the triangle's: section 27.5, where the plan view's rings had stepped a ring diameter off, one
    beside the tail's end marking nothing), so each marks its own pad; the rings move only where, round their triangles,
    the two would clash (moved back there by the check, a resize places them again); the legend names each ring; the
    stacked view's note has both tails centred on the field, ending together where their lengths are equal, else the
    longer named, one side's traces fanning in under the field into the centred Row tail, and no length finer than its
    three decimals.  At 1440 px wide the plan view's caption reaches under a narrow board's tail end, so the rings of the
    nearly equal tails part on a slant off the line through them."""
    page = new_page(browser, width=1440)
    boot(page)
    # The default build as the form opens (the user's decision of 2026-10-27, section 27.7: the rectangular mode's tails 12
    # / 12 mm): both tails 12 mm, the stacked note's tails ending together (the Row tail 4.500 mm longer before), and its
    # pin-1 rings right in both views.
    form = page.evaluate("() => ['topTailLength', 'bottomTailLength'].map(id => document.getElementById(id).value)")
    note = page.inner_text("#assemblyRowBus") if page.query_selector("#assemblyRowBus") else ""
    check("the default build as the form opens: both tails 12 mm, ending together in the stacked view's note (no tail longer)",
          form == ["12", "12"] and "both centred on the field, ending together, their contacts in line" in note and "longer" not in note, (form, note))
    for view in ("exploded", "plan"):
        page.click(f'[data-assembly-mode="{view}"]'); page.wait_for_timeout(250)
        problems, rings = stacked_pin1(page)
        check(f"the default build as the form opens, {view} view: the two boards' pin-1 rings differ in colour, do not overlap, neither "
              "takes in the other board's triangle and each rounds its own", status(page).startswith("Valid build") and problems == [], (problems, rings))
        covered, counts = pin1_strokes(page)
        check(f"the default build as the form opens, {view} view: both pin-1 rings drawn above both boards (each ring's stroke its own "
              "colour over the other board)", covered == [], (covered, counts))
        shaped, shapes = pin1_shapes(page)
        check(f"the default build as the form opens, {view} view: each pin-1 ring drawn as its board's ring lies on screen (each semi-axis "
              "within 5 %, the centre within 1 px: section 27.9)", shaped == [], (shaped, shapes))
    page.click('[data-assembly-mode="exploded"]'); page.wait_for_timeout(100)
    cases = [(rows, columns, sides, tails, "bottom") for rows, columns in ((2, 2), (3, 2), (2, 3), (3, 3)) for sides in ("both", "left")
             for tails in (("12", "7.5"), ("12", "12"), ("7.5", "7.5"))]
    cases += [(2, 2, "both", ("12", "11.5"), "bottom"), (2, 2, "both", ("12", "12"), "left")]
    cases += [(12, 32, sides, tails, "bottom") for sides in ("both", "left") for tails in (("12", "7.5"), ("12", "12"))]
    seen_over = {"exploded": 0, "plan": 0}  # views where the bottom FPC's ring crosses the top FPC (the stroke check bites)
    for rows, columns, sides, (top, bottom), exit_side in cases:
        name = f"{rows} x {columns} {sides}, tails {top} / {bottom} mm" + ("" if exit_side == "bottom" else f", leaving {exit_side}")
        page.fill("#rows", str(rows)); page.fill("#columns", str(columns)); page.select_option("#rowSides", sides)
        page.fill("#topTailLength", top); page.fill("#bottomTailLength", bottom); page.select_option("#connectorSide", exit_side)
        page.click("#regenerate" if page.is_visible("#regenerate") else "#generate"); settle(page)
        for view in ("exploded", "plan"):
            page.click(f'[data-assembly-mode="{view}"]'); page.wait_for_timeout(250)
            problems, rings = stacked_pin1(page)
            check(f"stacked pin 1, {name}, {view} view: the two boards' pin-1 rings differ in colour, do not overlap, neither takes in the "
                  "other board's triangle and each rounds its own", status(page).startswith("Valid build") and problems == [], (problems, rings))
            page.evaluate(PIN1_HOME)
            home, _ = stacked_pin1(page, margin=2.0)
            steps = sorted((ring["layer"], ring["step"]) for ring in rings)
            check(f"stacked pin 1, {name}, {view} view: the rings move only where the two round their triangles would clash",
                  (home == []) == (steps == [("lower", "0,0"), ("upper", "0,0")]), (home, steps))
            page.evaluate("() => window.dispatchEvent(new Event('resize'))"); page.wait_for_timeout(100)
            again, placed = stacked_pin1(page)
            check(f"stacked pin 1, {name}, {view} view: a resize places the rings again", again == [] and [(ring["x"], ring["y"]) for ring in placed]
                  == [(ring["x"], ring["y"]) for ring in rings], (again, placed, rings))
            # Both rings above both boards (P5-diagonal-bus.md section 27.8: the bottom FPC's ring had lain under the top FPC's
            # translucent face, its stroke broken over the gold fingers of the top FPC's tail).
            covered, counts = pin1_strokes(page)
            check(f"stacked pin 1, {name}, {view} view: both pin-1 rings drawn above both boards (each ring's stroke its own colour "
                  "over the other board)", covered == [], (covered, counts))
            # Each drawn as its board's ring lies on screen (section 27.9: at the ring's box, 1.28 times the ring in the exploded view).
            shaped, shapes = pin1_shapes(page)
            check(f"stacked pin 1, {name}, {view} view: each pin-1 ring drawn as its board's ring lies on screen (each semi-axis within 5 %, "
                  "the centre within 1 px)", shaped == [], (shaped, shapes))
            seen_over[view] += counts.get("lower", (0, 0))[0] > 0
            if view == "exploded" and (rows, columns, sides, top, bottom, exit_side) == (12, 32, "both", "12", "12", "bottom"):
                # Seen from straight above (the exploded view turned to tilt 0, arrow keys) the boards' 96 px apart still
                # overlap, so the bottom FPC's ring crosses the top FPC there too and the stroke check bites in this view
                # (not on a 2 x 2: beside the coin for scale it sits left of the camera's axis, the top FPC drawn off it).
                page.focus("#stackedPreview")
                for _ in range(12):
                    page.keyboard.press("ArrowDown")
                page.wait_for_timeout(250)
                covered, counts = pin1_strokes(page)
                check(f"stacked pin 1, {name}, exploded view from straight above: both pin-1 rings drawn above both boards",
                      covered == [] and page.evaluate("() => document.getElementById('stackedPreview').dataset.orbit") == "0,-20", (covered, counts))
                seen_over[view] += counts.get("lower", (0, 0))[0] > 0
                page.keyboard.press("0"); page.wait_for_timeout(200)
            if (rows, columns, sides, exit_side) == (2, 2, "both", "bottom") and top in ("12",):
                page.locator(".stacked-review").screenshot(path=f"{SHOTS}/stacked_pin1_2x2_both_{top}_{bottom}_{view}.png")
        # The two boards' keys in the legend, its notes folded under "About this view" (#assemblyNotes).
        legend = page.inner_text("#assemblyLegend") + "\n" + page.inner_text("#assemblyNotes")
        check(f"stacked pin 1, {name}: the legend names the top FPC's teal ring and the bottom FPC's orange ring and says how they part",
              "(teal ring)" in legend and "(orange ring)" in legend and "Each pin-1 ring rounds its board's triangle past the tail's end" in legend
              and "each still round its own triangle's centre" in legend, legend)
        note = page.inner_text("#assemblyRowBus") if page.query_selector("#assemblyRowBus") else ""
        ends = "ending together, their contacts in line" if top == bottom else f"the Row tail {float(top) - float(bottom):.3f} mm longer"
        check(f"stacked pin 1, {name}: the stacked view's note has both tails centred on the field, {ends}",
              f"both centred on the field, {ends}" in note and (sides == "both" or "fan in under the field into the Row tail centred under it" in note), note)
        finer = re.findall(r"\d\.\d{4,}", legend)
        check(f"stacked pin 1, {name}: the stacked view's notes give every length to three decimals (the shared outline's depth too)",
              finer == [] and re.search(r"tail roots \(\d+\.\d{3} mm below the taxel field\)", note), (finer, note))
        page.click('[data-assembly-mode="exploded"]'); page.wait_for_timeout(100)
    page.select_option("#connectorSide", "bottom")
    check("stacked pin 1: the stroke check saw the bottom FPC's ring cross the top FPC in both views", all(seen_over.values()), seen_over)
    check("stacked pin 1 part: no console errors", not console_errors(page), console_errors(page))
    page.close()


def part_stale(browser):
    page = new_page(browser)
    boot(page)
    first_id = status(page).split()[2]
    edits = {"name": "Tactile FPC 12x32 b", "rows": "11", "columns": "31", "pitchX": "2.1", "pitchY": "2.1", "rowWidth": "1.3",
             "columnWidth": "1.3", "topTailLength": "13", "bottomTailLength": "8", "connectorSide": "left", "rowLayer": "bottom",
             "scanOrder": "reverse", "rowPins": "16", "columnPins": "40"}
    bad = []
    for control, new in edits.items():
        tag = page.eval_on_selector(f"#{control}", "e => e.tagName")
        old = page.input_value(f"#{control}")
        (page.select_option if tag == "SELECT" else page.fill)(f"#{control}", new)
        page.wait_for_timeout(30)
        on = stale(page) and all(downloads_disabled(page)) and first_id in page.inner_text("#staleBanner")
        (page.select_option if tag == "SELECT" else page.fill)(f"#{control}", old)
        page.wait_for_timeout(30)
        off = not stale(page) and not any(downloads_disabled(page))
        if not (on and off):
            bad.append((control, on, off))
    check("editing each of the 14 controls shows the stale banner and disables all 7 downloads; reverting restores them", not bad, bad)
    page.fill("#rows", "10")
    page.wait_for_timeout(1300)
    banner = page.inner_text("#staleBanner")
    page.click("#regenerate"); settle(page)
    new_id = status(page).split()[2]
    check("Regenerate clears the stale state and the live 'would become' id equals the new build",
          not stale(page) and not any(downloads_disabled(page)) and new_id != first_id and new_id in banner, [banner[:160], new_id])
    page.screenshot(path=f"{SHOTS}/stale_cleared.png")
    # an edit while a build runs leaves the arriving result stale
    held = []
    page.route("**/api/generate", lambda route: held.append(route))
    page.fill("#rows", "9"); page.click("#generate"); page.wait_for_timeout(200)
    during = all(downloads_disabled(page)) and page.is_disabled("#generate")
    page.fill("#rows", "8")
    held[0].continue_(); page.unroute("**/api/generate"); settle(page)
    check("downloads and Generate are disabled during a build; an edit made meanwhile leaves the result stale",
          during and stale(page) and all(downloads_disabled(page)), page.inner_text("#staleBanner")[:120])
    page.screenshot(path=f"{SHOTS}/stale_banner.png")
    page.close()


def part_zoom(browser):
    page = new_page(browser)
    boot(page)
    page.evaluate("() => window.scrollTo(0, 0)")
    page.evaluate("() => document.querySelector('#rowPreview').scrollIntoView({block: 'center'})")
    page.wait_for_timeout(100)
    base = page.get_attribute("#rowPreview svg", "viewBox")
    box = page.evaluate("() => { const b = document.querySelector('#rowPreview').getBoundingClientRect(); return [b.left, b.top, b.width, b.height]; }")
    cx, cy = round(box[0] + box[2] * 0.3), round(box[1] + box[3] * 0.55)
    to_user = "([x, y]) => { const m = document.querySelector('#rowPreview svg').getScreenCTM().inverse(); const p = new DOMPoint(x, y).matrixTransform(m); return [p.x, p.y]; }"
    before = page.evaluate(to_user, [cx, cy])
    page.mouse.move(cx, cy)
    y0 = page.evaluate("() => window.scrollY")
    page.mouse.wheel(0, -400); page.wait_for_timeout(120)
    after = page.evaluate(to_user, [cx, cy])
    drift = math.hypot(after[0] - before[0], after[1] - before[1])
    zoomed = page.get_attribute("#rowPreview svg", "viewBox")
    check("wheel up zooms about the cursor (point under the cursor fixed) and does not scroll the page",
          zoomed != base and drift < 1e-3 and page.evaluate("() => window.scrollY") == y0, f"drift {drift:.6f} mm; {base} -> {zoomed}")
    ring = page.evaluate("""() => { const svg = document.querySelector('#rowPreview svg'); const r = svg.querySelector('.pin1-ring');
        const s = svg.getScreenCTM().a; return [+r.getAttribute('r'), s, r.getBoundingClientRect().width]; }""")
    check("the pin-1 ring keeps a screen radius of 9 px (but at least 1 mm) after zooming",
          abs(ring[0] - max(1, 9 / ring[1])) < 1e-5 and abs(ring[2] - 2 * ring[0] * ring[1]) < 1.0, ring)
    vb = [float(v) for v in zoomed.split()]
    scale = page.evaluate("() => document.querySelector('#rowPreview svg').getScreenCTM().a")
    page.mouse.move(cx, cy); page.mouse.down(); page.mouse.move(cx + 100, cy + 60, steps=5); page.mouse.up()
    panned = [float(v) for v in page.get_attribute("#rowPreview svg", "viewBox").split()]
    check("drag pans the view by the drag distance", abs((vb[0] - panned[0]) * scale - 100) < 0.5 and abs((vb[1] - panned[1]) * scale - 60) < 0.5,
          f"dx {(vb[0] - panned[0]) * scale:.2f}px dy {(vb[1] - panned[1]) * scale:.2f}px")
    page.click("#rowZoomTools [data-zoom=reset]")
    check("Reset restores the fit view", page.get_attribute("#rowPreview svg", "viewBox") == base)
    page.click("#rowZoomTools [data-zoom=in]"); page.click("#rowZoomTools [data-zoom=in]")
    page.dblclick("#rowPreview")
    check("double-click restores the fit view", page.get_attribute("#rowPreview svg", "viewBox") == base)
    page.focus("#rowPreview"); page.keyboard.press("+"); page.keyboard.press("ArrowRight")
    keyed = page.get_attribute("#rowPreview svg", "viewBox")
    page.keyboard.press("0")
    check("keyboard + / arrows / 0 zoom, pan and reset the focused pane", keyed != base and page.get_attribute("#rowPreview svg", "viewBox") == base)
    for _ in range(30):
        page.click("#rowZoomTools [data-zoom=in]")
    level = page.inner_text("#rowZoomLevel")
    check("zoom is capped at 400x", level.startswith("400.0×"), level)
    page.click("#rowZoomTools [data-zoom=reset]")
    # the wheel at fit view scrolls the page (no scroll trap); ctrl+wheel never zooms the page
    page.evaluate("() => window.scrollTo(0, 200)"); page.wait_for_timeout(80)
    box = page.evaluate("() => { const b = document.querySelector('#rowPreview').getBoundingClientRect(); return [b.left + b.width / 2, b.top + b.height / 2]; }")
    page.mouse.move(round(box[0]), round(box[1]))
    y1 = page.evaluate("() => window.scrollY")
    for _ in range(3):
        page.mouse.wheel(0, 300); page.wait_for_timeout(60)
    y2 = page.evaluate("() => window.scrollY")
    check("wheel down over a preview at fit view scrolls the page and leaves the view unchanged",
          y2 > y1 and page.get_attribute("#rowPreview svg", "viewBox") == base, f"scrollY {y1} -> {y2}")
    prevented = page.evaluate("""() => { const pane = document.querySelector('#rowPreview'); const b = pane.getBoundingClientRect();
        const e = new WheelEvent('wheel', {deltaY: 120, ctrlKey: true, cancelable: true, bubbles: true, clientX: b.left + 50, clientY: b.top + 50});
        return !pane.dispatchEvent(e); }""")
    check("ctrl+wheel (pinch) over a preview is consumed even at a zoom limit", prevented)
    # the column pane at its own fit view: ring inside the pane at three widths
    page.close()
    for width in (1600, 1280, 900, 420):
        page = new_page(browser, width=width)
        boot(page)
        clips = []
        for side in ("bottom", "top", "left", "right"):
            page.select_option("#connectorSide", side); page.click("#generate"); settle(page)
            for key in ("row", "column"):
                r = page.evaluate("""key => { const pane = document.getElementById(key + 'Preview'); pane.scrollIntoView({block: 'center'});
                    const p = pane.getBoundingClientRect(); const g = pane.querySelector('.pin1-ring').getBoundingClientRect();
                    return [p.left - g.left, p.top - g.top, g.right - p.right, g.bottom - p.bottom, g.width]; }""", key)
                clips.append((side, key, round(max(r[:4] + [0]), 2), round(r[4], 1)))
        worst = max(c[2] for c in clips)
        check(f"viewport {width}px: every 2D pin-1 ring is inside its pane for all sides", worst <= 0 and min(c[3] for c in clips) >= 17, clips)
        overflow = page.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
        check(f"viewport {width}px: no horizontal page overflow", overflow <= 0, f"{overflow}px")
        page.close()
    # large board: ring stays visible at fit view
    page = new_page(browser)
    boot(page)
    page.fill("#rows", "40"); page.fill("#columns", "32"); page.fill("#pitchX", "6"); page.fill("#pitchY", "5"); page.click("#generate"); settle(page)
    big = page.evaluate("""() => ['row', 'column'].map(key => { const pane = document.getElementById(key + 'Preview'); const svg = pane.querySelector('svg');
        const m = svg.querySelector('.pin1-marker').getBoundingClientRect(); const g = svg.querySelector('.pin1-ring').getBoundingClientRect();
        const p = pane.getBoundingClientRect();
        return {scale: svg.getScreenCTM().a, marker: Math.max(m.width, m.height), ring: g.width, inside: g.left >= p.left && g.right <= p.right && g.top >= p.top && g.bottom <= p.bottom}; })""")
    check("40x32 at 6/5 mm (about 1.3 px/mm): the pin-1 ring is 18 px across and inside the pane although the marker is about 1 px",
          status(page).startswith("Valid build") and all(b["ring"] >= 17 and b["inside"] for b in big), big)
    page.locator(".previews").screenshot(path=f"{SHOTS}/large_board_previews.png")
    page.close()


def part_drc_and_failures(browser):
    page = new_page(browser)
    seen = []
    page.on("response", lambda r: seen.append(r.json()) if r.url.endswith("/api/generate") and r.request.method == "POST" else None)
    boot(page)
    for design in ({}, {"rows": "20", "columns": "17", "pitchX": "2.5"}):
        if design:
            for k, v in design.items():
                page.fill(f"#{k}", v)
            page.click("#generate"); settle(page)
        result = seen[-1]
        bad = []
        for key in ("row", "column"):
            checks = result["boards"][key]["verification"]["checks"]
            rows = page.evaluate("""key => [...document.querySelectorAll('#drc-' + key + ' tbody tr')].map(tr => ({rule: tr.dataset.rule,
                cells: [...tr.children].map(td => td.innerText)}))""", key)
            got = {r["rule"]: r["cells"] for r in rows}
            if set(got) != set(checks) | {"registration"}:
                bad.append((key, "rules", sorted(set(got) ^ (set(checks) | {"registration"}))))
            for rule, record in checks.items():
                cells = got.get(rule)
                if not cells:
                    continue
                measured = record["measured_mm"]
                if measured is None:
                    want = "—" if record["required_mm"] is None else "no pair within reach"
                    ok = cells[1].strip() == want
                else:
                    ok = fixed(measured) in cells[1] or (rule in ("outline_simple", "connectivity") and cells[1].strip() == str(round(measured)))
                finger = record.get("finger_section")
                if finger and finger["measured_mm"] is not None:
                    # route_route_clearance also lists the tail pieces' finger-section gap and its rule
                    ok = ok and f"{fixed(finger['measured_mm'])} mm tail pieces" in cells[1] and f"≥ {fixed(finger['required_mm'])} mm tail pieces" in cells[2]
                verdict = cells[3].split()[0]
                if not ok or verdict != ("PASS" if record["passed"] else "FAIL"):
                    bad.append((key, rule, cells, measured, record["passed"]))
        check(f"DRC panel lists every rule of both boards with its measured value and pass/fail, the tail pieces' finger section too ({result['manifest']['build_id']})", not bad, bad[:4])
    # a DRC failure (injected) keeps the failing geometry and marks the row
    def fail_one(route):
        response = route.fetch(); data = response.json()
        rec = data["boards"]["column"]["verification"]["checks"]["route_route_clearance"]
        rec.update({"measured_mm": 0.15, "passed": False, "violation_count": 3})
        data["boards"]["column"]["verification"]["all_checks_passed"] = False
        data["ok"] = False
        data["validation"]["errors"].append({"code": "E_DRC_ROUTE_CLEARANCE", "message": "injected", "field": "boards.column.route_route_clearance"})
        route.fulfill(response=response, body=json.dumps(data))
    page.route("**/api/generate", fail_one)
    page.fill("#rows", "12"); page.fill("#columns", "32"); page.fill("#pitchX", "2"); page.click("#generate"); settle(page)
    page.unroute("**/api/generate")
    row = page.evaluate("() => { const tr = document.querySelector('#drc-column tr[data-rule=route_route_clearance]'); return [tr.className, tr.innerText]; }")
    check("an injected DRC failure shows FAIL with the measured value, the card is marked, downloads are disabled",
          row[0] == "is-fail" and "0.150 mm" in row[1] and "FAIL" in row[1] and "3 violations" in row[1]
          and page.evaluate("() => document.querySelector('#columnCard').classList.contains('has-drc-failure')") and all(downloads_disabled(page)), row)
    page.screenshot(path=f"{SHOTS}/drc_failure.png", full_page=True)
    # failures clear previous previews
    cases = [("json500", lambda r: r.fulfill(status=500, content_type="application/json", body=json.dumps({"ok": False, "code": "E_INTERNAL", "error": "boom"})), "E_INTERNAL"),
             ("html502", lambda r: r.fulfill(status=502, content_type="text/html", body="<h1>bad gateway</h1>"), "HTTP_502"),
             ("abort", lambda r: r.abort(), "E_NETWORK"),
             ("contract", lambda r: r.fulfill(status=200, content_type="application/json", body="{}"), "E_CLIENT_CONTRACT")]
    for name, handler, code in cases:
        page.click("#generate"); settle(page)  # a good build first
        page.route("**/api/generate", handler)
        page.fill("#rows", "13" if name != "json500" else "14")
        page.click("#generate"); settle(page)
        page.unroute("**/api/generate")
        INJECTED.append(name)
        cleared = page.evaluate("""() => ['rowPreview', 'columnPreview', 'rowPreview3d', 'columnPreview3d', 'stackedPreview', 'drcTables']
            .every(id => !document.getElementById(id).querySelector('svg, table'))""")
        check(f"failed generation ({name}) clears previews, assembly and DRC and shows {code}",
              cleared and code in status(page) and code in page.inner_text("#summary") and all(downloads_disabled(page)) and not stale(page), status(page)[:120])
        page.fill("#rows", "12")
    page.screenshot(path=f"{SHOTS}/failure_cleared.png")
    page.close()


def part_aria(browser):
    page = new_page(browser)
    boot(page)
    attrs = page.evaluate("""() => [...document.querySelectorAll('[role=tab]')].map(t => {
        const panel = document.getElementById(t.getAttribute('aria-controls'));
        return [t.id, t.getAttribute('aria-selected'), t.tabIndex, panel.getAttribute('role'), panel.getAttribute('aria-labelledby') === t.id, panel.hidden]; })""")
    ok = all(a[3] == "tabpanel" and a[4] and ((a[1] == "true") == (a[2] == 0) == (not a[5])) for a in attrs)
    check("tabs: aria-selected, roving tabindex, aria-controls -> tabpanel with aria-labelledby, inactive panel hidden", ok, attrs)
    page.focus("#rowTab2d"); page.keyboard.press("ArrowRight")
    s1 = page.evaluate("() => [document.activeElement.id, document.querySelector('#rowTab3d').getAttribute('aria-selected'), document.querySelector('#rowPreview').hidden]")
    page.keyboard.press("ArrowRight")
    s2 = page.evaluate("() => document.activeElement.id")
    page.keyboard.press("End"); s3 = page.evaluate("() => document.activeElement.id")
    page.keyboard.press("Home"); s4 = page.evaluate("() => document.activeElement.id")
    page.keyboard.press("ArrowLeft"); s5 = page.evaluate("() => document.activeElement.id")
    check("keyboard: ArrowRight selects/focuses the next tab (wrapping), End/Home/ArrowLeft work",
          s1 == ["rowTab3d", "true", True] and s2 == "rowTab2d" and s3 == "rowTab3d" and s4 == "rowTab2d" and s5 == "rowTab3d", [s1, s2, s3, s4, s5])
    labels = page.evaluate("() => [...document.querySelectorAll('svg[aria-label]')].map(s => s.getAttribute('aria-label'))")
    check("the six SVG copies have distinct aria-labels", len(labels) == 6 and len(set(labels)) == 6, labels)
    texts = page.evaluate("() => document.body.innerText")
    check("stale texts are gone (Phase 2 gating, Flexible 3D, '1 lanes')", "Phase 2" not in texts and "Flexible" not in texts and " 1 lanes" not in texts)
    # oblique view fits its pane (rigid tilt) for wide and tall boards
    cdp = page.context.new_cdp_session(page); cdp.send("DOM.enable"); cdp.send("Runtime.enable")
    for rows, cols in ((12, 32), (1, 32), (64, 1), (64, 32), (1, 1)):
        page.click("#rowTab2d"); page.click("#columnTab2d")
        page.fill("#rows", str(rows)); page.fill("#columns", str(cols)); page.click("#generate"); settle(page)
        for key in ("row", "column"):
            page.click(f"#{key}Tab3d"); page.wait_for_timeout(120)
            pane = page.evaluate(f"() => {{ const b = document.getElementById('{key}Preview3d').getBoundingClientRect(); return [b.left, b.top, b.right, b.bottom]; }}")
            # The board's outline and its coin for scale (fitOblique fits the two together: beside a 24.26 mm quarter a
            # 1 x 1 board is small, as it is).
            spans = []
            for selector in (f"#{key}Preview3d polygon.outline", f"#{key}Preview3d .coin-layer-top"):
                obj = cdp.send("Runtime.evaluate", {"expression": f"document.querySelector('{selector}')"})["result"]["objectId"]
                quads = cdp.send("DOM.getContentQuads", {"objectId": obj})["quads"]
                spans.append(([q[i] for q in quads for i in range(0, 8, 2)], [q[i] for q in quads for i in range(1, 8, 2)]))
            xs = spans[0][0] + spans[1][0]; ys = spans[0][1] + spans[1][1]
            clip = max(pane[0] - min(xs), pane[1] - min(ys), max(xs) - pane[2], max(ys) - pane[3], 0)
            span = max(max(xs) - min(xs), max(ys) - min(ys)); own = max(max(spans[0][0]) - min(spans[0][0]), max(spans[0][1]) - min(spans[0][1]))
            check(f"{rows}x{cols} {key}: oblique outline and coin inside the pane and not tiny (the two over 150 px, the outline over 60 px)",
                  clip < 1 and span > 150 and own > 60, f"overflow {clip:.1f}px span {span:.0f}px outline {own:.0f}px")
            if rows == 1 and cols == 32 and key == "column":
                page.locator("#columnCard").screenshot(path=f"{SHOTS}/oblique_1x32_column.png")
    page.close()


def part_downloads_and_http(browser):
    page = new_page(browser)
    exports = {}
    page.on("response", lambda r: exports.__setitem__(r.url.rsplit("/", 1)[-1], dict(r.headers)) if "/api/export/" in r.url and r.status == 200 else None)
    results = []
    page.on("response", lambda r: results.append(r.json()) if r.url.endswith("/api/generate") and r.request.method == "POST" else None)
    boot(page)
    result = results[-1]; build = result["manifest"]["build_id"]
    names = {}
    for selector in DOWNLOAD_SELECTORS:
        with page.expect_download() as info:
            page.click(selector)
        download = info.value
        path = f"{DOWNLOADS}/{download.suggested_filename}"
        download.save_as(path)
        names[selector] = (download.suggested_filename, path)
        settle(page)
    check("every download name starts with the build id", all(n.startswith(build + "-") for n, _ in names.values()), [n for n, _ in names.values()])
    for kind, selector in (("project", '[data-export="project"]'), ("top-gerber", '[data-export="top-gerber"]'), ("bottom-gerber", '[data-export="bottom-gerber"]'),
                           ("easyeda-pro", '[data-export="easyeda-pro"]')):
        header = exports[kind].get("content-disposition", "")
        check(f"{kind} ZIP saved under the Content-Disposition name", names[selector][0] in header, [names[selector][0], header])
    with zipfile.ZipFile(names['[data-export="easyeda-pro"]'][1]) as projects:
        members = projects.namelist()
    roles = {board["physical_side"]: board["role"] for board in result["boards"].values()}
    check("the EasyEDA Pro download is {build}-easyeda-pro.zip with one .epro2 per board and README_EASYEDA.txt",
          names['[data-export="easyeda-pro"]'][0] == f"{build}-easyeda-pro.zip"
          and sorted(member for member in members if member.endswith(".epro2")) == sorted(f"easyeda_pro/{build}-{side}-{roles[side]}.epro2" for side in ("top", "bottom"))
          and "easyeda_pro/README_EASYEDA.txt" in members, [names['[data-export="easyeda-pro"]'][0], members])
    with open(names['[data-download="layout"]'][1], encoding="utf-8") as handle:
        layout = json.load(handle)
    check("derived-layout download equals {format: manifest.layout_format, units: 'mm', boards} (key order kept)",
          list(layout) == ["format", "units", "boards"] and layout == {"format": result["manifest"]["layout_format"], "units": "mm", "boards": result["boards"]})
    with zipfile.ZipFile(names['[data-export="project"]'][1]) as bundle:
        member = json.loads(bundle.read("derived-layout.json"))
    check("and it equals the review bundle's derived-layout.json in value", member == layout)
    with open(names['[data-download="design"]'][1], encoding="utf-8") as handle:
        design = json.load(handle)
    with open(names['[data-download="manifest"]'][1], encoding="utf-8") as handle:
        manifest = json.load(handle)
    check("design and manifest downloads equal result.design and result.manifest", design == result["design"] and manifest == result["manifest"])
    # 503 twice then pass-through; 408 once
    count = {"n": 0}

    def busy(route):
        count["n"] += 1
        if count["n"] <= 2:
            route.fulfill(status=503, headers={"Retry-After": "1"}, content_type="application/json", body=json.dumps({"ok": False, "code": "E_HTTP_BUSY", "error": "busy"}))
        else:
            route.continue_()
    page.route("**/api/generate", busy)
    page.fill("#rows", "11"); page.click("#generate"); settle(page)
    page.unroute("**/api/generate")
    INJECTED.append("503")
    check("503 E_HTTP_BUSY with Retry-After is retried until the build succeeds", count["n"] == 3 and status(page).startswith("Valid build"), [count["n"], status(page)[:80]])
    count["n"] = 0

    def timeout(route):
        count["n"] += 1
        if count["n"] == 1:
            route.fulfill(status=408, content_type="application/json", body=json.dumps({"ok": False, "code": "E_HTTP_TIMEOUT", "error": "slow"}))
        else:
            route.continue_()
    page.route("**/api/generate", timeout)
    page.fill("#rows", "12"); page.click("#generate"); settle(page)
    page.unroute("**/api/generate")
    INJECTED.append("408")
    check("408 E_HTTP_TIMEOUT is retried once", count["n"] == 2 and status(page).startswith("Valid build"), count["n"])
    page.route("**/api/export/top-gerber", lambda r: r.fulfill(status=422, content_type="application/json", body=json.dumps(
        {"ok": False, "code": "E_EXPORT_BLOCKED", "error": "blocked", "validation": {"errors": [{"code": "E_ROWS_RANGE", "message": "rows", "field": "matrix.rows"}], "warnings": []}})))
    page.click('[data-export="top-gerber"]'); page.wait_for_timeout(500)
    page.unroute("**/api/export/top-gerber")
    INJECTED.append("422")
    check("422 E_EXPORT_BLOCKED shows its code and puts its validation into the summary",
          "Export failed: E_EXPORT_BLOCKED" in status(page) and "E_ROWS_RANGE" in page.inner_text("#summary"), status(page)[:100])
    # a late export does not overwrite the status of a newer build
    page.click("#generate"); settle(page)
    old = status(page).split()[2]
    held = []
    page.route("**/api/export/project", lambda route: held.append(route))
    page.click('[data-export="project"]'); page.wait_for_timeout(300)
    page.fill("#rows", "10"); page.click("#generate"); settle(page)
    new = status(page).split()[2]
    with page.expect_download() as info:
        held[0].continue_()
    page.unroute("**/api/export/project"); page.wait_for_timeout(400)
    final = status(page)
    check("an export finishing after a regenerate names the previous build and keeps the new build's note",
          info.value.suggested_filename.startswith(old) and "previous build " + old in final and new in final
          and new in page.inner_text("#downloadNote"), final)
    # field mapping of server errors (aliases, role mapping, alias values)
    def rewrite(route):
        response = route.fetch(); data = response.json()
        data["ok"] = False
        data["validation"]["errors"] = [
            {"code": "E_TAIL_SIDE", "message": "side", "field": "connector_side"},
            {"code": "E_ROLE_MAPPING", "message": "roles", "field": "role_mapping.top"},
            {"code": "E_CHANNEL_ORDER", "message": "order", "field": "scan_order"},
            {"code": "E_ROWS_RANGE", "message": "rows", "field": "row_num"},
            {"code": "E_CONNECTOR_PINS", "message": "pins", "field": "connector.column_pins"},
        ]
        data["validation"]["normalization"]["aliases_applied"] = [{"alias": "row_num", "field": "matrix.rows"}]
        for key in data["boards"]:
            data["boards"][key].pop("svg", None)
        route.fulfill(response=response, body=json.dumps(data))
    page.route("**/api/generate", rewrite)
    page.click("#generate"); settle(page)
    page.unroute("**/api/generate")
    marked = page.evaluate("() => ['connectorSide', 'rowLayer', 'scanOrder', 'rows', 'columnPins'].map(id => document.getElementById(id).getAttribute('aria-invalid'))")
    check("server errors map to inputs by field path (alias paths, role_mapping.top, aliases_applied, nested connector)", marked == ["true"] * 5, marked)
    page.click("#summary .field-link >> nth=3")
    check("summary entries focus their input", page.evaluate("() => document.activeElement.id") == "rows", page.evaluate("() => document.activeElement.id"))
    errors = console_errors(page, allowed=("status of 503", "status of 408", "status of 422"))
    check("no unexpected console errors (downloads/HTTP part)", not errors, errors)
    page.close()


SHOWN = """(ids) => ids.map(id => { const node = document.getElementById(id); return [id, Boolean(node && node.checkVisibility())]; })"""
BASIC_CONTROLS = ["name", "rows", "columns", "pitchX", "pitchY", "rowWidth", "columnWidth", "topTailLength", "bottomTailLength", "connectorSide", "generate"]
ADVANCED_CONTROLS = ["rowLayer", "scanOrder", "rowPins", "columnPins", "traceWidth", "traceSpace", "rowSides", "lockedRules", "profileBadge"]
FOLDS = ["formAdvanced", "assemblyMore", "drcPanel", "manufacturingNote"]


def flip_a_check(route):
    """The real /api/generate reply with the Row FPC's first DRC rule failing (a failing build the UI must show)."""
    response = route.fetch()
    body = response.json()
    checks = body.get("boards", {}).get("row", {}).get("verification", {}).get("checks", {})
    if checks:
        first = next(iter(checks.values()))
        first["passed"] = False
        first["violation_count"] = 1
    route.fulfill(response=response, json=body)


def part_clean_interface(browser):
    """The rectangular mode as it opens, folded (no unfold()): the basic sensor and tail controls and Generate in sight,
    the rest under Advanced; the header without its old eyebrow and profile badge; a clean pass without the summary box,
    the design checks one line ("all N checks pass") and folded, the stacked view's notes and the ordering notes folded,
    every download button in sight; a failing check opens the design checks listing only the failing rules, "Show all
    checks" the rest."""
    page = new_page(browser, width=1440, folded=True)
    boot(page)
    shown = dict(page.evaluate(SHOWN, BASIC_CONTROLS + ADVANCED_CONTROLS))
    check("clean: the basic controls are in sight", all(shown[name] for name in BASIC_CONTROLS), shown)
    check("clean: the advanced controls are folded under Advanced", not any(shown[name] for name in ADVANCED_CONTROLS), shown)
    folds = page.evaluate("(ids) => ids.map(id => [id, document.getElementById(id).open])", FOLDS)
    check("clean: Advanced, the stacked view's notes, the design checks and the ordering notes start folded", not any(open_ for _, open_ in folds), folds)
    page.click("#formAdvanced > summary"); page.wait_for_timeout(100)
    opened = dict(page.evaluate(SHOWN, ADVANCED_CONTROLS))
    check("clean: opening Advanced shows its controls", all(opened.values()), opened)
    header = page.inner_text(".masthead")
    check("clean: the header holds the title, its line on FlexiTac and the mode switch only",
          "LOCAL" not in header and "Generic Matrix" not in header and "FlexiTac-Gen" in header, header)
    # The user's requests of 2026-10-30: the title FlexiTac-Gen with a line on FlexiTac (the paper, the website), the mode
    # switch larger and right after them, its modes "Rectangular" and "Gen by Surface"; the page never says "CAD".
    title = page.evaluate("""() => { const block = document.querySelector('.masthead-title'); const m = document.getElementById('modePicker');
        const [a, b] = [block.getBoundingClientRect(), m.getBoundingClientRect()]; const span = m.querySelector('span');
        return {title: document.title, h1: block.querySelector('h1').textContent, next: block.nextElementSibling === m, gap: b.left - a.right,
                middle: Math.abs((a.top + a.bottom) / 2 - (b.top + b.bottom) / 2), height: b.height, font: parseFloat(getComputedStyle(span).fontSize),
                modes: [...m.querySelectorAll('span')].map(s => s.textContent), line: block.querySelector('.masthead-tagline').textContent.replace(/\\s+/g, ' ').trim(),
                links: [...block.querySelectorAll('a')].map(a => [a.textContent, a.href, a.target, a.rel])}; }""")
    check("clean: the title is FlexiTac-Gen (page and tab), the mode switch right after it (beside it, under 48 px off) and large "
          "(at least 40 px tall, 16 px text), its modes Rectangular and Gen by Surface",
          title["title"] == title["h1"] == "FlexiTac-Gen" and title["next"] and 0 <= title["gap"] < 48 and title["middle"] < 6
          and title["height"] >= 40 and title["font"] >= 16 and title["modes"] == ["Rectangular", "Gen by Surface"], title)
    check("clean: the line under the title links FlexiTac to its paper and the FlexiTac website, each in a new tab",
          title["line"] == "A customizer for FlexiTac sensors. For assembly instructions and applications, see the FlexiTac website."
          and title["links"] == [["FlexiTac", "https://arxiv.org/abs/2604.28156", "_blank", "noopener noreferrer"],
                                 ["FlexiTac website", "https://flexitac.github.io/", "_blank", "noopener noreferrer"]], title)
    words = page.evaluate("""() => [document.title, document.body.innerText, ...[...document.querySelectorAll('[title], [aria-label], [placeholder]')]
        .flatMap(node => ['title', 'aria-label', 'placeholder'].map(name => node.getAttribute(name) || ''))].filter(text => /\\bCAD\\b/i.test(text))""")
    check("clean: the Rectangular mode's page never says CAD (its text in sight, the tab, tooltips and labels)", words == [], [word[:200] for word in words])
    total = page.inner_text("#drcTotal")
    check("clean: a clean pass shows no summary box, the status line and the design checks' one line",
          status(page).startswith("Valid build") and not page.is_visible("#summary") and re.fullmatch(r"✓ all \d+ checks pass", total), (status(page), total))
    buttons = page.evaluate("() => [...document.querySelectorAll('[data-download], [data-export]')].map(b => b.checkVisibility() && !b.disabled)")
    check("clean: every download button is in sight and enabled", len(buttons) == 7 and all(buttons), buttons)
    # The two Gerber ZIPs first and set off (the user's request of 2026-10-30): filled, bold, taller than the others.
    order = page.evaluate("""() => [...document.querySelectorAll('.download-actions button')].map(b => { const s = getComputedStyle(b);
        return [b.textContent.trim(), Number(s.fontWeight), s.backgroundColor, Math.round(b.getBoundingClientRect().height)]; })""")
    check("clean: the Top and Bottom FPC Gerber ZIPs come first among the downloads, filled, bold and taller than the others",
          [name for name, *_ in order[:2]] == ["Top FPC Gerber ZIP", "Bottom FPC Gerber ZIP"] and all(weight >= 800 for _, weight, _, _ in order[:2])
          and all(fill != "rgb(255, 255, 255)" for _, _, fill, _ in order[:2]) and all(fill == "rgb(255, 255, 255)" for _, _, fill, _ in order[2:])
          and min(height for *_, height in order[:2]) > max(height for *_, height in order[2:]), order)
    check("clean: the stacked view's keys in sight, its notes folded", page.is_visible(".assembly-key.upper-key") and not page.is_visible("#assemblyRowBus"),
          page.inner_text("#assemblyLegend"))
    page.set_viewport_size({"width": 900, "height": 1000}); page.wait_for_timeout(200)
    overflow = page.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
    check("clean: no horizontal page overflow at 900 px", overflow <= 0, f"{overflow}px")
    page.set_viewport_size({"width": 1440, "height": 1000}); page.wait_for_timeout(100)
    page.route("**/api/generate", flip_a_check)
    page.fill("#rows", "11"); page.click("#regenerate" if page.is_visible("#regenerate") else "#generate"); settle(page)
    failing = page.evaluate("""() => { const panel = document.getElementById('drcPanel');
        const rows = [...panel.querySelectorAll('tbody tr')];
        return [panel.open, document.getElementById('drcTotal').textContent, rows.filter(r => r.checkVisibility()).map(r => r.className),
                document.getElementById('drcShowAll').checkVisibility()]; }""")
    check("clean: a failing check opens the design checks, listing only the failing rule, with Show all checks",
          failing[0] is True and failing[1].startswith("1 of ") and failing[2] == ["is-fail"] and failing[3] is True, failing)
    page.click("#drcShowAll"); page.wait_for_timeout(100)
    every = page.evaluate("() => [...document.querySelectorAll('#drcPanel tbody tr')].filter(r => !r.checkVisibility()).length")
    check("clean: Show all checks lists every rule", every == 0 and not page.is_visible("#drcShowAll"), every)
    page.unroute("**/api/generate")
    check("clean part: no console errors", not console_errors(page), console_errors(page))
    page.close()


# The look, its pressed buttons, then the outline's fill and the ENIG's display in the 2D preview, the oblique view and the
# stacked view's lower board.
LOOK_STATE = """() => { const svgs = ['#rowPreview svg', '#rowCard .oblique-board svg', '#stackedPreview .assembly-board.is-lower svg'].map(s => document.querySelector(s));
    return [document.body.dataset.look, [...document.querySelectorAll('button[data-look]')].filter(b => b.getAttribute('aria-pressed') === 'true').map(b => b.dataset.look),
            svgs.map(svg => [getComputedStyle(svg.querySelector('.outline')).fill, getComputedStyle(svg.querySelector('.lk-gold')).display])]; }"""


def part_looks(browser):
    """The looks (app.js setLook): Photo by default (the outline the photo's open PI #df8401 under the coverlay, the look's
    extra layers shown) in the 2D preview, the oblique view and the stacked view's boards; Diagram the server SVG's own
    colours (the extra layers hidden); the choice kept across a reload; in Photo the exploded view's pin-1 rings placed and
    drawn as in Diagram."""
    page = new_page(browser, width=1440)
    boot(page)
    look = page.evaluate(LOOK_STATE)
    check("looks: Photo by default, its button pressed, the outline the photo's open PI and the ENIG shown in every view",
          look[0] == "photo" and look[1] == ["photo"] and all(view == ["rgb(223, 132, 1)", "inline"] for view in look[2]), look)
    page.click('button[data-look="diagram"]'); page.wait_for_timeout(200)
    diagram = page.evaluate(LOOK_STATE)
    check("looks: Diagram gives the server SVG's colours and hides the look's layers in every view",
          diagram[0] == "diagram" and diagram[1] == ["diagram"] and all(view == ["rgb(244, 215, 161)", "none"] for view in diagram[2]), diagram)
    page.reload(); settle(page)
    kept = page.evaluate(LOOK_STATE)
    check("looks: the choice is kept across a reload", kept[0] == "diagram" and kept[1] == ["diagram"], kept)
    page.click('button[data-look="photo"]'); page.wait_for_timeout(200)
    check("looks: back to Photo", page.evaluate(LOOK_STATE)[0] == "photo")
    page.evaluate("() => document.querySelector('#stackedPreview').scrollIntoView({block: 'center'})"); page.wait_for_timeout(200)
    mode = page.evaluate("() => document.getElementById('stackedPreview').dataset.mode")
    check("looks: the stacked view opens in Exploded 3D", mode == "exploded", mode)
    problems, rings = stacked_pin1(page)
    check("looks: in Photo the two boards' pin-1 rings differ in colour, do not overlap, neither takes in the other board's triangle and each rounds its own",
          problems == [], (problems, rings))
    shaped, shapes = pin1_shapes(page)
    check("looks: in Photo each pin-1 ring drawn as its board's ring lies on screen", shaped == [], (shaped, shapes))
    page.locator(".stacked-review").screenshot(path=f"{SHOTS}/stacked_exploded_photo.png")
    check("looks part: no console errors", not console_errors(page), console_errors(page))
    page.close()


ORBIT_STATE = """() => { const view = document.getElementById('stackedPreview');
    return [view.dataset.orbit || '', getComputedStyle(view.querySelector('.assembly-camera')).transform, document.getElementById('orbitHint').hidden]; }"""


def part_stacked_orbit(browser):
    """The exploded view turns with the mouse (app.js attachOrbit): a drag across turns the stack in its plane and a drag
    down tilts it toward the view from above (0.4 degrees a pixel), the tilt held between straight above and from under
    the stack; the pin-1 rings drawn on the boards as they now lie and placed again once the drag ends; the arrow keys
    turn it by 5 degrees and 0 or a double click sets it back to 57 / -20 degrees; the angles held across a new design;
    the plan view keeps still and hides the hint."""
    page = new_page(browser, width=1440)
    boot(page)
    page.evaluate("() => document.querySelector('#stackedPreview').scrollIntoView({block: 'center'})")
    home = page.evaluate(ORBIT_STATE)
    box = page.locator("#stackedPreview").bounding_box()
    x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    page.mouse.move(x, y); page.mouse.down(); page.mouse.move(x + 60, y + 25, steps=6); page.mouse.move(x + 120, y + 50, steps=6); page.mouse.up()
    page.wait_for_timeout(150)
    turned = page.evaluate(ORBIT_STATE)
    check("orbit: a drag 120 px right and 50 px down turns the exploded view to tilt 37, spin -68 degrees (the hint shown)",
          home[0] == "" and turned[0] == "37,-68" and turned[1] != home[1] and turned[2] is False, (home, turned))
    problems, rings = stacked_pin1(page)
    check("orbit: after the drag the two pin-1 rings are placed again, apart, each round its own triangle",
          problems == [], (problems, rings))
    shaped, shapes = pin1_shapes(page)
    check("orbit: after the drag each pin-1 ring is drawn as its board's ring lies on screen", shaped == [], (shaped, shapes))
    page.mouse.move(x, y); page.mouse.down(); page.mouse.move(x, y - 400, steps=8); page.mouse.up(); page.wait_for_timeout(150)
    low = page.evaluate(ORBIT_STATE)[0]
    for _ in range(2):
        page.mouse.move(x, y); page.mouse.down(); page.mouse.move(x, y + 400, steps=8); page.mouse.up()
    page.wait_for_timeout(150)
    high = page.evaluate(ORBIT_STATE)[0]
    check("orbit: the tilt is held between 0 (straight above) and 180 degrees (from under the stack)", low == "180,-68" and high == "0,-68", (low, high))
    page.focus("#stackedPreview"); page.keyboard.press("ArrowLeft"); page.keyboard.press("ArrowUp"); page.wait_for_timeout(150)
    keys = page.evaluate(ORBIT_STATE)[0]
    page.keyboard.press("0"); page.wait_for_timeout(150)
    reset = page.evaluate(ORBIT_STATE)
    check("orbit: ArrowLeft and ArrowUp turn it by 5 degrees, 0 sets it back to 57 / -20 (the view as it opened)",
          keys == "5,-63" and reset[0] == "57,-20" and reset[1] == home[1], (keys, reset, home))
    page.mouse.move(x, y); page.mouse.down(); page.mouse.move(x - 50, y, steps=5); page.mouse.up(); page.wait_for_timeout(150)
    page.fill("#rows", "8"); page.click("#regenerate" if page.is_visible("#regenerate") else "#generate"); settle(page)
    kept = page.evaluate(ORBIT_STATE)
    check("orbit: the angles hold across a new design", kept[0] == "57,0" and status(page).startswith("Valid build"), kept)
    page.evaluate("() => document.querySelector('#stackedPreview').scrollIntoView({block: 'center'})")
    box = page.locator("#stackedPreview").bounding_box()
    x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    page.mouse.dblclick(x, y); page.wait_for_timeout(150)
    check("orbit: a double click sets it back to 57 / -20", page.evaluate(ORBIT_STATE)[0] == "57,-20", page.evaluate(ORBIT_STATE))
    page.click('[data-assembly-mode="plan"]'); page.wait_for_timeout(200)
    before = page.evaluate(ORBIT_STATE)
    page.mouse.move(x, y); page.mouse.down(); page.mouse.move(x + 100, y + 100, steps=5); page.mouse.up(); page.wait_for_timeout(150)
    after = page.evaluate(ORBIT_STATE)
    check("orbit: the plan view keeps still under a drag and hides the hint", before == after and after[1] == "none" and after[2] is True, (before, after))
    page.click('[data-assembly-mode="exploded"]'); page.wait_for_timeout(150)
    check("orbit part: no console errors", not console_errors(page), console_errors(page))
    page.close()


SIDE_AT_CENTRE = """(selector) => { const node = document.querySelector(selector); const box = node.getBoundingClientRect();
    const hit = document.elementFromPoint(box.left + box.width / 2, box.top + box.height / 2);
    return hit ? (hit.closest('.board-back-face') ? 'back' : hit.closest('svg') ? 'front' : 'none') : 'none'; }"""


def part_two_sided(browser):
    """The 3D views draw each single-sided FPC's two sides (app.js boardBackSvg, backFace): its copper side where that
    faces the camera, else its polyimide with the copper seen through it, the stiffener outermost and no coverlay window
    or ENIG: the stacked view's top FPC (turned over, copper down) shows its polyimide from above and the bottom FPC its
    copper; seen from under the stack the bottom FPC shows its polyimide.  The board cards' oblique views turn with the
    mouse as the stacked view does (0.4 degrees a pixel, double click back to 56 / -22 degrees), each board showing its
    other side once turned over."""
    page = new_page(browser, width=1440, height=1000)
    boot(page)
    page.evaluate("() => document.querySelector('#stackedPreview').scrollIntoView({block: 'center'})"); page.wait_for_timeout(200)
    backs = page.evaluate("""() => [...document.querySelectorAll('#stackedPreview .assembly-board')].map(board => {
        const back = board.querySelector('.board-back-face svg');
        return [board.classList.contains('is-upper') ? 'upper' : 'lower', Boolean(back), back ? back.querySelectorAll('.opening, .pin1-marker, .view-label').length : -1,
                back ? back.getAttribute('aria-hidden') : null]; })""")
    check("two sides: each stacked board has its polyimide side, without coverlay windows, pin-1 marker or label, hidden from assistive tech",
          sorted(backs) == [["lower", True, 0, "true"], ["upper", True, 0, "true"]], backs)
    upper, lower = page.evaluate(SIDE_AT_CENTRE, "#stackedPreview .assembly-board.is-upper"), page.evaluate(SIDE_AT_CENTRE, "#stackedPreview .assembly-board.is-lower")
    check("two sides: from above the turned-over top FPC shows its polyimide side", upper == "back", (upper, lower))
    box = page.locator("#stackedPreview").bounding_box(); x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    page.mouse.move(x, y); page.mouse.down(); page.mouse.move(x, y - 260, steps=8); page.mouse.up(); page.wait_for_timeout(300)
    below = page.evaluate(SIDE_AT_CENTRE, "#stackedPreview .assembly-board.is-lower")
    check("two sides: from under the stack the bottom FPC shows its polyimide side", below == "back", below)
    page.dblclick("#stackedPreview"); page.wait_for_timeout(200)
    page.click("#rowTab3d"); page.wait_for_timeout(200)
    page.evaluate("() => document.querySelector('#rowCard').scrollIntoView({block: 'center'})"); page.wait_for_timeout(200)
    home = page.evaluate(SIDE_AT_CENTRE, "#rowCard .oblique-board")
    pane = page.locator("#rowPreview3d").bounding_box(); px, py = pane["x"] + pane["width"] / 2, pane["y"] + pane["height"] / 2
    page.mouse.move(px, py); page.mouse.down(); page.mouse.move(px + 150, py - 250, steps=8); page.mouse.up(); page.wait_for_timeout(400)
    turned = page.evaluate("() => document.getElementById('rowPreview3d').dataset.orbit")
    side = page.evaluate(SIDE_AT_CENTRE, "#rowCard .oblique-board")
    check("two sides: the Row FPC's oblique view turns with the mouse (to tilt 156, spin -82) and then shows its polyimide side",
          home == "front" and turned == "156,-82" and side == "back", (home, turned, side))
    page.dblclick("#rowPreview3d"); page.wait_for_timeout(300)
    check("two sides: a double click sets the oblique view back to 56 / -22 degrees, its copper side in front",
          page.evaluate("() => document.getElementById('rowPreview3d').dataset.orbit") == "56,-22" and page.evaluate(SIDE_AT_CENTRE, "#rowCard .oblique-board") == "front")
    check("two sides part: no console errors", not console_errors(page), console_errors(page))
    page.close()


# The page names its files relative to itself, so the static site also works under a subpath.
COIN_HREF = "static/vendor/coin/us-quarter-obverse.jpg"
COIN_2D = r"""(selector) => { const svg = document.querySelector(selector); const coin = svg && svg.querySelector(':scope > .coin-ref');
    if (!coin) return null;
    const board = svg.querySelector(':scope > g[transform]'); const kids = [...svg.children];
    const [x, y, w, h] = svg.getAttribute('viewBox').trim().split(/\s+/).map(Number);
    const photo = coin.querySelector('image.coin-photo'); const box = photo.getBBox();
    const [cx, cy, r] = [box.x + box.width / 2, box.y + box.height / 2, box.width / 2];
    const m = board.transform.baseVal.consolidate().matrix; let clear = Infinity; let inside = false;
    for (const polygon of board.querySelectorAll(':scope > .outline')) {
      const v = polygon.getAttribute('points').trim().split(/[\s,]+/).map(Number); const p = [];
      for (let i = 0; i + 1 < v.length; i += 2) p.push([m.a * v[i] + m.c * v[i + 1] + m.e, m.b * v[i] + m.d * v[i + 1] + m.f]);
      for (let i = 0, j = p.length - 1; i < p.length; j = i, i += 1) {
        const [[x0, y0], [x1, y1]] = [p[j], p[i]]; const [dx, dy] = [x1 - x0, y1 - y0];
        if ((y1 > cy) !== (y0 > cy) && cx < x0 + (cy - y0) * dx / dy) inside = !inside;
        const t = Math.max(0, Math.min(1, ((cx - x0) * dx + (cy - y0) * dy) / (dx * dx + dy * dy)));
        clear = Math.min(clear, Math.hypot(x0 + t * dx - cx, y0 + t * dy - cy) - r);
      }
    }
    const outline = board.querySelector('.outline');
    return {r: +r.toFixed(3), right: +(x + w - cx - r).toFixed(3), bottom: +(y + h - cy - r).toFixed(3), under: kids.indexOf(coin) < kids.indexOf(board), placed: coin.querySelectorAll('[transform]').length,
            clear: +clear.toFixed(3), inside, href: photo.getAttribute('href'), clip: photo.getAttribute('clip-path'),
            ratio: photo.getBoundingClientRect().width / outline.getBoundingClientRect().width, outlineMm: outline.getBBox().width * Math.hypot(m.a, m.b)}; }"""
# A 3D view's coin: its layers, how far below the boards its plane lies and its face above it (CSS px, from the computed
# transforms' m43), its gleam's angle and the view's spin, and what lies on top at its face's centre and at eight points
# half way to its projected edge.
COIN_3D = r"""(scope) => { const plane = document.querySelector(`${scope} .coin-plane`); if (!plane) return null;
    const z = node => new DOMMatrixReadOnly(getComputedStyle(node).transform === 'none' ? undefined : getComputedStyle(node).transform).m43;
    const layers = [...plane.children].map(n => n.getAttribute('class').replace('coin-layer coin-layer-', ''));
    const top = plane.querySelector('.coin-layer-top'); const box = top.getBoundingClientRect();
    const hold = document.createElement('style'); hold.textContent = '.coin-plane, .coin-plane * { pointer-events:auto !important; }'; document.head.append(hold);
    const hits = [[0, 0], ...Array.from({length: 8}, (_, k) => [Math.cos(k * Math.PI / 4) * 0.45, Math.sin(k * Math.PI / 4) * 0.45])].map(([u, v]) => {
      // the topmost element there that is not one of the coin's containers (the 3D views' cameras paint nothing)
      const hit = document.elementsFromPoint(box.left + box.width * (0.5 + u / 2), box.top + box.height * (0.5 + v / 2)).find(n => !n.contains(plane));
      return hit && hit.closest('.coin-plane') === plane ? 'coin' : hit ? (hit.closest('svg') ? hit.closest('svg').getAttribute('class') || 'board' : hit.localName) : 'none'; });
    hold.remove();
    const angle = getComputedStyle(plane.querySelector('.coin-layer-gleam')).backgroundImage.match(/^linear-gradient\((-?[\d.]+)deg/);
    const spin = parseFloat(getComputedStyle(plane).getPropertyValue('--coin-spin'));
    return {layers: layers.join(','), plane: +z(plane).toFixed(2), gleam: angle ? Number(angle[1]) : 180, spin, top: +z(top).toFixed(2), expected: +(1.75 / 28.26 * plane.offsetWidth).toFixed(2),
            hidden: getComputedStyle(plane.querySelector('.coin-layer-cast')).backfaceVisibility,
            href: top.querySelector('image').getAttribute('href'), hits: hits.join(',')}; }"""
COIN_PHOTO = """async (href) => { const reply = await fetch(href); const bytes = (await reply.arrayBuffer()).byteLength;
    return [reply.status, reply.headers.get('content-type'), bytes]; }"""


def part_coin(browser):
    """A coin for scale in every view of a board (the user's requests of 2026-10-30): a US quarter (24.26 mm) whose face
    is the US Mint's photo (web/vendor/coin), drawn to scale in the board's millimetres.  In the 2D views it lies under the
    board (drawn before it) at the bottom right of the view, 0.6 mm in from its edges, at least 2 mm clear of the outline
    (the view grows to hold it).  In the oblique and stacked 3D views it lies on a plane of its own below the boards
    (28 / 56 px), as thick as a quarter (1.75 mm: its shadow, eight disks of its reeded side, its face, its gleam that
    keeps to the room as the view turns), the boards covering none of it; the plan view lays it flat; the legends name
    it."""
    page = new_page(browser, width=1440)
    boot(page)
    for name in ("row", "column"):
        coin = page.evaluate(COIN_2D, f"#{name}Preview svg")
        check(f"coin: the {name} 2D view's quarter (r 12.13 mm) lies under the board at its bottom right, 0.6 mm in, the "
              "US Mint photo clipped to its circle, placed by coordinates (no transform beside the board group's)",
              coin is not None and coin["r"] == 12.13 and coin["right"] == 0.6 and coin["bottom"] == 0.6 and coin["under"] and coin["placed"] == 0
              and coin["href"] == COIN_HREF and coin["clip"] == "url(#coin-clip)", coin)
        check(f"coin: the {name} 2D view's quarter keeps at least 2 mm clear of the outline, outside it",
              coin is not None and coin["clear"] >= 2 - 1e-6 and not coin["inside"], coin)
        check(f"coin: the {name} 2D view's quarter is drawn to scale with the board (on screen, its width over the outline's "
              "= 24.26 mm over the outline's mm)", coin is not None and abs(coin["ratio"] - 24.26 / coin["outlineMm"]) < 0.01, coin)
    status_code, kind, size = page.evaluate(COIN_PHOTO, COIN_HREF)
    check("coin: the photo is served from the app (offline, inside its CSP)", status_code == 200 and kind == "image/jpeg" and size > 10000, (status_code, kind, size))
    page.click("#rowTab3d"); page.wait_for_timeout(300)
    page.evaluate("() => document.querySelector('#rowCard').scrollIntoView({block: 'center'})"); page.wait_for_timeout(200)
    layers = "cast," + ",".join(["side"] * 8) + ",top,gleam"
    oblique = page.evaluate(COIN_3D, "#rowCard .oblique-board")
    check("coin: the Row FPC's oblique view lays the quarter 28 px below the board, its face 1.75 mm above its shadow, "
          "the board covering none of it",
          oblique is not None and oblique["layers"] == layers and oblique["plane"] == -28 and abs(oblique["top"] - oblique["expected"]) < 0.05
          and oblique["hits"] == ",".join(["coin"] * 9) and oblique["href"] == COIN_HREF, oblique)
    page.evaluate("() => document.querySelector('#stackedPreview').scrollIntoView({block: 'center'})"); page.wait_for_timeout(300)
    stacked = page.evaluate(COIN_3D, "#stackedPreview .assembly-camera")
    check("coin: the stacked view lays the quarter 56 px below the bottom FPC, its face 1.75 mm above its shadow (hidden "
          "from below), the boards covering none of it",
          stacked is not None and stacked["layers"] == layers and stacked["plane"] == -56 and abs(stacked["top"] - stacked["expected"]) < 0.05
          and stacked["hidden"] == "hidden" and stacked["hits"] == ",".join(["coin"] * 9), stacked)
    page.focus("#stackedPreview"); page.keyboard.press("ArrowLeft"); page.wait_for_timeout(150)
    turned = page.evaluate(COIN_3D, "#stackedPreview .assembly-camera")
    page.keyboard.press("0"); page.wait_for_timeout(150)
    check("coin: turned 5 degrees (ArrowLeft) the stacked view's gleam turns back by as much",
          turned is not None and turned["spin"] == -15 and abs(turned["gleam"] + turned["spin"] - 165) < 1e-6, turned)
    page.click('[data-assembly-mode="plan"]'); page.wait_for_timeout(300)
    plan = page.evaluate(COIN_3D, "#stackedPreview .assembly-camera")
    check("coin: its gleam keeps to the room as the view turns (its angle undoes the spin: angle + spin = 165 degrees)",
          oblique is not None and stacked is not None and abs(oblique["gleam"] + oblique["spin"] - 165) < 1e-6
          and abs(stacked["gleam"] + stacked["spin"] - 165) < 1e-6, (oblique, stacked))
    check("coin: the plan view lays the quarter flat beside the boards (no rise), none of it covered",
          plan is not None and plan["plane"] == 0 and plan["top"] == 0 and plan["hits"] == ",".join(["coin"] * 9), plan)
    page.click('[data-assembly-mode="exploded"]'); page.wait_for_timeout(200)
    legends = [page.inner_text(f"#{key}Legend") for key in ("row", "column")] + [page.inner_text("#assemblyLegend")]
    check("coin: the board legends and the stacked view's keys name it", all("Coin for scale" in text and "US quarter, 24.26 mm" in text for text in legends), legends)
    check("coin part: no console errors", not console_errors(page), console_errors(page))
    page.close()


# A 3D view's boards: their stack-up, the depth of a millimetre on screen (the board's own scale, at least 2 px for the
# FPC), each wall layer's kind, depth (mm) and computed translateZ (px), the other side's and the copper side's.
DEPTH_STATE = r"""(selector) => [...document.querySelectorAll(selector)].map(board => {
    const z = node => { const t = node ? getComputedStyle(node).transform : 'none'; return t === 'none' ? 0 : +new DOMMatrixReadOnly(t).m43.toFixed(3); };
    const fpc = Number(board.dataset.fpcMm); const own = board.offsetWidth / Number(board.style.getPropertyValue('--view-mm'));
    return {fpc, stiffener: Number(board.dataset.stiffenerMm), own: +own.toFixed(4), scale: +Math.max(own, 2 / fpc).toFixed(4),
            layers: [...board.querySelectorAll('svg.board-edge')].map(e => [e.getAttribute('class').replace('board-edge board-edge-', ''),
              Number(e.style.getPropertyValue('--depth-mm')), z(e), getComputedStyle(e).display, getComputedStyle(e).pointerEvents]),
            back: z(board.querySelector('.board-back-face')), front: z(board.querySelector(':scope > svg, :scope > .assembly-face > svg'))}; })"""


def depth_problems(state):
    """What is wrong with a board's thickness (DEPTH_STATE): the stack-up 0.11 + 0.225 mm, three FPC wall rings and five
    stiffener rings at the middles of their layers, the stiffener's outer face at 0.335 mm, the other side at 0.11 mm,
    each at its depth times the scale (within 0.02 px), the copper side at 0, never a pointer target."""
    fpc, stiffener, scale = state["fpc"], state["stiffener"], state["scale"]
    expected = [("fpc", fpc * (k + 0.5) / 3) for k in range(3)] + [("stiffener", fpc + stiffener * (k + 0.5) / 5) for k in range(5)]
    expected.append(("stiffener-face", fpc + stiffener))
    problems = []
    if (fpc, stiffener) != (0.11, 0.225):
        problems.append(("stack-up", fpc, stiffener))
    if [kind for kind, *_ in state["layers"]] != [kind for kind, _ in expected]:
        problems.append(("layers", [kind for kind, *_ in state["layers"]]))
    for (kind, depth, z, display, events), (_, want) in zip(state["layers"], expected):
        if abs(depth - want) > 1e-6 or abs(z + want * scale) > 0.02 or display == "none" or events != "none":
            problems.append((kind, depth, z, display, events))
    if abs(state["back"] + fpc * scale) > 0.02 or state["front"] != 0:
        problems.append(("sides", state["back"], state["front"]))
    return problems


def part_depth(browser):
    """The boards' thickness in the 3D views (the user's request of 2026-10-30): the stack-up of each board's result
    (board.fpc.stackup: 0.11 mm of PI, copper, coverlay adhesive and coverlay, the PI stiffener 0.225 mm below it) behind
    the copper side, which stays in its place; to scale where that is 2 px or more on screen, else the FPC drawn 2 px
    thick and the stiffener in proportion; the walls rings along the edges, so the turned-over top FPC stays see-through
    over the taxel field; none in the plan view; the captions say so."""
    page = new_page(browser, width=1440)
    boot(page)
    page.click("#rowTab3d"); page.click("#columnTab3d"); page.wait_for_timeout(300)
    oblique = page.evaluate(DEPTH_STATE, ".three-d-pane .oblique-board")
    check("depth: both oblique views draw the board 0.11 mm thick with its 0.225 mm stiffener behind the copper side (walls, the "
          "stiffener's outer face and the other side each at its depth, the copper side in place)",
          len(oblique) == 2 and all(depth_problems(state) == [] for state in oblique), [(state, depth_problems(state)) for state in oblique])
    check("depth: at the oblique views' scale (under 18.2 px a mm) the FPC is drawn 2 px thick, the stiffener in proportion",
          all(state["own"] < 2 / 0.11 and abs(state["back"] + 2) < 0.02 for state in oblique), oblique)
    widths = page.evaluate("() => [...document.querySelectorAll('.oblique-board')].map(board => board.style.width)")
    page.evaluate("() => document.querySelectorAll('.oblique-board').forEach(board => { board.style.width = '4000px'; })")
    page.wait_for_timeout(100)
    large = page.evaluate(DEPTH_STATE, ".three-d-pane .oblique-board")
    page.evaluate("(widths) => document.querySelectorAll('.oblique-board').forEach((board, index) => { board.style.width = widths[index]; })", widths)
    check("depth: drawn larger than 2 px (a board 4000 px wide), the thickness is to the board's own scale",
          all(state["own"] > 2 / 0.11 and state["scale"] == state["own"] and depth_problems(state) == [] for state in large), large)
    page.evaluate("() => document.querySelector('#stackedPreview').scrollIntoView({block: 'center'})"); page.wait_for_timeout(300)
    stacked = page.evaluate(DEPTH_STATE, "#stackedPreview .assembly-board")
    check("depth: both stacked boards are as thick, behind their copper sides (the top FPC's turned over with it)",
          len(stacked) == 2 and all(depth_problems(state) == [] for state in stacked), [(state, depth_problems(state)) for state in stacked])
    # The top FPC stays see-through over the field: its walls paint nothing inside its projected taxel field.
    cdp = page.context.new_cdp_session(page); cdp.send("DOM.enable"); cdp.send("Runtime.enable")
    obj = cdp.send("Runtime.evaluate", {"expression": "document.querySelector('#stackedPreview .is-upper rect.taxel-field')"})["result"]["objectId"]
    quad = cdp.send("DOM.getContentQuads", {"objectId": obj})["quads"][0]
    from PIL import Image, ImageChops
    import io
    shot = lambda: Image.open(io.BytesIO(page.screenshot())).convert("RGB")
    shown = shot()
    hide = page.add_style_tag(content=".board-edge{visibility:hidden !important}"); page.wait_for_timeout(80)
    hidden = shot(); page.evaluate("s => s.remove()", hide)
    xs, ys = quad[0::2], quad[1::2]
    inner = (int(min(xs)) + 4, int(min(ys)) + 4, int(max(xs)) - 4, int(max(ys)) - 4)
    corners = [(quad[i], quad[i + 1]) for i in range(0, 8, 2)]
    worst = 0
    for i in range(1, 10):
        for j in range(1, 8):
            u, v = i / 10, j / 8
            x = (1 - u) * (1 - v) * corners[0][0] + u * (1 - v) * corners[1][0] + u * v * corners[2][0] + (1 - u) * v * corners[3][0]
            y = (1 - u) * (1 - v) * corners[0][1] + u * (1 - v) * corners[1][1] + u * v * corners[2][1] + (1 - u) * v * corners[3][1]
            worst = max(worst, max(abs(a - b) for a, b in zip(shown.getpixel((int(x), int(y))), hidden.getpixel((int(x), int(y))))))
    edges = ImageChops.difference(shown, hidden).getbbox()
    check("depth: the walls change nothing inside the top FPC's projected taxel field (it stays see-through) and show at its edges",
          worst <= 2 and edges is not None, (worst, edges, inner))
    caption = page.inner_text("#stackedPreview .assembly-caption")
    pane = page.evaluate("() => getComputedStyle(document.getElementById('rowPreview3d'), '::after').content")
    check("depth: the captions say the thickness is drawn at least 2 px", "thickness at least 2 px" in caption and "thickness at least 2 px" in pane, (caption, pane))
    page.click('[data-assembly-mode="plan"]'); page.wait_for_timeout(300)
    plan = page.evaluate(DEPTH_STATE, "#stackedPreview .assembly-board")
    check("depth: the plan view draws no thickness (no walls, the other side in the copper side's plane)",
          all(state["back"] == 0 and all(display == "none" for _, _, _, display, _ in state["layers"]) for state in plan), plan)
    page.click('[data-assembly-mode="exploded"]'); page.wait_for_timeout(150)
    check("depth part: no console errors", not console_errors(page), console_errors(page))
    page.close()


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        parts = (part_boot_and_limits, part_clean_interface, part_looks, part_row_traces, part_stacked_pin1, part_stacked_orbit, part_two_sided, part_coin, part_depth, part_nudges_and_advice, part_stale, part_zoom, part_drc_and_failures,
                 part_aria, part_downloads_and_http)
        chosen = [part for part in parts if len(sys.argv) < 2 or part.__name__ in sys.argv[1:]]
        for part in chosen:
            print(f"--- {part.__name__}", flush=True)
            try:
                part(browser)
            except Exception as error:  # noqa: BLE001 - report and continue
                check(f"{part.__name__} ran to completion", False, repr(error))
        browser.close()
    return summary()


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
