
import { useLanguage } from "../context/LanguageContext";
import "./About.css";

const coreModules = [
  {
    number: "01",
    title: "TabPFN Crop Classification",
    description:
      "Uses a trained TabPFN machine learning model to recommend suitable crops from 22 crop classes based on seven soil and climate parameters.",
  },
  {
    number: "02",
    title: "Three-Level Reliability System",
    description:
      "Checks input values and identifies normal, unusual, and severely invalid conditions. Warnings are provided for unusual inputs, while unsafe recommendations are withheld.",
  },
  {
    number: "03",
    title: "SHAP Explainability",
    description:
      "Uses SHAP to explain the model's predictions by identifying which soil and climate features positively or negatively influence the recommended crop.",
  },
  {
    number: "04",
    title: "Regional Historical Insights",
    description:
      "Provides historical agricultural information through district-level crop production records to help users explore regional agricultural trends.",
  },
  {
    number: "05",
    title: "AgriAssist AI Assistant",
    description:
      "An interactive agricultural assistant powered by Google Gemini that provides conversational guidance on crop management, soil health, irrigation, and plant nutrition.",
  },
  {
    number: "06",
    title: "Model Evaluation",
    description:
      "Evaluates the crop recommendation model using training and testing data to assess its classification performance.",
  },
];

const inputFeatures = [
  [
    "N",
    "Nitrogen",
    "kg/ha",
    "0 – 140",
    "Supports vegetative growth and chlorophyll production.",
  ],
  [
    "P",
    "Phosphorus",
    "kg/ha",
    "5 – 145",
    "Supports root development and flowering.",
  ],
  [
    "K",
    "Potassium",
    "kg/ha",
    "5 – 205",
    "Helps regulate water balance and plant growth.",
  ],
  [
    "Temperature",
    "Ambient temperature",
    "°C",
    "8.8 – 43.7",
    "Influences plant growth and development.",
  ],
  [
    "Humidity",
    "Relative humidity",
    "%",
    "14.3 – 100.0",
    "Influences plant water balance and growth.",
  ],
  [
    "pH",
    "Soil pH",
    "pH",
    "3.5 – 9.9",
    "Affects nutrient availability in the soil.",
  ],
  [
    "Rainfall",
    "Rainfall",
    "mm",
    "20.2 – 298.6",
    "Provides information about water availability.",
  ],
];

