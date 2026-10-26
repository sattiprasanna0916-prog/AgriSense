
from functools import lru_cache
from pathlib import Path

import pandas as pd

DATA_FILE = Path("data/processed/historical_individual_crop_records.csv")


@lru_cache(maxsize=1)
def load_historical_data():
    """Load the prepared historical dataset once per application process."""
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Historical dataset not found: {DATA_FILE.resolve()}"
        )

    df = pd.read_csv(DATA_FILE)

    required = {
        "State_Name",
        "District_Name",
        "Crop_Year",
        "Season",
        "Crop",
        "Area",
        "Production",
    }
    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"Historical dataset is missing columns: {sorted(missing)}"
        )

    return df


def get_district_crop_ranking(
    state: str,
    district: str,
    season: str,
    limit: int = 10,
):
    """Rank recorded crops by total production for a district and season."""
    df = load_historical_data()

    if not 1 <= limit <= 50:
        raise ValueError("limit must be between 1 and 50")

    filtered = df[
        df["State_Name"].str.casefold().eq(state.strip().casefold())
        & df["District_Name"].str.casefold().eq(
            district.strip().casefold()
        )
        & df["Season"].str.casefold().eq(season.strip().casefold())
    ]

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
        .sort_values("total_production", ascending=False)
        .head(limit)
    )

    return {
        "state": state,
        "district": district,
        "season": season,
        "years_covered": sorted(
            int(year) for year in filtered["Crop_Year"].dropna().unique()
        ),
        "crops": ranking.to_dict(orient="records"),
        "message": (
            "Rankings describe historical records, not guaranteed "
            "future suitability or profitability."
        ),
    }


def get_crop_production_trend(
    state: str,
    district: str,
    crop: str,
    season: str,
):
    """Return yearly recorded production and area for one crop."""
    df = load_historical_data()

    filtered = df[
        df["State_Name"].str.casefold().eq(state.strip().casefold())
        & df["District_Name"].str.casefold().eq(
            district.strip().casefold()
        )
        & df["Crop"].str.casefold().eq(crop.strip().casefold())
        & df["Season"].str.casefold().eq(season.strip().casefold())
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

    return {
        "state": state,
        "district": district,
        "crop": crop,
        "season": season,
        "trend": [
            {
                "year": int(row.Crop_Year),
                "total_production": float(row.total_production),
                "total_area": float(row.total_area),
            }
            for row in yearly.itertuples(index=False)
        ],
        "message": (
            "Historical trends do not predict future production "
            "and may reflect incomplete reporting."
        ),
    }
