# Research artifact

- [Manuscript](paper.md): editable, numbered-source systems technical report.
- [Reading PDF](paper.pdf): generated from the manuscript with ReportLab; not a TeX-compiled PDF.
- [Standalone LaTeX source](paper.tex): generated from Markdown with Pandoc. The local app compiler could not initialize its platform directories, so TeX compilation is unverified.
- [Literature matrix](literature-matrix.md) and [machine-readable sources](references.json): fifteen version-pinned primary papers, reading locations, implications and counterevidence.
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
