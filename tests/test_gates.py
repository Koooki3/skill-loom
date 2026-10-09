"""Malformed evidence must remain an explicit error at every gate entrypoint."""

from contextlib import redirect_stderr
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from skillloom.cli import main
from skillloom.common import LoomError, digest, write_json
from skillloom.gates import PROFILES, gate


class ReceiptValidation(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.receipt = self.base / "receipt.json"
        (self.base / "evidence.txt").write_bytes(b"fixture")
        self.artifact = {"path": "evidence.txt", "sha256": digest(b"fixture")}

    def tearDown(self):
        self.temp.cleanup()

    def valid(self):
        return {"checks": [{"id": name, "status": "pass", "artifacts": [dict(self.artifact)]}
                           for name in sorted(PROFILES["skill-change"])]}

    def test_nonobject_receipts_are_explicit_errors(self):
        for value in ([], None, True, 1, "receipt"):
            with self.subTest(value=value):
                write_json(self.receipt, value)
                with self.assertRaises(LoomError):
                    gate(self.receipt, "skill-change")

    def test_malformed_check_shapes_are_explicit_errors(self):
        values = [{"checks": value} for value in (None, {}, "checks")]
        values += [{"checks": [value]} for value in (None, [], "check")]
        values += [{"checks": [{"id": value}]} for value in (None, [], {}, True, 1, "", "   ")]
        values += [{"profile": [], "checks": []}, {"checks": [{"id": "same"}, {"id": "same"}]}]
        for value in values:
            with self.subTest(value=value):
                write_json(self.receipt, value)
                with self.assertRaises(LoomError):
                    gate(self.receipt, "skill-change")

    def test_malformed_artifacts_are_explicit_errors(self):
        collections = [None, {}, "artifacts", [None], [[]], ["artifact"], [{}],
                       [{"path": [], "sha256": "a" * 64}],
                       [{"path": " ", "sha256": "a" * 64}],
                       [{"path": "evidence.txt", "sha256": []}],
                       [{"path": "evidence.txt", "sha256": "not-a-digest"}]]
        for artifacts in collections:
            with self.subTest(artifacts=artifacts):
                write_json(self.receipt, {"checks": [{"id": "scope", "status": "pass", "artifacts": artifacts}]})
                with self.assertRaises(LoomError):
                    gate(self.receipt, "skill-change")

    def test_full_shape_validation_precedes_artifact_reads(self):
        value = self.valid()
        value["checks"].append({"id": []})
        write_json(self.receipt, value)
        with patch.object(Path, "read_bytes", side_effect=AssertionError("premature artifact read")):
            with self.assertRaises(LoomError):
                gate(self.receipt, "skill-change")

    def test_valid_and_incomplete_receipts_keep_existing_verdicts(self):
        value = self.valid()
        write_json(self.receipt, value)
        self.assertEqual(gate(self.receipt, "skill-change")["status"], "pass")
        value["checks"][0]["artifacts"] = []
        write_json(self.receipt, value)
        self.assertEqual(gate(self.receipt, "skill-change")["status"], "fail")

    def test_cli_and_hook_report_invalid_receipts_without_tracebacks(self):
        write_json(self.receipt, [])
        errors = io.StringIO()
        with redirect_stderr(errors):
            code = main(["gate", "--receipt", str(self.receipt), "--profile", "skill-change"])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(errors.getvalue())["error_type"], "LoomError")
        hook = Path(__file__).resolve().parents[1] / "scripts/stop_gate.py"
        result = subprocess.run([sys.executable, "-B", str(hook), "--receipt", str(self.receipt),
                                 "--expected-run-id", "fixture", "--expected-candidate-digest", "a" * 64],
                                input="{}", text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 1)
        self.assertIn("unverified", json.loads(result.stdout)["systemMessage"])
        self.assertNotIn("Traceback", result.stderr)
