import { useState } from "react";
import "./Prediction.css";
import API_URL from "../api";

const fields = [
  { key: "N", label: "Nitrogen", unit: "kg/ha", value: 90, range: "0 – 140" },
  { key: "P", label: "Phosphorus", unit: "kg/ha", value: 42, range: "5 – 145" },
  { key: "K", label: "Potassium", unit: "kg/ha", value: 43, range: "5 – 205" },
  { key: "temperature", label: "Temperature", unit: "°C", value: 20.88, range: "8.8 – 43.7" },
  { key: "humidity", label: "Humidity", unit: "%", value: 82, range: "14.3 – 100" },
  { key: "ph", label: "Soil pH", unit: "pH", value: 6.5, range: "3.5 – 9.9" },
  { key: "rainfall", label: "Rainfall", unit: "mm", value: 202.94, range: "20.2 – 298.6" },
];

const initialValues = Object.fromEntries(
  fields.map((field) => [field.key, String(field.value)])
);

export default function Prediction() {
  const [values, setValues] = useState({ ...initialValues });
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const [explanation, setExplanation] = useState(null);
  const [explainLoading, setExplainLoading] = useState(false);
  const [explainError, setExplainError] = useState("");

  function resetExample() {
    setValues({ ...initialValues });
    setResult(null);
    setExplanation(null);
    setError("");
    setExplainError("");
  }

  function getInput() {
    const input = {};

    for (const field of fields) {
      const raw = (values[field.key] || "").trim();
      const number = Number(raw);

      if (raw === "" || !Number.isFinite(number)) {
        throw new Error(`Please enter a valid number for ${field.label}.`);
      }

      input[field.key] = number;
    }

    return input;
  }

  async function predictCrop(event) {
    event.preventDefault();

    setError("");
    setResult(null);
    setExplanation(null);
    setExplainError("");

    let input;

    try {
      input = getInput();
    } catch (err) {
      setError(err.message);
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(input),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Prediction request failed.");
      }

      setResult(data);
    } catch (err) {
      setError(
        `${err.message}. Please check that the AgriSmart backend is running.`
      );
    } finally {
      setLoading(false);
    }
  }

  async function explainCrop() {
    setExplainError("");
    setExplanation(null);

    let input;

    try {
      input = getInput();
    } catch (err) {
      setExplainError(err.message);
      return;
    }

    setExplainLoading(true);

    try {
      const response = await fetch(`${API_URL}/explain`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(input),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Explanation calculation failed.");
      }

      setExplanation(data);
    } catch (err) {
      setExplainError(
        err.message || "Failed to generate feature explanation."
      );
    } finally {
      setExplainLoading(false);
    }
  }

  const reliability =
    result?.reliability_level ||
    (result?.recommendation_withheld
      ? "level_3_severe_or_invalid"
      : result?.input_warnings?.length > 0
        ? "level_2_unusual"
        : "level_1_reference");

  return (
    <main className="prediction-page">
      <header className="prediction-heading">
        <div>
          <span className="prediction-eyebrow">SMART FARMING • AI INSIGHTS</span>
          <h1>
            Crop Recommendation <span>🌱</span>
          </h1>
          <p>
            Discover suitable crops using soil nutrients and environmental
            measurements.
          </p>
        </div>
      </header>

      <div className="prediction-workspace">

        {/* LEFT COLUMN: INFORMATION AND RESULTS */}
        <section className="prediction-result-card" aria-live="polite">

          <div className="recommendation-information">
            <div className="prediction-info-panel">
              <h3>ⓘ Information</h3>
              <p>
                Crop recommendation is an important aspect of precision
                agriculture. AgriSmart uses soil nutrients and environmental
                factors to identify suitable crop candidates for your field.
              </p>
            </div>

            <div className="recommendation-how">
              <h2>How does it work? <span>❓</span></h2>
              <p>
                Enter all seven parameters. The TabPFN machine learning model
                evaluates your measurements and predicts suitable crops based
                on patterns learned from its training dataset.
              </p>
            </div>

            <div className="recommendation-results-heading">
              <div>
                <span className="prediction-section-label">YOUR ANALYSIS</span>
                <h2>Recommendation Results</h2>
              </div>
            </div>
          </div>

          {!result && !loading && (
            <div className="prediction-empty-state">
              <div className="empty-state-icon">🌱</div>
              <h2>No Analysis Available</h2>
              <p>
                Enter your soil and climate measurements to get started
                with crop recommendation.
              </p>
            </div>
          )}

          {loading && (
            <div className="prediction-loading-state">
              <div className="prediction-spinner" />
              <h2>Evaluating your soil profile</h2>
              <p>TabPFN is evaluating the seven input parameters...</p>
            </div>
          )}

          {result && (
            <div className="prediction-output-wrapper">

              {/* RELIABILITY */}
              <div className={`reliability-banner ${reliability}`}>
                <div className="reliability-banner-header">
                  <span className="reliability-indicator" />
                  <strong>
                    {reliability === "level_1_reference" &&
                      "Level 1: Within Reference Distribution"}
                    {reliability === "level_2_unusual" &&
                      "Level 2: Unusual Input Profile"}
                    {reliability === "level_3_severe_or_invalid" &&
                      "Level 3: Recommendation Withheld"}
                  </strong>
                </div>

                <p className="reliability-banner-desc">
                  {reliability === "level_1_reference" &&
                    "Measurements are within the reference dataset's observed bounds and typical distribution."}
                  {reliability === "level_2_unusual" &&
                    "The input profile contains unusual measurements or combinations. Interpret the recommendation cautiously."}
                  {reliability === "level_3_severe_or_invalid" &&
                    "The input profile contains severe anomalies or invalid measurements. The recommendation is withheld."}
                </p>

                {result.distribution_check && (
                  <div className="reliability-metrics-pill">
                    <span>
                      5-NN Distance:{" "}
                      <strong>
                        {result.distribution_check.nearest_neighbor_distance ?? "N/A"}
                      </strong>
                    </span>

                    <span>
                      Reference Threshold:{" "}
                      <strong>
                        {result.distribution_check.reference_distance_threshold}
                      </strong>
                    </span>

                    <span>
                      Severe Threshold:{" "}
                      <strong>
                        {result.distribution_check.severe_distance_threshold ?? 3.0}
                      </strong>
                    </span>
                  </div>
                )}
              </div>

              {/* WITHHELD RECOMMENDATION */}
              {result.recommendation_withheld ? (
                <div className="withheld-card">
                  <div className="withheld-icon">🛡️</div>
                  <h2>Recommendation Withheld</h2>

                  <p className="withheld-lead">
                    No crop recommendation is issued because the input
                    profile contains severe anomalies or unviable parameters.
                  </p>

                  <div className="withheld-reasons-box">
                    <strong>Diagnostic Findings</strong>
                    <ul>
                      {result.input_warnings?.map((warning, index) => (
                        <li key={index}>{warning}</li>
                      ))}
                    </ul>
                  </div>

                  <div className="withheld-guidance">
                    <strong>How to Resolve</strong>
                    <ol>
                      <li>Check the measurement values and their units.</li>
                      <li>Verify the soil and climate measurements.</li>
                      <li>Consult a local soil testing laboratory.</li>
                    </ol>
                  </div>
                </div>
              ) : (
                <>
                  {/* PRIMARY CROP */}
                  <div className="prediction-hero-crop">
                    <span className="prediction-step">
                      PRIMARY SUITABILITY RECOMMENDATION
                    </span>

                    <div className="prediction-crop-header">
                      <div className="prediction-crop-symbol">🌱</div>
                      <div>
                        <h2>{result.predicted_crop}</h2>
                        <p>Leading candidate for this soil profile</p>
                      </div>
                    </div>
                  </div>

                  {/* TOP THREE CROPS */}
                  <div className="prediction-candidates-section">
                    <h3 className="section-title">
                      Top-Three Crop Candidates
                    </h3>

                    <div className="candidates-list">
                      {result.top_3?.map((item) => (
                        <div className="candidate-item" key={item.crop}>
                          <div className="candidate-header">
                            <span className="candidate-name">
                              {item.crop}
                            </span>

                            <span className="candidate-percentage">
                              {Number(item.percentage).toFixed(2)}%
                            </span>
                          </div>

                          <div className="candidate-track">
                            <div
                              className="candidate-fill"
                              style={{
                                width: `${Math.min(
                                  Math.max(Number(item.percentage) || 0, 0),
                                  100
                                )}%`,
                              }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>

                    <p className="probability-caveat">
                      <strong>Note:</strong> Percentages represent
                      classification probabilities from the trained
                      benchmark model. They do not predict harvest yield
                      or financial profitability.
                    </p>
                  </div>

                  {/* INPUT WARNINGS */}
                  {result.input_warnings?.length > 0 && (
                    <div className="warnings-container">
                      <strong>Input Distribution Warnings</strong>
                      <ul>
                        {result.input_warnings.map((warning, index) => (
                          <li key={index}>{warning}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* SHAP BUTTON */}
                  <div className="explain-action-bar">
                    <button
                      className="prediction-explain-btn"
                      type="button"
                      onClick={explainCrop}
                      disabled={explainLoading}
                    >
                      {explainLoading
                        ? "Generating SHAP Attributions..."
                        : "Explain This Prediction with SHAP →"}
                    </button>

                    <span className="explain-hint">
                      View the feature contributions for {result.predicted_crop}
                    </span>
                  </div>

                  {explainError && (
                    <div className="prediction-error-box" role="alert">
                      {explainError}
                    </div>
                  )}
                </>
              )}

              {/* SHAP EXPLANATION */}
              {explanation && (
                <section className="shap-explanation-card">
                  <div className="shap-header">
                    <span className="prediction-step">EXPLAINABLE AI</span>
                    <h2>Why {explanation.predicted_crop}?</h2>
                    <p className="shap-disclaimer-note">
                      {explanation.note}
                    </p>
                  </div>

                  <div className="shap-bars-container">
                    {explanation.explanation?.map((item) => {
                      const positive = item.shap_value >= 0;
                      const width = Math.min(
                        Math.abs(item.shap_value) * 300,
                        100
                      );

                      return (
                        <div className="shap-row" key={item.feature}>
                          <div className="shap-feature-meta">
                            <strong>{item.feature}</strong>
                            <small>Input: {item.value}</small>
                          </div>

                          <div className="shap-visual-column">
                            <div className="shap-axis-track">
                              <div className="shap-center-line" />

                              <div
                                className={`shap-bar ${
                                  positive ? "positive" : "negative"
                                }`}
                                style={{
                                  width: `${Math.max(width, 4)}%`,
                                  left: positive
                                    ? "50%"
                                    : `calc(50% - ${Math.max(width, 4)}%)`,
                                }}
                              />
                            </div>
                          </div>

                          <div className="shap-score-value">
                            <span className={positive ? "val-pos" : "val-neg"}>
                              {positive ? "+" : ""}
                              {Number(item.shap_value).toFixed(4)}
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  <div className="shap-legend">
                    <span>
                      <i className="legend-dot pos" /> Positive contribution
                    </span>
                    <span>
                      <i className="legend-dot neg" /> Negative contribution
                    </span>
                  </div>
                </section>
              )}
            </div>
          )}
        </section>

        {/* RIGHT COLUMN: SEVEN MODEL INPUTS */}
        <form className="prediction-form-card" onSubmit={predictCrop}>
          <div className="prediction-card-heading">
            <div>
              <span className="prediction-section-label">FIELD PARAMETERS</span>
              <h2>Enter Your Soil Details</h2>
              <p>Provide the soil and climate measurements below.</p>
            </div>

            <button
              className="prediction-reset-btn"
              type="button"
              onClick={resetExample}
            >
              <span>↻</span> Reset
            </button>
          </div>

          <div className="prediction-fields-grid">
            {fields.map((field) => (
              <label className="prediction-field-group" key={field.key}>
                <span className="field-label-text">{field.label}</span>

                <div className="prediction-input-wrap">
                  <input
                    type="number"
                    step="any"
                    value={values[field.key]}
                    onChange={(event) =>
                      setValues((previous) => ({
                        ...previous,
                        [field.key]: event.target.value,
                      }))
                    }
                    required
                  />

                  <small className="field-unit">{field.unit}</small>
                </div>

                <span className="field-reference-range">
                  Observed range: {field.range} {field.unit}
                </span>
              </label>
            ))}
          </div>

          <button
            className="prediction-primary-btn"
            type="submit"
            disabled={loading}
          >
            {loading ? "Evaluating with TabPFN..." : "Predict Crop →"}
          </button>

          <p className="prediction-help-text">
            This application is an educational decision-support prototype.
            Verify recommendations with local agricultural experts.
          </p>

          {error && (
            <div className="prediction-error-box" role="alert">
              {error}
            </div>
          )}
        </form>
      </div>
    </main>
  );
}