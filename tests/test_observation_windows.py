"""Synthetic window contracts, distinct from host or model performance."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from skillloom.cli import main
from skillloom.common import LoomError
from skillloom.evidence import observe_codex, observe_claude
from skillloom.usage import usage_report


SINCE = "2026-10-30T00:00:00Z"
UNTIL = "2026-11-06T00:00:00Z"


def row(host, timestamp, name="used"):
    if host == "codex":
        value = {"type": "response_item",
                 "payload": {"type": "function_call", "arguments": "skills/" + name + "/SKILL.md"}}
    else:
        value = {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Skill", "input": {"skill": name}}]}}
    if timestamp is not None:
        value["timestamp"] = timestamp
    return value


def write(path, rows):
    path.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf8")
    return path


HOSTS = (("codex", observe_codex, "skill_md_reads"), ("claude", observe_claude, "skills"))


class ObservationWindowTests(unittest.TestCase):
    def test_exclusive_inclusive_offsets_unordered_and_utc_days(self):
        for host, observer, key in HOSTS:
            with self.subTest(host=host), tempfile.TemporaryDirectory() as tmp:
                p = write(Path(tmp) / "private.jsonl", [
                    row(host, UNTIL), row(host, "2026-10-30T08:00:00+08:00", "boundary"),
                    row(host, "2026-10-30T01:00:00+01:00", "boundary"),
                    row(host, "2026-11-06T00:00:00.000001Z", "future"),
                    row(host, "2026-10-30T00:00:00.000001Z"),
                    row(host, "2026-11-06T07:00:00+08:00")])
                r = observer([p], since=SINCE, until=UNTIL)
                self.assertEqual(r[key], {"used": {"calls": 3, "sessions": 1}})
                self.assertEqual(r["record_selection"]["matching_records"], 3)
                self.assertEqual(r["record_selection"]["outside_window_records"], 3)
                self.assertEqual(r["window"], {"first_day": "2026-10-30", "last_day": "2026-11-06", "span_days": 8})
                equivalent = observer([p], since="2026-10-30T08:00:00+08:00", until="2026-11-06T08:00:00+08:00")
                self.assertEqual(r[key], equivalent[key])
                self.assertEqual(r["record_selection"], equivalent["record_selection"])

    def test_untimed_and_invalid_objects_do_not_become_activity(self):
        for host, observer, key in HOSTS:
            with self.subTest(host=host), tempfile.TemporaryDirectory() as tmp:
                bad = [None, "2026-11-01", "2026-11-01T00:00:00", "2026-02-30T00:00:00Z", 10, "9999-12-31T23:59:59-23:59"]
                p = write(Path(tmp) / "private.jsonl", [row(host, t) for t in bad] + [[], None])
                r = observer([p], since=SINCE)
                self.assertEqual(r["file_count"], 0)
                self.assertEqual(r[key], {})
                self.assertEqual(r["record_selection"]["untimed_records_skipped"], len(bad))
                self.assertIsNone(r["window"]["first_day"])

    def test_empty_selected_files_cannot_satisfy_usage_coverage(self):
        for host, observer, key in HOSTS:
            with self.subTest(host=host), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                paths = [write(root / str(i), [row(host, "2026-01-01T00:00:00Z")]) for i in range(10)]
                paths += [write(root / "matching", [row(host, "2026-10-31T00:00:00Z"), row(host, UNTIL)])]
                r = observer(paths + [paths[-1]], since=SINCE, until=UNTIL)
                self.assertEqual(r["file_count"], 1)
                self.assertEqual(r["record_selection"]["selected_file_count"], 11)
                self.assertEqual(r["duplicate_inputs_skipped"], 1)
                result = usage_report({host: {"skills": [{"name": "rare", "description_chars": 4}]}}, [r])["hosts"][0]
                self.assertFalse(result["window_sufficient"])
                self.assertEqual(result["review_candidates"], [])

    def test_adjacent_windows_partition_boundary_and_keep_default(self):
        for host, observer, key in HOSTS:
            with self.subTest(host=host), tempfile.TemporaryDirectory() as tmp:
                p = write(Path(tmp) / "private.jsonl", [row(host, t) for t in (SINCE, "2026-11-01T00:00:00Z", UNTIL)])
                earlier = observer([p], until="2026-11-01T00:00:00Z")
                later = observer([p], since="2026-11-01T00:00:00Z")
                default = observer([p])
                self.assertNotIn("record_selection", default)
                self.assertEqual(default[key]["used"]["calls"], 3)
                self.assertEqual(earlier[key]["used"]["calls"] + later[key]["used"]["calls"], 3)

    def test_cumulative_codex_tokens_are_not_interval_costs(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = write(Path(tmp) / "private.jsonl", [
                {"type": "event_msg", "timestamp": "2026-10-31T00:00:00Z",
                 "payload": {"type": "token_count", "info": {"total_token_usage": {"total_tokens": 9999}}}}])
            default = observe_codex([p])
            filtered = observe_codex([p], since=SINCE)
            self.assertEqual(default["reported_total_tokens_sum"], 9999)
            self.assertIsNone(filtered["reported_total_tokens_sum"])
            self.assertEqual(filtered["files_with_usage"], 0)
            self.assertEqual(filtered["record_selection"]["token_totals"], "not_computed_for_filtered_window")

    def test_invalid_bounds_fail_before_reading_or_output(self):
        invalid = [
            {"since": "2026-11-01"}, {"until": "2026-11-01T00:00:00"},
            {"since": ""}, {"since": 1}, {"since": UNTIL, "until": SINCE},
            {"since": SINCE, "until": "2026-10-30T08:00:00+08:00"}]
        for _, observer, _ in HOSTS:
            for bounds in invalid:
                with self.subTest(observer=observer.__name__, bounds=bounds), self.assertRaises(LoomError):
                    observer(["nonexistent-private-path"], **bounds)

    def test_documented_cli_routes_and_malformed_scan_scope(self):
        for host, _, key in HOSTS:
            with self.subTest(host=host), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                p = write(root / "private.jsonl", [row(host, "2026-10-31T00:00:00Z")])
                with p.open("a", encoding="utf8") as f:
                    f.write("\nmalformed private payload")
                out = root / "out.json"
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    status = main(["observe-" + host, "--log", str(p), "--since", SINCE, "--until", UNTIL, "--out", str(out)])
                self.assertEqual(status, 0)
                result = json.loads(out.read_text(encoding="utf8"))
                self.assertEqual(result[key]["used"]["calls"], 1)
                self.assertEqual(result["counts"]["malformed_lines"], 1)
                self.assertNotIn("private", json.dumps(result))
                out.unlink()
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    status = main(["observe-" + host, "--log", str(p), "--since", "bad", "--out", str(out)])
                self.assertEqual(status, 2)
                self.assertFalse(out.exists())
