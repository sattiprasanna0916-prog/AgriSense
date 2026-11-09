import { useTheme } from "../context/ThemeContext";
import { useLanguage } from "../context/LanguageContext";

export default function ThemeLanguageControls({ className = "" }) {
  const { theme, toggleTheme } = useTheme();
  const { lang, toggleLanguage, t } = useLanguage();

  return (
    <div className={`header-controls ${className}`}>
      <button
        type="button"
        className="lang-toggle-btn"
        onClick={toggleLanguage}
        title={lang === "en" ? "Switch to Telugu (తెలుగు)" : "Switch to English"}
        aria-label="Toggle language between English and Telugu"
      >
        <span className="lang-badge">{lang === "en" ? "EN" : "తె"}</span>
        <span>{lang === "en" ? "తెలుగు" : "English"}</span>
      </button>

      <button
        type="button"
        className="theme-toggle-btn"
        onClick={toggleTheme}
        title={theme === "light" ? "Switch to Dark Mode" : "Switch to Light Mode"}
        aria-label="Toggle light and dark mode"
      >
        <span>{theme === "light" ? "🌙" : "☀️"}</span>
        <span>{theme === "light" ? (lang === "te" ? "డార్క్" : "Dark") : (lang === "te" ? "లైట్" : "Light")}</span>
      </button>
    </div>
  );
}

