"""Environment-aware first-deployment recommendations. Read-only; install nothing, run nothing."""

import json
import os
from pathlib import Path
import re
import shutil

from .common import LoomError, now
from .strategy import catalog_items, validate_profile

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "build", "dist", ".mypy_cache", ".tox", "site-packages"}
MAX_FILES, MAX_DEPTH, MAX_MANIFEST = 5000, 4, 200_000

# Marker -> catalog capability ids. A tag fires on file/dir names, suffix counts, a GitHub remote,
# or a dependency named in a root manifest. Only tag names and counts leave this module.
SIGNALS = [
    {"tag": "python", "names": ["pyproject.toml", "requirements.txt", "setup.py"], "suffixes": {".py": 3},
     "capabilities": ["reproducible-experiments", "experiment-logging", "code-fix"]},
    {"tag": "notebook", "suffixes": {".ipynb": 1},
     "capabilities": ["notebook-authoring", "data-exploration", "experiment-notebook"]},
    {"tag": "react", "dependencies": ["react", "next"],
     "capabilities": ["react-composition", "component-api", "state-architecture", "react-performance",
                      "rendering-optimization", "bundle-analysis"]},
    {"tag": "web-frontend", "suffixes": {".tsx": 3, ".jsx": 3, ".vue": 3, ".svelte": 3, ".css": 5},
     "capabilities": ["interface-design", "visual-review", "responsive-ui", "web-accessibility",
                      "keyboard-navigation", "semantic-review"]},
    {"tag": "github", "github_remote": True, "names": [".github"],
     "capabilities": ["pull-request-review", "comment-triage", "ci-diagnosis", "workflow-debugging"]},
    {"tag": "docs", "names": ["docs", "README.md"],
     "capabilities": ["project-documentation", "onboarding", "build-debug-guides"]},
    {"tag": "paper", "suffixes": {".tex": 1, ".bib": 1},
     "capabilities": ["research-paper-editing", "argument-structure", "review-readiness", "citation-audit",
                      "bibliographic-verification", "bibtex", "scientific-plotting"]},
    {"tag": "mcp", "dependencies": ["mcp", "fastmcp", "@modelcontextprotocol/sdk"],
     "capabilities": ["mcp-server-development", "tool-schema", "transport-auth"]},
    {"tag": "pdf", "suffixes": {".pdf": 3},
     "capabilities": ["pdf-text-extraction", "pdf-page-operations", "ocr-preparation"]},
]

# Executables a skill needs at run time. Missing ones are reported, never installed.
TOOL_REQUIREMENTS = {"gh-fix-ci": ["gh"], "gh-address-comments": ["gh"], "yeet": ["gh", "git"],
                     "oil-motion": ["ffmpeg", "python3"], "mcp-builder": ["node"]}
HOST_TOOLS = ("codex", "claude", "git", "gh", "node", "python3", "ffmpeg")


