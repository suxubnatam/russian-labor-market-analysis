"""Shared data contract and project defaults."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DEFAULT_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DEFAULT_REPORT_DIR = PROJECT_ROOT / "reports"

VALID_YEAR_RANGE = range(2010, 2024)

TARGET_COLUMNS = (
    "year",
    "quarter",
    "month",
    "region",
    "vesa",
    "ves_kvart",
    "vesa_ob",
    "settlement_type",
    "gender",
    "age",
    "age_5group",
    "education",
    "marital_status",
    "year_vocational_edu",
    "labor_force_status",
    "social_category",
    "workplace",
    "employment_contract",
    "economic_activity_group",
    "job_profession_match",
    "informal_employment",
)

# Source names changed case after 2021. Normalizing to lowercase lets one map
# describe every survey wave.
COLUMN_ALIASES = {
    "god": "year",
    "kwartal": "quarter",
    "mes": "month",
    "territ": "region",
    "vesa": "vesa",
    "vesa_kvart": "ves_kvart",
    "ves_kvart": "ves_kvart",
    "vesa_ob": "vesa_ob",
    "possel": "settlement_type",
    "nas_pol": "gender",
    "nas_vozr": "age",
    "nas_voz4": "age_5group",
    "nasobraz": "education",
    "nasbrach": "marital_status",
    "god_okonch": "year_vocational_edu",
    "struktak": "labor_force_status",
    "kateg": "social_category",
    "v_os": "workplace",
    "tip_dg": "employment_contract",
    "vid_osn1": "economic_activity_group",
    "sv_prof": "job_profession_match",
    "zan_nf": "informal_employment",
}

CRITICAL_COLUMNS = {
    "year",
    "month",
    "vesa",
    "vesa_ob",
    "gender",
    "age",
    "labor_force_status",
    "informal_employment",
}

INTEGER_COLUMNS = {
    "year",
    "quarter",
    "month",
    "region",
    "age",
    "education",
    "marital_status",
    "year_vocational_edu",
    "social_category",
    "workplace",
    "employment_contract",
    "economic_activity_group",
    "job_profession_match",
}

WEIGHT_COLUMNS = ("vesa", "ves_kvart", "vesa_ob")
