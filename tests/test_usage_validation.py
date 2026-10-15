"""Invalid usage reports are rejected before publishing output. Synthetic data only."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from skillloom.common import LoomError
from skillloom.usage import usage_report


def inventory():
    return {"claude": {"skills": [{"name": "unused", "description_chars": 80}]}}


def observation(**changes):
    report = {"host": "claude", "file_count": 10,
              "window": {"first_day": "2026-10-01", "last_day": "2026-10-07"},
              "skills": {}}
    report.update(changes)
    return report


class UsageInputTests(unittest.TestCase):
    def test_report_structure_errors_are_controlled(self):
        invalid = [
            None, [], "not a report", {"host": []}, {"host": {}}, {"host": "claude", "window": None},
            observation(skills=[]), observation(skills={"unused": []}),
            observation(skills={"": {"calls": 1}}),
        ]
        for report in invalid:
            with self.subTest(report=report), self.assertRaises(LoomError):
                usage_report(inventory(), [report])
        for inventories in ([], {"claud": inventory()["claude"]}, {"claude": None}, {"claude": {"skills": None}},
                            {"claude": {"skills": [[]]}}, {"claude": {"skills": [{"name": []}]}}):
            with self.subTest(inventories=inventories), self.assertRaises(LoomError):
                usage_report(inventories, [observation()])

    def test_invalid_counts_cannot_supply_evidence(self):
        for value in (-1, True, 2.5, "10", None):
            with self.subTest(field="file_count", value=value), self.assertRaises(LoomError):
                usage_report(inventory(), [observation(file_count=value)])
            for field in ("calls", "sessions"):
                with self.subTest(field=field, value=value), self.assertRaises(LoomError):
                    usage_report(inventory(), [observation(skills={"unused": {**{"calls": 1, "sessions": 1}, field: value}})])
            with self.subTest(field="description_chars", value=value), self.assertRaises(LoomError):
                usage_report({"claude": {"skills": [{"name": "unused", "description_chars": value}]}},
                             [observation()])

    def test_populated_reports_require_explicit_tables_and_counts(self):
        missing_table = observation()
        del missing_table["skills"]
        reports = [missing_table,
                   {**missing_table, "host": "codex"},
                   observation(skills={"unused": {}}),
                   observation(skills={"unused": {"calls": 1}}),
                   observation(skills={"unused": {"sessions": 1}}),
                   observation(skills={"unused": {"calls": 1, "sessions": 2}}),
                   observation(skills={"unused": {"calls": 12, "sessions": 11}}),
                   observation(skills={"unused": {"calls": 1, "sessions": 0}}),
                   observation(file_count=0, skills={"unused": {"calls": 1, "sessions": 1}})]
        for report in reports:
            with self.subTest(report=report), self.assertRaises(LoomError):
                usage_report(inventory(), [report])

    def test_invalid_window_does_not_produce_review_candidates(self):
        windows = [
            {"first_day": "2026-W01-1", "last_day": "2026-01-11"},
            {"first_day": "2026-01-01", "last_day": "2026-W02-1"},
            {"first_day": "2026-10-01"},
            {"first_day": "2026-10-01", "last_day": 7},
            {"first_day": "2026-02-30", "last_day": "2026-10-07"},
            {"first_day": "2026-10-07", "last_day": "2026-10-01"},
        ]
        for window in windows:
            with self.subTest(window=window), self.assertRaises(LoomError):
                usage_report(inventory(), [observation(window=window)])

    def test_thresholds_and_protection_have_explicit_types(self):
        for value in (True, 0, -1, 1.5, "7", None):
            for field in ("min_sessions", "min_days"):
                with self.subTest(field=field, value=value), self.assertRaises(LoomError):
                    usage_report(inventory(), [observation()], **{field: value})
        for protected in ("unused", [None], [[]]):
            with self.subTest(protected=protected), self.assertRaises(LoomError):
                usage_report(inventory(), [observation()], protected=protected)

    def test_optional_fields_and_valid_statuses_remain_compatible(self):
        for window in ({}, {"first_day": None, "last_day": None, "span_days": 0}):
            host = usage_report({"claude": {"skills": [{"name": "unused"}]}},
                                [{"host": "claude", "window": window}])["hosts"][0]
            self.assertEqual(host["skills"][0]["status"], "unobserved")
            self.assertEqual(host["review_candidates"], [])
        host = usage_report(inventory(), [observation()], protected=("unused",))["hosts"][0]
        self.assertTrue(host["window_sufficient"])
        self.assertEqual(host["review_candidates"], [])
        self.assertEqual(usage_report(inventory(), [observation()])["hosts"][0]["review_candidates"][0]["skill"],
                         "unused")

    def test_cli_rejects_invalid_json_shapes_without_replacing_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inv, obs, output = root / "inventory.json", root / "observation.json", root / "output.json"
            inv.write_text(json.dumps(inventory()["claude"]), encoding="utf-8")
            for report in ([], observation(window=None), observation(skills={"unused": []}),
                           {key: value for key, value in observation().items() if key != "skills"},
                           observation(skills={"unused": {"sessions": 1}})):
                obs.write_text(json.dumps(report), encoding="utf-8")
                for existing in (False, True):
                    if output.exists():
                        output.unlink()
                    if existing:
                        output.write_text("keep existing output", encoding="utf-8")
                    result = subprocess.run(
                        [sys.executable, "-B", "-m", "skillloom", "usage", "--inventory", f"claude={inv}",
                         "--observation", str(obs), "--out", str(output)],
                        cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, encoding="utf-8",
                    )
                    with self.subTest(report=report, existing=existing):
                        self.assertEqual(result.returncode, 2, result.stderr)
                        self.assertEqual(json.loads(result.stderr)["error_type"], "LoomError")
                        self.assertNotIn("Traceback", result.stderr)
                        if existing:
                            self.assertEqual(output.read_text(encoding="utf-8"), "keep existing output")
                        else:
                            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
