
from pathlib import Path

import pandas as pd


# =====================================================
# PATH
# =====================================================

BASE_DIR = Path(__file__).resolve().parent

FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "historical_individual_crop_records.csv"
)

if not FILE.exists():
    raise FileNotFoundError(
        f"Historical dataset not found: {FILE}\n"
        "Run prepare_historical_data.py first."
    )


# =====================================================
# LOAD DATASET
# =====================================================

df = pd.read_csv(FILE)

required_columns = [
    "Crop_Year",
    "State_Name",
    "District_Name",
    "Season",
    "Crop",
    "Production",
    "Area",
]

missing_columns = set(required_columns) - set(df.columns)

if missing_columns:
    raise ValueError(
        f"Missing required columns: {sorted(missing_columns)}"
    )

if df.empty:
    raise ValueError("Historical dataset is empty.")

for column in ["Crop_Year", "Production", "Area"]:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce",
    )


# =====================================================
# DATASET SUMMARY
# =====================================================

print("=== DATASET SUMMARY ===")

print(f"Records: {len(df):,}")

print(
    f"Years: {df['Crop_Year'].min()}–"
    f"{df['Crop_Year'].max()}"
)

print(f"States: {df['State_Name'].nunique()}")
print(f"Districts: {df['District_Name'].nunique()}")
print(f"Crop labels: {df['Crop'].nunique()}")


# =====================================================
# SAMPLE DISTRICTS
# =====================================================

print("\n=== SAMPLE DISTRICTS ===")

print(
    df[["State_Name", "District_Name"]]
    .drop_duplicates()
    .sort_values(["State_Name", "District_Name"])
    .head(15)
    .to_string(index=False)
)


# =====================================================
# MOST FREQUENT INDIVIDUAL CROPS
# =====================================================

print("\n=== MOST FREQUENT INDIVIDUAL CROPS ===")

print(
    df["Crop"]
    .value_counts()
    .head(15)
    .to_string()
)


# =====================================================
# SAMPLE HISTORICAL CROP RANKING
# =====================================================

district = "ANANTAPUR"
season = "Kharif"

print("\n=== SAMPLE HISTORICAL CROP RANKING ===")

sample = df[
    (
        df["District_Name"]
        .astype("string")
        .str.strip()
        .str.casefold()
        == district.casefold()
    )
    &
    (
        df["Season"]
        .astype("string")
        .str.strip()
        .str.casefold()
        == season.casefold()
    )
].copy()

if sample.empty:

    print(f"No records found for {district}, {season}.")

else:

    ranking = (
        sample.groupby("Crop", as_index=False)
        .agg(
            total_production=("Production", "sum"),
            total_area=("Area", "sum"),
            years_recorded=("Crop_Year", "nunique"),
        )
        .sort_values(
            "total_production",
            ascending=False,
        )
    )

    print(
        ranking.head(10).to_string(index=False)
    )


# =====================================================
# COMPLETION
# =====================================================

print("\nHistorical insights test complete.")
