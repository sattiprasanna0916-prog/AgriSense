import { useState } from "react";
import "./Prediction.css";

const API_URL = "http://127.0.0.1:8000";

const fields = [
  { key: "N", label: "Nitrogen (N)", unit: "kg/ha", value: 90, range: "0 – 140" },
  { key: "P", label: "Phosphorus (P)", unit: "kg/ha", value: 42, range: "5 – 145" },
  { key: "K", label: "Potassium (K)", unit: "kg/ha", value: 43, range: "5 – 205" },
  { key: "temperature", label: "Temperature", unit: "°C", value: 20.88, range: "8.8 – 43.7" },
  { key: "humidity", label: "Relative humidity", unit: "%", value: 82.0, range: "14.3 – 100.0" },
  { key: "ph", label: "Soil pH", unit: "pH", value: 6.5, range: "3.5 – 9.9" },
  { key: "rainfall", label: "Rainfall", unit: "mm", value: 202.94, range: "20.2 – 298.6" },
];

const seasons = [
  "Kharif",
  "Rabi",
  "Whole Year",
  "Summer",
  "Winter",
  "Autumn",
];

export default function Prediction() {
  const [values, setValues] = useState(
    Object.fromEntries(fields.map((field) => [field.key, String(field.value)]))
  );
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const [explanation, setExplanation] = useState(null);
  const [explainLoading, setExplainLoading] = useState(false);
  const [explainError, setExplainError] = useState("");

  const [stateName, setStateName] = useState("Andhra Pradesh");
  const [district, setDistrict] = useState("ANANTAPUR");
  const [season, setSeason] = useState("Kharif");

  const [historicalData, setHistoricalData] = useState(null);
  const [historicalLoading, setHistoricalLoading] = useState(false);
  const [historicalError, setHistoricalError] = useState("");

  function resetExample() {
    setValues(
      Object.fromEntries(fields.map((field) => [field.key, String(field.value)]))
    );
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
        throw new Error(`Please enter a valid finite number for ${field.label}.`);
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
        body: JSON.stringify({
          ...input,
          state: stateName.trim(),
          district: district.trim(),
          season,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Prediction request failed.");
      }

      setResult(data);
    } catch (err) {
      setError(`${err.message}. Please check that the AgriSense backend is running.`);
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
      setExplainError(err.message || "Failed to generate feature explanation.");
    } finally {
      setExplainLoading(false);
    }
  }

  async function loadHistoricalInsights() {
    setHistoricalLoading(true);
    setHistoricalError("");
    setHistoricalData(null);

    try {
      const params = new URLSearchParams({
        state: stateName.trim(),
        district: district.trim(),
        season,
        limit: "5",
      });

      const response = await fetch(
        `${API_URL}/historical/ranking?${params.toString()}`
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Could not load historical crop records."
        );
      }

      setHistoricalData(data);
    } catch (err) {
      setHistoricalError(
        err.message || "Could not retrieve historical crop records."
      );
    } finally {
      setHistoricalLoading(false);
    }
  }

  // Determine reliability badge style and labels
  const reliability = result?.reliability_level || (
    result?.recommendation_withheld
      ? "level_3_severe_or_invalid"
      : result?.input_warnings?.length > 0
        ? "level_2_unusual"
        : "level_1_reference"
  );

  return (
    <main className="prediction-page">
      <header className="prediction-heading">
        <span className="prediction-eyebrow">
          EXPLAINABLE AI · TABPFN FOUNDATION CLASSIFIER
        </span>
        <h1>Find suitable crops for <span>your soil & climate.</span></h1>
        <p>
          Submit nitrogen, phosphorus, potassium, temperature, humidity, pH, and
          rainfall to receive crop candidates evaluated by TabPFN with local SHAP feature attributions.
        </p>
      </header>

      <div className="prediction-workspace">
        {/* Left Card: Input Form */}
        <form className="prediction-form-card" onSubmit={predictCrop}>
          <div className="prediction-card-heading">
            <div>
              <h2>Soil & climate inputs</h2>
            </div>
            <button
              className="prediction-reset-btn"
              type="button"
              onClick={resetExample}
              title="Reset fields to sample data"
            >
              Reset Example
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
                    onChange={(e) =>
                      setValues((prev) => ({
                        ...prev,
                        [field.key]: e.target.value,
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

          {/* Regional Context Accordion/Section */}
          <div className="prediction-context-box">
            <div className="context-box-header">
              <h3>Regional historical context</h3>
              <span className="context-box-tag">Optional Context</span>
            </div>
            <p className="context-box-desc">
              State, district, and season retrieve recorded production history.
              These are not features of the 7-input TabPFN model.
            </p>

            <div className="context-inputs-row">
              <label>
                State
                <input
                  value={stateName}
                  onChange={(e) => setStateName(e.target.value)}
                  placeholder="e.g. Andhra Pradesh"
                />
              </label>

              <label>
                District
                <input
                  value={district}
                  onChange={(e) => setDistrict(e.target.value)}
                  placeholder="e.g. ANANTAPUR"
                />
              </label>

              <label>
                Season
                <select
                  value={season}
                  onChange={(e) => setSeason(e.target.value)}
                >
                  {seasons.map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <button
              type="button"
              className="context-load-btn"
              onClick={loadHistoricalInsights}
              disabled={historicalLoading}
            >
              {historicalLoading
                ? "Loading historical records..."
                : "Query Regional Production History"}
            </button>
          </div>

          <button
            className="prediction-primary-btn"
            type="submit"
            disabled={loading}
          >
            {loading ? (
              <span className="prediction-btn-spinner">
                <span className="mini-spinner" /> Evaluating with TabPFN...
              </span>
            ) : (
              "Evaluate Crop Suitability →"
            )}
          </button>

          <p className="prediction-help-text">
            Predictions evaluate soil suitability based on the 2,200-record benchmark.
            Outputs are educational decision-support estimates.
          </p>

          {error && (
            <div className="prediction-error-box" role="alert">
              <strong>Error:</strong> {error}
            </div>
          )}
        </form>

        {/* Right Card: Recommendation Output & Safeguards */}
        <section className="prediction-result-card" aria-live="polite">
          {!result && !loading && (
            <div className="prediction-empty-state">
              <div className="empty-state-icon">🌱</div>
              
              <h2>Your evaluation will appear here</h2>
              <p>
                Enter soil nutrients and climate parameters to analyze crop suitability,
                review 3-level reliability checks, and inspect feature explanations.
              </p>
            </div>
          )}

          {loading && (
            <div className="prediction-loading-state">
              <div className="prediction-spinner" />
              <h2>Evaluating Field Profile</h2>
              <p>TabPFN is computing posterior class probabilities...</p>
            </div>
          )}

          {result && (
            <div className="prediction-output-wrapper">
              {/* Reliability Policy Status Banner */}
              <div className={`reliability-banner ${reliability}`}>
                <div className="reliability-banner-header">
                  <span className="reliability-indicator" />
                  <strong>
                    {reliability === "level_1_reference" && "Level 1: Within Reference Distribution"}
                    {reliability === "level_2_unusual" && "Level 2: Unusual Input Profile"}
                    {reliability === "level_3_severe_or_invalid" && "Level 3: Recommendation Withheld"}
                  </strong>
                </div>

                <p className="reliability-banner-desc">
                  {reliability === "level_1_reference" &&
                    "All measurements lie within the reference dataset's observed bounds and typical multivariate distribution."}
                  {reliability === "level_2_unusual" &&
                    "Input measurements exceed observed dataset ranges or form an unusual multivariate combination. The model is extrapolating beyond familiar training clusters."}
                  {reliability === "level_3_severe_or_invalid" &&
                    "Input measurements violate physical feasibility, exceed agricultural guardrails, or represent a severely unfamiliar combination. Recommendation is withheld to prevent misleading guidance."}
                </p>

                {result.distribution_check && (
                  <div className="reliability-metrics-pill">
                    <span>
                      5-NN Distance:{" "}
                      <strong>
                        {result.distribution_check.nearest_neighbor_distance != null
                          ? result.distribution_check.nearest_neighbor_distance
                          : "N/A"}
                      </strong>
                    </span>
                    <span>
                      Unusual Threshold:{" "}
                      <strong>{result.distribution_check.reference_distance_threshold}</strong>
                    </span>
                    <span>
                      Severe Threshold:{" "}
                      <strong>{result.distribution_check.severe_distance_threshold || 3.0}</strong>
                    </span>
                  </div>
                )}
              </div>

              {/* LEVEL 3 WITHHELD STATE */}
              {result.recommendation_withheld ? (
                <div className="withheld-card">
                  <div className="withheld-icon">🛡️</div>
                  <h2>Recommendation Withheld</h2>
                  <p className="withheld-lead">
                    No crop recommendation is issued because the input profile contains severe anomalies or unviable agricultural parameters.
                  </p>

                  <div className="withheld-reasons-box">
                    <strong>Diagnostic Findings:</strong>
                    <ul>
                      {result.input_warnings?.map((warning, idx) => (
                        <li key={idx}>{warning}</li>
                      ))}
                    </ul>
                  </div>

                  <div className="withheld-guidance">
                    <strong>How to Resolve:</strong>
                    <ol>
                      <li>Check that numerical values match standard units (kg/ha, °C, %, mm, pH).</li>
                      <li>Verify soil pH is between 3.5 and 9.5 and temperature reflects realistic regional climate.</li>
                      <li>Consult a local district agricultural officer or soil testing laboratory.</li>
                    </ol>
                  </div>
                </div>
              ) : (
                /* LEVEL 1 OR LEVEL 2 PREDICTION DISPLAY */
                <>
                  <div className="prediction-hero-crop">
                    <span className="prediction-step">PRIMARY SUITABILITY RECOMMENDATION</span>
                    <div className="prediction-crop-header">
                      <div className="prediction-crop-symbol">🌱</div>
                      <div>
                        <h2>{result.predicted_crop}</h2>
                        <p>Leading candidate for this soil and climate profile</p>
                      </div>
                    </div>
                  </div>

                  <div className="prediction-candidates-section">
                    <h3 className="section-title">Top-Three Crop Candidates</h3>

                    <div className="candidates-list">
                      {result.top_3?.map((item) => (
                        <div key={item.crop} className="candidate-item">
                          <div className="candidate-header">
                            <span className="candidate-name">{item.crop}</span>
                            <span className="candidate-percentage">
                              {item.percentage.toFixed(2)}%
                            </span>
                          </div>
                          <div className="candidate-track">
                            <div
                              className="candidate-fill"
                              style={{ width: `${Math.min(item.percentage, 100)}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>

                    <p className="probability-caveat">
                      <strong>Understanding Model Percentages:</strong> Percentages reflect relative
                      classification certainty within the trained benchmark dataset. They do not predict
                      harvest yield, weather resilience, or financial profitability.
                    </p>
                  </div>

                  {/* Input Warnings (for Level 2) */}
                  {result.input_warnings?.length > 0 && (
                    <div className="warnings-container">
                      <strong>Input Distribution Warnings:</strong>
                      <ul>
                        {result.input_warnings.map((warn, index) => (
                          <li key={index}>{warn}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* SHAP Explanation Action */}
                  <div className="explain-action-bar">
                    <button
                      className="prediction-explain-btn"
                      type="button"
                      onClick={explainCrop}
                      disabled={explainLoading}
                    >
                      {explainLoading ? (
                        <span className="prediction-btn-spinner">
                          <span className="mini-spinner" /> Generating SHAP Attributions...
                        </span>
                      ) : (
                        "Explain This Prediction with SHAP →"
                      )}
                    </button>
                    <span className="explain-hint">
                      Computes local feature contributions for {result.predicted_crop}
                    </span>
                  </div>

                  {explainError && (
                    <div className="prediction-error-box" role="alert">
                      {explainError}
                    </div>
                  )}
                </>
              )}

              {/* SHAP EXPLANATION CARD */}
              {explanation && (
                <section className="shap-explanation-card">
                  <div className="shap-header">
                    <span className="prediction-step">FEATURE EXPLANABILITY</span>
                    <h2>Why {explanation.predicted_crop}?</h2>
                    <p className="shap-disclaimer-note">{explanation.note}</p>
                  </div>

                  <div className="shap-bars-container">
                    {explanation.explanation?.map((item) => {
                      const isPositive = item.shap_value >= 0;
                      const absVal = Math.abs(item.shap_value);
                      const barWidth = Math.min(absVal * 300, 100);

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
                                className={`shap-bar ${isPositive ? "positive" : "negative"}`}
                                style={{
                                  width: `${Math.max(barWidth, 4)}%`,
                                  left: isPositive ? "50%" : `calc(50% - ${Math.max(barWidth, 4)}%)`,
                                }}
                              />
                            </div>
                          </div>

                          <div className="shap-score-value">
                            <span className={isPositive ? "val-pos" : "val-neg"}>
                              {isPositive ? "+" : ""}
                              {item.shap_value.toFixed(4)}
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  <div className="shap-legend">
                    <span>
                      <span className="legend-dot pos" /> Positive SHAP value (increases confidence)
                    </span>
                    <span>
                      <span className="legend-dot neg" /> Negative SHAP value (decreases confidence)
                    </span>
                  </div>
                </section>
              )}
            </div>
          )}
        </section>
      </div>

      {/* DISTINCT REGIONAL HISTORICAL SECTION */}
      <section className="regional-historical-section">
        <div className="regional-section-header">
          <span className="prediction-eyebrow">REGIONAL HISTORICAL EVIDENCE (1997–2014)</span>
          <h2>District Production Records vs Soil Suitability</h2>
          <p>
            Historical records describe what was grown and reported in this district.
            They provide regional context but do not evaluate your field's soil chemistry or future yield.
          </p>
        </div>

        {historicalLoading && (
          <div className="historical-loading-box">
            <span className="mini-spinner" /> Loading district crop production records...
          </div>
        )}

        {historicalError && (
          <div className="prediction-error-box">
            {historicalError}
          </div>
        )}

        {historicalData && (
          <div className="historical-results-card">
            <div className="historical-meta-bar">
              <div>
                <strong>Location:</strong> {historicalData.district || district},{" "}
                {historicalData.state || stateName}
              </div>
              <div>
                <strong>Season:</strong> {historicalData.season || season}
              </div>
              <div>
                <strong>Years Recorded:</strong>{" "}
                {historicalData.years_covered?.length || 0} seasons
              </div>
            </div>

            {historicalData.crops?.length > 0 ? (
              <div className="historical-crops-grid">
                {historicalData.crops.map((crop, index) => (
                  <div
                    className="historical-crop-card"
                    key={`${crop.Crop || crop.crop}-${index}`}
                  >
                    <div className="crop-card-top">
                      <span className="crop-rank">#{index + 1}</span>
                      <h4>{crop.Crop || crop.crop}</h4>
                    </div>

                    <div className="crop-stats-grid">
                      <div>
                        <span>Total Production</span>
                        <strong>
                          {crop.total_production != null
                            ? Number(crop.total_production).toLocaleString("en-IN")
                            : "N/A"}
                        </strong>
                      </div>
                      <div>
                        <span>Total Area</span>
                        <strong>
                          {crop.total_area != null
                            ? Number(crop.total_area).toLocaleString("en-IN")
                            : "N/A"}
                        </strong>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="no-historical-text">
                No matching historical crop records found for this district and season.
              </p>
            )}

            <div className="historical-methodology-note">
              <strong>Methodological Notice:</strong> Historical production statistics reflect past
              farmer decisions, market demand, and irrigation infrastructure. A crop having high
              historical volume does not guarantee it will thrive in your soil; conversely, a suitable
              crop may have zero recorded production if local seeds or markets were unavailable.
            </div>
          </div>
        )}
      </section>
    </main>
  );
}
