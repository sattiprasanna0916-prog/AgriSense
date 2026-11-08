import "./About.css";

const coreModules = [
  {
    number: "01",
    title: "TabPFN Tabular Classifier",
    description:
      "Uses a trained Prior-Data Fitted Network (TabPFN) to rank 22 crop candidates based on 7 soil and climate measurements without requiring conventional gradient descent tuning at inference time.",
  },
  {
    number: "02",
    title: "Three-Level Reliability Policy",
    description:
      "Safeguards against extrapolation and typos by distinguishing within-reference inputs (Level 1), unusual combinations (Level 2), and severely unfamiliar or invalid inputs where recommendations are safely withheld (Level 3).",
  },
  {
    number: "03",
    title: "SHAP Explainability",
    description:
      "Uses KernelExplainer to compute local feature attributions, revealing which specific soil nutrients and climate measurements increased or decreased model confidence for the predicted crop.",
  },
  {
    number: "04",
    title: "Regional Historical Context",
    description:
      "Maintains an independent 1997–2014 district-level production dataset to provide regional agricultural history without conflating historical planting with field-level soil suitability.",
  },
  {
    number: "05",
    title: "AgriAssist AI Assistant",
    description:
      "A context-aware agricultural assistant powered by Google Gemini and grounded in verified historical production data for interactive agricultural exploration.",
  },
  {
    number: "06",
    title: "Rigorous Leak-Free Evaluation",
    description:
      "Evaluated across stratified 5-fold cross-validation and an isolated 440-record held-out test split, measuring Multiclass Log Loss, Multiclass Brier Score, and Expected Calibration Error (ECE).",
  },
];

const inputFeatures = [
  ["N", "Nitrogen ratio", "kg/ha", "0 – 140", "Essential macronutrient for vegetative plant growth and chlorophyll."],
  ["P", "Phosphorus ratio", "kg/ha", "5 – 145", "Key for root development, flowering, and cellular energy transfer."],
  ["K", "Potassium ratio", "kg/ha", "5 – 205", "Regulates stomatal opening, water retention, and enzyme activation."],
  ["Temperature", "Ambient temperature", "°C", "8.8 – 43.7", "Governs metabolic rates and physiological thermal thresholds."],
  ["Humidity", "Relative humidity", "%", "14.3 – 100.0", "Affects transpiration, fungal disease pressure, and pollination."],
  ["pH", "Soil acidity/alkalinity", "pH", "3.5 – 9.9", "Controls bioavailability of soil minerals and root nutrient absorption."],
  ["Rainfall", "Precipitation volume", "mm", "20.2 – 298.6", "Key seasonal moisture parameter across growth cycles."],
];

