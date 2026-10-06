"""User-specific decision support. Proposals only; never alters a skill system."""

from collections import Counter
import platform
import re
import shutil

from .common import LoomError

DIMENSIONS = {"task_fit", "evidence", "maintainability", "efficiency", "portability"}


def capability_ids(value):
    if not isinstance(value, list) or any(not isinstance(c, str) or not re.fullmatch(r"[a-z][a-z0-9-]{0,63}", c) for c in value):
        raise LoomError("Capabilities must be a list of short portable identifiers")
    if len(value) != len(set(value)):
        raise LoomError("Capability identifiers must be unique")
    return value


def catalog_items(catalog):
    if not isinstance(catalog, dict) or not isinstance(catalog.get("skills"), list):
        raise LoomError("Catalog must contain a skills list")
    seen = set()
    for item in catalog["skills"]:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str) or not item["name"].strip():
            raise LoomError("Catalog entries require a name")
        if item["name"] in seen:
            raise LoomError("Duplicate catalog skill name")
        seen.add(item["name"])
        capability_ids(item.get("capabilities", []))
        if not isinstance(item.get("description", ""), str):
            raise LoomError("Catalog description must be text")
    return catalog["skills"]


def validate_profile(profile):
    if profile.get("schema") != 1:
        raise LoomError("Unsupported profile schema")
    capability_ids(profile.get("required_capabilities", []))
    weights = profile.get("weights", {})
    if set(weights) != DIMENSIONS or any(type(x) not in {int, float} or not 0 <= x <= 1 for x in weights.values()) or abs(sum(weights.values()) - 1) > 1e-6:
        raise LoomError("Five ranking weights must each be 0..1 and sum to 1")
    budgets = profile.get("budgets", {})
    for name in ("active_skills", "description_chars", "repair_rounds"):
        if type(budgets.get(name)) is not int or budgets[name] < 1:
            raise LoomError("Profile requires positive explicit portfolio/repair budgets")
    return profile


def doctor(profile):
    validate_profile(profile)
    return {"schema": 1, "platform": platform.system(), "python": platform.python_version(),
            "tools_present": {name: shutil.which(name) is not None for name in ("codex", "claude", "git", "node")},
            "profile_valid": True, "limits": "Executable presence only. No credentials, home scan, host sessions or feature probes performed."}


def rank(profile, candidates):
    validate_profile(profile)
    results = []
    required = set(profile["required_capabilities"])
    for item in candidates["candidates"]:
        ratings = item.get("ratings", {})
        if any(key not in DIMENSIONS or type(value) not in {int, float} or not 0 <= value <= 4 for key, value in ratings.items()):
            raise LoomError("Rubric ratings must be 0..4 for known dimensions")
        refs = item.get("evidence_refs", {})
        if not isinstance(refs, dict):
            raise LoomError("Evidence references must be a mapping")
        known = {key: value for key, value in ratings.items() if isinstance(refs.get(key), str) and refs[key].strip()}
        unknown = sorted(DIMENSIONS - set(known))
        score = round(100 * sum(profile["weights"][key] * value / 4 for key, value in known.items()), 2)
        offered = set(capability_ids(item.get("capabilities", [])))
        reasons = []
        if not offered & required:
            reasons.append("no-current-capability-fit")
        if item.get("license_review") != "approved":
            reasons.append("license-unreviewed")
        if item.get("permissions_review") != "acceptable":
            reasons.append("permissions-unreviewed")
        if not re.fullmatch(r"[0-9a-f]{40}", item.get("commit", "")):
            reasons.append("source-not-pinned")
        if item.get("behavior_test") != "pass":
            reasons.append("local-behavior-unverified")
        if unknown:
            reasons.append("incomplete-rubric-evidence")
        results.append({"id": item["id"], "queue_score": score, "unknown_dimensions": unknown,
                        "required_overlap": sorted(offered & required), "adoption_blockers": reasons,
                        "next_action": "review-pilot" if not reasons else "investigate",
                        "automatic_install": False})
    return {"schema": 1, "ranked": sorted(results, key=lambda x: (-x["queue_score"], x["id"])),
            "limits": "Human/agent-graded evidence queue, not a probability or universal skill-quality score. Recalibrate on held-out local tasks."}


def gap_analysis(profile, catalog, observations):
    validate_profile(profile)
    providers = {}
    for item in catalog_items(catalog):
        for capability in item.get("capabilities", []):
            providers.setdefault(capability, []).append(item["name"])
    tasks = observations.get("tasks", [])
    if not isinstance(tasks, list):
        raise LoomError("Observations must contain a tasks list")
    requested = Counter()
    failed = Counter()
    environment = Counter()
    evidence_counts = Counter()
    for task in tasks:
        if not isinstance(task, dict):
            raise LoomError("Task observation must be an object")
        if task.get("outcome") not in {"pass", "fail", "unverified"} or task.get("cause") not in {"none", "skill", "environment", "source", "unknown"}:
            raise LoomError("Task observations require bounded outcome and cause labels")
        for capability in capability_ids(task.get("required_capabilities", [])):
            requested[capability] += 1
            ref = task.get("evidence_ref")
            evidence_counts[capability] += isinstance(ref, str) and bool(ref.strip())
            if task["outcome"] == "fail" and task["cause"] == "skill":
                failed[capability] += 1
            if task["outcome"] == "fail" and task["cause"] == "environment":
                environment[capability] += 1
    results = []
    for capability in sorted(set(profile["required_capabilities"]) | set(requested)):
        available = providers.get(capability, [])
        if environment[capability]:
            action = "repair-environment-first"
        elif not available:
            action = "search-or-design-candidate"
        elif failed[capability]:
            action = "reproduce-and-adapt-existing"
        else:
            action = "use-existing-and-measure"
        results.append({"capability": capability, "providers": available,
                        "observed_tasks": requested[capability], "skill_failures": failed[capability],
                        "environment_failures": environment[capability], "observations_with_evidence": evidence_counts[capability],
                        "next_action": action, "evidence_sufficient_for_automatic_change": False})
    return {"schema": 1, "gaps": results,
            "limits": "Capability mapping and cause labels require review. Missing coverage is a hypothesis; first check native tools and project workflows."}


def portfolio(profile, catalog):
    validate_profile(profile)
    skills = catalog_items(catalog)
    pairs = []
    for i, left in enumerate(skills):
        a = set(left.get("capabilities", []))
        if not a:
            continue
        for right in skills[i + 1:]:
            b = set(right.get("capabilities", []))
            overlap = len(a & b) / len(a | b) if a | b else 0
            if overlap >= .8 and left.get("scope") == right.get("scope"):
                pairs.append({"skills": [left["name"], right["name"]], "capability_overlap": round(overlap, 3),
                              "action": "review-triggers-and-complementarity", "auto_merge": False})
    chars = sum(len(item.get("description", "")) for item in skills)
    budget = profile["budgets"]
    return {"schema": 1, "skill_count": len(skills), "description_chars": chars,
            "budget_exceeded": {"active_skills": len(skills) > budget["active_skills"], "description_chars": chars > budget["description_chars"]},
            "overlap_candidates": pairs, "unmapped_skills": [x["name"] for x in skills if not x.get("capabilities")],
            "limits": "Overlap is not redundancy. Complementary artifacts and host-provided tools may share capabilities. Budgets are user choices, not quality thresholds."}
