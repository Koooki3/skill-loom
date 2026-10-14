"""Synthetic fixtures only: no real transcripts, paths or identities."""

import json
from pathlib import Path
import tempfile
import unittest

from skillloom.common import LoomError
from skillloom.cli import host_reports
from skillloom.evidence import observe_claude, observe_codex
from skillloom.recommend import detect, recommend, scan_project
from skillloom.strategy import default_profile, validate_profile
from skillloom.usage import usage_report

HASH = "a" * 40


def lines(path, rows):
    Path(path).write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def claude_turn(day, *blocks):
    return {"type": "assistant", "timestamp": day + "T10:00:00Z", "message": {"content": list(blocks)}}


def tool(name, **arguments):
    return {"type": "tool_use", "name": name, "input": arguments}


def inventory(*names, chars=100):
    return {"skills": [{"name": n, "description_chars": chars} for n in names]}


class ObserveClaudeTests(unittest.TestCase):
    def test_skill_calls_are_exact_and_content_is_not_exported(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "session.jsonl"
            lines(log, [
                {"type": "user", "timestamp": "2026-10-12T09:00:00Z", "message": {"content": "secret prompt text"}},
                claude_turn("2026-10-12", tool("Skill", skill="oil-ui"), tool("Skill", skill="oil-ui"),
                            tool("Skill", skill="plugin:docx"), tool("Skill", skill="Bad Name!"),
                            tool("Agent", subagent_type="Explore", prompt="secret"), tool("Bash", command="ls /home/x")),
                claude_turn("2026-10-14", tool("Skill", skill="oil-ui")),
            ])
            report = observe_claude([log])
        self.assertEqual(report["host"], "claude")
        self.assertEqual(report["skills"]["oil-ui"], {"calls": 3, "sessions": 1})
        self.assertEqual(report["skills"]["plugin:docx"]["calls"], 1)
        self.assertNotIn("Bad Name!", report["skills"])
        self.assertEqual(report["counts"]["skill_calls_unnamed"], 1)
        self.assertEqual(report["subagent_dispatches"], {"Explore": 1})
        self.assertEqual(report["window"], {"first_day": "2026-10-12", "last_day": "2026-10-14", "span_days": 3})
        self.assertEqual(report["counts"]["user_turns"], 1)
        text = json.dumps(report)
        for leaked in ("secret", "/home/x", "session.jsonl"):
            self.assertNotIn(leaked, text)

    def test_malformed_lines_are_counted_not_fatal(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "s.jsonl"
            log.write_text("not json\n[1]\n", encoding="utf-8")
            report = observe_claude([log])
        self.assertEqual(report["counts"], {"malformed_lines": 1})
        self.assertEqual(report["window"]["span_days"], 0)


class ObserveCodexSkillReadTests(unittest.TestCase):
    def test_skill_md_open_is_a_load_signal_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            first, second = Path(tmp) / "a.jsonl", Path(tmp) / "b.jsonl"
            call = {"type": "response_item", "timestamp": "2026-10-12T01:00:00Z",
                    "payload": {"type": "custom_tool_call", "name": "exec", "input": "cat ~/x/skills/team-mode/SKILL.md"}}
            lines(first, [call, call, {**call, "payload": {**call["payload"], "input": "ls skills/Not_Valid/SKILL.md"}}])
            lines(second, [call])
            report = observe_codex([first, second])
        self.assertEqual(report["host"], "codex")
        self.assertEqual(report["skill_md_reads"], {"team-mode": {"calls": 3, "sessions": 2}})
        self.assertEqual(report["skill_attribution"], "not_inferred")
        self.assertIn("load signal", report["limits"])
        self.assertNotIn("~/x", json.dumps(report))


class UsageTests(unittest.TestCase):
    def observation(self, host, files, first, last, table):
        key = "skills" if host == "claude" else "skill_md_reads"
        return {"host": host, "file_count": files, "window": {"first_day": first, "last_day": last}, key: table}

    def test_short_window_never_proposes_deactivation(self):
        obs = [self.observation("claude", 3, "2026-10-12", "2026-10-14", {"a": {"calls": 2, "sessions": 1}})]
        report = usage_report({"claude": inventory("a", "b")}, obs)
        host = report["hosts"][0]
        self.assertFalse(host["window_sufficient"])
        self.assertEqual(host["review_candidates"], [])
        self.assertEqual({r["skill"]: r["status"] for r in host["skills"]}, {"a": "used", "b": "unobserved"})

    def test_sufficient_window_lists_unobserved_by_cost_and_honours_protection(self):
        inv = {"skills": [{"name": "big", "description_chars": 900}, {"name": "small", "description_chars": 50},
                          {"name": "keep", "description_chars": 999}, {"name": "hit", "description_chars": 500}]}
        obs = [self.observation("claude", 12, "2026-10-01", "2026-10-14", {"hit": {"calls": 1, "sessions": 1}, "ext": {"calls": 4, "sessions": 2}})]
        host = usage_report({"claude": inv}, obs, protected=["keep"])["hosts"][0]
        self.assertTrue(host["window_sufficient"])
        self.assertEqual([c["skill"] for c in host["review_candidates"]], ["big", "small"])
        self.assertFalse(host["review_candidates"][0]["automatic_mutation"])
        self.assertEqual(host["seen_but_not_installed"], ["ext"])

    def test_hosts_are_judged_separately_and_codex_reads_are_weaker(self):
        obs = [self.observation("claude", 20, "2026-10-01", "2026-10-14", {"x": {"calls": 1, "sessions": 1}}),
               self.observation("codex", 20, "2026-10-01", "2026-10-14", {"y": {"calls": 1, "sessions": 1}})]
        report = usage_report({"claude": inventory("x", "y"), "codex": inventory("x", "y")}, obs)
        status = {h["host"]: {r["skill"]: r["status"] for r in h["skills"]} for h in report["hosts"]}
        self.assertEqual(status["claude"], {"x": "used", "y": "unobserved"})
        self.assertEqual(status["codex"], {"x": "unobserved", "y": "load-signal"})

    def test_missing_host_observation_is_not_called_unobserved(self):
        host = usage_report({"codex": inventory("a")}, [self.observation("claude", 20, "2026-10-01", "2026-10-14", {})])["hosts"][0]
        self.assertEqual(host["skills"][0]["status"], "no-observation")
        self.assertEqual(host["review_candidates"], [])

    def test_input_validation(self):
        with self.assertRaises(LoomError):
            usage_report({}, [])
        with self.assertRaises(LoomError):
            usage_report({"claude": inventory("a")}, [{"host": "other"}])
        with self.assertRaises(LoomError):
            usage_report({"claude": inventory("a")}, [], min_days=0)


class RecommendTests(unittest.TestCase):
    def catalog(self):
        def item(name, caps, **extra):
            base = {"name": name, "description": "d" * 10, "scope": "general", "capabilities": caps,
                    "source_kind": "pinned_upstream_adaptation",
                    "upstream": {"repo": "o/r", "ref": HASH, "path": "skills/" + name, "license": "MIT"}}
            base.update(extra)
            return base
        return {"skills": [
            item("react-perf", ["react-performance"]),
            item("pr-helper", ["pull-request-review"], upstream={"repo": "o/r", "ref": HASH, "path": "p", "license": "CC-BY-NC-4.0"}),
            item("gh-fix-ci", ["ci-diagnosis"]),
            item("unpinned", ["react-composition"], upstream={"repo": "o/r", "ref": None, "license": None}),
            item("fixed-scope", ["react-performance"], scope="project_specific: one repo"),
            item("local-only", ["react-performance"], source_kind="local_authored", upstream=None),
            item("installed", ["react-performance"]),
            item("unrelated", ["pdf-text-extraction"]),
        ]}

    def project(self, tmp):
        root = Path(tmp) / "proj"
        (root / ".git").mkdir(parents=True)
        (root / ".git" / "config").write_text('[remote "origin"]\n url = git@github.com:o/r.git\n', encoding="utf-8")
        (root / "package.json").write_text(json.dumps({"dependencies": {"react": "1", "next": "1"}}), encoding="utf-8")
        (root / "node_modules" / "pkg").mkdir(parents=True)
        (root / "node_modules" / "pkg" / "x.pdf").write_text("ignored", encoding="utf-8")
        return root

    def test_signals_drive_a_reviewable_queue_without_installing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.project(tmp)
            report = recommend(default_profile(), self.catalog(), {"claude": inventory("installed")}, [root])
        names = [r["skill"] for r in report["recommended"]]
        self.assertEqual(names, ["gh-fix-ci", "pr-helper", "react-perf", "unpinned"])
        self.assertEqual(set(report["signals"]) & {"react", "github"}, {"react", "github"})
        self.assertNotIn("pdf", report["signals"])
        self.assertEqual(report["skipped"]["scoped"], ["fixed-scope"])
        self.assertEqual(report["skipped"]["no_source"], ["local-only"])
        self.assertEqual(report["skipped"]["already_everywhere"], ["installed"])
        by = {r["skill"]: r for r in report["recommended"]}
        self.assertIn("non-commercial-license", by["pr-helper"]["notes"])
        self.assertIn("source-not-pinned", by["unpinned"]["notes"])
        self.assertIn("license-unknown", by["unpinned"]["notes"])
        self.assertEqual(by["unpinned"]["next_action"], "pin-source-first")
        self.assertNotIn("stage_command", by["unpinned"])
        self.assertIn("--commit " + HASH, by["react-perf"]["stage_command"])
        self.assertTrue(all(r["automatic_install"] is False for r in report["recommended"]))
        self.assertNotIn(str(root), json.dumps(report))

    def test_required_capability_outranks_signal_only_matches(self):
        profile = default_profile()
        profile["required_capabilities"] = ["react-composition"]
        with tempfile.TemporaryDirectory() as tmp:
            report = recommend(profile, self.catalog(), {"claude": inventory()}, [self.project(tmp)])
        self.assertEqual(report["recommended"][0]["skill"], "unpinned")

    def test_scoped_skills_only_with_explicit_opt_in(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = recommend(default_profile(), self.catalog(), {"claude": inventory()}, [self.project(tmp)], allow_scoped=True)
        self.assertIn("fixed-scope", [r["skill"] for r in report["recommended"]])

    def test_budget_headroom_flags_overflow(self):
        profile = default_profile()
        profile["budgets"]["active_skills"] = 2
        with tempfile.TemporaryDirectory() as tmp:
            report = recommend(profile, self.catalog(), {"claude": inventory("installed")}, [self.project(tmp)])
        self.assertEqual(report["budget_headroom"]["skills"], 1)
        self.assertEqual([r["within_skill_budget"] for r in report["recommended"]], [True, False, False, False])

    def test_scan_skips_vendored_dirs_and_reports_counts_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            scan = scan_project(self.project(tmp))
        self.assertNotIn(".pdf", scan["suffixes"])
        self.assertTrue(scan["github_remote"])
        self.assertIn("react", scan["dependencies"])
        self.assertEqual(detect([scan])["react"]["markers"], ["next", "react"])

    def test_pyproject_prose_is_not_a_dependency(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pyproject.toml").write_text(
                '[project]\ndescription = "we talk about react and mcp in prose"\ndependencies = ["mcp>=1", "numpy"]\n', encoding="utf-8")
            scan = scan_project(root)
        self.assertIn("mcp", scan["dependencies"])
        self.assertNotIn("react", scan["dependencies"])

    def test_bad_inputs(self):
        with self.assertRaises(LoomError):
            recommend(default_profile(), self.catalog(), {}, [])
        with self.assertRaises(LoomError):
            scan_project("/nonexistent-root-for-skillloom-tests")


class ProfileAndCliHelperTests(unittest.TestCase):
    def test_default_profile_is_valid(self):
        self.assertEqual(validate_profile(default_profile())["schema"], 1)

    def test_host_reports_requires_one_pair_per_host(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "r.json"
            path.write_text("{}", encoding="utf-8")
            self.assertEqual(host_reports([f"claude={path}"]), {"claude": {}})
            for bad in ([str(path)], ["=" + str(path)], ["claude="], [f"claude={path}", f"claude={path}"]):
                with self.assertRaises(LoomError):
                    host_reports(bad)


if __name__ == "__main__":
    unittest.main()
