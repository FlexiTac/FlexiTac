"""The page's Apple-style theme (web/theme.css over web/styles.css) in the browser, light and dark.

Against a running app.py (FPC_PORT), on pages as the user opens them (no fold opened by an init script), 1440 x 900.
The look is light for every visitor whatever the system's scheme, dark once the header's toggle is turned on (the user's
request of 2026-11-06; web/theme.js): "dark" below is the toggle's, turned on with a click on the Library page before
the page checked opens (so the generator opens dark from the stored choice), the system's scheme light.
- part_toggle (2026-11-06): a dark system with no stored choice opens both pages light (data-theme light, the page's
  grey, color-scheme light, the toggle off: its moon, aria-pressed false, "Turn dark mode on"); the toggle a button
  named Dark mode, 44 x 44 and round, right before GitHub (10 px) on its line, the community links next to it, at 1440 px;
  clicked on the Library it turns the page dark (pressed, its sun, "Turn dark mode off", the page black, the bar
  #161617, color-scheme dark), the choice stored; the generator then opens dark and stays dark after a reload; off on
  the generator, the Library opens light, after a reload too; Tab reaches it with its focus ring and Enter and Space
  flip it; a second tab follows a flip in the first (the storage event), and the first's clear() of the storage (light
  again, the event's key null); no flash: with dark stored, on both pages
  data-theme is set before <body> is parsed and before the first paint, and with the pages' other scripts blocked the
  first screen is already dark (the bar and the page black), light for a dark system with nothing stored; with
  storage blocked the pages open light, the toggle still flips the page and a reload is light again; at 390, 375 and
  320 px the toggle on the title's line before GitHub (6 px), 40 x 40, 36 x 36 and 32 x 32 as the community's circles
  (the line's room, the review of 2026-11-06), the header as tall as before the toggle (239, 239 and 238.5 px) and a
  tap flips it; no console error.
- part_schemes, in the light and the dark look, in Gen by Surface (its default part's sensor built) and at #rect:
  - scrolling changes nothing: the whole page scrolled to its end in 300 px steps and back, every element's opacity,
    transform, visibility, filter, backdrop filter and classes (but the guide's .is-here, which follows the scroll) as
    they were, no animation started; scroll-behavior auto, every element's animation timeline auto and no scroll or
    view timeline named;
  - the first screen: Generate sensor's bottom at most 876 px and at most the page's before the theme, the rectangular
    form's Generate & validate in the window and no lower than before the theme (FPC_THEME_BASELINE: a JSON file with
    cadQuickGenerateBottom and generateBottomRect, else the values measured on the page before the theme);
  - the scheme: light, data-theme light, the page's grey (#f5f5f7) and color-scheme light; dark, data-theme dark, the
    shell dark (the page, the header,
    the guide, the cards, the form, the fields, the design checks' row) with light text, the drawings' areas light
    lightboxes (the 3D view's #f5f5f7 and its pills' light material, the previews' white, the stacked view's grey and,
    beside it in Gen by Surface, the sensor on the part's (2026-11-05), the map's white; color-scheme light there);
  - the colours, as Apple uses them: the elements filled with the action blue (or any blue) only the regions' primary
    actions (Generate sensor, Generate & validate in the form and in Advanced Customization, the two Gerber ZIPs, Fit while it is the
    guide's next step) and the selection states (the guide's next step, Edit border on; tinted: the chosen tool, the
    chosen proposal), and no element larger than 12 px filled green; in eight states: Gen by Surface as it opens, with
    Advanced Customization open, with the border editor on and with a setting changed (Fit the next step: Fit blue,
    Generate & validate off), #rect as it opens, with its folds open, stale, and with a failing design check (the
    server's reply with one rule failed);
  - no leftover of styles.css's palette outside the drawings (its teal family, its stray blues, its teal-cast greys and
    ink), in the same states; the border editor's frame on the 3D view keeps the border's own data blue (#1e88e5);
  - no colour fades: every button's, summary's and header link's transition 0s (a hover, a press and a state change
    at once);
  - the 3D view's keyboard focus ring drawn above its canvas (its ::after);
  - #rect stale: the previews and the stacked view faded as lightboxes (light: styles.css's half opacity, greyed;
    dark: opaque and paled by the filter, not a grey slab over the dark card);
  - hit targets: the segmented controls (the mode switch, the preview tabs, the stacked view's modes, the looks), the
    zoom buttons, the design checks' row and its Show all checks (shown on a failure), the camera buttons, the sensor on
    the part's Reset view, the header's toggle at least 24 x 24 px;
  - no console error.
  Gen by Surface's default part loads once more when it failed (a server busy with another client's fit answers 503);
  its checks start once the sensor on the part is drawn (or settled with nothing to draw).
- part_reduced_motion (prefers-reduced-motion: reduce): the disclosure arrows' and every button's, summary's and header
  link's transition 0s; a guide step and its Advanced Customization switch jump (80 ms after the click the target is in its place);
  a button held down is neither scaled nor moved; no animation.
- part_reduced_transparency (prefers-reduced-transparency: reduce, by CDP), light and dark (the toggle's): the 3D view's
  three pills without backdrop filter, their material opaque (alpha .95 or more) and light.
- part_contrast_and_forced: prefers-contrast more (the cards edged in the control border, the secondary text darker,
  links underlined) and forced colours (the chosen mode, tab, stacked view mode and look outlined): smoke, no console
  error.
- part_library (2026-11-05): Generate sensor's bottom at most 857.1 px with the header's Library link; library.html in
  both schemes, the action blue only on Open in Gen by Surface, nothing green, no old palette, no fades; more contrast
  underlines its links and the header's Library link.
Screenshots go to $FPC_BROWSER_OUT/shots (theme_*.png).
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True  # no __pycache__ next to the scripts
sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright.sync_api import sync_playwright  # noqa: E402

from rp import DARK_CHOICE, DONE, RECT_URL, SHOTS, THEME_KEY, URL, check, summary, wait_until  # noqa: E402

WEBGL_ARGS = ["--enable-unsafe-swiftshader", "--use-angle=swiftshader"]
WIDTH, HEIGHT = 1440, 900
# The page before the theme (40c4050, 1440 x 900, Chromium's DejaVu Sans on Linux): Generate sensor's bottom with
# Advanced Customization folded, and the rectangular form's Generate & validate's.
BASELINE = {"cadQuickGenerateBottom": 856.6, "generateBottomRect": 365.0}
FIRST_SCREEN = 876  # px: Generate sensor's bottom at most (the plan's first-screen budget)
SETTLED = ("() => !['pending', 'running'].includes(JSON.parse(document.getElementById('cadState').textContent || '{}').default_build)"
           " && ['loaded', 'skipped', 'failed'].includes(JSON.parse(document.getElementById('cadState').textContent || '{}').default_part)"
           " && JSON.parse(document.getElementById('cadState').textContent || '{}').busy?.length === 0")
BUILT = "() => !document.body.classList.contains('cad-no-build') && " + DONE[6:]
# The sensor on the part beside the stacked view (2026-11-05) drawn, or settled on a state with nothing to draw: its DOM
# no longer changes (the scroll invariance compares every element's classes).
ON_PART_SETTLED = ("() => ['drawn', 'unavailable', 'failed', 'empty'].includes("
                   "JSON.parse(document.getElementById('cadState').textContent || '{}').on_part?.state)")
RECT_DONE = "() => (" + DONE[6:] + ") && !document.querySelector('#status').textContent.startsWith('Deriving')"

# The drawings and what they draw keep their own colours (the plan's sections 1 and 5): the SVGs, the 3D view's canvas,
# the photos and the oblique and stacked scenes (the legends' swatches and ring keys went with the legends on 2026-11-06).
DRAWINGS = "svg, canvas, img, .oblique-board, .assembly-scene, .coin-ref, .coin-plane"
# Blue fills allowed: each region's one primary action and the selection states (the theme's rule of colour, 2026-11-04).
FIT_NEXT = '#guideSubsteps .flow-substep[data-substep="fit"].is-next'
BLUE_ALLOWED = ["#generate", "#cadGenerate", "#cadQuickGenerate", ".download-actions button.download-main",
                f"body:has({FIT_NEXT}) #cadFit", ".flow-step.is-next .flow-no", ".flow-substep.is-next .flow-sub-no",
                '#cadEditBorder[aria-pressed="true"]']
# The page's buttons, summaries and header links whose transition is not 0s (no colour fades in the theme).
FADING = """() => [...document.querySelectorAll('button, summary, a.masthead-link')]
    .map(n => [n.id || n.className || n.tagName, getComputedStyle(n).transitionDuration]).filter(([, d]) => d.split(', ').some(x => x !== '0s'))"""
BLUE_TINT_ALLOWED = [".cad-tools input:checked + span", "#cadProposals tr.is-chosen"]
# styles.css's palette that the theme replaces: its teal family, its stray blues, its teal-cast greys and its ink.
OLD_PALETTE = {
    "teal": ["#075c69", "#087e8b", "#066d78", "#065560", "#77cbd1", "#9fc6cb", "#b9e6df", "#b9d9db", "#e4f2f3", "#d6ecee",
             "#eef9f8", "#f6fbfa", "#eef5f3", "#dbe8e6", "#3d555a", "#63808a", "#f4f8f7", "#395158", "#536d74"],
    "blue": ["#2563eb", "#0b5d9c", "#1e88e5", "#eaf2fe", "#bdd2f6"],
    "slate": ["#132033", "#5d6977", "#f7f8f5", "#dbe2e5", "#354454", "#26404a", "#3f5f66", "#33454d", "#53676e", "#20303a",
              "#c7d3d7", "#9eafb5", "#607d8b", "#edf2f4", "#e7f4f0", "#fbfdfd", "#fbfcfa", "#d6e2e5", "#eef5f5", "#b9c8cc",
              "#a9bcc1", "#8a9a9e", "#e3eceb", "#bfcbd0", "#9aa5aa", "#d1d8da", "#f0f4ef", "#d7e1d8", "#3d4b58"],
}
# Kept on purpose: the border editor's frame on the 3D view is the border's own line colour, the drawings' blue (plan 3.4).
OLD_KEPT = [[".cad-view.is-editing", "outline", "#1e88e5"]]
# The hit targets (WCAG 2.5.8, 24 x 24 px) of the small controls.
TARGETS = {"the mode switch": "#modePicker label", "the preview tabs": ".preview-tabs button", "the stacked view's modes": ".mode-switch button",
           "the looks": ".look-bar button", "the zoom buttons": ".zoom-tools button", "the design checks' row": ".drc-panel > summary",
           "Show all checks": ".drc-bar button", "the camera buttons": ".cad-views button", "the reset of the view on the part": "#onPartReset",
           "the reset of the registration's 3D view": "#stackedReset", "the header's toggle": "#themeToggle"}

# Each element's opacity, transform, visibility, filters and classes (the guide's .is-here apart), and the animations.
SNAPSHOT = """() => { const out = [];
  for (const node of document.querySelectorAll('body, body *')) {
    if (node.closest('svg') && node.tagName.toLowerCase() !== 'svg') continue;
    const s = getComputedStyle(node);
    out.push([s.opacity, s.transform, s.visibility, s.filter, s.backdropFilter,
              [...node.classList].filter(c => c !== 'is-here').join(' ')].join('|'));
  }
  return {nodes: out, animations: document.getAnimations().map(a => a.animationName || a.transitionProperty || 'animation')}; }"""
TIMELINES = """() => { const bad = [];
  for (const node of document.querySelectorAll('*')) { const s = getComputedStyle(node);
    if ((s.animationTimeline && s.animationTimeline !== 'auto') || (s.scrollTimelineName && s.scrollTimelineName !== 'none')
        || (s.viewTimelineName && s.viewTimelineName !== 'none')) bad.push(node.tagName + (node.id ? '#' + node.id : '')); }
  return {bad: bad.slice(0, 10), html: getComputedStyle(document.documentElement).scrollBehavior, body: getComputedStyle(document.body).scrollBehavior}; }"""

# The colours of every visible element (and its ::before / ::after): blue and green fills, and styles.css's old palette.
SCAN = r"""([drawings, blueAllowed, tintAllowed, old, kept]) => {
  const parse = s => { const m = s && s.match(/rgba?\(([^)]+)\)/); if (!m) return null; const p = m[1].split(/[ ,\/]+/).filter(Boolean).map(Number);
    return {r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1}; };
  const all = s => (s.match(/rgba?\([^)]+\)/g) || []).map(parse);
  const blue = c => c && c.a > 0 && ((c.r === 0 && c.g === 113 && c.b === 227) || (c.r === 0 && c.g === 102 && c.b === 204)
    || (c.r === 0 && c.g === 88 && c.b === 176) || (c.b > c.r + 80 && c.b > c.g + 40));
  const green = c => c && c.a >= .5 && c.g > c.r + 40 && c.g > c.b + 40;
  const hex = c => '#' + [c.r, c.g, c.b].map(v => Math.round(v).toString(16).padStart(2, '0')).join('');
  const name = el => { let s = el.tagName.toLowerCase() + (el.id ? '#' + el.id : '');
    const cls = [...el.classList].slice(0, 3); if (cls.length) s += '.' + cls.join('.');
    if (!el.id) { const p = el.parentElement && el.parentElement.closest('[id]'); if (p) s = '#' + p.id + ' ' + s; }
    return s; };
  const ownText = el => [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
  const found = {blue: [], green: [], old: []};
  for (const el of document.querySelectorAll('body *')) {
    if (el.closest(drawings)) continue;
    if (!el.checkVisibility({checkOpacity: true, checkVisibilityCSS: true})) continue;
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    for (const pseudo of ['', '::before', '::after']) {
      const cs = getComputedStyle(el, pseudo || null);
      if (pseudo && (cs.content === 'none' || cs.content === 'normal' || cs.display === 'none')) continue;
      const w = pseudo ? parseFloat(cs.width) : r.width, h = pseudo ? parseFloat(cs.height) : r.height;
      const big = w > 12 && h > 12;
      const label = name(el) + pseudo;
      const fills = [parse(cs.backgroundColor), ...(cs.backgroundImage === 'none' ? [] : all(cs.backgroundImage))];
      for (const c of fills) {
        if (big && blue(c)) {
          const tint = c.a < .5;
          const ok = !pseudo && (tint ? tintAllowed.concat(blueAllowed) : blueAllowed).some(sel => el.matches(sel));
          if (!ok) found.blue.push([label, hex(c) + (tint ? ' a' + c.a : ''), Math.round(w), Math.round(h)]);
        }
        if (big && green(c)) found.green.push([label, hex(c), Math.round(w), Math.round(h)]);
      }
      // The old palette: the text colour where there is text (or a control, or an icon), the visible edges, the fills.
      const values = [];
      if (ownText(el) || ['INPUT', 'SELECT', 'TEXTAREA', 'BUTTON', 'SUMMARY'].includes(el.tagName) || el.querySelector(':scope > svg') || pseudo)
        values.push(['color', cs.color]);
      for (const side of ['Top', 'Right', 'Bottom', 'Left'])
        if (parseFloat(cs['border' + side + 'Width']) > 0 && cs['border' + side + 'Style'] !== 'none') values.push(['border-' + side.toLowerCase(), cs['border' + side + 'Color']]);
      if (cs.outlineStyle !== 'none' && parseFloat(cs.outlineWidth) > 0) values.push(['outline', cs.outlineColor]);
      values.push(['background-color', cs.backgroundColor], ['background-image', cs.backgroundImage], ['box-shadow', cs.boxShadow]);
      for (const [prop, value] of values)
        for (const c of all(value || '')) if (c && c.a > 0 && old.includes(hex(c))
            && !kept.some(([sel, p, h]) => !pseudo && el.matches(sel) && prop.startsWith(p) && h === hex(c))) found.old.push([label, prop, hex(c)]);
    }
  }
  return found; }"""

SCHEME = """() => { const cs = (sel, pseudo) => { const node = document.querySelector(sel); return node ? getComputedStyle(node, pseudo || null) : null; };
  const pick = (sel, props, pseudo) => { const s = cs(sel, pseudo); return s ? Object.fromEntries(props.map(p => [p, s[p]])) : null; };
  return {html: pick('html', ['colorScheme']), theme: document.documentElement.dataset.theme || null, body: pick('body', ['backgroundColor', 'color']),
    masthead: pick('.masthead', ['backgroundColor', 'color']), title: pick('.masthead h1', ['color']),
    guide: pick('.flow-guide', ['backgroundColor']), workspace: pick('#cadWorkspace', ['backgroundColor', 'color']),
    hint: pick('.cad-title-hint', ['color']), card: pick('#rowCard', ['backgroundColor', 'color']), downloads: pick('.downloads', ['backgroundColor']),
    controls: pick('.controls', ['backgroundColor']), field: pick('#rows', ['backgroundColor', 'color']), drc: pick('.drc-panel > summary', ['backgroundColor']),
    view: pick('.cad-view', ['backgroundColor', 'colorScheme']), tools: pick('.cad-view-tools', ['backgroundColor', 'colorScheme']),
    status3d: pick('#cadStatus', ['color']), canvas: pick('.canvas-wrap', ['backgroundColor', 'colorScheme']),
    stacked: pick('.stacked-canvas', ['backgroundImage', 'colorScheme']), map: pick('.cad-flat', ['backgroundColor', 'colorScheme']),
    onPart: pick('#sensorOnPart', ['backgroundImage', 'colorScheme']),
    chips: pick('.is-registration .figure-tools .mode-switch', ['backgroundColor', 'colorScheme']), reset: pick('#stackedReset', ['backgroundColor', 'colorScheme'])}; }"""


def rgba(value):
    """The (r, g, b, a) of a computed colour string."""
    inner = value[value.index("(") + 1:value.rindex(")")].replace("/", " ").replace(",", " ").split()
    numbers = [float(part) for part in inner]
    return tuple(numbers[:3]) + ((numbers[3],) if len(numbers) > 3 else (1.0,))


def luminance(value):
    def channel(level):
        level /= 255.0
        return level / 12.92 if level <= 0.04045 else ((level + 0.055) / 1.055) ** 2.4
    red, green, blue, _ = rgba(value)
    return 0.2126 * channel(red) + 0.7152 * channel(green) + 0.0722 * channel(blue)


def baseline():
    path = os.environ.get("FPC_THEME_BASELINE")
    if not path:
        return dict(BASELINE), "the page before the theme (recorded)"
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    return {key: float(data[key]) for key in BASELINE}, path


def flip_a_check(route):
    """The real /api/generate reply with the Row FPC's first DRC rule failing (as ui_checks.py's part_clean_interface)."""
    response = route.fetch()
    body = response.json()
    checks = body.get("boards", {}).get("row", {}).get("verification", {}).get("checks", {})
    if checks:
        first = next(iter(checks.values()))
        first["passed"] = False
        first["violation_count"] = 1
    route.fulfill(response=response, json=body)


def new_page(browser, scheme="light", motion="no-preference", forced="none", contrast="no-preference", features=None, system="light"):
    """A page in the look ``scheme``: "dark" turns the header's toggle on, clicked on the Library page (the choice then
    stored for the page the part opens); the system's own scheme ``system``, light unless asked."""
    context = browser.new_context(viewport={"width": WIDTH, "height": HEIGHT}, color_scheme=system, reduced_motion=motion,
                                  forced_colors=forced, contrast=contrast)
    page = context.new_page()
    page.errors = []
    page.on("console", lambda message: page.errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: page.errors.append(str(error)))
    if features:
        # CDP replaces the emulated features as a whole: the scheme and motion are named again with the extra ones.
        session = context.new_cdp_session(page)
        session.send("Emulation.setEmulatedMedia", {"features": [{"name": "prefers-color-scheme", "value": system},
                                                                 {"name": "prefers-reduced-motion", "value": motion}] + features})
    if scheme == "dark":
        page.goto(URL + "library.html")
        page.click("#themeToggle")
        if page.evaluate("() => document.documentElement.dataset.theme") != "dark":
            raise RuntimeError("the header's toggle did not turn the dark look on")
        page.mouse.move(WIDTH - 2, HEIGHT - 2)
    return page


