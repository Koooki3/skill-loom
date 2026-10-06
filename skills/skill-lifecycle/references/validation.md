# Validation and rollout

Before editing, keep the installed file hashes, original bytes, source commit and local intent. Work in a separate candidate directory. Define one realistic positive task, one adjacent negative task, a regression task for the observed failure, and a held-out task when behavior changes materially.

Static metadata, local-link and script-syntax checks do not execute the skill. Host discovery does not prove that scripts, services or UI flows work. Record these evidence levels separately; leave missing services unverified.

Review the exact change set and acceptance evidence, then use a hash-guarded transaction. Reject a changed source or installation rather than overwriting new work. Keep rollback files outside the discovery directory. Test rollback on an isolated fixture, and on a live change only when authorized and the current files still match the transaction.

For broad changes, use an independent reviewer with the task inputs rather than telling it the intended answer. Measure total quality, latency and cost, including child-agent and integration work. Character-count reductions are not measured token savings.

Retire only with evidence that the capability is unneeded or superseded, after checking references. Keep recoverable records; do not remove a skill merely because the available log sample did not mention it.
