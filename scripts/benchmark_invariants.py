"""Deterministic fault-injection study; does not evaluate an LLM or a real service.

Comparators are deliberately simple reference implementations, not existing skill
managers. Every case uses an isolated TemporaryDirectory. No network is used.
"""

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import shutil
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from skillloom.common import LoomError, atomic_write, digest, now, object_digest, write_json
from skillloom.gates import gate
from skillloom.inventory import inspect_skill
from skillloom.transactions import apply, plan_change, rollback


def make_skill(path, body="Use supplied evidence."):
    atomic_write(path / "SKILL.md", ("---\nname: example\ndescription: Summarize supplied source material.\n---\n" + body + "\n").encode())


def mutation_case(case, method):
    with tempfile.TemporaryDirectory(prefix="skillloom-benchmark-") as temporary:
        base = Path(temporary).resolve()
        candidate, runtime, journal = base / "candidate/example", base / "runtime", base / "journal"
        make_skill(candidate)
        target = runtime / "example"
        make_skill(target, "Original instruction.")
        before = (target / "SKILL.md").read_bytes()
        if case == "missing-reference":
            make_skill(candidate, "Read [evidence](missing.md).")
        if case == "syntax-error":
            atomic_write(candidate / "broken.py", b"def invalid(:\n")
        try:
            plan = plan_change(candidate, runtime, journal) if method == "guarded" else None
            if case == "candidate-drift":
                make_skill(candidate, "Unreviewed candidate edit.")
            if case == "runtime-drift":
                make_skill(target, "Subsequent user work.")
            if case == "new-local-file":
                atomic_write(target / "user.txt", b"new user work")
            if method == "static-only" and inspect_skill(candidate)["errors"]:
                return "refused"
            if method == "guarded":
                result = apply(plan, object_digest(plan))
            else:
                shutil.copytree(candidate, target, dirs_exist_ok=True)
                result = None
            if case == "rollback-drift":
                make_skill(target, "User work after installation.")
                if method == "guarded":
                    rollback(result["transaction"])
                else:
                    atomic_write(target / "SKILL.md", before)
            if case == "corrupt-backup":
                if method == "guarded":
                    atomic_write(Path(result["transaction"]) / "backup/SKILL.md", b"corrupt")
                    rollback(result["transaction"])
                else:
                    atomic_write(target / "SKILL.md", b"corrupt")
            return "applied"
        except LoomError:
            return "refused"


def receipt_case(case, method):
    with tempfile.TemporaryDirectory(prefix="skillloom-receipt-") as temporary:
        base = Path(temporary).resolve()
        evidence = base / "evidence.txt"
        atomic_write(evidence, b"verified fixture")
        receipt = {"schema": 1, "profile": "documents", "run_id": "run-a", "candidate_digest": "a" * 64,
                   "created_at": now(), "checks": [{"id": key, "status": "pass", "artifacts": [{"path": "evidence.txt", "sha256": digest(evidence.read_bytes())}]} for key in ["scope", "fidelity", "render"]]}
        if case == "stale-artifact":
            atomic_write(evidence, b"changed fixture")
        if case == "expired-receipt":
            receipt["created_at"] = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        write_json(base / "receipt.json", receipt)
        if method == "declaration-only":
            return "accepted" if all(x["status"] == "pass" for x in receipt["checks"]) else "refused"
        run = "run-b" if case == "replayed-receipt" else "run-a"
        checked = gate(base / "receipt.json", "documents", expected_run=run, expected_candidate="a" * 64, max_age_hours=24)
        return "accepted" if checked["status"] == "pass" else "refused"


def benchmark():
    rows = []
    mutation_cases = ["clean-update", "missing-reference", "syntax-error", "candidate-drift", "runtime-drift", "new-local-file", "rollback-drift", "corrupt-backup"]
    for case in mutation_cases:
        expected = "applied" if case == "clean-update" else "refused"
        for method in ["unchecked-copy", "static-only", "guarded"]:
            observed = mutation_case(case, method)
            rows.append({"family": "mutation", "case": case, "method": method, "expected": expected, "observed": observed, "contract_satisfied": observed == expected})
    for case in ["valid-receipt", "stale-artifact", "replayed-receipt", "expired-receipt"]:
        expected = "accepted" if case == "valid-receipt" else "refused"
        for method in ["declaration-only", "bound-receipt"]:
            observed = receipt_case(case, method)
            rows.append({"family": "receipt", "case": case, "method": method, "expected": expected, "observed": observed, "contract_satisfied": observed == expected})
    summary = {}
    for row in rows:
        stats = summary.setdefault(row["method"], {"satisfied": 0, "cases": 0})
        stats["cases"] += 1
        stats["satisfied"] += row["contract_satisfied"]
    return {"schema": 1, "observed_at": now(), "study": "deterministic-fault-injection", "rows": rows, "summary": summary,
            "independent_units": "12 deliberately constructed scenarios; repeat runs are not independent statistical samples",
            "limits": "Hand-selected software contracts with simple comparator implementations, not agent-task accuracy, global safety, deployment readiness or comparisons to published skill systems."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    report = benchmark()
    write_json(args.out, report)
    print(json.dumps(report["summary"], indent=2))
    return 0 if all(row["contract_satisfied"] for row in report["rows"] if row["method"] in {"guarded", "bound-receipt"}) else 1


if __name__ == "__main__":
    raise SystemExit(main())
