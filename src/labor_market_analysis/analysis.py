"""End-to-end aggregation and report generation over Parquet partitions."""

from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from labor_market_analysis.metrics import finalize_weighted_components, weighted_components
from labor_market_analysis.visualization import (
    plot_latest_comparison,
    plot_unemployment_trend,
)

UNEMPLOYED_SPEC = ("labor_force_status", "unemployed")
INFORMAL_SPEC = ("informal_employment", "informal")


def _parquet_parts(processed_dir: Path) -> list[Path]:
    parts = sorted(processed_dir.glob("year=*/*.parquet"))
    if not parts:
        raise FileNotFoundError(f"No partitioned Parquet files found in {processed_dir}")
    return parts


def _partition_year(path: Path) -> int:
    prefix, value = path.parent.name.split("=", maxsplit=1)
    if prefix != "year":
        raise ValueError(f"Unexpected partition directory: {path.parent.name}")
    return int(value)


def _unemployment_components(frame: pd.DataFrame, group_by: Sequence[str]) -> pd.DataFrame:
    labor_force = frame[frame["labor_force_status"].isin(["employed", "unemployed"])]
    weight = "vesa" if "month" in group_by else "vesa_ob"
    return weighted_components(
        labor_force,
        outcome_column=UNEMPLOYED_SPEC[0],
        positive_value=UNEMPLOYED_SPEC[1],
        weight_column=weight,
        group_by=group_by,
    )


def _informal_components(frame: pd.DataFrame, group_by: Sequence[str]) -> pd.DataFrame:
    employed = frame[
        (frame["labor_force_status"] == "employed")
        & frame["informal_employment"].isin(["formal", "informal"])
    ]
    return weighted_components(
        employed,
        outcome_column=INFORMAL_SPEC[0],
        positive_value=INFORMAL_SPEC[1],
        weight_column="vesa_ob",
        group_by=group_by,
    )


def _finalize(
    chunks: list[pd.DataFrame], group_by: Sequence[str], metric_name: str
) -> pd.DataFrame:
    return finalize_weighted_components(
        pd.concat(chunks, ignore_index=True),
        group_by=group_by,
        metric_name=metric_name,
    ).sort_values(list(group_by), na_position="last")


def run_analysis(processed_dir: Path, report_dir: Path) -> dict[str, Path]:
    """Generate compact analytical tables and portfolio-ready figures."""

    specifications = {
        "monthly_unemployment": ("unemployment_rate", ("year", "month")),
        "unemployment_by_age": ("unemployment_rate", ("year", "age_5group")),
        "unemployment_by_gender": ("unemployment_rate", ("year", "gender")),
        "unemployment_by_settlement": (
            "unemployment_rate",
            ("year", "settlement_type"),
        ),
        "unemployment_by_region": ("unemployment_rate", ("year", "region")),
        "annual_informal_share": ("informal_employment_share", ("year",)),
        "informal_share_by_gender": (
            "informal_employment_share",
            ("year", "gender"),
        ),
        "informal_share_by_settlement": (
            "informal_employment_share",
            ("year", "settlement_type"),
        ),
    }
    partials: dict[str, list[pd.DataFrame]] = {name: [] for name in specifications}

    read_columns = [
        "month",
        "region",
        "vesa",
        "vesa_ob",
        "gender",
        "age_5group",
        "settlement_type",
        "labor_force_status",
        "informal_employment",
    ]
    for path in _parquet_parts(processed_dir):
        frame = pd.read_parquet(path, columns=read_columns)
        frame["year"] = _partition_year(path)
        for name, (metric_name, group_by) in specifications.items():
            if metric_name == "unemployment_rate":
                partials[name].append(_unemployment_components(frame, group_by))
            else:
                partials[name].append(_informal_components(frame, group_by))

    tables = {
        name: _finalize(partials[name], group_by, metric_name)
        for name, (metric_name, group_by) in specifications.items()
    }

    table_dir = report_dir / "tables"
    figure_dir = report_dir / "figures"
    table_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, Path] = {}
    for name, table in tables.items():
        output_path = table_dir / f"{name}.csv"
        table.to_csv(output_path, index=False)
        outputs[name] = output_path

    outputs["unemployment_trend_figure"] = plot_unemployment_trend(
        tables["monthly_unemployment"], figure_dir / "unemployment_trend.png"
    )
    outputs["age_figure"] = plot_latest_comparison(
        tables["unemployment_by_age"],
        category="age_5group",
        metric="unemployment_rate",
        title="Уровень безработицы по возрастным группам",
        path=figure_dir / "unemployment_by_age.png",
    )
    outputs["gender_figure"] = plot_latest_comparison(
        tables["informal_share_by_gender"],
        category="gender",
        metric="informal_employment_share",
        title="Доля неформальной занятости по полу",
        path=figure_dir / "informal_share_by_gender.png",
    )
    outputs["settlement_figure"] = plot_latest_comparison(
        tables["informal_share_by_settlement"],
        category="settlement_type",
        metric="informal_employment_share",
        title="Доля неформальной занятости по типу поселения",
        path=figure_dir / "informal_share_by_settlement.png",
    )
    return outputs
