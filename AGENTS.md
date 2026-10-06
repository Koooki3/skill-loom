# Working on Skill Loom

Use the smallest effective agent team. Assign one writer per file or module.
Keep mutations explicit, scoped, hash-guarded and recoverable. Read-only commands
must not execute skill code. Never add automatic host-policy changes, implicit
network installation, credential harvesting, or unbounded repair loops.

Run `python -m unittest discover -s tests -v` for functional changes and
`python scripts/check_release.py` before publishing. Update affected CLI examples
and evidence limitations. Use fixtures for destructive/error paths.

Keep raw logs, machine paths, credentials, local plans and raw runtime snapshots
out of commits. Public examples must be anonymized; label synthetic fixtures and
curated real-case summaries separately so neither is mistaken for the other.
Do not claim task-quality or token improvements from metadata size alone.
