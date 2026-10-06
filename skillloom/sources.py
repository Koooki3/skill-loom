"""Public GitHub discovery and bounded pinned-file staging. No installation."""

import hashlib
import json
from pathlib import Path
import re
from urllib.parse import quote
from urllib.request import Request, urlopen

from .common import LoomError, atomic_write, digest, now, relative_path, snapshot, write_json


def repository(value):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", value) or any(p in {".", ".."} for p in value.split("/")):
        raise LoomError("Use owner/repository, not an arbitrary URL")
    return value


def download(url, limit=8 * 1024 * 1024):
    request = Request(url, headers={"User-Agent": "Skill-Loom/0.1", "Accept": "application/vnd.github+json"})
    with urlopen(request, timeout=30) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise LoomError("Remote response exceeds the configured size limit")
    return data


def api(repo, suffix):
    endpoint = f"https://api.github.com/repos/{repository(repo)}"
    return json.loads(download(endpoint + ("/" + suffix if suffix else "")))


def discover(registry):
    results = []
    for item in registry["sources"]:
        repo = repository(item["repository"])
        try:
            meta = api(repo, "")
            sha = api(repo, "commits/" + quote(meta["default_branch"], safe=""))["sha"]
            results.append({"repository": repo, "candidate_commit": sha, "pinned_commit": item.get("commit"),
                            "changed": sha != item.get("commit"), "status": "observed"})
        except (OSError, ValueError, KeyError) as exc:
            results.append({"repository": repo, "status": "unavailable", "error_type": type(exc).__name__, "http_status": getattr(exc, "code", None)})
    return {"observed_at": now(), "sources": results, "installed": False}


def scout(queries, per_query=10):
    """Bounded public repository search; query text is deliberately user supplied."""
    if not 1 <= len(queries) <= 5 or not 1 <= per_query <= 20:
        raise LoomError("Scout allows 1..5 explicit public queries, at most 20 results each")
    results, failures = {}, []
    for query in queries:
        if not query.strip() or len(query) > 200:
            raise LoomError("Search query must contain 1..200 characters")
        try:
            data = json.loads(download("https://api.github.com/search/repositories?q=" + quote(query, safe="") + f"&per_page={per_query}"))
            for item in data.get("items", []):
                results[item["full_name"]] = {"repository": item["full_name"], "url": item["html_url"],
                                              "pushed_at": item["pushed_at"], "archived": item["archived"],
                                              "license_hint": (item.get("license") or {}).get("spdx_id"),
                                              "quality": "unreviewed"}
        except (OSError, ValueError, KeyError) as exc:
            failures.append({"query_index": queries.index(query), "error_type": type(exc).__name__})
    return {"observed_at": now(), "query_count": len(queries), "repositories": list(results.values()),
            "unavailable": failures, "coverage": "bounded GitHub repository sample, not global skill coverage", "installed": False}


def stage(repo, commit, subpath, destination):
    repo = repository(repo)
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise LoomError("Staging requires a full lowercase 40-character commit SHA")
    subpath = relative_path(subpath).as_posix()
    destination = Path(destination).resolve()
    if destination.exists():
        raise LoomError("Destination must be new; never overwrite a candidate")
    tree = api(repo, "git/trees/" + commit + "?recursive=1")
    if tree.get("truncated"):
        raise LoomError("Repository tree is truncated; use the official sparse installer and review it locally")
    selected = [entry for entry in tree["tree"] if entry["path"].startswith(subpath + "/")]
    files = [entry for entry in selected if entry["type"] == "blob"]
    if not any(entry["path"] == subpath + "/SKILL.md" for entry in files):
        raise LoomError("Selected path has no SKILL.md")
    if len(files) > 400 or sum(entry.get("size", 0) for entry in files) > 20 * 1024 * 1024:
        raise LoomError("Candidate exceeds the 400-file / 20 MiB review limit")
    licenses = [entry for entry in tree["tree"] if "/" not in entry["path"] and entry["type"] == "blob"
                and entry["path"].upper().startswith(("LICENSE", "COPYING", "NOTICE"))]
    contents, modes = {}, {}
    for entry in files + licenses:
        if entry.get("mode") not in {"100644", "100755"}:
            raise LoomError("Links and special files cannot be staged")
        source_path = entry["path"]
        local = source_path[len(subpath) + 1:] if source_path.startswith(subpath + "/") else "upstream-licenses/" + source_path
        relative_path(local)
        if local.casefold() == "provenance.json" or local.casefold() in {key.casefold() for key in contents}:
            raise LoomError("Reserved or case-colliding candidate path")
        data = download(f"https://raw.githubusercontent.com/{repo}/{commit}/{quote(source_path, safe='/')}", 2 * 1024 * 1024)
        blob_sha = hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()
        if entry.get("sha") != blob_sha or entry.get("size") != len(data):
            raise LoomError("Downloaded content does not match the pinned Git blob: " + source_path)
        contents[local] = data
        modes[local] = 0o755 if entry["mode"] == "100755" else 0o644
        if sum(map(len, contents.values())) > 20 * 1024 * 1024:
            raise LoomError("Candidate content exceeds limit")
    destination.mkdir(parents=True, exist_ok=False)
    for path, data in contents.items():
        atomic_write(destination / path, data, mode=modes[path])
    provenance = {"repository": repo, "commit": commit, "path": subpath, "retrieved_at": now(),
                  "upstream_files": {key: digest(value) for key, value in contents.items()},
                  "upstream_modes": modes,
                  "license_review": "required", "reviewed": False}
    write_json(destination / "provenance.json", provenance)
    return {"status": "staged", "file_count": len(snapshot(destination)), "provenance": provenance,
            "limits": "Public bytes downloaded; no third-party code executed and no host skill installed."}
