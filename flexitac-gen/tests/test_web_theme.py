"""The page's Apple-style theme (web/theme.css, over web/styles.css): static checks that need no browser.

- index.html links theme.css once, right after styles.css, by a relative URL (the static site copies web/ as it is).
- theme.css loads nothing: no @import, @font-face or @layer (a layer would lose to styles.css), no URL but data:
  ones (the SVG namespace inside them aside), the system font stack.
- Motion is interaction feedback only: no animation, no scroll- or view-driven timeline, no @starting-style, no
  content-visibility, no smooth scrolling, nothing fixed or sticky of its own; a transform and a transition only on
  the disclosure arrows (no colour fades: a hover, a press and every state change at once); every transition of the
  page (styles.css's and theme.css's) off under prefers-reduced-motion.
- What the browser checks and the drawings rely on stays styles.css's (the plan's section 3.0): no SVG element styled,
  the pin-1 rings, the zoom pane's SVG, the stacked view's faces and the view labels untouched, no input's appearance,
  the guide's and the map's sticky boxes, nothing on the 3D chain or its ancestors that flattens it (filter, opacity,
  overflow, backdrop-filter, contain, isolation; styles.css's own stale fade there may only be re-valued, as the dark
  scheme does), no overflow but visible on the boxes that hold a sticky one, no flex
  status or banner, nothing hidden by opacity or visibility, one !important (styles.css's own on .locked, mirrored).
- Type: a font shorthand always names a family (one without is dropped); body's size and leading are styles.css's.
- Colour: the palette's text pairs reach WCAG's 4.5:1 and its control edges and focus ring 3:1, light and dark, with
  more contrast too, computed from the hex values; the drawing areas (lightboxes) take the light palette in every
  scheme; the 3D view's background is viewer.js's clear colour.
- web/'s JavaScript has no IntersectionObserver or scroll timeline, and every smooth scroll is guarded by
  prefers-reduced-motion.

The page itself is checked in a browser by tools/browser/theme_checks.py.
"""

from __future__ import annotations

import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
THEME = WEB / "theme.css"
STYLES = WEB / "styles.css"
LIGHTBOXES = (".cad-view-wrap", ".canvas-wrap", ".stacked-canvas", ".cad-flat")


# --- a small CSS reader: rules with their selectors, declarations and enclosing at-rules ------------------------------

class Rule:
    def __init__(self, selectors, declarations, conditions):
        self.selectors = selectors        # tuple of selector strings
        self.declarations = declarations  # list of (property, value, important)
        self.conditions = conditions      # tuple of the enclosing at-rules' preludes, outermost first

    def __repr__(self):
        return "Rule(%r, %r)" % (", ".join(self.selectors), self.conditions)


def _strip_comments(text):
    return re.sub(r"/\*.*?\*/", "", text, flags=re.S)


def _scan(text, start, stops):
    """The index of the first character of ``stops`` at the top level from ``start`` (outside strings and brackets)."""
    depth, quote, index = 0, None, start
    while index < len(text):
        char = text[index]
        if quote:
            if char == "\\":
                index += 1
            elif char == quote:
                quote = None
        elif char in "\"'":
            quote = char
        elif char in "([":
            depth += 1
        elif char in ")]":
            depth -= 1
        elif depth == 0 and char in stops:
            return index
        index += 1
    return len(text)


def _split(text, separator):
    parts, start = [], 0
    while start <= len(text):
        end = _scan(text, start, separator)
        parts.append(text[start:end])
        start = end + 1
    return [part.strip() for part in parts if part.strip()]


def _declarations(body):
    found = []
    for item in _split(body, ";"):
        name, colon, value = item.partition(":")
        if not colon:
            continue
        value = value.strip()
        important = bool(re.search(r"!\s*important\s*$", value))
        found.append((name.strip().lower(), re.sub(r"\s*!\s*important\s*$", "", value), important))
    return found


