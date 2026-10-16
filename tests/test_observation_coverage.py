
"""Synthetic accounting contracts; no inference about usefulness or task quality."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest

from skillloom.cli import parser
from skillloom.evidence import observe_claude, observe_codex
from skillloom.usage import usage_report


def inventory(*names):
    return {"skills": [{"name": name, "description_chars": 100} for name in names]}


def observation(host, files, first="2026-10-01", last="2026-10-07", table=None):
    key = "skills" if host == "claude" else "skill_md_reads"
    return {"host": host, "file_count": files,
            "window": {"first_day": first, "last_day": last}, key: table or {}}


def report(host, observations):
    return usage_report({host: inventory("used", "rare")}, observations)["hosts"][0]


class ObservationInputIdentityTests(unittest.TestCase):
    def fixture(self, root, host):
        path = root / "private-name.jsonl"
        rows = []
        for day in ("2026-10-01", "2026-10-07"):
            if host == "codex":
                rows.append({"timestamp": day + "T00:00:00Z", "type": "response_item",
                             "payload": {"type": "function_call", "arguments": "read skills/used/SKILL.md"}})
            else:
                rows.append({"timestamp": day + "T00:00:00Z", "type": "assistant",
                             "message": {"content": [{"type": "tool_use", "name": "Skill",
                                                       "input": {"skill": "used"}}]}})
        path.write_text("\n".join(map(json.dumps, rows)), encoding="utf8")
        return path

    def test_repeated_paths_and_aliases_do_not_create_files_or_calls(self):
        for host, observer, table in (("codex", observe_codex, "skill_md_reads"),
                                      ("claude", observe_claude, "skills")):
            with self.subTest(host=host), tempfile.TemporaryDirectory() as tmp:
                path = self.fixture(Path(tmp), host)
                alias_parent = path.parent / "alias-parent"
                alias_parent.mkdir()
                alias = alias_parent / ".." / path.name
                observed = observer([path] * 9 + [alias])
                self.assertEqual(observed["file_count"], 1)
                self.assertEqual(observed["duplicate_inputs_skipped"], 9)
                self.assertEqual(observed[table]["used"], {"calls": 2, "sessions": 1})
                self.assertFalse(report(host, [observed])["window_sufficient"])
                self.assertNotIn("private-name", json.dumps(observed))
                self.assertNotIn(str(path), json.dumps(observed))

    def test_hardlinks_share_one_filesystem_object(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self.fixture(root, "codex")
            alias = root / "hardlink.jsonl"
            os.link(path, alias)
            observed = observe_codex([path, alias])
            self.assertEqual(observed["file_count"], 1)
            self.assertEqual(observed["duplicate_inputs_skipped"], 1)

    def test_distinct_files_remain_distinct_without_logical_session_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self.fixture(root, "claude")
            copied = root / "copy.jsonl"
            copied.write_bytes(path.read_bytes())
            observed = observe_claude([path, copied])
            self.assertEqual(observed["file_count"], 2)
            self.assertEqual(observed["counting_unit"], "distinct-filesystem-objects")
            self.assertIn("copied or overlapping", observed["limits"])

    def test_cli_file_threshold_and_legacy_alias_match(self):
        for option in ("--min-files", "--min-sessions"):
            args = parser().parse_args(["usage", "--inventory", "codex=sample.json", "--observation", "obs.json", "--out", "out.json", option, "12"])
            self.assertEqual(args.min_sessions, 12)


class AggregateCoverageTests(unittest.TestCase):
    def test_duplicate_aggregate_cannot_cross_file_threshold(self):
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                under = observation(host, 6)
                once, repeated = report(host, [under]), report(host, [under, copy.deepcopy(under)])
                self.assertFalse(repeated["window_sufficient"])
                self.assertEqual(repeated["observed_files"], once["observed_files"])
                self.assertEqual(repeated["review_candidates"], [])

    def test_date_endpoints_from_different_reports_are_not_spliced(self):
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                result = report(host, [observation(host, 10, "2026-10-01", "2026-10-01"),
                                       observation(host, 10, "2026-10-07", "2026-10-07")])
                self.assertEqual(result["span_days"], 1)
                self.assertFalse(result["window_sufficient"])

    def test_both_thresholds_must_hold_in_the_same_report(self):
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                result = report(host, [observation(host, 10, "2026-10-01", "2026-10-01"),
                                       observation(host, 1, "2026-10-01", "2026-10-08")])
                self.assertEqual(result["observed_files"], 10)
                self.assertEqual(result["span_days"], 8)
                self.assertFalse(result["window_sufficient"])

    def test_positive_signal_from_small_report_prevents_candidate(self):
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                large = observation(host, 10)
                small = observation(host, 1, "2026-10-08", "2026-10-08",
                                    {"used": {"calls": 1, "sessions": 1}})
                result = report(host, [large, small])
                self.assertTrue(result["window_sufficient"])
                self.assertEqual([row["skill"] for row in result["review_candidates"]], ["rare"])
                self.assertEqual(result["skills"][0]["status"], "used" if host == "claude" else "load-signal")

    def test_report_order_and_reimport_preserve_counts_and_decisions(self):
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                large = observation(host, 10, table={"used": {"calls": 4, "sessions": 2}})
                small = observation(host, 3, table={"used": {"calls": 3, "sessions": 3}})
                first = report(host, [large, small])
                repeat = report(host, [small, large, copy.deepcopy(large)])
                for key in ("observed_files", "span_days", "window_sufficient", "skills",
                            "review_candidates", "seen_but_not_installed"):
                    self.assertEqual(first[key], repeat[key])
                self.assertEqual(first["skills"][0]["calls"], 4)
                self.assertEqual(first["skills"][0]["sessions"], 3)
                self.assertEqual(first["count_aggregation"], "per-skill-maximum")

    def test_legacy_reports_and_empty_windows_remain_supported(self):
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                self.assertTrue(report(host, [observation(host, 10)])["window_sufficient"])
                self.assertFalse(report(host, [{"host": host}])["window_sufficient"])
                self.assertFalse(report(host, [])["window_sufficient"])
