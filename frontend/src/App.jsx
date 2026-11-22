import React, { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {BookOpen,
  Check,
  CheckCircle2,
  Copy,
  Download,
  FileText,
  FolderOpen,
  History,
  Loader2,
  Mic,
  Moon,
  MoreHorizontal,
  Plus,
  RefreshCw,
  RotateCw,
  Sparkles,
  Sun,
  ThumbsDown,
  ThumbsUp,
  Upload, ArrowUp} from "lucide-react";

const API_BASE = import.meta.env.VITE_API_URL || "";
const MODES = ["Standard", "Quick", "Deep"];

function cleanStars(text) {
  if (!text) return "";
  return String(text).split("*").join("");
}

function isNumberedLine(line) {
  let i = 0;
  while (i < line.length && line[i] >= "0" && line[i] <= "9") {
    i += 1;
  }
  return i > 0 && line[i] === ".";
}

function buildSmartMarkdown(rawText, topicTitle) {
  const base = cleanStars(rawText).trim();
  if (!base) return "";
  const title =
    cleanStars(topicTitle || "Research Overview").trim() || "Research Overview";
  const shortTitle = title.length > 80 ? title.slice(0, 77) + "..." : title;

  if (base.startsWith("#")) {
    return base;
  }

  const lines = base
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter(Boolean);

  const hasTableOrList = lines.some(
    (l) => l.includes("|") || l.startsWith("\u2022") || isNumberedLine(l)
  );

  if (hasTableOrList) {
    return "## " + shortTitle + "\n\n" + base;
  }

  const sentences = base
    .split(/(?<=[.!?])\s+/)
    .map((s) => s.trim())
    .filter(Boolean);

  if (sentences.length > 1) {
    const bullets = sentences.slice(1).map((s) => "\u2022 Important: " + s);
    return (
      "## " +
      shortTitle +
      "\n\n" +
      sentences[0] +
      "\n\n### Key & Important Points\n" +
      bullets.join("\n")
    );
  }

  return "## " + shortTitle + "\n\n\u2022 Important: " + base;
}

function ProjectLogo({ size = 36 }) {
  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: Math.round(size * 0.32),
        background: "linear-gradient(135deg, #3b82f6 0%, #8b5cf6 55%, #06b6d4 100%)",
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        flexShrink: 0,
        boxShadow: "0 6px 18px rgba(59, 130, 246, 0.28)",
      }}
      title="Clarity"
    >
      <svg
        width={Math.round(size * 0.6)}
        height={Math.round(size * 0.6)}
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <circle cx="6" cy="7" r="2.2" fill="#ffffff" />
        <circle cx="18" cy="7" r="2.2" fill="#ffffff" />
        <circle cx="12" cy="18" r="2.4" fill="#ffffff" />
        <path
          d="M8 8.2L10.6 15.8M16 8.2L13.4 15.8M8.2 7H15.8"
          stroke="#ffffff"
          strokeWidth="1.8"
          strokeLinecap="round"
        />
        <path
          d="M12 3.2L12.7 5.1L14.6 5.8L12.7 6.5L12 8.4L11.3 6.5L9.4 5.8L11.3 5.1L12 3.2Z"
          fill="#fde047"
        />
      </svg>
    </div>
  );
}

