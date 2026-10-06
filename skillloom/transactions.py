"""Reviewed, hash-guarded single-skill changes with recoverable file journals.

This is a cooperative local maintenance tool, not a security boundary against a
malicious process with the same filesystem permissions. Stop the host from
updating the same skill while applying or recovering a transaction.
"""

from contextlib import contextmanager
from pathlib import Path
import uuid

from .common import (LoomError, atomic_write, contained, digest, file_modes, is_link, now,
                     object_digest, prune_empty, read_json, relative_path,
                     snapshot, valid_name, write_json)
from .inventory import inspect_skill


def checked_root(root):
    root = Path(root).absolute()
    if root != root.resolve() or is_link(root):
        raise LoomError("Select the physical root, not a symlink or junction")
    if root == Path(root.anchor) or root == Path.home() or root.name in {".codex", ".claude", ".system", "plugins", "memories"}:
        raise LoomError("A dedicated user-managed skills directory is required")
    return root


def validate_layout(plan):
    if plan.get("schema") != 1 or plan.get("operation") not in {"install", "update", "retire"}:
        raise LoomError("Unsupported change plan")
    if not valid_name(plan.get("name")):
        raise LoomError("Invalid target name")
    root = checked_root(plan["root"])
    target = root / plan["name"]
    if is_link(target) or target.resolve() != target:
        raise LoomError("Target location changed or is linked")
    journal = Path(plan["journal"]).resolve()
    if contained(journal, root) or contained(root, journal):
        raise LoomError("Journal and runtime roots must be disjoint")
    source = Path(plan["candidate"]).resolve() if plan.get("candidate") else None
    if source and (contained(source, root) or contained(root, source) or contained(journal, source) or contained(source, journal)):
        raise LoomError("Candidate, journal, and runtime roots must be disjoint")
    for table in (plan["before"], plan["after"]):
        for path, sha in table.items():
            relative_path(path)
            if not isinstance(sha, str) or len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
                raise LoomError("Invalid file digest")
    for hashes, modes in ((plan["before"], plan["before_modes"]), (plan["after"], plan["after_modes"])):
        if set(hashes) != set(modes) or any(type(mode) is not int or not 0 <= mode <= 0o777 for mode in modes.values()):
            raise LoomError("Invalid file mode table")
    return root, target, journal, source


def plan_change(candidate, root, journal, retire=None):
    root = checked_root(root)
    source = Path(candidate).resolve() if candidate else None
    name = retire if retire else source.name
    if not valid_name(name):
        raise LoomError("Invalid skill name")
    target = root / name
    before = snapshot(target)
    before_modes = file_modes(target, before)
    if before and "SKILL.md" not in before:
        raise LoomError("Existing target is not a skill; refusing adoption")
    if retire:
        if not before:
            raise LoomError("Cannot retire a missing skill")
        after = {}
        after_modes = {}
        operation = "retire"
    else:
        review = inspect_skill(source)
        if review["errors"]:
            raise LoomError("Candidate failed static inspection: " + "; ".join(review["errors"]))
        after = snapshot(source)
        after_modes = file_modes(source, after)
        operation = "update" if before else "install"
    result = {"schema": 1, "created_at": now(), "operation": operation, "name": name,
              "root": str(root), "candidate": str(source) if source else None,
              "journal": str(Path(journal).resolve()), "before": before, "after": after,
              "before_modes": before_modes, "after_modes": after_modes,
              "changes": [{"path": p, "before": before.get(p), "after": after.get(p),
                           "before_mode": before_modes.get(p), "after_mode": after_modes.get(p)}
                          for p in sorted(set(before) | set(after))
                          if (before.get(p), before_modes.get(p)) != (after.get(p), after_modes.get(p))]}
    validate_layout(result)
    return result


@contextmanager
def root_lock(root):
    root.mkdir(parents=True, exist_ok=True)
    lock = root / ".skillloom.lock"
    try:
        handle = lock.open("x", encoding="utf-8")
    except FileExistsError as exc:
        raise LoomError("Maintenance lock exists; inspect its journal/process before removing it") from exc
    try:
        with handle:
            handle.write(now())
        yield
    finally:
        lock.unlink()


def checked_plan(plan):
    """Do not trust an edited redundant changes list."""
    expected = [{"path": p, "before": plan["before"].get(p), "after": plan["after"].get(p),
                 "before_mode": plan["before_modes"].get(p), "after_mode": plan["after_modes"].get(p)}
                for p in sorted(set(plan["before"]) | set(plan["after"]))
                if (plan["before"].get(p), plan["before_modes"].get(p)) != (plan["after"].get(p), plan["after_modes"].get(p))]
    if plan.get("changes") != expected:
        raise LoomError("Plan changes do not match snapshots")


