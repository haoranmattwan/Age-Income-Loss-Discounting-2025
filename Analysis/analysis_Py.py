"""Reproduce the analyses for Wan et al. (2025) in Python.

The R workflow is the authoritative reproduction of the published analysis. This
module provides a transparent, testable Python implementation of the data
preparation, descriptive results, and Bayesian multilevel beta regressions.

Run without model fitting:
    python Analysis/analysis_Py.py

Refit the published Bayesian model sequence:
    python Analysis/analysis_Py.py --fit-models
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


ARTICLE_URL = "https://doi.org/10.1093/geronb/gbaf162"
EXPECTED_COLUMNS = {
    "ID",
    "Age",
    "Income",
    "Education",
    "Gender",
    "Anxiety",
    "Depression",
    "Distress",
    "Health",
    "Ethnicity",
    "Race",
    "Amount",
    "Delay",
    "RSV",
}
EXPECTED_AMOUNTS = {150, 2_500, 30_000}
EXPECTED_DELAYS = {1, 3, 12, 36, 120}
RANDOM_SEED = 20_250_908


@dataclass(frozen=True)
class ModelSpec:
    """Fixed- and group-level specification for one published model."""

    name: str
    formula: str
    data_key: str
    random_amount_slope: bool = False


MODEL_SPECS = (
    ModelSpec("model_1", "Age_std + I(Age_std ** 2)", "model_1"),
    ModelSpec(
        "model_2",
        "Age_std + I(Age_std ** 2) + Income_std",
        "model_2",
    ),
    ModelSpec(
        "model_3",
        "Age_std + I(Age_std ** 2) + Income_std + Anxiety_std",
        "model_3",
    ),
    ModelSpec(
        "model_4",
        "(Age_std + Income_std + Anxiety_std + Amount_std + Education_std + "
        "Gender_c + Health_std) ** 2 + I(Age_std ** 2)",
        "model_4",
        random_amount_slope=True,
    ),
)


def two_sd_scale(values: pd.Series) -> pd.Series:
    """Center a numeric variable and divide by two sample standard deviations."""

    numeric = pd.to_numeric(values, errors="raise").astype(float)
    scale = 2 * numeric.std(ddof=1)
    if not np.isfinite(scale) or scale == 0:
        raise ValueError(f"Cannot scale {values.name!r}: zero or undefined variance.")
    return (numeric - numeric.mean()) / scale


def hyperboloid(delay: np.ndarray, k: float, s: float) -> np.ndarray:
    """Hyperboloid discounting function RSV = 1 / (1 + kD)^s."""

    return 1 / np.power(1 + k * delay, s)


def validate_raw_data(data: pd.DataFrame) -> None:
    """Fail early when the supplementary workbook does not match the article."""

    missing = EXPECTED_COLUMNS.difference(data.columns)
    if missing:
        raise ValueError(f"Supplementary data are missing columns: {sorted(missing)}")

    observed_amounts = set(data["Amount"].dropna().astype(int).unique())
    observed_delays = set(data["Delay"].dropna().astype(int).unique())
    participant_counts = data.groupby("ID", observed=True).size()

    errors: list[str] = []
    if data["ID"].nunique() != 594:
        errors.append(f"expected 594 participants; found {data['ID'].nunique()}")
    if len(data) != 8_910:
        errors.append(f"expected 8,910 rows; found {len(data):,}")
    if observed_amounts != EXPECTED_AMOUNTS:
        errors.append(f"expected amounts {sorted(EXPECTED_AMOUNTS)}; found {sorted(observed_amounts)}")
    if observed_delays != EXPECTED_DELAYS:
        errors.append(f"expected delays {sorted(EXPECTED_DELAYS)}; found {sorted(observed_delays)}")
    if not participant_counts.eq(15).all():
        errors.append("each participant must contribute 15 amount-by-delay observations")
    if not data["Age"].between(20, 80, inclusive="both").all():
        errors.append("ages must be within the published range of 20-80 years")

    if errors:
        raise ValueError("Supplementary-data validation failed: " + "; ".join(errors))


def load_supplementary_data(path: str | Path) -> pd.DataFrame:
    """Load and validate the publisher-supplied data sheet."""

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Data file not found: {path}. Download Supplementary Data from "
            f"{ARTICLE_URL} and save it as Analysis/Supplementary Data.xlsx."
        )

    data = pd.read_excel(path, sheet_name="Data")
    validate_raw_data(data)

    numeric_columns = EXPECTED_COLUMNS.difference({"ID"})
    for column in numeric_columns:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    data["Age_group"] = pd.cut(
        data["Age"],
        bins=[20, 35, 51, 65, 81],
        labels=["20-34", "35-50", "51-64", "65-80"],
        right=False,
        ordered=True,
    )
    data["Amount_log"] = np.log(data["Amount"])
    return data


def trapezoidal_auc(group: pd.DataFrame) -> float:
    """Calculate normalized-delay AuC exactly as defined in the article."""

    ordered = group.sort_values("Delay")
    normalized_delay = ordered["Delay"].to_numpy(dtype=float) / ordered["Delay"].max()
    return float(np.trapezoid(ordered["RSV"].to_numpy(dtype=float), normalized_delay))


def build_auc_data(raw: pd.DataFrame) -> pd.DataFrame:
    """Return one AuC observation per participant and log-transformed amount."""

    auc = (
        raw.groupby(["ID", "Amount_log"], observed=True, sort=True)
        .apply(trapezoidal_auc, include_groups=False)
        .rename("AuC")
        .reset_index()
    )
    demographics = raw.drop_duplicates("ID").drop(
        columns=["Amount", "Amount_log", "Delay", "RSV"]
    )
    auc = auc.merge(demographics, on="ID", validate="many_to_one")

    lower = np.nextafter(0.0, 1.0)
    upper = np.nextafter(1.0, 0.0)
    auc["AuC"] = auc["AuC"].clip(lower=lower, upper=upper)
    return auc.sort_values(["ID", "Amount_log"], ignore_index=True)


def _complete_cases(data: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    return data.dropna(subset=list(columns)).copy()


def prepare_model_data(auc: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Construct model-specific complete-case samples and transformations."""

    model_1 = auc.loc[auc["Age"] >= 35].copy()
    model_1["Age_std"] = two_sd_scale(model_1["Age"])

    model_2 = _complete_cases(auc.loc[auc["Age"] >= 35], ["Income"])
    model_2["Age_std"] = two_sd_scale(model_2["Age"])
    model_2["Income_std"] = two_sd_scale(model_2["Income"])

    model_3 = _complete_cases(
        auc.loc[auc["Age"] >= 35], ["Income", "Anxiety", "Depression", "Distress"]
    )
    for variable in ("Age", "Income", "Anxiety", "Depression", "Distress"):
        model_3[f"{variable}_std"] = two_sd_scale(model_3[variable])

    model_4 = _complete_cases(
        auc.loc[auc["Age"] >= 35],
        ["Income", "Gender", "Education", "Anxiety", "Depression", "Distress", "Health"],
    )
    scale_columns = {
        "Age": "Age_std",
        "Amount_log": "Amount_std",
        "Income": "Income_std",
        "Education": "Education_std",
        "Anxiety": "Anxiety_std",
        "Depression": "Depression_std",
        "Distress": "Distress_std",
        "Health": "Health_std",
    }
    for source, target in scale_columns.items():
        model_4[target] = two_sd_scale(model_4[source])
    model_4["Gender_c"] = model_4["Gender"] - model_4["Gender"].mean()

    return {
        "model_1": model_1,
        "model_2": model_2,
        "model_3": model_3,
        "model_4": model_4,
    }


