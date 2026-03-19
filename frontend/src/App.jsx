import { useEffect, useState } from "react";
import PipelineView from "./components/PipelineView";
import SourcePanel from "./components/SourcePanel";
import GeneratePanel from "./components/GeneratePanel";
import ScorePanel from "./components/ScorePanel";
import PackagePanel from "./components/PackagePanel";
import AuditTrail from "./components/AuditTrail";

const TABS = [
  { id: "pipeline", label: "Overview", icon: "▦" },
  { id: "source", label: "Sourcing", icon: "◎" },
  { id: "generate", label: "Generation", icon: "✦" },
  { id: "score", label: "Scoring", icon: "◈" },
  { id: "package", label: "Package", icon: "▣" },
  { id: "audit", label: "Audit Trail", icon: "≡" },
];

const TRIGGER_LABELS = {
  seasonal_spring: "🌸 Seasonal Spring",
  seasonal_winter: "❄️ Seasonal Winter",
  event_viral_trend: "🔥 Viral Trend",
  event_competitor_launch: "⚡ Competitor Launch",
  scheduled: "🕐 Scheduled",
  manual: "🎯 Manual",
};

const PRODUCTS = {
  ceramidin_cream: { label: "Ceramidin™ Cream", sub: "Skin Barrier Moisturizer" },
  cicapair_treatment: { label: "Cicapair™ Treatment", sub: "Tiger Grass Color Correcting" },
  dermask_micro_jet: { label: "Dermask™ Micro Jet", sub: "Clearing Solution" },
};

const MODELS = {
  "claude-haiku-3-5-20241022": "Claude Haiku 3.5",
  "claude-sonnet-4-20250514": "Claude Sonnet 4",
  "claude-opus-4-20250514": "Claude Opus 4",
};

const IMAGE_GENERATORS = {
  "midjourney-v6": "Midjourney v6",
  "flux-1.1-pro": "Flux 1.1 Pro",
  "gpt-image-1": "GPT Image 1",
};

const VIDEO_GENERATORS = {
  "runway-gen4": "Runway Gen-4",
  "veo-3": "Google Veo 3",
  "sora": "OpenAI Sora",
};

