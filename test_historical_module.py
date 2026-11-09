
from pprint import pprint

from historical_insights import (
    get_district_crop_ranking,
    get_crop_production_trend,
)


def main():

    # ================================================
    # DISTRICT CROP RANKING
    # ================================================

    print("=== DISTRICT CROP RANKING ===")

    try:
        ranking = get_district_crop_ranking(
            state="Andhra Pradesh",
            district="ANANTAPUR",
            season="Kharif",
            limit=5,
        )

        pprint(ranking, sort_dicts=False)

    except Exception as exc:
        print(
            f"District crop ranking test failed: "
            f"{type(exc).__name__}: {exc}"
        )

    # ================================================
    # GROUNDNUT PRODUCTION TREND
    # ================================================

    print("\n=== GROUNDNUT PRODUCTION TREND ===")

    try:
        trend = get_crop_production_trend(
            state="Andhra Pradesh",
            district="ANANTAPUR",
            crop="Groundnut",
            season="Kharif",
        )

        pprint(trend, sort_dicts=False)

    except Exception as exc:
        print(
            f"Production trend test failed: "
            f"{type(exc).__name__}: {exc}"
        )

    # ================================================
    # COMPLETION
    # ================================================

    print("\nHistorical analytics module test complete.")


if __name__ == "__main__":
    main()
