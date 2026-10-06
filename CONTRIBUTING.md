# Contributing

Start with a reproducible task or failure, not a larger skill count. Describe the
expected output, environment, observed behavior, and a minimal anonymized fixture.
Do not upload raw agent transcripts, personal paths, credentials or private data.

Run `python -m unittest discover -s tests -v` and
`python scripts/check_release.py`. Use an isolated directory for the demo.
Changes to transaction semantics need drift, interruption and rollback coverage.
Document untested hosts explicitly. Keep deterministic checks separate from
model-quality claims and preserve users' local customizations.

For upstream skill suggestions, provide the repository, exact skill path,
commit, license, task fit, dependencies and known limitations. This project does
not redistribute the referenced third-party skill collections.