def open_cad(page):
    for attempt in (1, 2):
        page.goto(URL)
        wait_until(page, DONE, 120)
        wait_until(page, SETTLED, 180)
        part = page.evaluate("() => JSON.parse(document.getElementById('cadState').textContent || '{}').default_part")
        if part != "failed" or attempt == 2:
            break
        # app.py has one surface slot: another client's fit at that moment answers the default part's load with 503s.
        print("the default part failed to load (a busy server?): loading the page once more", flush=True)
        page.errors.clear()
        page.wait_for_timeout(5000)
    wait_until(page, BUILT, 120)
    wait_until(page, ON_PART_SETTLED, 120)
    page.wait_for_timeout(500)
    page.mouse.move(WIDTH - 2, HEIGHT - 2)
    page.wait_for_timeout(250)


def open_rect(page):
    page.goto(RECT_URL)
    wait_until(page, RECT_DONE, 120)
    page.wait_for_timeout(500)
    page.mouse.move(WIDTH - 2, HEIGHT - 2)
    page.wait_for_timeout(250)


def scroll_invariance(page, label):
    page.evaluate("() => window.scrollTo(0, 0)")
    page.wait_for_timeout(250)
    before = page.evaluate(SNAPSHOT)
    height = page.evaluate("() => document.documentElement.scrollHeight - innerHeight")
    stops = list(range(300, height, 300)) + [height] + list(range(height - 300, 0, -300)) + [0]
    changed = []
    for y in stops:
        page.evaluate("y => window.scrollTo(0, y)", y)
        page.wait_for_timeout(70)
        now = page.evaluate(SNAPSHOT)
        if now["animations"] != before["animations"]:
            changed.append((y, "animations", now["animations"]))
        elif now["nodes"] != before["nodes"]:
            diff = [index for index, (a, b) in enumerate(zip(before["nodes"], now["nodes"])) if a != b][:3]
            changed.append((y, len(now["nodes"]) - len(before["nodes"]), [(before["nodes"][i], now["nodes"][i]) for i in diff]))
    check(f"{label}: scrolled to the end in 300 px steps and back ({len(stops)} stops over {height} px), no element's opacity, transform, "
          "visibility, filter, backdrop filter or classes (but .is-here) changes and no animation starts", height > 600 and not changed, changed[:3])
    timelines = page.evaluate(TIMELINES)
    check(f"{label}: scroll-behavior auto, every animation timeline auto, no scroll or view timeline named, no animation running",
          timelines["html"] == "auto" and timelines["body"] == "auto" and not timelines["bad"] and not before["animations"], [timelines, before["animations"]])
    page.evaluate("() => window.scrollTo(0, 0)")
    page.wait_for_timeout(150)


