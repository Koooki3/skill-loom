# Changelog

## Unreleased

No changes yet.

## 0.2.1 — 2026-10-30

Documentation PATCH: make prior adoption/defer/reject decisions reusable under
explicit source, task and environment conditions.

- Add a manual decision-history guide and two-record synthetic JSON example.
  No CLI reads or enforces the format; a successor requests review, not installation.
- Add dated local evidence, seven-source triage and two primary-paper readings.
  Preserve historical manuscript results and distinguish proposals from experiments.
- Document reopening conditions and retention of earlier evidence. No runtime
  behavior, schema, dependency, host policy or global skill changes.


## 0.2.0 — 2026-10-25

Includes the previously unreleased 14 October feature commit and merged PRs #1 and #2,
plus the weekly signal-interpretation correction. This is a MINOR release from v0.1.1.

### Observation accounting and validation

- Skip repeated paths, resolved aliases and hardlinks within each observation command.
  Export no input identity; distinct copied or overlapping files remain unresolved.
- Require one report to meet both file and elapsed-span thresholds. Do not add
  aggregates with unknown overlap or splice their date windows. Per-skill counts
  use maxima; positive signals from all reports still suppress unobserved candidates.
- Recognize Windows and mixed separators in Codex path-reference signals.
- Label Codex signals with optional `skill_signal_basis` metadata. The legacy
  `skill_md_reads` field counts syntactic tool-payload path references, including
  quoted code and failed commands; it does not verify file access or skill use.
  Existing counts, `load-signal` status and schema 1 remain compatible.
- Add a quoted-path regression and dated research/source-review supplement.
- Read linked-worktree Git metadata for recommendation markers without running Git.
- Validate catalog source repository/path fields before staging suggestions; emit
  structured argv and omit shell templates for paths with spaces or metacharacters.
  Replace the destination placeholder and pass argv without a shell.
- Add `--min-files`; retain the legacy `--min-sessions` flag and Python keyword.
  schema 1 remains readable; regenerate old reports before relying on their counts.
- Add 10 accounting tests, 6 release-interface tests and a 12-case synthetic baseline/candidate study;
  record current source/research review and claim limits. No dependencies added.

- Reject malformed `usage` inventory/observation structures, invalid counts and
  incomplete or reversed date windows with a controlled CLI error. A failed
  command leaves existing output untouched and creates no new output report.
- Add synthetic API and CLI regression coverage; valid reports and optional
  empty observation windows keep their existing behavior.

### First-deployment and host-observation commands

Driven by one real deployment and its first week of local run records (Codex and Claude Code profiles
of one user): first deployment needed hand-built profiles and hand-checked candidates, and Claude Code
had no observation path, so later updates had no usage evidence.

- `recommend`: environment-aware first-deployment queue. Scans explicit project roots for markers
  (manifests, suffix counts, GitHub remote, declared dependencies), maps them to catalog capabilities,
  reports missing host tools, license caveats, source pinning and budget headroom, and prints structured
  `stage_argv` plus a command template for shell-simple paths. Works without a profile (neutral defaults). Installs nothing; fixed-scope skills are
  excluded unless `--allow-scoped`.
- `observe-claude`: structural aggregation of Claude Code transcripts. A `Skill` tool call is a structured
  event, so per-skill call counts are exact; also subagent dispatch counts and the observed day window.
  No prompts, tool inputs, outputs or paths are exported.
- `observe-codex` now reports `skill_md_reads` (syntactic references to `skills/<name>/SKILL.md` in tool payloads) and the day window.
  This is a load signal only; audit and install work produce it too. `skill_attribution` stays `not_inferred`.
- `usage`: per-host skill status (`used`, `load-signal`, `unobserved`, `no-observation`) from host
  inventories plus observation reports. Review candidates for deactivation appear only after the evidence
  window in a single report clears `--min-files` and `--min-days`; protected skills are excluded; nothing is changed.
- A missing PyYAML now fails with an instruction instead of a traceback.
- 17 regression tests on synthetic fixtures, including the window gate and protection rules.

The 14 October maintainer-reported sample (not independently resampled this week) had a 2–3 day window with 9 Claude and 47 Codex files, below the default `usage`
thresholds, so no deactivation was proposed. Matching is a hypothesis for review, not a quality score.

## 0.1.1 — 2026-10-09

- Validate receipt objects, check IDs, artifact collections and digest fields before
  reading evidence. Malformed input produces a structured CLI error and an explicit
  unverified Stop-hook result instead of an uncaught traceback.
- Add six regression tests for malformed input, pre-read validation and entrypoints.
- Add an incremental ClaimReceipt literature note and weekly regression report.
  Valid receipt verdicts and schema 1 remain unchanged.

## 0.1.0 — 2026-10-06

- Initial local lifecycle toolkit, source discovery and pinned staging.
- User profiles, evidence-based gap/ranking/portfolio decision support.
- File-hash and mode guarded changes, interrupted recovery, rollback and bounded gates.
- Codex/Claude adapter documentation and anonymized 39-skill catalog.
- Reproducible fault-injection study, research review and technical report.
- Review-driven fixes: no-op drift checks, POSIX executable modes, cleanup pending
  intent, strict capability-list validation and evidence-reference handling;
  pinned Git blob identity/size, finite age limits and case-insensitive reserved names.

Version 0.1 remains a prototype. Model quality, broad cross-host native hooks and
multi-user hosted operation are not established by the software test suite.
