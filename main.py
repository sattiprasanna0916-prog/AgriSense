
import json
import logging
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sklearn.model_selection import train_test_split

from agri_chatbot import router as chatbot_router
from auth import router as auth_router
from database import engine, Base
from explain_prediction import MODEL as model
from explain_prediction import explain_prediction
from historical_insights import (
    get_district_crop_ranking,
    get_crop_production_trend,
)
from input_validation import CropInputValidator


# =====================================================
# CONFIGURATION
# =====================================================

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "models" / "tabpfn_crop_model.joblib"
METRICS_PATH = BASE_DIR / "artifacts" / "evaluation_metrics.json"
DATA_PATH = BASE_DIR / "data" / "raw" / "Crop_recommendation.csv"

THRESHOLDS_PATH = (
    BASE_DIR / "artifacts" / "reliability_thresholds.json"
)

HISTORICAL_DATA_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "historical_individual_crop_records.csv"
)

FEATURES = [
    "N",
    "P",
    "K",
    "temperature",
    "humidity",
    "ph",
    "rainfall",
]

DEFAULT_UNUSUAL_THRESHOLD = 0.9158
DEFAULT_SEVERE_THRESHOLD = 3.00

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =====================================================
# LOAD MODEL AND DATA
# =====================================================

if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Model not found: {MODEL_PATH}")

if not METRICS_PATH.exists():
    raise FileNotFoundError(f"Metrics not found: {METRICS_PATH}")

if not DATA_PATH.exists():
    raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")

# The model is loaded by explain_prediction.py and shared here.
if model is None:
    raise RuntimeError("TabPFN model could not be loaded.")

with METRICS_PATH.open("r", encoding="utf-8") as file:
    evaluation_metrics = json.load(file)

dataset = pd.read_csv(DATA_PATH)

missing_columns = set(FEATURES + ["label"]) - set(dataset.columns)

if missing_columns:
    raise ValueError(
        f"Crop dataset is missing columns: {sorted(missing_columns)}"
    )


# =====================================================
# LOAD RELIABILITY THRESHOLDS
# =====================================================

unusual_threshold = DEFAULT_UNUSUAL_THRESHOLD
severe_threshold = DEFAULT_SEVERE_THRESHOLD

if THRESHOLDS_PATH.exists():

    try:
        with THRESHOLDS_PATH.open("r", encoding="utf-8") as file:
            threshold_data = json.load(file)

        selected = threshold_data.get("selected_thresholds", {})

        unusual_threshold = float(
            selected.get(
                "threshold_unusual",
                unusual_threshold,
            )
        )

        severe_threshold = float(
            selected.get(
                "threshold_severe",
                severe_threshold,
            )
        )

    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"Could not load reliability thresholds: {exc}"
        ) from exc


# =====================================================
# INITIALIZE INPUT VALIDATOR
# =====================================================

# Use the same split as the model training and threshold derivation.
X_train, _, _, _ = train_test_split(
    dataset[FEATURES],
    dataset["label"],
    test_size=0.2,
    random_state=42,
    stratify=dataset["label"],
)

input_validator = CropInputValidator(
    X_train,
    unusual_distance_threshold=unusual_threshold,
    severe_distance_threshold=severe_threshold,
)

observed_ranges = input_validator.ranges


# =====================================================
# FASTAPI APPLICATION
# =====================================================

app = FastAPI(
    title="Explainable AI Agricultural Decision Support System",
    description="TabPFN-based educational crop recommendation prototype",
    version="1.0.0",
)

Base.metadata.create_all(bind=engine)

