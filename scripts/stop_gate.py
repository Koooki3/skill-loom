"""Opt-in Stop hook example for verified command-hook hosts. One repair only.

The receipt path is explicitly configured by the user, never selected by stdin.
Malformed input/faults terminate with an error instead of creating a retry loop.
"""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from skillloom.gates import stop_decision


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--profile", default="skill-change")
    parser.add_argument("--expected-run-id", required=True)
    parser.add_argument("--expected-candidate-digest", required=True)
    parser.add_argument("--max-age-hours", type=float, default=24)
    args = parser.parse_args()
    try:
        raw = sys.stdin.read(65537)
        if len(raw) > 65536:
            raise ValueError("Oversized hook input")
        event = json.loads(raw)
        if not isinstance(event, dict):
            raise ValueError("Hook input must be an object")
        decision, report = stop_decision(args.receipt, args.profile, event,
                                         expected_run=args.expected_run_id,
                                         expected_candidate=args.expected_candidate_digest,
                                         max_age_hours=args.max_age_hours)
        print(json.dumps(decision))
        if report["status"] != "pass":
            print("Skill Loom: acceptance remains incomplete; do not claim completion.", file=sys.stderr)
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"systemMessage": "Skill Loom: gate unavailable. Report acceptance as unverified; do not claim a pass."}))
        print(f"Skill Loom hook unavailable: {type(exc).__name__}; report unverified acceptance.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
