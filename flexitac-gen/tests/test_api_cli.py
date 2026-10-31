"""Command-line interface (audit M14; decision D15), run as a subprocess."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from engine import generate_design

ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(self.directory, ignore_errors=True))
        (self.directory / "small.json").write_text('{"rows": 4, "columns": 5}', encoding="utf-8")
        (self.directory / "typo.json").write_text('{"matrix": {"colums": 5}}', encoding="utf-8")
        (self.directory / "nan.json").write_text('{"rows": NaN}', encoding="utf-8")

    def run_cli(self, *args: str, stdin: bytes = b"") -> tuple[int, object]:
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        completed = subprocess.run(
            [sys.executable, "-B", str(ROOT / "cli.py"), *args], input=stdin, capture_output=True, cwd=self.directory, env=environment, timeout=300
        )
        return completed.returncode, json.loads(completed.stdout) if completed.stdout.strip() else completed.stderr.decode()

    def test_schema(self) -> None:
        code, schema = self.run_cli("schema")
        self.assertEqual(code, 0)
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertFalse(schema["additionalProperties"])
        # Every CLI-level code the tool can print is listed.
        used = set(re.findall(r'"(E_[A-Z_]+)"', (ROOT / "cli.py").read_text(encoding="utf-8")))
        self.assertEqual(set(schema["x-cli-error-codes"]), used)
        # --pretty is accepted after the command as well as before it.
        for args in (("schema", "--pretty"), ("--pretty", "schema")):
            completed = subprocess.run([sys.executable, "-B", str(ROOT / "cli.py"), *args], capture_output=True, timeout=300,
                                       env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue(completed.stdout.startswith(b"{\n  "), args)

    def test_a_document_that_is_not_one_object_is_rejected(self) -> None:
        # The engine reads a missing design as "use the defaults"; a design file never means that.
        documents = {"null.json": "null", "list.json": "[1, 2]", "text.json": '"design"', "number.json": "5", "flag.json": "true"}
        for name, text in documents.items():
            (self.directory / name).write_text(text, encoding="utf-8")
        for command in (("validate",), ("generate", "--compact"), ("export", "--out", "out")):
            for name in documents:
                with self.subTest(command=command, document=name):
                    code, result = self.run_cli(*command, name)
                    self.assertEqual(code, 2)
                    self.assertEqual((result["ok"], result["code"], result["field"]), (False, "E_CLI_NOT_OBJECT", "$"))
            with self.subTest(command=command, stdin="null"):
                code, result = self.run_cli(*command, "-", stdin=b"null")
                self.assertEqual((code, result["code"]), (2, "E_CLI_NOT_OBJECT"))
        self.assertFalse((self.directory / "out").exists())
        # In a batch the valid design is still exported.
        code, batch = self.run_cli("export", "--out", "out", "small.json", "null.json")
        self.assertEqual(code, 2)
        self.assertEqual([entry.get("code") for entry in batch["results"]], [None, "E_CLI_NOT_OBJECT"])
        self.assertEqual(len(list((self.directory / "out").iterdir())), 3)

    def test_an_unwritable_output_directory_is_a_structured_error(self) -> None:
        (self.directory / "taken").write_text("not a directory", encoding="utf-8")
        code, result = self.run_cli("export", "--out", "taken", "small.json")
        self.assertEqual(code, 2)
        self.assertEqual((result["ok"], result["code"]), (False, "E_CLI_OUTPUT"))
        self.assertEqual(result["build_id"], generate_design({"rows": 4, "columns": 5})["manifest"]["build_id"])

    def test_validate(self) -> None:
        code, result = self.run_cli("validate", "small.json")
        self.assertEqual(code, 0)
        self.assertTrue(result["ok"])
        self.assertEqual(result["identity"]["build_id"], generate_design({"rows": 4, "columns": 5})["manifest"]["build_id"])
        code, result = self.run_cli("validate", "typo.json")
        self.assertEqual(code, 1)
        self.assertEqual(result["validation"]["errors"][0]["code"], "E_UNKNOWN_FIELD")
        code, result = self.run_cli("validate", "-", stdin=b'{"rows": 2}')
        self.assertEqual((code, result["design"]["matrix"]["rows"]), (0, 2))

    def test_generate_full_and_compact(self) -> None:
        code, full = self.run_cli("generate", "small.json")
        self.assertEqual(code, 0)
        self.assertNotIn("derived_layout", full)
        self.assertIn("svg", full["boards"]["row"])
        code, compact = self.run_cli("--pretty", "generate", "--compact", "small.json")
        self.assertEqual(code, 0)
        self.assertEqual(set(compact), {"ok", "design", "validation", "manifest", "boards"})
        self.assertNotIn("svg", compact["boards"]["row"])
        self.assertEqual(compact["manifest"], full["manifest"])

    def test_export_writes_build_id_named_archives(self) -> None:
        code, summary = self.run_cli("export", "small.json", "--out", "out")
        self.assertEqual(code, 0)
        build_id = summary["build_id"]
        self.assertEqual(
            sorted(Path(path).name for path in summary["files"].values()),
            sorted([f"{build_id}-project-review.zip", f"{build_id}-top-rows-direct-gerber.zip", f"{build_id}-bottom-columns-direct-gerber.zip"]),
        )
        for path in summary["files"].values():
            self.assertTrue(Path(path).is_absolute())
            self.assertTrue(zipfile.is_zipfile(path))
        self.assertEqual(sorted(p.name for p in (self.directory / "out").iterdir()), sorted(Path(p).name for p in summary["files"].values()))

    def test_several_inputs_are_a_batch(self) -> None:
        code, batch = self.run_cli("generate", "--compact", "small.json", "typo.json")
        self.assertEqual(code, 1)
        self.assertFalse(batch["ok"])
        self.assertEqual([(entry["input"], entry["ok"]) for entry in batch["results"]], [("small.json", True), ("typo.json", False)])
        code, batch = self.run_cli("export", "--out", "batch", "small.json", "typo.json", "nan.json", "missing.json")
        self.assertEqual(code, 2)
        entries = {entry["input"]: entry for entry in batch["results"]}
        self.assertEqual(len(entries["small.json"]["files"]), 3)
        self.assertEqual(entries["typo.json"]["code"], "E_EXPORT_BLOCKED")
        self.assertEqual(entries["nan.json"]["code"], "E_CLI_INVALID_JSON")
        self.assertEqual(entries["missing.json"]["code"], "E_CLI_INPUT")
        self.assertEqual(len(list((self.directory / "batch").iterdir())), 3)
        code, batch = self.run_cli("validate", "small.json", "small.json")
        self.assertEqual((code, batch["ok"], len(batch["results"])), (0, True, 2))

    def test_a_batch_exits_with_its_worst_status_wherever_that_entry_is(self) -> None:
        # docs/API.md: a batch exits with the largest status of its entries, so
        # the failing entry is put first here (stage-T reviewer finding: every
        # other batch ends with its worst entry, where "last" and "largest" agree).
        for command, inputs, status in (
            (("validate",), ("typo.json", "small.json"), 1),
            (("generate", "--compact"), ("missing.json", "typo.json", "small.json"), 2),
            (("export", "--out", "first"), ("nan.json", "small.json", "typo.json"), 2),
        ):
            with self.subTest(command=command, inputs=inputs):
                code, batch = self.run_cli(*command, *inputs)
                self.assertEqual(code, status)
                self.assertFalse(batch["ok"])
                self.assertEqual([entry["input"] for entry in batch["results"]], list(inputs))
                self.assertTrue(next(entry for entry in batch["results"] if entry["input"] == "small.json")["ok"])
        # The valid design after an unreadable one is still exported.
        self.assertEqual(len(list((self.directory / "first").iterdir())), 3)


if __name__ == "__main__":
    unittest.main()
