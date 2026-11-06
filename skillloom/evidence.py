"""Small, explicit event vocabulary; no prompts, output bodies, or user paths."""

from collections import Counter, defaultdict
from datetime import date, datetime, timezone
import json
from pathlib import Path
import re

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


SKILL_MD_READ = re.compile(r"skills[\\/]+([a-z0-9]+(?:-[a-z0-9]+)*)[\\/]+SKILL\.md")
SKILL_REF = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*(?::[a-z0-9]+(?:-[a-z0-9]+)*)?")
AGENT_TYPE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,39}")


def _timestamp(stamp):
    """Parse the same bounded, aware timestamp syntax on Python 3.10 and newer."""
    if not isinstance(stamp, str) or not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})", stamp):
        return None
    try:
        return datetime.fromisoformat(stamp.replace("Z", "+00:00")).astimezone(timezone.utc)
    except (ValueError, OverflowError):
        return None


class _RecordSelection:
    """Optional temporal selection, separate from host interpretation and outcomes."""
    def __init__(self, since, until):
        self.active = since is not None or until is not None
        self.since, self.until = _timestamp(since), _timestamp(until)
        if (since is not None and self.since is None) or (until is not None and self.until is None):
            raise LoomError("Observation bounds require YYYY-MM-DDTHH:MM:SS[.ffffff]Z or an explicit +/-HH:MM offset")
        if self.since is not None and self.until is not None and self.since >= self.until:
            raise LoomError("Observation since must be earlier than until")
        self.files = set()
        self.matched = self.excluded = self.untimed = 0

    def accepts(self, item, index):
        if not self.active:
            return True
        stamp = _timestamp(item.get("timestamp"))
        if stamp is None:
            self.untimed += 1
            return False
        if (self.since is not None and stamp <= self.since) or (self.until is not None and stamp > self.until):
            self.excluded += 1
            return False
        self.files.add(index)
        self.matched += 1
        return True

    def day(self, stamp):
        return _timestamp(stamp).date() if self.active else _day(stamp)

    def fields(self, selected_files):
        if not self.active:
            return {}
        iso = lambda value: value.isoformat().replace("+00:00", "Z") if value else None
        return {"record_selection": {
            "since_exclusive": iso(self.since), "until_inclusive": iso(self.until),
            "selected_file_count": selected_files, "matching_records": self.matched,
            "outside_window_records": self.excluded, "untimed_records_skipped": self.untimed,
            "day_basis": "UTC", "token_totals": "not_computed_for_filtered_window",
            "limits": "Full input scan, not a byte cursor or continuous-capture claim. "
                      "Only timestamped JSON objects can match; malformed-line counts cover the whole scan. "
                      "file_count includes only distinct input files with at least one matching object. "
                      "Cumulative host token counters are not interval costs."}}


def _day(stamp):
    """Calendar day of an ISO timestamp, or None; times of day and zones are not kept."""
    try:
        return date.fromisoformat(stamp[:10]) if isinstance(stamp, str) else None
    except ValueError:
        return None


def _window(days):
    days = sorted(days)
    if not days:
        return {"first_day": None, "last_day": None, "span_days": 0}
    return {"first_day": days[0].isoformat(), "last_day": days[-1].isoformat(),
            "span_days": (days[-1] - days[0]).days + 1}


def _skill_table(calls, sessions):
    return {name: {"calls": calls[name], "sessions": len(sessions[name])} for name in sorted(calls)}


def _distinct_inputs(paths):
    """Deduplicate selected filesystem objects locally; export no path or identity."""
    selected = list(map(Path, paths))
    unique, seen = [], set()
    for path in selected:
        resolved = path.resolve(strict=True)
        stat = resolved.stat()
        identity = ("inode", stat.st_dev, stat.st_ino) if stat.st_ino else ("path", resolved)
        if identity not in seen:
            unique.append(resolved)
            seen.add(identity)
    return unique, len(selected) - len(unique)


