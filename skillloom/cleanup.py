"""Exact-file cleanup inside a deliberately adopted, reconstructible cache."""

from pathlib import Path
import math
import time
from .common import (LoomError, contained, digest, is_link, now, object_digest,
                     prune_empty, read_json, relative_path, snapshot, write_json)

MARKER = ".skillloom-cache.json"


def cache_root(root):
    original = Path(root).absolute()
    root = original.resolve()
    if root != original or is_link(original) or root == Path(root.anchor) or root == Path.home():
        raise LoomError("Select a dedicated physical task cache")
    if root.name.lower() in {".codex", ".claude", "skills", "sessions", "plugins", "memories", "projects", "outputs", "backup", "backups"}:
        raise LoomError("Runtime, output, and evidence roots are not caches")
    marker = root / MARKER
    if is_link(marker):
        raise LoomError("Cache marker cannot be linked")
    record = read_json(marker)
    if record != {"owner": "skill-loom", "reconstructible": True, "schema": 1}:
        raise LoomError("Cache requires an explicit reconstructible-ownership marker")
    return root


def cleanup_plan(root, age_days):
    root = cache_root(root)
    if type(age_days) not in {int, float} or not math.isfinite(age_days) or age_days < 0:
        raise LoomError("Age must be finite and nonnegative")
    hashes = snapshot(root)
    cutoff = time.time() - age_days * 86400
    files = []
    for path, sha in hashes.items():
        if path != MARKER:
            item = root / path
            stat = item.stat()
            if stat.st_mtime <= cutoff:
                files.append({"path": path, "sha256": sha, "bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns})
    return {"schema": 1, "operation": "cleanup", "root": str(root), "created_at": now(),
            "minimum_age_days": age_days, "files": files, "bytes": sum(x["bytes"] for x in files)}


def cleanup_apply(plan, expected_digest, receipt_path):
    if object_digest(plan) != expected_digest or plan.get("schema") != 1 or plan.get("operation") != "cleanup":
        raise LoomError("Reviewed cleanup plan mismatch")
    root = cache_root(plan["root"])
    receipt_path = Path(receipt_path).resolve()
    if contained(receipt_path, root):
        raise LoomError("Preserve the cleanup receipt outside the cache")
    # Snapshot validates nested links, including those not selected for deletion.
    current = snapshot(root)
    seen = set()
    for item in plan["files"]:
        relative_path(item["path"])
        if item["path"] == MARKER or item["path"] in seen:
            raise LoomError("Invalid cleanup entry")
        seen.add(item["path"])
        path = root / item["path"]
        if current.get(item["path"]) != item["sha256"] or path.stat().st_mtime_ns != item["mtime_ns"]:
            raise LoomError("Cache file changed since planning")
    receipt = {"status": "applying", "plan_digest": expected_digest, "deleted_files": [], "deleted_bytes": 0}
    write_json(receipt_path, receipt)
    for item in plan["files"]:
        path = root / item["path"]
        # Recheck immediately before each unlink. Run only while cache writers are stopped.
        if is_link(path) or digest(path.read_bytes()) != item["sha256"] or path.stat().st_mtime_ns != item["mtime_ns"]:
            raise LoomError("Concurrent cache change; partial cleanup receipt retained")
        receipt["pending_file"] = item
        write_json(receipt_path, receipt)
        path.unlink()
        prune_empty(path.parent, root)
        receipt["deleted_files"].append(item["path"])
        receipt["deleted_bytes"] += item["bytes"]
        receipt.pop("pending_file", None)
        write_json(receipt_path, receipt)
    receipt["status"] = "complete"
    write_json(receipt_path, receipt)
    return receipt