def _manifest_text(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            return handle.read(MAX_MANIFEST)
    except OSError:
        return ""


def _dependencies(root):
    """Dependency names from root-level manifests of the project and its direct subfolders."""
    found = set()
    folders = [root] + [p for p in sorted(root.iterdir()) if p.is_dir() and p.name not in SKIP_DIRS][:30]
    for folder in folders:
        package = _manifest_text(folder / "package.json")
        if package:
            try:
                data = json.loads(package)
                for section in ("dependencies", "devDependencies", "peerDependencies"):
                    found.update((data.get(section) or {}).keys())
            except (ValueError, AttributeError):
                pass
        for line in _manifest_text(folder / "requirements.txt").splitlines():
            match = re.match(r"\s*([A-Za-z][A-Za-z0-9_.-]*)", line)
            if match and not line.lstrip().startswith("#"):
                found.add(match.group(1).lower())
        # pyproject: quoted requirement strings only, so prose in descriptions is not read as a dependency
        found.update(w.lower() for w in re.findall(
            r'"([A-Za-z][A-Za-z0-9_.-]*)(?:\[[^\]]*\])?\s*(?:[=<>~!;]|")', _manifest_text(folder / "pyproject.toml")))
    return found


def scan_project(root):
    root = Path(root)
    if not root.is_dir():
        raise LoomError("Project root is not a directory")
    names, suffixes, files, truncated = set(), {}, 0, False
    base_depth = len(root.resolve().parts)
    for parent, dirs, filenames in os.walk(root, followlinks=False):
        depth = len(Path(parent).resolve().parts) - base_depth
        dirs[:] = [d for d in sorted(dirs) if d not in SKIP_DIRS and not (Path(parent) / d).is_symlink()]
        if depth >= MAX_DEPTH:
            dirs[:] = []
        if depth <= 1:
            names.update(dirs)
            names.update(filenames)
        for filename in filenames:
            files += 1
            if files > MAX_FILES:
                truncated = True
                break
            suffix = Path(filename).suffix.lower()
            if suffix:
                suffixes[suffix] = suffixes.get(suffix, 0) + 1
        if truncated:
            break
    git_config = _manifest_text(root / ".git" / "config")
    return {"names": names, "suffixes": suffixes, "files": files, "truncated": truncated,
            "github_remote": "github.com" in git_config, "dependencies": _dependencies(root)}


def detect(scans):
    """Fire tags over one or more project scans; returns {tag: evidence} with counts only."""
    fired = {}
    for scan in scans:
        for rule in SIGNALS:
            hit = [n for n in rule.get("names", []) if n in scan["names"]]
            hit += [s for s, minimum in rule.get("suffixes", {}).items() if scan["suffixes"].get(s, 0) >= minimum]
            hit += [d for d in rule.get("dependencies", []) if d in scan["dependencies"]]
            if rule.get("github_remote") and scan["github_remote"]:
                hit.append("github-remote")
            if hit:
                entry = fired.setdefault(rule["tag"], {"projects": 0, "markers": set()})
                entry["projects"] += 1
                entry["markers"].update(hit)
    return {tag: {"projects": e["projects"], "markers": sorted(e["markers"])} for tag, e in sorted(fired.items())}


def recommend(profile, catalog, inventories, project_roots, allow_scoped=False):
    """inventories: {host: inventory report}. Returns a ranked, reviewable adoption queue."""
    validate_profile(profile)
    items = catalog_items(catalog)
    if not inventories:
        raise LoomError("Provide at least one host inventory")
    scans = [scan_project(root) for root in project_roots]
    tags = detect(scans)
    signal_caps = {c for rule in SIGNALS if rule["tag"] in tags for c in rule["capabilities"]}
    required = set(profile["required_capabilities"])
    installed = {host: {s["name"] for s in report["skills"]} for host, report in inventories.items()}
    tools = {name: shutil.which(name) is not None for name in HOST_TOOLS}
    budget = profile["budgets"]
    used_chars = max((r.get("description_chars", 0) for r in inventories.values()), default=0)
    used_skills = max((len(names) for names in installed.values()), default=0)
    recommended, skipped = [], {"scoped": [], "no_source": [], "already_everywhere": []}
    for item in items:
        name = item["name"]
        missing_on = sorted(host for host in installed if name not in installed[host])
        if not missing_on:
            skipped["already_everywhere"].append(name)
            continue
        if str(item.get("scope", "general")) != "general" and not allow_scoped:
            skipped["scoped"].append(name)
            continue
        upstream = item.get("upstream") or {}
        if item.get("source_kind") not in {"pinned_upstream_adaptation", "known_upstream_unpinned"} or not upstream.get("repo"):
            skipped["no_source"].append(name)
            continue
        capabilities = item.get("capabilities", [])
        matched = sorted(set(capabilities) & (signal_caps | required))
        if not matched:
            continue
        weight = sum(2 if c in required else 1 for c in matched)
        pinned = bool(re.fullmatch(r"[0-9a-f]{40}", upstream.get("ref") or ""))
        notes = []
        if not pinned:
            notes.append("source-not-pinned")
        license_text = str(upstream.get("license") or "")
        if re.search(r"(?<![A-Za-z])NC(?![A-Za-z])", license_text):
            notes.append("non-commercial-license")
        if not license_text:
            notes.append("license-unknown")
        missing_tools = sorted(t for t in TOOL_REQUIREMENTS.get(name, []) if not tools.get(t, shutil.which(t) is not None))
        entry = {"skill": name, "score": round(weight / max(len(capabilities), 1), 3), "matched_capabilities": matched,
                 "missing_on": missing_on, "description_chars": len(item.get("description", "")),
                 "license": license_text or None, "notes": notes,
                 "missing_tools": missing_tools, "next_action": "stage-and-review" if pinned else "pin-source-first",
                 "automatic_install": False}
        if pinned:
            entry["stage_command"] = ("python -m skillloom stage --repo {repo} --commit {ref} --path {path} "
                                      "--destination <NEW_DIRECTORY>").format(
                repo=upstream["repo"], ref=upstream["ref"], path=upstream.get("path", ""))
        recommended.append(entry)
    recommended.sort(key=lambda e: (-e["score"], e["skill"]))
    room = max(budget["active_skills"] - used_skills, 0)
    chars_room = max(budget["description_chars"] - used_chars, 0)
    for index, entry in enumerate(recommended):
        entry["within_skill_budget"] = index < room
    return {"schema": 1, "observed_at": now(), "projects_scanned": len(scans),
            "scan_truncated": any(s["truncated"] for s in scans), "signals": tags,
            "host_tools": tools, "budget_headroom": {"skills": room, "description_chars": chars_room},
            "recommended": recommended, "skipped": {k: sorted(v) for k, v in skipped.items()},
            "limits": "Marker and capability matching is a hypothesis for the first deployment, not a quality judgement. "
                      "Each candidate still needs `stage`, license/permission review and a local behaviour check. "
                      "Fixed-scope skills are excluded unless --allow-scoped. No paths, file names or manifest text exported."}
