"""Normalize survey waves to one documented analytical schema."""

from collections.abc import Iterable

import numpy as np
import pandas as pd

from labor_market_analysis.config import (
    COLUMN_ALIASES,
    CRITICAL_COLUMNS,
    INTEGER_COLUMNS,
    TARGET_COLUMNS,
    VALID_YEAR_RANGE,
    WEIGHT_COLUMNS,
)

GENDER_LABELS = {1: "male", 2: "female"}
LABOR_FORCE_LABELS = {
    1: "employed",
    2: "unemployed",
    3: "not_in_labor_force",
}
INFORMAL_EMPLOYMENT_LABELS = {0: "formal", 1: "informal"}
SETTLEMENT_LABELS = {1: "urban", 2: "rural"}

AGE_BINS = [15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 101]
AGE_LABELS = [
    "15-19",
    "20-24",
    "25-29",
    "30-34",
    "35-39",
    "40-44",
    "45-49",
    "50-54",
    "55-59",
    "60-64",
    "65-69",
    "70-74",
    "75-79",
    "80+",
]


def normalized_name(column: object) -> str:
    """Return the canonical name for a source column when one is known."""

    name = str(column).strip().lower()
    return COLUMN_ALIASES.get(name, name)


def source_column_mapping(columns: Iterable[object]) -> dict[object, str]:
    """Build a collision-safe source-to-canonical rename mapping."""

    mapping = {column: normalized_name(column) for column in columns}
    canonical = [name for name in mapping.values() if name in TARGET_COLUMNS]
    duplicates = sorted({name for name in canonical if canonical.count(name) > 1})
    if duplicates:
        raise ValueError(f"Several source columns map to the same fields: {duplicates}")
    return mapping


def _region_code(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    # Older waves store 45 (Moscow), newer ones may store 45000 or a sub-code.
    normalized = values.where(values < 1_000, np.floor(values / 1_000))
    return normalized.astype("Int16")


def _recode(series: pd.Series, labels: dict[int, str]) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    return numeric.map(labels).astype("string")


def validate_harmonized_frame(frame: pd.DataFrame) -> None:
    """Validate invariants required by all downstream calculations."""

    missing = CRITICAL_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing critical columns: {sorted(missing)}")

    years = frame["year"].dropna().astype(int)
    invalid_years = sorted(set(years).difference(VALID_YEAR_RANGE))
    if invalid_years:
        raise ValueError(f"Years outside 2010-2023: {invalid_years}")

    months = frame["month"].dropna().astype(int)
    if not months.between(1, 12).all():
        invalid_months = sorted(months[~months.between(1, 12)].unique().tolist())
        raise ValueError(f"Months outside 1-12: {invalid_months}")

    for weight in WEIGHT_COLUMNS:
        negative = frame[weight].dropna() < 0
        if negative.any():
            raise ValueError(f"Column {weight!r} contains negative weights")


def harmonize_dataframe(frame: pd.DataFrame) -> pd.DataFrame:
    """Return one survey chunk in the canonical 21-column schema.

    Source variable names are matched case-insensitively. Rows outside the
    documented working-age range (15-100) are excluded.
    """

    renamed = frame.rename(columns=source_column_mapping(frame.columns))
    missing = CRITICAL_COLUMNS.difference(renamed.columns)
    if missing:
        raise ValueError(f"Source data do not contain required fields: {sorted(missing)}")

    result = renamed.reindex(columns=TARGET_COLUMNS).copy()

    for column in INTEGER_COLUMNS.difference({"region"}):
        result[column] = pd.to_numeric(result[column], errors="coerce").astype("Int16")
    for column in WEIGHT_COLUMNS:
        result[column] = pd.to_numeric(result[column], errors="coerce").astype("Float64")

    result["region"] = _region_code(result["region"])
    result["gender"] = _recode(result["gender"], GENDER_LABELS)
    result["labor_force_status"] = _recode(
        result["labor_force_status"], LABOR_FORCE_LABELS
    )
    result["informal_employment"] = _recode(
        result["informal_employment"], INFORMAL_EMPLOYMENT_LABELS
    )
    result["settlement_type"] = _recode(result["settlement_type"], SETTLEMENT_LABELS)

    result = result[result["age"].between(15, 100)].copy()
    result["age_5group"] = pd.cut(
        result["age"],
        bins=AGE_BINS,
        labels=AGE_LABELS,
        right=False,
        include_lowest=True,
    ).astype("string")

    validate_harmonized_frame(result)
    return result.sort_values(["year", "quarter", "month"], na_position="last").reset_index(
        drop=True
    )
