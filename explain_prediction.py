
import joblib
import shap
import pandas as pd
import numpy as np

from functools import lru_cache
from pathlib import Path
from time import perf_counter


# =====================================================
# CONFIGURATION
# =====================================================

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "models" / "tabpfn_crop_model.joblib"
DATASET_PATH = BASE_DIR / "data" / "raw" / "Crop_recommendation.csv"

FEATURES = [
    "N", "P", "K", "temperature",
    "humidity", "ph", "rainfall",
]

BACKGROUND_SIZE = 5
SHAP_SAMPLES = 10


# =====================================================
# LOAD MODEL AND DATASET ONCE
# =====================================================

MODEL = joblib.load(MODEL_PATH)

dataset = pd.read_csv(DATASET_PATH)

if not all(feature in dataset.columns for feature in FEATURES):
    raise ValueError("Dataset is missing required features.")

BACKGROUND = dataset[FEATURES].sample(
    n=min(BACKGROUND_SIZE, len(dataset)),
    random_state=42
).reset_index(drop=True)

# Dataset statistics used for input interpretation.
FEATURE_STATS = {}

for feature in FEATURES:
    FEATURE_STATS[feature] = {
        "min": float(dataset[feature].min()),
        "max": float(dataset[feature].max()),
        "q25": float(dataset[feature].quantile(0.25)),
        "median": float(dataset[feature].median()),
        "q75": float(dataset[feature].quantile(0.75)),
    }


# =====================================================
# CACHED SHAP EXPLAINER
# =====================================================

@lru_cache(maxsize=22)
def get_explainer(class_index):

    def predict_single_class(data):
        data = pd.DataFrame(data, columns=FEATURES)
        return MODEL.predict_proba(data)[:, class_index]

    return shap.KernelExplainer(
        predict_single_class,
        BACKGROUND
    )


# =====================================================
# CACHED EXPLANATION CALCULATION
# =====================================================

@lru_cache(maxsize=128)
def calculate_cached_explanation(input_values):

    sample = pd.DataFrame(
        [input_values],
        columns=FEATURES
    )

    # TabPFN prediction.
    probabilities = MODEL.predict_proba(sample)[0]

    predicted_index = int(np.argmax(probabilities))

    # Explain only the predicted crop.
    explainer = get_explainer(predicted_index)

    shap_values = explainer.shap_values(
        sample,
        nsamples=SHAP_SAMPLES
    )

    if isinstance(shap_values, list):
        shap_values = shap_values[0]

    values = np.asarray(shap_values).squeeze()

    if values.ndim != 1 or len(values) != len(FEATURES):
        raise ValueError(
            f"Unexpected SHAP output shape: {np.asarray(shap_values).shape}"
        )

    return (
        predicted_index,
        tuple(float(x) for x in probabilities),
        tuple(float(x) for x in values)
    )


# =====================================================
# INPUT CONDITION ANALYSIS
# =====================================================

def analyze_input_conditions(sample):

    results = []

    for feature in FEATURES:

        value = float(sample[feature])
        stats = FEATURE_STATS[feature]

        if value < stats["q25"]:
            condition = "Low"
            description = "Below the lower quartile of the dataset."

        elif value > stats["q75"]:
            condition = "High"
            description = "Above the upper quartile of the dataset."

        else:
            condition = "Typical"
            description = "Within the middle 50% of the dataset."

        results.append({
            "feature": feature,
            "value": value,
            "condition": condition,
            "dataset_min": stats["min"],
            "dataset_max": stats["max"],
            "dataset_median": stats["median"],
            "description": description
        })

    return results


# =====================================================
# GENERATE PREDICTION SUMMARY
# =====================================================

def generate_prediction_summary(
    crop,
    probability,
    top_factors,
    positive_factors,
    negative_factors
):

    percentage = round(probability * 100, 2)

    if top_factors:
        important_features = [
            item["feature"] for item in top_factors[:3]
        ]
        feature_text = ", ".join(important_features)
    else:
        feature_text = "the supplied agricultural parameters"

    if positive_factors:
        positive_text = ", ".join(
            item["feature"] for item in positive_factors[:3]
        )
    else:
        positive_text = "no positive SHAP contributions"

    if negative_factors:
        negative_text = ", ".join(
            item["feature"] for item in negative_factors[:3]
        )
    else:
        negative_text = "no negative SHAP contributions"

    return (
        f"{crop} is the leading model recommendation with a "
        f"predicted probability of {percentage}%. "
        f"The most influential parameters are {feature_text}. "
        f"Positive contributions include {positive_text}, while "
        f"negative contributions include {negative_text}. "
        f"These SHAP values describe the model's prediction, "
        f"not agricultural causation or guaranteed crop suitability."
    )


# =====================================================
# EXPLAIN PREDICTION
# =====================================================

