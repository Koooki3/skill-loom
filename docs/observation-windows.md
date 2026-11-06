# Observe a declared time interval

Version 0.3.0 adds optional time selection to both structural observers. Select
the input files yourself; no background collection or global transcript search runs.

~~~bash
python -m skillloom observe-codex --log examples/observation-window.codex.jsonl --since 2026-10-30T00:00:00Z --until 2026-11-06T00:00:00Z --out ../loom-state/week-codex.json
python -m skillloom observe-claude --log examples/observation-window.claude.jsonl --since 2026-10-30T00:00:00Z --until 2026-11-06T00:00:00Z --out ../loom-state/week-claude.json
~~~

These files are wholly synthetic. Each command selects one tool record at the
inclusive upper endpoint. The record equal to the lower endpoint is excluded.
The examples do not demonstrate actual skill loading or a successful task.

| Contract | Behavior |
|---|---|
| Bounds | Optional, independently usable; since is exclusive, until inclusive |
| Timestamp syntax | YYYY-MM-DDTHH:MM:SS, optional 1–6 fractional digits, followed by Z or +/-HH:MM |
| Comparison | UTC instants, regardless of input order or offset; filtered calendar days use UTC |
| Missing/invalid record timestamp | Skip and count under record_selection.untimed_records_skipped |
| Invalid bound or since >= until | Reject before reading inputs or writing output |
| file_count when filtered | Distinct input files with at least one matching timestamped JSON object |
| selected_file_count | All distinct selected files, including those with no matches |
| Cumulative Codex tokens | reported_total_tokens_sum=null and files_with_usage=0 in filtered mode |
| No options | Previous full-file behavior and report shape; no record_selection field |

A matching object need not contain a recognized host event. Record matching is
a temporal selection, not evidence of a skill invocation. Non-object JSON values
are ignored; malformed JSON counts describe the whole input scan because no
timestamp can be recovered reliably. Reports omit raw contents and input paths.

This still scans the full selected file. It is not an incremental byte cursor,
a fixed snapshot of a growing file, logical-event deduplication, continuous
capture or a throughput improvement. Timestamps beyond microsecond precision
are unsupported in filtered mode and remain counted as untimed. UTC days may
differ from the original local calendar day; bounds themselves do not establish
observed coverage.

Keep the previous private report. For adjacent intervals (a,b] and (b,c], the
boundary b is included once; overlapping intervals can still duplicate events.
The usage command retains its conservative per-report coverage and maximum
aggregation rules. Files without matching objects cannot inflate its coverage.
One conversation does not become multiple independent trials when split by week.

Do not subtract cumulative host counters and call the result interval cost:
resets, compaction, source changes and missing events need an explicit measurement
contract. Python's [aware datetime rules](https://docs.python.org/3.10/library/datetime.html#aware-and-naive-objects)
supply instant comparison; they do not establish capture completeness.

To downgrade, preserve both reports and return to v0.2.1 in a separate
environment. Remove --since/--until from old CLI invocations. Schema remains 1;
record_selection is optional. Old usage readers can consume the existing host,
file_count, skill table and window fields while ignoring the new metadata.