export default function App() {
  const [theme, setTheme] = useState("dark");
  const [health, setHealth] = useState({ online: false, db: "checking" });

  const [sourcesOpen, setSourcesOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState("");
  const [documents, setDocuments] = useState([]);

  const [mode, setMode] = useState("Standard");
  const [plusMenuOpen, setPlusMenuOpen] = useState(false);
  const [modeMenuOpen, setModeMenuOpen] = useState(false);
  const [topic, setTopic] = useState("");
  const [lastQuery, setLastQuery] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [running, setRunning] = useState(false);
  const [listening, setListening] = useState(false);
  const [followup, setFollowup] = useState("");
  const [currentRun, setCurrentRun] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");
  const [copiedSummary, setCopiedSummary] = useState(false);
  const [reaction, setReaction] = useState(null);
  const recognitionRef = useRef(null);

  const [activeTab, setActiveTab] = useState("report");
  const [copiedReport, setCopiedReport] = useState(false);
  const [runsHistory, setRunsHistory] = useState([]);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  async function fetchHealth() {
    try {
      const res = await fetch(`${API_BASE}/health`);
      if (!res.ok) throw new Error("Health failed");
      const data = await res.json();
      setHealth({ online: true, db: data.database || "connected" });
    } catch {
      setHealth({ online: false, db: "offline" });
    }
  }

  async function fetchDocuments() {
    try {
      const res = await fetch(`${API_BASE}/documents`);
      if (res.ok) {
        const data = await res.json();
        setDocuments(Array.isArray(data) ? data : []);
      }
    } catch {}
  }

  async function fetchHistory() {
    try {
      const res = await fetch(`${API_BASE}/research/runs?limit=12`);
      if (res.ok) {
        const data = await res.json();
        setRunsHistory(Array.isArray(data) ? data : []);
      }
    } catch {}
  }

  useEffect(() => {
    fetchHealth();
    fetchDocuments();
    fetchHistory();
  }, []);

  function toggleVoiceInput() {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setErrorMsg("Voice input is not supported in this browser.");
      return;
    }
    if (listening && recognitionRef.current) {
      recognitionRef.current.stop();
      setListening(false);
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.lang = "en-IN";
    recognition.interimResults = false;
    recognition.onstart = () => setListening(true);
    recognition.onerror = () => setListening(false);
    recognition.onend = () => setListening(false);
    recognition.onresult = (event) => {
      const transcript = event.results?.[0]?.[0]?.transcript || "";
      if (transcript) {
        setTopic((prev) => (prev ? `${prev} ${transcript}` : transcript));
      }
    };
    recognitionRef.current = recognition;
    recognition.start();
  }

  async function handleUploadDocument(e) {
    e.preventDefault();
    if (!selectedFile) return;
    setUploading(true);
    setUploadMsg("");
    setErrorMsg("");
    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      const res = await fetch(`${API_BASE}/documents/upload`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) {
        const txt = await res.text();
        throw new Error(txt || `Upload error ${res.status}`);
      }
      const data = await res.json();
      setUploadMsg(
        `Indexed "${data.filename || selectedFile.name}" (${data.chunk_count ?? 0} chunks)`
      );
      setSelectedFile(null);
      await fetchDocuments();
    } catch (err) {
      setErrorMsg(`Document upload failed: ${err.message}`);
    } finally {
      setUploading(false);
    }
  }

  async function executeResearch(queryText, customSessionId = "") {
    const cleanQuery = (queryText || "").trim();
    if (!cleanQuery) {
      setErrorMsg("Type a topic and press Enter to run research.");
      return;
    }
    setLastQuery(cleanQuery);
    setReaction(null);
    setRunning(true);
    setErrorMsg("");
    try {
      const payload = {
        task: cleanQuery,
        research_mode: mode,
        session_id: (customSessionId || sessionId || "").trim() || undefined,
      };
      const res = await fetch(`${API_BASE}/research/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const txt = await res.text();
        throw new Error(txt || `Server returned ${res.status}`);
      }
      const data = await res.json();
      setCurrentRun(data);
      setActiveTab("report");
      await Promise.all([fetchHealth(), fetchHistory()]);
    } catch (err) {
      setErrorMsg(`Research run failed: ${err.message}`);
    } finally {
      setRunning(false);
    }
  }

  async function handleFollowupSubmit(e) {
    e.preventDefault();
    if (!followup.trim() || !currentRun) return;
    const combined = `${currentRun.task || lastQuery || topic} \u2014 Follow-up: ${followup.trim()}`;
    setFollowup("");
    await executeResearch(combined, "");
  }

  async function handleLoadRun(sid) {
    setErrorMsg("");
    try {
      const res = await fetch(`${API_BASE}/research/runs/${sid}`);
      if (!res.ok) throw new Error(`Failed to load run (${res.status})`);
      const data = await res.json();
      setCurrentRun(data);
      setLastQuery(data.task || "");
      setActiveTab("report");
    } catch (err) {
      setErrorMsg(err.message);
    }
  }

  async function handleExport(fmt) {
    const sid = currentRun?.session_id;
    if (!sid) return;
    try {
      const res = await fetch(
        `${API_BASE}/research/runs/${sid}/export?fmt=${encodeURIComponent(fmt)}`
      );
      if (!res.ok) throw new Error(`Export ${fmt.toUpperCase()} failed`);
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `research_${sid.slice(0, 8)}.${fmt}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setErrorMsg(err.message);
    }
  }

  const citations = currentRun?.citations || [];
  const claims = currentRun?.verified_claims?.claims || [];
  const shownPrompt = lastQuery || currentRun?.task || "";
  const shownResponse = currentRun?.summary || "";
  const chatMarkdown = buildSmartMarkdown(shownResponse, shownPrompt);
  const reportMarkdown = buildSmartMarkdown(currentRun?.final_report || "", shownPrompt);

  return (
    <div className="app-shell">
      <header className="top-bar">
        <div className="brand-group">
<ProjectLogo size={36} />
          <div>
            <div className="brand-title">Clarity</div>
            <div className="brand-sub">
            </div>
          </div>
        </div>

        <div className="top-actions">
          <span className={`pill ${health.online ? "ok" : "err"}`}>
            <CheckCircle2 size={13} />
            {health.online ? "API Online" : "API Offline"}
          </span>
          <span className="pill">DB: {health.db}</span>
          <button
            type="button"
            className="theme-btn"
            onClick={() => fetchHealth()}
            title="Refresh backend status"
          >
            <RefreshCw size={14} />
          </button>
          <button
            type="button"
            className="theme-btn"
            onClick={() => setTheme((t) => (t === "dark" ? "light" : "dark"))}
          >
            {theme === "dark" ? <Sun size={14} /> : <Moon size={14} />}
            {theme === "dark" ? "Light" : "Dark"}
          </button>
        </div>
      </header>

      <main className={`workspace-grid-hover ${sourcesOpen ? "sources-expanded" : ""}`}>
        <div
          className="sources-hover-shell"
          onMouseEnter={() => setSourcesOpen(true)}
          onMouseLeave={() => setSourcesOpen(false)}
        >
          {!sourcesOpen ? (
            <div
              className="sources-rail-card"
              onClick={() => setSourcesOpen(true)}
              title="Hover to open Sources & Knowledge Base"
            >
              <FolderOpen size={18} />
              <span className="pill" style={{ padding: "3px 7px" }}>
                {documents.length}
              </span>
              <span className="sources-rail-label">Hover for Sources</span>
            </div>
          ) : (
            <section className="panel" style={{ height: "100%" }}>
              <div className="panel-heading">
                <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <FolderOpen size={16} />
                  Sources & Knowledge Base
                </span>
                <span className="muted">{documents.length} docs</span>
              </div>

              <form className="upload-box" onSubmit={handleUploadDocument}>
                <div className="muted">Upload PDF, DOCX, TXT, or CSV for RAG queries</div>
                <input
                  type="file"
                  accept=".pdf,.docx,.txt,.csv"
                  onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                  className="input-clean"
                />
                <button
                  type="submit"
                  className="btn-secondary"
                  disabled={!selectedFile || uploading}
                >
                  {uploading ? (
                    <>
                      <Loader2 size={14} /> Indexing...
                    </>
                  ) : (
                    <>
                      <Upload size={14} /> Index Document
                    </>
                  )}
                </button>
                {uploadMsg && (
                  <div className="muted" style={{ color: "var(--ok-fg)" }}>
                    {uploadMsg}
                  </div>
                )}
              </form>

              <div>
                <div className="section-label">Indexed Documents</div>
                {documents.length === 0 ? (
                  <div className="muted">No documents indexed yet.</div>
                ) : (
                  documents.map((doc, idx) => (
                    <div key={doc.id || doc.filename || idx} className="item-card">
                      <div className="row-between">
                        <div>
                          <span className="tag-badge">
                            {(doc.file_ext || "DOC").toUpperCase()}
                          </span>
                          <strong>{doc.filename || doc.title || "Document"}</strong>
                        </div>
                      </div>
                      <div className="muted" style={{ marginTop: 4 }}>
                        Chunks: {doc.chunk_count ?? 0}
                      </div>
                    </div>
                  ))
                )}
              </div>

              {citations.length > 0 && (
                <div>
                  <div className="section-label">Active Run Citations</div>
                  {citations.map((c, idx) => (
                    <div key={c.id || idx} className="item-card">
                      <span className="tag-badge">[{c.id || c.citation_id || idx + 1}]</span>
                      <span>{c.title || c.source || "Source"}</span>
                      {c.url && (
                        <div style={{ marginTop: 4 }}>
                          <a
                            href={c.url}
                            target="_blank"
                            rel="noreferrer"
                            style={{ color: "var(--accent)", fontSize: "0.75rem" }}
                          >
                            Open Source
                          </a>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </section>
          )}
        </div>

        <section className="panel studio-col">
          <div className="panel-heading">
            <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <BookOpen size={16} />
              Research & Chat Studio
            </span>
            <span className="pill">Mode: {mode}</span>
          </div>

          <div className="studio-body-scroll">
            {errorMsg && <div className="alert-err">{errorMsg}</div>}

            {shownPrompt || running || currentRun ? (
              <div className="chat-turn-list">
                {shownPrompt && (
                  <div className="user-bubble-row">
                    <div className="user-prompt-bubble">{shownPrompt}</div>
                  </div>
                )}

                {running && (
                  <div className="assistant-turn-block">
                    <div
                      className="assistant-turn-text muted"
                      style={{ display: "flex", alignItems: "center", gap: 8 }}
                    >
                      <Loader2 size={15} />
                      <span>Running 7-Agent research workflow...</span>
                    </div>
                  </div>
                )}

                {!running && currentRun && (
                  <div className="assistant-turn-block">
                    <div className="response-structured-box">
                      <span className="imp-highlight-chip">
                        <Sparkles size={11} /> Topic Heading & Key Highlights
                      </span>
                      <div className="markdown-body">
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          components={{
                            table: ({ node, ...props }) => (
                              <div className="table-wrap">
                                <table {...props} />
                              </div>
                            ),
                          }}
                        >
                          {chatMarkdown}
                        </ReactMarkdown>
                      </div>
                    </div>

                    <div className="msg-action-bar">
                      <button
                        type="button"
                        className={`msg-action-btn ${reaction === "up" ? "active" : ""}`}
                        onClick={() => setReaction((r) => (r === "up" ? null : "up"))}
                        title="Helpful"
                      >
                        <ThumbsUp size={15} />
                      </button>

                      <button
                        type="button"
                        className={`msg-action-btn ${reaction === "down" ? "active" : ""}`}
                        onClick={() => setReaction((r) => (r === "down" ? null : "down"))}
                        title="Needs improvement"
                      >
                        <ThumbsDown size={15} />
                      </button>

                      <button
                        type="button"
                        className="msg-action-btn"
                        onClick={() => executeResearch(shownPrompt, currentRun.session_id || "")}
                        title="Re-run query"
                      >
                        <RotateCw size={15} />
                      </button>

                      <button
                        type="button"
                        className="msg-action-btn"
                        onClick={() => {
                          navigator.clipboard?.writeText(
                            cleanStars(shownResponse || currentRun.final_report || "")
                          );
                          setCopiedSummary(true);
                          setTimeout(() => setCopiedSummary(false), 1600);
                        }}
                        title="Copy response"
                      >
                        {copiedSummary ? <Check size={15} /> : <Copy size={15} />}
                      </button>

                      <button
                        type="button"
                        className="msg-action-btn"
                        onClick={() => setActiveTab("report")}
                        title="Open full report"
                      >
                        <MoreHorizontal size={15} />
                      </button>
                    </div>

                    <form
                      onSubmit={handleFollowupSubmit}
                      style={{ marginTop: 8, display: "flex", gap: 8 }}
                    >
                      <input
                        type="text"
                        className="input-clean"
                        placeholder="Ask a follow-up question and press Enter..."
                        value={followup}
                        onChange={(e) => setFollowup(e.target.value)}
                      />
                      <button
                        type="submit"
                        className="btn-secondary"
                        disabled={running || !followup.trim()}
                      >
                        Follow-up
                      </button>
                    </form>
                  </div>
                )}
              </div>
            ) : (
              <div className="item-card">
                <div className="muted">
                  Type a query in the bottom bar and press <strong>Enter</strong> to run research.
                </div>
              </div>
            )}
          </div>

          <div className="bottom-composer-dock">
            <div
              className="gemini-pill-wrap"
              onMouseLeave={() => setModeMenuOpen(false)}
            >
              <button
                type="button"
                className={`gemini-plus-btn ${modeMenuOpen ? "open" : ""}`}
                onClick={() => setModeMenuOpen((o) => !o)}
                title="Research modes"
              >
                <Plus size={18} />
              </button>

              <input
                type="text"
                className="gemini-pill-input"
                placeholder="Ask Research Studio... (Press Enter to run)"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey && !running) {
                    e.preventDefault();
                    const q = topic;
                    setTopic("");
                    executeResearch(q, sessionId);
                  }
                }}
              />

              <div className="gemini-right-group">
                  <Sparkles size={12} /> 7-Agent

                <button
                  type="button"
                  className={`gemini-icon-btn ${listening ? "listening" : ""}`}
                  onClick={toggleVoiceInput}
                  title={listening ? "Stop voice input" : "Voice input"}
                >
                  <Mic size={17} />
                </button>
                  <button
                    type="submit"
                    className="clarity-send-circle"
                    aria-label="Send query"
                    title="Send"
                    disabled={running}
                  >
                    <ArrowUp size={17} />
                  </button>
                </div>

              {modeMenuOpen && (
                <div className="gemini-popover">
                  <div
                    className="section-label"
                    style={{ padding: "4px 8px", marginBottom: 4 }}
                  >
                    Select Research Mode
                  </div>
                  {MODES.map((m) => (
                    <button
                      key={m}
                      type="button"
                      className={`mode-option ${mode === m ? "active" : ""}`}
                      onClick={() => {
                        setMode(m);
                        setModeMenuOpen(false);
                      }}
                    >
                      <span>{m}</span>
                      <span>{mode === m ? "Active" : ""}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="pill-sub-row">
              <input
                type="text"
                className="input-clean"
                style={{ maxWidth: 260, padding: "6px 11px", fontSize: "0.8rem" }}
                value={sessionId}
                onChange={(e) => setSessionId(e.target.value)}
              />
              <span className="muted">Press Enter to run directly</span>
            </div>
          </div>
        </section>

        <section className="panel">
          <div className="panel-heading">
            <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <FileText size={16} />
              Studio & Verification
            </span>
          </div>

          <div className="tabs-bar">
            <button
              type="button"
              className={`tab-btn ${activeTab === "report" ? "active" : ""}`}
              onClick={() => setActiveTab("report")}
            >
              Report
            </button>
            <button
              type="button"
              className={`tab-btn ${activeTab === "facts" ? "active" : ""}`}
              onClick={() => setActiveTab("facts")}
            >
              Fact Check ({claims.length})
            </button>
            <button
              type="button"
              className={`tab-btn ${activeTab === "history" ? "active" : ""}`}
              onClick={() => {
                setActiveTab("history");
                fetchHistory();
              }}
            >
              History & Export
            </button>
          </div>

          {activeTab === "report" && (
            <div>
              {reportMarkdown ? (
                <div className="report-card">
                  <div className="report-toolbar">
                    <button
                      type="button"
                      className="btn-secondary"
                      onClick={() => {
                        navigator.clipboard?.writeText(reportMarkdown);
                        setCopiedReport(true);
                        setTimeout(() => setCopiedReport(false), 1800);
                      }}
                    >
                      {copiedReport ? "Copied" : "Copy Report"}
                    </button>
                  </div>
                  <div className="markdown-body">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        table: ({ node, ...props }) => (
                          <div className="table-wrap">
                            <table {...props} />
                          </div>
                        ),
                      }}
                    >
                      {reportMarkdown}
                    </ReactMarkdown>
                  </div>
                </div>
              ) : (
                <div className="item-card">
                  <div className="muted">
                    Run a research topic from the center studio to view the generated report here.
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === "facts" && (
            <div>
              {claims.length === 0 ? (
                <div className="item-card">
                  <div className="muted">No verified claims available for the active run.</div>
                </div>
              ) : (
                claims.map((c, idx) => (
                  <div key={idx} className="item-card">
                    <span className="tag-badge">[{c.status || "Unchecked"}]</span>
                    <strong>{cleanStars(c.claim)}</strong>
                    {c.evidence && (
                      <div className="muted" style={{ marginTop: 4 }}>
                        Evidence: {cleanStars(c.evidence)}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          )}

          {activeTab === "history" && (
            <div>
              {currentRun?.session_id && (
                <div style={{ marginBottom: 14 }}>
                  <div className="section-label">Export Active Run</div>
                  <div className="export-row">
                    {["md", "docx", "pdf"].map((fmt) => (
                      <button
                        key={fmt}
                        type="button"
                        className="btn-secondary"
                        onClick={() => handleExport(fmt)}
                      >
                        <Download size={13} /> {fmt.toUpperCase()}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <div className="section-label">
                <History size={12} style={{ verticalAlign: "middle", marginRight: 4 }} />
                Recent Runs
              </div>
              {runsHistory.length === 0 ? (
                <div className="muted">No saved runs found.</div>
              ) : (
                runsHistory.map((r, idx) => {
                  const sid = r.session_id;
                  return (
                    <div key={sid || idx} className="history-row">
                      <div style={{ minWidth: 0 }}>
                        <div
                          style={{
                            fontSize: "0.82rem",
                            fontWeight: 500,
                            whiteSpace: "nowrap",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                          }}
                        >
                          {cleanStars(r.task) || "Untitled Research"}
                        </div>
                        <div className="muted">{r.status || "completed"}</div>
                      </div>
                      {sid && (
                        <button
                          type="button"
                          className="btn-secondary"
                          onClick={() => handleLoadRun(sid)}
                        >
                          Load
                        </button>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
