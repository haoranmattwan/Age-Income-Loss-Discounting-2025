# Analysis guide

This directory contains two implementations of the published analysis. The R workflow follows the software stack used for the article. The Python workflow independently expresses the same central Bayesian models for cross-platform verification.

## Input

Download the article's `Supplementary Data.xlsx` workbook from the [publisher's supplementary-material section](https://academic.oup.com/psychsocgerontology/article/80/11/gbaf162/8249241#supplementary-data) and save it here:

```text
Analysis/Supplementary Data.xlsx
```

Both workflows validate the expected columns, 594 participant identifiers, three monetary amounts, five delays, and 15 observations per participant before analysis.

## Published model sequence

All outcomes are participant-by-amount AuCs in `(0, 1)`. Continuous predictors are centered and divided by two sample standard deviations within the complete-case sample for each model.

| Model | Analysis sample | Fixed effects | Group-level effects |
| --- | --- | --- | --- |
| 1 | Age 35-80 | Age, Age² | Participant intercept |
| 2 | Age 35-80 with income | Model 1 + income | Participant intercept |
| 3 | Complete income and HADS data | Model 2 + anxiety | Participant intercept |
| 4 | Complete covariate data | All pairwise interactions among age, income, anxiety, log amount, education, gender, and health; plus Age² | Correlated participant intercept and log-amount slope |

The article's Table 3 displays the Model 4 main effects and age interactions. The complete pairwise-interaction output corresponds to Supplementary Table 2.

Supplementary models replace anxiety with depression or total HADS distress.

## R workflow

`analysis_R.qmd` contains:

1. input validation and AuC construction;
2. descriptive and correlational checks;
3. the prospective simulation-based power analysis;
4. the published Bayesian model sequence;
5. posterior summaries and model diagnostics; and
6. population-level predictions for the principal figures.

Model fitting and the 5,000-replication power analysis are opt-in parameters. Cached R model objects are written below `Analysis/cache/` and are ignored by Git.

## Python workflow

`analysis_Py.py` is the reviewable, testable source. `analysis_Py.ipynb` is an interactive walkthrough that imports the script rather than duplicating model logic.

The Python port uses the same beta likelihood, logit link, fixed-effects design, coefficient priors, participant intercepts, and Model 4 participant amount slope. PyMC and Stan use different samplers and parameterizations, so posterior draws should agree substantively rather than bit-for-bit.

The published power analysis is intentionally not approximated in Python: a binomial GLM is not an adequate substitute for the beta mixed models used in the article. Use the R workflow to reproduce that analysis.

## Generated files

Generated figures, tables, fitted models, notebook assets, and rendered reports are written below ignored output/cache directories. Source data and generated results should remain local; only source code, documentation, and dependency specifications belong in version control.

## Diagnostic expectations

Before interpreting a Bayesian refit, confirm:

- no divergent transitions;
- split R-hat below 1.01;
- adequate bulk and tail effective sample sizes;
- stable trace plots; and
- posterior predictive behavior compatible with the observed AuC distribution.

Failure of these checks should be reported and resolved rather than suppressed.