app.include_router(auth_router)
app.include_router(chatbot_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================
# INPUT SCHEMA
# =====================================================

class CropInput(BaseModel):

    N: float = Field(ge=0, le=10000, allow_inf_nan=False)
    P: float = Field(ge=0, le=10000, allow_inf_nan=False)
    K: float = Field(ge=0, le=10000, allow_inf_nan=False)

    temperature: float = Field(
        ge=-50,
        le=70,
        allow_inf_nan=False,
    )

    humidity: float = Field(
        ge=0,
        le=100,
        allow_inf_nan=False,
    )

    ph: float = Field(
        ge=0,
        le=14,
        allow_inf_nan=False,
    )

    rainfall: float = Field(
        ge=0,
        le=10000,
        allow_inf_nan=False,
    )

    state: str | None = None
    district: str | None = None
    season: str | None = None


# =====================================================
# HOME AND HEALTH
# =====================================================

@app.get("/")
def home():
    return {
        "message": "Crop Recommendation API is running",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model": "TabPFNClassifier",
        "model_loaded": model is not None,
    }


# =====================================================
# MODEL EVALUATION
# =====================================================

@app.get("/evaluation")
def evaluation():
    return evaluation_metrics


# =====================================================
# CROP PREDICTION
# =====================================================

@app.post("/predict")
def predict(data: CropInput):

    try:
        values = data.model_dump()

        # Only the original seven features go to TabPFN.
        input_values = {
            feature: values[feature]
            for feature in FEATURES
        }

        input_df = pd.DataFrame(
            [input_values],
            columns=FEATURES,
        )

        # Validate physical limits, guardrails and data familiarity.
        validation = input_validator.validate(values)
        warnings = validation["warnings"]

        # Withhold recommendation for severe or invalid inputs.
        if validation["recommendation_withheld"]:

            return {
                "predicted_crop": "Recommendation Withheld",
                "top_3": [],
                "input_warnings": warnings,
                "observed_training_ranges": observed_ranges,
                "historical_comparison": None,
                "notice": (
                    "Recommendation withheld: The input measurements "
                    "violate physical feasibility, exceed agricultural "
                    "guardrails, or represent a severely unfamiliar "
                    "combination. Please review and verify the inputs."
                ),
                "input_validation": {
                    "status": validation["range_status"],
                    "distribution_status": validation["distribution_status"],
                    "reliability_level": validation["reliability_level"],
                    "recommendation_withheld": True,
                },
                "distribution_check": {
                    "nearest_neighbor_distance": validation[
                        "nearest_neighbor_distance"
                    ],
                    "reference_distance_threshold": validation[
                        "reference_distance_threshold"
                    ],
                    "severe_distance_threshold": validation[
                        "severe_distance_threshold"
                    ],
                },
                "reliability_level": validation["reliability_level"],
                "recommendation_withheld": True,
            }

        # Generate crop probabilities.
        probabilities = model.predict_proba(input_df)[0]
        classes = list(model.classes_)

        ranked = sorted(
            zip(classes, probabilities),
            key=lambda item: item[1],
            reverse=True,
        )

        top_3 = [
            {
                "crop": str(crop),
                "probability": round(float(probability), 6),
                "percentage": round(float(probability) * 100, 2),
            }
            for crop, probability in ranked[:3]
        ]

        result = {
            "predicted_crop": str(ranked[0][0]),
            "top_3": top_3,
            "input_warnings": warnings,
            "observed_training_ranges": observed_ranges,
            "historical_comparison": None,
            "notice": (
                "Educational decision-support prototype. Predictions "
                "are not guarantees of crop suitability or yield. "
                "Model probabilities are not calibrated confidence "
                "estimates."
            ),
            "input_validation": {
                "status": validation["range_status"],
                "distribution_status": validation["distribution_status"],
                "reliability_level": validation["reliability_level"],
                "recommendation_withheld": False,
            },
            "distribution_check": {
                "nearest_neighbor_distance": validation[
                    "nearest_neighbor_distance"
                ],
                "reference_distance_threshold": validation[
                    "reference_distance_threshold"
                ],
                "severe_distance_threshold": validation[
                    "severe_distance_threshold"
                ],
            },
            "reliability_level": validation["reliability_level"],
            "recommendation_withheld": False,
        }

        # Retrieve historical evidence when location is provided.
        state = (data.state or "").strip()
        district = (data.district or "").strip()
        season = (data.season or "").strip()

        if state and district and season:

            try:
                historical = get_district_crop_ranking(
                    state=state,
                    district=district,
                    season=season,
                    limit=10,
                )

                historical_payload = (
                    historical.get("crops", [])
                    if isinstance(historical, dict)
                    else historical
                    if isinstance(historical, list)
                    else []
                )

                historical_names = {
                    str(
                        record.get(
                            "Crop",
                            record.get("crop", ""),
                        )
                    ).strip().casefold()

                    for record in historical_payload
                    if isinstance(record, dict)
                }

                compared_crops = [
                    {
                        **item,
                        "found_in_historical_ranking": (
                            item["crop"].casefold() in historical_names
                        ),
                    }
                    for item in top_3
                ]

                result["historical_comparison"] = {
                    "state": state,
                    "district": district,
                    "season": season,
                    "historical_ranking": historical,
                    "top_3_comparison": compared_crops,
                    "message": (
                        "Historical records provide regional context. "
                        "They do not prove current suitability or "
                        "guarantee future production."
                    ),
                }

            except Exception as exc:
                logger.exception("Historical crop ranking failed")

                result["historical_comparison"] = {
                    "error": type(exc).__name__,
                    "message": (
                        "The soil-based prediction succeeded, but "
                        "historical evidence could not be retrieved."
                    ),
                }

        return result

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception("Crop prediction failed")

        raise HTTPException(
            status_code=500,
            detail="An internal error occurred while generating the prediction.",
        ) from exc


# =====================================================
# SHAP EXPLANATION
# =====================================================

@app.post("/explain")
def explain(data: CropInput):

    try:
        values = data.model_dump()

        validation = input_validator.validate(values)

        if validation["recommendation_withheld"]:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Cannot generate explanation because the "
                    "recommendation was withheld by input validation."
                ),
            )

        input_values = {
            feature: values[feature]
            for feature in FEATURES
        }

        # Reuse the cached SHAP implementation.
        return explain_prediction(input_values)

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception("SHAP explanation failed")

        raise HTTPException(
            status_code=500,
            detail="Could not generate the crop explanation.",
        ) from exc


