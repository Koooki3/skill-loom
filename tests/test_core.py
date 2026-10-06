import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from skillloom.common import LoomError, atomic_write, digest, object_digest, snapshot, write_json
from skillloom.cleanup import MARKER, cleanup_apply, cleanup_plan
from skillloom.demo import run_demo
from skillloom.evidence import observe_codex, suggest, summarize_events
from skillloom.gates import PROFILES, gate, stop_decision
from skillloom.inventory import inventory
from skillloom.sources import stage
from skillloom.transactions import apply, plan_change, rollback


class Workspace(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name).resolve()
        self.runtime = self.base / "runtime"
        self.candidate = self.base / "candidate" / "example-skill"
        self.journal = self.base / "journal"
        self.skill(self.candidate, "Use supplied evidence.")

    def tearDown(self):
        self.temp.cleanup()

    def skill(self, path, text):
        atomic_write(path / "SKILL.md", f"---\nname: example-skill\ndescription: Summarize supplied evidence for a local task.\n---\n{text}\n".encode())

    def plan(self):
        return plan_change(self.candidate, self.runtime, self.journal)

    def install(self):
        plan = self.plan()
        return apply(plan, object_digest(plan))

    def test_install_rollback_and_reapply(self):
        result = self.install()
        self.assertEqual(snapshot(self.runtime / "example-skill"), snapshot(self.candidate))
        self.assertEqual(rollback(result["transaction"])["status"], "rolled_back")
        self.assertFalse((self.runtime / "example-skill").exists())
        self.assertEqual(self.install()["status"], "complete")

    def test_update_restores_original_bytes(self):
        self.install()
        before = snapshot(self.runtime / "example-skill")
        self.skill(self.candidate, "Changed instruction.")
        result = self.install()
        rollback(result["transaction"])
        self.assertEqual(snapshot(self.runtime / "example-skill"), before)

    def test_unchanged_is_noop(self):
        self.install()
        self.assertEqual(self.install()["status"], "no_change")

    def test_noop_still_refuses_runtime_drift(self):
        self.install()
        plan = self.plan()
        self.skill(self.runtime / "example-skill", "new user content")
        with self.assertRaises(LoomError):
            apply(plan, object_digest(plan))

    @unittest.skipIf(os.name == "nt", "POSIX execute bits are not supported by Windows")
    def test_executable_mode_survives_update_and_rollback(self):
        atomic_write(self.candidate / "run.sh", b"#!/bin/sh\nexit 0\n", mode=0o755)
        self.install()
        self.assertEqual((self.runtime / "example-skill/run.sh").stat().st_mode & 0o777, 0o755)
        atomic_write(self.candidate / "run.sh", b"#!/bin/sh\nexit 1\n", mode=0o744)
        result = self.install()
        self.assertEqual((self.runtime / "example-skill/run.sh").stat().st_mode & 0o777, 0o744)
        rollback(result["transaction"])
        self.assertEqual((self.runtime / "example-skill/run.sh").stat().st_mode & 0o777, 0o755)

    def test_modified_candidate_refused(self):
        plan = self.plan()
        self.skill(self.candidate, "Changed after review.")
        with self.assertRaises(LoomError):
            apply(plan, object_digest(plan))
        self.assertFalse((self.runtime / "example-skill").exists())

    def test_modified_runtime_refused(self):
        self.install()
        self.skill(self.candidate, "Candidate change.")
        plan = self.plan()
        self.skill(self.runtime / "example-skill", "Someone else's work.")
        with self.assertRaises(LoomError):
            apply(plan, object_digest(plan))

    def test_changed_review_digest_refused(self):
        plan = self.plan()
        with self.assertRaises(LoomError):
            apply(plan, "0" * 64)

    def test_inconsistent_change_list_refused(self):
        plan = self.plan()
        plan["changes"] = []
        with self.assertRaises(LoomError):
            apply(plan, object_digest(plan))

    def test_rollback_refuses_subsequent_edits(self):
        result = self.install()
        self.skill(self.runtime / "example-skill", "New user work.")
        with self.assertRaises(LoomError):
            rollback(result["transaction"])

    def test_rollback_refuses_unrelated_new_file(self):
        result = self.install()
        atomic_write(self.runtime / "example-skill" / "notes.txt", b"user notes")
        with self.assertRaises(LoomError):
            rollback(result["transaction"])

    def test_corrupt_backup_refused(self):
        self.install()
        self.skill(self.candidate, "New version.")
        result = self.install()
        atomic_write(Path(result["transaction"]) / "backup" / "SKILL.md", b"broken")
        with self.assertRaises(LoomError):
            rollback(result["transaction"])

    def test_retirement_is_reversible(self):
        self.install()
        plan = plan_change(None, self.runtime, self.journal, retire="example-skill")
        result = apply(plan, object_digest(plan))
        self.assertFalse((self.runtime / "example-skill").exists())
        rollback(result["transaction"])
        self.assertTrue((self.runtime / "example-skill" / "SKILL.md").exists())

    def test_apply_failure_keeps_recoverable_journal(self):
        self.install()
        self.skill(self.candidate, "New version.")
        atomic_write(self.candidate / "second.txt", b"new")
        plan = self.plan()
        import skillloom.transactions as tx
        original = tx.atomic_write
        def fail_one(path, data, **kwargs):
            if Path(path) == self.runtime / "example-skill" / "second.txt":
                raise OSError("simulated disk failure")
            return original(path, data, **kwargs)
        with patch.object(tx, "atomic_write", side_effect=fail_one):
            with self.assertRaises(OSError):
                apply(plan, object_digest(plan))
        records = list(self.journal.glob("*/transaction.json"))
        interrupted = next(p.parent for p in records if json.loads(p.read_text())["status"] == "interrupted")
        rollback(interrupted)
        self.assertEqual(snapshot(self.runtime / "example-skill"), plan["before"])

    def test_malformed_frontmatter_reported(self):
        atomic_write(self.candidate / "SKILL.md", b"---\nname: example-skill\ndescription: [not, text]\n---\n")
        self.assertGreater(inventory([self.candidate.parent])["error_count"], 0)

    def test_missing_reference_blocks_candidate(self):
        self.skill(self.candidate, "Read [missing](references/missing.md).")
        with self.assertRaises(LoomError):
            self.plan()

    def test_fenced_example_link_ignored(self):
        self.skill(self.candidate, "```md\n[example](missing.md)\n```\n")
        self.assertEqual(inventory([self.candidate.parent])["error_count"], 0)

    def test_broken_python_blocks_candidate(self):
        atomic_write(self.candidate / "bad.py", b"def broken(:\n")
        with self.assertRaises(LoomError):
            self.plan()

    def test_duplicate_discovery_name_reported(self):
        report = inventory([self.candidate.parent, self.candidate.parent])
        self.assertEqual(report["duplicate_names"], {"example-skill": 2})

    def test_link_mutation_refused(self):
        target = self.candidate / "external.txt"
        try:
            target.symlink_to(self.base / "elsewhere.txt")
        except OSError:
            self.skipTest("OS requires symlink privilege")
        with self.assertRaises(LoomError):
            self.plan()

    def test_public_stage_rejects_unpinned_ref(self):
        with self.assertRaises(LoomError):
            stage("owner/repo", "main", "skills/a", self.base / "stage")

    def test_public_stage_rejects_path_traversal(self):
        with self.assertRaises(LoomError):
            stage("owner/repo", "a" * 40, "../a", self.base / "stage")

    def source_tree(self):
        data = (self.candidate / "SKILL.md").read_bytes()
        sha = hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()
        return data, {"tree": [{"path": "skills/a/SKILL.md", "type": "blob", "mode": "100644", "sha": sha, "size": len(data)}]}

    def test_public_stage_accepts_matching_pinned_blob(self):
        data, tree = self.source_tree()
        with patch("skillloom.sources.api", return_value=tree), patch("skillloom.sources.download", return_value=data):
            result = stage("owner/repo", "a" * 40, "skills/a", self.base / "stage")
        self.assertEqual(result["status"], "staged")
        self.assertEqual((self.base / "stage/SKILL.md").read_bytes(), data)

    def test_public_stage_refuses_mismatched_or_missing_blob_identity(self):
        data, tree = self.source_tree()
        for invalid in (data + b"changed", data[:-1]):
            with self.subTest(download=invalid[-8:]):
                with patch("skillloom.sources.api", return_value=tree), patch("skillloom.sources.download", return_value=invalid):
                    with self.assertRaises(LoomError):
                        stage("owner/repo", "a" * 40, "skills/a", self.base / "stage")
                self.assertFalse((self.base / "stage").exists())
        tree["tree"][0].pop("sha")
        with patch("skillloom.sources.api", return_value=tree), patch("skillloom.sources.download", return_value=data):
            with self.assertRaises(LoomError):
                stage("owner/repo", "a" * 40, "skills/a", self.base / "stage")

    def test_public_stage_reserves_provenance_name_case_insensitively(self):
        for name in ("provenance.json", "Provenance.json", "PROVENANCE.JSON"):
            data, tree = self.source_tree()
            tree["tree"].append(dict(tree["tree"][0], path="skills/a/" + name))
            with self.subTest(name=name):
                with patch("skillloom.sources.api", return_value=tree), patch("skillloom.sources.download", return_value=data):
                    with self.assertRaises(LoomError):
                        stage("owner/repo", "a" * 40, "skills/a", self.base / "stage")
                self.assertFalse((self.base / "stage").exists())

    def test_discovery_reads_metadata_then_full_commit(self):
        from skillloom.sources import discover
        def response(url, limit=0):
            responses = {"https://api.github.com/repos/owner/repo": {"default_branch": "main"},
                         "https://api.github.com/repos/owner/repo/commits/main": {"sha": "a" * 40}}
            if url not in responses:
                raise OSError("Unrecognized GitHub endpoint")
            return json.dumps(responses[url]).encode()
        with patch("skillloom.sources.download", side_effect=response):
            report = discover({"sources": [{"repository": "owner/repo", "commit": "b" * 40}]})
        self.assertEqual(report["sources"][0]["candidate_commit"], "a" * 40)
        self.assertTrue(report["sources"][0]["changed"])

    def test_event_export_discards_private_fields(self):
        path = self.base / "events.jsonl"
        event = {"skill": "example-skill", "task_class": "maintenance", "outcome": "fail", "failure_code": "routing", "prompt": "PRIVATE", "tokens": 12}
        path.write_text(json.dumps(event), encoding="utf-8")
        report = summarize_events(path)
        self.assertEqual(report["discarded_fields"], 1)
        self.assertNotIn("PRIVATE", json.dumps(report))
        self.assertEqual(report["tokens_total"], 12)

    def test_absence_does_not_suggest_deletion(self):
        report = suggest(inventory([self.candidate.parent]), {"skills": {}})
        self.assertEqual(report["proposals"], [])

    def test_rollout_observation_does_not_export_text(self):
        path = self.base / "rollout.jsonl"
        path.write_text(json.dumps({"type": "response_item", "payload": {"type": "function_call", "arguments": "PRIVATE"}}), encoding="utf-8")
        report = observe_codex([path])
        self.assertEqual(report["counts"]["tool_calls"], 1)
        self.assertNotIn("PRIVATE", json.dumps(report))
        self.assertEqual(report["skill_attribution"], "not_inferred")

    def receipt(self):
        atomic_write(self.base / "evidence.txt", b"verified fixture")
        artifact = {"path": "evidence.txt", "sha256": digest(b"verified fixture")}
        receipt = self.base / "receipt.json"
        write_json(receipt, {"checks": [{"id": name, "status": "pass", "artifacts": [artifact]} for name in sorted(PROFILES["skill-change"])]})
        return receipt

    def test_gate_detects_stale_evidence(self):
        receipt = self.receipt()
        self.assertEqual(gate(receipt, "skill-change")["status"], "pass")
        atomic_write(self.base / "evidence.txt", b"changed")
        self.assertEqual(gate(receipt, "skill-change")["status"], "fail")

    def test_gate_refuses_nonfinite_or_nonpositive_evidence_age(self):
        receipt = self.receipt()
        for value in (float("nan"), float("inf"), -float("inf"), 0, -1, True):
            with self.subTest(value=value), self.assertRaises(LoomError):
                gate(receipt, "skill-change", max_age_hours=value)

    def test_stop_loop_has_one_repair_limit(self):
        receipt = self.receipt()
        atomic_write(self.base / "evidence.txt", b"changed")
        first, report = stop_decision(receipt, "skill-change", {})
        self.assertEqual(first["decision"], "block")
        second, report = stop_decision(receipt, "skill-change", {"stop_hook_active": True})
        self.assertIn("systemMessage", second)
        self.assertNotIn("decision", second)
        self.assertEqual(report["status"], "fail")

    def cache(self):
        root = self.base / "task-cache"
        write_json(root / MARKER, {"owner": "skill-loom", "reconstructible": True, "schema": 1})
        atomic_write(root / "render.tmp", b"rebuild me")
        return root

    def test_cleanup_removes_exact_reviewed_files(self):
        root = self.cache()
        plan = cleanup_plan(root, 0)
        report = cleanup_apply(plan, object_digest(plan), self.base / "cleanup-receipt.json")
        self.assertEqual(report["deleted_bytes"], len(b"rebuild me"))
        self.assertTrue((root / MARKER).exists())

    def test_cleanup_refuses_unowned_directory(self):
        with self.assertRaises((LoomError, OSError)):
            cleanup_plan(self.base, 0)

    def test_cleanup_refuses_nonfinite_age(self):
        root = self.cache()
        for value in (float("nan"), float("inf"), -float("inf")):
            with self.subTest(value=value), self.assertRaises(LoomError):
                cleanup_plan(root, value)
        self.assertTrue((root / "render.tmp").exists())

    def test_cleanup_refuses_changed_cache(self):
        root = self.cache()
        plan = cleanup_plan(root, 0)
        atomic_write(root / "render.tmp", b"new work")
        with self.assertRaises(LoomError):
            cleanup_apply(plan, object_digest(plan), self.base / "receipt.json")
        self.assertTrue((root / "render.tmp").exists())

    def test_offline_demo_closes_iteration(self):
        report = run_demo(self.base / "demo")
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["rollback_exact"])

    def test_cleanup_interruption_retains_pending_intent(self):
        import skillloom.cleanup as cleanup
        root = self.cache()
        plan = cleanup_plan(root, 0)
        receipt = self.base / "cleanup-receipt.json"
        original = cleanup.write_json
        def fail_after_unlink(path, value):
            if value.get("deleted_files"):
                raise OSError("simulated receipt write failure")
            original(path, value)
        with patch.object(cleanup, "write_json", side_effect=fail_after_unlink):
            with self.assertRaises(OSError):
                cleanup_apply(plan, object_digest(plan), receipt)
        self.assertFalse((root / "render.tmp").exists())
        self.assertEqual(json.loads(receipt.read_text())["pending_file"]["path"], "render.tmp")

    def test_strategy_rejects_string_capability_collection(self):
        from skillloom.strategy import portfolio
        profile = json.loads((Path(__file__).resolve().parents[1] / "examples/user-profile.json").read_text())
        with self.assertRaises(LoomError):
            portfolio(profile, {"skills": [{"name": "invalid", "capabilities": "source-notes"}]})

    def test_rank_blank_evidence_does_not_count(self):
        from skillloom.strategy import rank
        profile = json.loads((Path(__file__).resolve().parents[1] / "examples/user-profile.json").read_text())
        result = rank(profile, {"candidates": [{"id": "blank", "ratings": {"task_fit": 4}, "evidence_refs": {"task_fit": "   "}, "capabilities": ["source-notes"]}]})
        self.assertEqual(result["ranked"][0]["queue_score"], 0)

    def test_gate_rejects_wrong_run_and_missing_timestamp(self):
        receipt = self.receipt()
        result = gate(receipt, "skill-change", expected_run="new-run", expected_candidate="a" * 64, max_age_hours=24)
        self.assertEqual(result["status"], "fail")
        self.assertEqual(len(result["failures"]), 3)

    def test_profile_rank_requires_evidence_for_ratings(self):
        from skillloom.strategy import rank
        profile = json.loads((Path(__file__).resolve().parents[1] / "examples/user-profile.json").read_text())
        result = rank(profile, {"candidates": [{"id": "unproven", "ratings": {"task_fit": 4}, "capabilities": ["source-notes"]}]})
        self.assertEqual(result["ranked"][0]["queue_score"], 0)
        self.assertTrue(result["ranked"][0]["adoption_blockers"])

    def test_gap_environment_failure_is_not_new_skill_request(self):
        from skillloom.strategy import gap_analysis
        profile = json.loads((Path(__file__).resolve().parents[1] / "examples/user-profile.json").read_text())
        result = gap_analysis(profile, {"skills": []}, {"tasks": [{"required_capabilities": ["source-notes"], "outcome": "fail", "cause": "environment", "evidence_ref": "case1"}]})
        item = next(x for x in result["gaps"] if x["capability"] == "source-notes")
        self.assertEqual(item["next_action"], "repair-environment-first")


if __name__ == "__main__":
    unittest.main()