def explain_prediction(input_data):

    start_time = perf_counter()

    # Validate input.
    missing = [
        feature for feature in FEATURES
        if feature not in input_data
    ]

    if missing:
        raise ValueError(f"Missing input features: {missing}")

    sample = {
        feature: float(input_data[feature])
        for feature in FEATURES
    }

    sample_df = pd.DataFrame([sample])

    if not np.isfinite(sample_df.to_numpy()).all():
        raise ValueError("Input contains invalid numeric values.")

    input_values = tuple(sample[feature] for feature in FEATURES)

    # Get cached or newly calculated prediction and SHAP values.
    predicted_index, probabilities, shap_values = (
        calculate_cached_explanation(input_values)
    )

    probabilities = np.asarray(probabilities)
    values = np.asarray(shap_values)

    predicted_crop = str(MODEL.classes_[predicted_index])
    predicted_probability = float(probabilities[predicted_index])

    # =================================================
    # ALL SEVEN FEATURE CONTRIBUTIONS
    # =================================================

    explanation = []

    for i, feature in enumerate(FEATURES):

        explanation.append({
            "feature": feature,
            "value": float(sample[feature]),
            "shap_value": float(values[i]),
            "impact": (
                "Positive" if values[i] > 0
                else "Negative" if values[i] < 0
                else "Neutral"
            )
        })

    explanation.sort(
        key=lambda item: abs(item["shap_value"]),
        reverse=True
    )

    # =================================================
    # TOP THREE INFLUENTIAL FEATURES
    # =================================================

    top_factors = explanation[:3]

    # =================================================
    # POSITIVE AND NEGATIVE CONTRIBUTIONS
    # =================================================

    positive_factors = [
        item for item in explanation
        if item["shap_value"] > 0
    ]

    negative_factors = [
        item for item in explanation
        if item["shap_value"] < 0
    ]

    # =================================================
    # TOP THREE CROP PROBABILITIES
    # =================================================

    top_indices = np.argsort(probabilities)[::-1][:3]

    top_crops = []

    for index in top_indices:

        top_crops.append({
            "crop": str(MODEL.classes_[index]),
            "probability": float(probabilities[index]),
            "percentage": round(
                float(probabilities[index]) * 100, 2
            )
        })

    probability_gap = None

    if len(top_crops) >= 2:
        probability_gap = round(
            (
                top_crops[0]["probability"]
                - top_crops[1]["probability"]
            ) * 100,
            2
        )

    # =================================================
    # INPUT CONDITION ANALYSIS
    # =================================================

    input_analysis = analyze_input_conditions(sample)

    # =================================================
    # NATURAL LANGUAGE SUMMARY
    # =================================================

    prediction_summary = generate_prediction_summary(
        predicted_crop,
        predicted_probability,
        top_factors,
        positive_factors,
        negative_factors
    )

    # =================================================
    # RESPONSE
    # =================================================

    elapsed_time = round(
        perf_counter() - start_time,
        3
    )

    return {
        # Existing response fields.
        "predicted_crop": predicted_crop,
        "predicted_probability": predicted_probability,
        "explanation": explanation,
        "explanation_time": elapsed_time,

        # New explanation fields.
        "top_factors": top_factors,
        "positive_factors": positive_factors,
        "negative_factors": negative_factors,
        "input_analysis": input_analysis,
        "prediction_summary": prediction_summary,

        "top_crops": top_crops,

        "probability_analysis": {
            "top_crop": top_crops[0]["crop"],
            "second_crop": (
                top_crops[1]["crop"]
                if len(top_crops) > 1 else None
            ),
            "probability_difference": probability_gap
        },

        "note": (
            "SHAP values explain how input features influence "
            "the selected crop's predicted probability relative "
            "to the background dataset. They do not establish "
            "agricultural causation."
        )
    }


# =====================================================
# TEST
# =====================================================

if __name__ == "__main__":

    example = {
        "N": 90,
        "P": 42,
        "K": 43,
        "temperature": 20.88,
        "humidity": 82,
        "ph": 6.5,
        "rainfall": 202.94,
    }

    result = explain_prediction(example)

    print("\nPREDICTION")
    print("Crop:", result["predicted_crop"])
    print(
        "Probability:",
        round(result["predicted_probability"] * 100, 2),
        "%"
    )

    print("\nTOP THREE INFLUENTIAL FEATURES")

    for item in result["top_factors"]:
        print(
            item["feature"],
            round(item["shap_value"], 6)
        )

    print("\nPOSITIVE CONTRIBUTIONS")

    for item in result["positive_factors"]:
        print(item["feature"], item["shap_value"])

    print("\nNEGATIVE CONTRIBUTIONS")

    for item in result["negative_factors"]:
        print(item["feature"], item["shap_value"])

    print("\nINPUT CONDITION ANALYSIS")

    for item in result["input_analysis"]:
        print(
            item["feature"],
            item["value"],
            item["condition"]
        )

    print("\nTOP THREE CROPS")

    for item in result["top_crops"]:
        print(item["crop"], item["percentage"], "%")

    print("\nPREDICTION SUMMARY")
    print(result["prediction_summary"])

    print("\nEXPLANATION TIME:")
    print(result["explanation_time"], "seconds")

    print("\nCACHE INFORMATION:")
    print(calculate_cached_explanation.cache_info())
