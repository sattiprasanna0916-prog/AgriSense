
"""
evaluate_calibration.py
-----------------------
Probability Calibration Evaluation for TabPFN on Crop Recommendation.

Methodology:
1. Reproduces the original stratified 80:20 train/test split.
2. Keeps the held-out 20% test partition untouched.
3. Generates OOF probabilities using 5-fold Stratified CV.
4. Compares:
   - Uncalibrated TabPFN
   - Temperature Scaling
   - Isotonic Calibration (one-vs-rest)
5. Evaluates:
   - Multiclass Log Loss
   - Multiclass Brier Score
   - Top-1 ECE
   - Accuracy
   - Macro F1
   - Mean Top-1 Confidence

Execution:
- Only 5 TabPFN model fits.
- No nested cross-validation.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, Tuple

import numpy as np
import pandas as pd

from scipy.optimize import minimize_scalar

from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import accuracy_score, f1_score, log_loss
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.preprocessing import LabelBinarizer

from tabpfn import TabPFNClassifier


# =============================================================
# CONFIGURATION
# =============================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_PATH = BASE_DIR / "data" / "raw" / "Crop_recommendation.csv"
OUTPUT_PATH = BASE_DIR / "artifacts" / "calibration_evaluation.json"

FEATURES = [
    "N", "P", "K", "temperature",
    "humidity", "ph", "rainfall",
]

RANDOM_STATE = 42
TEST_SIZE = 0.20
N_FOLDS = 5
NUM_BINS_ECE = 10
EPS = 1e-12


# =============================================================
# METRIC FUNCTIONS
# =============================================================

def compute_multiclass_brier(
    y_true_onehot: np.ndarray,
    probas: np.ndarray
) -> Tuple[float, float]:
    """Compute multiclass Brier score."""

    sample_brier = np.sum(
        (probas - y_true_onehot) ** 2,
        axis=1
    )

    brier_sum = float(np.mean(sample_brier))
    brier_mean = float(brier_sum / probas.shape[1])

    return brier_sum, brier_mean


def compute_top1_ece(
    y_true_indices: np.ndarray,
    probas: np.ndarray,
    n_bins: int = NUM_BINS_ECE
) -> Tuple[float, Dict[str, Any]]:
    """Compute Top-1 Expected Calibration Error."""

    confidences = np.max(probas, axis=1)
    predictions = np.argmax(probas, axis=1)

    accuracies = (
        predictions == y_true_indices
    ).astype(float)

    bin_boundaries = np.linspace(
        0.0,
        1.0,
        n_bins + 1
    )

    ece = 0.0
    bin_details = []

    for i in range(n_bins):

        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]

        if i == n_bins - 1:
            in_bin = (
                (confidences >= bin_lower)
                & (confidences <= bin_upper)
            )
        else:
            in_bin = (
                (confidences >= bin_lower)
                & (confidences < bin_upper)
            )

        bin_count = int(np.sum(in_bin))

        if bin_count > 0:

            bin_acc = float(
                np.mean(accuracies[in_bin])
            )

            bin_conf = float(
                np.mean(confidences[in_bin])
            )

            bin_weight = bin_count / len(confidences)
            bin_error = abs(bin_acc - bin_conf)

            ece += bin_weight * bin_error

            bin_details.append({
                "bin_range": [
                    round(bin_lower, 2),
                    round(bin_upper, 2)
                ],
                "count": bin_count,
                "accuracy": round(bin_acc, 4),
                "confidence": round(bin_conf, 4),
                "calibration_error": round(bin_error, 4),
            })

        else:

            bin_details.append({
                "bin_range": [
                    round(bin_lower, 2),
                    round(bin_upper, 2)
                ],
                "count": 0,
                "accuracy": None,
                "confidence": None,
                "calibration_error": 0.0,
            })

    return float(ece), {"bins": bin_details}


# =============================================================
# TEMPERATURE SCALING
# =============================================================

def optimize_temperature(
    probas: np.ndarray,
    y_onehot: np.ndarray
) -> float:
    """Find scalar temperature T > 0 minimizing log loss."""

    p_safe = np.clip(probas, EPS, 1.0)
    log_p = np.log(p_safe)

    def nll(t: float) -> float:

        if t <= 0:
            return 1e9

        scaled_logits = log_p / t

        max_logits = np.max(
            scaled_logits,
            axis=1,
            keepdims=True
        )

        exp_scaled = np.exp(
            scaled_logits - max_logits
        )

        softmax_probs = (
            exp_scaled
            / np.sum(exp_scaled, axis=1, keepdims=True)
        )

        softmax_probs = np.clip(
            softmax_probs,
            EPS,
            1.0
        )

        return -float(
            np.mean(
                np.sum(
                    y_onehot * np.log(softmax_probs),
                    axis=1
                )
            )
        )

    result = minimize_scalar(
        nll,
        bounds=(0.05, 10.0),
        method="bounded"
    )

    if not result.success or not np.isfinite(result.x):
        raise RuntimeError("Temperature optimization failed.")

    return float(result.x)


def apply_temperature(
    probas: np.ndarray,
    temperature: float
) -> np.ndarray:
    """Apply temperature scaling."""

    if temperature <= 0 or not np.isfinite(temperature):
        raise ValueError("Temperature must be positive and finite.")

    p_safe = np.clip(probas, EPS, 1.0)
    log_p = np.log(p_safe)

    scaled = log_p / temperature

    max_scaled = np.max(
        scaled,
        axis=1,
        keepdims=True
    )

    exp_scaled = np.exp(
        scaled - max_scaled
    )

    return exp_scaled / np.sum(
        exp_scaled,
        axis=1,
        keepdims=True
    )


# =============================================================
# MAIN EVALUATION
# =============================================================

def run_calibration_evaluation():

    print("=" * 70)
    print("PROBABILITY CALIBRATION EVALUATION (TabPFN)")
    print("=" * 70)

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}"
        )

    df = pd.read_csv(DATA_PATH)

    required_columns = FEATURES + ["label"]

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing dataset columns: {missing_columns}"
        )

    if df[required_columns].isnull().any().any():
        raise ValueError(
            "Dataset contains missing values."
        )

    X = df[FEATURES].apply(
        pd.to_numeric,
        errors="raise"
    )

    y = df["label"].astype(str).str.strip()

    if not np.isfinite(X.to_numpy(dtype=float)).all():
        raise ValueError(
            "Dataset contains non-finite numeric values."
        )

    if (y == "").any():
        raise ValueError("Dataset contains empty labels.")

    # Reproduce exact train/test split.
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y
    )

    classes = sorted(y_train.unique())
    n_classes = len(classes)

    class_to_idx = {
        c: i for i, c in enumerate(classes)
    }

    if int(y_train.value_counts().min()) < N_FOLDS:
        raise ValueError(
            "Insufficient samples per class for 5-fold CV."
        )

    print(f"Total dataset records:        {len(df)}")
    print(f"Training partition:           {len(X_train)}")
    print(f"Held-out test partition:      {len(X_test)} (untouched)")
    print(f"Classes:                      {n_classes}")

    # =========================================================
    # FIVE-FOLD OOF PREDICTIONS
    # =========================================================

    skf = StratifiedKFold(
        n_splits=N_FOLDS,
        shuffle=True,
        random_state=RANDOM_STATE
    )

    oof_raw_probas = np.zeros(
        (len(X_train), n_classes),
        dtype=np.float64
    )

    oof_y_true = np.empty(
        len(X_train),
        dtype=object
    )

    fold_indices = []

    print(
        f"\nRunning {N_FOLDS}-Fold CV "
        f"on {len(X_train)} training records..."
    )

    start_total_cv = time.perf_counter()

    for fold, (train_idx, val_idx) in enumerate(
        skf.split(X_train, y_train),
        start=1
    ):

        f_train_x = X_train.iloc[train_idx]
        f_train_y = y_train.iloc[train_idx]

        f_val_x = X_train.iloc[val_idx]
        f_val_y = y_train.iloc[val_idx]

        print(f"\n--- Fold {fold}/{N_FOLDS} ---")

        model = TabPFNClassifier(
            device="auto"
        )

        t0 = time.perf_counter()

        model.fit(
            f_train_x,
            f_train_y
        )

        fit_dur = time.perf_counter() - t0

        t0 = time.perf_counter()

        val_probs = model.predict_proba(
            f_val_x
        )

        pred_dur = time.perf_counter() - t0

        print(
            f"TabPFN Fit: {fit_dur:.2f}s | "
            f"Val Inference: {pred_dur:.2f}s"
        )

        # Align fold model classes to global class order.
        fold_class_indices = [
            class_to_idx[str(c)]
            for c in model.classes_
        ]

        for i_sample in range(len(val_idx)):

            for i_col, c_idx in enumerate(
                fold_class_indices
            ):

                oof_raw_probas[
                    val_idx[i_sample],
                    c_idx
                ] = val_probs[i_sample, i_col]

            oof_y_true[val_idx[i_sample]] = (
                f_val_y.iloc[i_sample]
            )

        fold_indices.append(
            (train_idx, val_idx)
        )

    cv_elapsed = (
        time.perf_counter() - start_total_cv
    )

    print(
        f"\nAll {N_FOLDS} folds completed in "
        f"{cv_elapsed:.2f}s "
        f"({cv_elapsed / 60:.1f} minutes)."
    )

    # Validate probability output.
    if (
        not np.isfinite(oof_raw_probas).all()
        or np.any(oof_raw_probas < 0)
    ):
        raise ValueError(
            "Invalid OOF probability values."
        )

    row_sums = oof_raw_probas.sum(axis=1)

    if np.any(row_sums <= EPS):
        raise ValueError(
            "OOF probability matrix contains zero-sum rows."
        )

    oof_raw_probas /= row_sums[:, None]

    # =========================================================
    # ONE-HOT LABELS
    # =========================================================

    lb = LabelBinarizer()

    lb.fit(classes)

    y_true_onehot = lb.transform(
        oof_y_true
    )

    y_true_indices = np.array([
        class_to_idx[label]
        for label in oof_y_true
    ])

    # =========================================================
    # METHOD A: UNCALIBRATED TABPFN
    # =========================================================

    uncal_pred_indices = np.argmax(
        oof_raw_probas,
        axis=1
    )

    uncal_preds = [
        classes[idx]
        for idx in uncal_pred_indices
    ]

    uncal_acc = float(
        accuracy_score(oof_y_true, uncal_preds)
    )

    uncal_f1 = float(
        f1_score(
            oof_y_true,
            uncal_preds,
            average="macro",
            zero_division=0
        )
    )

    uncal_logloss = float(
        log_loss(
            oof_y_true,
            oof_raw_probas,
            labels=classes
        )
    )

    uncal_brier_sum, uncal_brier_mean = (
        compute_multiclass_brier(
            y_true_onehot,
            oof_raw_probas
        )
    )

    uncal_ece, uncal_bin_details = (
        compute_top1_ece(
            y_true_indices,
            oof_raw_probas
        )
    )

    uncal_mean_conf = float(
        np.mean(
            np.max(oof_raw_probas, axis=1)
        )
    )

    print("\n" + "=" * 50)
    print("METHOD A: UNCALIBRATED TabPFN")
    print("=" * 50)

    print(f"Accuracy:                      {uncal_acc:.4f}")
    print(f"Macro F1:                      {uncal_f1:.4f}")
    print(f"Multiclass Log Loss:           {uncal_logloss:.5f}")
    print(f"Multiclass Brier (Sum):        {uncal_brier_sum:.5f}")
    print(f"Multiclass Brier (Mean/class): {uncal_brier_mean:.5f}")
    print(f"Top-1 ECE:                     {uncal_ece:.4f}")
    print(f"Mean Top-1 Confidence:         {uncal_mean_conf:.4f}")

    # =========================================================
    # METHOD B: TEMPERATURE SCALING
    # =========================================================

    print("\nEvaluating temperature scaling...")

    oof_temp_probas = np.zeros_like(
        oof_raw_probas
    )

    learned_temperatures = []

    for fold, (train_idx, val_idx) in enumerate(
        fold_indices,
        start=1
    ):

        p_train = oof_raw_probas[train_idx]
        y_train_oh = y_true_onehot[train_idx]

        t_opt = optimize_temperature(
            p_train,
            y_train_oh
        )

        learned_temperatures.append(t_opt)

        oof_temp_probas[val_idx] = apply_temperature(
            oof_raw_probas[val_idx],
            t_opt
        )

    mean_temperature = float(
        np.mean(learned_temperatures)
    )

    temp_pred_indices = np.argmax(
        oof_temp_probas,
        axis=1
    )

    temp_preds = [
        classes[idx]
        for idx in temp_pred_indices
    ]

    temp_acc = float(
        accuracy_score(oof_y_true, temp_preds)
    )

    temp_f1 = float(
        f1_score(
            oof_y_true,
            temp_preds,
            average="macro",
            zero_division=0
        )
    )

    temp_logloss = float(
        log_loss(
            oof_y_true,
            oof_temp_probas,
            labels=classes
        )
    )

    temp_brier_sum, temp_brier_mean = (
        compute_multiclass_brier(
            y_true_onehot,
            oof_temp_probas
        )
    )

    temp_ece, temp_bin_details = (
        compute_top1_ece(
            y_true_indices,
            oof_temp_probas
        )
    )

    temp_mean_conf = float(
        np.mean(
            np.max(oof_temp_probas, axis=1)
        )
    )

    print("\n" + "=" * 50)
    print("METHOD B: TEMPERATURE SCALING")
    print("=" * 50)

    print(
        f"Mean Temperature: {mean_temperature:.4f} "
        f"(folds: {[round(t, 3) for t in learned_temperatures]})"
    )

    print(f"Accuracy:                      {temp_acc:.4f}")
    print(f"Macro F1:                      {temp_f1:.4f}")
    print(f"Multiclass Log Loss:           {temp_logloss:.5f}")
    print(f"Multiclass Brier (Sum):        {temp_brier_sum:.5f}")
    print(f"Multiclass Brier (Mean/class): {temp_brier_mean:.5f}")
    print(f"Top-1 ECE:                     {temp_ece:.4f}")
    print(f"Mean Top-1 Confidence:         {temp_mean_conf:.4f}")

    # =========================================================
    # METHOD C: ISOTONIC CALIBRATION
    # =========================================================

    print("\nEvaluating isotonic calibration...")

    oof_iso_probas = np.zeros_like(
        oof_raw_probas
    )

    for fold, (train_idx, val_idx) in enumerate(
        fold_indices,
        start=1
    ):

        p_train = oof_raw_probas[train_idx]
        y_train_oh = y_true_onehot[train_idx]

        p_val = oof_raw_probas[val_idx]

        cal_fold_out = np.zeros_like(
            p_val
        )

        for c in range(n_classes):

            iso = IsotonicRegression(
                out_of_bounds="clip",
                y_min=0.0,
                y_max=1.0
            )

            iso.fit(
                p_train[:, c],
                y_train_oh[:, c]
            )

            cal_fold_out[:, c] = iso.predict(
                p_val[:, c]
            )

        cal_fold_out = np.clip(
            cal_fold_out,
            1e-7,
            1.0
        )

        cal_fold_out /= np.sum(
            cal_fold_out,
            axis=1,
            keepdims=True
        )

        oof_iso_probas[val_idx] = cal_fold_out

    iso_pred_indices = np.argmax(
        oof_iso_probas,
        axis=1
    )

    iso_preds = [
        classes[idx]
        for idx in iso_pred_indices
    ]

    iso_acc = float(
        accuracy_score(oof_y_true, iso_preds)
    )

    iso_f1 = float(
        f1_score(
            oof_y_true,
            iso_preds,
            average="macro",
            zero_division=0
        )
    )

    iso_logloss = float(
        log_loss(
            oof_y_true,
            oof_iso_probas,
            labels=classes
        )
    )

    iso_brier_sum, iso_brier_mean = (
        compute_multiclass_brier(
            y_true_onehot,
            oof_iso_probas
        )
    )

    iso_ece, iso_bin_details = (
        compute_top1_ece(
            y_true_indices,
            oof_iso_probas
        )
    )

    iso_mean_conf = float(
        np.mean(
            np.max(oof_iso_probas, axis=1)
        )
    )

    print("\n" + "=" * 50)
    print("METHOD C: ISOTONIC CALIBRATION")
    print("=" * 50)

    print(f"Accuracy:                      {iso_acc:.4f}")
    print(f"Macro F1:                      {iso_f1:.4f}")
    print(f"Multiclass Log Loss:           {iso_logloss:.5f}")
    print(f"Multiclass Brier (Sum):        {iso_brier_sum:.5f}")
    print(f"Multiclass Brier (Mean/class): {iso_brier_mean:.5f}")
    print(f"Top-1 ECE:                     {iso_ece:.4f}")
    print(f"Mean Top-1 Confidence:         {iso_mean_conf:.4f}")

    # =========================================================
    # DYNAMIC RECOMMENDATION
    # =========================================================

    methods = {
        "uncalibrated_tabpfn": (
            uncal_logloss,
            uncal_brier_sum
        ),
        "temperature_scaling": (
            temp_logloss,
            temp_brier_sum
        ),
        "isotonic_calibration": (
            iso_logloss,
            iso_brier_sum
        ),
    }

    best_logloss = min(
        methods,
        key=lambda k: methods[k][0]
    )

    best_brier = min(
        methods,
        key=lambda k: methods[k][1]
    )

    recommend_retaining_original = (
        best_logloss == "uncalibrated_tabpfn"
        and best_brier == "uncalibrated_tabpfn"
    )

    if recommend_retaining_original:

        recommendation_summary = (
            "Retain the original uncalibrated TabPFN probabilities. "
            "They achieved the lowest log loss and Brier score "
            "in this evaluation."
        )

    elif best_logloss == best_brier:

        recommendation_summary = (
            f"{best_logloss} achieved the lowest log loss "
            "and Brier score in this evaluation."
        )

    else:

        recommendation_summary = (
            "Calibration results disagree. "
            f"{best_logloss} achieved the lowest log loss, while "
            f"{best_brier} achieved the lowest Brier score. "
            "No single method is clearly superior."
        )

    # =========================================================
    # RESULTS PAYLOAD
    # =========================================================

    results_payload = {

        "dataset": DATA_PATH.name,

        "evaluation_partition": "X_train (1,760 records)",

        "held_out_test_records_isolated": len(X_test),

        "held_out_test_used": False,

        "cv_folds": N_FOLDS,

        "classes_count": n_classes,

        "class_names": classes,

        "total_cv_seconds": round(cv_elapsed, 3),

        "comparison_table": {

            "metrics": [
                "Accuracy",
                "Macro F1",
                "Multiclass Log Loss",
                "Multiclass Brier Score (Sum)",
                "Multiclass Brier Score (Mean/class)",
                "Top-1 ECE",
                "Mean Top-1 Confidence",
            ],

            "uncalibrated_tabpfn": {

                "accuracy": round(uncal_acc, 6),

                "macro_f1": round(uncal_f1, 6),

                "multiclass_log_loss": round(
                    uncal_logloss, 6
                ),

                "multiclass_brier_sum": round(
                    uncal_brier_sum, 6
                ),

                "multiclass_brier_mean_per_class": round(
                    uncal_brier_mean, 6
                ),

                "top1_ece": round(uncal_ece, 6),

                "mean_top1_confidence": round(
                    uncal_mean_conf, 6
                ),
            },

            "temperature_scaling": {

                "mean_learned_temperature": round(
                    mean_temperature, 4
                ),

                "fold_temperatures": [
                    round(t, 4)
                    for t in learned_temperatures
                ],

                "accuracy": round(temp_acc, 6),

                "macro_f1": round(temp_f1, 6),

                "multiclass_log_loss": round(
                    temp_logloss, 6
                ),

                "multiclass_brier_sum": round(
                    temp_brier_sum, 6
                ),

                "multiclass_brier_mean_per_class": round(
                    temp_brier_mean, 6
                ),

                "top1_ece": round(temp_ece, 6),

                "mean_top1_confidence": round(
                    temp_mean_conf, 6
                ),
            },

            "isotonic_calibration": {

                "accuracy": round(iso_acc, 6),

                "macro_f1": round(iso_f1, 6),

                "multiclass_log_loss": round(
                    iso_logloss, 6
                ),

                "multiclass_brier_sum": round(
                    iso_brier_sum, 6
                ),

                "multiclass_brier_mean_per_class": round(
                    iso_brier_mean, 6
                ),

                "top1_ece": round(iso_ece, 6),

                "mean_top1_confidence": round(
                    iso_mean_conf, 6
                ),
            },
        },

        "recommendation": recommendation_summary,

        "recommend_retaining_original_model": (
            recommend_retaining_original
        ),

        "best_log_loss_method": best_logloss,

        "best_brier_score_method": best_brier,

        "metric_definitions_and_limitations": {

            "accuracy_and_macro_f1": (
                "Measures categorical prediction performance. "
                "These metrics do not directly measure probability calibration."
            ),

            "multiclass_log_loss": (
                "A strictly proper scoring rule that penalizes "
                "confident incorrect predictions."
            ),

            "multiclass_brier_score": (
                "Measures squared probability errors across all classes."
            ),

            "top1_expected_calibration_error": (
                "Weighted average difference between top-1 confidence "
                "and accuracy across 10 bins. ECE is sensitive to bin boundaries."
            ),

            "calibration_methodology_limitation": (
                "This evaluation uses five-fold OOF predictions and fits "
                "calibrators using predictions from the other folds. "
                "The base models generating those predictions may have "
                "seen the evaluated fold's records during their training. "
                "Therefore, this is an exploratory comparison, not a "
                "fully independent nested calibration evaluation."
            ),

            "held_out_test": (
                "The original held-out 20% test partition was not used "
                "for calibration fitting or evaluation."
            ),
        },

        "ece_bin_breakdowns": {

            "uncalibrated": uncal_bin_details,

            "temperature_scaling": temp_bin_details,

            "isotonic": iso_bin_details,
        },
    }

    # =========================================================
    # SAVE RESULTS
    # =========================================================

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            results_payload,
            f,
            indent=2
        )

    print("\n" + "=" * 70)
    print("CALIBRATION EVALUATION COMPLETED")

    print(
        f"Results saved to: {OUTPUT_PATH}"
    )

    print(
        f"\nRecommendation: {recommendation_summary}"
    )

    print(
        f"Best Log Loss: {best_logloss}"
    )

    print(
        f"Best Brier Score: {best_brier}"
    )

    print("=" * 70)

    return results_payload


# =============================================================
# ENTRY POINT
# =============================================================

if __name__ == "__main__":
    run_calibration_evaluation()