def parse_css(text):
    """(rules, at-rules): every style rule (inside @media / @supports too) and every at-rule's prelude."""
    text = _strip_comments(text)
    rules, at_rules = [], []

    def block(index, conditions):
        while index < len(text):
            while index < len(text) and text[index].isspace():
                index += 1
            if index >= len(text):
                return index
            if text[index] == "}":
                return index + 1
            stop = _scan(text, index, "{;}")
            prelude = " ".join(text[index:stop].split())
            if stop >= len(text) or text[stop] != "{":
                if prelude.startswith("@"):
                    at_rules.append(prelude)  # a statement: @import ...; @layer a, b;
                index = stop + 1 if stop < len(text) and text[stop] == ";" else stop
                continue
            if prelude.startswith("@"):
                at_rules.append(prelude)
                if prelude.split()[0] in ("@media", "@supports", "@layer", "@container", "@scope", "@document"):
                    index = block(stop + 1, conditions + (prelude,))
                else:  # @font-face, @keyframes, @property, @starting-style ...: their body is not a style rule here
                    index = _skip_block(stop + 1)
                continue
            end = _scan(text, stop + 1, "}")
            rules.append(Rule(tuple(_split(prelude, ",")), _declarations(text[stop + 1:end]), conditions))
            index = end + 1
        return index

    def _skip_block(index):
        depth = 1
        while index < len(text) and depth:
            stop = _scan(text, index, "{}")
            if stop >= len(text):
                return stop
            depth += 1 if text[stop] == "{" else -1
            index = stop + 1
        return index

    block(0, ())
    return rules, at_rules


def subject(selector):
    """The selector's last compound (what it styles), pseudo-elements included."""
    parts, start, index = [], 0, 0
    while index < len(selector):
        stop = _scan(selector, index, " >+~")
        parts.append(selector[start:stop])
        index = start = stop + 1
    return [part for part in parts if part.strip()][-1].strip()


def _has_class(compound, name):
    """Whether a compound (or selector) names the class or id ``name`` (".x", "#x"), not one it begins (.x-y)."""
    return re.search(re.escape(name) + r"(?![\w-])", compound) is not None


def _type_of(compound):
    match = re.match(r"([a-zA-Z][\w-]*|\*)", compound)
    return match.group(1).lower() if match else None


# --- colour -------------------------------------------------------------------------------------------------------------

def _colour(value):
    value = value.strip().lower()
    match = re.fullmatch(r"#([0-9a-f]{3}|[0-9a-f]{6})", value)
    if match:
        digits = match.group(1)
        if len(digits) == 3:
            digits = "".join(char * 2 for char in digits)
        return tuple(int(digits[i:i + 2], 16) for i in (0, 2, 4)) + (1.0,)
    match = re.fullmatch(r"rgba?\(([^)]*)\)", value)
    if match:
        parts = [part for part in re.split(r"[\s,/]+", match.group(1)) if part]
        alpha = float(parts[3]) if len(parts) > 3 else 1.0
        return tuple(float(part) for part in parts[:3]) + (alpha,)
    raise ValueError("not a colour: %r" % value)


def _over(colour, background):
    """``colour`` composited over the opaque ``background``."""
    alpha = colour[3]
    return tuple(colour[i] * alpha + background[i] * (1 - alpha) for i in range(3)) + (1.0,)