def colours(page, label, results):
    page.mouse.move(WIDTH - 2, HEIGHT - 2)
    page.wait_for_timeout(300)
    found = page.evaluate(SCAN, [DRAWINGS, BLUE_ALLOWED, BLUE_TINT_ALLOWED, sorted({value for values in OLD_PALETTE.values() for value in values}), OLD_KEPT])
    for key in ("blue", "green", "old"):
        results.setdefault(key, []).extend((label,) + tuple(item) for item in found[key])
    return found


def hit_targets(page, label, seen):
    sizes = page.evaluate("""(targets) => Object.fromEntries(Object.entries(targets).map(([name, sel]) => [name,
        [...document.querySelectorAll(sel)].filter(n => n.checkVisibility()).map(n => { const r = n.getBoundingClientRect();
          return [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10]; })]))""", TARGETS)
    small = {name: [size for size in boxes if size[0] < 24 or size[1] < 24] for name, boxes in sizes.items()}
    small = {name: boxes for name, boxes in small.items() if boxes}
    for name, boxes in sizes.items():
        if boxes:
            seen.add(name)
    check(f"{label}: the small controls' hit targets at least 24 x 24 px ({', '.join(name for name, boxes in sizes.items() if boxes)})", not small, small)


def check_scheme(page, scheme, label, mode):
    data = page.evaluate(SCHEME)
    if scheme == "light":
        check(f"{label}: light: data-theme light, the page's grey (#f5f5f7), color-scheme light", data["theme"] == "light"
              and data["body"]["backgroundColor"] == "rgb(245, 245, 247)" and data["html"]["colorScheme"] == "light", [data["theme"], data["body"]])
        return
    shell = {"body": data["body"], "masthead": data["masthead"], "workspace" if mode == "cad" else "controls": data["workspace" if mode == "cad" else "controls"],
             "card": data["card"], "downloads": data["downloads"], "field": data["field"], "design checks": data["drc"]}
    if mode == "cad":
        shell["guide"] = data["guide"]
    dark = {name: luminance(value["backgroundColor"]) for name, value in shell.items()}
    text = {name: luminance(data[name]["color"]) for name in ("body", "title", "card", "field")}
    secondary = luminance(data["hint"]["color"])
    check(f"{label}: dark (the toggle's): data-theme dark, the shell dark (the page, the header{', the guide, the workspace' if mode == 'cad' else ', the form'}, the cards, "
          "the fields, the design checks' row: luminance under .03), its text light (over .6; the secondary grey over .25), color-scheme dark",
          data["theme"] == "dark" and all(value < 0.03 for value in dark.values()) and all(value > 0.6 for value in text.values()) and secondary > 0.25
          and data["html"]["colorScheme"] == "dark",
          {"backgrounds": {k: round(v, 4) for k, v in dark.items()}, "text": {k: round(v, 3) for k, v in text.items()}, "secondary": round(secondary, 3)})
    boxes = {"canvas": data["canvas"]["backgroundColor"] == "rgb(255, 255, 255)" and data["canvas"]["colorScheme"] == "light",
             "stacked": "rgb(245, 245, 247)" in data["stacked"]["backgroundImage"] and data["stacked"]["colorScheme"] == "light",
             # The figures' controls over them (2026-11-06): the light material, outside the stacked view's pane too.
             "chips": rgba(data["chips"]["backgroundColor"])[:3] == (255.0, 255.0, 255.0) and data["chips"]["colorScheme"] == "light",
             "reset": rgba(data["reset"]["backgroundColor"])[:3] == (255.0, 255.0, 255.0) and data["reset"]["colorScheme"] == "light"}
    if mode == "cad":
        boxes.update(view=data["view"]["backgroundColor"] == "rgb(245, 245, 247)" and data["view"]["colorScheme"] == "light",
                     tools=rgba(data["tools"]["backgroundColor"])[:3] == (255.0, 255.0, 255.0) and data["tools"]["colorScheme"] == "light",
                     status=luminance(data["status3d"]["color"]) < 0.05,
                     map=data["map"]["backgroundColor"] == "rgb(255, 255, 255)" and data["map"]["colorScheme"] == "light",
                     on_part="rgb(245, 245, 247)" in data["onPart"]["backgroundImage"] and data["onPart"]["colorScheme"] == "light")
    check(f"{label}: dark: the drawings' areas stay light lightboxes ({', '.join(boxes)}: their light colours, color-scheme light)",
          all(boxes.values()), {"boxes": boxes, "data": {k: data[k] for k in ("view", "tools", "status3d", "canvas", "stacked", "map", "onPart", "chips", "reset")}})