export default function App() {
  const [activeTab, setActiveTab] = useState("pipeline");
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [logs, setLogs] = useState(null);
  const [error, setError] = useState(null);
  const [trigger, setTrigger] = useState("seasonal_spring");
  const [product, setProduct] = useState("ceramidin_cream");
  const [generationModel, setGenerationModel] = useState("claude-sonnet-4-20250514");
  const [judgeModel, setJudgeModel] = useState("claude-sonnet-4-20250514");
  const [imageGenerator, setImageGenerator] = useState("midjourney-v6");
  const [videoGenerator, setVideoGenerator] = useState("runway-gen4");
  const [modelMenuOpen, setModelMenuOpen] = useState(false);
  const [optionLists, setOptionLists] = useState({
    generation_models: Object.keys(MODELS),
    judge_models: Object.keys(MODELS),
    image_generators: Object.keys(IMAGE_GENERATORS),
    video_generators: Object.keys(VIDEO_GENERATORS),
  });

  useEffect(() => {
    let cancelled = false;
    fetch("/api/models")
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (!data || cancelled) return;
        setOptionLists({
          generation_models: data.generation_models || Object.keys(MODELS),
          judge_models: data.judge_models || Object.keys(MODELS),
          image_generators: data.image_generators || Object.keys(IMAGE_GENERATORS),
          video_generators: data.video_generators || Object.keys(VIDEO_GENERATORS),
        });

        if (data.defaults?.generation_model) setGenerationModel(data.defaults.generation_model);
        if (data.defaults?.judge_model) setJudgeModel(data.defaults.judge_model);
        if (data.defaults?.image_generator) setImageGenerator(data.defaults.image_generator);
        if (data.defaults?.video_generator) setVideoGenerator(data.defaults.video_generator);
      })
      .catch(() => {
        // Silent fallback to local constants if backend option endpoint is unavailable.
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const handleRun = async () => {
    setRunning(true);
    setError(null);
    setResult(null);
    setLogs(null);
    try {
      const runRes = await fetch("/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          trigger,
          product,
          generation_model: generationModel,
          judge_model: judgeModel,
          image_generator: imageGenerator,
          video_generator: videoGenerator,
        }),
      }).then(r => r.json());

      const runId = runRes.run_id;

      let attempts = 0;
      const maxAttempts = 120;
      while (attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 2000));
        attempts++;

        const statusRes = await fetch(`/api/status/${runId}`).then(r => r.json());

        if (statusRes.status === "complete") {
          const actualId = statusRes.run_id;
          const fullResult = await fetch(`/api/result/${actualId}`).then(r => r.json());
          const fullLogs = await fetch(`/api/logs/${actualId}`).then(r => r.json());
          setResult(fullResult);
          setLogs(fullLogs);
          setRunning(false);
          return;
        } else if (statusRes.status === "failed") {
          setError(`Pipeline failed: ${statusRes.error}`);
          setRunning(false);
          return;
        }
      }

      setError("Pipeline timed out after 2 minutes");
    } catch (e) {
      setError(e.message);
    }
    setRunning(false);
  };

  const meta = result?.campaign_metadata || {};
  const allPassed = meta.assets_passed === 4;

  return (
    <div style={{ display: "flex", height: "100vh", background: "var(--bg-primary)" }}>
      {/* Sidebar */}
      <div style={{
        width: 260,
        background: "var(--bg-secondary)",
        borderRight: "1px solid var(--border)",
        display: "flex",
        flexDirection: "column",
        flexShrink: 0,
        boxShadow: "2px 0 8px rgba(0,0,0,0.04)",
        overflowY: "auto",
      }}>
        {/* Brand header */}
        <div style={{
          padding: "24px 20px 20px",
          background: "var(--gradient-brand)",
          position: "relative",
          overflow: "hidden",
        }}>
          <div style={{
            position: "absolute", top: -20, right: -20,
            width: 80, height: 80, borderRadius: "50%",
            background: "rgba(255,255,255,0.08)"
          }} />
          <div style={{
            position: "absolute", bottom: -30, right: 20,
            width: 60, height: 60, borderRadius: "50%",
            background: "rgba(255,255,255,0.06)"
          }} />
          <div style={{ fontSize: 11, fontWeight: 700, color: "rgba(255,255,255,0.7)", letterSpacing: 2, textTransform: "uppercase", marginBottom: 4 }}>
            Dr. Jart+ × Pencil
          </div>
          <div style={{ fontSize: 16, fontWeight: 800, color: "#ffffff", lineHeight: 1.2, marginBottom: 2 }}>
            AI Content Pipeline
          </div>
          <div style={{ fontSize: 11, color: "rgba(255,255,255,0.6)" }}>v1.0 · Model Selectable</div>
        </div>

        {/* Product selector */}
        <div style={{ padding: "16px 16px 0" }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: "var(--text-muted)", marginBottom: 8, textTransform: "uppercase", letterSpacing: 0.8 }}>Anchor Product</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {Object.entries(PRODUCTS).map(([key, p]) => {
              const isSelected = product === key;
              return (
                <button
                  key={key}
                  onClick={() => setProduct(key)}
                  style={{
                    padding: "9px 12px",
                    borderRadius: 8,
                    border: `1px solid ${isSelected ? "var(--accent)" : "var(--border)"}`,
                    background: isSelected ? "var(--accent-light)" : "transparent",
                    color: isSelected ? "var(--accent)" : "var(--text-secondary)",
                    fontSize: 12,
                    fontWeight: isSelected ? 700 : 500,
                    textAlign: "left",
                    cursor: "pointer",
                    transition: "all 0.15s",
                  }}
                >
                  <div>{p.label}</div>
                  <div style={{ fontSize: 10, color: isSelected ? "var(--accent)" : "var(--text-muted)", marginTop: 1, fontWeight: 400, opacity: 0.8 }}>{p.sub}</div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Trigger selector + Run */}
        <div style={{ padding: "16px 16px 12px" }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: "var(--text-muted)", marginBottom: 8, textTransform: "uppercase", letterSpacing: 0.8 }}>Campaign Trigger</div>
          <select
            value={trigger}
            onChange={e => setTrigger(e.target.value)}
            style={{
              width: "100%",
              padding: "9px 12px",
              background: "var(--bg-primary)",
              border: "1px solid var(--border)",
              color: "var(--text-primary)",
              borderRadius: 8,
              fontSize: 13,
              fontFamily: "var(--font-sans)",
              fontWeight: 500,
              outline: "none",
              cursor: "pointer",
            }}
          >
            {Object.entries(TRIGGER_LABELS).map(([val, label]) => (
              <option key={val} value={val}>{label}</option>
            ))}
          </select>
          <div style={{ marginTop: 10 }}>
            <button
              onClick={() => setModelMenuOpen(v => !v)}
              style={{
                width: "100%",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "9px 12px",
                background: "var(--bg-primary)",
                border: "1px solid var(--border)",
                color: "var(--text-primary)",
                borderRadius: 8,
                fontSize: 12,
                fontWeight: 700,
                letterSpacing: 0.4,
                textTransform: "uppercase",
                cursor: "pointer",
              }}
            >
              <span>Model Settings</span>
              <span style={{ fontSize: 14, opacity: 0.8 }}>{modelMenuOpen ? "▾" : "▸"}</span>
            </button>

            {modelMenuOpen && (
              <div style={{ marginTop: 10 }}>
                <div style={{ fontSize: 11, fontWeight: 600, color: "var(--text-muted)", margin: "0 0 8px", textTransform: "uppercase", letterSpacing: 0.8 }}>Prompt Generation Model</div>
                <select
                  value={generationModel}
                  onChange={e => setGenerationModel(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "9px 12px",
                    background: "var(--bg-primary)",
                    border: "1px solid var(--border)",
                    color: "var(--text-primary)",
                    borderRadius: 8,
                    fontSize: 13,
                    fontFamily: "var(--font-sans)",
                    fontWeight: 500,
                    outline: "none",
                    cursor: "pointer",
                  }}
                >
                  {optionLists.generation_models.map((val) => (
                    <option key={val} value={val}>{MODELS[val] || val}</option>
                  ))}
                </select>

                <div style={{ fontSize: 11, fontWeight: 600, color: "var(--text-muted)", margin: "10px 0 8px", textTransform: "uppercase", letterSpacing: 0.8 }}>Judge Model</div>
                <select
                  value={judgeModel}
                  onChange={e => setJudgeModel(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "9px 12px",
                    background: "var(--bg-primary)",
                    border: "1px solid var(--border)",
                    color: "var(--text-primary)",
                    borderRadius: 8,
                    fontSize: 13,
                    fontFamily: "var(--font-sans)",
                    fontWeight: 500,
                    outline: "none",
                    cursor: "pointer",
                  }}
                >
                  {optionLists.judge_models.map((val) => (
                    <option key={val} value={val}>{MODELS[val] || val}</option>
                  ))}
                </select>

                <div style={{ fontSize: 11, fontWeight: 600, color: "var(--text-muted)", margin: "10px 0 8px", textTransform: "uppercase", letterSpacing: 0.8 }}>Image Generator</div>
                <select
                  value={imageGenerator}
                  onChange={e => setImageGenerator(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "9px 12px",
                    background: "var(--bg-primary)",
                    border: "1px solid var(--border)",
                    color: "var(--text-primary)",
                    borderRadius: 8,
                    fontSize: 13,
                    fontFamily: "var(--font-sans)",
                    fontWeight: 500,
                    outline: "none",
                    cursor: "pointer",
                  }}
                >
                  {optionLists.image_generators.map((val) => (
                    <option key={val} value={val}>{IMAGE_GENERATORS[val] || val}</option>
                  ))}
                </select>

                <div style={{ fontSize: 11, fontWeight: 600, color: "var(--text-muted)", margin: "10px 0 8px", textTransform: "uppercase", letterSpacing: 0.8 }}>Video Generator</div>
                <select
                  value={videoGenerator}
                  onChange={e => setVideoGenerator(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "9px 12px",
                    background: "var(--bg-primary)",
                    border: "1px solid var(--border)",
                    color: "var(--text-primary)",
                    borderRadius: 8,
                    fontSize: 13,
                    fontFamily: "var(--font-sans)",
                    fontWeight: 500,
                    outline: "none",
                    cursor: "pointer",
                  }}
                >
                  {optionLists.video_generators.map((val) => (
                    <option key={val} value={val}>{VIDEO_GENERATORS[val] || val}</option>
                  ))}
                </select>
              </div>
            )}
          </div>
          <button
            onClick={handleRun}
            disabled={running}
            style={{
              width: "100%",
              marginTop: 10,
              padding: "11px",
              borderRadius: 10,
              border: "none",
              background: running ? "var(--border)" : "var(--gradient-brand)",
              color: running ? "var(--text-muted)" : "#fff",
              fontSize: 14,
              fontWeight: 700,
              letterSpacing: 0.3,
              boxShadow: running ? "none" : "0 4px 14px rgba(99,102,241,0.4)",
              transition: "all 0.2s",
            }}
          >
            {running ? "⏳  Running Pipeline..." : "▶  Run Pipeline"}
          </button>
        </div>

        {/* Status pill */}
        {meta.status && (
          <div style={{ margin: "0 16px 12px", padding: "12px 14px", borderRadius: 10, background: allPassed ? "var(--accent-green-light)" : "var(--accent-yellow-light)", border: `1px solid ${allPassed ? "#6ee7b7" : "#fcd34d"}` }}>
            <div style={{ fontSize: 11, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 0.8, marginBottom: 4 }}>Last Run</div>
            <div style={{ fontSize: 13, fontWeight: 700, color: allPassed ? "var(--accent-green)" : "var(--accent-yellow)" }}>{meta.status}</div>
            <div style={{ fontSize: 12, color: "var(--text-secondary)", marginTop: 2 }}>
              {meta.assets_passed}/4 assets passed · {meta.total_iterations} iterations
            </div>
          </div>
        )}

        {/* Navigation */}
        <div style={{ flex: 1, padding: "4px 10px" }}>
          {TABS.map(t => {
            const isActive = activeTab === t.id;
            return (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id)}
                style={{
                  width: "100%",
                  padding: "10px 12px",
                  marginBottom: 2,
                  borderRadius: 8,
                  border: "none",
                  background: isActive ? "var(--accent-light)" : "transparent",
                  color: isActive ? "var(--accent)" : "var(--text-secondary)",
                  fontSize: 13,
                  fontWeight: isActive ? 700 : 500,
                  textAlign: "left",
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  transition: "all 0.15s",
                }}
              >
                <span style={{ fontSize: 14, opacity: isActive ? 1 : 0.6 }}>{t.icon}</span>
                {t.label}
                {isActive && <span style={{ marginLeft: "auto", width: 6, height: 6, borderRadius: "50%", background: "var(--accent)", flexShrink: 0 }} />}
              </button>
            );
          })}
        </div>

        {/* Footer */}
        <div style={{ padding: "12px 16px", borderTop: "1px solid var(--border)" }}>
          <div style={{ fontSize: 11, color: "var(--text-muted)", lineHeight: 1.7 }}>
            <span style={{ display: "block", fontWeight: 600, color: "var(--text-secondary)" }}>{PRODUCTS[product]?.label}</span>
            Anchor product · Dr. Jart+
            <span style={{ display: "block", marginTop: 4 }}>Gen: {MODELS[generationModel] || generationModel} · Judge: {MODELS[judgeModel] || judgeModel}</span>
            <span style={{ display: "block", marginTop: 2 }}>Img: {IMAGE_GENERATORS[imageGenerator] || imageGenerator} · Vid: {VIDEO_GENERATORS[videoGenerator] || videoGenerator}</span>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div style={{ flex: 1, overflow: "auto", padding: "32px 36px" }}>
        {error && (
          <div style={{
            background: "var(--accent-red-light)",
            border: "1px solid #fca5a5",
            borderRadius: 12,
            padding: "14px 18px",
            marginBottom: 24,
            color: "var(--accent-red)",
            fontSize: 13,
            fontWeight: 500,
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}>
            <span style={{ fontSize: 16 }}>⚠</span> {error}
          </div>
        )}

        {activeTab === "pipeline" && <PipelineView result={result} running={running} />}
        {activeTab === "source" && <SourcePanel result={result} />}
        {activeTab === "generate" && <GeneratePanel result={result} />}
        {activeTab === "score" && <ScorePanel result={result} />}
        {activeTab === "package" && <PackagePanel result={result} />}
        {activeTab === "audit" && <AuditTrail logs={logs} />}
      </div>
    </div>
  );
}
