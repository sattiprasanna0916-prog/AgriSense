
import { useState, useRef, useEffect } from "react";
import "./AgriAssist.css";
import API_URL from "../api";

const initialMessage = {
  role: "assistant",
  content:
    "Hello! I'm AgriAssist 🌱. I can help you with soil health, fertilizers, irrigation, crop management, plant nutrition, and pest control. Ask me any agricultural question!",
  source: "agrisense_assistant",
};

const suggestedPrompts = [
  {
    icon: "🌱",
    title: "Soil Health",
    question: "How can I improve soil health naturally?",
  },
  {
    icon: "💧",
    title: "Irrigation",
    question: "What are the best irrigation practices for crops?",
  },
  {
    icon: "🌾",
    title: "Crop Management",
    question: "How can I improve crop growth and productivity?",
  },
  {
    icon: "🛡️",
    title: "Pest Management",
    question: "What are natural ways to control common crop pests?",
  },
];

export default function AgriAssist() {
  const [messages, setMessages] = useState([initialMessage]);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Automatically scroll to the latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "end",
    });
  }, [messages, loading]);

  // Send message to Gemini chatbot
  async function sendMessage(questionText, isRetry = false) {
    const question = (questionText || message).trim();

    if (!question || loading) return;

    // Prepare conversation history
    let previousMessages = messages.filter(
      (item) =>
        (item.role === "user" || item.role === "assistant") &&
        !item.isError
    );

    // Remove failed question from history during retry
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

    // Display user question
    if (!isRetry) {
      setMessages((prev) => [
        ...prev,
        {
          role: "user",
          content: question,
        },
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

      // Display Gemini response
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

  // Handle form submission
  function handleFormSubmit(e) {
    e.preventDefault();
    sendMessage();
  }

  // Source label
  function getSourceLabel(source) {
    if (source === "gemini") {
      return "Gemini AI";
    }

    if (source === "agrisense_assistant") {
      return "AgriAssist";
    }

    return source?.replaceAll("_", " ") || "AgriAssist";
  }

  // Clear conversation
  function clearConversation() {
    if (loading) return;

    setMessages([initialMessage]);
    setMessage("");
    inputRef.current?.focus();
  }

  return (
    <section className="agriassist-page">

      {/* PAGE HEADING */}
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
            Your AI-powered agricultural assistant for soil health,
            crop management, irrigation guidance, and pest control.
          </p>

        </div>

        <div className="agriassist-heading-icon">
          <span>🌿</span>
        </div>
      </header>

      {/* MAIN SIDE-BY-SIDE LAYOUT */}
      <div className="agriassist-layout">

        {/* LEFT SIDE: SUGGESTED QUESTIONS */}
        <aside className="agriassist-prompts-panel">

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
                  onClick={() => {
                    setMessage(prompt.question);
                    inputRef.current?.focus();
                  }}
                >
                  <span className="prompt-icon">
                    {prompt.icon}
                  </span>

                  <span className="prompt-text">
                    <strong>{prompt.title}</strong>
                    <small>{prompt.question}</small>
                  </span>

                  <span className="prompt-arrow">↗</span>
                </button>
              ))}

            </div>
          </div>

          {/* LEFT PANEL INFORMATION */}
          <div className="context-history-note">
            <span>🌱</span>

            <div>
              <strong>Smart Farming Assistant</strong>
              <p>
                Ask questions and get AI-powered agricultural guidance
                through a natural conversation.
              </p>
            </div>
          </div>

        </aside>

        {/* RIGHT SIDE: CHAT INTERFACE */}
        <div className="agriassist-chat-card">

          {/* CHAT HEADER */}
          <div className="agriassist-chat-topbar">

            <div className="chat-profile">

              <div className="chat-profile-avatar">
                🌱
              </div>

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

          {/* CHAT MESSAGES */}
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

                    {/* RETRY FAILED MESSAGE */}
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

            {/* THINKING ANIMATION */}
            {loading && (
              <div className="chat-message-row assistant">

                <div className="chat-avatar">
                  🌱
                </div>

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

          {/* MESSAGE INPUT */}
          <form
            className="agriassist-input-bar"
            onSubmit={handleFormSubmit}
          >

            <div className="chat-input-wrapper">

              <span className="chat-input-icon">
                ✎
              </span>

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

          {/* INPUT FOOTER */}
          <div className="chat-input-footer">
            <span>✦ Powered by Gemini AI</span>
            <span>Maximum 1000 characters</span>
          </div>

        </div>

      </div>

      {/* DISCLAIMER */}
      <div className="agriassist-disclaimer-card">

        <span className="disclaimer-icon">
          ⓘ
        </span>

        <div>
          <strong>Agricultural Guidance Disclaimer</strong>

          <p>
            AgriAssist provides general agricultural information
            for educational purposes. Verify important crop,
            fertilizer, pesticide, and disease-management decisions
            with qualified agricultural experts before application.
          </p>
        </div>

      </div>

    </section>
  );
}