export default function About() {
  const { lang } = useLanguage();
  const te = lang === "te";

  return (
    <main className="about-page">
      {/* HERO SECTION */}
      <header className="about-hero">
        <span className="about-eyebrow">
          {te ? "పరిశోధన & పద్ధతులు" : "RESEARCH & METHODOLOGY"}
        </span>

        <h1>
          {te
            ? "వ్యవసాయ నిర్ణయ మద్దతు కోసం "
            : "Explainable AI for "}
          <br />
          <span>
            {te
              ? "ఎక్స్‌ప్లెయినబుల్ AI సాంకేతికత."
              : "agricultural decision support."}
          </span>
        </h1>

        <p>
          {te
            ? "అగ్రిస్మార్ట్ అనేది మెషిన్ లెర్నింగ్, ఎక్స్‌ప్లెయినబుల్ AI మరియు విశ్వసనీయత తనిఖీలను ఉపయోగించి వ్యవసాయ పంట సిఫార్సులను అందించే నిర్ణయ మద్దతు వ్యవస్థ."
            : "AgriSmart is an agricultural decision-support system that uses machine learning, explainable AI, and input reliability checks to recommend suitable crops based on soil and climate conditions."}
        </p>

        {/* PROJECT METRICS */}
        <div className="about-metrics-bar">
          <div className="about-metric-card">
            <strong>2,200</strong>
            <span>
              {te ? "డేటాసెట్ రికార్డులు" : "Dataset Records"}
            </span>
          </div>

          <div className="about-metric-card">
            <strong>22</strong>
            <span>
              {te ? "పంటల తరగతులు" : "Crop Classes"}
            </span>
          </div>

          <div className="about-metric-card">
            <strong>7</strong>
            <span>
              {te ? "ఇన్‌పుట్ ఫీచర్లు" : "Input Features"}
            </span>
          </div>

          <div className="about-metric-card">
            <strong>3 Levels</strong>
            <span>
              {te ? "విశ్వసనీయత స్థాయిలు" : "Reliability Levels"}
            </span>
          </div>
        </div>
      </header>

      {/* CORE MODULES */}
      <section className="about-section">
        <div className="about-section-header">
          <span className="about-eyebrow">
            {te ? "ప్రధాన మాడ్యూల్స్" : "CORE MODULES"}
          </span>

          <h2>
            {te
              ? "సిస్టమ్ ప్రధాన భాగాలు"
              : "Integrated Decision Support Modules"}
          </h2>

          <p>
            {te
              ? "అగ్రిస్మార్ట్ పంట సిఫార్సులు, వివరణాత్మక AI, విశ్వసనీయత తనిఖీలు మరియు వ్యవసాయ విశ్లేషణలను కలిపి అందిస్తుంది."
              : "AgriSmart combines crop prediction, explainability, reliability safeguards, and agricultural insights in one application."}
          </p>
        </div>

        <div className="about-modules-grid">
          {coreModules.map((item) => (
            <article
              className="about-module-card"
              key={item.number}
            >
              <span className="about-module-num">
                {item.number}
              </span>

              <h3>{item.title}</h3>
              <p>{item.description}</p>
            </article>
          ))}
        </div>
      </section>

      {/* INPUT FEATURES */}
      <section className="about-section">
        <div className="about-section-header">
          <span className="about-eyebrow">
            {te ? "ఇన్‌పుట్ వివరాలు" : "INPUT SPECIFICATION"}
          </span>

          <h2>
            {te
              ? "ఏడు నేల మరియు వాతావరణ పారామితులు"
              : "Seven Soil & Climate Parameters"}
          </h2>

          <p>
            {te
              ? "పంట సిఫార్సు మోడల్ ఈ ఏడు సంఖ్యా విలువలను ఉపయోగిస్తుంది."
              : "The TabPFN crop classification model accepts seven numerical input features for crop recommendation."}
          </p>
        </div>

        <div className="about-table-wrap">
          <table className="about-spec-table">
            <thead>
              <tr>
                <th>{te ? "ఫీచర్" : "Feature"}</th>
                <th>{te ? "పారామీటర్ పేరు" : "Parameter Name"}</th>
                <th>{te ? "యూనిట్" : "Unit"}</th>
                <th>{te ? "పరిధి" : "Observed Range"}</th>
                <th>{te ? "ప్రాముఖ్యత" : "Agricultural Role"}</th>
              </tr>
            </thead>

            <tbody>
              {inputFeatures.map(
                ([sym, name, unit, range, role]) => (
                  <tr key={sym}>
                    <td>
                      <code className="feature-code">
                        {sym}
                      </code>
                    </td>

                    <td>
                      <strong>{name}</strong>
                    </td>

                    <td>{unit}</td>

                    <td>
                      <span className="range-badge">
                        {range}
                      </span>
                    </td>

                    <td>{role}</td>
                  </tr>
                )
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* RELIABILITY POLICY */}
      <section className="about-policy-section">
        <div className="about-section-header">
          <span className="about-eyebrow">
            {te ? "విశ్వసనీయత తనిఖీలు" : "RELIABILITY SAFEGUARDS"}
          </span>

          <h2>
            {te
              ? "మూడు స్థాయిల ఇన్‌పుట్ విశ్వసనీయత వ్యవస్థ"
              : "Three-Level Input Reliability System"}
          </h2>

          <p>
            {te
              ? "సరైన పంట సిఫార్సులను అందించడానికి సిస్టమ్ ఇన్‌పుట్ విలువలను తనిఖీ చేస్తుంది."
              : "The system checks the supplied input values and classifies them into three reliability levels to reduce misleading recommendations."}
          </p>
        </div>

        <div className="about-policy-cards">
          <div className="about-policy-card level1">
            <div className="policy-badge">
              Level 1: Normal Inputs
            </div>

            <h3>Normal Recommendation</h3>

            <p>
              Input values are within the expected reference
              distribution. The system displays the crop
              recommendation and alternative crop predictions.
            </p>
          </div>

          <div className="about-policy-card level2">
            <div className="policy-badge">
              Level 2: Unusual Inputs
            </div>

            <h3>Prediction with Warning</h3>

            <p>
              Some input values or combinations are unusual.
              The system displays the prediction with
              appropriate warnings so users can interpret
              the result cautiously.
            </p>
          </div>

          <div className="about-policy-card level3">
            <div className="policy-badge">
              Level 3: Invalid Inputs
            </div>

            <h3>Recommendation Withheld</h3>

            <p>
              Input values contain severe anomalies or invalid
              conditions. The system withholds the crop
              recommendation to avoid providing misleading
              results.
            </p>
          </div>
        </div>
      </section>

      {/* RESPONSIBLE USE */}
      <section className="about-responsible-box">
        <span className="about-eyebrow">
          {te ? "బాధ్యతాయుత వినియోగం" : "RESPONSIBLE USE"}
        </span>

        <h2>
          {te
            ? "ముఖ్యమైన సమాచారం"
            : "Project Limitations & Responsible Use"}
        </h2>

        <p>
          <strong>1. Dataset:</strong>{" "}
          The system uses a curated dataset containing
          2,200 records across 22 crop classes. Its performance
          on this dataset does not guarantee identical results
          for every real-world agricultural condition.
        </p>

        <p>
          <strong>2. Crop Suitability:</strong>{" "}
          The recommendations are based on the soil and climate
          parameters supplied to the machine learning model.
          They should be considered decision-support suggestions.
        </p>

        <p>
          <strong>3. Agricultural Guidance:</strong>{" "}
          This prototype does not replace professional soil
          testing, agricultural experts, or local farming advice.
        </p>
      </section>
    </main>
  );
}
