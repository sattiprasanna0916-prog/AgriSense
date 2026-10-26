
import json
from pathlib import Path
import shap
import joblib
import pandas as pd
from agri_chatbot import router as chatbot_router
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from auth import router as auth_router
from input_validation import CropInputValidator
from historical_insights import (
    get_district_crop_ranking,
    get_crop_production_trend,
)
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "tabpfn_crop_model.joblib"
METRICS_PATH = BASE_DIR / "artifacts" / "evaluation_metrics.json"
DATA_PATH = BASE_DIR / "data" / "raw" / "Crop_recommendation.csv"

FEATURES = [
    "N", "P", "K", "temperature",
    "humidity", "ph", "rainfall"
]

app = FastAPI(
    title="Explainable AI Agricultural Decision Support System",
    description="TabPFN-based educational crop recommendation prototype",
    version="1.0.0",
)
app.include_router(auth_router)
app.include_router(chatbot_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CropInput(BaseModel):
    N: float = Field(ge=0, le=10000)
    P: float = Field(ge=0, le=10000)
    K: float = Field(ge=0, le=10000)
    temperature: float = Field(ge=-50, le=70)
    humidity: float = Field(ge=0, le=100)
    ph: float = Field(ge=0, le=14)
    rainfall: float = Field(ge=0, le=10000)
    state: str | None = None
    district: str | None = None
    season: str | None = None

# Load the model, metrics and observed feature ranges once.
if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Model not found: {MODEL_PATH}")

if not METRICS_PATH.exists():
    raise FileNotFoundError(f"Metrics not found: {METRICS_PATH}")

if not DATA_PATH.exists():
    raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")

model = joblib.load(MODEL_PATH)

with METRICS_PATH.open("r", encoding="utf-8") as file:
    evaluation_metrics = json.load(file)

dataset = pd.read_csv(DATA_PATH)

THRESHOLDS_PATH = BASE_DIR / "artifacts" / "reliability_thresholds.json"
unusual_threshold = 0.9158
severe_threshold = 3.00
if THRESHOLDS_PATH.exists():
    try:
        with THRESHOLDS_PATH.open("r", encoding="utf-8") as f:
            thresh_data = json.load(f).get("selected_thresholds", {})
            unusual_threshold = thresh_data.get("threshold_unusual", unusual_threshold)
            severe_threshold = thresh_data.get("threshold_severe", severe_threshold)
    except Exception:
        pass

input_validator = CropInputValidator(
    dataset,
    unusual_distance_threshold=unusual_threshold,
    severe_distance_threshold=severe_threshold,
)
observed_ranges = input_validator.ranges


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


@app.get("/evaluation")
def evaluation():
    return evaluation_metrics



@app.post("/predict")
def predict(data: CropInput):
    try:
        values = data.model_dump()

        # TabPFN must receive only its original seven features.
        input_df = pd.DataFrame(
            [{feature: values[feature] for feature in FEATURES}],
            columns=FEATURES,
        )

        validation = input_validator.validate(values)
        warnings = validation["warnings"]

        # Withhold recommendation if inputs are severely unfamiliar or invalid
        if validation["recommendation_withheld"]:
            return {
                "predicted_crop": "Recommendation Withheld",
                "top_3": [],
                "input_warnings": warnings,
                "observed_training_ranges": observed_ranges,
                "historical_comparison": None,
                "notice": (
                    "Recommendation withheld: The input measurements violate "
                    "physical feasibility, exceed agricultural guardrails, or "
                    "represent a severely unfamiliar combination. Please review "
                    "and verify the input measurements."
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
                "probability": round(float(prob), 6),
                "percentage": round(float(prob) * 100, 2),
            }
            for crop, prob in ranked[:3]
        ]

        result = {
            "predicted_crop": str(ranked[0][0]),
            "top_3": top_3,
            "input_warnings": warnings,
            "observed_training_ranges": observed_ranges,
            "historical_comparison": None,
            "notice": (
                "Educational decision-support prototype. "
                "Predictions are not guarantees of crop suitability "
                "or yield. Model probabilities are not calibrated "
                "confidence estimates."
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

        # Retrieve historical evidence only when all location
        # fields have been provided.
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

                # Support the historical lookup's existing response
                # structure without assuming its exact field names.
                records = (
                    historical
                    if isinstance(historical, list)
                    else historical.get("ranking", [])
                    if isinstance(historical, dict)
                    else []
                )

                
                
                historical_payload = (
                    historical.get("crops", [])
                    if isinstance(historical, dict)
                    else historical
                )

                historical_names = {
                    str(record.get("Crop", record.get("crop", "")))
                    .strip()
                    .casefold()
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

            except (ValueError, FileNotFoundError) as exc:
                result["historical_comparison"] = {
                    "error": str(exc),
                    "message": (
                        "The soil-based prediction succeeded, but "
                        "historical evidence could not be retrieved."
                    ),
                }

        return result

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {type(exc).__name__}: {exc}",
        ) from exc

@app.post("/explain")
def explain(data: CropInput):
    try:
        values = data.model_dump()

        validation = input_validator.validate(values)
        if validation["recommendation_withheld"]:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Cannot generate explanation: recommendation is withheld "
                    "because input measurements are severely unfamiliar or invalid. "
                    f"Details: {'; '.join(validation['warnings'])}"
                ),
            )

        input_df = pd.DataFrame([values], columns=FEATURES)

        background = (
            pd.read_csv("data/raw/Crop_recommendation.csv")
            [FEATURES]
            .sample(n=10, random_state=42)
        )

        explainer = shap.KernelExplainer(
            model.predict_proba,
            background,
        )

        shap_values = explainer.shap_values(
            input_df,
            nsamples=20,
        )

        probabilities = model.predict_proba(input_df)[0]
        predicted_index = int(probabilities.argmax())
        predicted_crop = str(model.classes_[predicted_index])

        # SHAP 0.54.1 output: samples × features × classes
        contributions = shap_values[0, :, predicted_index]

        explanation = sorted(
            [
                {
                    "feature": feature,
                    "value": float(values[feature]),
                    "shap_value": round(float(contributions[i]), 6),
                }
                for i, feature in enumerate(FEATURES)
            ],
            key=lambda item: abs(item["shap_value"]),
            reverse=True,
        )

        return {
            "predicted_crop": predicted_crop,
            "explanation": explanation,
            "note": (
                "SHAP values explain model output relative to the "
                "background dataset; they do not establish "
                "agricultural causation."
            ),
        }

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Explanation failed: {type(exc).__name__}: {exc}",
        ) from exc

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
        raise HTTPException(status_code=500, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


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
        raise HTTPException(status_code=500, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
