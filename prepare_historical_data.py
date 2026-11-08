
from pathlib import Path

import pandas as pd


# =====================================================
# PATHS
# =====================================================

BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "data" / "raw" / "crop_production.csv"
OUTPUT_DIR = BASE_DIR / "data" / "processed"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# =====================================================
# LOAD DATASET
# =====================================================

if not INPUT_FILE.exists():
    raise FileNotFoundError(f"Dataset not found: {INPUT_FILE}")

df = pd.read_csv(INPUT_FILE)

required_columns = [
    "State_Name",
    "District_Name",
    "Crop_Year",
    "Season",
    "Crop",
    "Production",
]

missing_columns = set(required_columns) - set(df.columns)

if missing_columns:
    raise ValueError(
        f"Missing required columns: {sorted(missing_columns)}"
    )


# =====================================================
# CLEAN DATA
# =====================================================

text_columns = [
    "State_Name",
    "District_Name",
    "Season",
    "Crop",
]

for column in text_columns:
    df[column] = df[column].astype("string").str.strip()

df["Crop_Year"] = pd.to_numeric(
    df["Crop_Year"],
    errors="coerce",
)

df["Production"] = pd.to_numeric(
    df["Production"],
    errors="coerce",
)


# =====================================================
# HISTORICAL DATA FILTERING
# =====================================================

# Exclude 2015 and later from this analysis copy.
historical = df[
    df["Crop_Year"].notna()
    & (df["Crop_Year"] < 2015)
].copy()

# Retain only records with known production.
known_production = historical[
    historical["Production"].notna()
].copy()


# =====================================================
# SEPARATE AGGREGATE AND INDIVIDUAL CROPS
# =====================================================

aggregate_labels = {
    "oilseeds total",
    "pulses total",
    "total foodgrain",
}

crop_names = known_production["Crop"].str.casefold()

aggregate_mask = (
    crop_names.isin(aggregate_labels)
    | crop_names.str.startswith("other", na=False)
)

aggregate_records = known_production[
    aggregate_mask
].copy()

crop_records = known_production[
    ~aggregate_mask
].copy()


# =====================================================
# SAVE OUTPUT FILES
# =====================================================

known_production.to_csv(
    OUTPUT_DIR / "historical_production_known.csv",
    index=False,
)

crop_records.to_csv(
    OUTPUT_DIR / "historical_individual_crop_records.csv",
    index=False,
)

aggregate_records.to_csv(
    OUTPUT_DIR / "historical_aggregate_crop_records.csv",
    index=False,
)


# =====================================================
# SUMMARY
# =====================================================

print("\n=== HISTORICAL DATA PREPARATION ===")

print(f"Original records: {len(df):,}")
print(f"Records before 2015: {len(historical):,}")
print(f"Records with known production: {len(known_production):,}")
print(f"Individual crop records: {len(crop_records):,}")
print(f"Aggregate/broad-category records: {len(aggregate_records):,}")

print(
    "Zero-production records retained: "
    f"{(known_production['Production'] == 0).sum():,}"
)

if not historical.empty:
    print(
        f"Years included: "
        f"{int(historical['Crop_Year'].min())}–"
        f"{int(historical['Crop_Year'].max())}"
    )
else:
    print("Years included: No valid historical records")

print(f"Output directory: {OUTPUT_DIR}")

print("\nPreparation complete.")
