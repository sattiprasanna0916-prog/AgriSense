
import pandas as pd

df = pd.read_csv("data/raw/crop_production.csv")

print("\n=== LAST FIVE YEARS: RECORD COUNTS ===")
print(df["Crop_Year"].value_counts().sort_index().tail(5).to_string())

print("\n=== RECORD COUNTS BY YEAR AND SEASON ===")
print(
    pd.crosstab(df["Crop_Year"], df["Season"])
    .tail(5)
    .to_string()
)

print("\n=== POSSIBLE AGGREGATE CROP LABELS ===")
aggregate_words = ["total", "other", "misc"]
mask = df["Crop"].str.lower().str.contains(
    "|".join(aggregate_words), na=False
)
print("Number of records:", int(mask.sum()))
print("Distinct labels:")
print(sorted(df.loc[mask, "Crop"].unique().tolist()))

print("\n=== MISSING PRODUCTION BY YEAR ===")
print(
    df.assign(production_missing=df["Production"].isna())
    .groupby("Crop_Year")
    .agg(
        records=("Crop", "size"),
        missing_production=("production_missing", "sum"),
    )
    .tail(8)
    .to_string()
)

print("\n=== COVERAGE CHECK COMPLETE ===")