# The header's toggle (2026-11-06): its state and its box, and what the page shows.
TOGGLE = """() => { const b = document.getElementById('themeToggle'), r = b.getBoundingClientRect();
  const gh = document.querySelector('.masthead-github').getBoundingClientRect(), shown = s => b.querySelector(s).checkVisibility();
  const stored = (() => { try { return localStorage.getItem('%s'); } catch (error) { return 'blocked'; } })();
  return {theme: document.documentElement.dataset.theme || null, pressed: b.getAttribute('aria-pressed'), title: b.title,
          moon: shown('.theme-moon'), sun: shown('.theme-sun'), body: getComputedStyle(document.body).backgroundColor,
          bar: getComputedStyle(document.querySelector('.masthead')).backgroundColor, scheme: getComputedStyle(document.documentElement).colorScheme,
          box: [r.width, r.height].map(v => Math.round(v * 10) / 10), gap: Math.round((gh.left - r.right) * 10) / 10,
          middle: Math.round(Math.abs((r.top + r.bottom) / 2 - (gh.top + gh.bottom) / 2) * 10) / 10,
          next: Boolean(b.nextElementSibling && b.nextElementSibling.matches('nav.masthead-links')), round: getComputedStyle(b).borderRadius,
          masthead: Math.round(document.querySelector('.masthead').getBoundingClientRect().height * 10) / 10, stored}; }""" % THEME_KEY
LIGHT_LOOK = {"theme": "light", "pressed": "false", "title": "Turn dark mode on", "moon": True, "sun": False, "body": "rgb(245, 245, 247)",
              "bar": "rgb(251, 251, 253)", "scheme": "light"}
DARK_LOOK = {"theme": "dark", "pressed": "true", "title": "Turn dark mode off", "moon": False, "sun": True, "body": "rgb(0, 0, 0)",
             "bar": "rgb(22, 22, 23)", "scheme": "dark"}
# Recorded from the document's creation (an init script): the order in which <html data-theme> is set and <body> is
# inserted, the look at DOMContentLoaded, and when the attribute was set against the first paint.
FIRST_PAINT = """(() => { const seen = window.__look = {order: [], ready: null, setAt: null};
  new MutationObserver(records => { for (const record of records) {
      if (record.type === 'attributes' && record.attributeName === 'data-theme' && seen.setAt === null) { seen.order.push('theme:' + record.target.dataset.theme); seen.setAt = performance.now(); }
      if (record.type === 'childList' && [...record.addedNodes].some(node => node.nodeName === 'BODY')) seen.order.push('body');
    } }).observe(document, {childList: true, subtree: true, attributes: true, attributeFilter: ['data-theme']});
  document.addEventListener('DOMContentLoaded', () => { seen.ready = document.documentElement.dataset.theme || null; });
})();"""
FIRST_PAINT_READ = """() => { const paint = performance.getEntriesByType('paint').find(entry => entry.name === 'first-paint');
  return {...window.__look, firstPaint: paint ? paint.startTime : null}; }"""
# Storage that throws (a private window or blocked site data).
NO_STORAGE = """Object.defineProperty(window, 'localStorage', {configurable: true, get() { throw new DOMException('The operation is insecure.', 'SecurityError'); }});"""
# The pages' own scripts, blocked for the first screen (theme.js alone runs).
PAGE_SCRIPTS = ("**/static/backend.js", "**/static/app.js", "**/static/cad/main.js", "**/static/library.js")
TOGGLE_PAGES = (("index.html", RECT_URL), ("library.html", URL + "library.html"))