def observe_codex(paths, *, since=None, until=None):
    """Read explicit rollout files; export only structural counts and token totals.

    Deliberately do not infer skill usage or task success from text matches.
    Never include input filenames, prompts, commands, tool outputs, or identities.
    """
    selection = _RecordSelection(since, until)
    paths, skipped = _distinct_inputs(paths)
    counts = Counter()
    usage = []
    reads, read_sessions, days = Counter(), defaultdict(set), set()
    for index, path in enumerate(paths):
        latest = None
        with Path(path).open(encoding="utf-8-sig") as handle:
            for line in handle:
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    counts["malformed_lines"] += 1
                    continue
                if not isinstance(item, dict) or not selection.accepts(item, index):
                    continue
                payload = item.get("payload")
                if not isinstance(payload, dict):
                    continue
                kind = item.get("type")
                day = selection.day(item.get("timestamp"))
                if day:
                    days.add(day)
                if kind == "response_item" and payload.get("type") in {"function_call", "custom_tool_call"}:
                    counts["tool_calls"] += 1
                    # These are syntactic path references in tool payloads, including quoted
                    # code and failed commands. They do not verify file access or skill use.
                    for name in set(SKILL_MD_READ.findall(json.dumps(payload, ensure_ascii=False))):
                        reads[name] += 1
                        read_sessions[name].add(index)
                if kind == "event_msg" and payload.get("type") in {"task_started", "task_complete", "turn_aborted"}:
                    counts[payload["type"]] += 1
                if not selection.active and kind == "event_msg" and payload.get("type") == "token_count":
                    info = payload.get("info") or {}
                    total = info.get("total_token_usage", {}) if isinstance(info, dict) else {}
                    value = total.get("total_tokens") if isinstance(total, dict) else None
                    if type(value) is int and value >= 0:
                        latest = value
        if latest is not None:
            usage.append(latest)
    return {"schema": 1, "host": "codex", "observed_at": now(), "file_count": len(selection.files) if selection.active else len(paths),
            "duplicate_inputs_skipped": skipped, "counting_unit": "distinct-filesystem-objects",
            "counts": dict(counts), **selection.fields(len(paths)),
            "reported_total_tokens_sum": sum(usage) if usage else None,
            "files_with_usage": len(usage), "skill_attribution": "not_inferred",
            "skill_signal_basis": "syntactic-tool-payload-path-reference",
            "skill_md_reads": _skill_table(reads, read_sessions), "window": _window(days),
            "limits": "Structural local sample; task_complete is a host event, not proof of quality. "
                      "skill_md_reads is a legacy name for syntactic SKILL.md path references in tool payloads. "
                      "This legacy load signal can match quoted code, audit text and failed commands; file access, skill use and success "
                      "are not verified. sessions counts input files containing a signal, "
                      "not verified logical sessions. Distinct files may contain copied or overlapping events. "
                      "Date endpoints describe elapsed span, not continuous capture. No raw content exported."}


def observe_claude(paths, *, since=None, until=None):
    """Aggregate explicitly selected Claude Code transcripts into structural counts.

    A Skill tool call is a structured host event, so skill attribution here is exact for
    calls and says nothing about success. Prompts, tool inputs, outputs and paths are never exported.
    """
    selection = _RecordSelection(since, until)
    paths, skipped = _distinct_inputs(paths)
    counts, agents = Counter(), Counter()
    calls, call_sessions, days = Counter(), defaultdict(set), set()
    for index, path in enumerate(paths):
        with Path(path).open(encoding="utf-8-sig") as handle:
            for line in handle:
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    counts["malformed_lines"] += 1
                    continue
                if not isinstance(item, dict) or not selection.accepts(item, index):
                    continue
                day = selection.day(item.get("timestamp"))
                if day:
                    days.add(day)
                message = item.get("message")
                content = message.get("content") if isinstance(message, dict) else None
                if item.get("type") == "user" and (isinstance(content, str) or (
                        isinstance(content, list) and any(isinstance(b, dict) and b.get("type") == "text" for b in content))):
                    counts["user_turns"] += 1
                if item.get("type") != "assistant" or not isinstance(content, list):
                    continue
                for block in content:
                    if not isinstance(block, dict) or block.get("type") != "tool_use":
                        continue
                    counts["tool_calls"] += 1
                    arguments = block.get("input") if isinstance(block.get("input"), dict) else {}
                    if block.get("name") == "Skill":
                        name = arguments.get("skill")
                        if isinstance(name, str) and SKILL_REF.fullmatch(name):
                            calls[name] += 1
                            call_sessions[name].add(index)
                        else:
                            counts["skill_calls_unnamed"] += 1
                    elif block.get("name") == "Agent":
                        kind = arguments.get("subagent_type", "default")
                        agents[kind if isinstance(kind, str) and AGENT_TYPE.fullmatch(kind) else "other"] += 1
    return {"schema": 1, "host": "claude", "observed_at": now(), "file_count": len(selection.files) if selection.active else len(paths),
            "duplicate_inputs_skipped": skipped, "counting_unit": "distinct-filesystem-objects",
            "counts": dict(counts), **selection.fields(len(paths)),
            "skill_attribution": "tool_use:Skill", "skills": _skill_table(calls, call_sessions),
            "subagent_dispatches": dict(sorted(agents.items())), "window": _window(days),
            "limits": "Structural local sample. A Skill call shows the skill was loaded, not that the task passed. "
                      "sessions counts input files containing a signal, not verified logical sessions. Distinct files "
                      "may contain copied or overlapping events. Date endpoints describe elapsed span, not "
                      "continuous capture. No raw content, paths or identities exported."}


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
