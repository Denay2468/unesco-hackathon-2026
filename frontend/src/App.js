import React, { useState, useEffect, useRef, useCallback } from "react";
import { api } from "./api";
import "./App.css";

// ─────────────────────────────────────────────────────────────────────────────
// ICONS (inline SVG to avoid extra deps)
// ─────────────────────────────────────────────────────────────────────────────
const Icon = ({ name, size = 20 }) => {
  const icons = {
    scan: <><path d="M3 7V5a2 2 0 0 1 2-2h2M17 3h2a2 2 0 0 1 2 2v2M21 17v2a2 2 0 0 1-2 2h-2M7 21H5a2 2 0 0 1-2-2v-2"/><rect x="7" y="7" width="10" height="10" rx="1"/></>,
    academy: <><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></>,
    lighting: <><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></>,
    metadata: <><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/><line x1="9" y1="3" x2="9" y2="21"/></>,
    reverse_image: <><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><path d="M11 8v6M8 11h6"/></>,
    voice_artifacts: <><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></>,
    check: <><polyline points="20 6 9 17 4 12"/></>,
    x: <><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></>,
    upload: <><polyline points="16 16 12 12 8 16"/><line x1="12" y1="12" x2="12" y2="21"/><path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"/></>,
    trophy: <><path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/><path d="M4 22h16"/><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"/><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2z"/></>,
    arrow_left: <><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></>,
    film: <><rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18"/><line x1="7" y1="2" x2="7" y2="22"/><line x1="17" y1="2" x2="17" y2="22"/><line x1="2" y1="12" x2="22" y2="12"/><line x1="2" y1="7" x2="7" y2="7"/><line x1="2" y1="17" x2="7" y2="17"/><line x1="17" y1="17" x2="22" y2="17"/><line x1="17" y1="7" x2="22" y2="7"/></>,
    mic: <><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></>,
    image: <><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></>,
  };
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      {icons[name]}
    </svg>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// TOOL CONFIG
// ─────────────────────────────────────────────────────────────────────────────
const TOOL_CONFIG = {
  lighting:      { label: "Analyze Lighting",       icon: "lighting",       color: "#f59e0b" },
  metadata:      { label: "Check Metadata",          icon: "metadata",       color: "#3b82f6" },
  reverse_image: { label: "Reverse Image Search",    icon: "reverse_image",  color: "#8b5cf6" },
  voice_artifacts:{ label: "Voice Artifact Scan",   icon: "voice_artifacts", color: "#ec4899" },
};

const MEDIA_TYPE_TOOLS = {
  image: ["lighting", "metadata", "reverse_image"],
  video: ["lighting", "metadata", "voice_artifacts"],
  audio: ["voice_artifacts", "metadata", "reverse_image"],
};

// ─────────────────────────────────────────────────────────────────────────────
// ACADEMY MODE
// ─────────────────────────────────────────────────────────────────────────────
function AcademyMode({ totalScore, onScoreUpdate }) {
  const [cases, setCases] = useState([]);
  const [activeCase, setActiveCase] = useState(null);
  const [revealedClues, setRevealedClues] = useState({});
  const [loadingClue, setLoadingClue] = useState(null);
  const [guess, setGuess] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [username] = useState(() => `Detective_${Math.floor(Math.random() * 9000) + 1000}`);

  useEffect(() => {
    api.getCases().then(setCases).catch(console.error).finally(() => setLoading(false));
  }, []);

  const selectCase = async (id) => {
    setLoading(true);
    const data = await api.getCase(id).catch(() => null);
    if (data) {
      setActiveCase(data);
      setRevealedClues({});
      setGuess(null);
      setResult(null);
    }
    setLoading(false);
  };

  const useTool = async (toolType) => {
    if (revealedClues[toolType] || loadingClue) return;
    setLoadingClue(toolType);
    const clue = await api.getClue(activeCase.id, toolType).catch(() => null);
    if (clue) setRevealedClues(prev => ({ ...prev, [toolType]: clue.clue_text }));
    setLoadingClue(null);
  };

  const submitGuess = async (g) => {
    setGuess(g);
    const res = await api.verifyGuess(activeCase.id, g, username).catch(() => null);
    if (res) {
      setResult(res);
      if (res.points_earned > 0) onScoreUpdate(res.points_earned);
    }
  };

  const availableTools = activeCase ? (MEDIA_TYPE_TOOLS[activeCase.media_type] || Object.keys(TOOL_CONFIG)) : [];

  if (loading) return <div className="loading-state"><div className="spinner"/><span>Loading case files…</span></div>;

  // Case list
  if (!activeCase) return (
    <div className="academy-cases">
      <div className="section-header">
        <h2>Active Cases</h2>
        <p>Select a case to begin your investigation</p>
      </div>
      <div className="cases-grid">
        {cases.map(c => (
          <button key={c.id} className="case-card" onClick={() => selectCase(c.id)}>
            <div className="case-card-icon">
              <Icon name={c.media_type === "audio" ? "mic" : c.media_type === "video" ? "film" : "image"} size={28}/>
            </div>
            <div className="case-card-body">
              <span className="case-badge">{c.media_type.toUpperCase()}</span>
              <h3>{c.title}</h3>
              <span className="case-points">+100 pts available</span>
            </div>
            <div className="case-card-arrow">›</div>
          </button>
        ))}
      </div>
    </div>
  );

  // Case investigation view
  return (
    <div className="case-detail">
      <button className="back-btn" onClick={() => setActiveCase(null)}>
        <Icon name="arrow_left" size={16}/> All Cases
      </button>

      <div className="case-header">
        <span className="case-badge">{activeCase.media_type.toUpperCase()}</span>
        <h2>{activeCase.title}</h2>
      </div>

      <div className="case-body">
        {/* Media placeholder */}
        <div className="media-placeholder">
          <Icon name={activeCase.media_type === "audio" ? "mic" : activeCase.media_type === "video" ? "film" : "image"} size={40}/>
          <span>Media file loaded</span>
          <code className="media-url">{activeCase.media_url}</code>
        </div>

        {/* Story */}
        <div className="story-card">
          <div className="story-label">📋 CASE FILE</div>
          <p>{activeCase.story}</p>
        </div>

        {/* Tools */}
        <div className="tools-section">
          <h3>Forensic Tools</h3>
          <div className="tools-grid">
            {availableTools.map(toolType => {
              const t = TOOL_CONFIG[toolType];
              const used = !!revealedClues[toolType];
              const busy = loadingClue === toolType;
              return (
                <button
                  key={toolType}
                  className={`tool-btn ${used ? "used" : ""} ${busy ? "loading" : ""}`}
                  style={{ "--tool-color": t.color }}
                  onClick={() => useTool(toolType)}
                  disabled={busy || !!result}
                >
                  <Icon name={t.icon} size={18}/>
                  <span>{busy ? "Scanning…" : t.label}</span>
                  {used && <span className="tool-check">✓</span>}
                </button>
              );
            })}
          </div>

          {/* Revealed clues */}
          {Object.entries(revealedClues).map(([toolType, text]) => (
            <div key={toolType} className="clue-card" style={{ "--tool-color": TOOL_CONFIG[toolType]?.color }}>
              <div className="clue-label">
                <Icon name={TOOL_CONFIG[toolType]?.icon} size={14}/>
                {TOOL_CONFIG[toolType]?.label}
              </div>
              <p>{text}</p>
            </div>
          ))}
        </div>

        {/* Guess interface */}
        {!result && (
          <div className="verdict-section">
            <h3>Your Verdict</h3>
            <p>Based on your investigation, is this media real or AI-generated?</p>
            <div className="verdict-buttons">
              <button className="verdict-btn real" onClick={() => submitGuess("real")}>
                <Icon name="check" size={20}/> Real
              </button>
              <button className="verdict-btn fake" onClick={() => submitGuess("fake")}>
                <Icon name="x" size={20}/> Fake / AI-Generated
              </button>
            </div>
          </div>
        )}

        {/* Result reveal */}
        {result && (
          <div className={`result-card ${result.correct ? "correct" : "incorrect"}`}>
            <div className="result-header">
              <Icon name={result.correct ? "check" : "x"} size={32}/>
              <div>
                <h3>{result.correct ? "Correct! +100 pts" : "Not quite…"}</h3>
                <p>This media is <strong>{result.correct_answer.toUpperCase()}</strong></p>
              </div>
            </div>
            <div className="result-explanation">
              <div className="explanation-label">🔍 FORENSIC ANALYSIS</div>
              <p>{result.explanation}</p>
            </div>
            <button className="back-btn" style={{ marginTop: "1rem" }} onClick={() => setActiveCase(null)}>
              ← Next Case
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// SCANNER MODE
// ─────────────────────────────────────────────────────────────────────────────
function ScannerMode() {
  const [dragging, setDragging] = useState(false);
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("idle"); // idle | scanning | done | error
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");
  const inputRef = useRef();

  const handleFile = useCallback((f) => {
    setFile(f);
    setResult(null);
    setStatus("idle");
    setErrorMsg("");
  }, []);

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  }, [handleFile]);

  const scan = async () => {
    if (!file) return;
    setStatus("scanning");
    setErrorMsg("");
    try {
      const res = await api.detectUpload(file);
      setResult(res);
      setStatus("done");
    } catch (err) {
      setErrorMsg(err.message || "Detection failed");
      setStatus("error");
    }
  };

  const reset = () => {
    setFile(null);
    setResult(null);
    setStatus("idle");
    setErrorMsg("");
  };

  const confidence = result ? Math.round(result.confidence * 100) : 0;
  const isFake = confidence >= 50;
  const meterColor = confidence < 30 ? "#22c55e" : confidence < 60 ? "#f59e0b" : "#ef4444";

  return (
    <div className="scanner-mode">
      <div className="section-header">
        <h2>Live Scanner</h2>
        <p>Upload any image, video, or audio file to check for AI manipulation</p>
      </div>

      {/* Drop zone */}
      {!result && (
        <div
          className={`drop-zone ${dragging ? "drag-over" : ""} ${file ? "has-file" : ""}`}
          onDragOver={e => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          onClick={() => !file && inputRef.current?.click()}
        >
          <input ref={inputRef} type="file" accept="image/*,video/*,audio/*" style={{ display: "none" }} onChange={e => e.target.files[0] && handleFile(e.target.files[0])}/>
          {!file ? (
            <>
              <div className="drop-icon"><Icon name="upload" size={40}/></div>
              <p className="drop-label">Drop a file here or <span className="drop-link">browse</span></p>
              <p className="drop-hint">Supports images (JPEG/PNG/WebP), video (MP4/WebM), audio (MP3/WAV/OGG) · Max 25 MB</p>
            </>
          ) : (
            <div className="file-preview">
              <Icon name={file.type.startsWith("audio") ? "mic" : file.type.startsWith("video") ? "film" : "image"} size={32}/>
              <div className="file-info">
                <span className="file-name">{file.name}</span>
                <span className="file-size">{(file.size / 1024 / 1024).toFixed(2)} MB · {file.type}</span>
              </div>
              <button className="remove-file" onClick={e => { e.stopPropagation(); reset(); }}>
                <Icon name="x" size={16}/>
              </button>
            </div>
          )}
        </div>
      )}

      {/* Scan button */}
      {file && status !== "done" && (
        <button className={`scan-btn ${status === "scanning" ? "scanning" : ""}`} onClick={scan} disabled={status === "scanning"}>
          {status === "scanning" ? (
            <><div className="spinner"/> Analyzing…</>
          ) : (
            <><Icon name="scan" size={18}/> Scan for Deepfake</>
          )}
        </button>
      )}

      {/* Error state */}
      {status === "error" && (
        <div className="error-card">
          <Icon name="x" size={20}/>
          <p>{errorMsg}</p>
          {errorMsg.includes("Daily scan limit") && (
            <p className="error-hint">Switch to The Academy tab — there are 4 training cases waiting for you!</p>
          )}
          <button className="back-btn" onClick={reset}>Try another file</button>
        </div>
      )}

      {/* Result */}
      {status === "done" && result && (
        <div className="scan-result">
          <div className={`verdict-banner ${isFake ? "fake" : "real"}`}>
            <Icon name={isFake ? "x" : "check"} size={28}/>
            <div>
              <h3>{result.verdict}</h3>
              <p>{result.file_type} analysis complete</p>
            </div>
          </div>

          <div className="confidence-meter">
            <div className="meter-label">
              <span>AI Confidence Score</span>
              <span className="meter-pct" style={{ color: meterColor }}>{result.percentage}</span>
            </div>
            <div className="meter-track">
              <div className="meter-fill" style={{ width: result.percentage, background: meterColor }}/>
            </div>
            <div className="meter-scale">
              <span style={{ color: "#22c55e" }}>Real</span>
              <span style={{ color: "#f59e0b" }}>Uncertain</span>
              <span style={{ color: "#ef4444" }}>AI-Generated</span>
            </div>
          </div>

          <div className="result-disclaimer">
            <strong>Important:</strong> This tool provides a probability estimate, not a definitive verdict.
            Always verify with multiple sources and apply critical thinking before drawing conclusions.
          </div>

          <button className="scan-btn" onClick={reset} style={{ background: "transparent", border: "1px solid var(--border)", color: "var(--text-secondary)" }}>
            Scan another file
          </button>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// APP ROOT
// ─────────────────────────────────────────────────────────────────────────────
export default function App() {
  const [tab, setTab] = useState("academy");
  const [totalScore, setTotalScore] = useState(0);

  const handleScoreUpdate = (pts) => setTotalScore(s => s + pts);

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <div className="header-brand">
          <div className="brand-icon">🔍</div>
          <div>
            <h1>Deepfake Detective</h1>
            <span className="brand-sub">UNESCO MIL Hackathon 2026</span>
          </div>
        </div>
        {totalScore > 0 && (
          <div className="score-badge">
            <Icon name="trophy" size={16}/>
            <span>{totalScore} pts</span>
          </div>
        )}
      </header>

      {/* Tab bar */}
      <nav className="tab-bar">
        <button className={`tab-btn ${tab === "academy" ? "active" : ""}`} onClick={() => setTab("academy")}>
          <Icon name="academy" size={18}/>
          <span>The Academy</span>
        </button>
        <button className={`tab-btn ${tab === "scanner" ? "active" : ""}`} onClick={() => setTab("scanner")}>
          <Icon name="scan" size={18}/>
          <span>The Scanner</span>
        </button>
      </nav>

      {/* Main content */}
      <main className="app-main">
        {tab === "academy"
          ? <AcademyMode totalScore={totalScore} onScoreUpdate={handleScoreUpdate}/>
          : <ScannerMode/>
        }
      </main>

      <footer className="app-footer">
        <p>Built for Media & Information Literacy · Deepfakes affect democracy · Always verify before you share</p>
      </footer>
    </div>
  );
}
