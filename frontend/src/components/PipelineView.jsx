export default function PipelineView({ result }) {
  const meta = result?.campaign_metadata || {};

  const steps = [
    { name: "Source Collect", desc: "Load + filter trend data", color: "#00d4aa" },
    { name: "Evidence Check", desc: "Sufficiency gate", color: "#00d4aa" },
    { name: "Narrative Synth", desc: "Distill 3 trend narratives", color: "#64b5f6" },
    { name: "Generate Assets", desc: "4 creative agents", color: "#64b5f6" },
    { name: "Score (Deterministic)", desc: "Rule-based format checks", color: "#ffc107" },
    { name: "Score (LLM Judge)", desc: "Brand + trend alignment", color: "#ffc107" },
    { name: "Route Decision", desc: "Pass / retry / diagnose", color: "#ce93d8" },
    { name: "Package", desc: "Bundle deliverables", color: "#ce93d8" },
  ];

  return (
    <div>
      <h1 style={{ fontSize: 28, fontWeight: 800, color: "var(--text-primary)", marginBottom: 8 }}>Scalable AI Content Pipeline</h1>
      <p style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 32, maxWidth: 600 }}>
        A chain of specialized agents that source trends, generate brand-safe creative, score quality, and package campaign-ready deliverables for Dr. Jart+.
      </p>

      {/* Pipeline steps */}
      <div style={{ display: "flex", gap: 8, marginBottom: 32, flexWrap: "wrap" }}>
        {steps.map((s, i) => (
          <div key={i} style={{ flex: "1 1 140px", background: "var(--bg-card)", borderRadius: 10, padding: 12, borderLeft: `3px solid ${s.color}` }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: s.color }}>{s.name}</div>
            <div style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 4 }}>{s.desc}</div>
          </div>
        ))}
      </div>

      {/* Results summary */}
      {meta.status && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 12 }}>
          <MetricCard label="Status" value={meta.status} color={meta.assets_passed === 4 ? "#00d4aa" : "#ffc107"} />
          <MetricCard label="Assets Passed" value={`${meta.assets_passed}/4`} color={meta.assets_passed === 4 ? "#00d4aa" : "#ff5252"} />
          <MetricCard label="Source Records" value={meta.sourced_records_count} color="#64b5f6" />
          <MetricCard label="Iterations" value={meta.total_iterations} color="#ce93d8" />
        </div>
      )}

      {meta.failure_diagnosis && (
        <div style={{ marginTop: 20, background: "#ffc10711", border: "1px solid #ffc10744", borderRadius: 10, padding: 16 }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: "var(--accent-yellow)", marginBottom: 8 }}>⚠️ Failure Diagnosis</div>
          <div style={{ fontSize: 11, color: "var(--text-secondary)", lineHeight: 1.6 }}>{meta.failure_diagnosis}</div>
        </div>
      )}

      {!result && (
        <div style={{ textAlign: "center", padding: 60, color: "var(--text-muted)" }}>
          <div style={{ fontSize: 40, marginBottom: 16 }}>⚡</div>
          <div style={{ fontSize: 14 }}>Click "Run Pipeline" to start</div>
        </div>
      )}
    </div>
  );
}

function MetricCard({ label, value, color }) {
  return (
    <div style={{ background: "var(--bg-card)", borderRadius: 10, padding: 16, border: "1px solid var(--border)" }}>
      <div style={{ fontSize: 10, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 1, marginBottom: 6 }}>{label}</div>
      <div style={{ fontSize: 20, fontWeight: 800, color }}>{value}</div>
    </div>
  );
}
