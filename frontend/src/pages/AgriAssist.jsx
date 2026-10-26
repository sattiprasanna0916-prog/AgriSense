import { useState, useRef, useEffect } from "react";
import "./AgriAssist.css";

const API_URL = "http://127.0.0.1:8000";

const initialMessage = {
  role: "assistant",
  content:
    "Hello! I'm AgriAssist 🌱. I can help answer agronomic questions about soil health, fertilizers, irrigation, crop seasons, or retrieve verified district crop production history (1997–2014). What would you like to explore?",
  source: "agrisense_assistant",
};

export default function AgriAssist() {
  const [messages, setMessages] = useState([initialMessage]);
  const [message, setMessage] = useState("");
  const [stateName, setStateName] = useState("Andhra Pradesh");
  const [district, setDistrict] = useState("ANANTAPUR");
  const [season, setSeason] = useState("Kharif");
  const [crop, setCrop] = useState("Groundnut");
  const [loading, setLoading] = useState(false);
  const [lastFailedMessage, setLastFailedMessage] = useState(null);

  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function sendMessage(questionText) {
    const question = (questionText || message).trim();
    if (!question || loading) return;

    const conversationHistory = messages
      .filter((item) => item.role === "user" || item.role === "assistant")
      .slice(-10)
      .map((item) => ({
        role: item.role,
        content: item.content,
      }));

    setMessages((prev) => [
      ...prev,
      { role: "user", content: question },
    ]);
    setMessage("");
    setLoading(true);
    setLastFailedMessage(null);

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: question,
          state: stateName.trim(),
          district: district.trim(),
          season,
          crop: crop.trim(),
          history: conversationHistory,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          typeof errorData.detail === "string"
            ? errorData.detail
            : "The chatbot encountered an error while processing your question."
        );
      }

      const data = await response.json();

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.reply,
          source: data.source,
        },
      ]);
    } catch (error) {
      setLastFailedMessage(question);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: error.message?.includes("Failed to fetch")
            ? "I couldn't connect to the AgriAssist backend. Please ensure the FastAPI server is running on http://127.0.0.1:8000."
            : `Assistance Notice: ${error.message || "An unexpected error occurred."}`,
          isError: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleFormSubmit(e) {
    e.preventDefault();
    sendMessage();
  }

  return (
    <section className="agriassist-page">
      <header className="agriassist-heading">
        <span className="section-eyebrow">CONVERSATIONAL AGRICULTURAL ADVISORY</span>
        <h1>AgriAssist</h1>
        <p>
          Ask questions about soil management, seasonal planning, crop practices,
          or query historical district production trends.
        </p>
      </header>

      <div className="agriassist-layout">
        {/* Left Side: Context & Suggestions */}
        <aside className="agriassist-context-panel">
          <div className="context-card-header">
            <h3>Regional Query Context</h3>
            <span className="context-badge">Grounding Data</span>
          </div>
          <p className="context-card-desc">
            These parameters are used to retrieve verified district production records
            when your question pertains to regional trends or crop history.
          </p>

          <div className="context-inputs-column">
            <label>
              <span>State</span>
              <input
                value={stateName}
                onChange={(e) => setStateName(e.target.value)}
                placeholder="State name"
              />
            </label>

            <label>
              <span>District</span>
              <input
                value={district}
                onChange={(e) => setDistrict(e.target.value)}
                placeholder="District name"
              />
            </label>

            <label>
              <span>Season</span>
              <select
                value={season}
                onChange={(e) => setSeason(e.target.value)}
              >
                {["Kharif", "Rabi", "Whole Year", "Summer", "Winter", "Autumn"].map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>

            <label>
              <span>Crop (for trend queries)</span>
              <input
                value={crop}
                onChange={(e) => setCrop(e.target.value)}
                placeholder="e.g. Groundnut"
              />
            </label>
          </div>

          <div className="agriassist-prompts-section">
            <h4>Suggested Inquiries</h4>
            {[
              "How can I manage soil nitrogen balance for cereal crops?",
              "What irrigation schedule works best for Kharif season?",
              "Show top historical crops recorded in this district",
              "Show the historical production trend for this crop",
            ].map((prompt, i) => (
              <button
                key={i}
                type="button"
                className="prompt-chip-btn"
                onClick={() => {
                  setMessage(prompt);
                }}
              >
                <span className="prompt-arrow">↳</span> {prompt}
              </button>
            ))}
          </div>
        </aside>

        {/* Right Side: Chat Messenger */}
        <div className="agriassist-chat-card">
          <div className="agriassist-chat-topbar">
            <div className="status-indicator-wrap">
              <span className="agriassist-status-dot" />
              <strong>AgriAssist Online</strong>
            </div>
            <span className="model-tag">Gemini 3.8 Flash + Historical Data</span>
          </div>

          <div className="agriassist-messages-container" aria-live="polite">
            {messages.map((item, index) => {
              const isAssistant = item.role === "assistant";
              return (
                <div
                  className={`chat-message-row ${item.role} ${item.isError ? "error-msg" : ""}`}
                  key={index}
                >
                  <div className="chat-avatar">
                    {isAssistant ? "🌱" : "👤"}
                  </div>

                  <div className="chat-bubble-content">
                    <div className="chat-bubble">
                      {item.content}
                    </div>

                    {item.source && (
                      <span className="chat-source-tag">
                        Source: {item.source === "gemini_with_historical_data"
                          ? "Regional Historical Data Context + Gemini"
                          : item.source === "gemini"
                            ? "General Agronomic Knowledge"
                            : item.source.replaceAll("_", " ")}
                      </span>
                    )}

                    {item.isError && lastFailedMessage && (
                      <button
                        className="retry-chat-btn"
                        type="button"
                        onClick={() => sendMessage(lastFailedMessage)}
                      >
                        🔄 Retry sending question
                      </button>
                    )}
                  </div>
                </div>
              );
            })}

            {loading && (
              <div className="chat-message-row assistant">
                <div className="chat-avatar">🌱</div>
                <div className="chat-bubble-content">
                  <div className="chat-bubble thinking">
                    <span className="typing-dot" />
                    <span className="typing-dot" />
                    <span className="typing-dot" />
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          <form className="agriassist-input-bar" onSubmit={handleFormSubmit}>
            <input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Ask AgriAssist about soil, fertilizers, irrigation, or regional trends..."
              maxLength={1000}
              aria-label="Your agricultural question"
            />
            <button
              type="submit"
              className="chat-send-btn"
              disabled={loading || !message.trim()}
            >
              {loading ? "Thinking..." : "Send →"}
            </button>
          </form>
        </div>
      </div>

      <div className="agriassist-disclaimer-card">
        <strong>Agricultural Guidance Disclaimer:</strong> AgriAssist provides conversational
        educational assistance. Chemical, pesticide, or diagnostic disease recommendations are
        general in nature and must be verified with certified local agronomists or pesticide safety labels before application.
      </div>
    </section>
  );
}
