"""Small, explicit event vocabulary; no prompts, output bodies, or user paths."""

from collections import Counter, defaultdict
import json
from pathlib import Path

from .common import LoomError, now, valid_name

OUTCOMES = {"pass", "fail", "unverified"}
TASKS = {"research", "production", "documents", "maintenance", "other"}
FAILURES = {"none", "routing", "missing-resource", "environment", "factuality", "validation", "scope", "other"}
FIELDS = {"skill", "task_class", "outcome", "failure_code", "duration_ms", "tokens"}


def summarize_events(path):
    counts = Counter()
    skills = defaultdict(Counter)
    removed_fields = 0
    durations, tokens = [], []
    for index, line in enumerate(Path(path).read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        event = json.loads(line)
        if not isinstance(event, dict):
            raise LoomError(f"Event {index} must be an object")
        skill = event.get("skill")
        if not valid_name(skill) or event.get("outcome") not in OUTCOMES or event.get("task_class") not in TASKS:
            raise LoomError(f"Event {index} does not match the bounded event vocabulary")
        failure = event.get("failure_code", "none")
        if failure not in FAILURES:
            raise LoomError(f"Event {index} has an unsupported failure code")
        removed_fields += len(set(event) - FIELDS)
        counts[event["outcome"]] += 1
        skills[skill][event["outcome"]] += 1
        if event["outcome"] == "fail":
            skills[skill]["failure:" + failure] += 1
        for key, values in (("duration_ms", durations), ("tokens", tokens)):
            if key in event:
                if type(event[key]) is not int or not 0 <= event[key] <= 10**12:
                    raise LoomError(f"Event {index}: invalid measurement")
                values.append(event[key])
    return {"schema": 1, "observed_at": now(), "event_count": sum(counts.values()),
            "outcomes": dict(counts), "skills": {k: dict(v) for k, v in sorted(skills.items())},
            "discarded_fields": removed_fields, "duration_ms_total": sum(durations) if durations else None,
            "tokens_total": sum(tokens) if tokens else None,
            "limits": "Curated observations, not causal evidence. Unobserved skills are not candidates for automatic removal."}


def observe_codex(paths):
    """Read explicit rollout files; export only structural counts and token totals.

    Deliberately do not infer skill usage or task success from text matches.
    Never include input filenames, prompts, commands, tool outputs, or identities.
    """
    counts = Counter()
    usage = []
    for path in paths:
        latest = None
        with Path(path).open(encoding="utf-8-sig") as handle:
            for line in handle:
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    counts["malformed_lines"] += 1
                    continue
                if not isinstance(item, dict):
                    continue
                payload = item.get("payload")
                if not isinstance(payload, dict):
                    continue
                kind = item.get("type")
                if kind == "response_item" and payload.get("type") in {"function_call", "custom_tool_call"}:
                    counts["tool_calls"] += 1
                if kind == "event_msg" and payload.get("type") in {"task_started", "task_complete", "turn_aborted"}:
                    counts[payload["type"]] += 1
                if kind == "event_msg" and payload.get("type") == "token_count":
                    info = payload.get("info") or {}
                    total = info.get("total_token_usage", {}) if isinstance(info, dict) else {}
                    value = total.get("total_tokens") if isinstance(total, dict) else None
                    if type(value) is int and value >= 0:
                        latest = value
        if latest is not None:
            usage.append(latest)
    return {"schema": 1, "observed_at": now(), "file_count": len(paths), "counts": dict(counts),
            "reported_total_tokens_sum": sum(usage) if usage else None,
            "files_with_usage": len(usage), "skill_attribution": "not_inferred",
            "limits": "Structural local sample; task_complete is a host event, not proof of quality. No raw content exported."}


def suggest(inventory_report, event_report, minimum_failures=2):
    if minimum_failures < 1:
        raise LoomError("minimum_failures must be positive")
    proposals = []
    for skill in inventory_report["skills"]:
        if skill["errors"]:
            proposals.append({"skill": skill["name"], "action": "repair", "basis": "static-failure",
                              "acceptance": "Static errors cleared plus one relevant positive and one negative task"})
    for skill, counts in event_report.get("skills", {}).items():
        if counts.get("fail", 0) >= minimum_failures:
            proposals.append({"skill": skill, "action": "investigate", "basis": "repeated-curated-failures",
                              "acceptance": "Reproduce incident, identify skill/tool/environment cause, compare a held-out task"})
    return {"schema": 1, "proposals": proposals, "automatic_mutation": False,
            "limits": "Failure frequency prioritizes investigation. It does not justify installing, deleting, or rewriting a skill by itself."}