def _luminance(colour):
    def channel(value):
        value /= 255.0
        return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
    red, green, blue = (channel(value) for value in colour[:3])
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast(first, second):
    lighter, darker = sorted((_luminance(first), _luminance(second)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


# --- the media a palette is computed for ------------------------------------------------------------------------------

def _holds(condition, media):
    """Whether an at-rule prelude holds for ``media`` (a dict of media features; a wide desktop window)."""
    kind, _, query = condition.partition(" ")
    if kind == "@supports":
        return not query.strip().startswith("not")  # the browsers of the checks support what the theme asks for
    if kind != "@media":
        raise AssertionError("unexpected at-rule around a palette: %s" % condition)
    for feature in re.findall(r"\(([^()]*)\)", query):
        name, _, value = (part.strip() for part in feature.partition(":"))
        if name in ("max-width", "pointer"):
            return False  # the palettes are not width- or pointer-dependent; a desktop window
        if media.get(name, "no-preference" if name.startswith("prefers-") else "none") != value:
            return False
    return True


def palette(rules, media, target=":root"):
    """The custom properties ``target`` gets for ``media``, in source order (later rules win), var() resolved."""
    tokens = {}
    for rule in rules:
        if target in rule.selectors and all(_holds(condition, media) for condition in rule.conditions):
            tokens.update({name: value for name, value, _ in rule.declarations if name.startswith("--")})

    def resolve(value, seen=()):
        match = re.fullmatch(r"var\((--[\w-]+)\)", value.strip())
        if not match:
            return value
        name = match.group(1)
        if name in seen or name not in tokens:
            raise AssertionError("unresolved token %s" % name)
        return resolve(tokens[name], seen + (name,))

    return {name: resolve(value) for name, value in tokens.items()}


MEDIA = {
    "light": {"prefers-color-scheme": "light"},
    "dark": {"prefers-color-scheme": "dark"},
    "light, more contrast": {"prefers-color-scheme": "light", "prefers-contrast": "more"},
    "dark, more contrast": {"prefers-color-scheme": "dark", "prefers-contrast": "more"},
}

# Text and what it sits on (WCAG 1.4.3, 4.5:1).  A translucent fill is taken over the surface it lies on: a tuple, the
# topmost layer first.
SURFACES = ("--surface", "--bg", "--inset", "--surface-2", "--well", "--nav", "--control-bg")
TEXT_PAIRS = (
    [(fg, bg) for fg in ("--text", "--text-2", "--link", "--ok", "--warn", "--error") for bg in SURFACES]
    + [("--ok", "--ok-tint"), ("--warn", "--warn-tint"), ("--error", "--error-tint"),
       ("--text", "--ok-tint"), ("--text", "--warn-tint"), ("--text", "--error-tint"),
       ("--base-text", "--base-tint"), ("--text", "--base-hover"), ("--text", "--thumb"),
       ("#fff", "--accent"), ("#fff", "--accent-hover"), ("#fff", "--accent-press"),
       ("--text-2-on-fill", ("--fill", "--nav")), ("--text-2-on-fill", ("--fill-hover", "--nav")),
       ("--text-2-on-fill", ("--fill", "--bg")), ("--text-2-on-fill", ("--fill", "--surface")),  # the guide's steps done
       ("--text-2", "--error-tint"),  # a PASS badge on a failing rule's row
       ("--text", ("--fill-press", "--surface")), ("--text", ("--fill-press", "--warn-tint")),
       ("--text", ("--accent-tint", "--surface"))]
)
# In the lightboxes only (light in either scheme): the 3D view's pills, their material over the view's grey (#f5f5f7,
# the light --bg), the chosen tool link blue on the selection tint, Remove model the error red.
LIGHTBOX_TEXT_PAIRS = [("--text", ("--material", "--bg")), ("--text-2", ("--material", "--bg")), ("--error", ("--material", "--bg")),
                       ("--link", ("--accent-tint", "--material", "--bg")), ("--error", ("--error-tint", "--material", "--bg"))]
# Control edges, the focus ring and the drawn marks of state (WCAG 1.4.11, 3:1).
EDGE_PAIRS = (
    [(fg, bg) for fg in ("--control-border", "--focus", "--text-3") for bg in SURFACES]
    + [("--base-edge", "--surface"), ("--base-edge", "--base-tint"), ("--ok", "--surface"), ("--warn", "--surface"),
       ("--error", "--surface")]
)


def _resolve_pair_colour(tokens, ref):
    if isinstance(ref, tuple):  # translucent fills, the topmost first, over an opaque surface
        colour = _resolve_pair_colour(tokens, ref[-1])
        for layer in reversed(ref[:-1]):
            colour = _over(_colour(tokens[layer]), colour)
        return colour
    colour = _colour(tokens[ref] if ref.startswith("--") else ref)
    if colour[3] < 1:
        raise AssertionError("%s is translucent: name the surface it lies on" % ref)
    return colour


# --- the files ----------------------------------------------------------------------------------------------------------

class _Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stylesheets, self.styles = [], 0

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "link" and "stylesheet" in (attributes.get("rel") or "").split():
            self.stylesheets.append(attributes.get("href"))
        if tag == "style":
            self.styles += 1

    handle_startendtag = handle_starttag


def _scripts():
    """web/'s own JavaScript (not the vendored three.js)."""
    return sorted(path for path in WEB.rglob("*.js") if "vendor" not in path.relative_to(WEB).parts)


class ThemeFileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = THEME.read_text(encoding="utf-8")
        cls.source = _strip_comments(cls.text)
        cls.rules, cls.at_rules = parse_css(cls.text)
        cls.styles_rules, _ = parse_css(STYLES.read_text(encoding="utf-8"))

    def _declared(self, predicate, rules=None):
        """(selector, property, value) of every declaration whose property satisfies ``predicate``."""
        return [(selector, name, value) for rule in (self.rules if rules is None else rules) for name, value, _ in rule.declarations
                if predicate(name) for selector in rule.selectors]

    def test_the_reader_reads_the_whole_file(self):
        # Every '{' opens a rule or an at-rule the reader saw: nothing hides behind a parse error.
        blocks = len(self.rules) + sum(1 for at in self.at_rules if at.split()[0] in ("@media", "@supports"))
        self.assertEqual(self.source.count("{"), blocks)
        self.assertEqual(self.source.count("{"), self.source.count("}"))
        self.assertGreater(len(self.rules), 300)

    def test_index_links_the_theme_once_after_styles_by_a_relative_url(self):
        page = _Links()
        page.feed((WEB / "index.html").read_text(encoding="utf-8"))
        self.assertEqual(page.stylesheets.count("static/theme.css"), 1, page.stylesheets)
        self.assertEqual(page.stylesheets.index("static/theme.css"), page.stylesheets.index("static/styles.css") + 1, page.stylesheets)
        for href in page.stylesheets:
            self.assertIsNone(re.match(r"([a-z]+:|/)", href), "%s: a relative URL (the site lives under a subpath)" % href)
        self.assertEqual(page.styles, 0, "no inline <style>: the CSP allows only the page's own style sheets")

    def test_it_loads_nothing_and_uses_the_system_font_stack(self):
        names = sorted({at.split()[0] for at in self.at_rules})
        self.assertEqual(set(names) - {"@media", "@supports"}, set(), "no @import, @font-face, @layer or other at-rule: %s" % names)
        # Every url() is a data: URI; the only http inside one is the SVG namespace, which SVG needs.
        urls = re.findall(r"url\(\s*([\"']?)(.*?)\1\s*\)", self.source)
        self.assertTrue(urls)
        for _, url in urls:
            self.assertTrue(url.startswith("data:"), url[:60])
        outside = re.sub(r"url\(\s*([\"']?).*?\1\s*\)", "url()", self.source)
        self.assertNotIn("http", outside.lower().replace("xmlns", ""))
        for _, url in urls:
            self.assertEqual(re.findall(r"https?:[^'\"\s]*", url), ["http://www.w3.org/2000/svg"] if "svg" in url else [])
        fonts = self._declared(lambda name: name in ("font-family", "--font", "--font-mono"))
        for selector, name, value in fonts:
            self.assertIsNone(re.search(r"\.(woff2?|ttf|otf)|local\(", value), (selector, name))
            if name.startswith("--"):
                self.assertRegex(value, r"(sans-serif|monospace)$", "the stack ends with a generic family")
            else:
                self.assertRegex(value, r"^(var\(--font(-mono)?\)|inherit)$", (selector, value))

    def test_nothing_moves_with_the_scroll_or_as_the_page_opens(self):
        # The plan's section 4: no scroll-triggered or reveal-on-scroll motion, no parallax, no entrance animation.
        for word in ("animation", "@keyframes", "scroll-timeline", "view-timeline", "animation-timeline", "@starting-style",
                     "content-visibility", "scroll-behavior", "scroll-snap", "background-attachment", "offset-path", "will-change"):
            self.assertNotIn(word, self.source, word)
        positions = {value for _, name, value in self._declared(lambda name: name == "position")}
        self.assertLessEqual(positions, {"relative", "absolute"}, "nothing fixed or sticky of the theme's own (the header is not fixed)")

    def test_a_transform_only_on_the_disclosure_arrows(self):
        moved = self._declared(lambda name: name in ("transform", "rotate", "scale", "translate", "perspective", "zoom"))
        self.assertTrue(moved)
        for selector, name, value in moved:
            self.assertRegex(subject(selector), r"^(summary|\.flow-customize)\b.*::before$", (selector, name, value))
            self.assertEqual((name, value), ("transform", "rotate(90deg)"), selector)
        # The only transition is the arrow's turn: no colour fades (a hover's fade out also ran when a button came back on
        # with the pointer elsewhere, a state change that the plan wants at once), nothing that moves a box.
        transitions = self._declared(lambda name: name.startswith("transition") and name != "transition-timing-function")
        self.assertTrue(transitions)
        for selector, name, value in transitions:
            if value in ("none",):
                continue
            self.assertEqual(name, "transition", (selector, name, value))
            for part in _split(value, ","):
                self.assertEqual(part.split()[0], "transform", (selector, part))
                self.assertRegex(subject(selector), r"^(summary|\.flow-customize)\b.*::before$", selector)

    def test_every_transition_of_the_page_is_off_under_reduced_motion(self):
        reduced = [rule for rule in self.rules if any("prefers-reduced-motion: reduce" in condition for condition in rule.conditions)]
        self.assertTrue(reduced)
        off = {selector for rule in reduced for name, value, _ in rule.declarations if name == "transition" and value == "none"
               for selector in rule.selectors}
        zeroed = {name for rule in reduced for name, value, _ in rule.declarations if name.startswith("--dur") and value in ("0ms", "0s")}
        self.assertEqual(zeroed, {"--dur-disclose"})
        for label, rules in (("theme.css", self.rules), ("styles.css", self.styles_rules)):
            for rule in rules:
                if any("prefers-reduced-motion" in condition for condition in rule.conditions):
                    continue
                for name, value, _ in rule.declarations:
                    if not name.startswith("transition") or name == "transition-timing-function" or value == "none":
                        continue
                    if name in ("transition", "transition-duration") and set(re.findall(r"[\d.]+m?s\b|var\(--[\w-]+\)", value)) <= {"0s", "0ms"}:
                        continue  # a duration of 0 (the hover's way in)
                    for selector in rule.selectors:
                        with self.subTest(file=label, selector=selector):
                            self.assertIn(selector, off, "%s's transition (%s) is not turned off under prefers-reduced-motion" % (selector, value))
                    for duration in re.findall(r"var\((--[\w-]+)\)", value):
                        self.assertIn(duration, zeroed | {"--ease", "--ease-disclose"}, (rule, value))

    def test_what_the_checks_and_the_drawings_rely_on_stays_styles_css_s(self):
        # Plan 3.0's forbidden properties.  No SVG element is styled (the drawings, the pin-1 rings, the zoom pane's SVG
        # are the server's and app.js's).
        svg_types = {"svg", "g", "path", "rect", "circle", "ellipse", "line", "polyline", "polygon", "text", "use", "image"}
        for rule in self.rules:
            for selector in rule.selectors:
                compounds = [part for part in re.split(r"[\s>+~]+", re.sub(r"\([^()]*\)", "()", selector)) if part]
                self.assertFalse({_type_of(part) for part in compounds} & svg_types, selector)
                names = {name for name, _, _ in rule.declarations}
                if "pin1-ring" in selector:
                    self.assertFalse({name for name in names if name.startswith("stroke")} | (names & {"visibility"}), selector)
                if "zoom-pane" in selector:
                    self.assertFalse(names & {"height", "min-height", "max-height", "padding"} or any(n.startswith("padding") for n in names), selector)
                if "assembly-face" in selector:
                    self.assertFalse(names & {"transform", "rotate", "translate", "scale"}, selector)
                if "view-label" in selector:
                    self.assertNotIn("display", names, selector)
                if names & {"appearance", "-webkit-appearance", "-moz-appearance"}:
                    # Never an input's (the mm inputs keep styles.css's): the rule names its element, and not input.
                    self.assertNotIn(_type_of(subject(selector)), (None, "*", "input"), selector)
                    self.assertNotIn("input", selector)
        # The guide's and the map's sticky boxes.
        sticky = {"position", "top", "bottom", "inset", "height", "min-height", "max-height", "overflow", "overflow-y", "align-self",
                  "grid-column", "grid-area"}
        for selector, name, value in self._declared(lambda name: name in sticky):
            last = subject(selector)
            self.assertFalse(_has_class(last, ".flow-guide") or _has_class(last, ".cad-flat"), (selector, name, value))
        # The 3D chain (the oblique boards, the stacked scene, the coin) and every box around it: nothing that flattens
        # preserve-3d or clips it.
        chain = (".oblique-board", ".coin-plane", ".three-d-pane", ".view-pane", ".canvas-wrap", ".stacked-canvas", ".board-card",
                 ".stacked-review", ".look-scope", ".previews", ".results", "#results", ".workbench", "#workbench", "#rowCard", "#columnCard",
                 "#rowPreview3d", "#columnPreview3d", "#stackedPreview")
        flattening = {"filter", "opacity", "overflow", "overflow-x", "overflow-y", "backdrop-filter", "-webkit-backdrop-filter", "contain",
                      "isolation", "clip-path", "mix-blend-mode"}
        # styles.css's own stale fade (.workbench.is-stale .canvas-wrap and .stacked-canvas: half opacity, a grayscale
        # filter) may be re-valued, never added to: the dark scheme keeps those lightboxes opaque and pales them by the
        # filter.  Only an opacity of 1 (none at all) and a filter styles.css sets on the same selector pass.
        fades = {(selector, name) for rule in self.styles_rules for name, _, _ in rule.declarations if name in flattening
                 for selector in rule.selectors if ".is-stale" in selector}
        self.assertIn((".workbench.is-stale .canvas-wrap", "filter"), fades, "styles.css's stale fade as the theme knows it")
        for selector, name, value in self._declared(lambda name: name in flattening):
            if (selector, name) in fades and (name != "opacity" or value == "1"):
                continue
            last = subject(selector)
            self.assertFalse(any(_has_class(last, item) for item in chain) or ".assembly-" in last
                             or _type_of(last) in ("main", "body", "html") or last.startswith(":root"), (selector, name, value))
        # The boxes that hold a sticky one: overflow visible or not set.
        holders = (".board-card", ".downloads", ".cad-workspace", ".cad-customize", ".cad-resolution", ".cad-resolution-main",
                   ".cad-resolution-map", ".drc-panel", ".workbench", ".results", ".previews", ".stacked-review")
        for selector, name, value in self._declared(lambda name: name.startswith("overflow") and name != "overflow-wrap"):
            last = subject(selector)
            if any(_has_class(last, item) for item in holders) or _type_of(last) in ("main", "body", "html"):
                self.assertEqual(value, "visible", selector)
        # The status and the banners are no flex or grid boxes (their innerText as before; their dots are ::before).
        for selector, name, value in self._declared(lambda name: name == "display"):
            last = subject(selector)
            if any(_has_class(last, item) for item in (".status", "#status", ".stale-banner", "#staleBanner", ".mask-note")):
                self.assertNotRegex(value, r"flex|grid", selector)
        # Nothing hidden by opacity or visibility (hiding is display:none, [hidden] or a closed details).
        self.assertEqual({value for _, _, value in self._declared(lambda name: name == "opacity")}, {"1"})
        self.assertEqual(self._declared(lambda name: name in ("visibility", "content-visibility")), [])
        # One !important: the mirror of styles.css's own on .locked.
        important = [(selector, name) for rule in self.rules for name, _, flag in rule.declarations if flag for selector in rule.selectors]
        self.assertEqual(important, [(".locked", "border-color")])
        self.assertTrue(any(flag for rule in self.styles_rules if ".locked" in rule.selectors for _, _, flag in rule.declarations),
                        "styles.css's .locked has its own !important (its border), which the theme's mirrors")

    def test_type_a_font_shorthand_names_a_family_and_body_keeps_its_size(self):
        generic = r"(serif|sans-serif|monospace|system-ui|ui-monospace|var\(--font(-mono)?\)|inherit|initial)\s*$"
        for selector, name, value in self._declared(lambda name: name == "font"):
            self.assertRegex(value, generic, "%s: a font shorthand without a family is dropped" % selector)
        for selector, name, value in self._declared(lambda name: name in ("font", "font-size", "line-height")):
            last = subject(selector)
            self.assertFalse(re.match(r"(body|html|:root)(\[|$|:)", last), "%s sets %s: body's size and leading are styles.css's "
                             "(the drawings' captions inherit them)" % (selector, name))
        self.assertEqual(self._declared(lambda name: name == "text-transform"), [])

    def test_palette_contrast_light_and_dark(self):
        failures, measured = [], 0
        for label, media in MEDIA.items():
            for where, tokens, extra in (("the page", palette(self.rules, media), []),
                                         ("the lightboxes", palette(self.rules, media, ".cad-view-wrap"), LIGHTBOX_TEXT_PAIRS)):
                for pairs, floor in ((TEXT_PAIRS + extra, 4.5), (EDGE_PAIRS, 3.0)):
                    for fg, bg in pairs:
                        ratio = contrast(_resolve_pair_colour(tokens, fg), _resolve_pair_colour(tokens, bg))
                        measured += 1
                        if ratio < floor:
                            failures.append("%s, %s: %s on %s is %.2f (under %.1f)" % (label, where, fg, bg, ratio, floor))
        self.assertEqual(failures, [])
        self.assertGreater(measured, 600)

    def test_the_lightboxes_take_the_light_palette_in_every_scheme(self):
        light = palette(self.rules, MEDIA["light"])
        dark = palette(self.rules, MEDIA["dark"])
        self.assertNotEqual(light["--surface"], dark["--surface"], "the shell has a dark palette")
        self.assertEqual(light["--card"], "#fff", "Photo's cutouts are filled with --card")
        self.assertLessEqual(set(dark), set(light), "every dark token has its light value (the lightboxes declare those)")
        for box in LIGHTBOXES:
            for light_media, dark_media in (("light", "dark"), ("light, more contrast", "dark, more contrast")):
                with self.subTest(box=box, scheme=dark_media):
                    self.assertEqual(palette(self.rules, MEDIA[dark_media], box), palette(self.rules, MEDIA[light_media], box))
                    self.assertEqual(palette(self.rules, MEDIA[dark_media], box)["--surface"], "#fff")
        schemes = {(rule.selectors, rule.conditions): value for rule in self.rules for name, value, _ in rule.declarations if name == "color-scheme"}
        self.assertEqual(schemes.get(((":root",) + LIGHTBOXES, ())), "light")
        self.assertEqual(schemes.get(((":root",), ("@media (prefers-color-scheme: dark)",))), "dark")
        # Every token the theme uses is defined (by its palette or by styles.css).
        defined = set(light) | {name for rule in self.rules + self.styles_rules for name, _, _ in rule.declarations if name.startswith("--")}
        used = set(re.findall(r"var\((--[\w-]+)", self.source))
        self.assertEqual(used - defined, set())

    def test_the_3d_view_is_viewer_js_s_clear_colour(self):
        viewer = (WEB / "cad" / "viewer.js").read_text(encoding="utf-8")
        clear = re.findall(r"scene\.background\s*=\s*new THREE\.Color\(0x([0-9a-f]{6})\)", viewer)
        self.assertEqual(len(clear), 1, clear)
        backgrounds = [value for selector, name, value in self._declared(lambda name: name in ("background", "background-color"))
                       if selector == ".cad-view"]
        self.assertEqual(backgrounds, ["#" + clear[0]])

    def test_the_page_s_javascript_neither_observes_nor_smooths_the_scroll_unguarded(self):
        scripts = _scripts()
        self.assertIn(WEB / "cad" / "main.js", scripts)
        guarded = 0
        for path in scripts:
            text = path.read_text(encoding="utf-8")
            for word in ("IntersectionObserver", "ScrollTimeline", "ViewTimeline", "animationTimeline", "scrollTimeline", "viewTimeline"):
                self.assertNotIn(word, text, "%s: %s" % (path.name, word))
            self.assertIsNone(re.search(r"scroll-?[bB]ehavior", text), path.name)
            lines = text.splitlines()
            for number, line in enumerate(lines):
                for match in re.finditer(r"behavior\s*:", line):
                    value = line[match.end():_scan(line, match.end(), ",}")]
                    if "smooth" not in value:
                        continue
                    condition = re.match(r"\s*!?\s*([A-Za-z_$][\w$]*)\s*\?", value)
                    context = "\n".join(lines[max(0, number - 10):number])
                    ok = "prefers-reduced-motion" in value or bool(
                        condition and re.search(r"\b%s\s*=[^\n]*prefers-reduced-motion" % re.escape(condition.group(1)), context))
                    with self.subTest(script=path.name, line=number + 1):
                        self.assertTrue(ok, "a smooth scroll not guarded by prefers-reduced-motion: %s" % line.strip())
                    guarded += 1
        self.assertGreaterEqual(guarded, 3, "main.js's three guided scrolls were seen")


class ThemeReaderTests(unittest.TestCase):
    """The small CSS reader and the contrast arithmetic above, on known values."""

    def test_rules_selectors_and_conditions(self):
        rules, at_rules = parse_css('a,b:is(.x,.y) > c::before { color:red; --u:url("data:x;y{z}") !important }'
                                    "@media (prefers-color-scheme: dark) { @supports (x:y) { :root { --a:#000 } } } @import 'x';")
        self.assertEqual([rule.selectors for rule in rules], [("a", "b:is(.x,.y) > c::before"), (":root",)])
        self.assertEqual(rules[0].declarations, [("color", "red", False), ("--u", 'url("data:x;y{z}")', True)])
        self.assertEqual(rules[1].conditions, ("@media (prefers-color-scheme: dark)", "@supports (x:y)"))
        self.assertEqual(at_rules, ["@media (prefers-color-scheme: dark)", "@supports (x:y)", "@import 'x'"])
        self.assertEqual(subject("b:is(.x, .y) > c::before"), "c::before")
        self.assertTrue(_has_class(".flow-guide", ".flow-guide") and not _has_class(".flow-guide-title", ".flow-guide"))

    def test_contrast_of_known_pairs(self):
        self.assertAlmostEqual(contrast(_colour("#fff"), _colour("#000")), 21.0, places=6)
        self.assertAlmostEqual(contrast(_colour("#6e6e73"), _colour("#fff")), 5.07, places=2)
        self.assertAlmostEqual(contrast(_colour("#ffffff"), _colour("#0071e3")), 4.70, places=2)
        self.assertEqual(_over(_colour("rgba(0,0,0,.5)"), _colour("#fff"))[:3], (127.5, 127.5, 127.5))

    def test_palette_follows_the_media(self):
        rules, _ = parse_css(":root { --a:#fff; --b:var(--a) } @media (prefers-color-scheme: dark) { :root { --a:#000 } }"
                             " @media (max-width:500px) { :root { --a:#f00 } }")
        self.assertEqual(palette(rules, MEDIA["light"]), {"--a": "#fff", "--b": "#fff"})
        self.assertEqual(palette(rules, MEDIA["dark"]), {"--a": "#000", "--b": "#000"})


if __name__ == "__main__":
    unittest.main()
