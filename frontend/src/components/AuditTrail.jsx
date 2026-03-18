import { useState } from "react";

export default function AuditTrail({ logs }) {
  const entries = logs?.entries || [];
  const [expanded, setExpanded] = useState(null);

  const actionColors = {
    llm_call: "#64b5f6",
    format_compliance_check: "#ffc107",
    composite_score_calculated: "#ce93d8",
    load_and_filter: "#00d4aa",
    sufficiency_evaluation: "#00d4aa",
    narratives_generated: "#64b5f6",
    skipped_passed_asset: "#5a6785",
    judge_parse_failure: "#ff5252",
    generation_failed: "#ff5252",
    bundle_assembled: "#ce93d8",
    retry: "#ffc107",
    all_passed: "#00d4aa",
    pattern_failure: "#ff5252",
  };

  return (
    <div>
      <h2 style={{ fontSize: 22, fontWeight: 800, color: "var(--text-primary)", marginBottom: 4 }}>Audit Trail</h2>
      <p style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 24 }}>
        Complete pipeline transparency — every node, every decision, every LLM call
      </p>

      <div style={{ fontSize: 12, color: "var(--text-secondary)", marginBottom: 16 }}>
        {entries.length} entries recorded
      </div>

      {entries.map((entry, i) => {
        const color = actionColors[entry.action] || "var(--text-muted)";
        const isExpanded = expanded === i;

        return (
          <div key={i} onClick={() => setExpanded(isExpanded ? null : i)} style={{ background: "var(--bg-card)", borderRadius: 8, padding: 12, marginBottom: 4, border: `1px solid ${isExpanded ? color + "44" : "var(--border)"}`, cursor: "pointer", transition: "border-color 0.2s" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <span style={{ width: 8, height: 8, borderRadius: "50%", background: color, flexShrink: 0 }} />
                <span style={{ fontSize: 12, fontWeight: 600, color: "var(--text-primary)" }}>{entry.node}</span>
                <span style={{ fontSize: 11, color, fontWeight: 600 }}>{entry.action}</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                {entry.latency_ms && <span style={{ fontSize: 10, color: "var(--text-muted)" }}>{entry.latency_ms}ms</span>}
                {entry.model_used && <span style={{ fontSize: 10, color: "var(--text-muted)" }}>{entry.model_used.split("-").slice(-1)[0]}</span>}
                <span style={{ fontSize: 10, color: "var(--text-muted)" }}>{isExpanded ? "▼" : "▶"}</span>
              </div>
            </div>

            {isExpanded && (
              <div style={{ marginTop: 12, paddingTop: 12, borderTop: "1px solid var(--border)" }}>
                {entry.input_snapshot && Object.keys(entry.input_snapshot).length > 0 && (
                  <div style={{ marginBottom: 8 }}>
                    <div style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", marginBottom: 4 }}>INPUT</div>
                    <pre style={{ fontSize: 10, color: "var(--text-secondary)", whiteSpace: "pre-wrap", lineHeight: 1.5 }}>{JSON.stringify(entry.input_snapshot, null, 2)}</pre>
                  </div>
                )}
                {entry.output_snapshot && Object.keys(entry.output_snapshot).length > 0 && (
                  <div style={{ marginBottom: 8 }}>
                    <div style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", marginBottom: 4 }}>OUTPUT</div>
                    <pre style={{ fontSize: 10, color: "#5a9e6f", whiteSpace: "pre-wrap", lineHeight: 1.5 }}>{JSON.stringify(entry.output_snapshot, null, 2)}</pre>
                  </div>
                )}
                {entry.metadata && Object.keys(entry.metadata).length > 0 && (
                  <div>
                    <div style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", marginBottom: 4 }}>METADATA</div>
                    <pre style={{ fontSize: 10, color: "var(--accent-yellow)", whiteSpace: "pre-wrap", lineHeight: 1.5 }}>{JSON.stringify(entry.metadata, null, 2)}</pre>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}

      {entries.length === 0 && (
        <div style={{ color: "var(--text-muted)", fontSize: 12, padding: 40, textAlign: "center" }}>Run the pipeline to see the audit trail</div>
      )}
    </div>
  );
}
