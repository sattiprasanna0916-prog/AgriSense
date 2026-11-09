
import { useState } from "react";
import ThemeLanguageControls from "./components/ThemeLanguageControls";
import { useLanguage } from "./context/LanguageContext";
import API_URL from "./api";
import "./Auth.css";

export default function Auth({ onLogin }) {
  const [mode, setMode] = useState("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const { t, lang } = useLanguage();

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");

    const cleanEmail = email.trim().toLowerCase();

    if (!cleanEmail || !cleanEmail.includes("@")) {
      setError(
        lang === "te"
          ? "దయచేసి సరైన ఈమెయిల్ చిరునామాను నమోదు చేయండి."
          : "Please enter a valid email address."
      );
      return;
    }

    if (mode === "register" && !name.trim()) {
      setError(
        lang === "te"
          ? "దయచేసి మీ పేరును నమోదు చేయండి."
          : "Please enter your name."
      );
      return;
    }

    if (mode === "register" && password.length < 8) {
      setError(
        lang === "te"
          ? "పాస్‌వర్డ్ కనీసం 8 అక్షరాలు ఉండాలి."
          : "Password must be at least 8 characters long."
      );
      return;
    }

    if (mode === "register" && password !== confirmPassword) {
      setError(
        lang === "te"
          ? "పాస్‌వర్డ్‌లు సరిపోలడం లేదు."
          : "Passwords do not match."
      );
      return;
    }

    setLoading(true);

    try {
      const credentials =
        mode === "register"
          ? {
              name: name.trim(),
              email: cleanEmail,
              password,
            }
          : {
              email: cleanEmail,
              password,
            };

      const endpoint =
        mode === "login" ? "/auth/login" : "/auth/register";

      const response = await fetch(`${API_URL}${endpoint}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(credentials),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : lang === "te"
              ? "ధృవీకరణ విఫలమైంది. దయచేసి వివరాలను పరిశీలించి మళ్లీ ప్రయత్నించండి."
              : "Authentication failed. Please verify your details and try again."
        );
      }

      let loginData = data;

      // Automatically log in after successful registration
      if (mode === "register") {
        const loginResponse = await fetch(`${API_URL}/auth/login`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            email: cleanEmail,
            password,
          }),
        });

        loginData = await loginResponse.json();

        if (!loginResponse.ok) {
          throw new Error(
            typeof loginData.detail === "string"
              ? loginData.detail
              : lang === "te"
                ? "ఖాతా సృష్టించబడింది, కానీ ఆటోమేటిక్ సైన్-ఇన్ విఫలమైంది. దయచేసి మాన్యువల్‌గా లాగిన్ అవ్వండి."
                : "Account created, but automatic sign-in failed. Please sign in manually."
          );
        }
      }

      if (!loginData.access_token || !loginData.user) {
        throw new Error(
          lang === "te"
            ? "సర్వర్ నుండి సరైన సమాధానం రాలేదు."
            : "Server returned an invalid authentication response."
        );
      }

      localStorage.setItem(
        "agrisense_token",
        loginData.access_token
      );

      onLogin(loginData.user);

    } catch (err) {
      setError(
        err.message ||
          (lang === "te"
            ? "ఊహించని లోపం ఏర్పడింది. దయచేసి మళ్లీ ప్రయత్నించండి."
            : "An unexpected error occurred. Please try again.")
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-page">
      <div className="auth-glow auth-glow-one" aria-hidden="true" />
      <div className="auth-glow auth-glow-two" aria-hidden="true" />

      <section className="auth-card" aria-labelledby="auth-title">

        <div
          style={{
            display: "flex",
            justifyContent: "flex-end",
            marginBottom: 16,
          }}
        >
          <ThemeLanguageControls />
        </div>

        <div className="auth-heading">
          <h1 id="auth-title">
            {mode === "login" ? (
              <>
                {lang === "te" ? "తిరిగి " : "Welcome "}
                <span>
                  {lang === "te" ? "స్వాగతం." : "back."}
                </span>
              </>
            ) : (
              <>
                {lang === "te" ? "స్వాగతం " : "Start with "}
                <span>{t("brandName")}.</span>
              </>
            )}
          </h1>

          <p>
            {mode === "login"
              ? t("authSubtitle")
              : lang === "te"
                ? "ఎక్స్‌ప్లెయినబుల్ పంట నిర్ణయ మద్దతు వ్యవస్థను ఉపయోగించడానికి ఖాతాను సృష్టించుకోండి."
                : "Create an account to explore explainable crop decision support."}
          </p>
        </div>

        <div
          className="auth-tabs"
          role="tablist"
          aria-label="Authentication Options"
        >
          <button
            type="button"
            role="tab"
            aria-selected={mode === "login"}
            className={mode === "login" ? "active" : ""}
            onClick={() => {
              setMode("login");
              setError("");
            }}
          >
            {t("authTabLogin")}
          </button>

          <button
            type="button"
            role="tab"
            aria-selected={mode === "register"}
            className={mode === "register" ? "active" : ""}
            onClick={() => {
              setMode("register");
              setError("");
            }}
          >
            {t("authTabRegister")}
          </button>
        </div>

        <form
          onSubmit={handleSubmit}
          className="auth-form"
          noValidate
        >

          {/* Full Name - Registration Only */}
          {mode === "register" && (
            <div className="auth-field">
              <label htmlFor="auth-name">
                {lang === "te" ? "పూర్తి పేరు" : "Full Name"}
              </label>

              <input
                id="auth-name"
                type="text"
                placeholder={
                  lang === "te"
                    ? "మీ పేరును నమోదు చేయండి"
                    : "Enter your full name"
                }
                autoComplete="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                maxLength={100}
                required
              />
            </div>
          )}

          {/* Email */}
          <div className="auth-field">
            <label htmlFor="auth-email">
              {t("authEmail")}
            </label>

            <input
              id="auth-email"
              type="email"
              placeholder={t("authEmailPlaceholder")}
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          {/* Password */}
          <div className="auth-field">
            <div className="auth-field-header">
              <label htmlFor="auth-password">
                {t("authPassword")}
              </label>

              {mode === "register" && (
                <span className="auth-hint">
                  {t("authPasswordMin")}
                </span>
              )}
            </div>

            <input
              id="auth-password"
              type="password"
              placeholder={
                mode === "register"
                  ? lang === "te"
                    ? "బలమైన పాస్‌వర్డ్ ఇవ్వండి"
                    : "Create a strong password"
                  : t("authPasswordPlaceholder")
              }
              autoComplete={
                mode === "login"
                  ? "current-password"
                  : "new-password"
              }
              minLength={mode === "register" ? 8 : 1}
              maxLength={128}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          {/* Confirm Password - Registration Only */}
          {mode === "register" && (
            <div className="auth-field">
              <label htmlFor="auth-confirm-password">
                {lang === "te"
                  ? "పాస్‌వర్డ్ నిర్ధారించండి"
                  : "Confirm Password"}
              </label>

              <input
                id="auth-confirm-password"
                type="password"
                placeholder={
                  lang === "te"
                    ? "పాస్‌వర్డ్‌ను మళ్లీ నమోదు చేయండి"
                    : "Re-enter your password"
                }
                autoComplete="new-password"
                maxLength={128}
                value={confirmPassword}
                onChange={(e) =>
                  setConfirmPassword(e.target.value)
                }
                required
              />
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="auth-error" role="alert">
              <span className="auth-error-icon">⚠️</span>
              <span>{error}</span>
            </div>
          )}

          {/* Submit Button */}
          <button
            className="auth-submit"
            type="submit"
            disabled={loading}
          >
            {loading ? (
              <span className="auth-spinner-wrap">
                <span className="auth-mini-spinner" />
                {t("loading")}
              </span>
            ) : mode === "login" ? (
              `${t("authLoginBtn")} →`
            ) : (
              `${t("authRegisterBtn")} →`
            )}
          </button>
        </form>

        <div className="auth-security">
          {t("authSecurityNotice")}
        </div>

        <p className="auth-footer">
          {lang === "te"
            ? "విద్యా మరియు నిర్ణయ మద్దతు వ్యవస్థ · సురక్షిత యాక్సెస్"
            : "Educational decision support prototype · Secure access"}
        </p>
      </section>

      {/* Right Side Platform Highlights */}
      <aside className="auth-side" aria-label="Platform Highlights">

        <span className="auth-side-label">
          {t("authSideBadge")}
        </span>

        <h2>
          {lang === "te"
            ? "ఖచ్చితమైన వ్యవసాయ నిర్ణయాలు."
            : "Smarter field decisions."}

          <br />

          <span>
            {lang === "te"
              ? "పారదర్శకమైన అంచనాలు."
              : "Transparent predictions."}
          </span>
        </h2>

        <div className="auth-feature-list">

          <div className="auth-feature">
            <span className="feature-num">01</span>
            <div>
              <strong>{t("authFeature1Title")}</strong>
              <p>{t("authFeature1Desc")}</p>
            </div>
          </div>

          <div className="auth-feature">
            <span className="feature-num">02</span>
            <div>
              <strong>{t("authFeature3Title")}</strong>
              <p>{t("authFeature3Desc")}</p>
            </div>
          </div>

          <div className="auth-feature">
            <span className="feature-num">03</span>
            <div>
              <strong>{t("authFeature2Title")}</strong>
              <p>{t("authFeature2Desc")}</p>
            </div>
          </div>

        </div>

        <div className="auth-disclaimer-box">
          <strong>{t("authDisclaimerTitle")}</strong>
          <p>{t("authDisclaimerDesc")}</p>
        </div>

      </aside>
    </main>
  );
}
