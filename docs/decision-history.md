# Keep decisions useful when conditions change

Use this guide when a later maintenance run encounters a candidate already
considered, or an old acceptance result whose environment has changed.
The [evolution playbook](evolution-playbook.md) already requires reasons for
adoption, deferral and rejection. This guide makes the conditions for reusing
those reasons explicit.

Copy the [synthetic example](../examples/decision-history.example.json) into
private maintenance storage and adapt it. This is a **manual record convention**,
not a CLI input, JSON schema migration, automatic gate or background service.
No Skill Loom command loads, validates or enforces these records.

## Before repeating a decision

Find only records relevant to the current task, candidate and host. Compare the
reviewed source commit, local patch or artifact digest, task contract, host/tool
versions and evidence scope. An unchanged GitHub head alone does not establish
that the local environment or task is unchanged. Unknown versions remain unknown.

| Current observation | Next action |
|---|---|
| Same candidate, task and applicable evidence; prior reason still holds | Retain the decision and reference it; avoid repeating installation or notification |
| Relevant upstream fix, changed tool interface, changed task contract or validated counterexample | Open a new review linked to the old decision; state what changed |
| Previously passing test targets a retired API or no longer matches the task | Preserve its historical result; mark present applicability unknown and obtain a current probe |
| No new evidence and insufficient task coverage | Defer; do not infer that an unobserved skill is unnecessary |

A different commit is a reason to inspect the relevant diff, not permission to
install it. A new paper is a source to evaluate, not evidence of local benefit.
If a previous rejection concerned missing tools, a successful installation alone
still does not establish task correctness.

## Minimal record and handoff

Record a stable decision ID, predecessor if any, candidate identity, task and
environment scope, evidence references and their status, decision, reason,
protected constraints, and concrete conditions for reopening. Evidence references
should resolve within private storage; do not embed credentials or raw transcripts.
Use null for an unknown outcome, rather than inventing a successful or zero result.

Keep the original record and evidence. Add a successor when the decision or its
basis changes, explaining which earlier conclusion remains applicable. A record
link is an audit aid, not a signature or proof that its statements are true.
Do not place private records in a skill discovery root or publish them unchanged.

For a consequential candidate, give an independent reviewer the scoped patch,
task contract and necessary evidence. For model-task evaluation, keep held-out
targets away from the candidate author; a fresh reviewer sharing all files is
not an enforced permission boundary. Use the smallest useful team. Nothing in
this convention expands tool access or changes host approval policy.

After a review, use existing `plan`, reviewed digest, `apply`, verification and
`rollback` procedures when an authorized skill change is warranted. A decision
record does not replace a transaction journal or authorize a mutation.

## Read the example as a scenario

Both records are synthetic and all task outcomes are unknown. The first defers
a candidate because no applicable probe has run. The successor records a changed
tool interface and requests review; it does not approve installation. Check that
the predecessor exists and the new record retains the old evidence without
relabelling it as a current pass. This is an illustrative walkthrough, not a
tested decision engine or a measured reduction in repeated work.

## Research basis and remaining work

The [dated research supplement](../research/weekly-2026-10-30.md) compares two
primary papers and distinguishes their results from this project's guidance.
The convention above is an engineering proposal. Its usefulness across users,
models and repeated maintenance runs remains unmeasured.
