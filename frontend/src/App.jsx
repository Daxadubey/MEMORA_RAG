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
  const [uploadId, setUploadId] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState("No document uploaded yet.");
  const [selectedFile, setSelectedFile] = useState(null);
  const [sources, setSources] = useState([]);
  const [expandedSources, setExpandedSources] = useState({});

  const askQuestion = async (query = question) => {
    if (!uploadId) {
      setError("Please upload a document before asking a question.");
      return;
    }

    const trimmed = query.trim();
    if (!trimmed) {
      setError("Please enter a question or choose an example.");
      return;
    }

    setLoading(true);
    setError("");
    setAnswer("");
    setSources([]);
    setExpandedSources({});

    try {
      const response = await fetch("http://127.0.0.1:8000/ask", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question: trimmed, upload_id: uploadId }),
      });

      if (!response.ok) {
        const errorBody = await response.json().catch(() => null);
        throw new Error(
          errorBody?.detail || "Failed to get response from server",
        );
      }

      const data = await response.json();
      setAnswer(data.answer || "No answer returned from server.");
      setSources(Array.isArray(data.sources) ? data.sources : []);
    } catch (err) {
      setError(err.message || "Unable to connect to the Memora AI backend.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestion = (suggestion) => {
    if (!uploadId) return;
    setQuestion(suggestion);
    askQuestion(suggestion);
  };

  const uploadDocument = async () => {
    if (!selectedFile) {
      setError("Please select a document to upload.");
      return;
    }

    setUploading(true);
    setError("");
    setAnswer("");
    setSources([]);
    setExpandedSources({});
    setUploadStatus("Uploading document...");

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      const response = await fetch("http://127.0.0.1:8000/upload", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data?.detail || "Upload failed");
      }

      setUploadId(data.upload_id);
      setUploadStatus("Document ready.");
      setError("");
    } catch (err) {
      setError(err.message || "Unable to upload the document.");
      setUploadStatus("Upload failed.");
      console.error(err);
    } finally {
      setUploading(false);
    }
  };

  const renderAnswer = () => {
    return answer
      .split("\n\n")
      .map((block, index) => <p key={index}>{block}</p>);
  };

  const toggleSource = (index) => {
    setExpandedSources((prev) => ({
      ...prev,
      [index]: !prev[index],
    }));
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
              {uploading
                ? "Uploading document..."
                : uploadId
                  ? "Document ready"
                  : "Upload a document first"}
            </div>
          </div>

          <div className="upload-section">
            <label className="file-input-label">
              <span>Choose a document</span>
              <input
                type="file"
                accept=".docx,.pdf,.txt"
                onChange={(e) => {
                  setSelectedFile(e.target.files?.[0] || null);
                  setError("");
                  setUploadStatus("Ready to upload.");
                }}
              />
            </label>
            <button
              className="upload-button"
              type="button"
              onClick={uploadDocument}
              disabled={uploading || loading}
            >
              {uploading ? "Uploading..." : "Upload Document"}
            </button>
            <div className="upload-status">{uploadStatus}</div>
          </div>

          <div className="suggestions-row">
            {exampleQuestions.map((example) => (
              <button
                key={example}
                className="suggestion-button"
                type="button"
                onClick={() => handleSuggestion(example)}
                disabled={loading || !uploadId}
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
              disabled={loading || !uploadId}
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

              {sources.length > 0 && (
                <section className="sources-section">
                  <div className="sources-header">
                    <h4>Sources Used</h4>
                    <span>
                      {sources.length} source{sources.length === 1 ? "" : "s"}
                    </span>
                  </div>
                  <div className="sources-list">
                    {sources.map((source, index) => {
                      const expanded = Boolean(expandedSources[index]);
                      const similarity = Number(source.similarity) || 0;
                      const percentage = Math.round(similarity * 100);
                      const chunkText = source.chunk || "";
                      const preview =
                        chunkText.length > 160
                          ? `${chunkText.slice(0, 160).trim()}…`
                          : chunkText;
                      const hasMore = chunkText.length > 160;

                      return (
                        <div key={index} className="source-card">
                          <div className="source-card-header">
                            <div>
                              <span className="source-label">
                                Source {index + 1}
                              </span>
                              <span className="source-score">
                                {percentage}% match
                              </span>
                            </div>
                            {hasMore && (
                              <button
                                className="source-toggle"
                                type="button"
                                onClick={() => toggleSource(index)}
                              >
                                {expanded ? "Show less" : "Show more"}
                              </button>
                            )}
                          </div>
                          <p
                            className={`source-text ${expanded ? "expanded" : "collapsed"}`}
                          >
                            {expanded ? chunkText : preview}
                          </p>
                        </div>
                      );
                    })}
                  </div>
                </section>
              )}
            </article>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
