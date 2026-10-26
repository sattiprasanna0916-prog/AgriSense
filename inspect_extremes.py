
import pandas as pd

df = pd.read_csv("data/raw/crop_production.csv")

columns = [
    "State_Name",
    "District_Name",
    "Crop_Year",
    "Season",
    "Crop",
    "Area",
    "Production",
]

print("\n=== TOP 15 AREA RECORDS ===")
print(
    df.nlargest(15, "Area")[columns].to_string(index=False)
)

print("\n=== TOP 15 PRODUCTION RECORDS ===")
print(
    df.nlargest(15, "Production")[columns].to_string(index=False)
)

print("\n=== PRODUCTION PER AREA: TOP 15 ===")
valid = df[
    df["Area"].gt(0)
    & df["Production"].notna()
].copy()

valid["production_per_area"] = (
    valid["Production"] / valid["Area"]
)

print(
    valid.nlargest(15, "production_per_area")[
        columns + ["production_per_area"]
    ].to_string(index=False)
)

print("\n=== ZERO PRODUCTION WITH POSITIVE AREA ===")
zero = df[
    df["Area"].gt(0)
    & df["Production"].eq(0)
]

print(f"Count: {len(zero):,}")
print(zero[columns].head(10).to_string(index=False))
