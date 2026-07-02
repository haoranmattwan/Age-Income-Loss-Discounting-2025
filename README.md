# Age, Income, and the Discounting of Delayed Monetary Losses

[![DOI](https://img.shields.io/badge/DOI-10.1093%2Fgeronb%2Fgbaf162-1f6feb)](https://doi.org/10.1093/geronb/gbaf162)
[![License: MIT](https://img.shields.io/badge/code%20license-MIT-2ea44f)](LICENSE)

Reproducible R and Python workflows for the analyses reported in:

> Wan, H., Myerson, J., Green, L., Strube, M. J., & Hale, S. (2025). Age, income, and the discounting of delayed monetary losses. *The Journals of Gerontology, Series B: Psychological Sciences and Social Sciences, 80*(11), gbaf162. https://doi.org/10.1093/geronb/gbaf162

## Study overview

The study examined how age and household income relate to delay discounting of monetary losses. A US sample of 594 adults aged 20-80 completed an adjusting-amount task with losses of $150, $2,500, and $30,000 at delays from 1 month to 10 years. Discounting was summarized as area under the curve (AuC) and analyzed with Bayesian multilevel beta regressions.

The published results showed that:

- older adults discounted delayed losses less steeply than younger adults;
- income was unrelated to discounting among adults younger than 35, but higher income predicted shallower discounting among adults aged 35-80;
- the age association was nonlinear and weakened at older ages; and
- age differences were larger for larger delayed losses.

These are cross-sectional associations. The analyses do not establish within-person aging effects or causal effects of income.

## Data access

Participant-level data are not stored in this repository. Download **Supplementary Data** from the [publisher's article page](https://academic.oup.com/psychsocgerontology/article/80/11/gbaf162/8249241#supplementary-data), retain the workbook name `Supplementary Data.xlsx`, and place it in `Analysis/`.

The expected workbook contains:

- `Variable Definition`: variable names and coding; and
- `Data`: 8,910 observations from 594 participants, with three loss amounts and five delays per participant.

Do not commit the workbook or derivative participant-level files. The repository's `.gitignore` is configured to keep data and other private research materials local.

## Reproduce the analyses

### R

The R workflow is the authoritative computational reproduction of the published analysis.

```bash
R -q -e 'install.packages("renv"); renv::restore()'
quarto render Analysis/analysis_R.qmd
```

Bayesian model fitting is disabled by default because it is computationally intensive. To refit the models:

```bash
quarto render Analysis/analysis_R.qmd -P fit_models:true -P run_power:true
```

The prospective power analysis uses 5,000 simulated data sets. It can be enabled independently with `-P run_power:true`.

### Python

The Python workflow is an independent implementation of the published Bayesian models, including the participant random intercepts and the random slope for log amount in Model 4.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python Analysis/analysis_Py.py
```

Use `--skip-figures` for a validation-only run on systems without a graphical stack.

To fit all Bayesian models with the published sampling schedule:

```bash
python Analysis/analysis_Py.py --fit-models
```

The companion notebook, `Analysis/analysis_Py.ipynb`, provides an interactive route through the same functions. See [`Analysis/README.md`](Analysis/README.md) for model specifications, outputs, and expected run behavior.

## Repository structure

| Path | Purpose |
| --- | --- |
| `Analysis/analysis_R.qmd` | R reproduction of data preparation, descriptive analyses, power analysis, Bayesian models, contrasts, and figures |
| `Analysis/analysis_Py.py` | Testable Python implementation of data preparation, descriptive analyses, and Bayesian models |
| `Analysis/analysis_Py.ipynb` | Interactive Python walkthrough |
| `Figure/` | Published figure files retained in the historical repository |
| `renv.lock` | R dependency lockfile |
| `requirements.txt` | Minimal direct Python dependencies |
| `CITATION.cff` | Machine-readable citation metadata |

## Reproducibility notes

- Continuous predictors are centered at their analysis-sample means and divided by two standard deviations; gender is grand-mean centered.
- Monetary amount is analyzed on the natural-log scale.
- AuC values equal to 0 or 1 are moved to the nearest representable value inside `(0, 1)` for beta regression.
- Bayesian models use four chains, 4,000 iterations per chain, a 2,000-iteration warmup, Cauchy(0, 2.5) coefficient priors, half-Cauchy(0, 2.5) group-level standard-deviation priors, and effectively flat priors for the intercept and precision, matching the article and original analysis code.
- Posterior inferences are summarized by the median, posterior standard deviation, and probability of direction (`pd`); the article treated `pd > .975` as statistically significant.
- Random seeds make the workflows auditable, but posterior draws can differ slightly across operating systems and Stan/PyMC versions.

## Open-science scope

The study design, hypotheses, and analytic plan were not preregistered, as disclosed in the article. This repository supports computational transparency for the published analyses; it is not a preregistration. The participant data are distributed by the publisher as article supplementary material.

## License and citation

Code in this repository is available under the [MIT License](LICENSE). The article, supplementary data, and published figures remain subject to their respective publisher and author terms. Cite the article above when using the study or data; cite this repository additionally when using the code.

Contributions that improve reproducibility without changing the published estimand are welcome; see [`CONTRIBUTING.md`](CONTRIBUTING.md).
