# Skill Loom

**Evidence-driven, reversible maintenance for agent skills.**

[中文](README.md) · [Design](docs/design-and-quality.md) · [Host adapters](docs/host-adapters.md) · [Research paper](research/paper.md)

Skill Loom connects user requirements, source discovery, capability gaps,
candidate review, validation and rollback. It is a local Python toolkit and an
operating guide for Codex, Claude Code and other compatible agent harnesses.

This first release is a research and engineering prototype. It does not crawl
the whole internet, certify skill quality, train a model, or silently update a
user's environment.

## Quick start

Requires Python 3.10+. Clone the repository, create a virtual environment, then
install with `python -m pip install -e .` using that environment's interpreter.
On Windows use `.venv/Scripts/python`; on Unix use `.venv/bin/python`.

```bash
python -m skillloom demo --workdir ../skill-loom-demo-001
python -m unittest discover -s tests -v
```

The offline demo discovers a broken local reference, applies a repair, checks it,
restores the original, reapplies, and verifies a no-change run. It requires a new
directory and never deletes an earlier run.

## What is implemented

- Inspect metadata, local references and Python syntax without executing skills.
- Observe registered public source revisions and search with explicit public queries.
- Stage a skill at an immutable commit with provenance and retained license files.
- Compare editable user requirements with capabilities and curated task evidence.
- Rank evidence-graded candidates and flag portfolio overlap for review.
- Plan exact file changes, retain originals, reject drift and roll back safely.
- Check task/candidate/time-bound evidence receipts with an opt-in bounded Stop hook.
- Clean only explicitly owned reconstructible caches using reviewed exact-file plans.

The [catalog](docs/skill-catalog.md) documents 39 anonymized local skills, including
six project-specific entries; it is not a universal installation list. The
repository distributes its own small `skill-lifecycle` skill, not the referenced
third-party collections.

## Evidence and limitations

[Validation](docs/validation.md) separates software tests, deterministic fault
injection, real local deployment, native-host discovery and untested platforms.
The 12 selected fault scenarios are not an LLM-performance benchmark. No measured
task-accuracy or token-saving advantage is claimed.

The [literature matrix](research/literature-matrix.md) grounds the design in prior
work and records counterevidence. The accompanying paper is a systems technical
report, not a peer-reviewed claim of a new state-of-the-art learning algorithm.

Private profiles, raw transcripts and rollback journals stay outside the public
repository. No background monitoring, cloud service or model API is enabled.

See [contributing](CONTRIBUTING.md), [security](SECURITY.md),
[maintenance](docs/releasing-and-governance.md) and [license](LICENSE).
