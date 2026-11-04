"""The page's Apple-style theme (web/theme.css over web/styles.css) in the browser, light and dark.

Against a running app.py (FPC_PORT), on pages as the user opens them (no fold opened by an init script), 1440 x 900:
- part_schemes, in the light and the dark scheme, in Gen by Surface (its default part's sensor built) and at #rect:
  - scrolling changes nothing: the whole page scrolled to its end in 300 px steps and back, every element's opacity,
    transform, visibility, filter, backdrop filter and classes (but the guide's .is-here, which follows the scroll) as
    they were, no animation started; scroll-behavior auto, every element's animation timeline auto and no scroll or
    view timeline named;
  - the first screen: Generate sensor's bottom at most 876 px and at most the page's before the theme, the rectangular
    form's Generate & validate in the window and no lower than before the theme (FPC_THEME_BASELINE: a JSON file with
    cadQuickGenerateBottom and generateBottomRect, else the values measured on the page before the theme);
  - the scheme: light, the page's grey (#f5f5f7) and color-scheme light; dark, the shell dark (the page, the header,
    the guide, the cards, the form, the fields, the design checks' row) with light text, the drawings' areas light
    lightboxes (the 3D view's #f5f5f7 and its pills' light material, the previews' white, the stacked view's grey, the
    map's white; color-scheme light there);
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
    zoom buttons, the design checks' row and its Show all checks (shown on a failure), the camera buttons at least 24 x 24 px;
  - no console error.
  Gen by Surface's default part loads once more when it failed (a server busy with another client's fit answers 503).
- part_reduced_motion (prefers-reduced-motion: reduce): the disclosure arrows' and every button's, summary's and header
  link's transition 0s; a guide step and its Advanced Customization switch jump (80 ms after the click the target is in its place);
  a button held down is neither scaled nor moved; no animation.
- part_reduced_transparency (prefers-reduced-transparency: reduce, by CDP), light and dark: the 3D view's three pills
  without backdrop filter, their material opaque (alpha .95 or more) and light.
- part_contrast_and_forced: prefers-contrast more (the cards edged in the control border, the secondary text darker,
  links underlined) and forced colours (the chosen mode, tab, stacked view mode and look outlined): smoke, no console
  error.
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

from rp import DONE, RECT_URL, SHOTS, URL, check, summary, wait_until  # noqa: E402

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
RECT_DONE = "() => (" + DONE[6:] + ") && !document.querySelector('#status').textContent.startsWith('Deriving')"

# The drawings and what they draw keep their own colours (the plan's sections 1 and 5): the SVGs, the 3D view's canvas,
# the photos, the oblique and stacked scenes, the legends' swatches and the stacked view's ring keys (teal and orange).
DRAWINGS = "svg, canvas, img, .oblique-board, .assembly-scene, .swatch, .assembly-key, .coin-ref, .coin-plane"
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
           "Show all checks": ".drc-bar button", "the camera buttons": ".cad-views button"}

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
  return {html: pick('html', ['colorScheme']), body: pick('body', ['backgroundColor', 'color']),
    masthead: pick('.masthead', ['backgroundColor', 'color']), title: pick('.masthead h1', ['color']),
    guide: pick('.flow-guide', ['backgroundColor']), workspace: pick('#cadWorkspace', ['backgroundColor', 'color']),
    hint: pick('.cad-title-hint', ['color']), card: pick('#rowCard', ['backgroundColor', 'color']), downloads: pick('.downloads', ['backgroundColor']),
    controls: pick('.controls', ['backgroundColor']), field: pick('#rows', ['backgroundColor', 'color']), drc: pick('.drc-panel > summary', ['backgroundColor']),
    view: pick('.cad-view', ['backgroundColor', 'colorScheme']), tools: pick('.cad-view-tools', ['backgroundColor', 'colorScheme']),
    status3d: pick('#cadStatus', ['color']), canvas: pick('.canvas-wrap', ['backgroundColor', 'colorScheme']),
    stacked: pick('.stacked-canvas', ['backgroundImage', 'colorScheme']), map: pick('.cad-flat', ['backgroundColor', 'colorScheme'])}; }"""


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


