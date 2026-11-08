import { useState } from "react";
import "./Auth.css";

	import API_URL from "./api";
export default function Auth({ onLogin }) {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");

    const cleanEmail = email.trim().toLowerCase();
    if (!cleanEmail || !cleanEmail.includes("@")) {
      setError("Please enter a valid email address.");
      return;
    }

    if (mode === "register" && password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }

    setLoading(true);

    try {
      const credentials = { email: cleanEmail, password };
      const endpoint = mode === "login" ? "/auth/login" : "/auth/register";

      const response = await fetch(`${API_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(credentials),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Authentication failed. Please verify your details and try again."
        );
      }

      let loginData = data;

      // After successful registration, automatically log in
      if (mode === "register") {
        const loginResponse = await fetch(`${API_URL}/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(credentials),
        });

        loginData = await loginResponse.json();

        if (!loginResponse.ok) {
          throw new Error(
            typeof loginData.detail === "string"
              ? loginData.detail
              : "Account created, but automatic sign-in failed. Please sign in manually."
          );
        }
      }

      if (!loginData.access_token || !loginData.user) {
        throw new Error("Server returned an invalid authentication response.");
      }

      localStorage.setItem("agrisense_token", loginData.access_token);
      onLogin(loginData.user);
    } catch (err) {
      setError(err.message || "An unexpected error occurred. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-page">
      <div className="auth-glow auth-glow-one" aria-hidden="true" />
      <div className="auth-glow auth-glow-two" aria-hidden="true" />

      <section className="auth-card" aria-labelledby="auth-title">
        <div className="auth-heading">
          <h1 id="auth-title">
            {mode === "login" ? (
              <>Welcome <span>back.</span></>
            ) : (
              <>Start with <span>AgriSmart.</span></>
            )}
          </h1>
          <p>
            {mode === "login"
              ? "Sign in to access AI crop recommendations, SHAP explanations, and regional insights."
              : "Create an account to explore explainable crop decision support."}
          </p>
        </div>

        <div className="auth-tabs" role="tablist" aria-label="Authentication Options">
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
            Sign In
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
            Create Account
          </button>
        </div>

        <form onSubmit={handleSubmit} className="auth-form" noValidate>
          <div className="auth-field">
            <label htmlFor="auth-email">Email Address</label>
            <input
              id="auth-email"
              type="email"
              placeholder="you@example.com"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="auth-field">
            <div className="auth-field-header">
              <label htmlFor="auth-password">Password</label>
              {mode === "register" && (
                <span className="auth-hint">Min. 8 characters</span>
              )}
            </div>
            <input
              id="auth-password"
              type="password"
              placeholder={mode === "register" ? "Create a strong password" : "Enter your password"}
              autoComplete={mode === "login" ? "current-password" : "new-password"}
              minLength={mode === "register" ? 8 : 1}
              maxLength={128}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          {error && (
            <div className="auth-error" role="alert">
              <span className="auth-error-icon">⚠️</span>
              <span>{error}</span>
            </div>
          )}

          <button className="auth-submit" type="submit" disabled={loading}>
            {loading ? (
              <span className="auth-spinner-wrap">
                <span className="auth-mini-spinner" /> Signing in...
              </span>
            ) : mode === "login" ? (
              "Sign In to AgriSmart →"
            ) : (
              "Create My Account →"
            )}
          </button>
        </form>

        <div className="auth-security">
          <span className="security-icon">🔒</span>
          Argon2 password hashing · Stateless JWT authentication
        </div>

        <p className="auth-footer">
          Educational decision support prototype · Secure access
        </p>
      </section>

      <aside className="auth-side" aria-label="Platform Highlights">
        <span className="auth-side-label">EXPLAINABLE AI · TABPFN CLASSIFIER</span>
        <h2>
          Smarter field decisions.
          <br />
          <span>Transparent predictions.</span>
        </h2>

        <div className="auth-feature-list">
          <div className="auth-feature">
            <span className="feature-num">01</span>
            <div>
              <strong>TabPFN Multi-Crop Classification</strong>
              <p>Evaluates soil N-P-K, pH, temperature, humidity, and rainfall.</p>
            </div>
          </div>

          <div className="auth-feature">
            <span className="feature-num">02</span>
            <div>
              <strong>Three-Level Reliability Safeguards</strong>
              <p>Distinguishes familiar distributions from unusual combinations and severe outliers.</p>
            </div>
          </div>

          <div className="auth-feature">
            <span className="feature-num">03</span>
            <div>
              <strong>SHAP Feature Explainability</strong>
              <p>Inspects positive and negative contributions driving each crop recommendation.</p>
            </div>
          </div>
        </div>

        <div className="auth-disclaimer-box">
          <strong>Decision-Support Notice</strong>
          <p>
            Model predictions and historical production statistics provide complementary
            regional perspective, not guarantees of crop suitability or yield.
          </p>
        </div>
      </aside>
    </main>
  );
}
