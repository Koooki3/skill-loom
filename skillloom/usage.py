"""Per-host skill usage evidence. Proposes review candidates; never edits a skill system."""

from .common import LoomError, now

# A skill is only called unused after the whole window has had a fair chance to use it.
DEFAULT_MIN_SESSIONS = 10
DEFAULT_MIN_DAYS = 7


def _host_report(host, inventory_report, observations, protected, min_sessions, min_days):
    mine = [o for o in observations if o.get("host") == host]
    sessions = sum(o.get("file_count", 0) for o in mine)
    firsts = [o["window"]["first_day"] for o in mine if o.get("window", {}).get("first_day")]
    lasts = [o["window"]["last_day"] for o in mine if o.get("window", {}).get("last_day")]
    span = 0
    if firsts and lasts:
        from datetime import date
        span = (date.fromisoformat(max(lasts)) - date.fromisoformat(min(firsts))).days + 1
    sufficient = bool(mine) and sessions >= min_sessions and span >= min_days
    # claude: exact Skill tool calls. codex: SKILL.md opens (a weaker load signal).
    key, exact = ("skills", True) if host == "claude" else ("skill_md_reads", False)
    seen = {}
    for observation in mine:
        for name, row in (observation.get(key) or {}).items():
            total = seen.setdefault(name, {"calls": 0, "sessions": 0})
            total["calls"] += row.get("calls", 0)
            total["sessions"] += row.get("sessions", 0)
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
    return {"host": host, "installed": len(rows), "observed_files": sessions, "span_days": span,
            "window_sufficient": sufficient, "attribution": "exact-skill-call" if exact else "skill-md-read-signal",
            "skills": rows, "review_candidates": candidates,
            "seen_but_not_installed": sorted(set(seen) - installed)}


def usage_report(inventories, observations, protected=(), min_sessions=DEFAULT_MIN_SESSIONS, min_days=DEFAULT_MIN_DAYS):
    """inventories: {host: inventory report}; observations: observe-claude / observe-codex reports."""
    if not inventories:
        raise LoomError("Provide at least one host inventory")
    if min_sessions < 1 or min_days < 1:
        raise LoomError("Evidence window thresholds must be positive")
    for report in observations:
        if report.get("host") not in {"claude", "codex"}:
            raise LoomError("Observation reports must come from observe-claude or observe-codex")
    protected = set(protected)
    hosts = [_host_report(host, report, observations, protected, min_sessions, min_days)
             for host, report in sorted(inventories.items())]
    return {"schema": 1, "observed_at": now(),
            "thresholds": {"min_sessions": min_sessions, "min_days": min_days}, "hosts": hosts,
            "limits": "Unobserved is not useless: a skill may serve rare, high-value tasks, and a Skill call or SKILL.md "
                      "read does not show the task succeeded. Review candidates need human judgement and are only "
                      "listed after the whole window clears the thresholds. Nothing is changed."}
