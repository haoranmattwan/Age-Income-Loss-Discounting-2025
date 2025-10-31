# Age, Income, and the Discounting of Delayed Monetary Losses

This repository contains the analysis scripts, figures, and presentation materials for the peer-reviewed publication:

> Wan, H., Myerson, J., Green, L., Strube, M. J., & Hale, S. (2025). Age, income, and the discounting of delayed monetary losses. *The Journals of Gerontology, Series B: Psychological Sciences and Social Sciences, 80*(11), gbaf162. https://doi.org/10.1093/geronb/gbaf162

The data for this study are available in the Supplementary Material at the publisher's website.

---

## Project Overview

This study examined the effects of age and income on the discounting of delayed monetary losses, testing a "buffering hypothesis" which posits that age-related psychological factors may buffer against the stress of financial scarcity. The study used a wide range of loss amounts (\$150, \$2,500, and \$30,000) and a large, diverse sample of adults aged 20 to 80.

The analysis workflow begins with a simulation-based power analysis to determine the required sample size. The primary analysis then uses a series of Bayesian multilevel beta regressions to model the Area under the Curve (AuC) as the key measure of discounting. These models test for linear and nonlinear effects of age, as well as interactions between age, income, and the amount of the loss.

## Repository Structure

| File / Folder | Description |
| :--- | :--- |
| **`/Analysis/`** | Contains the primary scripts that replicate all findings in the paper. |
| `analysis.qmd` | A Quarto document with the complete **R** workflow, using `brms` for Bayesian modeling. |
| `analysis.ipynb` | A Jupyter Notebook providing a **Python** translation of the analysis, using `pymc` for modeling. |
| **`/Presentation/`** | Contains the poster that was presented at DACC. |
| **`/Figure/`** | All figures as they appear in the final publication. |

---

## Methodological Approach

The analysis follows a comprehensive workflow, from initial power analysis to final model validation.

* **Simulation-Based Power Analysis**: Prior to data collection, a custom R function was written to simulate data (`glmmTMB`) and conduct a power analysis to determine the required sample size for detecting key interaction effects within a multilevel beta regression framework.
* **Data Validation and Reliability**: Initial analyses included fitting nonlinear hyperboloid functions to group-level data to ensure data quality and calculating Cronbach's alpha to check the internal consistency of the discounting measure.
* **Bayesian Hierarchical Modeling**: The primary analysis used Bayesian multilevel beta regression to appropriately model the proportional Area under the Curve (AuC) data while accounting for repeated measures within participants. The models tested for both linear and nonlinear (quadratic) effects of age and examined two-way interactions between age, income, loss amount, and other variables to test the study's hypotheses.
* **Cross-Platform Validation**: To ensure the robustness of the findings, the entire Bayesian multilevel model was replicated from R (`brms`) into Python (`pymc`), confirming that the model specification and results were consistent across statistical ecosystems.

---

## Software and Execution

To run the analyses, you will need the appropriate software environment and the raw data file (e.g., `Lifespan.csv`) from the publication's supplementary material.

### R Environment (`/Analysis/analysis_R.qmd`)

* **Required Packages**: `brms`, `cmdstanr`, `tidyverse` (includes `readr`, `dplyr`, `ggplot2`), `glmmTMB`, `tidybayes`, `psych`, `Hmisc`, `multcomp`, `minpack.lm`, `doSNOW`, `here`, `modelr`, `ggpubr`, `bayestestR`.
* **Installation**:
    ```R
    # Install main packages
    install.packages(c("brms", "tidyverse", "glmmTMB", "tidybayes", "psych", 
                       "Hmisc", "multcomp", "minpack.lm", "doSNOW", "here", 
                       "modelr", "ggpubr", "bayestestR"))
    
    # brms requires a working Stan installation via cmdstanr
    install.packages("cmdstanr", repos = c("[https://mc-stan.org/r-packages/](https://mc-stan.org/r-packages/)", getOption("repos")))
    cmdstanr::install_cmdstan()
    ```

### Python Environment (`/Analysis/analysis_Py.ipynb`)

* **Required Packages**: `pandas`, `numpy`, `scipy`, `statsmodels`, `pymc`, `arviz`, `matplotlib`, `seaborn`, `pingouin`, `patsy`.
* **Installation**:
    ```bash
    pip install pandas numpy scipy statsmodels pymc arviz matplotlib seaborn pingouin patsy
    ```