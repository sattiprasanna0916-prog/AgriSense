
import { Link } from "react-router-dom";
import "./Home.css";

function Icon({ name, size = 18 }) {
  const common = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.8,
    strokeLinecap: "round",
    strokeLinejoin: "round",
    "aria-hidden": true,
  };

  const paths = {
    leaf: (
      <>
        <path d="M20 4c-8 0-14 4-14 11a5 5 0 0 0 5 5c7 0 11-6 9-16Z" />
        <path d="M4 21c3-6 7-9 13-12" />
      </>
    ),
    sprout: (
      <>
        <path d="M12 21v-9" />
        <path d="M12 12C5 12 4 7 4 4c5 0 8 2 8 8Z" />
        <path d="M12 15c0-6 3-9 8-9 0 5-2 9-8 9Z" />
      </>
    ),
    chart: (
      <>
        <path d="M4 19V5" />
        <path d="M4 19h17" />
        <path d="m7 14 4-4 3 2 5-6" />
      </>
    ),
    bot: (
      <>
        <rect x="4" y="7" width="16" height="13" rx="3" />
        <path d="M12 3v4m-4 5h.01M16 12h.01M9 16h6" />
      </>
    ),
    arrow: (
      <>
        <path d="M5 12h14" />
        <path d="m13 6 6 6-6 6" />
      </>
    ),
  };

  return <svg {...common}>{paths[name]}</svg>;
}

const metrics = [
  {
    title: "Crop Classification",
    value: "22 Crops",
    description: "Available crop categories",
    icon: "sprout",
    color: "green",
  },
  {
    title: "Machine Learning",
    value: "TabPFN",
    description: "Transformer-based tabular classifier",
    icon: "chart",
    color: "blue",
  },
  {
    title: "Explainable AI",
    value: "SHAP",
    description: "Feature contribution explanations",
    icon: "leaf",
    color: "green",
  },
];

const actions = [
  {
    label: "Crop Recommendations",
    description: "Predict suitable crops using soil and climate inputs",
    icon: "sprout",
    to: "/prediction",
    color: "green",
  },
  {
    label: "Historical Insights",
    description: "Explore historical agricultural production trends",
    icon: "chart",
    to: "/historical",
    color: "blue",
  },
  {
    label: "AI Assistant",
    description: "Get assistance with agricultural questions",
    icon: "bot",
    to: "/agriassist",
    color: "purple",
  },
  {
    label: "About AgriSmart",
    description: "Learn about the system and its technologies",
    icon: "leaf",
    to: "/about",
    color: "orange",
  },
];

export default function Home() {
  return (
    <main className="dashboard-page">

      {/* Dashboard Header */}
      <header className="dashboard-heading">
        <div className="dashboard-heading-copy">
          <span className="dashboard-eyebrow">
            AGRISMART WORKSPACE
          </span>

          <h1>
            Dashboard <span>Overview</span>
          </h1>

          <p>
            Your intelligent agricultural decision-support workspace.
            Explore crop recommendations, historical insights, and AI assistance.
          </p>
        </div>

        <Link to="/prediction" className="dashboard-upload-button">
          <Icon name="sprout" size={18} />
          Get Crop Recommendation
          <span className="dashboard-button-arrow">↗</span>
        </Link>
      </header>

      {/* Overview Metrics */}
      <section className="dashboard-metrics">
        {metrics.map((metric, index) => (
          <article
            className="dashboard-metric-card"
            key={metric.title}
          >
            <div className="metric-card-top">
              <span className="metric-title">{metric.title}</span>

              <span className={`metric-icon ${metric.color}`}>
                <Icon name={metric.icon} size={21} />
              </span>
            </div>

            <div className="metric-value">
              {metric.value}
            </div>

            <p>{metric.description}</p>

            <span className="metric-index">
              0{index + 1}
            </span>
          </article>
        ))}
      </section>

      {/* Main Dashboard Content */}
      <section className="dashboard-main-grid">

        {/* Crop Recommendation Panel */}
        <article className="dashboard-panel latest-analysis-panel">
          <div className="panel-heading">
            <div>
              <span className="panel-eyebrow">
                INTELLIGENT PREDICTION
              </span>

              <h2>Crop Recommendation</h2>

              <p>
                Discover suitable crops based on soil nutrients
                and environmental conditions.
              </p>
            </div>

            <span className="panel-heading-icon">
              <Icon name="sprout" size={23} />
            </span>
          </div>

          <div className="analysis-empty-state">
            <div className="empty-illustration">
              <div className="empty-illustration-circle">
                <Icon name="sprout" size={43} />
              </div>
              <span className="empty-decoration decoration-one">✦</span>
              <span className="empty-decoration decoration-two">✧</span>
            </div>

            <h3>Ready to Analyze Your Soil?</h3>

            <p>
              Enter nitrogen, phosphorus, potassium, temperature,
              humidity, soil pH, and rainfall values to receive
              intelligent crop recommendations with explanations.
            </p>

            <Link
              to="/prediction"
              className="empty-upload-button"
            >
              Start Crop Recommendation
              <Icon name="arrow" size={16} />
            </Link>
          </div>

          <div className="analysis-panel-footer">
            <span>
              <Icon name="leaf" size={14} />
              Powered by TabPFN
            </span>

            <span>Explainable predictions with SHAP</span>
          </div>
        </article>

        {/* Quick Actions */}
        <article className="dashboard-panel quick-actions-panel">
          <div className="panel-heading">
            <div>
              <span className="panel-eyebrow">
                EXPLORE FEATURES
              </span>

              <h2>Quick Actions</h2>

              <p>Access your AgriSmart tools.</p>
            </div>
          </div>

          <div className="quick-actions-list">
            {actions.map((action) => (
              <Link
                to={action.to}
                className="quick-action-link"
                key={action.label}
              >
                <span className={`quick-action-icon ${action.color}`}>
                  <Icon name={action.icon} size={19} />
                </span>

                <span className="quick-action-copy">
                  <strong>{action.label}</strong>
                  <small>{action.description}</small>
                </span>

                <span className="quick-action-arrow">
                  <Icon name="arrow" size={16} />
                </span>
              </Link>
            ))}
          </div>

          <div className="quick-actions-footer">
            <span className="footer-status-dot" />
            All agricultural tools in one workspace
          </div>
        </article>
      </section>

      {/* Bottom Information */}
      <section className="dashboard-bottom-note">
        <div className="bottom-note-icon">
          <Icon name="leaf" size={22} />
        </div>

        <div>
          <strong>Smarter Agricultural Decisions</strong>
          <p>
            AgriSmart combines machine learning, explainable AI,
            historical agricultural data, and conversational assistance
            to support informed crop planning.
          </p>
        </div>

        <Link to="/about" className="bottom-note-link">
          Explore AgriSmart <span>↗</span>
        </Link>
      </section>

    </main>
  );
}
