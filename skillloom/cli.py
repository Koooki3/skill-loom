"""Command-line surface. Read-only unless an explicit mutation command is used."""

import argparse
import json
from pathlib import Path
import sys

from . import __version__
from .common import LoomError, object_digest, read_json, write_json


def parser():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--version", action="version", version=__version__)
    sub = cli.add_subparsers(dest="command", required=True)
    p = sub.add_parser("inventory", help="Inspect metadata, links and Python syntax; execute nothing")
    p.add_argument("--root", action="append", required=True)
    p.add_argument("--out", required=True)
    p = sub.add_parser("discover", help="Observe public source HEADs; install nothing")
    p.add_argument("--registry", required=True)
    p.add_argument("--out", required=True)
    p = sub.add_parser("scout", help="Search public repositories with explicit non-private queries")
    p.add_argument("--query", action="append", required=True)
    p.add_argument("--per-query", type=int, default=10)
    p.add_argument("--out", required=True)
    p = sub.add_parser("doctor", help="Check a user profile and local executable presence")
    p.add_argument("--profile", required=True)
    p.add_argument("--out", required=True)
    p = sub.add_parser("rank", help="Rank evidence-graded candidates for this user; never install")
    p.add_argument("--profile", required=True)
    p.add_argument("--candidates", required=True)
    p.add_argument("--out", required=True)
    p = sub.add_parser("gaps", help="Compare explicit task needs, available capabilities and observations")
    p.add_argument("--profile", required=True)
    p.add_argument("--catalog", required=True)
    p.add_argument("--observations", required=True)
    p.add_argument("--out", required=True)
    p = sub.add_parser("portfolio", help="Flag capability overlap and user-defined budget excess")
    p.add_argument("--profile", required=True)
    p.add_argument("--catalog", required=True)
    p.add_argument("--out", required=True)
    p = sub.add_parser("stage", help="Download a pinned skill into a NEW staging directory")
    for name in ("repo", "commit", "path", "destination"):
        p.add_argument("--" + name, required=True)
    p = sub.add_parser("events", help="Summarize manually curated events using a bounded vocabulary")
    p.add_argument("--input", required=True)
    p.add_argument("--out", required=True)
    p = sub.add_parser("observe-codex", help="Aggregate explicitly selected local rollouts; export no text")
    p.add_argument("--log", action="append", required=True)
    p.add_argument("--out", required=True)
    p = sub.add_parser("suggest", help="Suggest investigation candidates, never edits")
    p.add_argument("--inventory", required=True)
    p.add_argument("--events", required=True)
    p.add_argument("--minimum-failures", type=int, default=2)
    p.add_argument("--out", required=True)
    p = sub.add_parser("plan", help="Create a reviewed single-skill install/update/retirement plan")
    choice = p.add_mutually_exclusive_group(required=True)
    choice.add_argument("--candidate")
    choice.add_argument("--retire")
    for name in ("root", "journal", "out"):
        p.add_argument("--" + name, required=True)
    p = sub.add_parser("apply", help="Apply an exact reviewed plan and retain rollback files")
    p.add_argument("--plan", required=True)
    p.add_argument("--digest", required=True)
    p = sub.add_parser("rollback", help="Restore only this transaction; fail on subsequent drift")
    p.add_argument("--transaction", required=True)
    p = sub.add_parser("gate", help="Check required receipt evidence and artifact hashes")
    p.add_argument("--receipt", required=True)
    p.add_argument("--profile", choices=["skill-change", "research", "production", "documents"], required=True)
    p.add_argument("--expected-run-id")
    p.add_argument("--expected-candidate-digest")
    p.add_argument("--max-age-hours", type=float)
    p.add_argument("--out")
    p = sub.add_parser("cleanup-plan", help="Inventory old files in an explicitly owned reconstructible cache")
    p.add_argument("--root", required=True)
    p.add_argument("--age-days", type=float, default=14)
    p.add_argument("--out", required=True)
    p = sub.add_parser("cleanup-apply", help="Delete only unchanged exact files in a reviewed cache plan")
    for name in ("plan", "digest", "receipt"):
        p.add_argument("--" + name, required=True)
    p = sub.add_parser("demo", help="Run an isolated offline self-evolution/rollback fixture")
    p.add_argument("--workdir", required=True)
    return cli


def dispatch(args):
    command = args.command
    if command == "inventory":
        from .inventory import inventory
        result = inventory(args.root)
    elif command == "discover":
        from .sources import discover
        result = discover(read_json(args.registry))
    elif command == "scout":
        from .sources import scout
        result = scout(args.query, args.per_query)
    elif command == "doctor":
        from .strategy import doctor
        result = doctor(read_json(args.profile))
    elif command == "rank":
        from .strategy import rank
        result = rank(read_json(args.profile), read_json(args.candidates))
    elif command == "gaps":
        from .strategy import gap_analysis
        result = gap_analysis(read_json(args.profile), read_json(args.catalog), read_json(args.observations))
    elif command == "portfolio":
        from .strategy import portfolio
        result = portfolio(read_json(args.profile), read_json(args.catalog))
    elif command == "stage":
        from .sources import stage
        result = stage(args.repo, args.commit, args.path, args.destination)
    elif command == "events":
        from .evidence import summarize_events
        result = summarize_events(args.input)
    elif command == "observe-codex":
        from .evidence import observe_codex
        result = observe_codex(args.log)
    elif command == "suggest":
        from .evidence import suggest
        result = suggest(read_json(args.inventory), read_json(args.events), args.minimum_failures)
    elif command == "plan":
        from .transactions import plan_change
        result = plan_change(args.candidate, args.root, args.journal, args.retire)
    elif command == "apply":
        from .transactions import apply
        result = apply(read_json(args.plan), args.digest)
    elif command == "rollback":
        from .transactions import rollback
        result = rollback(args.transaction)
    elif command == "gate":
        from .gates import gate
        result = gate(args.receipt, args.profile, args.expected_run_id, args.expected_candidate_digest, args.max_age_hours)
    elif command == "cleanup-plan":
        from .cleanup import cleanup_plan
        result = cleanup_plan(args.root, args.age_days)
    elif command == "cleanup-apply":
        from .cleanup import cleanup_apply
        result = cleanup_apply(read_json(args.plan), args.digest, args.receipt)
    elif command == "demo":
        from .demo import run_demo
        result = run_demo(args.workdir)
    else:
        raise LoomError("Unknown command")
    if getattr(args, "out", None):
        write_json(args.out, result)
    display = {k: v for k, v in result.items() if k not in {"skills", "before", "after", "changes", "provenance", "files", "deleted_files"}}
    if command in {"plan", "cleanup-plan"}:
        display["review_digest"] = object_digest(result)
    print(json.dumps(display, ensure_ascii=False, indent=2))
    unavailable = any(source.get("status") == "unavailable" for source in result.get("sources", [])) or bool(result.get("unavailable"))
    return 1 if result.get("error_count", 0) or result.get("status") == "fail" or unavailable else 0


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        return dispatch(args)
    except (LoomError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "error", "error_type": type(exc).__name__, "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
