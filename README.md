# 🌱 AgriSense – Explainable AI-Based Agricultural Decision Support System

AgriSense is an AI-powered agricultural decision support system designed to help farmers identify potentially suitable crops based on soil and climatic conditions. It combines machine learning, Explainable AI (XAI), input reliability assessment, historical agricultural insights, and an AI-powered chatbot to provide transparent and informative crop recommendations.

The system uses **TabPFN** for crop classification and **SHAP** for explaining model predictions. It provides the top three predicted crop options along with their prediction scores, helping users compare possible choices.

---

## 📌 Key Features

### 1. AI-Based Crop Recommendation
- Uses the TabPFN machine learning model for crop classification.
- Accepts seven agricultural parameters:
  - Nitrogen (N)
  - Phosphorus (P)
  - Potassium (K)
  - Temperature
  - Humidity
  - Soil pH
  - Rainfall
- Displays the top three predicted crops with their prediction scores.

### 2. Explainable AI Using SHAP
- Explains the contribution of individual input features to a prediction.
- Identifies which soil and climatic parameters influence the model's output.
- Improves transparency and interpretability of crop recommendations.

### 3. Input Reliability Assessment
Evaluates the entered agricultural parameters and categorizes inputs into three reliability levels:

- **Level 1 – Normal:** Inputs are within the expected reference distribution.
- **Level 2 – Unusual:** Inputs contain unusual values and require caution.
- **Level 3 – Severe/Invalid:** Inputs are invalid or outside acceptable limits; recommendations may be withheld.

### 4. Historical Agricultural Insights
- Provides historical crop production information.
- Supports filtering by state, district, season, and crop.
- Displays crop production rankings and historical trends.
- Helps users explore regional agricultural information.

### 5. AgriAssist – AI Agricultural Chatbot
- Provides an interactive agricultural question-answering interface.
- Uses the Gemini API to generate responses.
- Supports questions related to crops, soil conditions, and agricultural practices.
- Can provide historical agricultural context when relevant data is available.

### 6. User Authentication
- Provides registration and login functionality.
- Uses MySQL for user data storage.

### 7. User-Friendly Interface
- Developed with React and Vite.
- Provides an interactive interface for entering agricultural parameters and viewing results.
- Includes crop recommendations, explanations, historical insights, and chatbot functionality.

---

## 🏗️ System Architecture

AgriSense follows a client-server architecture.

```text
              USER
                |
                v
        REACT FRONTEND
           (Vite)
                |
                v
        FASTAPI BACKEND
                |
       +--------+---------+
       |        |         |
       v        v         v
    TabPFN     SHAP     MySQL
     Model   Explainability Authentication
       |
       v
  Top 3 Crop Predictions
       |
       v
  Reliability Assessment

       FASTAPI BACKEND
                |
       +--------+---------+
       |                  |
       v                  v
 Historical Insights   AgriAssist
       |               Gemini API
       v
 Production Trends
 and Crop Rankings
```

---

## 🧠 Machine Learning Model

**Model:** TabPFN (Tabular Prior-Data Fitted Network)

TabPFN is used as the primary classification model to predict suitable crop categories from the provided soil and climatic parameters.

### Dataset Information

The crop recommendation dataset contains:

| Attribute | Description |
|---|---|
| Nitrogen (N) | Nitrogen content in soil |
| Phosphorus (P) | Phosphorus content in soil |
| Potassium (K) | Potassium content in soil |
| Temperature | Environmental temperature |
| Humidity | Relative humidity |
| pH | Soil pH value |
| Rainfall | Rainfall measurement |
| Label | Crop category |

**Dataset statistics:**
- Total records: 2,200
- Input features: 7
- Target classes: 22
- Training records: 1,760
- Testing records: 440
- Train-test split: 80:20
- Random state: 42

The historical agricultural dataset is maintained separately and is used for historical insights rather than as an input to the TabPFN crop classifier.

### Model Evaluation Results

| Evaluation Metric | Score |
|---|---:|
| Accuracy | 99.32% |
| Macro Precision | 99.37% |
| Macro Recall | 99.32% |
| Macro F1-Score | 99.32% |
| Weighted F1-Score | 99.32% |

The model correctly classified 437 out of 440 test records.

*These results represent evaluation on the selected held-out test dataset and do not guarantee the same performance on unseen real-world agricultural conditions.*

---

