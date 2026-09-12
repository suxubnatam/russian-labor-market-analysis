import pandas as pd
import pytest


@pytest.fixture
def source_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "GOD": [2023, 2023, 2023, 2023],
            "KWARTAL": [1, 1, 1, 1],
            "MES": [1, 1, 2, 2],
            "TERRIT": [45000, 3, 11100, 45],
            "VESA": [3.0, 1.0, 100.0, 2.0],
            "VESA_KVART": [3.0, 1.0, 100.0, 2.0],
            "VESA_OB": [3.0, 1.0, 100.0, 2.0],
            "POSEL": [1, 2, 1, 1],
            "NAS_POL": [1, 2, 1, 2],
            "NAS_VOZR": [30, 22, 50, 14],
            "STRUKTAK": [1, 2, 3, 1],
            "ZAN_NF": [0, 1, 1, 0],
        }
    )


@pytest.fixture
def harmonized_metrics_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "year": [2023, 2023, 2023, 2023],
            "month": [1, 1, 1, 2],
            "gender": ["male", "female", "male", "female"],
            "settlement_type": ["urban", "rural", "urban", "rural"],
            "age_5group": ["30-34", "20-24", "50-54", "20-24"],
            "region": [45, 3, 11, 45],
            "labor_force_status": [
                "employed",
                "unemployed",
                "not_in_labor_force",
                "employed",
            ],
            "informal_employment": ["formal", "informal", "informal", "informal"],
            "vesa": [3.0, 1.0, 100.0, 2.0],
            "ves_kvart": [3.0, 1.0, 100.0, 2.0],
            "vesa_ob": [3.0, 1.0, 100.0, 2.0],
        }
    )
