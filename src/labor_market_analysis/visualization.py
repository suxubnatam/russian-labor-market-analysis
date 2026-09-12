"""Consistent, non-interactive charts for the published report."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

CATEGORY_LABELS = {
    "male": "Мужчины",
    "female": "Женщины",
    "urban": "Город",
    "rural": "Село",
}


def _finish_figure(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()
    return path


def plot_unemployment_trend(table: pd.DataFrame, path: Path) -> Path:
    """Plot monthly unemployment with its approximate confidence band."""

    dates = pd.to_datetime(
        table["year"].astype("Int64").astype(str)
        + "-"
        + table["month"].astype("Int64").astype(str)
        + "-01"
    )
    order = dates.argsort()
    ordered = table.iloc[order]
    dates = dates.iloc[order]

    plt.figure(figsize=(12, 6))
    plt.plot(dates, ordered["unemployment_rate"], color="#2457A7", linewidth=2)
    plt.fill_between(
        dates,
        ordered["ci_lower"].astype(float),
        ordered["ci_upper"].astype(float),
        color="#2457A7",
        alpha=0.16,
        label="Приближённый 95% ДИ",
    )
    plt.title("Динамика уровня безработицы в России")
    plt.xlabel("Год")
    plt.ylabel("Уровень безработицы, %")
    plt.grid(alpha=0.25)
    plt.legend(frameon=False)
    return _finish_figure(path)


def plot_latest_comparison(
    table: pd.DataFrame,
    *,
    category: str,
    metric: str,
    title: str,
    path: Path,
    max_categories: int = 20,
) -> Path:
    """Plot the latest available annual comparison for a demographic group."""

    latest_year = int(table["year"].max())
    latest = table[table["year"] == latest_year].dropna(subset=[category, metric]).copy()
    latest = latest.sort_values(metric, ascending=False).head(max_categories)
    if latest.empty:
        raise ValueError(f"No observations available for comparison by {category!r}")
    labels = latest[category].astype(str).replace(CATEGORY_LABELS)

    plt.figure(figsize=(10, max(4.5, len(latest) * 0.38)))
    plt.barh(labels, latest[metric], color="#D9782D")
    plt.gca().invert_yaxis()
    plt.title(f"{title}, {latest_year}")
    plt.xlabel("Доля, %")
    plt.ylabel("")
    plt.grid(axis="x", alpha=0.25)
    return _finish_figure(path)