def participant_correlations(auc: pd.DataFrame, minimum_age: int = 20) -> pd.DataFrame:
    """Pearson correlation matrix after averaging AuC across amounts."""

    variables = [
        "Age",
        "Income",
        "Education",
        "Gender",
        "Distress",
        "Anxiety",
        "Depression",
        "Health",
        "AuC",
    ]
    participant = (
        auc.loc[auc["Age"] >= minimum_age]
        .groupby("ID", observed=True)[variables]
        .mean()
    )
    return participant.corr(method="pearson")


def plot_group_discounting(raw: pd.DataFrame, output: str | Path | None = None):
    """Reproduce the group-level discounting functions in article Figure 1."""

    import matplotlib.pyplot as plt
    import seaborn as sns
    from scipy.optimize import curve_fit

    means = (
        raw.groupby(["Age_group", "Amount", "Delay"], observed=True)
        .agg(Mean_RSV=("RSV", "mean"))
        .reset_index()
    )
    palette = {150: "#33a02c", 2_500: "#ff7f00", 30_000: "#1f78b4"}
    markers = {150: "s", 2_500: "^", 30_000: "o"}
    line_styles = {150: ":", 2_500: "--", 30_000: "-"}

    sns.set_theme(style="white", context="paper")
    figure, axes = plt.subplots(1, 4, figsize=(10.2, 3.0), sharex=True, sharey=True)
    fit_rows: list[dict[str, float | str]] = []

    for axis, (age_group, panel) in zip(axes, means.groupby("Age_group", observed=True)):
        for amount, amount_data in panel.groupby("Amount", observed=True):
            delay = amount_data["Delay"].to_numpy(dtype=float)
            rsv = amount_data["Mean_RSV"].to_numpy(dtype=float)
            parameters, _ = curve_fit(
                hyperboloid,
                delay,
                rsv,
                p0=(0.1, 1.0),
                bounds=((0, 0), (np.inf, np.inf)),
                maxfev=20_000,
            )
            prediction = hyperboloid(delay, *parameters)
            residual_ss = np.square(rsv - prediction).sum()
            total_ss = np.square(rsv - rsv.mean()).sum()
            fit_rows.append(
                {
                    "Age_group": str(age_group),
                    "Amount": int(amount),
                    "R2": float(1 - residual_ss / total_ss),
                }
            )

            dense_delay = np.linspace(0, 120, 300)
            label = f"${int(amount):,}"
            axis.plot(
                dense_delay,
                hyperboloid(dense_delay, *parameters),
                color=palette[int(amount)],
                linestyle=line_styles[int(amount)],
                linewidth=1.25,
            )
            axis.scatter(
                delay,
                rsv,
                label=label,
                color=palette[int(amount)],
                edgecolor="black",
                marker=markers[int(amount)],
                linewidth=0.5,
                s=25,
                zorder=3,
            )

        axis.set_title(str(age_group), fontweight="bold")
        axis.set_xlim(-5, 125)
        axis.set_ylim(0, 1.01)
        axis.set_xlabel("Delay (months)")
        axis.spines[["top", "right"]].set_visible(False)

    axes[0].set_ylabel("Relative subjective value")
    handles, labels = axes[-1].get_legend_handles_labels()
    figure.legend(handles, labels, title="Amount", frameon=False, loc="center right")
    figure.tight_layout(rect=(0, 0, 0.92, 1))

    if output is not None:
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(output, dpi=300, bbox_inches="tight")

    return figure, pd.DataFrame(fit_rows)


