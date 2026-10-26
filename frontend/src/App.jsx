import { useEffect, useState } from "react";
import { Routes, Route, NavLink, Navigate } from "react-router-dom";
import AgriAssist from "./pages/AgriAssist";
import Auth from "./Auth";
import Home from "./pages/Home";
import Prediction from "./pages/Prediction";
import About from "./pages/About";
import HistoricalInsights from "./pages/HistoricalInsights";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [user, setUser] = useState(null);
  const [authChecking, setAuthChecking] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("agrisense_token");

    if (!token) {
      setAuthChecking(false);
      return;
    }

    fetch(`${API_URL}/auth/me`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error("Session expired");
        }
        return response.json();
      })
      .then((data) => setUser(data))
      .catch(() => {
        localStorage.removeItem("agrisense_token");
        setUser(null);
      })
      .finally(() => setAuthChecking(false));
  }, []);

  function handleLogout() {
    localStorage.removeItem("agrisense_token");
    setUser(null);
  }

  if (authChecking) {
    return (
      <div className="auth-loading">
        <div className="auth-loading-spinner" />
        <p>Connecting to AgriSense...</p>
      </div>
    );
  }

  if (!user) {
    return <Auth onLogin={setUser} />;
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="topbar-left">
          <NavLink className="brand" to="/" aria-label="AgriSense Home">
            
          </NavLink>
          <span className="model-badge" title="Trained TabPFN foundation classifier">
            TabPFN · Explainable AI
          </span>
        </div>

        <nav className="main-navigation" aria-label="Main Navigation">
          <NavLink to="/" end>
            Home
          </NavLink>
          <NavLink to="/prediction">
            Crop Prediction
          </NavLink>
          <NavLink to="/historical">
            Historical Insights
          </NavLink>
          <NavLink to="/agriassist">
            AgriAssist
          </NavLink>
          <NavLink to="/about">
            About
          </NavLink>
        </nav>

        <div className="topbar-user">
          <span className="user-email" title={user.email}>
            <span className="user-dot" />
            {user.email.split("@")[0]}
          </span>
          <button
            className="secondary-button logout-btn"
            type="button"
            onClick={handleLogout}
          >
            Log out
          </button>
        </div>
      </header>

      <main className="page-content">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/prediction" element={<Prediction />} />
          <Route path="/historical" element={<HistoricalInsights />} />
          <Route path="/agriassist" element={<AgriAssist />} />
          <Route path="/about" element={<About />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>

      <footer className="app-footer">
        <div className="footer-content">
          <div className="footer-brand">
            <NavLink className="brand" to="/">
              
            </NavLink>
            <p>
              Explainable AI-based agricultural decision support system using TabPFN,
              SHAP feature attribution, and regional production insights.
            </p>
          </div>

          <div className="footer-links">
            <NavLink to="/">Home</NavLink>
            <NavLink to="/prediction">Prediction</NavLink>
            <NavLink to="/historical">Historical Insights</NavLink>
            <NavLink to="/agriassist">AgriAssist</NavLink>
            <NavLink to="/about">Methodology</NavLink>
          </div>
        </div>

        <div className="footer-bottom">
          <span>
            Academic prototype for educational decision support · Model probabilities do not guarantee crop yield
          </span>
          <span className="footer-version">v1.2.0 · 2026</span>
        </div>
      </footer>
    </div>
  );
}

export default App;
