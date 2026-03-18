export default function SourcePanel({ result }) {
  const meta = result?.campaign_metadata || {};
  const narratives = result?.trend_narratives || [];

  return (
    <div>
      <PageHeader
        phase="Phase 1"
        title="Trend Sourcing"
        desc="The Trend Scout Agent identifies, filters, and structures public trend data to fuel the creative pipeline."
        color="var(--accent-green)"
        bg="var(--accent-green-light)"
      />

      {/* Stats row */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 14, marginBottom: 28 }}>
        <StatCard
          label="Records Sourced"
          value={meta.sourced_records_count ?? "—"}
          color="var(--accent-blue)"
          bg="var(--accent-blue-light)"
          icon="◈"
        />
        <StatCard
          label="Synthetic Records"
          value={meta.synthetic_records_count ?? 0}
          color="var(--accent-purple)"
          bg="var(--accent-purple-light)"
          icon="✦"
        />
        <StatCard
          label="Evidence Decision"
          value={meta.evidence_decision ?? "—"}
          color={meta.evidence_decision === "sufficient" ? "var(--accent-green)" : "var(--accent-yellow)"}
          bg={meta.evidence_decision === "sufficient" ? "var(--accent-green-light)" : "var(--accent-yellow-light)"}
          icon={meta.evidence_decision === "sufficient" ? "✓" : "⚠"}
        />
      </div>

      {/* Narratives */}
      <div style={{ fontSize: 13, fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: 1, marginBottom: 14 }}>
        Trend Narratives
      </div>

      {narratives.length > 0 ? narratives.map((n, i) => (
        <div key={i} style={{
          background: "var(--bg-card)",
          borderRadius: 12,
          padding: "18px 20px",
          marginBottom: 10,
          border: "1px solid var(--border)",
          boxShadow: "var(--shadow-sm)",
          display: "flex",
          gap: 16,
          alignItems: "flex-start",
        }}>
          <div style={{
            width: 32, height: 32, borderRadius: 8, flexShrink: 0,
            background: "var(--accent-blue-light)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 13, fontWeight: 800, color: "var(--accent-blue)",
          }}>{i + 1}</div>
          <div style={{ fontSize: 14, color: "var(--text-secondary)", lineHeight: 1.7, paddingTop: 4 }}>{n}</div>
        </div>
      )) : (
        <EmptyState message="Run the pipeline to discover trend narratives" />
      )}
    </div>
  );
}

function StatCard({ label, value, color, bg, icon }) {
  return (
    <div style={{
      background: "var(--bg-card)",
      borderRadius: 14,
      padding: "18px 20px",
      border: "1px solid var(--border)",
      boxShadow: "var(--shadow-sm)",
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 0.8 }}>{label}</div>
        <div style={{ width: 30, height: 30, borderRadius: 8, background: bg, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14, color }}>{icon}</div>
      </div>
      <div style={{ fontSize: 22, fontWeight: 800, color, textTransform: "capitalize" }}>{value}</div>
    </div>
  );
}

function PageHeader({ phase, title, desc, color, bg }) {
  return (
    <div style={{ marginBottom: 28 }}>
      <div style={{ display: "inline-flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
        <span style={{ padding: "3px 10px", borderRadius: 20, fontSize: 11, fontWeight: 700, color, background: bg, textTransform: "uppercase", letterSpacing: 0.8 }}>{phase}</span>
      </div>
      <h2 style={{ fontSize: 26, fontWeight: 800, color: "var(--text-primary)", marginBottom: 6 }}>{title}</h2>
      <p style={{ fontSize: 14, color: "var(--text-muted)", maxWidth: 560, lineHeight: 1.6 }}>{desc}</p>
    </div>
  );
}

function EmptyState({ message }) {
  return (
    <div style={{ textAlign: "center", padding: "50px 40px", color: "var(--text-muted)" }}>
      <div style={{ fontSize: 32, marginBottom: 12, opacity: 0.4 }}>◎</div>
      <div style={{ fontSize: 14 }}>{message}</div>
    </div>
  );
}
