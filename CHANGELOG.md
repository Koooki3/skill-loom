# Changelog

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