def looks(state, expected):
    return all(state.get(key) == value for key, value in expected.items())


def toggle_context(browser, system="light", width=WIDTH, height=HEIGHT, scripts=()):
    context = browser.new_context(viewport={"width": width, "height": height}, color_scheme=system)
    for script in scripts:
        context.add_init_script(script)
    context.errors = []
    context.on("console", lambda message: context.errors.append(message.text) if message.type == "error" else None)
    context.on("weberror", lambda error: context.errors.append(str(error.error)))
    return context


def open_toggle_page(page, url):
    page.goto(url)
    if url == RECT_URL:
        wait_until(page, RECT_DONE, 120)
    else:
        wait_until(page, "() => document.querySelectorAll('.lib-card').length > 0", 30)
    page.mouse.move(WIDTH - 2, HEIGHT - 2)
    page.wait_for_timeout(150)
    return page.evaluate(TOGGLE)


def part_toggle(browser):
    """The header's toggle: light by default whatever the system says, dark on it, kept, no flash, the keyboard, phones."""
    # A dark system, nothing stored: both pages light, the toggle off.
    context = toggle_context(browser, system="dark")
    page = context.new_page()
    opened = {name: open_toggle_page(page, url) for name, url in TOGGLE_PAGES}
    check("toggle: a dark system with no stored choice opens both pages light (data-theme light, the page's grey, the bar #fbfbfd, "
          "color-scheme light), the toggle off (its moon, aria-pressed false, 'Turn dark mode on'), nothing stored",
          all(looks(state, LIGHT_LOOK) and state["stored"] is None for state in opened.values()), opened)
    named = page.get_by_role("button", name="Dark mode", exact=True).count()
    state = opened["library.html"]
    check("toggle: a button named Dark mode, 44 x 44 and round, right before GitHub (10 px) and centred on its line, the community "
          "links next to it, the same box on both pages (1440 px)",
          named == 1 and state["box"] == [44.0, 44.0] and state["round"] != "0px" and state["gap"] == 10 and state["middle"] <= 0.5 and state["next"]
          and all(other[key] == state[key] for other in opened.values() for key in ("box", "gap", "middle", "masthead")), (named, opened))
    page.screenshot(path=f"{SHOTS}/theme_toggle_light_library.png", clip={"x": 0, "y": 0, "width": WIDTH, "height": 104})
    # On: the Library dark at once and the choice stored; the generator opens dark, and after a reload.
    page.click("#themeToggle")
    page.mouse.move(WIDTH - 2, HEIGHT - 2)
    page.wait_for_timeout(150)
    flipped = page.evaluate(TOGGLE)
    page.screenshot(path=f"{SHOTS}/theme_toggle_dark_library.png", clip={"x": 0, "y": 0, "width": WIDTH, "height": 104})
    there = open_toggle_page(page, RECT_URL)
    page.reload()
    wait_until(page, RECT_DONE, 120)
    reloaded = page.evaluate(TOGGLE)
    check("toggle: clicked on the Library it turns the page dark (pressed, its sun, 'Turn dark mode off', the page black, the bar #161617, "
          "color-scheme dark) and stores dark; the generator then opens dark, and stays dark after a reload",
          all(looks(state, DARK_LOOK) and state["stored"] == "dark" for state in (flipped, there, reloaded)), [flipped, there, reloaded])
    # Off on the generator: the Library opens light, and after a reload.
    page.click("#themeToggle")
    page.wait_for_timeout(150)
    off = page.evaluate(TOGGLE)
    library = open_toggle_page(page, URL + "library.html")
    page.reload()
    page.wait_for_timeout(300)
    again = page.evaluate(TOGGLE)
    check("toggle: off on the generator (light, stored light), the Library opens light, and after a reload",
          all(looks(state, LIGHT_LOOK) and state["stored"] == "light" for state in (off, library, again)), [off, library, again])
    # The keyboard: Tab from the top reaches it (after the Library link) with the page's focus ring; Enter and Space flip it.
    page.evaluate("() => { window.scrollTo(0, 0); document.activeElement && document.activeElement.blur(); }")
    order = []
    for _ in range(16):
        page.keyboard.press("Tab")
        order.append(page.evaluate("() => document.activeElement.id || document.activeElement.className || document.activeElement.tagName"))
        if order[-1] == "themeToggle":
            break
    ring = page.evaluate("""() => { const b = document.getElementById('themeToggle'), s = getComputedStyle(b);
        return [document.activeElement === b, b.matches(':focus-visible'), s.outlineStyle, s.outlineWidth, s.outlineColor, s.outlineOffset]; }""")
    page.screenshot(path=f"{SHOTS}/theme_toggle_focus.png", clip={"x": 900, "y": 0, "width": 540, "height": 104})
    page.keyboard.press("Enter")
    after_enter = page.evaluate("() => document.documentElement.dataset.theme")
    page.keyboard.press("Space")
    after_space = page.evaluate("() => document.documentElement.dataset.theme")
    check("toggle: Tab reaches it after the Library link with the focus ring (2 px, the focus blue, 2 px out); Enter turns dark on, Space off",
          order[-1] == "themeToggle" and "masthead-library" in order[-2:-1] and ring[:4] == [True, True, "solid", "2px"]
          and ring[4] == "rgb(0, 113, 227)" and ring[5] == "2px" and after_enter == "dark" and after_space == "light", [order, ring, after_enter, after_space])
    # Two tabs (the generator opens the Library in a new one): a flip in one, the other follows.
    other = context.new_page()
    open_toggle_page(other, RECT_URL)
    page.click("#themeToggle")
    followed = None
    for _ in range(50):
        followed = other.evaluate("() => document.documentElement.dataset.theme")
        if followed == "dark":
            break
        other.wait_for_timeout(40)
    pressed = other.evaluate("() => document.getElementById('themeToggle').getAttribute('aria-pressed')")
    check("toggle: a second tab follows a flip in the first (the storage event: the generator dark, its toggle pressed)",
          followed == "dark" and pressed == "true", [followed, pressed])
    # The first tab clears the storage (the event's key null; the review of 2026-11-06): nothing stored, the second light.
    page.evaluate("() => localStorage.clear()")
    cleared = None
    for _ in range(50):
        cleared = other.evaluate("() => [document.documentElement.dataset.theme, document.getElementById('themeToggle').getAttribute('aria-pressed')]")
        if cleared[0] == "light":
            break
        other.wait_for_timeout(40)
    check("toggle: the second tab follows the first's clear() of the storage too (light, its toggle not pressed, as its next reload opens)",
          cleared == ["light", "false"], cleared)
    check("toggle: no console error (both pages, every flip)", not context.errors, context.errors[:5])
    context.close()
    # No flash: dark stored (the toggle clicked on a first page), each page opened anew with the attribute recorded from the
    # document's creation: set before <body> is parsed and before the first paint; DOMContentLoaded sees it.
    context = toggle_context(browser, scripts=(FIRST_PAINT,))
    page = context.new_page()
    open_toggle_page(page, URL + "library.html")
    page.click("#themeToggle")
    early = {}
    for name, url in TOGGLE_PAGES:
        open_toggle_page(page, url)
        early[name] = page.evaluate(FIRST_PAINT_READ)
    check("no flash: with dark stored, on both pages data-theme dark is set before <body> is inserted and before the first paint, "
          "and DOMContentLoaded sees it", all(seen["order"][:2] == ["theme:dark", "body"] and seen["ready"] == "dark" and seen["firstPaint"] is not None
                                               and seen["setAt"] <= seen["firstPaint"] for seen in early.values()), early)
    # The first screen with the pages' own scripts blocked (theme.js alone runs): already dark.
    for pattern in PAGE_SCRIPTS:
        page.route(pattern, lambda route: route.abort())
    first = {}
    for name, url in (("index.html", URL), ("library.html", URL + "library.html")):
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(200)
        path = f"{SHOTS}/theme_first_screen_dark_{name.split('.')[0]}.png"
        page.screenshot(path=path)
        first[name] = page.evaluate("""() => [document.documentElement.dataset.theme, getComputedStyle(document.querySelector('.masthead')).backgroundColor,
            getComputedStyle(document.body).backgroundColor]""") + [pixel(path, 6, 6)]
    check("no flash: with the pages' own scripts blocked the first screen is already dark on both pages (data-theme dark, the bar "
          "#161617, the page black; the shot's corner the bar's)", all(state[:3] == ["dark", "rgb(22, 22, 23)", "rgb(0, 0, 0)"]
                                                                         and state[3] == (22, 22, 23) for state in first.values()), first)
    context.close()
    context = toggle_context(browser, system="dark")
    page = context.new_page()
    for pattern in PAGE_SCRIPTS:
        page.route(pattern, lambda route: route.abort())
    plain = {}
    for name, url in (("index.html", URL), ("library.html", URL + "library.html")):
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(200)
        path = f"{SHOTS}/theme_first_screen_light_{name.split('.')[0]}.png"
        page.screenshot(path=path)
        plain[name] = [page.evaluate("() => document.documentElement.dataset.theme"), pixel(path, 6, 6)]
    check("no flash: a dark system with nothing stored, the first screen light on both pages (the bar #fbfbfd)",
          all(state == ["light", (251, 251, 253)] for state in plain.values()), plain)
    context.close()
    # Storage blocked: the pages open light, the toggle still flips the page, a reload is light again.
    context = toggle_context(browser, scripts=(NO_STORAGE,))
    page = context.new_page()
    blocked = {}
    for name, url in TOGGLE_PAGES:
        state = open_toggle_page(page, url)
        page.click("#themeToggle")
        page.wait_for_timeout(100)
        flipped = page.evaluate(TOGGLE)
        page.reload()
        page.wait_for_timeout(400)
        blocked[name] = [state, flipped, page.evaluate(TOGGLE)]
    check("toggle: with storage blocked both pages open light, the toggle still turns the page dark, a reload is light again; no console error",
          all(looks(a, LIGHT_LOOK) and looks(b, DARK_LOOK) and looks(c, LIGHT_LOOK) and a["stored"] == "blocked" for a, b, c in blocked.values())
          and not context.errors, [blocked, context.errors[:3]])
    context.close()
    # Phones: on the title's line before GitHub (6 px), a circle as the community's, as large as the line has room for
    # (40, 36, 32 px), the header as tall as before the toggle; a tap flips it.
    phones = {}
    for width, height, mast, size in ((390, 844, 239.0, 40.0), (375, 812, 239.0, 36.0), (320, 700, 238.5, 32.0)):
        context = toggle_context(browser, width=width, height=height)
        page = context.new_page()
        for name, url in TOGGLE_PAGES:
            state = open_toggle_page(page, url)
            page.click("#themeToggle")
            page.wait_for_timeout(100)
            tapped = page.evaluate(TOGGLE)
            page.screenshot(path=f"{SHOTS}/theme_toggle_{width}_{name.split('.')[0]}.png", clip={"x": 0, "y": 0, "width": width, "height": 240})
            page.click("#themeToggle")
            links = page.evaluate("() => [...document.querySelectorAll('.masthead-link')].map(a => { const r = a.getBoundingClientRect(); return [r.width, r.height]; })")
            phones[(width, name)] = [state["box"], state["gap"], state["middle"], state["masthead"], mast, tapped["theme"],
                                     page.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth"), size, links]
        context.close()
    check("toggle: at 390, 375 and 320 px on the title's line before GitHub (6 px), 40, 36 and 32 px circles as the community's, the header "
          "as tall as before it (239, 239 and 238.5 px), a tap flips it, no sideways scroll",
          all(box == [size, size] and links == [[size, size]] * 2 and gap == 6 and middle <= 0.5 and abs(height - mast) <= 0.5 and theme == "dark"
              and overflow <= 0 for box, gap, middle, height, mast, theme, overflow, size, links in phones.values()),
          {f"{k[0]} {k[1]}": v for k, v in phones.items()})


def pixel(path, x, y):
    """The sRGB colour of a screenshot's pixel (Pillow, as the other checks read their shots)."""
    from PIL import Image
    return Image.open(path).convert("RGB").getpixel((x, y))


def part_schemes(browser):
    """Both schemes, both modes: scroll invariance, the first screen, the scheme, the colours, the hit targets."""
    base, source = baseline()
    print(f"first-screen baseline: {base} ({source})", flush=True)
    for scheme in ("light", "dark"):
        results, seen = {}, set()
        # Gen by Surface, as it opens: its default part's sensor built, Advanced Customization folded.
        page = new_page(browser, scheme)
        open_cad(page)
        label = f"{scheme}, Gen by Surface"
        quick = page.evaluate("() => [document.getElementById('cadQuickGenerate').getBoundingClientRect().bottom, document.getElementById('cadCustomize').open]")
        check(f"{label}: the first screen: Generate sensor's bottom at most {FIRST_SCREEN} px and no lower than before the theme "
              f"({base['cadQuickGenerateBottom']} px), Advanced Customization folded", quick[0] <= FIRST_SCREEN and quick[0] <= base["cadQuickGenerateBottom"] + 0.5
              and not quick[1], quick)
        page.screenshot(path=f"{SHOTS}/theme_{scheme}_cad.png")
        check_scheme(page, scheme, label, "cad")
        fading = page.evaluate(FADING)
        check(f"{label}: no colour fades: every button's, summary's and header link's transition 0s", not fading, fading[:6])
        page.focus("#cadView")
        ring = page.evaluate("() => { const v = document.getElementById('cadView'); const a = getComputedStyle(v, '::after');"
                             " return [v.matches(':focus-visible'), a.content, a.position, a.boxShadow, a.pointerEvents]; }")
        check(f"{label}: the 3D view's keyboard focus ring above its canvas (its ::after: an inset 2 px ring, the pointer let through)",
              ring[0] and ring[1] == '""' and ring[2] == "absolute" and "inset" in ring[3] and "2px" in ring[3] and ring[4] == "none", ring)
        page.evaluate("() => document.activeElement.blur()")
        scroll_invariance(page, label)
        colours(page, "cad", results)
        hit_targets(page, label, seen)
        page.click("#cadCustomize > summary")
        page.wait_for_timeout(400)
        check_scheme(page, scheme, label + ", Advanced Customization open", "cad")
        colours(page, "cad, Advanced Customization open", results)
        if page.is_enabled("#cadEditBorder"):
            page.click("#cadEditBorder")
            page.wait_for_timeout(400)
            colours(page, "cad, the border editor on", results)
            page.click("#cadEditBorder")
            page.wait_for_timeout(300)
        page.screenshot(path=f"{SHOTS}/theme_{scheme}_cad_open.png")
        # A setting changed (the pitch): Fit is the guide's next step, so it is the fold's one blue action (Generate &
        # validate waits for the new fit, off).
        page.fill("#cadPitch", "1.5")
        page.dispatch_event("#cadPitch", "input")
        page.dispatch_event("#cadPitch", "change")
        page.wait_for_timeout(300)
        page.mouse.move(WIDTH - 2, HEIGHT - 2)
        page.wait_for_timeout(100)
        fit = page.evaluate(f"""() => {{ const f = document.getElementById('cadFit'), g = document.getElementById('cadGenerate');
            return [Boolean(document.querySelector('{FIT_NEXT}')), f.disabled, getComputedStyle(f).backgroundColor, getComputedStyle(f).color,
                    g.disabled, getComputedStyle(g).backgroundColor]; }}""")
        check(f"{label}: a setting changed: Fit the guide's next step and the fold's one blue action (rgb(0, 113, 227), white), "
              "Generate & validate off and not blue", fit[0] and not fit[1] and fit[2] == "rgb(0, 113, 227)" and fit[3] == "rgb(255, 255, 255)"
              and fit[4] and fit[5] != "rgb(0, 113, 227)", fit)
        colours(page, "cad, a setting changed (Fit next)", results)
        check(f"{label}: no console error", not page.errors, page.errors[:5])
        page.context.close()
        # #rect: the results, the downloads; its folds; stale.
        page = new_page(browser, scheme)
        open_rect(page)
        label = f"{scheme}, #rect"
        bottom = page.evaluate("() => { const r = document.getElementById('generate').getBoundingClientRect(); return [r.top, r.bottom]; }")
        check(f"{label}: the first screen: Generate & validate in the window and no lower than before the theme ({base['generateBottomRect']} px)",
              bottom[0] >= 0 and bottom[1] <= HEIGHT and bottom[1] <= base["generateBottomRect"] + 0.5, bottom)
        page.screenshot(path=f"{SHOTS}/theme_{scheme}_rect.png")
        check_scheme(page, scheme, label, "rect")
        scroll_invariance(page, label)
        colours(page, "rect", results)
        hit_targets(page, label, seen)
        for selector in ("#moreFiles > summary", "#manufacturingNote > summary", "#drcPanel > summary", "#formCustomize > summary", "#formAdvanced > summary"):
            if page.is_visible(selector):
                page.click(selector)
                page.wait_for_timeout(150)
        colours(page, "rect, its folds open", results)
        hit_targets(page, label + ", its folds open", seen)
        page.evaluate("() => window.scrollTo(0, 0)")
        page.fill("#rows", "11")
        page.dispatch_event("#rows", "input")
        page.wait_for_timeout(500)
        colours(page, "rect, stale", results)
        # Out of date, the previews stay lightboxes: light, styles.css's fade (half opacity, greyed) over the white card;
        # dark, opaque and paled by the filter (half opacity over the dark card left a grey slab).
        fade = page.evaluate("""() => [document.getElementById('workbench').classList.contains('is-stale'),
            ...['#rowCard .canvas-wrap', '#stackedPreview'].map(s => { const c = getComputedStyle(document.querySelector(s)); return [c.opacity, c.filter]; })]""")
        paled = all(opacity == "1" and "grayscale(0.7)" in filt and "contrast(" in filt and "brightness(1.5)" in filt for opacity, filt in fade[1:])
        halved = all(opacity == "0.5" and filt == "grayscale(0.7)" for opacity, filt in fade[1:])
        check(f"{label}, stale: the previews and the stacked view faded as lightboxes ("
              + ("opaque, paled by the filter" if scheme == "dark" else "styles.css's half opacity, greyed") + ")",
              fade[0] and (paled if scheme == "dark" else halved), fade)
        # A failing design check (the server's reply with the Row FPC's first rule failed): the design checks open on it.
        page.route("**/api/generate", flip_a_check)
        page.click("#regenerate" if page.is_visible("#regenerate") else "#generate")
        page.wait_for_timeout(60)
        wait_until(page, RECT_DONE, 120)
        page.wait_for_timeout(300)
        page.unroute("**/api/generate")
        failing = page.evaluate("() => [document.getElementById('drcPanel').open, document.getElementById('drcTotal').textContent]")
        check(f"{label}: a failing check opens the design checks", failing[0] and failing[1].startswith("1 of "), failing)
        page.locator("#drcPanel").scroll_into_view_if_needed()
        page.screenshot(path=f"{SHOTS}/theme_{scheme}_rect_failing.png")
        colours(page, "rect, a failing check", results)
        hit_targets(page, label + ", a failing check", seen)
        check(f"{label}: no console error", not page.errors, page.errors[:5])
        page.context.close()
        check(f"{scheme}: the hit targets were measured on each kind of small control", seen == set(TARGETS), sorted(set(TARGETS) - seen))
        check(f"{scheme}: blue fills only the primary actions (Generate sensor, Generate & validate, the Gerber ZIPs) and the selection "
              "states, in eight states", not results.get("blue"), results.get("blue", [])[:8])
        check(f"{scheme}: no element larger than 12 px filled green, in eight states", not results.get("green"), results.get("green", [])[:8])
        check(f"{scheme}: none of styles.css's old palette (teal, stray blues, teal-cast greys and ink) outside the drawings, in eight states",
              not results.get("old"), sorted(set(results.get("old", [])))[:12])


def part_reduced_motion(browser):
    """prefers-reduced-motion: reduce: no transition, the guide's scrolls jump, a press neither scales nor moves."""
    page = new_page(browser, motion="reduce")
    open_cad(page)
    check("reduced motion: the page sees prefers-reduced-motion: reduce", page.evaluate("() => matchMedia('(prefers-reduced-motion: reduce)').matches"))
    arrows = page.evaluate("""() => ['#cadCustomize > summary', '#guideCustomize', '#drcPanel > summary', '#cadFileMore > summary']
        .map(s => [s, getComputedStyle(document.querySelector(s), '::before').transitionDuration])""")
    check("reduced motion: the disclosure arrows' transition 0s", all(set(duration.split(", ")) == {"0s"} for _, duration in arrows), arrows)
    moving = page.evaluate("""() => [...document.querySelectorAll('button, summary, a.masthead-link, .preview-tabs button, .look-bar button')]
        .map(n => [n.id || n.className || n.tagName, getComputedStyle(n).transitionDuration]).filter(([, d]) => d.split(', ').some(x => x !== '0s'))""")
    check("reduced motion: every button's, summary's and header link's transition 0s", not moving, moving[:6])
    page.evaluate("() => window.scrollTo(0, 0)")
    page.wait_for_timeout(200)
    page.click('[data-go="downloadsTitle"]')
    page.wait_for_timeout(80)
    early = page.evaluate("() => [document.getElementById('downloadsTitle').getBoundingClientRect().top, Math.abs(scrollY + innerHeight - document.documentElement.scrollHeight) < 2]")
    page.wait_for_timeout(700)
    late = page.evaluate("() => document.getElementById('downloadsTitle').getBoundingClientRect().top")
    check("reduced motion: a guide step jumps: 80 ms after the click its target is in its place (0-300 px from the top, or the page's end) and stays",
          (0 <= early[0] <= 300 or early[1]) and abs(early[0] - late) < 2, [early, late])
    page.evaluate("() => window.scrollTo(0, 0)")
    page.wait_for_timeout(200)
    page.click("#guideCustomize")
    page.wait_for_timeout(80)
    fold = page.evaluate("() => [document.getElementById('cadCustomize').getBoundingClientRect().top, document.getElementById('cadCustomize').open]")
    check("reduced motion: the guide's Advanced Customization switch opens the fold and jumps to it (80 ms after the click, 0-300 px from the top)",
          fold[1] and 0 <= fold[0] <= 300, fold)
    page.click("#guideCustomize")
    page.wait_for_timeout(200)
    page.evaluate("() => window.scrollTo(0, 0)")
    page.wait_for_timeout(200)
    box = page.locator(".cad-views button").first.bounding_box()
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.mouse.down()
    page.wait_for_timeout(60)
    pressed = page.evaluate("() => { const n = document.querySelector('.cad-views button'); const s = getComputedStyle(n); return [n.matches(':active'), s.transform, s.scale, s.translate]; }")
    page.mouse.move(WIDTH - 2, HEIGHT - 2)
    page.mouse.up()
    check("reduced motion: a button held down is neither scaled nor moved (transform, scale, translate none)",
          pressed[0] and pressed[1:] == ["none", "none", "none"], pressed)
    check("reduced motion: no animation, scroll-behavior auto", page.evaluate(
        "() => document.getAnimations().length === 0 && getComputedStyle(document.documentElement).scrollBehavior === 'auto'"))
    check("reduced motion: no console error", not page.errors, page.errors[:5])
    page.context.close()


def part_reduced_transparency(browser):
    """prefers-reduced-transparency: reduce (CDP): the 3D view's pills solid and light, light and dark."""
    for scheme in ("light", "dark"):
        page = new_page(browser, scheme, features=[{"name": "prefers-reduced-transparency", "value": "reduce"}])
        open_cad(page)
        media = page.evaluate("s => [matchMedia('(prefers-reduced-transparency: reduce)').matches, document.documentElement.dataset.theme === s]", scheme)
        pills = page.evaluate("""() => ['.cad-view-tools', '.cad-views', '.cad-status'].map(s => { const c = getComputedStyle(document.querySelector(s));
            return [s, c.backdropFilter, c.webkitBackdropFilter, c.backgroundColor]; })""")
        solid = all(backdrop == "none" and webkit in (None, "none") and rgba(colour)[3] >= 0.95 and rgba(colour)[:3] == (255.0, 255.0, 255.0)
                    for _, backdrop, webkit, colour in pills)
        check(f"{scheme}, reduced transparency: the 3D view's pills without backdrop filter, their material opaque (alpha .95 or more) and light",
              media == [True, True] and solid, [media, pills])
        check(f"{scheme}, reduced transparency: no console error", not page.errors, page.errors[:5])
        page.context.close()


def part_contrast_and_forced(browser):
    """More contrast and forced colours at #rect: smoke, the chosen segments outlined."""
    page = new_page(browser, contrast="more")
    open_rect(page)
    data = page.evaluate("""() => ({more: matchMedia('(prefers-contrast: more)').matches, card: getComputedStyle(document.getElementById('rowCard')).borderTopColor,
        note: getComputedStyle(document.getElementById('downloadNote')).color,
        links: [...document.querySelectorAll('a:not(.masthead-link)')].filter(a => a.checkVisibility()).map(a => [a.textContent.trim().slice(0, 30), getComputedStyle(a).textDecorationLine])})""")
    check("more contrast: the cards edged in the control border (#6e6e73), the secondary text #424245, every link in the text underlined "
          "(the header's GitHub and Discord are pills)", data["more"] and data["card"] == "rgb(110, 110, 115)" and data["note"] == "rgb(66, 66, 69)"
          and data["links"] and all("underline" in line for _, line in data["links"]), data)
    page.screenshot(path=f"{SHOTS}/theme_more_contrast_rect.png")
    check("more contrast: no console error", not page.errors, page.errors[:5])
    page.context.close()
    page = new_page(browser, forced="active")
    open_rect(page)
    outlines = page.evaluate("""() => ['.mode-picker input:checked + span', '.preview-tabs button[aria-selected="true"]',
        '.mode-switch button[aria-pressed="true"]', '.look-bar button[aria-pressed="true"]'].map(s => { const n = document.querySelector(s);
          return [s, n ? getComputedStyle(n).outlineStyle : null, n ? getComputedStyle(n).outlineWidth : null]; })""")
    check("forced colours: the chosen mode, preview tab, stacked view mode and look outlined (2 px)",
          page.evaluate("() => matchMedia('(forced-colors: active)').matches") and all(style == "solid" and width == "2px" for _, style, width in outlines), outlines)
    page.screenshot(path=f"{SHOTS}/theme_forced_rect.png")
    check("forced colours: no console error", not page.errors, page.errors[:5])
    page.context.close()



# The Library (library.html, the user's requests of 2026-11-05): the action blue fills only Open in Gen by Surface.
LIBRARY_BLUE = [".lib-open"]
LIBRARY_LINKS = """() => [...document.querySelectorAll('a')].filter(a => a.checkVisibility() && !a.matches('.masthead-link, .lib-card, .lib-open, .lib-pill'))
    .map(a => [a.textContent.trim().slice(0, 30), getComputedStyle(a).textDecorationLine, getComputedStyle(a.querySelector('span') || a).textDecorationLine])"""


def part_library(browser):
    """The Library and the header's link in the theme: Generate sensor's bottom still at most 857.1 px on the generator (the
    link changes no line of its header at 1440 px; 850.1 measured); library.html in the light and the dark scheme, its grid
    and a sensor's page, the action blue filling only Open in Gen by Surface, nothing green, none of styles.css's old
    palette, no colour fades; under more contrast every text link underlined (the header's Library link too, there and
    on the generator)."""
    page = new_page(browser)
    open_cad(page)
    bottom = page.evaluate("() => Math.round(document.getElementById('cadQuickGenerate').getBoundingClientRect().bottom * 10) / 10")
    check("library: Generate sensor's bottom at most 857.1 px with the header's Library link (1440 x 900)", bottom <= 857.1, bottom)
    page.context.close()
    for scheme in ("light", "dark"):
        page = new_page(browser, scheme=scheme)
        found = {}
        for fragment in ("", "#i2rt-yam-1mm"):
            page.goto(URL + "library.html" + fragment)
            wait_until(page, "() => document.querySelectorAll('.lib-card').length > 0", 30)
            page.wait_for_timeout(300)
            page.mouse.move(WIDTH - 2, HEIGHT - 2)
            scan = page.evaluate(SCAN, [DRAWINGS + ", .lib-shot", LIBRARY_BLUE, [], sorted({value for values in OLD_PALETTE.values() for value in values}), []])
            for key in ("blue", "green", "old"):
                found.setdefault(key, []).extend(scan[key])
            found.setdefault("fading", []).extend(page.evaluate(FADING.replace("a.masthead-link", "a")))
        opened = page.evaluate("() => getComputedStyle(document.querySelector('.lib-open')).backgroundColor")
        check(f"library {scheme}: the action blue fills only Open in Gen by Surface ({opened}), nothing green, none of styles.css's old palette, "
              "no colour fades", not any(found.values()) and opened == "rgb(0, 113, 227)", {key: value[:4] for key, value in found.items()})
        page.screenshot(path=f"{SHOTS}/theme_library_{scheme}.png")
        check(f"library {scheme}: no console error", not page.errors, page.errors[:5])
        page.context.close()
    page = new_page(browser, contrast="more")
    page.goto(URL + "library.html#widowx-250-1mm")
    wait_until(page, "() => document.querySelectorAll('.lib-card').length > 0", 30)
    links = page.evaluate(LIBRARY_LINKS)
    open_rect(page)
    header = page.evaluate("() => getComputedStyle(document.querySelector('.masthead-library')).textDecorationLine")
    check("library: under more contrast every text link of the Library underlined, and the header's Library link on the generator",
          links and all("underline" in own or "underline" in inner for _, own, inner in links) and "underline" in header, (links, header))
    page.context.close()

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(args=WEBGL_ARGS)
        parts = (part_toggle, part_schemes, part_reduced_motion, part_reduced_transparency, part_contrast_and_forced)
        parts += (part_library,)  # the Library and the header's link (2026-11-05)
        chosen = [part for part in parts if len(sys.argv) < 2 or part.__name__ in sys.argv[1:]]
        for part in chosen:
            print(f"--- {part.__name__}", flush=True)
            started = time.monotonic()
            try:
                part(browser)
            except Exception as error:  # noqa: BLE001 - report and continue
                check(f"{part.__name__} ran to completion", False, repr(error))
            print(f"    ({time.monotonic() - started:.0f} s)", flush=True)
        browser.close()
    return summary()


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