## 🛠️ Technologies Used

### Frontend
- React.js
- Vite
- JavaScript / TypeScript
- HTML5
- CSS3

### Backend
- Python
- FastAPI
- Uvicorn
- REST API

### Machine Learning and Explainable AI
- TabPFN
- SHAP
- Pandas
- NumPy
- Scikit-learn

### Database
- MySQL

### Generative AI
- Google Gemini API
- Google Gen AI SDK

### Development Tools
- Visual Studio Code
- Git
- GitHub
- Postman

---

## 📂 Project Structure

```text
AgriSense/
│
├── backend/
│   ├── main.py
│   ├── agri_chatbot.py
│   ├── historical_insights.py
│   ├── requirements.txt
│   ├── .env
│   │
│   ├── models/
│   │   └── tabpfn_crop_model.joblib
│   │
│   ├── data/
│   │   ├── Crop_recommendation.csv
│   │   └── processed/
│   │
│   └── tests/
│       ├── test_api_prediction.py
│       └── test_input_validation.py
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── App.jsx
│   │   └── api.js
│   │
│   ├── public/
│   ├── package.json
│   └── index.html
│
├── evaluation_metrics.json
├── test_predictions.csv
├── .gitignore
└── README.md
```

*The structure above is illustrative. Adjust filenames and folders to match the actual repository.*

---

## ⚙️ Installation and Setup

### Prerequisites

Install the following before running the application:

- Python 3.12
- Node.js and npm
- MySQL Server
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/sattiprasanna0916-prog/AgriSense.git
cd AgriSense
```

Replace the repository URL with your actual GitHub repository URL if the repository name is different.

### 2. Backend Setup

Open a terminal and navigate to the backend directory:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

Install the required packages:

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file inside the backend directory.

Add your configuration using the following placeholders:

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=your_supported_gemini_model

DB_HOST=localhost
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
DB_NAME=agrisense_auth
```

Use the exact environment variable names expected by your backend configuration.

**Security:** Never upload your `.env` file or API keys to GitHub.

### 4. Run the Backend

```bash
uvicorn main:app --reload
```

Backend API:

```text
http://127.0.0.1:8000
```

FastAPI documentation:

```text
http://127.0.0.1:8000/docs
```

### 5. Frontend Setup

Open another terminal:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

Frontend:

```text
http://localhost:5173
```

---

## 🔄 Application Workflow

1. The user opens the AgriSense application.
2. The user registers or logs in.
3. The user enters soil nutrient values and climatic parameters.
4. The backend validates the submitted inputs.
5. The reliability assessment evaluates the input values.
6. The TabPFN model predicts the top three crop categories.
7. SHAP explains the contribution of input features to the prediction.
8. Historical agricultural insights provide regional crop production information.
9. AgriAssist answers agricultural questions using the Gemini API.

---

## 🎯 Applications

- Agricultural decision support.
- Soil and climate-based crop selection.
- Understanding the influence of soil parameters on crop predictions.
- Exploring historical agricultural production trends.
- Accessing AI-assisted agricultural information.

---

## ⚠️ Limitations

- Recommendations depend on the training dataset and its coverage.
- The current crop classifier does not directly use location or season as model input features.
- Historical production insights are provided separately from crop classification.
- Prediction scores are not guaranteed probabilities of successful cultivation.
- The system does not currently guarantee crop yield, market profitability, or pest and disease risk.
- SHAP explanations and Gemini responses may require additional processing time or depend on external service availability.
- The system is intended for decision support and does not replace professional agricultural advice or laboratory soil testing.

---

## 🚀 Future Enhancements

- Integrate larger and more geographically diverse agricultural datasets.
- Incorporate location-specific weather and environmental information.
- Improve SHAP explanation performance.
- Add crop yield and profitability estimation.
- Integrate real-time weather information.
- Improve chatbot response reliability.
- Develop a mobile-friendly application.
- Deploy the complete system to a production environment.

---

## 👩‍💻 Author

**Satti Prasanna Lakshmi**

B.Tech – Artificial Intelligence and Machine Learning

GitHub: [sattiprasanna0916-prog](https://github.com/sattiprasanna0916-prog)

---

## 📄 License

This project is developed for academic and educational purposes. Add an appropriate open-source license if you intend to distribute the source code publicly.

---

**AgriSense – Making Agricultural Decisions More Explainable and Data-Driven.** 🌱