export default function About() {
  return (
    <main className="about-page">
      <header className="about-hero">
        <span className="about-eyebrow">RESEARCH & METHODOLOGY</span>
        <h1>
          Explainable AI for
          <br />
          <span>agricultural decision support.</span>
        </h1>
        <p>
          AgriSmart is an academic decision-support prototype combining modern
          tabular foundation models, explainable AI, empirical distribution safeguards,
          and regional production history to investigate agricultural suitability responsibly.
        </p>

        <div className="about-metrics-bar">
          <div className="about-metric-card">
            <strong>7</strong>
            <span>Model Input Features</span>
          </div>
          <div className="about-metric-card">
            <strong>22</strong>
            <span>Crop Classifications</span>
          </div>
          <div className="about-metric-card">
            <strong>3 Levels</strong>
            <span>Input Reliability Policy</span>
          </div>
          <div className="about-metric-card">
            <strong>99.32%</strong>
            <span>Held-Out Accuracy</span>
          </div>
        </div>
      </header>

      {/* Core Modules Grid */}
      <section className="about-section">
        <div className="about-section-header">
          <span className="about-eyebrow">ARCHITECTURAL PILLARS</span>
          <h2>Integrated Decision Support Modules</h2>
          <p>
            AgriSmart brings together prediction, explainability, safety guardrails, and regional analytics.
          </p>
        </div>

        <div className="about-modules-grid">
          {coreModules.map((item) => (
            <article className="about-module-card" key={item.number}>
              <span className="about-module-num">{item.number}</span>
              <h3>{item.title}</h3>
              <p>{item.description}</p>
            </article>
          ))}
        </div>
      </section>

      {/* Input Features Table */}
      <section className="about-section">
        <div className="about-section-header">
          <span className="about-eyebrow">FEATURE SPECIFICATION</span>
          <h2>Seven Soil & Climate Parameters</h2>
          <p>
            The TabPFN classifier accepts exactly seven continuous numerical features observed across the benchmark dataset.
          </p>
        </div>

        <div className="about-table-wrap">
          <table className="about-spec-table">
            <thead>
              <tr>
                <th>Feature</th>
                <th>Parameter Name</th>
                <th>Unit</th>
                <th>Observed Range</th>
                <th>Agronomic Role</th>
              </tr>
            </thead>
            <tbody>
              {inputFeatures.map(([sym, name, unit, range, role]) => (
                <tr key={sym}>
                  <td><code className="feature-code">{sym}</code></td>
                  <td><strong>{name}</strong></td>
                  <td>{unit}</td>
                  <td><span className="range-badge">{range}</span></td>
                  <td>{role}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Three-Level Reliability Policy Explanation */}
      <section className="about-policy-section">
        <div className="about-section-header">
          <span className="about-eyebrow">RELIABILITY SAFEGUARDS</span>
          <h2>Three-Level Input Reliability Architecture</h2>
          <p>
            Machine learning models should not silently hallucinate on unfamiliar or impossible inputs.
            AgriSmart implements an empirical multi-level policy derived via leakage-free cross-validation:
          </p>
        </div>

        <div className="about-policy-cards">
          <div className="about-policy-card level1">
            <div className="policy-badge">Level 1: Reference Distribution</div>
            <h3>Normal Recommendation</h3>
            <p>
              Inputs fall within observed training ranges and have a standardized 5-NN distance
              &le; 0.9158 (95th percentile). Top-3 crop recommendations and percentages are displayed normally.
            </p>
          </div>

          <div className="about-policy-card level2">
            <div className="policy-badge">Level 2: Unusual Profile</div>
            <h3>Prediction with Warning</h3>
            <p>
              Inputs are physically feasible but exceed observed dataset bounds or form an atypical
              multivariate combination (distance 0.92 to 3.00). Model predictions are shown with prominent
              cautionary disclosures regarding extrapolation.
            </p>
          </div>

          <div className="about-policy-card level3">
            <div className="policy-badge">Level 3: Severely Unfamiliar</div>
            <h3>Recommendation Withheld</h3>
            <p>
              Inputs violate physical laws (e.g. negative nutrients, humidity &gt; 100%), exceed agricultural
              guardrails (e.g. caustic pH 13), or exceed severe distance &gt; 3.00. The recommendation is safely
              withheld to prevent misleading agricultural guidance.
            </p>
          </div>
        </div>
      </section>

      {/* Probability Calibration Study Findings */}
      <section className="about-calibration-section">
        <div className="about-section-header">
          <span className="about-eyebrow">CALIBRATION STUDY FINDINGS</span>
          <h2>Probability Calibration & Integrity</h2>
          <p>
            An exhaustive 5-fold cross-validation calibration study was conducted on the 1,760 training samples
            (leaving the 440 test records completely isolated):
          </p>
        </div>

        <div className="about-calibration-content">
          <div className="calibration-finding-card">
            <h4>Empirical Calibration Results</h4>
            <ul>
              <li>
                <strong>Uncalibrated TabPFN:</strong> Mean top-1 confidence (99.28%) matches empirical accuracy (99.32%)
                with a remarkably low Top-1 Expected Calibration Error (ECE) of 0.27% and Log Loss of 0.01450.
              </li>
              <li>
                <strong>Temperature Scaling:</strong> Converged to T &approx; 0.84 with an imperceptible log loss delta
                (-0.00021), but slightly degraded the multiclass Brier score (+0.00015).
              </li>
              <li>
                <strong>Isotonic Calibration:</strong> Degraded all metrics (accuracy dropped from 99.32% to 99.03%,
                and Log Loss doubled to 0.03045) due to non-parametric step flattening across 22 classes.
              </li>
            </ul>
            <div className="calibration-verdict">
              <strong>Methodological Decision:</strong> In accordance with scientific integrity, the original
              uncalibrated model probabilities are retained with clear disclaimers, rather than applying artificial post-hoc scaling.
            </div>
          </div>
        </div>
      </section>

      {/* Disclaimers & Responsible Use */}
      <section className="about-responsible-box">
        <span className="about-eyebrow">ETHICAL & RESPONSIBLE USE</span>
        <h2>Decision Support Disclaimers</h2>
        <p>
          1. <strong>Synthetic Benchmark Dataset:</strong> The 2,200 records in `Crop_recommendation.csv` represent a
          curated dataset with well-separated clusters. Accuracy on this dataset does not prove identical performance
          across real-world heterogeneous farm soils with unmeasured micronutrients or biological activity.
        </p>
        <p>
          2. <strong>Suitability vs Regional Production:</strong> Historical district records describe past crop yields
          and planting decisions; they do not assess specific soil chemistry or microclimates. Historical production
          must never be treated as ground-truth suitability.
        </p>
        <p>
          3. <strong>Agronomic Guidance:</strong> This prototype does not substitute for on-site soil laboratory
          assays, certified agronomic extension advice, or agricultural risk management.
        </p>
      </section>
    </main>
  );
}
