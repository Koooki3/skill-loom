"""Static skill inspection; links at discovery roots are observed, never mutated."""

import ast
from collections import Counter
from pathlib import Path
import re
from urllib.parse import unquote
import yaml

from .common import digest, now, valid_name, is_link


def without_fences(text):
    fence = None
    kept = []
    for line in text.splitlines():
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            continue
        if fence is None:
            kept.append(line)
    return "\n".join(kept)


def inspect_skill(folder):
    folder = Path(folder)
    result = {"name": folder.name, "directory": str(folder), "physical_directory": str(folder.resolve()),
              "linked": is_link(folder), "errors": [], "warnings": [], "python_files": 0,
              "markdown_links": 0, "description_chars": 0}
    try:
        raw = (folder / "SKILL.md").read_bytes()
        text = raw.decode("utf-8-sig")
        match = re.match(r"\A---\s*\r?\n(.*?)\r?\n---(?:\s*\r?\n|$)", text, re.S)
        if not match:
            raise ValueError("Missing frontmatter")
        meta = yaml.safe_load(match.group(1))
        if not isinstance(meta, dict):
            raise ValueError("Frontmatter must be a mapping")
        name, description = meta.get("name"), meta.get("description")
        if not valid_name(name) or name != folder.name:
            result["errors"].append("Invalid name or name/directory mismatch")
        if not isinstance(description, str) or not description.strip() or len(description) > 1024:
            result["errors"].append("Description must be nonempty text of at most 1024 characters")
        result.update(name=name if isinstance(name, str) else folder.name,
                      description=description if isinstance(description, str) else "",
                      description_chars=len(description) if isinstance(description, str) else 0,
                      skill_sha256=digest(raw))
        # Do not traverse nested junctions or execute Python imports.
        import os
        for parent, dirs, files in os.walk(folder, followlinks=False):
            for name in list(dirs):
                if name in {".git", ".venv", "node_modules", "__pycache__"}:
                    dirs.remove(name)
                elif is_link(Path(parent) / name):
                    dirs.remove(name)
                    result["warnings"].append("Nested linked directory not inspected")
            for name in files:
                path = Path(parent) / name
                if is_link(path):
                    result["warnings"].append("Linked file not inspected")
                    continue
                if path.suffix == ".py":
                    try:
                        ast.parse(path.read_text(encoding="utf-8-sig"))
                        result["python_files"] += 1
                    except (SyntaxError, UnicodeError) as exc:
                        result["errors"].append(f"Python syntax: {path.relative_to(folder)}: {type(exc).__name__}")
                if path.suffix == ".md":
                    body = without_fences(path.read_text(encoding="utf-8-sig"))
                    for target in re.findall(r"\[[^\]\n]*\]\(([^)\n]+)\)", body):
                        target = target.strip().strip("<>")
                        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("#"):
                            continue
                        if any(ch in target for ch in "{}<>"):
                            continue
                        target = unquote(target.split("#")[0].split(' "')[0])
                        if target:
                            result["markdown_links"] += 1
                            if not (path.parent / target).exists():
                                result["errors"].append(f"Missing local link: {path.relative_to(folder)} -> {target}")
        ui_file = folder / "agents" / "openai.yaml"
        if ui_file.exists():
            ui = yaml.safe_load(ui_file.read_text(encoding="utf-8-sig"))
            if not isinstance(ui, dict):
                raise ValueError("openai.yaml must be a mapping")
            result["invocation_policy"] = ui.get("policy", {})
    except (OSError, ValueError, TypeError, UnicodeError, yaml.YAMLError) as exc:
        result["errors"].append(f"{type(exc).__name__}: {exc}")
    return result


def inventory(roots):
    skills, missing = [], []
    for root in map(Path, roots):
        if not root.is_dir():
            missing.append(str(root))
            continue
        skills.extend(inspect_skill(path) for path in sorted(root.iterdir())
                      if not path.name.startswith(".") and (path / "SKILL.md").is_file())
    counts = Counter(s["name"] for s in skills)
    duplicates = {name: count for name, count in counts.items() if count > 1}
    return {"schema": 1, "observed_at": now(), "roots": list(map(str, roots)),
            "skill_count": len(skills), "error_count": sum(len(s["errors"]) for s in skills) + len(missing) + len(duplicates),
            "warning_count": sum(len(s["warnings"]) for s in skills), "missing_roots": missing,
            "duplicate_names": duplicates, "description_chars": sum(s["description_chars"] for s in skills),
            "skills": skills, "limits": "Static inspection only. No behavioral, runtime-discovery, or service guarantee."}
