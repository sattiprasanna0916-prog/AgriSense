
import pandas as pd
from pathlib import Path

path = Path("data/raw/crop_production.csv")
df = pd.read_csv(path)

print("\n=== MISSING PRODUCTION ===")
missing = df[df["Production"].isna()]
print(f"Missing records: {len(missing):,}")
print(missing.head(10).to_string(index=False))

print("\n=== ZERO PRODUCTION ===")
zero = df[df["Production"].eq(0)]
print(f"Zero-production records: {len(zero):,}")
print(zero.head(10).to_string(index=False))

print("\n=== AREA AND PRODUCTION EXTREMES ===")
for col in ["Area", "Production"]:
    print(f"\n{col}:")
    print(df[col].nlargest(10).to_string())

print("\n=== POTENTIAL DUPLICATE KEYS ===")
keys = [
    "State_Name", "District_Name",
    "Crop_Year", "Season", "Crop"
]
duplicate_keys = df.duplicated(subset=keys, keep=False)
print(f"Records sharing a district/year/season/crop key: "
      f"{duplicate_keys.sum():,}")
print(df.loc[duplicate_keys, keys + ["Area", "Production"]]
      .head(15).to_string(index=False))

print("\n=== RECORD COUNTS BY YEAR ===")
print(df.groupby("Crop_Year").size().to_string())

print("\n=== PRODUCTION MISSINGNESS BY SEASON ===")
print(df.groupby("Season")["Production"]
      .agg(total="size", missing="count").assign(
          missing=lambda x: x["total"] - x["missing"]
      ).to_string())

print("\n=== QUALITY AUDIT COMPLETE ===")
