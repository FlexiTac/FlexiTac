"""Build identity (audit M6 identity part; decision D14).

Numbers are canonicalised before hashing (integral floats -> int, other
floats on the 6-decimal layout grid), the build hash covers the canonical
design, the full profile digest and the generator and exporter versions, and
names without ASCII letters or digits get a hash-based slug.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import unittest
from pathlib import Path
from unittest import mock

from engine import BuildCache, default_design, generate_design, load_profile
from exporters import direct_gerber

ROOT = Path(__file__).resolve().parents[1]
# What web/app.js payload() posts for the default form (/api/default filled
# in): the version header of the default design, the flat form aliases and
# the nested connector section (an empty input is null), in that order.
# JavaScript writes integral numbers without a fraction.  The bottom tail 12 mm since P5-diagonal-bus.md section 27.7
# (the rectangular mode's tails 12 / 12; 7.5 before); the electrodes 1 mm since the user's decision of 2026-11-06 (the
# default fill 0.5; 1.4 mm, fill 0.7, before).
BROWSER_DEFAULT_PAYLOAD = (
    '{"schema_version":"tactile-fpc-design/v1","template_id":"generic_matrix_v1",'
    '"name":"Tactile FPC 12x32","rows":12,"columns":32,"pitch_x_mm":2,"pitch_y_mm":2,'
    '"row_electrode_width_mm":1,"column_electrode_width_mm":1,"top_tail_length_mm":12,'
    '"bottom_tail_length_mm":12,"connector_side":"bottom","row_fpc_position":"top","scan_order":"forward",'
    '"trace_width_mm":0.127,"trace_space_mm":0.127,"connector":{"row_pins":null,"column_pins":null}}'
)


def _canonical(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _top_level_entries(text: str) -> list[tuple[str, str]]:
    """``(key, expression)`` of a JavaScript object literal body, split at top-level commas."""

    entries, depth, quote, current = [], 0, None, ""
    for char in text:
        if quote:
            quote = None if char == quote else quote
        elif char in "\"'`":
            quote = char
        elif char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
        if char == "," and depth == 0 and quote is None:
            entries.append(current)
            current = ""
        else:
            current += char
    entries.append(current)
    pairs = []
    for entry in (entry.strip() for entry in entries):
        if entry:
            key, _, expression = entry.partition(":")
            pairs.append((key.strip(), expression.strip()))
    return pairs


def _browser_payload_entries() -> list[tuple[str, str]]:
    """The entries of the object that ``payload()`` in web/app.js returns."""

    script = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
    body = re.search(r"function payload\(\) \{.*?return \{(.*?)\};\s*\}", script, re.S)
    if body is None:
        raise AssertionError("web/app.js no longer has a payload() returning an object literal")
    return _top_level_entries(re.sub(r"//[^\n]*", "", body.group(1)))


class IdentityTests(unittest.TestCase):
    def test_browser_payload_guard_covers_every_key(self) -> None:
        # Every key payload() sends, whatever its value expression, must be in
        # BROWSER_DEFAULT_PAYLOAD (reviewer T-IDENTITY-GUARD): a new key, a
        # dropped key or a key sent from another control fails here.
        payload = json.loads(BROWSER_DEFAULT_PAYLOAD)
        entries = _browser_payload_entries()
        self.assertEqual([key for key, _ in entries], list(payload), "web/app.js payload() changed; update BROWSER_DEFAULT_PAYLOAD")
        page = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        names = dict(re.findall(r'<(?:input|select)[^>]*\bid="([^"]+)"[^>]*\bname="([^"]+)"', page))
        defaults = default_design()
        for key, expression in entries:
            with self.subTest(key=key, expression=expression):
                control = re.fullmatch(r'value\("(\w+)"\)', expression)
                if control:
                    # A flat alias is sent from the form control of that name.
                    self.assertEqual(names.get(control.group(1)), key)
                elif key in ("schema_version", "template_id"):
                    # The version header is the /api/default design's own.
                    self.assertEqual(expression, f"state.design?.{key}")
                    self.assertEqual(payload[key], defaults[key])
                elif key == "connector":
                    self.assertEqual(expression, "connectorSection()")
                    fields = re.findall(r'data-field="connector\.(\w+)"', page)
                    self.assertEqual(list(payload[key]), fields)
                    self.assertEqual(set(payload[key].values()), {None})
                else:
                    self.fail(f"payload() sends {key} from an unrecognised expression {expression!r}")

    def test_browser_default_payload_and_default_design_share_one_build(self) -> None:
        payload = json.loads(BROWSER_DEFAULT_PAYLOAD)
        # formBody() adds the Row traces select (routing.row_sides, Both on the default form: the generic template's
        # default since P5-diagonal-bus.md section 18); without it the same build, the value then defaulted.
        self.assertIn("if (sides) body.routing = {row_sides: sides};", (ROOT / "web" / "app.js").read_text(encoding="utf-8"))
        bare = generate_design(payload)
        payload["routing"] = {"row_sides": "both"}
        browser = generate_design(payload)
        self.assertEqual(bare["validation"]["normalization"]["defaults_applied"], ["routing.row_sides"])
        self.assertEqual(bare["manifest"], browser["manifest"])
        # The browser sends schema_version, so no request warning is raised;
        # its fourteen flat form fields are the applied aliases (connector_side,
        # row_fpc_position and scan_order set two fields each) and nothing is defaulted.
        self.assertEqual(browser["validation"]["warnings"], [])
        normalization = browser["validation"]["normalization"]
        flat = {key for key, value in payload.items() if not isinstance(value, dict)} - {"schema_version", "template_id"}
        self.assertEqual({entry["alias"] for entry in normalization["aliases_applied"]}, flat)
        self.assertEqual(len(normalization["aliases_applied"]), 17)
        self.assertEqual(normalization["defaults_applied"], [])
        api = generate_design(default_design())
        self.assertTrue(browser["ok"] and api["ok"])
        self.assertEqual(browser["design"], api["design"])
        self.assertEqual(_canonical(browser["design"]), _canonical(api["design"]))
        for key in ("design_sha256", "build_sha256", "build_id"):
            self.assertEqual(browser["manifest"][key], api["manifest"][key])
        # The manifest describes the build, not how the request was spelled.
        self.assertEqual(browser["manifest"], api["manifest"])
        self.assertEqual(_canonical(browser["boards"]), _canonical(api["boards"]))

    def test_numbers_are_canonicalised_on_the_layout_grid_before_hashing(self) -> None:
        def build(**matrix):
            return generate_design({"matrix": dict({"columns": 8}, **matrix)})["manifest"]

        reference = build(pitch_x_mm=2)
        for variant in ({"pitch_x_mm": 2.0}, {"pitch_x_mm": 2.0000004}, {"pitch_x_mm": 1.9999996}, {"rows": 12.0}):
            with self.subTest(variant=variant):
                self.assertEqual(build(**variant)["build_id"], reference["build_id"])
        self.assertNotEqual(build(pitch_x_mm=2.000001)["build_id"], reference["build_id"])
        # Designs equal on the 1e-6 mm grid have identical geometry and one identity.
        first = generate_design({"matrix": {"columns": 8, "pitch_x_mm": 1.2345678, "taxel_width_mm": 0.81234561}})
        second = generate_design({"matrix": {"columns": 8, "pitch_x_mm": 1.2345681, "taxel_width_mm": 0.81234559}})
        self.assertTrue(first["ok"] and second["ok"])
        self.assertEqual(first["design"]["matrix"]["pitch_x_mm"], 1.234568)
        self.assertEqual(first["manifest"]["build_id"], second["manifest"]["build_id"])
        self.assertEqual(_canonical(first["boards"]), _canonical(second["boards"]))
        self.assertIs(type(generate_design()["design"]["matrix"]["pitch_x_mm"]), int)

    def test_build_identity_hashes_design_profile_digest_and_versions(self) -> None:
        result = generate_design()
        manifest = result["manifest"]
        self.assertEqual(manifest["format"], "tactile-fpc-manifest/v2")
        self.assertEqual(manifest["generator"], "deterministic-sensor-core/0.4.0")
        self.assertEqual(manifest["exporter"], direct_gerber.EXPORTER_VERSION)
        self.assertEqual(manifest["exporter"], "direct-gerber-pure-stdlib/0.3.0")
        self.assertEqual(manifest["layout_format"], result["derived_layout"]["format"])
        self.assertEqual(manifest["design_sha256"], _sha(_canonical(result["design"])))
        # The default design is the diagonal Row bus (P5-diagonal-bus.md section 18), built with CAD mode's rule set, the
        # surface profile (section 20): that profile's digest and the bus's version (diagonal-bus/11 since section 27.8, one
        # side's convex flank) are hashed.
        self.assertEqual(manifest["profile_sha256"], _sha(_canonical(load_profile("surface_matrix_v1"))))
        identity = {key: manifest[key] for key in ("design_sha256", "profile_sha256", "generator", "exporter", "row_bus")}
        self.assertEqual(manifest["row_bus"], "diagonal-bus/11")
        self.assertEqual(manifest["build_sha256"], _sha(_canonical(identity)))
        self.assertEqual(manifest["build_id"], f"{manifest['slug']}-{manifest['build_sha256'][:12]}")

        # A profile edit that keeps id and revision still gives a new build.
        edited = copy.deepcopy(load_profile("surface_matrix_v1"))
        edited["limits"]["high_fill_factor_warning"] = 0.81
        with mock.patch("engine.core.load_profile", return_value=edited):
            changed = generate_design()["manifest"]
        self.assertEqual(changed["profile"], manifest["profile"])
        self.assertEqual(changed["design_sha256"], manifest["design_sha256"])
        self.assertNotEqual(changed["profile_sha256"], manifest["profile_sha256"])
        self.assertNotEqual(changed["build_id"], manifest["build_id"])
        with mock.patch("engine.core.GENERATOR_VERSION", "deterministic-sensor-core/9.9.9"):
            self.assertNotEqual(generate_design()["manifest"]["build_id"], manifest["build_id"])
        with mock.patch.object(direct_gerber, "EXPORTER_VERSION", "direct-gerber-pure-stdlib/9.9.9"):
            self.assertNotEqual(generate_design()["manifest"]["build_id"], manifest["build_id"])

    def test_slug_falls_back_to_a_name_hash_for_non_ascii_names(self) -> None:
        def slug(name: str) -> str:
            manifest = generate_design({"project_name": name})["manifest"]
            self.assertEqual(manifest["build_id"], f"{manifest['slug']}-{manifest['build_sha256'][:12]}")
            return manifest["slug"]

        for name in ("触觉传感器", "Тактильный", "😀"):
            with self.subTest(name=name):
                self.assertEqual(slug(name), "tactile-fpc-" + hashlib.sha256(name.encode("utf-8")).hexdigest()[:8])
        self.assertNotEqual(slug("触觉传感器"), slug("触觉阵列"))
        self.assertEqual(slug("  触觉传感器  "), slug("触觉传感器"))
        self.assertEqual(slug("触觉传感器 v2"), "v2")
        self.assertEqual(slug("Demo 4 x 5"), "demo-4-x-5")
        self.assertEqual(slug("x" * 47 + " y"), "x" * 47)  # no trailing dash after the 48-character cut

    def test_identity_is_stable_across_runs(self) -> None:
        first = generate_design({"rows": 5, "columns": 17, "connector_side": "left"})["manifest"]
        second = generate_design({"rows": 5.0, "columns": 17, "tail": {"row_side": "left", "column_side": "left"}})["manifest"]
        self.assertEqual(first, second)


class BuildCacheTests(unittest.TestCase):
    def test_cached_builds_are_keyed_by_the_full_build_identity(self) -> None:
        cache = BuildCache()
        design = {"matrix": {"rows": 4, "columns": 6}}
        first = generate_design(design, cache=cache)
        again = generate_design({"rows": 4.0, "columns": 6, "matrix": {"pitch_x_mm": 2.0000001}}, cache=cache)
        self.assertEqual((cache.misses, cache.hits), (1, 1))
        self.assertEqual(_canonical(again["boards"]), _canonical(first["boards"]))
        # A geometry-relevant profile edit that keeps id and revision is a new
        # build: never the cached boards of the old profile (the bus's, the surface profile).
        edited = copy.deepcopy(load_profile("surface_matrix_v1"))
        edited["routing"]["electrode_overhang_mm"] = 0.15
        with mock.patch("engine.core.load_profile", return_value=edited):
            fresh = generate_design(design)
            cached = generate_design(design, cache=cache)
        self.assertTrue(fresh["ok"] and cached["ok"], cached["validation"]["errors"])
        self.assertEqual(cache.misses, 2)
        self.assertNotEqual(_canonical(fresh["boards"]), _canonical(first["boards"]))
        self.assertEqual(_canonical(cached["boards"]), _canonical(fresh["boards"]))
        self.assertEqual(cached["manifest"], fresh["manifest"])
        # The generator and exporter versions are part of the key as well.
        with mock.patch.object(direct_gerber, "EXPORTER_VERSION", "direct-gerber-pure-stdlib/9.9.9"):
            generate_design(design, cache=cache)
        with mock.patch("engine.core.GENERATOR_VERSION", "deterministic-sensor-core/9.9.9"):
            generate_design(design, cache=cache)
        self.assertEqual((cache.misses, cache.hits), (4, 1))
        self.assertEqual(_canonical(generate_design(design, cache=cache)["boards"]), _canonical(first["boards"]))
        self.assertEqual(cache.hits, 2)

    def test_cache_is_a_bounded_lru(self) -> None:
        cache = BuildCache(maxsize=2)
        for rows in (2, 3, 2, 4, 3):
            generate_design({"rows": rows, "columns": 4}, cache=cache)
        # 2 and 3 are built, 2 is reused, 4 evicts 3, so 3 is built again.
        self.assertEqual((cache.misses, cache.hits), (4, 1))


if __name__ == "__main__":
    unittest.main()
