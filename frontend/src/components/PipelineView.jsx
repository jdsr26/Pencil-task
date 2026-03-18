export default function PipelineView({ result, running }) {
  const meta = result?.campaign_metadata || {};

  const steps = [
    { name: "Source & Collect", desc: "Load + filter trend data", color: "#10b981", bg: "#d1fae5", phase: "Phase 1" },
    { name: "Evidence Check", desc: "Sufficiency gate", color: "#10b981", bg: "#d1fae5", phase: "Phase 1" },
    { name: "Narrative Synthesis", desc: "Distill 3 trend narratives", color: "#0ea5e9", bg: "#e0f2fe", phase: "Phase 1" },
    { name: "Generate Assets", desc: "4 creative agents", color: "#6366f1", bg: "#eef2ff", phase: "Phase 2" },
    { name: "Format Scoring", desc: "Rule-based format checks", color: "#f59e0b", bg: "#fef3c7", phase: "Phase 3" },
    { name: "LLM Judge", desc: "Brand + trend alignment", color: "#f59e0b", bg: "#fef3c7", phase: "Phase 3" },
    { name: "Route Decision", desc: "Pass / retry / diagnose", color: "#8b5cf6", bg: "#ede9fe", phase: "Phase 3" },
    { name: "Package", desc: "Bundle deliverables", color: "#8b5cf6", bg: "#ede9fe", phase: "Phase 4" },
  ];

  return (
    <div>
      {/* Hero header */}
      <div style={{
        background: "var(--gradient-hero)",
        borderRadius: 16,
        padding: "28px 32px",
        marginBottom: 28,
        position: "relative",
        overflow: "hidden",
      }}>
        <div style={{ position: "absolute", top: -40, right: -40, width: 160, height: 160, borderRadius: "50%", background: "rgba(255,255,255,0.07)" }} />
        <div style={{ position: "absolute", bottom: -20, right: 80, width: 80, height: 80, borderRadius: "50%", background: "rgba(255,255,255,0.05)" }} />
        <div style={{ fontSize: 12, fontWeight: 600, color: "rgba(255,255,255,0.7)", textTransform: "uppercase", letterSpacing: 1.2, marginBottom: 8 }}>
          Dr. Jart+ AI Content Pipeline
        </div>
        <h1 style={{ fontSize: 28, fontWeight: 900, color: "#ffffff", marginBottom: 8, lineHeight: 1.2 }}>
          Scalable Creative Intelligence
        </h1>
        <p style={{ fontSize: 14, color: "rgba(255,255,255,0.75)", maxWidth: 520, lineHeight: 1.6 }}>
          Specialized AI agents source trends, generate brand-safe creative, score quality, and deliver campaign-ready assets — fully automated.
        </p>
      </div>

      {/* Metrics row (post-run) */}
      {meta.status && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14, marginBottom: 28 }}>
          <MetricCard
            label="Pipeline Status"
            value={meta.status}
            color={meta.assets_passed === 4 ? "var(--accent-green)" : "var(--accent-yellow)"}
            bg={meta.assets_passed === 4 ? "var(--accent-green-light)" : "var(--accent-yellow-light)"}
            icon="◎"
          />
          <MetricCard
            label="Assets Passed"
            value={`${meta.assets_passed} / 4`}
            color={meta.assets_passed === 4 ? "var(--accent-green)" : "var(--accent-red)"}
            bg={meta.assets_passed === 4 ? "var(--accent-green-light)" : "var(--accent-red-light)"}
            icon="✓"
          />
          <MetricCard
            label="Source Records"
            value={meta.sourced_records_count ?? "—"}
            color="var(--accent-blue)"
            bg="var(--accent-blue-light)"
            icon="◈"
          />
          <MetricCard
            label="Total Iterations"
            value={meta.total_iterations ?? "—"}
            color="var(--accent-purple)"
            bg="var(--accent-purple-light)"
            icon="↺"
          />
        </div>
      )}

      {/* Pipeline steps */}
      <div style={{ marginBottom: 8 }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: 1, marginBottom: 14 }}>
          Pipeline Architecture
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10 }}>
          {steps.map((s, i) => (
            <div key={i} style={{
              background: "var(--bg-card)",
              borderRadius: 12,
              padding: "14px 16px",
              border: "1px solid var(--border)",
              boxShadow: "var(--shadow-sm)",
              position: "relative",
              overflow: "hidden",
            }}>
              <div style={{
                position: "absolute", top: 0, left: 0, right: 0, height: 3,
                background: s.color,
                borderRadius: "12px 12px 0 0",
              }} />
              <div style={{
                display: "inline-block",
                padding: "2px 8px",
                borderRadius: 20,
                fontSize: 10,
                fontWeight: 700,
                color: s.color,
                background: s.bg,
                marginBottom: 8,
                textTransform: "uppercase",
                letterSpacing: 0.5,
              }}>{s.phase}</div>
              <div style={{ fontSize: 13, fontWeight: 700, color: "var(--text-primary)", marginBottom: 3 }}>{s.name}</div>
              <div style={{ fontSize: 11, color: "var(--text-muted)" }}>{s.desc}</div>
              <div style={{
                position: "absolute", bottom: 10, right: 12,
                fontSize: 20, fontWeight: 900,
                color: s.bg === "#d1fae5" ? "#6ee7b7" : s.bg === "#e0f2fe" ? "#7dd3fc" : s.bg === "#eef2ff" ? "#a5b4fc" : s.bg === "#fef3c7" ? "#fcd34d" : "#c4b5fd",
              }}>{String(i + 1).padStart(2, "0")}</div>
            </div>
          ))}
        </div>
      </div>

      {meta.failure_diagnosis && (
        <div style={{ marginTop: 20, background: "var(--accent-yellow-light)", border: "1px solid #fcd34d", borderRadius: 12, padding: "16px 20px" }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: "var(--accent-yellow)", marginBottom: 6 }}>⚠ Failure Diagnosis</div>
          <div style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.6 }}>{meta.failure_diagnosis}</div>
        </div>
      )}

      {!result && !running && (
        <div style={{ textAlign: "center", padding: "60px 40px", color: "var(--text-muted)" }}>
          <div style={{
            width: 64, height: 64, borderRadius: 16, background: "var(--accent-light)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 28, margin: "0 auto 16px",
          }}>▶</div>
          <div style={{ fontSize: 15, fontWeight: 600, color: "var(--text-secondary)", marginBottom: 6 }}>Ready to run</div>
          <div style={{ fontSize: 13 }}>Select a campaign trigger and click "Run Pipeline"</div>
        </div>
      )}

      {running && (
        <div style={{ textAlign: "center", padding: "60px 40px" }}>
          <div style={{
            width: 64, height: 64, borderRadius: "50%",
            background: "var(--gradient-brand)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 24, margin: "0 auto 16px",
            animation: "spin 2s linear infinite",
          }}>⏳</div>
          <div style={{ fontSize: 15, fontWeight: 600, color: "var(--accent)", marginBottom: 6 }}>Pipeline running...</div>
          <div style={{ fontSize: 13, color: "var(--text-muted)" }}>AI agents are generating your campaign assets</div>
        </div>
      )}
    </div>
  );
}

function MetricCard({ label, value, color, bg, icon }) {
  return (
    <div style={{
      background: "var(--bg-card)",
      borderRadius: 14,
      padding: "18px 20px",
      border: "1px solid var(--border)",
      boxShadow: "var(--shadow-sm)",
    }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 0.8 }}>{label}</div>
        <div style={{ width: 30, height: 30, borderRadius: 8, background: bg, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14, color }}>{icon}</div>
      </div>
      <div style={{ fontSize: 24, fontWeight: 800, color }}>{value}</div>
    </div>
  );
}