def _fixed_design(formula: str, data: pd.DataFrame):
    import patsy

    design = patsy.dmatrix(formula, data=data, return_type="dataframe")
    if "Intercept" not in design:
        raise ValueError("The fixed-effects design must contain an intercept.")
    slopes = design.drop(columns="Intercept")
    return slopes.to_numpy(dtype=float), list(slopes.columns), design.design_info


def fit_beta_multilevel_model(
    data: pd.DataFrame,
    spec: ModelSpec,
    cache_file: str | Path | None = None,
    *,
    draws: int = 2_000,
    tune: int = 2_000,
    chains: int = 4,
    cores: int = 4,
    target_accept: float = 0.95,
    seed: int = RANDOM_SEED,
    refit: bool = False,
) -> tuple[az.InferenceData, patsy.DesignInfo]:
    """Fit a published Bayesian multilevel beta regression in PyMC."""

    import arviz as az
    import pymc as pm
    import pytensor.tensor as pt

    cache_path = Path(cache_file) if cache_file is not None else None
    x, coefficient_names, design_info = _fixed_design(spec.formula, data)
    if cache_path is not None and cache_path.exists() and not refit:
        return az.from_netcdf(cache_path), design_info

    participant_codes, participant_ids = pd.factorize(data["ID"], sort=True)
    coords = {
        "observation": np.arange(len(data)),
        "coefficient": coefficient_names,
        "participant": participant_ids,
    }

    with pm.Model(coords=coords) as model:
        x_data = pm.Data("x", x, dims=("observation", "coefficient"))
        y_data = pm.Data("y", data["AuC"].to_numpy(dtype=float), dims="observation")
        participant_index = pm.Data(
            "participant_index", participant_codes, dims="observation"
        )

        intercept = pm.Flat("Intercept")
        beta = pm.Cauchy("beta", alpha=0, beta=2.5, dims="coefficient")
        eta = intercept + pt.dot(x_data, beta)

        if spec.random_amount_slope:
            coords["group_effect"] = ["Intercept", "Amount_std"]
            model.add_coord("group_effect", coords["group_effect"])
            sd_distribution = pm.HalfCauchy.dist(beta=2.5, shape=2)
            chol, _, _ = pm.LKJCholeskyCov(
                "participant_cholesky",
                n=2,
                eta=1,
                sd_dist=sd_distribution,
                compute_corr=True,
            )
            z = pm.Normal(
                "participant_z",
                mu=0,
                sigma=1,
                dims=("participant", "group_effect"),
            )
            participant_effect = pm.Deterministic(
                "participant_effect",
                pt.dot(z, chol.T),
                dims=("participant", "group_effect"),
            )
            z_design = np.column_stack(
                [np.ones(len(data)), data["Amount_std"].to_numpy(dtype=float)]
            )
            random_contribution = (
                participant_effect[participant_index] * z_design
            ).sum(axis=1)
            eta = eta + random_contribution
        else:
            participant_sd = pm.HalfCauchy("participant_sd", beta=2.5)
            participant_z = pm.Normal(
                "participant_z", mu=0, sigma=1, dims="participant"
            )
            participant_effect = pm.Deterministic(
                "participant_effect",
                participant_z * participant_sd,
                dims="participant",
            )
            eta = eta + participant_effect[participant_index]

        mu = pm.Deterministic("mu", pm.math.sigmoid(eta), dims="observation")
        phi = pm.HalfFlat("phi")
        pm.Beta("AuC", mu=mu, nu=phi, observed=y_data, dims="observation")

        inference_data = pm.sample(
            draws=draws,
            tune=tune,
            chains=chains,
            cores=cores,
            random_seed=seed,
            target_accept=target_accept,
            return_inferencedata=True,
        )
        inference_data.extend(
            pm.sample_posterior_predictive(
                inference_data,
                var_names=["AuC"],
                random_seed=seed,
                progressbar=False,
            )
        )

    if cache_path is not None:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        inference_data.to_netcdf(cache_path)
    return inference_data, design_info


