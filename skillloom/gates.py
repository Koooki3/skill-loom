"""Validate evidence receipts. A receipt is an auditable claim, not a truth oracle."""

from pathlib import Path
from datetime import datetime, timezone
import math
import re
from .common import LoomError, digest, read_json

PROFILES = {
    "skill-change": {"scope", "provenance", "static", "behavior", "rollback"},
    "research": {"scope", "sources", "reproduction", "statistics"},
    "production": {"scope", "tests", "runtime", "rollback"},
    "documents": {"scope", "fidelity", "render"},
}



def _receipt_checks(receipt):
    """Validate the complete JSON shape before reading any evidence artifacts."""
    if not isinstance(receipt, dict):
        raise LoomError("Receipt must be an object")
    if receipt.get("profile") is not None and not isinstance(receipt["profile"], str):
        raise LoomError("Receipt profile must be a string or null")
    checks = receipt.get("checks", [])
    if not isinstance(checks, list):
        raise LoomError("Receipt checks must be a list")
    names = set()
    for check in checks:
        if not isinstance(check, dict):
            raise LoomError("Receipt checks must be objects")
        name = check.get("id")
        if not isinstance(name, str) or not name.strip():
            raise LoomError("Receipt check IDs must be nonempty strings")
        if name in names:
            raise LoomError("Receipt check IDs must be unique")
        names.add(name)
        artifacts = check.get("artifacts", [])
        if not isinstance(artifacts, list):
            raise LoomError("Receipt artifacts must be a list")
        for artifact in artifacts:
            if not isinstance(artifact, dict):
                raise LoomError("Receipt artifacts must be objects")
            location = artifact.get("path")
            checksum = artifact.get("sha256")
            if not isinstance(location, str) or not location.strip():
                raise LoomError("Evidence artifact path must be a nonempty string")
            if not isinstance(checksum, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", checksum):
                raise LoomError("Evidence artifact sha256 must contain 64 hexadecimal characters")
    return checks


def gate(receipt_path, profile, expected_run=None, expected_candidate=None, max_age_hours=None):
    if profile not in PROFILES:
        raise LoomError("Unknown acceptance profile")
    path = Path(receipt_path)
    receipt = read_json(path)
    checks = _receipt_checks(receipt)
    names = [check["id"] for check in checks]
    failures = [f"Missing check: {name}" for name in sorted(PROFILES[profile] - set(names))]
    if expected_run is not None and receipt.get("run_id") != expected_run:
        failures.append("Receipt belongs to a different task run")
    if expected_candidate is not None and receipt.get("candidate_digest") != expected_candidate:
        failures.append("Receipt belongs to a different candidate")
    if receipt.get("profile") not in {None, profile}:
        failures.append("Receipt profile mismatch")
    if max_age_hours is not None:
        if type(max_age_hours) not in {int, float} or not math.isfinite(max_age_hours) or max_age_hours <= 0:
            raise LoomError("Evidence age limit must be finite and positive")
        try:
            created = datetime.fromisoformat(receipt["created_at"])
            if created.tzinfo is None:
                raise ValueError("Timestamp needs a timezone")
            age = (datetime.now(timezone.utc) - created).total_seconds() / 3600
            if age < 0 or age > max_age_hours:
                failures.append("Receipt is stale or future-dated")
        except (KeyError, ValueError, TypeError):
            failures.append("Receipt has no valid observation time")
    for check in checks:
        if check.get("status") != "pass":
            failures.append(f"Check is not verified: {check.get('id')}")
            continue
        artifacts = check.get("artifacts", [])
        if not artifacts:
            failures.append(f"No evidence artifact: {check.get('id')}")
        for artifact in artifacts:
            artifact_path = path.parent / artifact["path"]
            try:
                if digest(artifact_path.read_bytes()) != artifact["sha256"]:
                    failures.append(f"Evidence changed: {check['id']}")
            except OSError:
                failures.append(f"Evidence unavailable: {check['id']}")
    return {"profile": profile, "status": "pass" if not failures else "fail", "failures": failures,
            "limits": "Checks declared status and artifact bytes, not whether the underlying claim is truthful or sufficient."}


def stop_decision(receipt, profile, event, **constraints):
    """One repair opportunity; a repeated Stop must terminate even on failure."""
    report = gate(receipt, profile, **constraints)
    if report["status"] == "pass":
        return {}, report
    if event.get("stop_hook_active") is True:
        return {"systemMessage": "Skill Loom: repair limit reached. Acceptance remains unverified; report the unresolved failure."}, report
    return {"decision": "block", "reason": "Acceptance evidence is incomplete. Make one scoped repair, or report the unresolved failure and stop. " + "; ".join(report["failures"][:3])}, report
