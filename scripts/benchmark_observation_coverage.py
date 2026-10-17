
"""Synthetic replay/coverage study. No model, network, or real transcript is used.

Run against the current checkout, or an explicitly reviewed older source tree:
python scripts/benchmark_observation_coverage.py --source-root <checkout> --out <new-report.json>
The output is replaced only at the explicit --out destination. Exit 1 means a
declared contract was not met; this is expected for the documented baseline.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parents[1])
parser.add_argument("--out", type=Path, required=True)
args = parser.parse_args()
source = args.source_root.resolve(strict=True)
sys.path.insert(0, str(source))
from skillloom.evidence import observe_claude, observe_codex
from skillloom.usage import usage_report


def observation(host, files, first="2026-10-01", last="2026-10-07", used=False):
    return {"host": host, "file_count": files, "window": {"first_day": first, "last_day": last},
            "skills" if host == "claude" else "skill_md_reads":
                {"used": {"calls": 1, "sessions": 1}} if used else {}}


def assess(host, name, observations, expected_sufficient, expected_candidates):
    inventory = {"skills": [{"name": n, "description_chars": 100} for n in ("used", "rare")]}
    result = usage_report({host: inventory}, observations)["hosts"][0]
    actual = {"window_sufficient": result["window_sufficient"],
              "review_candidates": sorted(row["skill"] for row in result["review_candidates"])}
    expected = {"window_sufficient": expected_sufficient, "review_candidates": sorted(expected_candidates)}
    return {"case": host + "-" + name, "expected": expected, "actual": actual,
            "observed_files": result["observed_files"], "span_days": result["span_days"],
            "contract_met": actual == expected}


rows = []
for host, observer in (("claude", observe_claude), ("codex", observe_codex)):
    under = observation(host, 6)
    rows.append(assess(host, "single-under-threshold", [under], False, []))
    rows.append(assess(host, "duplicate-aggregate", [under, dict(under)], False, []))
    crossed = [observation(host, 10, last="2026-10-01"),
               observation(host, 1, last="2026-10-08")]
    rows.append(assess(host, "crossed-thresholds", crossed, False, []))
    rows.append(assess(host, "qualifying-control", [observation(host, 10, used=True)], True, ["rare"]))
    rows.append(assess(host, "positive-small-report", [observation(host, 10),
                       observation(host, 1, first="2026-10-08", last="2026-10-08", used=True)], True, ["rare"]))
    with tempfile.TemporaryDirectory(prefix="loom-observation-study-") as tmp:
        path = Path(tmp) / "synthetic.jsonl"
        events = []
        for day in ("2026-10-01", "2026-10-07"):
            if host == "codex":
                event = {"timestamp": day + "T00:00:00Z", "type": "response_item",
                         "payload": {"type": "function_call", "arguments": "read skills/used/SKILL.md"}}
            else:
                event = {"timestamp": day + "T00:00:00Z", "type": "assistant",
                         "message": {"content": [{"type": "tool_use", "name": "Skill", "input": {"skill": "used"}}]}}
            events.append(json.dumps(event))
        path.write_text("\n".join(events), encoding="utf8")
        rows.append(assess(host, "repeated-input", [observer([path] * 10)], False, []))

result = {"schema": 1, "study": "synthetic-observation-coverage", "case_count": len(rows),
          "contracts_met": sum(row["contract_met"] for row in rows), "cases": rows,
          "source_sha256": {rel: hashlib.sha256((source / rel).read_bytes()).hexdigest()
                            for rel in ("skillloom/evidence.py", "skillloom/usage.py")},
          "limits": "Development-selected contract fixtures, not held-out trials or model-quality evidence. "
                    "File aliases are tested separately in the unit suite. Copied or overlapping logical sessions "
                    "inside different files are not deduplicated. Thresholds are review policy, not confidence bounds."}
args.out.parent.mkdir(parents=True, exist_ok=True)
args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf8")
print(json.dumps({"case_count": result["case_count"], "contracts_met": result["contracts_met"]}))
raise SystemExit(0 if result["contracts_met"] == result["case_count"] else 1)
