import { Link } from "react-router-dom";
import "./Home.css";

export default function Home() {
  return (
    <main className="home-page">
      <section className="home-hero">
        <div className="home-copy">
          <span className="home-eyebrow">
            EXPLAINABLE AI · TABPFN CLASSIFIER · AGRICULTURAL DECISION SUPPORT
          </span>

          <h1>
            Smarter crop decisions.
            <br />
            <span>Reliability beyond prediction.</span>
          </h1>

          <p>
            AgriSense combines modern tabular foundation AI (TabPFN) with local SHAP feature
            explanations, a three-level input reliability policy, and district-level
            historical production context (1997–2014) to help researchers and agronomists
            investigate crop suitability responsibly.
          </p>

          <div className="home-actions">
            <Link className="home-primary-link" to="/prediction">
              Explore Crop Predictions <span>→</span>
            </Link>
            <Link className="home-secondary-link" to="/historical">
              Regional Production History
            </Link>
          </div>

          <div className="home-stats">
            <div className="home-stat-item">
              <strong>22</strong>
              <span>Crop candidates</span>
            </div>
            <div className="home-stat-item">
              <strong>7</strong>
              <span>Soil & climate inputs</span>
            </div>
            <div className="home-stat-item">
              <strong>3-Level</strong>
              <span>Reliability policy</span>
            </div>
            <div className="home-stat-item">
              <strong>18 Yrs</strong>
              <span>Historical context</span>
            </div>
          </div>
        </div>

        <div className="home-visual">
          <img
            src="https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=1100&q=85"
            alt="Vibrant agricultural field under natural sunlight"
            className="home-hero-image"
          />
          <div className="home-image-card">
            <span className="image-card-icon">🌱</span>
            <div>
              <strong>Explainable Agronomic AI</strong>
              <p>
                Evaluates soil nutrients, temperature, humidity, pH, and precipitation with
                transparent attribution.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Feature Navigation Grid */}
      <section className="home-explore">
        <div className="home-section-heading">
          <span className="home-eyebrow">SYSTEM ARCHITECTURE</span>
          <h2>Integrated Decision Support Modules</h2>
          <p>
            Explore the four interconnected modules designed for transparent, reliable agricultural exploration.
          </p>
        </div>

        <div className="home-card-grid">
          <Link className="home-feature-card" to="/prediction">
            <span className="home-card-number">01</span>
            <div className="home-card-icon">🌱</div>
            <h3>TabPFN Crop Recommendation</h3>
            <p>
              Ranks top-3 crop candidates using a trained TabPFN classifier evaluated against nitrogen,
              phosphorus, potassium, temperature, humidity, pH, and rainfall.
            </p>
            <span className="home-card-link">Explore predictions →</span>
          </Link>

          <Link className="home-feature-card" to="/prediction">
            <span className="home-card-number">02</span>
            <div className="home-card-icon">🛡️</div>
            <h3>Three-Level Reliability Policy</h3>
            <p>
              Protects against extrapolation and data-entry errors by separating within-reference inputs,
              unusual combinations, and severely unfamiliar profiles where recommendations are withheld.
            </p>
            <span className="home-card-link">Test input safeguards →</span>
          </Link>

          <Link className="home-feature-card" to="/prediction">
            <span className="home-card-number">03</span>
            <div className="home-card-icon">🔍</div>
            <h3>SHAP Feature Explainability</h3>
            <p>
              Inspects how each soil nutrient and climate measurement pushed the model's confidence toward
              or against the predicted crop, grounding predictions in transparent attributions.
            </p>
            <span className="home-card-link">View XAI explanations →</span>
          </Link>

          <Link className="home-feature-card" to="/historical">
            <span className="home-card-number">04</span>
            <div className="home-card-icon">📊</div>
            <h3>Regional Historical Insights</h3>
            <p>
              Explores district-level crop production totals and longitudinal trends (1997–2014), clearly
              separated from field-level soil suitability predictions.
            </p>
            <span className="home-card-link">Explore historical records →</span>
          </Link>

          <Link className="home-feature-card" to="/agriassist">
            <span className="home-card-number">05</span>
            <div className="home-card-icon">💬</div>
            <h3>AgriAssist Chatbot</h3>
            <p>
              Ask agronomic questions regarding soil management, fertilizers, irrigation, and district
              production with context-grounded AI responses.
            </p>
            <span className="home-card-link">Chat with AgriAssist →</span>
          </Link>

          <Link className="home-feature-card" to="/about">
            <span className="home-card-number">06</span>
            <div className="home-card-icon">🧪</div>
            <h3>Methodology & Benchmarks</h3>
            <p>
              Review the cross-validation benchmarks, probability calibration evaluation, baseline Random Forest
              comparisons, and system limitations.
            </p>
            <span className="home-card-link">Read documentation →</span>
          </Link>
        </div>
      </section>

      {/* Prominent Educational Notice */}
      <section className="home-responsible-notice">
        <div className="notice-inner">
          <div className="notice-icon">📋</div>
          <div>
            <strong>Educational & Research Prototype Notice</strong>
            <p>
              AgriSense is an academic decision-support prototype. Model percentages reflect classification
              certainty on benchmark dataset clusters and do not forecast real-world harvest yield, pest
              resistance, or financial outcomes. Historical district production records describe past regional
              activity, not future suitability. Consult local agricultural extension officers before making
              farming decisions.
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}
