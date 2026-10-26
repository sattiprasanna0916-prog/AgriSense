
import pandas as pd

FILE = "data/processed/historical_individual_crop_records.csv"
df = pd.read_csv(FILE)

print("=== DATASET SUMMARY ===")
print(f"Records: {len(df):,}")
print(f"Years: {df['Crop_Year'].min()}–{df['Crop_Year'].max()}")
print(f"States: {df['State_Name'].nunique()}")
print(f"Districts: {df['District_Name'].nunique()}")
print(f"Crop labels: {df['Crop'].nunique()}")

print("\n=== SAMPLE DISTRICTS ===")
print(
    df[["State_Name", "District_Name"]]
    .drop_duplicates()
    .sort_values(["State_Name", "District_Name"])
    .head(15)
    .to_string(index=False)
)

print("\n=== MOST FREQUENT INDIVIDUAL CROPS ===")
print(df["Crop"].value_counts().head(15).to_string())

print("\n=== SAMPLE HISTORICAL CROP RANKING ===")
district = "ANANTAPUR"
season = "Kharif"

sample = df[
    (df["District_Name"].str.upper() == district)
    & (df["Season"].str.casefold() == season.casefold())
]

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
        .sort_values("total_production", ascending=False)
    )
    print(ranking.head(10).to_string(index=False))

print("\nHistorical insights test complete.")
