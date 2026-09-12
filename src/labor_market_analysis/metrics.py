"""Survey-weighted labor-market indicators with approximate uncertainty."""

from collections.abc import Sequence

import numpy as np
import pandas as pd


def select_weight(group_by: Sequence[str]) -> str:
    """Choose the survey weight matching the requested time resolution."""

    if "month" in group_by:
        return "vesa"
    if "quarter" in group_by:
        return "ves_kvart"
    return "vesa_ob"


def weighted_components(
    frame: pd.DataFrame,
    *,
    outcome_column: str,
    positive_value: object,
    weight_column: str,
    group_by: Sequence[str],
) -> pd.DataFrame:
    """Return additive components for a weighted proportion."""

    needed = {outcome_column, weight_column, *group_by}
    missing = needed.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing columns for weighted calculation: {sorted(missing)}")

    valid = frame[outcome_column].notna() & frame[weight_column].notna()
    valid &= frame[weight_column] > 0
    work = frame.loc[valid, list(group_by)].copy()
    weights = frame.loc[valid, weight_column].astype(float)
    work["weighted_numerator"] = weights * (
        frame.loc[valid, outcome_column] == positive_value
    ).astype(float)
    work["weighted_denominator"] = weights
    work["weight_squared"] = weights**2
    work["unweighted_n"] = 1

    component_columns = [
        "weighted_numerator",
        "weighted_denominator",
        "weight_squared",
        "unweighted_n",
    ]
    if group_by:
        return (
            work.groupby(list(group_by), dropna=False, observed=True)[component_columns]
            .sum()
            .reset_index()
        )
    return pd.DataFrame([work[component_columns].sum()])


def finalize_weighted_components(
    components: pd.DataFrame,
    *,
    group_by: Sequence[str],
    metric_name: str,
    scale: float = 100.0,
) -> pd.DataFrame:
    """Combine partial components and calculate a Wilson-style 95% interval.

    The interval uses Kish's effective sample size. It is an approximation,
    because public project inputs do not include complete strata/cluster design.
    """

    additive = [
        "weighted_numerator",
        "weighted_denominator",
        "weight_squared",
        "unweighted_n",
    ]
    if group_by:
        totals = (
            components.groupby(list(group_by), dropna=False, observed=True)[additive]
            .sum()
            .reset_index()
        )
    else:
        totals = pd.DataFrame([components[additive].sum()])

    denominator = totals["weighted_denominator"].astype(float)
    proportion = totals["weighted_numerator"] / denominator.replace(0, np.nan)
    effective_n = denominator.pow(2) / totals["weight_squared"].replace(0, np.nan)

    z = 1.959963984540054
    correction = z**2 / effective_n
    center = (proportion + correction / 2) / (1 + correction)
    margin = (
        z
        * np.sqrt(
            (proportion * (1 - proportion) / effective_n)
            + (z**2 / (4 * effective_n.pow(2)))
        )
        / (1 + correction)
    )

    totals[metric_name] = proportion * scale
    totals["ci_lower"] = (center - margin).clip(0, 1) * scale
    totals["ci_upper"] = (center + margin).clip(0, 1) * scale
    totals["effective_n"] = effective_n
    return totals[
        [
            *group_by,
            metric_name,
            "ci_lower",
            "ci_upper",
            "weighted_numerator",
            "weighted_denominator",
            "effective_n",
            "unweighted_n",
        ]
    ]


def _weighted_indicator(
    frame: pd.DataFrame,
    *,
    outcome_column: str,
    positive_value: object,
    group_by: Sequence[str],
    metric_name: str,
    weight_column: str | None,
) -> pd.DataFrame:
    selected_weight = weight_column or select_weight(group_by)
    components = weighted_components(
        frame,
        outcome_column=outcome_column,
        positive_value=positive_value,
        weight_column=selected_weight,
        group_by=group_by,
    )
    return finalize_weighted_components(
        components,
        group_by=group_by,
        metric_name=metric_name,
    )


def unemployment_rate(
    frame: pd.DataFrame,
    *,
    group_by: Sequence[str] = ("year", "month"),
    weight_column: str | None = None,
) -> pd.DataFrame:
    """Calculate unemployed / labor force as a weighted percentage."""

    labor_force = frame[
        frame["labor_force_status"].isin(["employed", "unemployed"])
    ]
    return _weighted_indicator(
        labor_force,
        outcome_column="labor_force_status",
        positive_value="unemployed",
        group_by=group_by,
        metric_name="unemployment_rate",
        weight_column=weight_column,
    )


def informal_employment_share(
    frame: pd.DataFrame,
    *,
    group_by: Sequence[str] = ("year",),
    weight_column: str | None = None,
) -> pd.DataFrame:
    """Calculate the weighted informal share among employed respondents."""

    employed = frame[
        (frame["labor_force_status"] == "employed")
        & frame["informal_employment"].isin(["formal", "informal"])
    ]
    return _weighted_indicator(
        employed,
        outcome_column="informal_employment",
        positive_value="informal",
        group_by=group_by,
        metric_name="informal_employment_share",
        weight_column=weight_column,
    )
