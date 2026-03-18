import { useState } from "react";

const ACTION_META = {
  llm_call: { color: "var(--accent-blue)", bg: "var(--accent-blue-light)", label: "LLM Call" },
  format_compliance_check: { color: "var(--accent-yellow)", bg: "var(--accent-yellow-light)", label: "Format Check" },
  composite_score_calculated: { color: "var(--accent-purple)", bg: "var(--accent-purple-light)", label: "Score Calculated" },
  load_and_filter: { color: "var(--accent-green)", bg: "var(--accent-green-light)", label: "Load & Filter" },
  sufficiency_evaluation: { color: "var(--accent-green)", bg: "var(--accent-green-light)", label: "Sufficiency Check" },
  narratives_generated: { color: "var(--accent-blue)", bg: "var(--accent-blue-light)", label: "Narratives Generated" },
  skipped_passed_asset: { color: "var(--text-muted)", bg: "var(--bg-primary)", label: "Skipped" },
  judge_parse_failure: { color: "var(--accent-red)", bg: "var(--accent-red-light)", label: "Parse Failure" },
  generation_failed: { color: "var(--accent-red)", bg: "var(--accent-red-light)", label: "Generation Failed" },
  bundle_assembled: { color: "var(--accent-purple)", bg: "var(--accent-purple-light)", label: "Bundle Assembled" },
  retry: { color: "var(--accent-yellow)", bg: "var(--accent-yellow-light)", label: "Retry" },
  all_passed: { color: "var(--accent-green)", bg: "var(--accent-green-light)", label: "All Passed" },
  coherence_failure: { color: "var(--accent-yellow)", bg: "var(--accent-yellow-light)", label: "Coherence Failure" },
  pattern_failure: { color: "var(--accent-red)", bg: "var(--accent-red-light)", label: "Pattern Failure" },
};

export default function AuditTrail({ logs }) {
  const entries = logs?.entries || [];
  const [expanded, setExpanded] = useState(null);

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: 26, fontWeight: 800, color: "var(--text-primary)", marginBottom: 6 }}>Audit Trail</h2>
        <p style={{ fontSize: 14, color: "var(--text-muted)", maxWidth: 560, lineHeight: 1.6 }}>
          Complete pipeline transparency — every node, every decision, every LLM call recorded.
        </p>
      </div>

      {entries.length > 0 && (
        <div style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 8,
          padding: "6px 14px",
          borderRadius: 20,
          background: "var(--accent-light)",
          marginBottom: 20,
          fontSize: 13,
          fontWeight: 600,
          color: "var(--accent)",
        }}>
          <span>≡</span> {entries.length} events recorded
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        {entries.map((entry, i) => {
          const meta = ACTION_META[entry.action] || { color: "var(--text-muted)", bg: "var(--bg-primary)", label: entry.action };
          const isExpanded = expanded === i;

          return (
            <div
              key={i}
              onClick={() => setExpanded(isExpanded ? null : i)}
              style={{
                background: "var(--bg-card)",
                borderRadius: 10,
                border: `1px solid ${isExpanded ? meta.color + "44" : "var(--border)"}`,
                overflow: "hidden",
                cursor: "pointer",
                transition: "border-color 0.15s, box-shadow 0.15s",
                boxShadow: isExpanded ? `0 4px 12px ${meta.color}18` : "var(--shadow-sm)",
              }}
            >
              {/* Row */}
              <div style={{ padding: "12px 16px", display: "flex", alignItems: "center", gap: 12 }}>
                {/* Index */}
                <div style={{
                  width: 24, height: 24, borderRadius: 6, flexShrink: 0,
                  background: meta.bg,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 10, fontWeight: 800, color: meta.color,
                }}>{i + 1}</div>

                {/* Node name */}
                <span style={{ fontSize: 13, fontWeight: 700, color: "var(--text-primary)", minWidth: 140 }}>
                  {entry.node}
                </span>

                {/* Action badge */}
                <span style={{
                  padding: "3px 10px",
                  borderRadius: 20,
                  fontSize: 11,
                  fontWeight: 600,
                  color: meta.color,
                  background: meta.bg,
                  flexShrink: 0,
                }}>{meta.label}</span>

                {/* Right side info */}
                <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 12 }}>
                  {entry.latency_ms && (
                    <span style={{ fontSize: 11, color: "var(--text-muted)", fontFamily: "var(--font-mono)", background: "var(--bg-primary)", padding: "2px 8px", borderRadius: 6 }}>
                      {entry.latency_ms}ms
                    </span>
                  )}
                  {entry.model_used && (
                    <span style={{ fontSize: 11, color: "var(--accent-blue)", fontWeight: 600 }}>
                      {entry.model_used.split("-").slice(-1)[0]}
                    </span>
                  )}
                  <span style={{ fontSize: 12, color: "var(--text-muted)", transition: "transform 0.2s", display: "inline-block", transform: isExpanded ? "rotate(90deg)" : "none" }}>▶</span>
                </div>
              </div>

              {/* Expanded detail */}
              {isExpanded && (
                <div style={{
                  borderTop: "1px solid var(--border)",
                  background: "var(--bg-primary)",
                  padding: "16px 20px",
                  display: "flex",
                  flexDirection: "column",
                  gap: 12,
                }}>
                  {entry.input_snapshot && Object.keys(entry.input_snapshot).length > 0 && (
                    <DetailSection title="Input" color="var(--accent-blue)">
                      <pre style={{ fontSize: 11, color: "var(--text-secondary)", whiteSpace: "pre-wrap", lineHeight: 1.6, fontFamily: "var(--font-mono)", margin: 0 }}>
                        {JSON.stringify(entry.input_snapshot, null, 2)}
                      </pre>
                    </DetailSection>
                  )}
                  {entry.output_snapshot && Object.keys(entry.output_snapshot).length > 0 && (
                    <DetailSection title="Output" color="var(--accent-green)">
                      <pre style={{ fontSize: 11, color: "#059669", whiteSpace: "pre-wrap", lineHeight: 1.6, fontFamily: "var(--font-mono)", margin: 0 }}>
                        {JSON.stringify(entry.output_snapshot, null, 2)}
                      </pre>
                    </DetailSection>
                  )}
                  {entry.metadata && Object.keys(entry.metadata).length > 0 && (
                    <DetailSection title="Metadata" color="var(--accent-yellow)">
                      <pre style={{ fontSize: 11, color: "#d97706", whiteSpace: "pre-wrap", lineHeight: 1.6, fontFamily: "var(--font-mono)", margin: 0 }}>
                        {JSON.stringify(entry.metadata, null, 2)}
                      </pre>
                    </DetailSection>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {entries.length === 0 && (
        <div style={{ textAlign: "center", padding: "50px 40px", color: "var(--text-muted)" }}>
          <div style={{ fontSize: 32, marginBottom: 12, opacity: 0.4 }}>≡</div>
          <div style={{ fontSize: 14 }}>Run the pipeline to see the audit trail</div>
        </div>
      )}
    </div>
  );
}

function DetailSection({ title, color, children }) {
  return (
    <div>
      <div style={{
        fontSize: 11, fontWeight: 700, color, textTransform: "uppercase", letterSpacing: 1,
        marginBottom: 8, display: "flex", alignItems: "center", gap: 6,
      }}>
        <span style={{ width: 3, height: 12, borderRadius: 2, background: color, display: "inline-block" }} />
        {title}
      </div>
      <div style={{ background: "var(--bg-card)", borderRadius: 8, padding: "12px 14px", border: "1px solid var(--border)" }}>
        {children}
      </div>
    </div>
  );
}
