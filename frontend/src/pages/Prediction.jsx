import { useState } from "react";
import { useLanguage } from "../context/LanguageContext";
import API_URL from "../api";
import "./Prediction.css";

const CROP_TRANSLATIONS = {
  rice: "వరి (Rice)",
  maize: "మొక్కజొన్న (Maize)",
  chickpea: "శనగ (Chickpea)",
  kidneybeans: "రాజ్మా (Kidneybeans)",
  pigeonpeas: "కందులు (Pigeonpeas)",
  mothbeans: "బొబ్బర్లు (Mothbeans)",
  mungbean: "పెసలు (Mungbean)",
  blackgram: "మినుములు (Blackgram)",
  lentil: "మసూర్ పప్పు (Lentil)",
  pomegranate: "దానిమ్మ (Pomegranate)",
  banana: "అరటి (Banana)",
  mango: "మామిడి (Mango)",
  grapes: "ద్రాక్ష (Grapes)",
  watermelon: "పుచ్చకాయ (Watermelon)",
  muskmelon: "ఖర్బూజా (Muskmelon)",
  apple: "యాపిల్ (Apple)",
  orange: "నారింజ (Orange)",
  papaya: "బొప్పాయి (Papaya)",
  coconut: "కొబ్బరి (Coconut)",
  cotton: "పత్తి (Cotton)",
  jute: "జనపనార (Jute)",
  coffee: "కాఫీ (Coffee)",
};

function formatCrop(crop, lang) {
  if (!crop) return "";
  const key = crop.toLowerCase().trim();
  if (lang === "te" && CROP_TRANSLATIONS[key]) {
    return CROP_TRANSLATIONS[key];
  }
  return crop.charAt(0).toUpperCase() + crop.slice(1);
}

const defaultFields = [
  { key: "N", labelKey: "fieldN", unit: "kg/ha", value: 90, range: "0 – 140" },
  { key: "P", labelKey: "fieldP", unit: "kg/ha", value: 42, range: "5 – 145" },
  { key: "K", labelKey: "fieldK", unit: "kg/ha", value: 43, range: "5 – 205" },
  { key: "temperature", labelKey: "fieldTemp", unit: "°C", value: 20.88, range: "8.8 – 43.7" },
  { key: "humidity", labelKey: "fieldHumidity", unit: "%", value: 82, range: "14.3 – 100" },
  { key: "ph", labelKey: "fieldPh", unit: "pH", value: 6.5, range: "3.5 – 9.9" },
  { key: "rainfall", labelKey: "fieldRainfall", unit: "mm", value: 202.94, range: "20.2 – 298.6" },
];

const initialValues = Object.fromEntries(
  defaultFields.map((field) => [field.key, String(field.value)])
);

