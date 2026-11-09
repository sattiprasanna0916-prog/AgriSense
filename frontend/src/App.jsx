import { useEffect, useState } from "react";
import {
  Routes,
  Route,
  NavLink,
  Navigate,
  useLocation,
} from "react-router-dom";

import AgriAssist from "./pages/AgriAssist";
import Auth from "./Auth";
import Home from "./pages/Home";
import Prediction from "./pages/Prediction";
import About from "./pages/About";
import HistoricalInsights from "./pages/HistoricalInsights";
import ThemeLanguageControls from "./components/ThemeLanguageControls";
import { useLanguage } from "./context/LanguageContext";
import API_URL from "./api";
import "./App.css";

const navigationItems = [
  { to: "/", labelKey: "navDashboard", icon: "▦", end: true },
  { to: "/prediction", labelKey: "navPrediction", icon: "❖" },
  { to: "/historical", labelKey: "navHistorical", icon: "◷" },
  { to: "/agriassist", labelKey: "navAgriAssist", icon: "♧" },
  { to: "/about", labelKey: "navAbout", icon: "ⓘ" },
];

function App() {
  const [user, setUser] = useState(null);
  const [authChecking, setAuthChecking] = useState(true);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  const { t } = useLanguage();
  const location = useLocation();

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
      .then(setUser)
      .catch(() => {
        localStorage.removeItem("agrisense_token");
        setUser(null);
      })
      .finally(() => setAuthChecking(false));
  }, []);

  useEffect(() => {
    setMobileNavOpen(false);
  }, [location.pathname]);

  function handleLogout() {
    localStorage.removeItem("agrisense_token");
    setUser(null);
  }

  if (authChecking) {
    return (
      <div className="auth-loading">
        <div className="auth-loading-spinner" />
        <p>{t("connecting")}</p>
      </div>
    );
  }

  if (!user) {
    return <Auth onLogin={setUser} />;
  }

  const displayName =
    user?.name ||
    user?.full_name ||
    user?.email?.split("@")[0] ||
    "Farmer";

  const firstName = displayName.split(" ")[0];

  return (
    <div className="app-shell">
      {mobileNavOpen && (
        <button
          className="sidebar-backdrop"
          aria-label="Close navigation"
          onClick={() => setMobileNavOpen(false)}
        />
      )}

      <aside
        className={`app-sidebar ${mobileNavOpen ? "sidebar-open" : ""}`}
      >
        <NavLink
          to="/"
          className="sidebar-brand"
          aria-label="AgriSmart dashboard"
        >
          <span className="brand-mark">🌱</span>

          <span className="brand-copy">
            <strong>{t("brandName")}</strong>
            <small>{t("brandSubtitle")}</small>
          </span>
        </NavLink>

        <nav className="sidebar-navigation" aria-label="Main navigation">
          {navigationItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `sidebar-link ${isActive ? "active" : ""}`
              }
            >
              <span className="sidebar-icon" aria-hidden="true">
                {item.icon}
              </span>
              <span>{t(item.labelKey)}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <span className="sidebar-avatar">🌿</span>

          <span className="sidebar-farmer-copy">
            <strong>{t("farmerDashboard")}</strong>
            <small>{t("smartAgriculture")}</small>
          </span>
        </div>
      </aside>

      <div className="app-main-column">
        <header className="app-topbar">
          <button
            className="mobile-menu-button"
            onClick={() => setMobileNavOpen((value) => !value)}
            aria-label="Toggle navigation"
          >
            ☰
          </button>

          <div className="topbar-welcome">
            <strong>{t("welcomeBack")}, {firstName}!</strong>
            <span>
              {t("topbarSub")}
            </span>
          </div>

          <div className="topbar-actions">
            <ThemeLanguageControls />

            <div className="topbar-user-avatar" title={displayName}>
              {displayName.charAt(0).toUpperCase()}
            </div>

            <button
              className="topbar-logout"
              type="button"
              onClick={handleLogout}
            >
              {t("logout")}
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
      </div>
    </div>
  );
}

export default App;