def apply(plan, expected_digest):
    if object_digest(plan) != expected_digest:
        raise LoomError("Plan digest differs from the reviewed plan")
    root, target, journal, source = validate_layout(plan)
    checked_plan(plan)
    with root_lock(root):
        if snapshot(target) != plan["before"] or file_modes(target, plan["before"]) != plan["before_modes"]:
            raise LoomError("Installed files changed since planning; make a new plan")
        if source and (snapshot(source) != plan["after"] or file_modes(source, plan["after"]) != plan["after_modes"]):
            raise LoomError("Candidate changed since planning; make a new plan")
        if not plan["changes"]:
            return {"status": "no_change", "plan_digest": expected_digest}
        transaction = journal / str(uuid.uuid4())
        transaction.mkdir(parents=True, exist_ok=False)
        # Copy every changed original before mutating any runtime file.
        for change in plan["changes"]:
            if change["before"]:
                data = (target / change["path"]).read_bytes()
                if digest(data) != change["before"]:
                    raise LoomError("Original drifted during backup")
                atomic_write(transaction / "backup" / change["path"], data)
        record = {"schema": 1, "plan": plan, "plan_digest": expected_digest,
                  "created_at": now(), "status": "prepared"}
        write_json(transaction / "transaction.json", record)
        try:
            record["status"] = "applying"
            write_json(transaction / "transaction.json", record)
            for change in plan["changes"]:
                path = target / change["path"]
                if change["after"]:
                    data = (source / change["path"]).read_bytes()
                    if digest(data) != change["after"]:
                        raise LoomError("Candidate drifted during application")
                    atomic_write(path, data, mode=change["after_mode"])
                else:
                    path.unlink()
                    prune_empty(path.parent, root)
            if snapshot(target) != plan["after"] or file_modes(target, plan["after"]) != plan["after_modes"]:
                raise LoomError("Post-apply verification failed")
            record["status"] = "complete"
            record["completed_at"] = now()
            write_json(transaction / "transaction.json", record)
        except Exception:
            # Leave a recoverable journal. Do not silently mask partial failure.
            record["status"] = "interrupted"
            write_json(transaction / "transaction.json", record)
            raise
    return {"status": "complete", "transaction": str(transaction), "changed_files": len(plan["changes"])}


def rollback(transaction):
    transaction = Path(transaction).resolve()
    record = read_json(transaction / "transaction.json")
    plan = record["plan"]
    root, target, journal, _ = validate_layout(plan)
    checked_plan(plan)
    if transaction.parent != journal or object_digest(plan) != record["plan_digest"]:
        raise LoomError("Journal location or plan integrity mismatch")
    if record["status"] == "rolled_back":
        return {"status": "already_rolled_back"}
    if record["status"] not in {"prepared", "applying", "interrupted", "complete", "rolling_back"}:
        raise LoomError("Unsupported transaction state")
    with root_lock(root):
        current = snapshot(target)
        current_modes = file_modes(target, current)
        # Also detect unrelated additions/changes, rather than overwriting them.
        if set(current) - (set(plan["before"]) | set(plan["after"])):
            raise LoomError("New files appeared; refusing rollback")
        for path in set(plan["before"]) | set(plan["after"]):
            old = (plan["before"].get(path), plan["before_modes"].get(path))
            new = (plan["after"].get(path), plan["after_modes"].get(path))
            allowed = {new} if record["status"] == "complete" else {old, new}
            if (current.get(path), current_modes.get(path)) not in allowed:
                raise LoomError("Runtime drift detected; refusing rollback")
        for change in plan["changes"]:
            if change["before"]:
                backup = transaction / "backup" / change["path"]
                if is_link(backup) or digest(backup.read_bytes()) != change["before"]:
                    raise LoomError("Backup integrity check failed")
        record["status"] = "rolling_back"
        write_json(transaction / "transaction.json", record)
        for change in plan["changes"]:
            path = target / change["path"]
            if change["before"]:
                atomic_write(path, (transaction / "backup" / change["path"]).read_bytes(), mode=change["before_mode"])
            elif path.exists():
                path.unlink()
                prune_empty(path.parent, root)
        if snapshot(target) != plan["before"] or file_modes(target, plan["before"]) != plan["before_modes"]:
            raise LoomError("Rollback postcondition failed")
        record["status"] = "rolled_back"
        record["rolled_back_at"] = now()
        write_json(transaction / "transaction.json", record)
    return {"status": "rolled_back", "transaction": str(transaction)}
