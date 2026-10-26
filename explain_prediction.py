
import joblib
import shap
import pandas as pd

MODEL_PATH = "models/tabpfn_crop_model.joblib"
DATASET_PATH = "data/raw/Crop_recommendation.csv"

FEATURES = [
    "N",
    "P",
    "K",
    "temperature",
    "humidity",
    "ph",
    "rainfall",
]


def explain_prediction(input_data):
    model = joblib.load(MODEL_PATH)

    dataset = pd.read_csv(DATASET_PATH)
    background = dataset[FEATURES].sample(
        n=10, random_state=42
    )

    sample = pd.DataFrame([input_data], columns=FEATURES)

    explainer = shap.KernelExplainer(
        model.predict_proba,
        background,
    )

    shap_values = explainer.shap_values(
        sample,
        nsamples=20,
    )

    probabilities = model.predict_proba(sample)[0]
    predicted_index = probabilities.argmax()
    predicted_crop = model.classes_[predicted_index]

    # SHAP 0.54.1 returns (samples, features, classes).
    values = shap_values[0, :, predicted_index]

    explanation = sorted(
        [
            {
                "feature": feature,
                "value": float(sample.iloc[0][feature]),
                "shap_value": float(values[i]),
            }
            for i, feature in enumerate(FEATURES)
        ],
        key=lambda item: abs(item["shap_value"]),
        reverse=True,
    )

    return {
        "predicted_crop": str(predicted_crop),
        "explanation": explanation,
        "note": (
            "SHAP values explain changes in the model output "
            "relative to the background dataset. They do not "
            "establish agricultural causation."
        ),
    }


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

    print("Predicted crop:", result["predicted_crop"])
    print("\nFeature contributions:")

    for item in result["explanation"]:
        print(
            f"{item['feature']}: "
            f"SHAP={item['shap_value']:.6f}"
        )

    print("\n", result["note"])