def posterior_summary(
    inference_data: az.InferenceData, coefficient_names: list[str]
) -> pd.DataFrame:
    """Summarize fixed effects by median, posterior SD, pd, R-hat, and ESS."""

    import arviz as az

    intercept = inference_data.posterior["Intercept"].stack(sample=("chain", "draw")).values
    beta = (
        inference_data.posterior["beta"]
        .stack(sample=("chain", "draw"))
        .transpose("coefficient", "sample")
        .values
    )
    draws = np.vstack([intercept, beta])
    names = ["Intercept", *coefficient_names]
    probability_direction = np.maximum((draws > 0).mean(axis=1), (draws < 0).mean(axis=1))

    diagnostics = az.summary(
        inference_data,
        var_names=["Intercept", "beta"],
        filter_vars="exact",
        kind="diagnostics",
    )
    diagnostic_values = diagnostics[["r_hat", "ess_bulk", "ess_tail"]].to_numpy()

    summary = pd.DataFrame(
        {
            "term": names,
            "median": np.median(draws, axis=1),
            "posterior_sd": np.std(draws, axis=1, ddof=1),
            "pd": probability_direction,
            "r_hat": diagnostic_values[:, 0],
            "ess_bulk": diagnostic_values[:, 1],
            "ess_tail": diagnostic_values[:, 2],
        }
    )
    return summary


