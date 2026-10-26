
from pathlib import Path
import pandas as pd

INPUT_FILE = Path("data/raw/crop_production.csv")
OUTPUT_DIR = Path("data/processed")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(INPUT_FILE)

# Standardize text fields without changing crop names themselves.
text_columns = ["State_Name", "District_Name", "Season", "Crop"]
for column in text_columns:
    df[column] = df[column].astype("string").str.strip()

# Keep the original dataset unchanged. Exclude 2015 only from this
# analysis copy because its coverage is much smaller than prior years.
historical = df[df["Crop_Year"] < 2015].copy()

# Production-based analysis requires a known production value.
known_production = historical[historical["Production"].notna()].copy()

# Separate summary/aggregate labels from individual crop labels.
aggregate_labels = {
    "Oilseeds total",
    "Pulses total",
    "Total foodgrain",
}

# Some labels beginning with "Other" are broad categories too.
aggregate_mask = (
    known_production["Crop"].str.lower().isin(
        {label.lower() for label in aggregate_labels}
    )
    | known_production["Crop"].str.lower().str.startswith("other ")
    | known_production["Crop"].str.lower().str.startswith("other")
)

aggregate_records = known_production[aggregate_mask].copy()
crop_records = known_production[~aggregate_mask].copy()

# Save separate analysis files.
known_production.to_csv(
    OUTPUT_DIR / "historical_production_known.csv", index=False
)
crop_records.to_csv(
    OUTPUT_DIR / "historical_individual_crop_records.csv", index=False
)
aggregate_records.to_csv(
    OUTPUT_DIR / "historical_aggregate_crop_records.csv", index=False
)

print("=== HISTORICAL DATA PREPARATION ===")
print(f"Original records: {len(df):,}")
print(f"Records before 2015: {len(historical):,}")
print(f"Records with known production: {len(known_production):,}")
print(f"Individual crop records: {len(crop_records):,}")
print(f"Aggregate/broad-category records: {len(aggregate_records):,}")
print(f"Zero-production records retained: {(known_production['Production'] == 0).sum():,}")
print(f"Years included: {historical['Crop_Year'].min()}–{historical['Crop_Year'].max()}")
print(f"Output directory: {OUTPUT_DIR.resolve()}")
print("\nPreparation complete.")
