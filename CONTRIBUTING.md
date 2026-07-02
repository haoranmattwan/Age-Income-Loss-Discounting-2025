# Contributing

Contributions should improve reproducibility, clarity, accessibility, or software reliability while preserving a clear distinction between the published analysis and any new exploratory work.

## Before contributing

1. Open an issue describing the proposed change and its scientific or technical rationale.
2. Do not upload participant-level data, Qualtrics exports, correspondence, unpublished drafts, or other private research materials.
3. Keep the R and Python data transformations aligned. If a model specification changes, document whether the change reproduces the article, corrects an implementation error, or constitutes a new sensitivity analysis.
4. Add or update a focused test when changing reusable Python functions.
5. Render affected documents and inspect warnings, model diagnostics, tables, and figures before submitting a pull request.

## Reporting standards

- State the analysis sample and missing-data rule.
- Define transformations and coding explicitly.
- Report model family, fixed and random effects, priors, sampling settings, and convergence diagnostics.
- Label analyses not reported in the article as extensions or sensitivity analyses.
- Avoid causal language for cross-sectional associations.

## Local checks

```bash
python -m unittest discover -s tests -v
quarto render Analysis/analysis_R.qmd --execute=false
```

Full Bayesian refits are not required for documentation-only changes, but changes to model code should be checked with short development runs before using the published sampling schedule.
