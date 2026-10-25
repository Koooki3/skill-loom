"""Per-host skill usage evidence. Proposes review candidates; never edits a skill system."""

from datetime import date

from .common import LoomError, now

# Review policy, not a statistical confidence bound or evidence of skill uselessness.
DEFAULT_MIN_FILES = 10
DEFAULT_MIN_SESSIONS = DEFAULT_MIN_FILES  # Legacy API name; this counts input files.
DEFAULT_MIN_DAYS = 7


def _count(value, field):
    if type(value) is not int or value < 0:
        raise LoomError(f"{field} must be a nonnegative integer")


def _validate_reports(inventories, observations):
    if not isinstance(inventories, dict) or not inventories:
        raise LoomError("Provide a nonempty object of host inventories")
    if not isinstance(observations, (list, tuple)):
        raise LoomError("Observation reports must be a list")
    for host, report in inventories.items():
        if not isinstance(host, str) or host not in {"claude", "codex"} or not isinstance(report, dict):
            raise LoomError("Inventory hosts must be claude or codex with report objects")
        skills = report.get("skills")
        if not isinstance(skills, list):
            raise LoomError("Inventory skills must be a list")
        for skill in skills:
            if not isinstance(skill, dict) or not isinstance(skill.get("name"), str) or not skill["name"]:
                raise LoomError("Each inventory skill must have a nonempty string name")
            _count(skill.get("description_chars", 0), "description_chars")
    for report in observations:
        if not isinstance(report, dict) or not isinstance(report.get("host"), str) or report["host"] not in {"claude", "codex"}:
            raise LoomError("Observation reports must come from observe-claude or observe-codex")
        _count(report.get("file_count", 0), "file_count")
        window = report.get("window", {})
        if not isinstance(window, dict):
            raise LoomError("Observation window must be an object")
        first, last = window.get("first_day"), window.get("last_day")
        if first is not None or last is not None:
            if not all(isinstance(day, str) and len(day) == 10 for day in (first, last)):
                raise LoomError("Window dates must be a pair of YYYY-MM-DD strings")
            try:
                first_day, last_day = date.fromisoformat(first), date.fromisoformat(last)
            except ValueError as exc:
                raise LoomError("Window dates must be valid YYYY-MM-DD dates") from exc
            if first_day.isoformat() != first or last_day.isoformat() != last:
                raise LoomError("Window dates must use the canonical YYYY-MM-DD format")
            if first_day > last_day:
                raise LoomError("Window first_day must not follow last_day")
        key = "skills" if report["host"] == "claude" else "skill_md_reads"
        if key not in report and (report.get("file_count", 0) or first is not None or last is not None):
            raise LoomError(f"Populated observations must include the {key} table")
        table = report.get(key, {})
        if not isinstance(table, dict):
            raise LoomError(f"Observation {key} must be an object")
        for name, row in table.items():
            if not isinstance(name, str) or not name or not isinstance(row, dict):
                raise LoomError("Each observed skill must have a nonempty string name and count object")
            for field in ("calls", "sessions"):
                _count(row.get(field), field)
            calls, sessions = row["calls"], row["sessions"]
            if sessions > min(calls, report.get("file_count", 0)) or (calls > 0 and sessions == 0):
                raise LoomError("Skill sessions must agree with calls and observed file_count")


def _host_report(host, inventory_report, observations, protected, min_sessions, min_days):
    mine = [o for o in observations if o.get("host") == host]
    # Reports lack member identities: addition or splicing dates could count the same
    # inputs twice. Require both thresholds within one report, including legacy ones.
    files = max((o.get("file_count", 0) for o in mine), default=0)
    spans = []
    qualified = 0
    for observation in mine:
        window = observation.get("window", {})
        first, last = window.get("first_day"), window.get("last_day")
        span = (date.fromisoformat(last) - date.fromisoformat(first)).days + 1 if first else 0
        spans.append(span)
        if observation.get("file_count", 0) >= min_sessions and span >= min_days:
            qualified += 1
    span = max(spans, default=0)
    sufficient = qualified > 0
    # claude: exact Skill tool calls. codex: syntactic SKILL.md path references.
    key, exact = ("skills", True) if host == "claude" else ("skill_md_reads", False)
    seen = {}
    for observation in mine:
        for name, row in (observation.get(key) or {}).items():
            total = seen.setdefault(name, {"calls": 0, "sessions": 0})
            # Keep positive signals from every report, even one too small to qualify.
            # Maxima are conservative reported counts, not a deduplicated event union.
            total["calls"] = max(total["calls"], row.get("calls", 0))
            total["sessions"] = max(total["sessions"], row.get("sessions", 0))
    rows, installed = [], set()
    for skill in inventory_report["skills"]:
        name = skill["name"]
        installed.add(name)
        hits = seen.get(name, {"calls": 0, "sessions": 0})
        if not mine:
            status = "no-observation"
        elif hits["calls"]:
            status = "used" if exact else "load-signal"
        else:
            status = "unobserved"
        rows.append({"skill": name, "status": status, "calls": hits["calls"], "sessions": hits["sessions"],
                     "description_chars": skill.get("description_chars", 0), "protected": name in protected})
    candidates = []
    if sufficient:
        candidates = [{"skill": row["skill"], "description_chars": row["description_chars"],
                       "action": "review-deactivation", "reversible": "move out of the discovery root, do not delete",
                       "automatic_mutation": False}
                      for row in sorted(rows, key=lambda r: (-r["description_chars"], r["skill"]))
                      if row["status"] == "unobserved" and not row["protected"]]
    return {"host": host, "installed": len(rows), "observed_files": files, "span_days": span,
            "coverage_policy": "single-report", "count_aggregation": "per-skill-maximum",
            "reports_supplied": len(mine), "qualifying_reports": qualified,
            "window_sufficient": sufficient, "attribution": "exact-skill-call" if exact else "skill-md-read-signal",
            "skills": rows, "review_candidates": candidates,
            "seen_but_not_installed": sorted(set(seen) - installed)}


def usage_report(inventories, observations, protected=(), min_sessions=DEFAULT_MIN_SESSIONS, min_days=DEFAULT_MIN_DAYS):
    """inventories: {host: inventory report}; observations: observe-claude / observe-codex reports."""
    if any(type(value) is not int or value < 1 for value in (min_sessions, min_days)):
        raise LoomError("Evidence window thresholds must be positive integers")
    if not isinstance(protected, (list, tuple, set, frozenset)) or any(
            not isinstance(name, str) or not name for name in protected):
        raise LoomError("Protected skills must be a collection of nonempty string names")
    _validate_reports(inventories, observations)
    protected = set(protected)
    hosts = [_host_report(host, report, observations, protected, min_sessions, min_days)
             for host, report in sorted(inventories.items())]
    return {"schema": 1, "observed_at": now(),
            "thresholds": {"min_files": min_sessions, "min_sessions": min_sessions, "min_days": min_days}, "hosts": hosts,
            "limits": "Unobserved is not useless: a skill may serve rare, high-value tasks. Codex load-signal is a "
                      "legacy label for syntactic tool-payload path references, not verified file access or skill use. "
                      "A Skill call does not show the task succeeded. Review candidates need human judgement and are only "
                      "listed when one report meets both file-count and elapsed-span thresholds; these do not prove "
                      "capture completeness or independent task opportunities. Across reports, file counts, spans "
                      "and per-skill counts are maxima, not sums or verified unique totals. sessions and "
                      "min_sessions are legacy names for file counts. Nothing is changed."}
