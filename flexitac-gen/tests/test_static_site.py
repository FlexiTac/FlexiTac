"""The static site: ``app.answer`` (the API without HTTP), the browser worker's
``web/py/bridge.py`` and ``tools/build_static_site.py`` (without Pyodide; the
browser checks, ``tools/browser/static_checks.py``, run the built site)."""

from __future__ import annotations

import hashlib
import io
import json
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

import app
from engine import default_design
from engine.profile import ProfileError
from surface.api import frame

try:
    import surface_fixtures as F
    from test_api_http import HttpTestCase
except ImportError:  # run as a package
    from tests import surface_fixtures as F
    from tests.test_api_http import HttpTestCase

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
sys.path.append(str(ROOT / "tools"))
sys.path.append(str(WEB / "py"))
import bridge  # noqa: E402
import build_static_site  # noqa: E402
import export_public  # noqa: E402

DESIGN = json.dumps(default_design()).encode("utf-8")
SURFACE = app.SURFACE_CONTENT_TYPE
# Headers the answer carries; the server adds the connection's own (length, security headers, Server, Date).
ANSWER_HEADERS = ("content-type", "content-disposition", "x-build-id", "x-design-sha256", "allow")


class AnswerTests(HttpTestCase):
    """``app.answer`` gives the page what the server gives it, byte for byte."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.mesh = F.stl_bytes(F.soft_finger_replica())

    def same(self, method: str, target: str, content_type: str = "", body: bytes = b"") -> app.Reply:
        answer = app.answer(method, target, content_type, body)
        reply = self.request(method, target, body if method == "POST" else None, {"Content-Type": content_type} if content_type else {})
        self.assertEqual(answer.status, reply.status, (target, answer.body[:200], reply.body[:200]))
        self.assertEqual(answer.body, reply.body, target)
        headers = {"content-type": answer.content_type, **{name.lower(): value for name, value in answer.headers}}
        self.assertEqual({k: headers.get(k) for k in ANSWER_HEADERS}, {k: reply.headers.get(k) for k in ANSWER_HEADERS}, target)
        return answer

    def test_routes(self) -> None:
        self.same("GET", "/api/default")
        self.same("GET", "/api/default?template=surface_matrix_v1")
        self.same("GET", "/api/schema")
        self.same("POST", "/api/validate", "application/json", DESIGN)
        self.same("POST", "/api/generate?view=compact", "application/json", DESIGN)
        for kind in ("top-gerber", "bottom-gerber", "project", "easyeda-pro"):
            with self.subTest(kind=kind):
                answer = self.same("POST", f"/api/export/{kind}", "application/json", DESIGN)
                self.assertEqual((answer.status, answer.content_type), (200, "application/zip"))
        self.assertEqual(self.same("POST", "/api/surface/inspect", SURFACE, frame({}, self.mesh)).status, 200)

    def test_errors(self) -> None:
        cases = (
            ("GET", "/api/default?view=compact", "", b"", 400, "E_HTTP_BAD_REQUEST"),
            ("GET", "/api/nothing", "", b"", 404, "E_HTTP_NOT_FOUND"),
            ("GET", "/api/generate", "", b"", 405, "E_HTTP_METHOD_NOT_ALLOWED"),
            ("POST", "/api/default", "application/json", b"{}", 405, "E_HTTP_METHOD_NOT_ALLOWED"),
            ("POST", "/api/generate", "application/json", b"{", 400, "E_HTTP_INVALID_JSON"),
            ("POST", "/api/generate", "application/json", b" ", 400, "E_HTTP_BODY_NOT_OBJECT"),
            ("POST", "/api/validate", "application/json", b"[]", 400, "E_HTTP_BODY_NOT_OBJECT"),
            ("POST", "/api/validate", "text/plain", b"{}", 415, "E_HTTP_UNSUPPORTED_MEDIA_TYPE"),
            ("POST", "/api/validate", "application/json; charset=latin-1", b"{}", 415, "E_HTTP_UNSUPPORTED_MEDIA_TYPE"),
            ("POST", "/api/export/top-gerber", "application/json", json.dumps({"matrix": {"pitch_x_mm": 1.0, "taxel_width_mm": 0.9}}).encode(), 422, "E_EXPORT_BLOCKED"),
            ("POST", "/api/surface/fit", "application/json", b"{}", 415, "E_HTTP_UNSUPPORTED_MEDIA_TYPE"),
            ("POST", "/api/surface/fit", SURFACE, b"\x00\x00", 422, "E_SURFACE_REQUEST"),
            ("POST", "/api/surface/fit", SURFACE, frame({"selection": "flat"}, b"not a mesh"), 422, None),
        )
        for method, target, content_type, body, status, code in cases:
            with self.subTest(method=method, target=target, body=body[:20]):
                answer = self.same(method, target, content_type, body)
                data = json.loads(answer.body)
                self.assertEqual((answer.status, data["ok"]), (status, False))
                if code is not None:
                    self.assertEqual(data["code"], code)

    def test_only_api_routes_and_the_body_limits(self) -> None:
        # The pages and their files are the static site's own (the Library, the generator and the forwarding page since
        # the user's decision of 2026-11-16).
        for target in ("/", "/index.html", "/gen.html", "/library.html", "/static/app.js"):
            self.assertEqual(json.loads(app.answer("GET", target).body)["code"], "E_HTTP_NOT_FOUND")
        too_large = app.answer("POST", "/api/validate", "application/json", b" " * (app.MAX_REQUEST_BYTES + 1))
        self.assertEqual((too_large.status, json.loads(too_large.body)["code"]), (413, "E_HTTP_BODY_TOO_LARGE"))
        too_large = app.answer("POST", "/api/surface/fit", SURFACE, b"\x00" * (app.MAX_SURFACE_BYTES + 1))
        self.assertEqual((too_large.status, json.loads(too_large.body)["code"]), (413, "E_HTTP_BODY_TOO_LARGE"))

    def test_answers_build_with_the_given_cache(self) -> None:
        cache = app.BuildCache(app.BUILD_CACHE_SIZE)
        with mock.patch.object(app, "generate_design", wraps=app.generate_design) as generate:
            first = app.answer("POST", "/api/export/top-gerber", "application/json", DESIGN, cache=cache)
            second = app.answer("POST", "/api/export/top-gerber", "application/json", DESIGN, cache=cache)
        self.assertEqual(first.body, second.body)
        self.assertEqual([call.kwargs["cache"] for call in generate.call_args_list], [cache, cache])


class BridgeTests(unittest.TestCase):
    def test_a_reply_as_the_worker_takes_it(self) -> None:
        status, phrase, headers, body = bridge.handle("POST", "/api/export/top-gerber", "application/json", DESIGN)
        names = [name for name, _ in json.loads(headers)]
        self.assertEqual((status, phrase, names[0]), (200, "OK", "Content-Type"))
        self.assertEqual(dict(json.loads(headers))["Content-Type"], "application/zip")
        self.assertIn("Content-Disposition", names)
        self.assertEqual(body, app.answer("POST", "/api/export/top-gerber", "application/json", DESIGN).body)
        status, phrase, _, body = bridge.handle("GET", "/api/nothing", "", memoryview(b""))
        self.assertEqual((status, phrase, json.loads(body)["code"]), (404, "Not Found", "E_HTTP_NOT_FOUND"))

    def test_unexpected_failures_are_the_servers_500s(self) -> None:
        for error, code in ((RuntimeError("boom"), "E_INTERNAL"), (ProfileError("broken"), "E_PROFILE_INVALID")):
            with self.subTest(code=code), mock.patch.object(app, "answer", side_effect=error), mock.patch("sys.stderr", io.StringIO()) as log:
                status, phrase, headers, body = bridge.handle("GET", "/api/default", "", b"")
                self.assertEqual((status, phrase, json.loads(body)["code"]), (500, "Internal Server Error", code))
                self.assertEqual(dict(json.loads(headers))["Content-Type"], "application/json; charset=utf-8")
                self.assertIn(code, log.getvalue())


class SiteBuildTests(unittest.TestCase):
    def test_the_page_runs_its_api_in_the_browser_under_the_servers_policy(self) -> None:
        # The generator (gen.html since the user's decision of 2026-11-16; the build's first page is the Library).
        page = build_static_site.page(name="gen.html")
        head = page.split("</head>", 1)[0]
        self.assertEqual(head.count('<meta name="flexitac-backend" content="browser" />'), 1)
        policy = re.search(r'<meta http-equiv="Content-Security-Policy" content="([^"]+)" />', head)
        self.assertIsNotNone(policy)
        server = dict(app.SECURITY_HEADERS)["Content-Security-Policy"]
        # The server's policy, with WebAssembly and GitHub's API (the header's star and fork counts) allowed.
        self.assertEqual(policy.group(1).replace("script-src 'self' 'wasm-unsafe-eval'; connect-src 'self' https://api.github.com; ", ""), server)
        # The policy comes first after the charset, before anything it governs (the look's script in <head> too).
        self.assertLess(head.index("Content-Security-Policy"), head.index("<link"))
        self.assertLess(head.index("Content-Security-Policy"), head.index('<script src="static/theme.js"></script>'))
        self.assertTrue(head.startswith('<!doctype html>\n<html lang="en">\n  <head>\n    <meta charset="utf-8" />\n    <meta http-equiv="Content-Security-Policy"'))

    def test_the_header_carries_the_repositorys_counts_when_built_with_them(self) -> None:
        # web/gen.html: the GitHub card's name alone (its counts hidden, nothing asked of GitHub); app.py and the build fill it.
        page = (WEB / "gen.html").read_text(encoding="utf-8")
        self.assertIn('data-gh-stats hidden>', page)
        self.assertNotIn("api.github.com", page)
        built = build_static_site.page({"stars": 159, "forks": 17}, "gen.html")
        self.assertIn('<span data-gh-stars>159</span>', built)
        self.assertIn('<span data-gh-forks>17</span>', built)
        self.assertIn('aria-label="FlexiTac on GitHub: 159 stars, 17 forks" data-gh-badge>', built)
        self.assertNotIn("data-gh-stats hidden>", built)
        self.assertEqual(build_static_site.page(None, "gen.html").count("data-gh-stats hidden>"), 1)
        self.assertEqual([build_static_site.count_text(n) for n in (0, 999, 1000, 1049, 1250, 9999, 10000, 12600)],
                         ["0", "999", "1k", "1k", "1.2k", "10k", "10k", "13k"])
        # web/counts.js writes them the same way (web/backend.js until the review of 2026-11-16).
        self.assertIn('const fmt = n => (n >= 1000 ? `${(n / 1000).toFixed(n >= 10000 ? 0 : 1).replace(/\\.0$/, "")}k` : String(n));',
                      (WEB / "counts.js").read_text(encoding="utf-8"))

    def test_the_counts_are_optional(self) -> None:
        # GitHub's API unreachable or refusing (rate limit): no counts, no failure; with GITHUB_TOKEN the request carries it.
        seen = []

        def refuse(request, timeout):
            seen.append(dict(request.header_items()))
            raise OSError("offline")
        with mock.patch.object(build_static_site.urllib.request, "urlopen", side_effect=refuse), mock.patch.dict("os.environ", {"GITHUB_TOKEN": "t0ken"}):
            self.assertIsNone(build_static_site.github_counts())
        self.assertEqual(seen[0].get("Authorization"), "Bearer t0ken")

        class Reply(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False
        with mock.patch.object(build_static_site.urllib.request, "urlopen", return_value=Reply(b'{"stargazers_count": 159, "forks_count": 17}')):
            self.assertEqual(build_static_site.github_counts(), {"stars": 159, "forks": 17})
        with mock.patch.object(build_static_site.urllib.request, "urlopen", return_value=Reply(b'{"message": "Not Found"}')):
            self.assertIsNone(build_static_site.github_counts())

    def test_every_url_of_the_page_is_relative(self) -> None:
        # The site is served under a path (https://<org>.github.io/<repo>/): the generator's page, and since 2026-11-16
        # the Library's (the first page) and the forwarding page's, and the forwarding script's own targets.
        for name in build_static_site.PAGES:
            with self.subTest(page=name):
                page = (WEB / name).read_text(encoding="utf-8")
                self.assertEqual(re.findall(r'(?:src|href)="/[^"]*"', page), [])
        self.assertEqual(re.findall(r'"(?:\./|gen\.html)"', (WEB / "forward.js").read_text(encoding="utf-8")), ['"gen.html"', '"./"'])
        for path in (WEB / "app.js", *sorted((WEB / "cad").glob("*.js"))):
            with self.subTest(path=path.name):
                source = path.read_text(encoding="utf-8")
                self.assertNotIn('"/static/', source)
                # Every API request goes through apiFetch (web/backend.js).
                self.assertEqual(re.findall(r"\bfetch\([`\"']/api", source), [])

    def test_the_engine_zip_is_reproducible_and_complete(self) -> None:
        data = build_static_site.engine_zip()
        self.assertEqual(hashlib.sha256(data).digest(), hashlib.sha256(build_static_site.engine_zip()).digest())
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            names = archive.namelist()
            self.assertEqual(names, sorted(names))
            self.assertTrue({"app.py", "bridge.py", "engine/__init__.py", "exporters/__init__.py", "surface/__init__.py"} <= set(names))
            self.assertTrue(any(name.startswith("profiles/") and name.endswith(".json") for name in names))
            self.assertFalse([name for name in names if "__pycache__" in name or name.endswith(".pyc")])
            self.assertEqual({info.date_time for info in archive.infolist()}, {build_static_site.ZIP_TIME})
            with tempfile.TemporaryDirectory() as folder:
                archive.extractall(folder)
                # Only the archive's files: the worker's import of bridge.py answers a request.
                script = "import sys, json; sys.path.insert(0, sys.argv[1]); import bridge; print(json.dumps(bridge.handle('GET', '/api/default', '', b'')[:2]))"
                done = subprocess.run([sys.executable, "-I", "-B", "-c", script, folder], cwd=folder, capture_output=True, text=True, timeout=120)
        self.assertEqual(done.returncode, 0, done.stderr[-2000:])
        self.assertEqual(json.loads(done.stdout), [200, "OK"])

    def test_the_pyodide_archive_is_checked_by_its_sha256(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            fake = Path(folder) / "pyodide-core.tar.bz2"
            fake.write_bytes(b"not the release")
            with self.assertRaisesRegex(build_static_site.BuildError, "SHA-256"):
                build_static_site.pyodide_archive(fake)

    def test_only_an_earlier_build_is_replaced(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            other = Path(folder) / "other"
            other.mkdir()
            (other / "notes.txt").write_text("keep", encoding="utf-8")
            with self.assertRaisesRegex(build_static_site.BuildError, "not written by this tool"):
                build_static_site.prepare(other)
            self.assertTrue((other / "notes.txt").is_file())
            earlier = Path(folder) / "site"
            earlier.mkdir()
            (earlier / build_static_site.BUILD_MARKER).write_text("", encoding="utf-8")
            (earlier / "stale.js").write_text("", encoding="utf-8")
            build_static_site.prepare(earlier)
            self.assertEqual(list(earlier.iterdir()), [])
            # A refused build leaves its folder empty: web/ is copied before the Library's gates refuse a file (the
            # review of 2026-11-13: a model of the deny-list stayed in the output folder).
            def copied(static: Path) -> None:
                (static / "library" / "bodies").mkdir(parents=True)
                (static / "library" / "bodies" / "refused.stl").write_bytes(b"x")

            refused = build_static_site.BuildError("the library's scenes are stale (refused)")
            with mock.patch.object(build_static_site, "pyodide_files", return_value={}), \
                    mock.patch.object(build_static_site, "pyodide_archive", return_value=b""), \
                    mock.patch.object(build_static_site, "engine_zip", return_value=b""), \
                    mock.patch.object(build_static_site, "copy_web", side_effect=copied), \
                    mock.patch.object(build_static_site, "library", side_effect=refused):
                with self.assertRaisesRegex(build_static_site.BuildError, "scenes are stale"):
                    build_static_site.build(earlier, github=False)
            self.assertEqual(list(earlier.iterdir()), [])


# web/counts.js run under node on a page (the static site's mark, web/forward.js's, a count kept in this tab, GitHub's
# reply): the requests it made, and the GitHub card as it left it (the stars' and forks' text, hidden, its name).
COUNTS_DRIVER = r"""
const vm = require("vm");
const fs = require("fs");
const source = fs.readFileSync(process.argv[2], "utf8");
const runs = [];
(async () => {
  for (const {backend, forwarding, kept, reply} of JSON.parse(process.argv[3])) {
    const asked = [];
    const node = () => ({textContent: "", hidden: true, label: "FlexiTac on GitHub", setAttribute(name, value) { this.label = value; }});
    const card = {stars: node(), forks: node(), stats: node(), badge: node()};
    const nodes = {"[data-gh-stars]": card.stars, "[data-gh-forks]": card.forks, "[data-gh-stats]": card.stats, "[data-gh-badge]": card.badge};
    const storage = new Map(kept ? [["gh-stats:FlexiTac/FlexiTac", JSON.stringify({...kept, at: Date.now() - kept.age})]] : []);
    const document = {
      documentElement: {hasAttribute: name => name === "data-forward" && forwarding},
      querySelector: selector => (selector === 'meta[name="flexitac-backend"]' && backend ? {content: backend} : null),
      querySelectorAll: selector => (nodes[selector] ? [nodes[selector]] : []),
      readyState: "interactive",
    };
    const fetch = (url, init) => {
      asked.push([url, init?.headers?.Accept ?? null]);
      return Promise.resolve({ok: reply !== null, json: () => Promise.resolve(reply)});
    };
    const sessionStorage = {getItem: key => storage.get(key) ?? null, setItem: (key, value) => storage.set(key, value)};
    vm.runInNewContext(source, {document, fetch, sessionStorage, JSON, Date, Promise});
    await new Promise(resolve => setTimeout(resolve, 20));
    runs.push({asked, card: [card.stars.textContent, card.forks.textContent, card.stats.hidden, card.badge.label],
               kept: storage.has("gh-stats:FlexiTac/FlexiTac")});
  }
  process.stdout.write(JSON.stringify(runs));
})();
"""


class CountsTests(unittest.TestCase):
    """The header's star and fork counts refreshed on the static site's pages by web/counts.js: the Library's (the first
    page since 2026-11-16) and the generator's (the review of 2026-11-16: the refresh was web/backend.js's, which the
    Library does not load, so the site's landing page had kept the build's counts)."""

    def test_both_pages_load_it_and_backend_js_asks_github_no_more(self) -> None:
        for name, count in (("index.html", 1), ("gen.html", 1), ("library.html", 0)):
            with self.subTest(page=name):
                page = (WEB / name).read_text(encoding="utf-8")
                self.assertEqual(page.count('<script src="static/counts.js" defer></script>'), count)
                self.assertEqual(page.count("counts.js"), count + (name != "library.html"))  # and the header's comment
        backend = (WEB / "backend.js").read_text(encoding="utf-8")
        self.assertNotIn("api.github.com", backend)
        self.assertNotIn("gh-stats", backend)
        source = (WEB / "counts.js").read_text(encoding="utf-8")
        self.assertIn('  if (document.querySelector(\'meta[name="flexitac-backend"]\')?.content !== "browser") return;\n', source)
        self.assertIn('  if (document.documentElement.hasAttribute("data-forward")) return;\n', source)
        # The one host it asks, the one the site's policy allows.
        self.assertEqual(re.findall(r"https://[^/`\"']+", source), ["https://api.github.com"])
        self.assertIn("connect-src 'self' https://api.github.com;", build_static_site.CSP)

    @unittest.skipUnless(__import__("shutil").which("node"), "node is not installed")
    def test_it_refreshes_the_card_on_the_static_site_alone(self) -> None:
        github = {"stargazers_count": 1234, "forks_count": 56}
        cases = [
            {"backend": "browser", "forwarding": False, "kept": None, "reply": github},  # the static site: asked, shown
            {"backend": None, "forwarding": False, "kept": None, "reply": github},  # app.py's page: nothing asked
            {"backend": "browser", "forwarding": True, "kept": None, "reply": github},  # a Library being sent on
            {"backend": "browser", "forwarding": False, "kept": {"stars": 1500, "forks": 60, "age": 60000}, "reply": github},  # kept: not asked
            {"backend": "browser", "forwarding": False, "kept": {"stars": 1500, "forks": 60, "age": 4000000}, "reply": github},  # an hour old: asked
            {"backend": "browser", "forwarding": False, "kept": None, "reply": None},  # GitHub refusing: the card as built
        ]
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / "driver.js").write_text(COUNTS_DRIVER, encoding="utf-8")
            run = subprocess.run(["node", "driver.js", str(WEB / "counts.js"), json.dumps(cases)], cwd=folder, capture_output=True, text=True, timeout=60)
        self.assertEqual(run.returncode, 0, run.stderr[-2000:])
        site, server, forwarding, kept, stale, refused = json.loads(run.stdout)
        asked = [[build_static_site.GITHUB_API, "application/vnd.github+json"]]
        shown = ["1.2k", "56", False, "FlexiTac on GitHub: 1234 stars, 56 forks"]
        unchanged = ["", "", True, "FlexiTac on GitHub"]
        self.assertEqual((site["asked"], site["card"], site["kept"]), (asked, shown, True))
        self.assertEqual((server["asked"], server["card"]), ([], unchanged))
        self.assertEqual((forwarding["asked"], forwarding["card"]), ([], unchanged))
        self.assertEqual((kept["asked"], kept["card"]), ([], ["1.5k", "60", False, "FlexiTac on GitHub: 1500 stars, 60 forks"]))
        self.assertEqual((stale["asked"], stale["card"]), (asked, shown))
        self.assertEqual((refused["asked"], refused["card"], refused["kept"]), (asked, unchanged, False))


class PublicExportTests(unittest.TestCase):
    """tools/export_public.py: the public copy in FlexiTac/FlexiTac (flexitac-gen/)."""

    def test_the_public_copy_keeps_what_its_documents_and_site_need(self) -> None:
        public = export_public.PUBLIC
        def covered(relative: str) -> bool:
            return any(relative == path or relative.startswith(path + "/") for path in public)
        for path in public:
            self.assertTrue((ROOT / path).exists(), path)
        documents = [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md")), ROOT / "claude" / "APP_HANDOFF.md",
                     ROOT / "tools" / "README.md", ROOT / "tools" / "browser" / "README.md"]
        for document in documents:
            self.assertTrue(covered(document.relative_to(ROOT).as_posix()), document)
            for target in re.findall(r"\[[^\]]*\]\(([^)\s#]+)", document.read_text(encoding="utf-8")):
                destination = (document.parent / target).resolve()
                if re.match(r"[a-z]+:", target) or ROOT not in destination.parents:
                    continue
                with self.subTest(document=document.name, link=target):
                    self.assertTrue(covered(destination.relative_to(ROOT).as_posix()))
        for source in (*build_static_site.ENGINE_SOURCES, "web", "tools/build_static_site.py", "LICENSE"):
            self.assertTrue(covered(source), source)
        # The Library's private tools (its importer, its tips' cutter and, since 2026-11-05, the grippers' scene builder:
        # they read the private recipes or need numpy and trimesh); their outputs are public with web/library/.
        for private in ("claude/sessions", "claude/specs", "asset", "outputs/x", "tools/gripper_scene.py", "tools/umi_tip_video.py",
                        "tools/library_import.py", "tools/library_tips.py", "tools/library_scenes.py"):
            self.assertFalse(covered(private), private)
        for shipped in ("web/library/scenes/scenes.json", "web/library/bodies/x.stl", "web/library/art/x.json.gz", "web/cad/library_view.js"):
            self.assertTrue(covered(shipped), shipped)
        # The showcase of 2026-11-12: the vendor's folder with its notice goes with web/, and the tool that builds it
        # and its decimator (stdlib; their --check needs no source) are public, so the public copy checks the files.
        # Its page of that day's second stage: its document, its pictures and the shapes the project draws go with web/,
        # the shots tool that shoots it and the check of its page with tools/browser, and the split tool whose shapes
        # the builder draws with is public already.
        for shipped in ("web/vendor/ufactory-g1/NOTICE.md", "web/vendor/ufactory-g1/body_shell.stl", "web/library/scenes/flexitac-g1.json",
                        "tools/library_showcase.py", "tools/mesh_decimate.py", "web/library/showcase.json",
                        "web/library/showcase/flexitac-g1.exploded.webp", "web/library/showcase/flexitac-g1.assembled.webp",
                        "web/library/showcase/flexitac-g1.card.webp", "web/library/bodies/flexitac-g1/drawn-shell-screw.stl",
                        "web/vendor/flexitac-v2/umi-finray.placed.json", "tools/library_split.py", "tools/browser/library_shots.py",
                        "tools/browser/showcase_checks.py"):
            self.assertTrue(covered(shipped), shipped)
            self.assertTrue((ROOT / shipped).is_file(), shipped)

    def test_an_export_writes_the_commits_public_files_and_the_workflow(self) -> None:
        def run(*args: str, cwd: Path) -> None:
            subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source"
            project = source / "fpc_agentic_customization"
            for path in export_public.PUBLIC:
                # Each path as it is here (a file, or a folder with a file in it); the .gitignore ignores nothing.
                file = project / path if (ROOT / path).is_file() else project / path / "x.txt"
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_text("# none\n" if path == ".gitignore" else path, encoding="utf-8")
            (project / "tools" / "public" / "pages-workflow.yml").write_text("name: site\n", encoding="utf-8")
            (project / "claude" / "sessions").mkdir()
            (project / "claude" / "sessions" / "log.md").write_text("private", encoding="utf-8")
            (project / "tools" / "umi_tip_video.py").write_text("private", encoding="utf-8")
            run("init", "-q", cwd=source)
            run("add", "-A", cwd=source)
            run("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "c", cwd=source)
            (project / "app.py").write_text("uncommitted", encoding="utf-8")
            repo = Path(folder) / "FlexiTac"
            (repo / ".git").mkdir(parents=True)
            commit = export_public.export(repo, "HEAD", source=project)
            target = repo / export_public.FOLDER
            self.assertEqual((target / export_public.MARKER).read_text(encoding="utf-8"), commit + "\n")
            self.assertEqual((target / "app.py").read_text(encoding="utf-8"), "app.py")  # the commit's, not the working tree's
            self.assertEqual((repo / export_public.WORKFLOW).read_text(encoding="utf-8"), "name: site\n")
            self.assertFalse((target / "claude" / "sessions").exists())
            self.assertFalse((target / "tools" / "umi_tip_video.py").exists())
            (target / "stale.txt").write_text("", encoding="utf-8")
            export_public.export(repo, "HEAD", source=project)
            self.assertFalse((target / "stale.txt").exists())
            (target / export_public.MARKER).unlink()
            with self.assertRaisesRegex(export_public.ExportError, "not written by this tool"):
                export_public.export(repo, "HEAD", source=project)
            with self.assertRaisesRegex(export_public.ExportError, "not a git clone"):
                export_public.export(Path(folder), "HEAD", source=project)


if __name__ == "__main__":
    unittest.main()
