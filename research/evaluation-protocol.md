# Behavioral evaluation protocol — proposed, not executed

The shipped deterministic experiment tests software contracts. This protocol describes the separate evidence needed to claim that a skill revision improves task outcomes. Do not replace missing runs with simulated model scores.

## Question and registered scope

Choose one user task family and one proposed change. State the failure it should fix, current skill and candidate content hashes, model identifier, host and harness versions, tools, permissions, external services, output contract, budget and grader. Record an expected benefit and an unacceptable regression before selecting candidates.

Compare **no skill**, **stable skill**, and **candidate skill** under equal available budgets and matched inputs. A baseline that removes required tools is not a fair no-skill baseline. Preserve baseline instructions that represent user authorization or mandatory domain constraints.

## Units, split and execution

The task is the primary unit; multiple trials of the same task are clustered repeats, not independent tasks. Keep development/selection tasks separate from a frozen evaluation set, including positive triggers, adjacent negative triggers, regressions and difficult source or environment cases. Determine counts from the question, pilot variability and affordable budget; there is no universal valid small sample count.

Randomize or counterbalance execution order, reset workspace state and keep task inputs unchanged. Archive all attempts, timeouts and refusals. For external nondeterminism record timestamps and service changes. Report unavailable evidence instead of silently excluding it. Agent reviewers should not see condition labels when the artifact can be assessed blind.

## Grading and cost

Use executable tests where suitable, source checks for factual work, render inspection for visual documents and human judgment for qualities not covered by deterministic checks. Calibrate model graders on human-checked examples and preserve disagreements. Skill selection, unnecessary invocations and constraint adherence are process measures; artifact success and fidelity are outcome measures.

Measure end-to-end wall time, total input/output usage across the whole agent tree, retries, integration rework and human corrections. Do not report only the main agent's token count. Provider cost depends on actual billing rules and cached/reasoning usage; cumulative session usage must not be relabeled as per-task spend.

Report per-task outcomes and paired differences. Estimate uncertainty only with justified units and sampling assumptions; account for task clustering when using repeated trials. State exclusions, stopping rules and multiplicity handling before examining final results. Avoid significance claims when the sample is a convenience collection too small for the target inference.

## Multi-round and portfolio experiments

Use fixed total search/evaluation budgets when comparing iteration strategies. Record every proposal, rejection, no-change, promotion and rollback; the best intermediate candidate must be chosen using selection data, not the frozen test set. Run negative-trigger and protected-constraint checks after merge/prune operations. Changing model or harness creates a new transfer test rather than inheriting the old result.

Stop or retain the current version when evidence is insufficient, regressions exceed the task contract, the budget is exhausted or independent checks cannot resolve a failure. More rounds are allowed when a concrete unresolved hypothesis and a useful discriminating test remain.

## Publication record

Publish anonymized task definitions or explain access limits, exact code/skill commits, environment, graders, exclusions, all aggregate results and representative failures. Keep raw private traces out of public artifacts. Separate observed data, grader decisions and author interpretation. Planned experiments stay labeled planned in the manuscript, README and release notes.
