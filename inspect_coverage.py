
from pathlib import Path

import pandas as pd


# =====================================================
# LOAD DATASET
# =====================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "raw" / "crop_production.csv"

if not DATA_FILE.exists():
    raise FileNotFoundError(f"Dataset not found: {DATA_FILE}")

df = pd.read_csv(DATA_FILE)

required_columns = {
    "Crop_Year",
    "Season",
    "Crop",
    "Production",
}

missing = required_columns - set(df.columns)

if missing:
    raise ValueError(
        f"Dataset is missing columns: {sorted(missing)}"
    )

df["Crop_Year"] = pd.to_numeric(
    df["Crop_Year"],
    errors="coerce"
)


# =====================================================
# LAST FIVE YEARS: RECORD COUNTS
# =====================================================

print("\n=== LAST FIVE YEARS: RECORD COUNTS ===")

print(
    df["Crop_Year"]
    .value_counts()
    .sort_index()
    .tail(5)
    .to_string()
)


# =====================================================
# RECORD COUNTS BY YEAR AND SEASON
# =====================================================

print("\n=== RECORD COUNTS BY YEAR AND SEASON ===")

print(
    pd.crosstab(df["Crop_Year"], df["Season"])
    .sort_index()
    .tail(5)
    .to_string()
)


# =====================================================
# POSSIBLE AGGREGATE CROP LABELS
# =====================================================

print("\n=== POSSIBLE AGGREGATE CROP LABELS ===")

aggregate_words = ["total", "other", "misc"]

crop_names = df["Crop"].fillna("").astype(str)

mask = crop_names.str.contains(
    "|".join(aggregate_words),
    case=False,
    na=False,
)

print("Number of records:", int(mask.sum()))

print("Distinct labels:")

print(
    sorted(
        df.loc[mask, "Crop"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )
)


# =====================================================
# MISSING PRODUCTION BY YEAR
# =====================================================

print("\n=== MISSING PRODUCTION BY YEAR ===")

print(
    df.assign(
        production_missing=df["Production"].isna()
    )
    .groupby("Crop_Year")
    .agg(
        records=("Crop", "size"),
        missing_production=("production_missing", "sum"),
    )
    .sort_index()
    .tail(8)
    .to_string()
)


print("\n=== COVERAGE CHECK COMPLETE ===")
