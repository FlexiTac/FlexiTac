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
        # The page and its files are the static site's own.
        for target in ("/", "/index.html", "/static/app.js"):
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
        page = build_static_site.page()
        head = page.split("</head>", 1)[0]
        self.assertEqual(head.count('<meta name="flexitac-backend" content="browser" />'), 1)
        policy = re.search(r'<meta http-equiv="Content-Security-Policy" content="([^"]+)" />', head)
        self.assertIsNotNone(policy)
        server = dict(app.SECURITY_HEADERS)["Content-Security-Policy"]
        # The server's policy, with WebAssembly and GitHub's API (the header's star and fork counts) allowed.
        self.assertEqual(policy.group(1).replace("script-src 'self' 'wasm-unsafe-eval'; connect-src 'self' https://api.github.com; ", ""), server)
        # The policy comes first after the charset, before anything it governs.
        self.assertLess(head.index("Content-Security-Policy"), head.index("<link"))
        self.assertTrue(head.startswith('<!doctype html>\n<html lang="en">\n  <head>\n    <meta charset="utf-8" />\n    <meta http-equiv="Content-Security-Policy"'))

    def test_the_header_carries_the_repositorys_counts_when_built_with_them(self) -> None:
        # app.py's page: the GitHub card's name alone (its counts hidden, nothing asked of GitHub).
        page = (WEB / "index.html").read_text(encoding="utf-8")
        self.assertIn('data-gh-stats hidden>', page)
        self.assertNotIn("api.github.com", page)
        built = build_static_site.page({"stars": 159, "forks": 17})
        self.assertIn('<span data-gh-stars>159</span>', built)
        self.assertIn('<span data-gh-forks>17</span>', built)
        self.assertIn('aria-label="FlexiTac on GitHub: 159 stars, 17 forks" data-gh-badge>', built)
        self.assertNotIn("data-gh-stats hidden>", built)
        self.assertEqual(build_static_site.page(None).count("data-gh-stats hidden>"), 1)
        self.assertEqual([build_static_site.count_text(n) for n in (0, 999, 1000, 1049, 1250, 9999, 10000, 12600)],
                         ["0", "999", "1k", "1k", "1.2k", "10k", "10k", "13k"])
        # web/backend.js writes them the same way.
        self.assertIn('const fmt = n => (n >= 1000 ? `${(n / 1000).toFixed(n >= 10000 ? 0 : 1).replace(/\\.0$/, "")}k` : String(n));',
                      (WEB / "backend.js").read_text(encoding="utf-8"))

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
        # The site is served under a path (https://<org>.github.io/<repo>/).
        page = (WEB / "index.html").read_text(encoding="utf-8")
        self.assertEqual(re.findall(r'(?:src|href)="/[^"]*"', page), [])
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
        for private in ("claude/sessions", "claude/specs", "asset", "outputs/x", "tools/gripper_scene.py", "tools/umi_tip_video.py"):
            self.assertFalse(covered(private), private)

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
