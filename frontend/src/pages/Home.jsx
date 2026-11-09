import { Link } from "react-router-dom";
import { useLanguage } from "../context/LanguageContext";
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

export default function Home() {
  const { t, lang } = useLanguage();

  const actions = [
    {
      label: t("dashAction1Title"),
      description: t("dashAction1Desc"),
      icon: "sprout",
      to: "/prediction",
      color: "green",
    },
    {
      label: t("dashAction2Title"),
      description: t("dashAction2Desc"),
      icon: "chart",
      to: "/historical",
      color: "blue",
    },
    {
      label: t("dashAction3Title"),
      description: t("dashAction3Desc"),
      icon: "bot",
      to: "/agriassist",
      color: "purple",
    },
    {
      label: t("navAbout"),
      description: lang === "te" ? "వ్యవస్థ మరియు సాంకేతిక వివరాలను తెలుసుకోండి" : "Learn about the system and its technologies",
      icon: "leaf",
      to: "/about",
      color: "orange",
    },
  ];

  return (
    <main className="dashboard-page">
      {/* Dashboard Header */}
      <header className="dashboard-heading">
        <div className="dashboard-heading-copy">
          <span className="dashboard-eyebrow">
            {t("dashEyebrow")}
          </span>

          <h1>
            {t("dashTitle")} <span>{t("dashTitleHighlight")}</span>
          </h1>

          <p>
            {t("dashSubtitle")}
          </p>
        </div>

        <Link to="/prediction" className="dashboard-upload-button">
          <Icon name="sprout" size={18} />
          {t("dashStartPrediction")}
          <span className="dashboard-button-arrow">↗</span>
        </Link>
      </header>

      {/* Main Dashboard Content */}
      <section className="dashboard-main-grid">
        {/* Crop Recommendation Panel */}
        <article className="dashboard-panel latest-analysis-panel">
          <div className="panel-heading">
            <div>
              <span className="panel-eyebrow">
                {lang === "te" ? "మేధోపరమైన అంచనా" : "INTELLIGENT PREDICTION"}
              </span>

              <h2>{t("navPrediction")}</h2>

              <p>
                {lang === "te"
                  ? "నేల పోషకాలు మరియు పర్యావరణ పరిస్థితుల ఆధారంగా అనువైన పంటలను కనుగొనండి."
                  : "Discover suitable crops based on soil nutrients and environmental conditions."}
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

            <h3>{lang === "te" ? "మీ నేలను విశ్లేషించడానికి సిద్ధమా?" : "Ready to Analyze Your Soil?"}</h3>

            <p>
              {lang === "te"
                ? "నత్రజని, భాస్వరం, పొటాషియం, ఉష్ణోగ్రత, తేమ, pH మరియు వర్షపాతం విలువలను నమోదు చేసి శాస్త్రీయ పంట సిఫార్సులను పొందండి."
                : "Enter nitrogen, phosphorus, potassium, temperature, humidity, soil pH, and rainfall values to receive intelligent crop recommendations with explanations."}
            </p>

            <Link
              to="/prediction"
              className="empty-upload-button"
            >
              {t("dashStartPrediction")}
              <Icon name="arrow" size={16} />
            </Link>
          </div>

          <div className="analysis-panel-footer">
            <span>
              <Icon name="leaf" size={14} />
              TabPFN Machine Learning
            </span>

            <span>Explainable predictions with SHAP</span>
          </div>
        </article>

        {/* Quick Actions */}
        <article className="dashboard-panel quick-actions-panel">
          <div className="panel-heading">
            <div>
              <span className="panel-eyebrow">
                {lang === "te" ? "ఫీచర్లు" : "EXPLORE FEATURES"}
              </span>

              <h2>{t("dashQuickActions")}</h2>

              <p>{lang === "te" ? "అగ్రిస్మార్ట్ సాధనాలను యాక్సెస్ చేయండి." : "Access your AgriSmart tools."}</p>
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
            {lang === "te" ? "అన్ని వ్యవసాయ సాధనాలు ఒకే వేదికపై" : "All agricultural tools in one workspace"}
          </div>
        </article>
      </section>

      {/* Bottom Information */}
      <section className="dashboard-bottom-note">
        <div className="bottom-note-icon">
          <Icon name="leaf" size={22} />
        </div>

        <div>
          <strong>{lang === "te" ? "తెలివైన వ్యవసాయ నిర్ణయాలు" : "Smarter Agricultural Decisions"}</strong>
          <p>
            {lang === "te"
              ? "అగ్రిస్మార్ట్ మెషిన్ లెర్నింగ్, ఎక్స్‌ప్లెయినబుల్ AI, చారిత్రక వ్యవసాయ డేటా మరియు AI సహాయకుడిని కలిపి పారదర్శకమైన పంట ప్రణాళికను అందిస్తుంది."
              : "AgriSmart combines machine learning, explainable AI, historical agricultural data, and conversational assistance to support informed crop planning."}
          </p>
        </div>

        <Link to="/about" className="bottom-note-link">
          {t("navAbout")} <span>↗</span>
        </Link>
      </section>
    </main>
  );
}
