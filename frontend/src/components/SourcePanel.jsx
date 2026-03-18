export default function SourcePanel({ result }) {
  const meta = result?.campaign_metadata || {};
  const narratives = result?.trend_narratives || [];

  // Get source info from audit log
  const sourceAudit = (result?.audit_log || []).find(e => e?.node === "source_collect") || (result ? {} : null);

  return (
    <div>
      <h2 style={{ fontSize: 22, fontWeight: 800, color: "var(--text-primary)", marginBottom: 4 }}>Phase 1: Sourcing</h2>
      <p style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 24 }}>Trend Scout Agent — identifies, filters, and structures public trend data</p>

      {/* Evidence decision */}
      <div style={{ display: "flex", gap: 12, marginBottom: 24 }}>
        <InfoCard label="Records" value={meta.sourced_records_count || "—"} />
        <InfoCard label="Synthetic" value={meta.synthetic_records_count || 0} />
        <InfoCard label="Evidence" value={meta.evidence_decision || "—"} color={meta.evidence_decision === "sufficient" ? "#00d4aa" : "#ffc107"} />
      </div>

      {/* Narratives */}
      <div style={{ fontSize: 15, fontWeight: 700, color: "var(--text-primary)", marginBottom: 12 }}>Trend Narratives</div>
      {narratives.length > 0 ? narratives.map((n, i) => (
        <div key={i} style={{ background: "var(--bg-card)", borderRadius: 8, padding: 12, marginBottom: 8, borderLeft: "3px solid var(--accent-blue)", fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.6 }}>
          <span style={{ color: "var(--accent-blue)", fontWeight: 700 }}>Narrative {i+1}:</span> {n}
        </div>
      )) : (
        <div style={{ color: "var(--text-muted)", fontSize: 12 }}>Run the pipeline to see narratives</div>
      )}
    </div>
  );
}

function InfoCard({ label, value, color = "var(--text-primary)" }) {
  return (
    <div style={{ background: "var(--bg-card)", borderRadius: 8, padding: 12, flex: 1, border: "1px solid var(--border)" }}>
      <div style={{ fontSize: 10, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 1, marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 18, fontWeight: 700, color }}>{value}</div>
    </div>
  );
}
