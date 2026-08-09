import { useState } from "react";
import "./App.css";

const exampleQuestions = [
  "What does the document memory contain?",
  "How does semantic search work in this project?",
  "What is the best way to ask the assistant?",
];

function App() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const askQuestion = async (query = question) => {
    const trimmed = query.trim();
    if (!trimmed) {
      setError("Please enter a question or choose an example.");
      return;
    }

    setLoading(true);
    setError("");
    setAnswer("");

    try {
      const response = await fetch("http://127.0.0.1:8000/ask", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question: trimmed }),
      });

      if (!response.ok) {
        throw new Error("Failed to get response from server");
      }

      const data = await response.json();
      setAnswer(data.answer || "No answer returned from server.");
    } catch (err) {
      setError("Unable to connect to the Memora AI backend.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestion = (suggestion) => {
    setQuestion(suggestion);
    askQuestion(suggestion);
  };

  const renderAnswer = () => {
    return answer.split("\n\n").map((block, index) => (
      <p key={index}>{block}</p>
    ));
  };

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <div className="brand-pill">Memora AI</div>
          <h1>Document memory, reimagined.</h1>
          <p className="subtitle">
            A smart assistant for your uploads that finds answers from your
            documents and presents them clearly.
          </p>
        </div>
      </header>

      <main className="app-main">
        <section className="hero-panel">
          <div>
            <h2>Ask anything from your document corpus.</h2>
            <p>
              Type a question, pick an example, and let Memora AI search your
              memory with speed and accuracy.
            </p>
          </div>
          <div className="hero-metrics">
            <div>
              <span>Fast retrieval</span>
              <p>Answers from your documents in seconds.</p>
            </div>
            <div>
              <span>Clean output</span>
              <p>Readable responses with helpful structure.</p>
            </div>
          </div>
        </section>

        <section className="chat-card">
          <div className="chat-top">
            <div>
              <h3>Talk to Memora</h3>
              <p>Ask a question based on your document knowledge base.</p>
            </div>
            <div className="status-pill">
              {loading ? "Waiting for response..." : "Ready to ask"}
            </div>
          </div>

          <div className="suggestions-row">
            {exampleQuestions.map((example) => (
              <button
                key={example}
                className="suggestion-button"
                type="button"
                onClick={() => handleSuggestion(example)}
                disabled={loading}
              >
                {example}
              </button>
            ))}
          </div>

          <div className="input-block">
            <textarea
              aria-label="Ask a question"
              placeholder="Ask a question about your documents..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  askQuestion();
                }
              }}
            />
            <button
              className="primary-button"
              onClick={() => askQuestion()}
              disabled={loading}
            >
              {loading ? "Thinking..." : "Ask Memora"}
            </button>
          </div>

          {error && <div className="error-panel">{error}</div>}

          {answer && (
            <article className="answer-card">
              <div className="answer-card-header">
                <h3>Memora Answer</h3>
                <span>Based on your document memory</span>
              </div>
              <div className="answer-content">{renderAnswer()}</div>
            </article>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