def new_page(browser, scheme="light", motion="no-preference", forced="none", contrast="no-preference", features=None):
    context = browser.new_context(viewport={"width": WIDTH, "height": HEIGHT}, color_scheme=scheme, reduced_motion=motion,
                                  forced_colors=forced, contrast=contrast)
    page = context.new_page()
    page.errors = []
    page.on("console", lambda message: page.errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: page.errors.append(str(error)))
    if features:
        # CDP replaces the emulated features as a whole: the scheme and motion are named again with the extra ones.
        session = context.new_cdp_session(page)
        session.send("Emulation.setEmulatedMedia", {"features": [{"name": "prefers-color-scheme", "value": scheme},
                                                                 {"name": "prefers-reduced-motion", "value": motion}] + features})
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
        check(f"{label}: light: the page's grey (#f5f5f7), color-scheme light", data["body"]["backgroundColor"] == "rgb(245, 245, 247)"
              and data["html"]["colorScheme"] == "light", data["body"])
        return
    shell = {"body": data["body"], "masthead": data["masthead"], "workspace" if mode == "cad" else "controls": data["workspace" if mode == "cad" else "controls"],
             "card": data["card"], "downloads": data["downloads"], "field": data["field"], "design checks": data["drc"]}
    if mode == "cad":
        shell["guide"] = data["guide"]
    dark = {name: luminance(value["backgroundColor"]) for name, value in shell.items()}
    text = {name: luminance(data[name]["color"]) for name in ("body", "title", "card", "field")}
    secondary = luminance(data["hint"]["color"])
    check(f"{label}: dark: the shell dark (the page, the header{', the guide, the workspace' if mode == 'cad' else ', the form'}, the cards, "
          "the fields, the design checks' row: luminance under .03), its text light (over .6; the secondary grey over .25), color-scheme dark",
          all(value < 0.03 for value in dark.values()) and all(value > 0.6 for value in text.values()) and secondary > 0.25
          and data["html"]["colorScheme"] == "dark",
          {"backgrounds": {k: round(v, 4) for k, v in dark.items()}, "text": {k: round(v, 3) for k, v in text.items()}, "secondary": round(secondary, 3)})
    boxes = {"canvas": data["canvas"]["backgroundColor"] == "rgb(255, 255, 255)" and data["canvas"]["colorScheme"] == "light",
             "stacked": "rgb(245, 245, 247)" in data["stacked"]["backgroundImage"] and data["stacked"]["colorScheme"] == "light"}
    if mode == "cad":
        boxes.update(view=data["view"]["backgroundColor"] == "rgb(245, 245, 247)" and data["view"]["colorScheme"] == "light",
                     tools=rgba(data["tools"]["backgroundColor"])[:3] == (255.0, 255.0, 255.0) and data["tools"]["colorScheme"] == "light",
                     status=luminance(data["status3d"]["color"]) < 0.05,
                     map=data["map"]["backgroundColor"] == "rgb(255, 255, 255)" and data["map"]["colorScheme"] == "light")
    check(f"{label}: dark: the drawings' areas stay light lightboxes ({', '.join(boxes)}: their light colours, color-scheme light)",
          all(boxes.values()), {"boxes": boxes, "data": {k: data[k] for k in ("view", "tools", "status3d", "canvas", "stacked", "map")}})


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
        media = page.evaluate("s => [matchMedia('(prefers-reduced-transparency: reduce)').matches, matchMedia('(prefers-color-scheme: ' + s + ')').matches]", scheme)
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


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(args=WEBGL_ARGS)
        parts = (part_schemes, part_reduced_motion, part_reduced_transparency, part_contrast_and_forced)
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
