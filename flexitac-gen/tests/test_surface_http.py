"""CAD mode over HTTP: the /api/surface/* routes of app.py (framed body: JSON header plus mesh bytes)."""

from __future__ import annotations

import http.client
import json
import struct
import unittest

import app
from surface import select
from surface.api import frame
from surface.errors import SURFACE_ERROR_CODES

try:
    import surface_fixtures as F
    from test_api_http import HttpTestCase, _parse
except ImportError:  # run as a package
    from tests import surface_fixtures as F
    from tests.test_api_http import HttpTestCase, _parse

SURFACE = {"Content-Type": app.SURFACE_CONTENT_TYPE}


class SurfaceRouteTests(HttpTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        triangles = F.soft_finger_replica()
        cls.mesh_bytes = F.stl_bytes(triangles)
        mesh = F.mesh(triangles)
        cls.selection = {"ops": [{"op": "grow", "seed_facet": select.nearest_facet(mesh, (0.0, -12.9, -62.7))}]}

    def post_surface(self, route: str, header: dict, mesh: bytes | None = None, headers: dict | None = None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.port, timeout=120)
        try:
            body = frame(header, self.mesh_bytes if mesh is None else mesh)
            connection.request("POST", route, body=body, headers=dict(SURFACE, **(headers or {})))
            response = connection.getresponse()
            data = response.read()
            return response.status, json.loads(data)
        finally:
            connection.close()

    def test_inspect_select_fit_and_map(self) -> None:
        status, inspected = self.post_surface("/api/surface/inspect", {})
        self.assertEqual(status, 200)
        self.assertEqual((inspected["ok"], inspected["mesh"]["facets"], inspected["mesh"]["unit"]), (True, 108, "mm"))
        self.assertTrue(inspected["candidates"]["flat"])
        status, selected = self.post_surface("/api/surface/select", {"selection": self.selection})
        self.assertEqual(status, 200)
        self.assertEqual(selected["selection"]["kind"], "planar")
        side = min(selected["selection"]["sides"], key=lambda s: abs(s["from_xyz"][2] + 3.0) + abs(s["to_xyz"][2] + 3.0))
        options = {"pitch_mm": 3.0, "rotation": "none", "proposals": 2}
        status, fitted = self.post_surface("/api/surface/fit", {"selection": self.selection, "base": {"side": side["index"]}, "options": options})
        self.assertEqual(status, 200, fitted)
        proposal = fitted["proposals"][0]
        header = {"selection": self.selection, "placement": proposal["placement"], "design": proposal["design"], "options": options}
        status, mapped = self.post_surface("/api/surface/map", header)
        self.assertEqual(status, 200, mapped)
        self.assertTrue(mapped["ok"])
        self.assertEqual(mapped["taxel_count"], proposal["metrics"]["taxels"])
        self.assertEqual(mapped["build_id"], proposal["build_id"])

    def test_a_rounded_plate_and_the_options_cad_mode_no_longer_has(self) -> None:
        # P5-diagonal-bus.md section 26.16: CAD mode fits the selected area; shape rectangle, the generic template and the
        # rectangle preference are refused over HTTP (422, E_SURFACE_REQUEST, the reason named), while a saved placement
        # that names them as a fit then accepted them still maps as fitted (the generic template not beside this
        # placement's containment field and 64 columns: section 26.18).  On a 30 x 38 mm plate with 5 mm corners
        # (section 16's corner tolerance; shape rectangle's full 238 before): the default fit, its map with the corner
        # tolerance's record, tip_first false accepted and echoed (the step runs, its zero-cost ties alone: none a lead),
        # a non-boolean refused.
        import math

        outline = []
        for cx, cy, start in ((25.0, 5.0, -90), (25.0, 33.0, 0), (5.0, 33.0, 90), (5.0, 5.0, 180)):
            for k in range(13):
                angle = math.radians(start + 90 * k / 12)
                outline.append((cx + 5.0 * math.cos(angle), cy + 5.0 * math.sin(angle)))
        triangles = F.plate(outline, 3.0)
        mesh_bytes = F.stl_bytes(triangles)
        selection = {"ops": [{"op": "grow", "seed_facet": select.nearest_facet(F.mesh(triangles), (15.0, 19.0, 3.0))}]}
        options = {"proposals": 2}
        status, fitted = self.post_surface("/api/surface/fit", {"selection": selection, "options": options}, mesh=mesh_bytes)
        self.assertEqual(status, 200, fitted)
        self.assertEqual((fitted["request"]["options"]["shape"], fitted["request"]["options"]["containment"]), ("fill", "field"))
        self.assertNotIn("rectangle_preference_pct", fitted["request"]["options"])
        proposal = fitted["proposals"][0]
        self.assertEqual((proposal["metrics"]["taxels"], proposal["metrics"]["containment"]), (248, "field"))
        header = {"selection": selection, "placement": proposal["placement"], "design": proposal["design"]}
        status, mapped = self.post_surface("/api/surface/map", header, mesh=mesh_bytes)
        self.assertEqual(status, 200, mapped)
        self.assertTrue(mapped["ok"])
        self.assertIn("field_corner_overhang", [record["rule"] for record in mapped["verification"]])
        for removed in ({"shape": "rectangle", "containment": "field"}, {"template": "generic"}, {"rectangle_preference_pct": 5}):
            with self.subTest(options=removed):
                status, refused = self.post_surface("/api/surface/fit", {"selection": selection, "options": removed}, mesh=mesh_bytes)
                self.assertEqual((status, refused["code"]), (422, "E_SURFACE_REQUEST"))
                self.assertIn("rectangular mode", refused["error"])
                saved = dict(proposal["placement"], options=dict(proposal["placement"]["options"], **removed))
                status, mapped = self.post_surface("/api/surface/map", dict(header, placement=saved), mesh=mesh_bytes)
                if removed.get("template") == "generic":
                    # The placement names containment field and 64 columns, which a fit on the generic template refused
                    # (0024bdb), so no placement saved then holds them (section 26.18).
                    self.assertEqual((status, mapped["code"]), (422, "E_SURFACE_REQUEST"))
                    self.assertIn("on the generic template", mapped["error"])
                    continue
                self.assertEqual((status, mapped["ok"], mapped["build_id"]), (200, True, proposal["build_id"]))
        # Tip first by default: the 248 is a tip-first field (0.5 mm nearer the plate's far end than the 249s after it).
        self.assertEqual((fitted["request"]["options"]["tip_first"], proposal["metrics"]["tip"]["lead"]), (True, True))
        status, plain = self.post_surface("/api/surface/fit", {"selection": selection, "options": dict(options, tip_first=False)}, mesh=mesh_bytes)
        self.assertEqual((status, plain["request"]["options"]["tip_first"]), (200, False))
        self.assertEqual({p["metrics"]["tip"]["lead"] for p in plain["proposals"]}, {False})
        status, refused = self.post_surface("/api/surface/fit", {"selection": selection, "options": dict(options, tip_first="no")}, mesh=mesh_bytes)
        self.assertEqual((status, refused["code"]), (422, "E_SURFACE_REQUEST"))
        self.assertIn("tip_first", json.dumps(refused))

    def test_surface_errors_are_422_with_their_code(self) -> None:
        status, reply = self.post_surface("/api/surface/select", {"selection": {"ops": [{"op": "grow", "seed_facet": 10**6}]}})
        self.assertEqual((status, reply["ok"], reply["code"]), (422, False, "E_SURFACE_FACET"))
        status, reply = self.post_surface("/api/surface/inspect", {}, mesh=b"not an stl")
        self.assertEqual((status, reply["code"]), (422, "E_SURFACE_MESH_FORMAT"))
        status, reply = self.post_surface("/api/surface/inspect", {"surprise": 1})
        self.assertEqual((status, reply["code"]), (422, "E_SURFACE_REQUEST"))
        for code in (reply["code"],):
            self.assertIn(code, SURFACE_ERROR_CODES)

    def test_framing_and_header_errors(self) -> None:
        for body in (b"", b"\0\0", struct.pack(">I", 999) + b"{}", struct.pack(">I", 2) + b"[]", struct.pack(">I", 3) + b"{x}"):
            with self.subTest(body=body):
                reply = self.request("POST", "/api/surface/inspect", body=body, headers=SURFACE)
                self.assertError(reply, 422, "E_SURFACE_REQUEST")

    def test_content_type_size_method_and_origin(self) -> None:
        reply = self.request("POST", "/api/surface/inspect", body=frame({}, self.mesh_bytes), headers={"Content-Type": "application/json"})
        self.assertError(reply, 415, "E_HTTP_UNSUPPORTED_MEDIA_TYPE")
        head = (
            f"POST /api/surface/inspect HTTP/1.1\r\nHost: 127.0.0.1:{self.server.port}\r\n"
            f"Content-Type: {app.SURFACE_CONTENT_TYPE}\r\nContent-Length: {app.MAX_SURFACE_BYTES + 1}\r\n\r\n"
        ).encode()
        self.assertError(_parse(self.raw(head, half_close=True)), 413, "E_HTTP_BODY_TOO_LARGE")
        # The JSON routes keep their own 128 KiB limit.
        big = b"{" + b" " * app.MAX_REQUEST_BYTES + b"}"
        self.assertError(self.post_raw(big), 413, "E_HTTP_BODY_TOO_LARGE")
        reply = self.request("GET", "/api/surface/fit")
        self.assertError(reply, 405, "E_HTTP_METHOD_NOT_ALLOWED")
        self.assertEqual(reply.headers["allow"], "POST")
        reply = self.request("POST", "/api/surface/inspect", body=frame({}, self.mesh_bytes), headers=dict(SURFACE, Origin="http://evil.example"))
        self.assertError(reply, 403, "E_HTTP_FORBIDDEN_ORIGIN")

    def test_bad_values_are_request_errors_never_500(self) -> None:
        seed = self.selection["ops"][0]["seed_facet"]
        huge = 10 ** 400  # valid JSON, too large for a float
        cases = [
            ("/api/surface/select", {"selection": {"ops": [{"op": "grow", "seed_facet": seed, "theta_d_deg": huge}]}}, "E_SURFACE_REQUEST"),
            ("/api/surface/select", {"selection": {"ops": [{"op": "disk", "seed_facet": seed, "radius_mm": huge}]}}, "E_SURFACE_REQUEST"),
            ("/api/surface/select", {"selection": {"ops": [{"op": "cleanup", "min_island_mm2": huge}]}}, "E_SURFACE_REQUEST"),
            ("/api/surface/select", {"selection": {"ops": [{"op": ["grow"], "seed_facet": seed}]}}, "E_SURFACE_REQUEST"),
            ("/api/surface/select", {"selection": {"ops": [{"op": "grow", "seed_facet": seed, "preset": {"a": 1}}]}}, "E_SURFACE_REQUEST"),
            ("/api/surface/select", {"selection": {"ops": [{"op": "grow", "seed_facet": seed, "mode": ["add"]}]}}, "E_SURFACE_REQUEST"),
            ("/api/surface/select", {"selection": {"ops": [{"op": "facets", "facets": [huge]}]}}, "E_SURFACE_FACET"),
            ("/api/surface/select", {"selection": self.selection, "extra": 1}, "E_SURFACE_REQUEST"),
            ("/api/surface/fit", {"selection": self.selection, "options": {"pitch_mm": huge}}, "E_SURFACE_REQUEST"),
            ("/api/surface/fit", {"selection": self.selection, "options": {"objective": ["max_area"]}}, "E_SURFACE_REQUEST"),
            ("/api/surface/fit", {"selection": self.selection, "base": {"point_xyz": [huge, 0, 0]}}, "E_SURFACE_BASE_EDGE"),
            ("/api/surface/fit", {"selection": self.selection, "base": {"arc": {"point_xyz": [0, 0, 0], "half_length_mm": huge}}}, "E_SURFACE_BASE_EDGE"),
            ("/api/surface/map", {"selection": self.selection, "placement": {"design": {}}, "design": {}}, "E_SURFACE_REQUEST"),
            ("/api/surface/map", {"selection": self.selection, "placement": [], "design": {}}, "E_SURFACE_REQUEST"),
        ]
        for route, header, code in cases:
            with self.subTest(route=route, header=header):
                status, reply = self.post_surface(route, header)
                self.assertEqual((status, reply["code"]), (422, code), reply)

    def test_a_damaged_placement_is_a_422_never_a_500(self) -> None:
        options = {"pitch_mm": 3.0, "rotation": "none", "proposals": 1}
        status, fitted = self.post_surface("/api/surface/fit", {"selection": self.selection, "base": {"point_xyz": [0.0, -12.9, -3.0]}, "options": options})
        self.assertEqual(status, 200, fitted)
        proposal = fitted["proposals"][0]
        segments = len(fitted["selection"]["outline_uv"])
        for change in (
            {"exit_edges": [0, segments]},
            {"exit_edges": [10 ** 30]},
            {"base_to_uv": None},
            {"base_from_uv": [1e308, 1e308]},
            {"base_inward_uv": [10 ** 200, 0]},
            {"field_origin_base": [1.7e308, -1.7e308]},
            {"note": json.loads("[" * 40 + "]" * 40)},  # nested beyond what the reply may echo
        ):
            with self.subTest(change=change):
                header = {"selection": self.selection, "placement": dict(proposal["placement"], **change), "design": proposal["design"]}
                status, reply = self.post_surface("/api/surface/map", header)
                self.assertEqual((status, reply["code"]), (422, "E_SURFACE_REQUEST"), reply)
        status, mapped = self.post_surface("/api/surface/map", {"selection": self.selection, "placement": proposal["placement"], "design": proposal["design"]})
        self.assertEqual((status, mapped["ok"]), (200, True))

    def test_a_number_too_long_to_parse_safely_is_refused_before_parsing(self) -> None:
        header = b'{"selection": {"ops": [{"op": "grow", "seed_facet": ' + b"9" * 5000 + b"}]}}"
        body = struct.pack(">I", len(header)) + header + self.mesh_bytes
        reply = self.request("POST", "/api/surface/select", body=body, headers=SURFACE)
        data = self.assertError(reply, 422, "E_SURFACE_REQUEST")
        self.assertIn("4300 digits", data["error"])

    def test_cad_requests_have_a_slot_of_their_own(self) -> None:
        generation = self.server.httpd.generation_slots
        for _ in range(app.MAX_CONCURRENT_GENERATIONS):
            generation.acquire()
        try:
            # Both generation slots busy: CAD mode still runs, the rectangular mode waits.
            status, reply = self.post_surface("/api/surface/inspect", {})
            self.assertEqual(status, 200, reply)
            self.assertError(self.request("POST", "/api/generate", body=b"{}", headers={"Content-Type": "application/json"}), 503, "E_HTTP_BUSY")
        finally:
            for _ in range(app.MAX_CONCURRENT_GENERATIONS):
                generation.release()
        surface = self.server.httpd.surface_slots
        surface.acquire()
        try:
            reply = self.request("POST", "/api/surface/inspect", body=frame({}, self.mesh_bytes), headers=SURFACE)
            self.assertError(reply, 503, "E_HTTP_BUSY")
            self.assertEqual(reply.headers["retry-after"], str(app.RETRY_AFTER_S))
            self.assertEqual(self.request("POST", "/api/generate", body=b"{}", headers={"Content-Type": "application/json"}).status, 200)
        finally:
            surface.release()

    def test_meshes_beyond_the_json_limit_and_the_unit_override(self) -> None:
        # A 250 KB mesh (twice the JSON routes' limit) is a normal surface request.
        triangles = F.sphere_cap(20.0, 60.0, rings=40, segments=120)
        data = F.stl_bytes(triangles)
        self.assertGreater(len(data), 2 * app.MAX_REQUEST_BYTES)
        status, reply = self.post_surface("/api/surface/inspect", {"unit": "mm"}, mesh=data)
        self.assertEqual((status, reply["mesh"]["facets"]), (200, len(triangles)))
        # The same bytes in another unit are another mesh, not the cached one.
        status, scaled = self.post_surface("/api/surface/inspect", {"unit": "cm"}, mesh=data)
        self.assertEqual(status, 200)
        self.assertAlmostEqual(scaled["mesh"]["extent_mm"][2], 10 * reply["mesh"]["extent_mm"][2], places=3)
        status, guessed = self.post_surface("/api/surface/inspect", {}, mesh=data)
        self.assertEqual((status, guessed["mesh"]["unit"]), (200, "mm"))

    def test_a_body_just_over_the_limit_still_gets_its_413(self) -> None:
        size = app.MAX_SURFACE_BYTES + 1
        head = (
            f"POST /api/surface/inspect HTTP/1.1\r\nHost: 127.0.0.1:{self.server.port}\r\n"
            f"Content-Type: {app.SURFACE_CONTENT_TYPE}\r\nContent-Length: {size}\r\n\r\n"
        ).encode()
        reply = _parse(self.raw(head + b"\0" * size, timeout=60))
        self.assertError(reply, 413, "E_HTTP_BODY_TOO_LARGE")

    def test_the_default_route_serves_each_template(self) -> None:
        generic = self.request("GET", "/api/default")
        self.assertEqual(generic.status, 200)
        # The generic reply is the same with or without the parameter.
        self.assertEqual(self.request("GET", "/api/default?template=generic_matrix_v1").body, generic.body)
        surface = self.request("GET", "/api/default?template=surface_matrix_v1").json()
        self.assertEqual(surface["design"]["template_id"], "surface_matrix_v1")
        self.assertEqual(surface["profile"]["id"], "jlc-fpc-surface-v1")
        self.assertTrue(surface["profile"]["name"].startswith("Surface Matrix v1"))
        self.assertEqual(surface["profile"]["limits"]["matrix.columns"]["maximum"], 64)
        # The generic template's default, the diagonal Row bus, takes the surface profile's bounds; its straight channel 32.
        self.assertEqual(generic.json()["profile"]["limits"]["matrix.columns"]["maximum"], 64)
        self.assertEqual(generic.json()["profile"]["limits"]["matrix.columns"]["channel"], {"maximum": 32})
        for query in ("template=custom", "template=surface_matrix_v1&template=generic_matrix_v1", "view=compact"):
            self.assertError(self.request("GET", f"/api/default?{query}"), 400, "E_HTTP_BAD_REQUEST")

    def test_the_schema_lists_the_surface_codes(self) -> None:
        schema = self.request("GET", "/api/schema").json()
        self.assertEqual(schema["x-surface-error-codes"], SURFACE_ERROR_CODES)
        self.assertIn("E_SURFACE", schema["x-http-error-codes"])


if __name__ == "__main__":
    unittest.main()