# =====================================================
# HISTORICAL CROP RANKING
# =====================================================

@app.get("/historical/ranking")
def historical_ranking(
    state: str,
    district: str,
    season: str,
    limit: int = 10,
):

    try:
        return get_district_crop_ranking(
            state=state,
            district=district,
            season=season,
            limit=limit,
        )

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=500,
            detail="Historical dataset is unavailable.",
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception("Historical ranking failed")

        raise HTTPException(
            status_code=500,
            detail="Could not retrieve historical crop rankings.",
        ) from exc


# =====================================================
# HISTORICAL LOCATION OPTIONS
# =====================================================

@lru_cache(maxsize=1)
def load_historical_locations():

    if not HISTORICAL_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Historical dataset not found: {HISTORICAL_DATA_PATH}"
        )

    df = pd.read_csv(
        HISTORICAL_DATA_PATH,
        usecols=["State_Name", "District_Name"],
    )

    df["State_Name"] = (
        df["State_Name"].astype("string").str.strip()
    )

    df["District_Name"] = (
        df["District_Name"].astype("string").str.strip()
    )

    df = df.dropna(
        subset=["State_Name", "District_Name"]
    )

    # Preserve the original application filtering rule.
    df = df[
        df["State_Name"].str.casefold()
        != "andaman and nicobar islands"
    ]

    return df


@app.get("/historical/locations")
def historical_locations(state: str | None = None):

    try:
        df = load_historical_locations()

        states = sorted(
            df["State_Name"].unique().tolist(),
            key=str.casefold,
        )

        districts = []

        if state:

            selected_state = state.strip().casefold()

            districts = sorted(
                df.loc[
                    df["State_Name"].str.casefold()
                    == selected_state,
                    "District_Name",
                ].unique().tolist(),
                key=str.casefold,
            )

        return {
            "states": states,
            "districts": districts,
        }

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=500,
            detail="Historical location dataset is unavailable.",
        ) from exc

    except Exception as exc:
        logger.exception("Historical location lookup failed")

        raise HTTPException(
            status_code=500,
            detail="Could not load historical locations.",
        ) from exc


# =====================================================
# HISTORICAL PRODUCTION TREND
# =====================================================

@app.get("/historical/trend")
def historical_trend(
    state: str,
    district: str,
    crop: str,
    season: str,
):

    try:
        return get_crop_production_trend(
            state=state,
            district=district,
            crop=crop,
            season=season,
        )

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=500,
            detail="Historical dataset is unavailable.",
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception("Historical production trend failed")

        raise HTTPException(
            status_code=500,
            detail="Could not retrieve historical production trends.",
        ) from exc
