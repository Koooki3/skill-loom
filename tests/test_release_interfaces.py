
"""Synthetic release-interface regressions; generated commands are never executed."""
import json
import os
from pathlib import Path
import tempfile
import unittest

from skillloom.cli import parser
from skillloom.common import LoomError
from skillloom.evidence import observe_codex
from skillloom.recommend import detect, recommend, scan_project
from skillloom.strategy import default_profile
from skillloom.usage import usage_report


class ReleaseInterfaceTests(unittest.TestCase):
    def test_windows_skill_read_prevents_unobserved_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "synthetic.jsonl"
            payload = {"type": "function_call",
                       "arguments": json.dumps({"cmd": r"Get-Content X:\synthetic\skills\used\SKILL.md"})}
            path.write_text(json.dumps({"timestamp": "2026-10-01T00:00:00Z",
                                        "type": "response_item", "payload": payload}), encoding="utf8")
            observation = observe_codex([path])
        inventory = {"skills": [{"name": "used"}]}
        host = usage_report({"codex": inventory}, [observation], min_sessions=1, min_days=1)["hosts"][0]
        self.assertTrue(host["window_sufficient"])
        self.assertEqual(host["skills"][0]["status"], "load-signal")
        self.assertEqual(host["review_candidates"], [])

    def test_windows_and_mixed_separators_in_custom_tool_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "synthetic.jsonl"
            payload = {"type": "custom_tool_call",
                       "input": r"read X:\fixture\skills\used\SKILL.md and skills/other\SKILL.md"}
            path.write_text(json.dumps({"type": "response_item", "payload": payload}), encoding="utf8")
            observation = observe_codex([path])
        self.assertEqual(set(observation["skill_md_reads"]), {"used", "other"})

    def test_linked_worktree_remote_marker_absolute_and_relative(self):
        for absolute in (True, False):
            with self.subTest(absolute=absolute), tempfile.TemporaryDirectory() as tmp:
                base = Path(tmp)
                project = base / "project"
                project.mkdir()
                common = base / "git-metadata"
                git_dir = common / "worktrees" / "fixture"
                git_dir.mkdir(parents=True)
                target = str(git_dir) if absolute else os.path.relpath(git_dir, project)
                (project / ".git").write_text("gitdir: " + target + "\n", encoding="utf8")
                (git_dir / "commondir").write_text("../..\n", encoding="utf8")
                (common / "config").write_text('[remote "origin"]\nurl = https://github.com/example/project.git\n',
                                               encoding="utf8")
                scan = scan_project(project)
                self.assertTrue(scan["github_remote"])
                self.assertIn("github", detect([scan]))

    def recommendation(self, upstream):
        profile = default_profile()
        profile["required_capabilities"] = ["project-documentation"]
        catalog = {"skills": [{"name": "docs", "description": "Synthetic fixture",
                               "capabilities": ["project-documentation"],
                               "source_kind": "pinned_upstream_adaptation", "upstream": upstream}]}
        return recommend(profile, catalog, {"codex": {"skills": []}}, [])

    def test_invalid_sources_are_rejected_before_command_output(self):
        valid = {"repo": "owner/project", "ref": "a" * 40, "path": "skills/docs"}
        for override in ({"repo": "o/r; echo synthetic"}, {"repo": ["o/r"]},
                         {"ref": ["main"]}, {"path": "../outside"}, {"path": None}):
            with self.subTest(override=override), self.assertRaises(LoomError):
                self.recommendation(dict(valid, **override))

    def test_shell_metacharacters_in_portable_path_use_only_argv(self):
        for path in ("skills/with space", "skills/notes;echo", "skills/$(placeholder)", "skills/quote'name"):
            with self.subTest(path=path):
                entry = self.recommendation({"repo": "owner/project", "ref": "a" * 40,
                                             "path": path})["recommended"][0]
                self.assertNotIn("stage_command", entry)
                self.assertIn("stage-argv-only", entry["notes"])
                self.assertIn("--path=" + path, entry["stage_argv"])
                parsed = parser().parse_args(entry["stage_argv"][3:])
                self.assertEqual(parsed.path, path)

    def test_safe_template_and_structured_arguments_preserve_valid_sources(self):
        entry = self.recommendation({"repo": "owner/project", "ref": "a" * 40,
                                     "path": "-skills/docs"})["recommended"][0]
        self.assertIn("--path=-skills/docs", entry["stage_command"])
        self.assertIn("--destination '<NEW_DIRECTORY>'", entry["stage_command"])
        parsed = parser().parse_args(entry["stage_argv"][3:])
        self.assertEqual(parsed.repo, "owner/project")
        self.assertEqual(parsed.path, "-skills/docs")
