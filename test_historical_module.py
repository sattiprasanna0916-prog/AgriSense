
from historical_insights import (
    get_district_crop_ranking,
    get_crop_production_trend,
)

print("=== DISTRICT CROP RANKING ===")
ranking = get_district_crop_ranking(
    state="Andhra Pradesh",
    district="ANANTAPUR",
    season="Kharif",
    limit=5,
)
print(ranking)

print("\n=== GROUNDNUT PRODUCTION TREND ===")
trend = get_crop_production_trend(
    state="Andhra Pradesh",
    district="ANANTAPUR",
    crop="Groundnut",
    season="Kharif",
)
print(trend)

print("\nHistorical analytics module test complete.")
