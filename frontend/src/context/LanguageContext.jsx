import { createContext, useContext, useState, useEffect } from "react";
import translations from "../i18n/translations";

const LanguageContext = createContext();

export function LanguageProvider({ children }) {
  const [lang, setLang] = useState(() => {
    return localStorage.getItem("agrisense_language") || "en";
  });

  useEffect(() => {
    localStorage.setItem("agrisense_language", lang);
    document.documentElement.lang = lang;
  }, [lang]);

  const toggleLanguage = () => {
    setLang((prev) => (prev === "en" ? "te" : "en"));
  };

  const t = (key, fallback = "") => {
    return translations[lang]?.[key] || translations["en"]?.[key] || fallback || key;
  };

  return (
    <LanguageContext.Provider value={{ lang, setLang, toggleLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error("useLanguage must be used within a LanguageProvider");
  }
  return context;
}

