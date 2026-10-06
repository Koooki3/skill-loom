"""Check public examples, local Markdown targets and obvious private artifacts."""

import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from skillloom.inventory import inventory, without_fences
from skillloom.strategy import gap_analysis, portfolio, rank, validate_profile


def check(root):
    errors = []
    profile = json.loads((root / "examples/user-profile.json").read_text(encoding="utf-8"))
    catalog = json.loads((root / "catalog/local-skills.example.json").read_text(encoding="utf-8"))
    validate_profile(profile)
    portfolio(profile, catalog)
    gap_analysis(profile, catalog, json.loads((root / "examples/observations.json").read_text(encoding="utf-8")))
    rank(profile, json.loads((root / "examples/candidates.json").read_text(encoding="utf-8")))
    report = inventory([root / "skills"])
    if report["error_count"]:
        errors.append("Bundled skill static validation failed")
    files = [p for p in root.rglob("*") if p.is_file() and not any(x in {".git", ".venv", "__pycache__", "build", "dist"} or x.endswith(".egg-info") for x in p.relative_to(root).parts)]
    for path in files:
        relative = path.relative_to(root).as_posix()
        if path.name in {"auth.json", "config.toml", ".env", "transaction.json"} or path.name.startswith("rollout-"):
            errors.append(f"Private/runtime artifact: {relative}")
        if path.suffix in {".json", ".md", ".py", ".yml", ".toml", ".tex", ".bib", ".svg"}:
            text = path.read_text(encoding="utf-8-sig")
            if re.search(r"[A-Z]:[/\\]Users[/\\][A-Za-z0-9][^/\\\s]*[/\\]", text):
                errors.append(f"Personal absolute path: {relative}")
            if re.search(r"(?:gh[pousr]_[A-Za-z0-9]{30,}|sk-proj-[A-Za-z0-9_-]{30,})", text):
                errors.append(f"Potential secret: {relative}")
            if path.suffix == ".json":
                json.loads(text)
            if path.suffix == ".md":
                body = without_fences(text)
                for target in re.findall(r"\[[^\]\n]*\]\(([^)\n]+)\)", body):
                    target = target.strip().strip("<>")
                    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("#") or any(c in target for c in "<>{}"):
                        continue
                    target = unquote(target.split("#")[0])
                    if target and not (path.parent / target).exists():
                        errors.append(f"Broken link: {relative} -> {target}")
    for required in ("README.md", "README.en.md", "LICENSE", "docs/design-and-quality.md", "research/paper.md"):
        if not (root / required).is_file():
            errors.append(f"Missing release artifact: {required}")
    return {"files_checked": len(files), "errors": errors, "status": "pass" if not errors else "fail",
            "limits": "Targeted checks, not a full secret scanner, license audit or external-link verifier."}


if __name__ == "__main__":
    result = check(Path(__file__).resolve().parents[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["status"] == "pass" else 1)