export default function Prediction() {
  const [values, setValues] = useState({ ...initialValues });
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const [explanation, setExplanation] = useState(null);
  const [explainLoading, setExplainLoading] = useState(false);
  const [explainError, setExplainError] = useState("");

  const { t, lang } = useLanguage();

  function resetExample() {
    setValues({ ...initialValues });
    setResult(null);
    setExplanation(null);
    setError("");
    setExplainError("");
  }

  function getInput() {
    const input = {};

    for (const field of defaultFields) {
      const raw = (values[field.key] || "").trim();
      const number = Number(raw);

      if (raw === "" || !Number.isFinite(number)) {
        throw new Error(
          lang === "te"
            ? `దయచేసి ${t(field.labelKey)} కోసం సరైన సంఖ్యను నమోదు చేయండి.`
            : `Please enter a valid number for ${t(field.labelKey)}.`
        );
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
        throw new Error(data.detail || (lang === "te" ? "సిఫార్సు అభ్యర్థన విఫలమైంది." : "Prediction request failed."));
      }

      setResult(data);
    } catch (err) {
      setError(
        lang === "te"
          ? `${err.message}. అగ్రిస్మార్ట్ బ్యాకెండ్ సర్వర్ రన్ అవుతోందో లేదో సరిచూసుకోండి.`
          : `${err.message}. Please check that the AgriSmart backend is running.`
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
        throw new Error(data.detail || (lang === "te" ? "కారణాల విశ్లేషణ విఫలమైంది." : "Explanation calculation failed."));
      }

      setExplanation(data);
    } catch (err) {
      setExplainError(
        err.message || (lang === "te" ? "వివరణను రూపొందించడం సాధ్యం కాలేదు." : "Failed to generate feature explanation.")
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
          <span className="prediction-eyebrow">
            {lang === "te" ? "స్మార్ట్ వ్యవసాయం • AI అంచనాలు" : "SMART FARMING • AI INSIGHTS"}
          </span>
          <h1>
            {t("predTitle")} <span>🌱</span>
          </h1>
          <p>
            {t("predSubtitle")}
          </p>
        </div>
      </header>

      <div className="prediction-workspace">
        {/* LEFT COLUMN: INFORMATION AND RESULTS */}
        <section className="prediction-result-card" aria-live="polite">
          <div className="recommendation-information">
            <div className="prediction-info-panel">
              <h3>ⓘ {lang === "te" ? "సమాచారం" : "Information"}</h3>
              <p>
                {lang === "te"
                  ? "పంట సిఫార్సు ఖచ్చితమైన వ్యవసాయంలో కీలకమైన భాగం. అగ్రిస్మార్ట్ మీ పొలానికి అనువైన పంటలను గుర్తించడానికి నేల పోషకాలు మరియు వాతావరణ కారకాలను ఉపయోగిస్తుంది."
                  : "Crop recommendation is an important aspect of precision agriculture. AgriSmart uses soil nutrients and environmental factors to identify suitable crop candidates for your field."}
              </p>
            </div>

            <div className="recommendation-how">
              <h2>{lang === "te" ? "ఇది ఎలా పనిచేస్తుంది?" : "How does it work?"} <span>❓</span></h2>
              <p>
                {lang === "te"
                  ? "ఏడు పారామితులను నమోదు చేయండి. మెషిన్ లెర్నింగ్ మోడల్ మీ కొలతలను విశ్లేషించి, శిక్షణ డేటా ఆధారంగా అనువైన పంటలను సూచిస్తుంది."
                  : "Enter all seven parameters. The machine learning model evaluates your measurements and predicts suitable crops based on patterns learned from its training dataset."}
              </p>
            </div>

            <div className="recommendation-results-heading">
              <div>
                <span className="prediction-section-label">
                  {lang === "te" ? "మీ విశ్లేషణ" : "YOUR ANALYSIS"}
                </span>
                <h2>{t("predResultsTitle")}</h2>
              </div>
            </div>
          </div>

          {!result && !loading && (
            <div className="prediction-empty-state">
              <div className="empty-state-icon">🌱</div>
              <h2>{lang === "te" ? "విశ్లేషణ ఇంకా జరగలేదు" : "No Analysis Available"}</h2>
              <p>
                {lang === "te"
                  ? "పంట సిఫార్సు ప్రారంభించడానికి కుడివైపు మీ నేల మరియు వాతావరణ వివరాలను నమోదు చేసి బటన్ నొక్కండి."
                  : "Enter your soil and climate measurements to get started with crop recommendation."}
              </p>
            </div>
          )}

          {loading && (
            <div className="prediction-loading-state">
              <div className="prediction-spinner" />
              <h2>{lang === "te" ? "నేల వివరాలను విశ్లేషిస్తున్నాము" : "Evaluating your soil profile"}</h2>
              <p>{t("predBtnPredicting")}</p>
            </div>
          )}

          {result && (
            <div className="prediction-output-wrapper">
              {/* RELIABILITY */}
              <div className={`reliability-banner ${reliability}`}>
                <div className="reliability-banner-header">
                  <span className="reliability-indicator" />
                  <strong>
                    {reliability === "level_1_reference" && t("predReliabilityNormal")}
                    {reliability === "level_2_unusual" && t("predReliabilityUnusual")}
                    {reliability === "level_3_severe_or_invalid" && t("predReliabilitySevere")}
                  </strong>
                </div>

                <p className="reliability-banner-desc">
                  {reliability === "level_1_reference" &&
                    (lang === "te"
                      ? "నమోదు చేసిన విలువలు సాధారణ వ్యవసాయ సహజ పరిమితులకు అనుగుణంగా ఉన్నాయి."
                      : "Measurements are within the reference dataset's observed bounds and typical distribution.")}
                  {reliability === "level_2_unusual" &&
                    (lang === "te"
                      ? "కొన్ని విలువలు అసాధారణంగా ఉన్నాయి. ఫలితాలను విచక్షణతో పరిశీలించండి."
                      : "The input profile contains unusual measurements or combinations. Interpret the recommendation cautiously.")}
                  {reliability === "level_3_severe_or_invalid" &&
                    (lang === "te"
                      ? "నమోదు చేసిన విలువలు వ్యవసాయ పరిమితికి మించి ఉన్నాయి. సిఫార్సు నిలిపివేయబడింది."
                      : "The input profile contains severe anomalies or invalid measurements. The recommendation is withheld.")}
                </p>

                
              </div>

              {/* WITHHELD RECOMMENDATION */}
              {result.recommendation_withheld ? (
                <div className="withheld-card">
                  <div className="withheld-icon">🛡️</div>
                  <h2>{lang === "te" ? "సిఫార్సు నిలిపివేయబడింది" : "Recommendation Withheld"}</h2>

                  <p className="withheld-lead">
                    {lang === "te"
                      ? "ఇచ్చిన విలువలు వ్యవసాయ సహజ పరిమితులకు భిన్నంగా ఉన్నందున పంట సిఫార్సు జారీ కాలేదు."
                      : "No crop recommendation is issued because the input profile contains severe anomalies or unviable parameters."}
                  </p>

                  <div className="withheld-reasons-box">
                    <strong>{lang === "te" ? "గమనించిన కారణాలు:" : "Diagnostic Findings"}</strong>
                    <ul>
                      {result.input_warnings?.map((warning, index) => (
                        <li key={index}>{warning}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              ) : (
                <>
                  {/* PRIMARY CROP */}
                  <div className="prediction-hero-crop">
                    <span className="prediction-step">
                      {lang === "te" ? "ప్రధాన పంట సిఫార్సు" : "PRIMARY SUITABILITY RECOMMENDATION"}
                    </span>

                    <div className="prediction-crop-header">
                      <div className="prediction-crop-symbol">🌱</div>
                      <div>
                        <h2>{formatCrop(result.predicted_crop, lang)}</h2>
                        <p>{lang === "te" ? "ఈ నేల మరియు వాతావరణానికి అత్యంత అనుకూలమైన పంట" : "Leading candidate for this soil profile"}</p>
                      </div>
                    </div>
                  </div>

                  {/* TOP THREE CROPS */}
                  <div className="prediction-candidates-section">
                    <h3 className="section-title">
                      {t("predAlternatives")}
                    </h3>

                    <div className="candidates-list">
                      {result.top_3?.map((item) => (
                        <div className="candidate-item" key={item.crop}>
                          <div className="candidate-header">
                            <span className="candidate-name">
                              {formatCrop(item.crop, lang)}
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
                      <strong>{lang === "te" ? "గమనిక:" : "Note:"}</strong>{" "}
                      {lang === "te"
                        ? "శాతాలు మోడల్ వర్గీకరణ సంభావ్యతను సూచిస్తాయి. ఇవి ఆర్థిక లాభాన్ని లేదా దిగుబడిని నేరుగా హామీ ఇవ్వవు."
                        : "Percentages represent classification probabilities from the trained model. They do not predict harvest yield or financial profitability."}
                    </p>
                  </div>

                  {/* INPUT WARNINGS */}
                  {result.input_warnings?.length > 0 && (
                    <div className="warnings-container">
                      <strong>{lang === "te" ? "ఇన్పుట్ హెచ్చరికలు" : "Input Distribution Warnings"}</strong>
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
                        ? t("predBtnExplaining")
                        : `${t("predBtnExplain")} →`}
                    </button>

                    <span className="explain-hint">
                      {lang === "te"
                        ? `${formatCrop(result.predicted_crop, lang)} ఎందుకు సిఫార్సు చేయబడిందో పోషకాల ప్రభావాన్ని చూడండి`
                        : `View the feature contributions for ${result.predicted_crop}`}
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
                    <span className="prediction-step">
                      {lang === "te" ? "వివరణాత్మక AI (SHAP)" : "EXPLAINABLE AI"}
                    </span>
                    <h2>
                      {lang === "te"
                        ? `${formatCrop(explanation.predicted_crop, lang)} ఎందుకు ఎంపికైంది?`
                        : `Why ${explanation.predicted_crop}?`}
                    </h2>
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
                            <small>{lang === "te" ? "విలువ" : "Input"}: {item.value}</small>
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
                      <i className="legend-dot pos" /> {t("predFactorPositive")}
                    </span>
                    <span>
                      <i className="legend-dot neg" /> {t("predFactorNegative")}
                    </span>
                  </div>
                </section>
              )}

              {/* ADDITIONAL EXPLAINABILITY INSIGHTS */}
              {explanation && (
                <div className="explainability-addons" style={{ display: "grid", gap: "18px", marginTop: "18px" }}>
                  {/* NATURAL LANGUAGE SUMMARY */}
                  {explanation.prediction_summary && (
                    <section className="shap-explanation-card explainability-summary-card">
                      <span className="prediction-step">{lang === "te" ? "మోడల్ వివరణ" : "MODEL INTERPRETATION"}</span>
                      <h3>{lang === "te" ? "ఈ సిఫార్సు ఎందుకు?" : "Prediction Summary"}</h3>
                      <p>{explanation.prediction_summary}</p>
                    </section>
                  )}

                  {/* TOP THREE INFLUENTIAL FEATURES */}
                  {Array.isArray(explanation.top_factors) && explanation.top_factors.length > 0 && (
                    <section className="shap-explanation-card">
                      <span className="prediction-step">{lang === "te" ? "ముఖ్యమైన లక్షణాలు" : "FEATURE IMPORTANCE"}</span>
                      <h3>{lang === "te" ? "అత్యంత ప్రభావవంతమైన 3 పారామితులు" : "Top 3 Influential Features"}</h3>
                      <div style={{ display: "grid", gap: "12px", marginTop: "14px" }}>
                        {explanation.top_factors.slice(0, 3).map((item, index) => (
                          <div key={item.feature} style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                            <strong style={{ minWidth: "28px" }}>#{index + 1}</strong>
                            <div style={{ flex: 1 }}>
                              <div style={{ display: "flex", justifyContent: "space-between", gap: "10px", marginBottom: "5px" }}>
                                <strong>{item.feature}</strong>
                                <span style={{ color: Number(item.shap_value) >= 0 ? "#159b60" : "#e5675f" }}>
                                  {Number(item.shap_value) >= 0 ? "+" : ""}{Number(item.shap_value).toFixed(4)}
                                </span>
                              </div>
                              <div style={{ height: "7px", background: "#edf2ee", borderRadius: "20px", overflow: "hidden" }}>
                                <div style={{ height: "100%", width: `${Math.min(Math.abs(Number(item.shap_value)) * 300, 100)}%`, background: Number(item.shap_value) >= 0 ? "#20a66a" : "#e5675f", borderRadius: "20px" }} />
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </section>
                  )}

                  {/* POSITIVE AND NEGATIVE CONTRIBUTORS */}
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(230px, 1fr))", gap: "18px" }}>
                    <section className="shap-explanation-card">
                      <h3 style={{ color: "#159b60" }}>{lang === "te" ? "అనుకూల ప్రభావాలు" : "Positive Contributors"}</h3>
                      {explanation.positive_factors?.length > 0 ? (
                        <ul style={{ paddingLeft: "20px", marginBottom: 0 }}>
                          {explanation.positive_factors.map((item) => (
                            <li key={item.feature} style={{ margin: "8px 0" }}>
                              <strong>{item.feature}</strong>: +{Number(item.shap_value).toFixed(4)}
                            </li>
                          ))}
                        </ul>
                      ) : <p>{lang === "te" ? "అనుకూల ప్రభావాలు లేవు." : "No positive contributions were identified."}</p>}
                    </section>

                    <section className="shap-explanation-card">
                      <h3 style={{ color: "#e5675f" }}>{lang === "te" ? "ప్రతికూల ప్రభావాలు" : "Negative Contributors"}</h3>
                      {explanation.negative_factors?.length > 0 ? (
                        <ul style={{ paddingLeft: "20px", marginBottom: 0 }}>
                          {explanation.negative_factors.map((item) => (
                            <li key={item.feature} style={{ margin: "8px 0" }}>
                              <strong>{item.feature}</strong>: {Number(item.shap_value).toFixed(4)}
                            </li>
                          ))}
                        </ul>
                      ) : <p>{lang === "te" ? "ప్రతికూల ప్రభావాలు లేవు." : "No negative contributions were identified."}</p>}
                    </section>
                  </div>

                  {/* INPUT CONDITION ANALYSIS */}
                  {Array.isArray(explanation.input_analysis) && explanation.input_analysis.length > 0 && (
                    <section className="shap-explanation-card">
                      <span className="prediction-step">{lang === "te" ? "ఇన్పుట్ విశ్లేషణ" : "DATA DISTRIBUTION CHECK"}</span>
                      <h3>{lang === "te" ? "ఇన్పుట్ పరిస్థితుల విశ్లేషణ" : "Input Condition Analysis"}</h3>
                      <p>{lang === "te" ? "మీరు నమోదు చేసిన విలువలు శిక్షణ డేటా పంపిణీతో ఎలా పోలుస్తాయో చూపిస్తుంది." : "Compares each entered measurement with the distribution of the training dataset."}</p>
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "10px", marginTop: "14px" }}>
                        {explanation.input_analysis.map((item) => {
                          const conditionColor = item.condition === "Low" ? "#d18a27" : item.condition === "High" ? "#3978c5" : "#159b60";
                          return (
                            <div key={item.feature} style={{ border: "1px solid #e2ebe4", borderRadius: "10px", padding: "12px" }}>
                              <div style={{ display: "flex", justifyContent: "space-between", gap: "8px", alignItems: "center" }}>
                                <strong>{item.feature}</strong>
                                <span style={{ color: conditionColor, background: `${conditionColor}18`, padding: "3px 8px", borderRadius: "20px", fontSize: "12px", fontWeight: 600 }}>{item.condition}</span>
                              </div>
                              <p style={{ margin: "8px 0 4px" }}>{lang === "te" ? "నమోదు చేసిన విలువ" : "Input"}: <strong>{item.value}</strong></p>
                              <small>{lang === "te" ? "డేటాసెట్ మధ్య విలువ" : "Dataset median"}: {Number(item.dataset_median).toFixed(2)}</small>
                              <p style={{ margin: "7px 0 0", fontSize: "12px", opacity: 0.8 }}>{item.description}</p>
                            </div>
                          );
                        })}
                      </div>
                    </section>
                  )}

                  {/* TOP THREE EXPLANATION CROP PROBABILITIES */}
                  {Array.isArray(explanation.top_crops) && explanation.top_crops.length > 0 && (
                    <section className="shap-explanation-card">
                      <span className="prediction-step">{lang === "te" ? "పంటల పోలిక" : "MODEL COMPARISON"}</span>
                      <h3>{lang === "te" ? "మొదటి 3 పంటల సంభావ్యతలు" : "Top 3 Crop Probability Comparison"}</h3>
                      <div style={{ display: "grid", gap: "13px", marginTop: "14px" }}>
                        {explanation.top_crops.map((item, index) => {
                          const percentage = Number(item.percentage ?? (Number(item.probability) * 100)) || 0;
                          return (
                            <div key={item.crop}>
                              <div style={{ display: "flex", justifyContent: "space-between", gap: "10px", marginBottom: "6px" }}>
                                <strong>{index + 1}. {formatCrop(item.crop, lang)}</strong>
                                <strong>{percentage.toFixed(2)}%</strong>
                              </div>
                              <div style={{ height: "9px", background: "#edf2ee", borderRadius: "20px", overflow: "hidden" }}>
                                <div style={{ height: "100%", width: `${Math.min(Math.max(percentage, 0), 100)}%`, background: index === 0 ? "#20a66a" : "#8abda0", borderRadius: "20px" }} />
                              </div>
                            </div>
                          );
                        })}
                      </div>
                      {explanation.probability_analysis?.probability_difference != null && (
                        <p style={{ marginTop: "14px" }}>
                          {lang === "te" ? "మొదటి మరియు రెండవ పంటల మధ్య సంభావ్యత తేడా:" : "Probability gap between the top two crops:"}
                          <strong> {Number(explanation.probability_analysis.probability_difference).toFixed(2)} percentage points</strong>
                        </p>
                      )}
                    </section>
                  )}

                  <p className="probability-caveat">
                    <strong>{lang === "te" ? "గమనిక:" : "Interpretation note:"}</strong>{" "}
                    {lang === "te"
                      ? "SHAP విలువలు మోడల్ అంచనాపై ఇన్పుట్ లక్షణాల ప్రభావాన్ని వివరిస్తాయి. అవి వ్యవసాయ కారణ సంబంధాన్ని లేదా దిగుబడి హామీని నిరూపించవు."
                      : "SHAP contributions describe the model's output relative to its background data. They do not establish agricultural causation, guarantee crop suitability, or predict yield."}
                  </p>
                </div>
              )}
            </div>
          )}
        </section>

        {/* RIGHT COLUMN: SEVEN MODEL INPUTS */}
        <form className="prediction-form-card" onSubmit={predictCrop}>
          <div className="prediction-card-heading">
            <div>
              <span className="prediction-section-label">
                {lang === "te" ? "పొలం వివరాలు" : "FIELD PARAMETERS"}
              </span>
              <h2>{t("predFormHeader")}</h2>
              <p>{t("predFormDesc")}</p>
            </div>

            <button
              className="prediction-reset-btn"
              type="button"
              onClick={resetExample}
            >
              <span>↻</span> {t("predBtnReset")}
            </button>
          </div>

          <div className="prediction-fields-grid">
            {defaultFields.map((field) => (
              <label className="prediction-field-group" key={field.key}>
                <span className="field-label-text">{t(field.labelKey)}</span>

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
                  {lang === "te" ? "సాధారణ పరిధి" : "Observed range"}: {field.range} {field.unit}
                </span>
              </label>
            ))}
          </div>

          <button
            className="prediction-primary-btn"
            type="submit"
            disabled={loading}
          >
            {loading ? t("predBtnPredicting") : `${t("predBtnPredict")} →`}
          </button>

          <p className="prediction-help-text">
            {t("predNotice")}
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
