# Research artifact

- [Manuscript](paper.md): editable, numbered-source systems technical report.
- [Reading PDF](paper.pdf): generated from the manuscript with ReportLab; not a TeX-compiled PDF.
- [Standalone LaTeX source](paper.tex): generated from Markdown with Pandoc. The local app compiler could not initialize its platform directories, so TeX compilation is unverified.
- [Literature matrix](literature-matrix.md) and [machine-readable sources](references.json): the original fifteen version-pinned papers plus dated incremental papers/specifications, reading locations, implications and counterevidence.
- [Engineering evidence](engineering-evidence.md): official engineering material and technical-debt literature.
- [Executed deterministic study](results/invariants.json) and [anonymized local case](results/local-cycle.anonymized.json).
- [Proposed behavioral protocol](evaluation-protocol.md): future model-task experiments; no claimed results.

This is a version 0.1 technical report, not a peer-reviewed publication or proof of novel learning methods. The selected fault scenarios support software contracts only. The reading PDF has been inspected for layout and equation fidelity; the editable Markdown is the content source of truth.

## Rebuild

From the repository root, with the project dependencies installed:

```bash
python scripts/benchmark_invariants.py
```

The command rewrites the result JSON. To regenerate charts, separately install `matplotlib` in your artifact environment and run `python scripts/render_assets.py`.

The standalone TeX source was produced using an existing Pandoc installation:

```bash
pandoc research/paper.md --standalone --from=markdown+autolink_bare_uris --to=latex --shift-heading-level-by=-1 --variable=geometry:margin=1in --variable=fontsize:11pt --variable=colorlinks:true --output=research/paper.tex
```

For the reading PDF, separately install `reportlab` and run `python scripts/render_paper.py`. This small renderer supports the manuscript's present constructs and checks for a serif font with Greek glyphs. It is not a general Markdown renderer; adding equations requires updating and visually checking that path. Artifact-generation libraries and Pandoc are optional, not dependencies of the runtime CLI. Keep source and derived documents synchronized when changing the manuscript.

## Patch supplements

[Receipt-validation regression report](weekly-2026-10-09.md) records v0.1.1.
The source register includes dated incremental sources in addition to the original fifteen; source kinds and version limits are explicit.
The original manuscript/PDF retains its 2026-10-06 scope and results.

[Observation identity and review-coverage supplement](weekly-2026-10-16.md) records v0.2.0, its [synthetic comparison](results/observation-coverage.json), and upstream review. It adds one recent preprint and three primary specifications; the historical manuscript and derived documents are unchanged.

[Path-signal interpretation and research supplement](weekly-2026-10-23.md) records the 23 October run, resumed on 25 October, and its quoted-path regression. Two versioned papers are added to the reference register; neither is reproduced. The original manuscript/PDF/TeX remains historical.

[Decision-history supplement](weekly-2026-10-30.md) adds a manual handoff example and two primary papers (R23–R24). It records a new bounded local sample and source triage; no paper is reproduced and no runtime history service is implemented. The historical manuscript/PDF/TeX is unchanged.
