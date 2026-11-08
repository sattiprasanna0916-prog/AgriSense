
import { useState, useRef, useEffect } from "react";
import "./AgriAssist.css";
import API_URL from "../api";

const initialMessage = {
  role: "assistant",
  content:
    "Hello! I'm AgriAssist 🌱. I can help answer agronomic questions about soil health, fertilizers, irrigation, crop seasons, or retrieve verified district crop production history (1997–2014). What would you like to explore?",
  source: "agrisense_assistant",
};

const suggestedPrompts = [
  {
    icon: "🌱",
    title: "Soil Health",
    question: "How can I manage soil nitrogen balance for cereal crops?",
  },
  {
    icon: "💧",
    title: "Irrigation",
    question: "What irrigation schedule works best for Kharif season?",
  },
  {
    icon: "🌾",
    title: "Crop History",
    question: "Show top historical crops recorded in this district",
  },
  {
    icon: "📊",
    title: "Production Trends",
    question: "Show the historical production trend for this crop",
  },
];

export default function AgriAssist() {
  const [messages, setMessages] = useState([initialMessage]);
  const [message, setMessage] = useState("");
  const [stateName, setStateName] = useState("Andhra Pradesh");
  const [district, setDistrict] = useState("ANANTAPUR");
  const [season, setSeason] = useState("Kharif");
  const [crop, setCrop] = useState("Groundnut");
  const [loading, setLoading] = useState(false);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "end",
    });
  }, [messages, loading]);

  async function sendMessage(questionText, isRetry = false) {
    const question = (questionText || message).trim();

    if (!question || loading) return;

    // Build conversation history before sending the current question.
    let previousMessages = messages.filter(
      (item) =>
        (item.role === "user" || item.role === "assistant") &&
        !item.isError
    );

    // On retry, remove the already displayed failed user question
    // from history because it is being sent again separately.
    if (isRetry) {
      const lastUserIndex = previousMessages
        .map((item) => item.role)
        .lastIndexOf("user");

      if (
        lastUserIndex !== -1 &&
        previousMessages[lastUserIndex].content === question
      ) {
        previousMessages = previousMessages.filter(
          (_, index) => index !== lastUserIndex
        );
      }
    }

    const conversationHistory = previousMessages
      .slice(-10)
      .map((item) => ({
        role: item.role,
        content: item.content,
      }));

    // Add the user message only for a new question.
    if (!isRetry) {
      setMessages((prev) => [
        ...prev,
        { role: "user", content: question },
      ]);
    }

    setMessage("");
    setLoading(true);

    try {
      const baseUrl = API_URL.replace(/\/+$/, "");

      const response = await fetch(`${baseUrl}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: question,
          state: stateName.trim(),
          district: district.trim(),
          season,
          crop: crop.trim(),
          history: conversationHistory,
        }),
      });

      let data = {};

      try {
        data = await response.json();
      } catch {
        throw new Error(
          "The server returned an invalid response. Please try again."
        );
      }

      if (!response.ok) {
        const detail =
          typeof data.detail === "string"
            ? data.detail
            : data.detail?.message ||
              data.message ||
              "The chatbot could not process your question.";

        throw new Error(detail);
      }

      if (!data.reply || typeof data.reply !== "string") {
        throw new Error(
          "AgriAssist received an empty response. Please try again."
        );
      }

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.reply,
          source: data.source || "gemini",
        },
      ]);
    } catch (error) {
      let errorMessage = error.message;

      if (
        error instanceof TypeError &&
        error.message.toLowerCase().includes("fetch")
      ) {
        errorMessage =
          "Unable to connect to the AgriAssist backend. Please check that your FastAPI server is running and the API URL is correct.";
      }

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Assistance Notice: ${
            errorMessage || "An unexpected error occurred."
          }`,
          isError: true,
          retryQuestion: question,
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

  function getSourceLabel(source) {
    if (source === "gemini_with_historical_data") {
      return "Regional Historical Data + Gemini";
    }

    if (source === "gemini") {
      return "General Agronomic Knowledge";
    }

    if (source === "agrisense_assistant") {
      return "AgriAssist";
    }

    return source?.replaceAll("_", " ") || "AgriAssist";
  }

  function clearConversation() {
    if (loading) return;

    setMessages([initialMessage]);
    setMessage("");
    inputRef.current?.focus();
  }

  return (
    <section className="agriassist-page">
      {/* Page Heading */}
      <header className="agriassist-heading">
        <div className="agriassist-heading-content">
          <span className="section-eyebrow">
            <span className="heading-eyebrow-icon">✦</span>
            INTELLIGENT AGRICULTURAL ASSISTANCE
          </span>

          <h1>
            Meet <span>AgriAssist.</span>
          </h1>

          <p>
            Your AI-powered agricultural companion for soil management,
            crop planning, irrigation guidance, and historical production
            insights.
          </p>
        </div>

        <div className="agriassist-heading-icon">
          <span>🌿</span>
        </div>
      </header>

      {/* Main Layout */}
      <div className="agriassist-layout">
        {/* Regional Context Panel */}
        <aside className="agriassist-context-panel">
          <div className="context-card-header">
            <div className="context-heading-icon">⌖</div>

            <div>
              <h3>Regional Context</h3>
              <p>Customize your agricultural region</p>
            </div>
          </div>

          <div className="context-grounding-note">
            <span className="grounding-icon">✓</span>
            <p>
              Regional filters help retrieve relevant historical
              production records for your questions.
            </p>
          </div>

          <div className="context-inputs-column">
            <label>
              <span>State</span>
              <input
                value={stateName}
                onChange={(e) => setStateName(e.target.value)}
                placeholder="Enter state name"
              />
            </label>

            <label>
              <span>District</span>
              <input
                value={district}
                onChange={(e) => setDistrict(e.target.value)}
                placeholder="Enter district name"
              />
            </label>

            <label>
              <span>Growing Season</span>
              <select
                value={season}
                onChange={(e) => setSeason(e.target.value)}
              >
                {[
                  "Kharif",
                  "Rabi",
                  "Whole Year",
                  "Summer",
                  "Winter",
                  "Autumn",
                ].map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>

            <label>
              <span>Crop of Interest</span>
              <input
                value={crop}
                onChange={(e) => setCrop(e.target.value)}
                placeholder="e.g. Groundnut"
              />
            </label>
          </div>

          {/* Suggested Questions */}
          <div className="agriassist-prompts-section">
            <div className="prompts-heading">
              <div>
                <h4>Explore Questions</h4>
                <p>Start with a suggested topic</p>
              </div>
              <span className="prompts-count">04</span>
            </div>

            <div className="prompt-list">
              {suggestedPrompts.map((prompt) => (
                <button
                  key={prompt.title}
                  type="button"
                  className="prompt-chip-btn"
                  disabled={loading}
                  onClick={() => setMessage(prompt.question)}
                >
                  <span className="prompt-icon">{prompt.icon}</span>

                  <span className="prompt-text">
                    <strong>{prompt.title}</strong>
                    <small>{prompt.question}</small>
                  </span>

                  <span className="prompt-arrow">↗</span>
                </button>
              ))}
            </div>
          </div>

          <div className="context-history-note">
            <span>📚</span>
            <div>
              <strong>Historical Data Available</strong>
              <p>District crop production records from 1997–2014.</p>
            </div>
          </div>
        </aside>

        {/* Chat Interface */}
        <div className="agriassist-chat-card">
          {/* Chat Header */}
          <div className="agriassist-chat-topbar">
            <div className="chat-profile">
              <div className="chat-profile-avatar">🌱</div>

              <div className="chat-profile-info">
                <strong>AgriAssist</strong>
                <span>
                  <i className="agriassist-status-dot" />
                  AI Agricultural Assistant
                </span>
              </div>
            </div>

            <div className="chat-model-info">
              <span className="model-status-icon">✦</span>
              Gemini AI
            </div>

            <button
              type="button"
              className="clear-chat-btn"
              onClick={clearConversation}
              disabled={loading}
              title="Clear conversation"
              aria-label="Clear conversation"
            >
              Clear Chat
            </button>
          </div>

          {/* Chat Messages */}
          <div
            className="agriassist-messages-container"
            aria-live="polite"
            aria-busy={loading}
          >
            <div className="chat-date-label">
              <span>YOUR AGRICULTURAL ASSISTANT</span>
            </div>

            {messages.map((item, index) => {
              const isAssistant = item.role === "assistant";

              return (
                <div
                  className={`chat-message-row ${item.role} ${
                    item.isError ? "error-msg" : ""
                  }`}
                  key={index}
                >
                  <div className="chat-avatar">
                    {isAssistant ? "🌱" : "👤"}
                  </div>

                  <div className="chat-bubble-content">
                    <div className="chat-message-name">
                      {isAssistant ? "AgriAssist" : "You"}
                    </div>

                    <div className="chat-bubble">
                      {item.content}
                    </div>

                    {item.source && (
                      <span className="chat-source-tag">
                        <span>✦</span>
                        {getSourceLabel(item.source)}
                      </span>
                    )}

                    {item.isError && item.retryQuestion && (
                      <button
                        className="retry-chat-btn"
                        type="button"
                        disabled={loading}
                        onClick={() =>
                          sendMessage(item.retryQuestion, true)
                        }
                      >
                        ↻ Retry sending question
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
                  <div className="chat-message-name">
                    AgriAssist is thinking
                  </div>

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

          {/* Message Input */}
          <form
            className="agriassist-input-bar"
            onSubmit={handleFormSubmit}
          >
            <div className="chat-input-wrapper">
              <span className="chat-input-icon">✎</span>

              <input
                ref={inputRef}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Ask anything about agriculture..."
                maxLength={1000}
                aria-label="Your agricultural question"
                disabled={loading}
              />
            </div>

            <button
              type="submit"
              className="chat-send-btn"
              disabled={loading || !message.trim()}
            >
              {loading ? (
                "Thinking..."
              ) : (
                <>
                  Send <span>➤</span>
                </>
              )}
            </button>
          </form>

          <div className="chat-input-footer">
            <span>✦ Powered by Gemini AI</span>
            <span>Maximum 1000 characters</span>
          </div>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="agriassist-disclaimer-card">
        <span className="disclaimer-icon">ⓘ</span>

        <div>
          <strong>Agricultural Guidance Disclaimer</strong>
          <p>
            AgriAssist provides conversational educational assistance.
            Chemical, pesticide, or diagnostic disease recommendations
            are general in nature and must be verified with certified
            local agronomists or pesticide safety labels before application.
          </p>
        </div>
      </div>
    </section>
  );
}
