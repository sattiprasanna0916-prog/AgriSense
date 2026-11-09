
from pathlib import Path

import numpy as np
import pandas as pd


# =====================================================
# LOAD DATASET
# =====================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "raw" / "crop_production.csv"

if not DATA_PATH.exists():
    raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")

df = pd.read_csv(DATA_PATH)

columns = [
    "State_Name",
    "District_Name",
    "Crop_Year",
    "Season",
    "Crop",
    "Area",
    "Production",
]

missing = set(columns) - set(df.columns)

if missing:
    raise ValueError(
        f"Dataset is missing columns: {sorted(missing)}"
    )

# Convert numeric columns safely.
for col in ["Area", "Production"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")


# =====================================================
# TOP AREA RECORDS
# =====================================================

print("\n=== TOP 15 AREA RECORDS ===")

print(
    df.nlargest(15, "Area")[columns].to_string(index=False)
)


# =====================================================
# TOP PRODUCTION RECORDS
# =====================================================

print("\n=== TOP 15 PRODUCTION RECORDS ===")

print(
    df.nlargest(15, "Production")[columns].to_string(index=False)
)


# =====================================================
# PRODUCTION PER AREA
# =====================================================

print("\n=== PRODUCTION PER AREA: TOP 15 ===")

valid = df[
    df["Area"].gt(0)
    & df["Production"].notna()
    & np.isfinite(df["Area"])
    & np.isfinite(df["Production"])
].copy()

valid["production_per_area"] = (
    valid["Production"] / valid["Area"]
)

print(
    valid.nlargest(15, "production_per_area")[
        columns + ["production_per_area"]
    ].to_string(index=False)
)


# =====================================================
# ZERO PRODUCTION WITH POSITIVE AREA
# =====================================================

print("\n=== ZERO PRODUCTION WITH POSITIVE AREA ===")

zero = df[
    df["Area"].gt(0)
    & df["Production"].eq(0)
]

print(f"Count: {len(zero):,}")

print(
    zero[columns]
    .head(10)
    .to_string(index=False)
)


print("\n=== EXTREME VALUE INSPECTION COMPLETE ===")