def count_divergences(inference_data: az.InferenceData) -> int:
    """Return the number of post-warmup divergent transitions."""

    return int(inference_data.sample_stats["diverging"].sum().item())


def run_models(
    model_data: dict[str, pd.DataFrame],
    cache_directory: str | Path,
    **sample_options,
) -> dict[str, tuple[az.InferenceData, patsy.DesignInfo]]:
    """Fit or load the four published models."""

    cache_directory = Path(cache_directory)
    fitted = {}
    for spec in MODEL_SPECS:
        print(f"Fitting {spec.name} ({len(model_data[spec.data_key]):,} observations)...")
        fitted[spec.name] = fit_beta_multilevel_model(
            model_data[spec.data_key],
            spec,
            cache_file=cache_directory / f"{spec.name}.nc",
            **sample_options,
        )
        divergences = count_divergences(fitted[spec.name][0])
        if divergences:
            print(f"WARNING: {spec.name} produced {divergences} divergent transitions.")
    return fitted


def _build_parser() -> argparse.ArgumentParser:
    analysis_directory = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data",
        type=Path,
        default=analysis_directory / "Supplementary Data.xlsx",
        help="Path to the publisher-supplied Supplementary Data workbook.",
    )
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=analysis_directory / "outputs",
        help="Directory for generated figures and tables.",
    )
    parser.add_argument(
        "--cache-directory",
        type=Path,
        default=analysis_directory / "cache" / "python_models",
        help="Directory for fitted-model NetCDF files.",
    )
    parser.add_argument("--fit-models", action="store_true", help="Fit the Bayesian models.")
    parser.add_argument(
        "--skip-figures",
        action="store_true",
        help="Run validation and tables without importing the plotting stack.",
    )
    parser.add_argument("--refit", action="store_true", help="Ignore compatible cached models.")
    parser.add_argument("--draws", type=int, default=2_000)
    parser.add_argument("--tune", type=int, default=2_000)
    parser.add_argument("--chains", type=int, default=4)
    parser.add_argument("--cores", type=int, default=4)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    raw = load_supplementary_data(args.data)
    auc = build_auc_data(raw)
    model_data = prepare_model_data(auc)

    print(
        f"Validated {raw['ID'].nunique():,} participants and {len(raw):,} task rows; "
        f"constructed {len(auc):,} participant-by-amount AuCs."
    )
    full_correlation = participant_correlations(auc)
    older_correlation = participant_correlations(auc, minimum_age=35)
    print(f"Age-mean AuC correlation (20-80): {full_correlation.loc['Age', 'AuC']:.3f}")
    print(f"Income-mean AuC correlation (35-80): {older_correlation.loc['Income', 'AuC']:.3f}")

    args.output_directory.mkdir(parents=True, exist_ok=True)
    if not args.skip_figures:
        import matplotlib.pyplot as plt

        figure, fits = plot_group_discounting(
            raw, args.output_directory / "figure_1_python.png"
        )
        plt.close(figure)
        fits.to_csv(args.output_directory / "hyperboloid_fit_r2.csv", index=False)
    full_correlation.to_csv(args.output_directory / "correlations_age_20_80.csv")
    older_correlation.to_csv(args.output_directory / "correlations_age_35_80.csv")

    if not args.fit_models:
        print("Bayesian fitting skipped. Re-run with --fit-models to fit Models 1-4.")
        return 0

    fitted = run_models(
        model_data,
        args.cache_directory,
        draws=args.draws,
        tune=args.tune,
        chains=args.chains,
        cores=args.cores,
        refit=args.refit,
    )
    for spec in MODEL_SPECS:
        inference_data, design_info = fitted[spec.name]
        coefficient_names = [
            name for name in design_info.column_names if name != "Intercept"
        ]
        summary = posterior_summary(inference_data, coefficient_names)
        summary.to_csv(args.output_directory / f"{spec.name}_summary.csv", index=False)
        print(f"\n{spec.name}\n{summary.to_string(index=False)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
