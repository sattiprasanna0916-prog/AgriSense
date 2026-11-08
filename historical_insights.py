
from functools import lru_cache
from pathlib import Path

import pandas as pd


# =====================================================
# CONFIGURATION
# =====================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "historical_individual_crop_records.csv"
)

REQUIRED_COLUMNS = {
    "State_Name",
    "District_Name",
    "Crop_Year",
    "Season",
    "Crop",
    "Area",
    "Production",
}


# =====================================================
# LOAD HISTORICAL DATA
# =====================================================

@lru_cache(maxsize=1)
def load_historical_data():

    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Historical dataset not found: {DATA_FILE}"
        )

    df = pd.read_csv(DATA_FILE)

    missing = REQUIRED_COLUMNS - set(df.columns)

    if missing:
        raise ValueError(
            f"Historical dataset is missing columns: "
            f"{sorted(missing)}"
        )

    # Convert numeric columns safely.
    for column in ["Crop_Year", "Area", "Production"]:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # Remove records without essential category information.
    for column in [
        "State_Name",
        "District_Name",
        "Season",
        "Crop",
    ]:
        df[column] = df[column].astype("string").str.strip()

    return df


# =====================================================
# VALIDATION AND FILTERING
# =====================================================

def validate_inputs(**kwargs):

    for name, value in kwargs.items():

        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"{name} must be a non-empty string."
            )


def filter_records(df, state, district, season):

    return df[
        df["State_Name"].str.casefold().eq(
            state.strip().casefold()
        )
        & df["District_Name"].str.casefold().eq(
            district.strip().casefold()
        )
        & df["Season"].str.casefold().eq(
            season.strip().casefold()
        )
    ]


# =====================================================
# DISTRICT CROP RANKING
# =====================================================

def get_district_crop_ranking(
    state: str,
    district: str,
    season: str,
    limit: int = 10,
):

    validate_inputs(
        state=state,
        district=district,
        season=season,
    )

    if not isinstance(limit, int) or not 1 <= limit <= 50:
        raise ValueError("limit must be an integer between 1 and 50")

    df = load_historical_data()

    filtered = filter_records(
        df, state, district, season
    )

    if filtered.empty:
        return {
            "state": state,
            "district": district,
            "season": season,
            "years_covered": [],
            "crops": [],
            "message": "No matching historical records were found.",
        }

    ranking = (
        filtered.groupby("Crop", as_index=False)
        .agg(
            total_production=("Production", "sum"),
            total_area=("Area", "sum"),
            years_recorded=("Crop_Year", "nunique"),
        )
        .sort_values(
            "total_production",
            ascending=False,
            na_position="last",
        )
        .head(limit)
    )

    return {
        "state": state,
        "district": district,
        "season": season,
        "years_covered": sorted(
            int(year)
            for year in filtered["Crop_Year"].dropna().unique()
        ),
        "crops": ranking.to_dict(orient="records"),
        "message": (
            "Rankings describe historical records, not guaranteed "
            "future suitability or profitability."
        ),
    }


# =====================================================
# CROP PRODUCTION TREND
# =====================================================

def get_crop_production_trend(
    state: str,
    district: str,
    crop: str,
    season: str,
):

    validate_inputs(
        state=state,
        district=district,
        crop=crop,
        season=season,
    )

    df = load_historical_data()

    filtered = filter_records(
        df, state, district, season
    )

    filtered = filtered[
        filtered["Crop"].str.casefold().eq(
            crop.strip().casefold()
        )
    ]

    if filtered.empty:
        return {
            "state": state,
            "district": district,
            "crop": crop,
            "season": season,
            "trend": [],
            "message": "No matching historical records were found.",
        }

    yearly = (
        filtered.groupby("Crop_Year", as_index=False)
        .agg(
            total_production=("Production", "sum"),
            total_area=("Area", "sum"),
        )
        .sort_values("Crop_Year")
    )

    trend = [
        {
            "year": int(row.Crop_Year),
            "total_production": float(row.total_production),
            "total_area": float(row.total_area),
        }
        for row in yearly.itertuples(index=False)
        if pd.notna(row.Crop_Year)
    ]

    return {
        "state": state,
        "district": district,
        "crop": crop,
        "season": season,
        "trend": trend,
        "message": (
            "Historical trends do not predict future production "
            "and may reflect incomplete reporting."
        ),
    }
