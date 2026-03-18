import { useState, useEffect } from "react";
import { runPipeline, getResult, getLogs, listRuns } from "./api/client";
import PipelineView from "./components/PipelineView";
import SourcePanel from "./components/SourcePanel";
import GeneratePanel from "./components/GeneratePanel";
import ScorePanel from "./components/ScorePanel";
import PackagePanel from "./components/PackagePanel";
import AuditTrail from "./components/AuditTrail";

const TABS = [
  { id: "pipeline", label: "Pipeline", icon: "⚡" },
  { id: "source", label: "Sourcing", icon: "🔍" },
  { id: "generate", label: "Generation", icon: "🧠" },
  { id: "score", label: "Scoring", icon: "✅" },
  { id: "package", label: "Package", icon: "📦" },
  { id: "audit", label: "Audit Trail", icon: "📋" },
];

export default function App() {
  const [activeTab, setActiveTab] = useState("pipeline");
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [logs, setLogs] = useState(null);
  const [error, setError] = useState(null);
  const [trigger, setTrigger] = useState("seasonal_spring");

  const handleRun = async () => {
    setRunning(true);
    setError(null);
    setResult(null);
    setLogs(null);
    try {
      // Start the pipeline (returns immediately)
      const runRes = await fetch("/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ trigger }),
      }).then(r => r.json());

      const runId = runRes.run_id;

      // Poll for completion
      let attempts = 0;
      const maxAttempts = 120; // 2 minutes max
      while (attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds
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
        // Still running — continue polling
      }

      setError("Pipeline timed out after 2 minutes");
    } catch (e) {
      setError(e.message);
    }
    setRunning(false);
  };

  const meta = result?.campaign_metadata || {};

  return (
    <div style={{ display: "flex", height: "100vh" }}>
      {/* Sidebar */}
      <div style={{ width: 220, background: "var(--bg-secondary)", borderRight: "1px solid var(--border)", display: "flex", flexDirection: "column", flexShrink: 0 }}>
        <div style={{ padding: "20px 16px", borderBottom: "1px solid var(--border)" }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: "var(--accent)", letterSpacing: 2, textTransform: "uppercase" }}>Dr. Jart+ × Pencil</div>
          <div style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 4 }}>AI Content Pipeline v1.0</div>
        </div>

        {/* Trigger selector */}
        <div style={{ padding: "12px 16px", borderBottom: "1px solid var(--border)" }}>
          <div style={{ fontSize: 10, color: "var(--text-muted)", marginBottom: 6, textTransform: "uppercase", letterSpacing: 1 }}>Trigger</div>
          <select value={trigger} onChange={e => setTrigger(e.target.value)} style={{ width: "100%", padding: "6px 8px", background: "var(--bg-card)", border: "1px solid var(--border)", color: "var(--text-primary)", borderRadius: 4, fontSize: 11, fontFamily: "var(--font-mono)" }}>
            <option value="seasonal_spring">Seasonal Spring</option>
            <option value="seasonal_winter">Seasonal Winter</option>
            <option value="event_viral_trend">Viral Trend</option>
            <option value="event_competitor_launch">Competitor Launch</option>
            <option value="scheduled">Scheduled</option>
            <option value="manual">Manual</option>
          </select>
          <button onClick={handleRun} disabled={running} style={{ width: "100%", marginTop: 8, padding: "10px", borderRadius: 6, border: "none", background: running ? "var(--border)" : "linear-gradient(135deg, #00d4aa, #00a8cc)", color: "#fff", fontSize: 12, fontWeight: 700 }}>
            {running ? "⏳ Running..." : "🚀 Run Pipeline"}
          </button>
        </div>

        {/* Status */}
        {meta.status && (
          <div style={{ padding: "12px 16px", borderBottom: "1px solid var(--border)", fontSize: 11 }}>
            <div style={{ color: "var(--text-muted)", marginBottom: 4 }}>Status</div>
            <div style={{ color: meta.assets_passed === 4 ? "var(--accent)" : "var(--accent-yellow)", fontWeight: 700 }}>{meta.status}</div>
            <div style={{ color: "var(--text-secondary)", marginTop: 4 }}>
              {meta.assets_passed}/4 passed · {meta.total_iterations} iterations
            </div>
          </div>
        )}

        {/* Nav tabs */}
        <div style={{ flex: 1, padding: "12px 8px" }}>
          {TABS.map(t => (
            <button key={t.id} onClick={() => setActiveTab(t.id)} style={{ width: "100%", padding: "10px 12px", marginBottom: 4, borderRadius: 8, border: "none", background: activeTab === t.id ? "var(--bg-card)" : "transparent", color: activeTab === t.id ? "var(--accent)" : "var(--text-muted)", fontSize: 12, fontWeight: 600, textAlign: "left" }}>
              <span style={{ marginRight: 8 }}>{t.icon}</span>{t.label}
            </button>
          ))}
        </div>

        <div style={{ padding: 16, borderTop: "1px solid var(--border)", fontSize: 10, color: "var(--text-muted)" }}>
          <div>Anchor: Ceramidin™ Cream</div>
          <div>Model: Claude Sonnet 4</div>
        </div>
      </div>

      {/* Main content */}
      <div style={{ flex: 1, overflow: "auto", padding: 32 }}>
        {error && <div style={{ background: "#ff525222", border: "1px solid var(--accent-red)", borderRadius: 8, padding: 16, marginBottom: 20, color: "var(--accent-red)", fontSize: 12 }}>Error: {error}</div>}

        {activeTab === "pipeline" && <PipelineView result={result} />}
        {activeTab === "source" && <SourcePanel result={result} />}
        {activeTab === "generate" && <GeneratePanel result={result} />}
        {activeTab === "score" && <ScorePanel result={result} />}
        {activeTab === "package" && <PackagePanel result={result} />}
        {activeTab === "audit" && <AuditTrail logs={logs} />}
      </div>
    </div>
  );
}
