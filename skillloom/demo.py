"""Offline evidence -> candidate -> apply -> rollback -> reapply drill."""

from pathlib import Path
from .common import LoomError, atomic_write, object_digest, snapshot, write_json
from .evidence import suggest
from .inventory import inventory
from .transactions import apply, plan_change, rollback


def run_demo(workdir):
    root = Path(workdir).resolve()
    if root.exists():
        raise LoomError("Demo needs a new directory; it never deletes an old run")
    active = root / "runtime"
    candidate = root / "candidate" / "source-notes"
    old = b"---\nname: source-notes\ndescription: Summarize supplied course pages with page evidence.\n---\nRead [evidence](references/evidence.md).\n"
    atomic_write(active / "source-notes" / "SKILL.md", old)
    baseline = inventory([active])
    initial = snapshot(active / "source-notes")
    events = {"skills": {"source-notes": {"fail": 2, "failure:missing-resource": 2}}}
    proposals = suggest(baseline, events)
    atomic_write(candidate / "SKILL.md", old)
    atomic_write(candidate / "references" / "evidence.md", b"Use supplied source pages. Mark missing evidence rather than inventing a citation.\n")
    fixed = inventory([candidate.parent])
    plan = plan_change(candidate, active, root / "journal")
    write_json(root / "plan.json", plan)
    first = apply(plan, object_digest(plan))
    installed = inventory([active])
    rollback_result = rollback(first["transaction"])
    restored = snapshot(active / "source-notes") == initial
    second = apply(plan, object_digest(plan))
    no_change_plan = plan_change(candidate, active, root / "journal")
    noop = apply(no_change_plan, object_digest(no_change_plan))
    passed = baseline["error_count"] > 0 and fixed["error_count"] == 0 and installed["error_count"] == 0 and restored and noop["status"] == "no_change"
    report = {"schema": 1, "fixture": True, "status": "pass" if passed else "fail",
              "baseline_errors": baseline["error_count"], "candidate_errors": fixed["error_count"],
              "installed_errors": installed["error_count"], "proposal_count": len(proposals["proposals"]),
              "rollback_exact": restored, "rollback_status": rollback_result["status"],
              "reapply_status": second["status"], "idempotent_status": noop["status"],
              "limits": "Deterministic missing-reference fixture, not an LLM task-quality or token-savings benchmark."}
    write_json(root / "report.json", report)
    return report
