const ASSET_LABELS = {
  ads: { label: "Google Ads", icon: "◈", color: "var(--accent-blue)" },
  video: { label: "Video Prompt", icon: "▶", color: "var(--accent-red)" },
  image: { label: "Image Prompt", icon: "◧", color: "var(--accent-purple)" },
  blog: { label: "Blog Post", icon: "≡", color: "var(--accent-green)" },
};

export default function ScorePanel({ result }) {
  const scores = result?.scores || {};
  const coherence = result?.campaign_metadata?.campaign_coherence || result?.campaign_coherence || null;

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <div style={{ display: "inline-flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
          <span style={{ padding: "3px 10px", borderRadius: 20, fontSize: 11, fontWeight: 700, color: "var(--accent-yellow)", background: "var(--accent-yellow-light)", textTransform: "uppercase", letterSpacing: 0.8 }}>Phase 3</span>
        </div>
        <h2 style={{ fontSize: 26, fontWeight: 800, color: "var(--text-primary)", marginBottom: 6 }}>Quality Scoring</h2>
        <p style={{ fontSize: 14, color: "var(--text-muted)", maxWidth: 560, lineHeight: 1.6 }}>
          Hybrid scoring system: deterministic format checks (25%) + LLM brand judge (40%) + trend alignment (35%).
        </p>
      </div>

      {Object.entries(ASSET_LABELS).length > 0 && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
          {Object.entries(ASSET_LABELS).map(([key, meta]) => {
            const score = scores[key] || {};
            const det = score.deterministic || {};
            const llm = score.llm_judge || {};
            const composite = score.composite || 0;
            const passed = score.passed || false;
            const feedback = score.all_feedback || [];

            return (
              <div key={key} style={{
                background: "var(--bg-card)",
                borderRadius: 16,
                border: `1px solid ${passed ? "#a7f3d0" : "var(--border)"}`,
                overflow: "hidden",
                boxShadow: "var(--shadow-sm)",
              }}>
                {/* Card header */}
                <div style={{
                  padding: "16px 20px",
                  background: passed ? "var(--accent-green-light)" : "var(--bg-primary)",
                  borderBottom: "1px solid var(--border)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <div style={{
                      width: 34, height: 34, borderRadius: 8,
                      background: passed ? "#d1fae5" : "#f1f5f9",
                      display: "flex", alignItems: "center", justifyContent: "center",
                      fontSize: 16, color: meta.color,
                    }}>{meta.icon}</div>
                    <span style={{ fontSize: 15, fontWeight: 700, color: "var(--text-primary)" }}>{meta.label}</span>
                  </div>
                  <div style={{
                    display: "flex", alignItems: "center", gap: 8,
                  }}>
                    <span style={{ fontSize: 20, fontWeight: 900, color: passed ? "var(--accent-green)" : "var(--accent-red)" }}>
                      {composite.toFixed?.(1) ?? "0.0"}
                    </span>
                    <span style={{
                      padding: "4px 10px",
                      borderRadius: 20,
                      fontSize: 12,
                      fontWeight: 700,
                      color: passed ? "var(--accent-green)" : "var(--accent-red)",
                      background: passed ? "#d1fae5" : "#fee2e2",
                    }}>
                      {passed ? "✓ PASS" : "✗ FAIL"}
                    </span>
                  </div>
                </div>

                {/* Score bars */}
                <div style={{ padding: "16px 20px" }}>
                  <ScoreBar label="Format Compliance" weight="25%" score={det.score || 0} />
                  <ScoreBar label="Brand Alignment" weight="40%" score={llm.brand_alignment || 0} />
                  <ScoreBar label="Trend Alignment" weight="35%" score={llm.trend_alignment || 0} />

                  {feedback.length > 0 && (
                    <div style={{ marginTop: 14, paddingTop: 14, borderTop: "1px solid var(--border)" }}>
                      <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 1, marginBottom: 8 }}>Feedback</div>
                      {feedback.map((f, i) => (
                        <div key={i} style={{
                          fontSize: 12, color: "var(--text-secondary)", marginBottom: 6,
                          paddingLeft: 12, borderLeft: "3px solid var(--border)",
                          lineHeight: 1.5,
                        }}>{f}</div>
                      ))}
                    </div>
                  )}

                  {det.checks && det.checks.length > 0 && (
                    <div style={{ marginTop: 14, paddingTop: 14, borderTop: "1px solid var(--border)" }}>
                      <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 1, marginBottom: 8 }}>Format Checks</div>
                      {det.checks.map((c, i) => (
                        <div key={i} style={{
                          fontSize: 12,
                          color: c.passed ? "var(--accent-green)" : "var(--accent-red)",
                          marginBottom: 4,
                          display: "flex", alignItems: "flex-start", gap: 6,
                        }}>
                          <span style={{ flexShrink: 0, fontWeight: 700 }}>{c.passed ? "✓" : "✗"}</span>
                          <span>{c.check_name}: <span style={{ color: "var(--text-muted)" }}>{c.actual} (expected: {c.expected})</span></span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Campaign Coherence — Tier 3 */}
      {coherence && (
        <div style={{
          marginTop: 20,
          background: "var(--bg-card)",
          borderRadius: 16,
          border: `1px solid ${coherence.coherent ? "#a7f3d0" : "#fca5a5"}`,
          overflow: "hidden",
          boxShadow: "var(--shadow-sm)",
        }}>
          <div style={{
            padding: "14px 20px",
            background: coherence.coherent ? "var(--accent-green-light)" : "var(--accent-red-light)",
            borderBottom: "1px solid var(--border)",
            display: "flex", alignItems: "center", justifyContent: "space-between",
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <span style={{ fontSize: 16 }}>⬡</span>
              <span style={{ fontSize: 15, fontWeight: 700, color: "var(--text-primary)" }}>Campaign Coherence</span>
              <span style={{ fontSize: 11, color: "var(--text-muted)", fontWeight: 500 }}>Tier 3 · Cross-asset consistency</span>
            </div>
            <span style={{
              padding: "4px 12px", borderRadius: 20, fontSize: 12, fontWeight: 700,
              color: coherence.coherent ? "var(--accent-green)" : "var(--accent-red)",
              background: coherence.coherent ? "#d1fae5" : "#fee2e2",
            }}>
              {coherence.coherent ? "✓ COHERENT" : "✗ ISSUES FOUND"}
            </span>
          </div>
          <div style={{ padding: "14px 20px", display: "flex", gap: 24, flexWrap: "wrap" }}>
            {[
              { label: "Product Consistent", val: coherence.product_consistent },
              { label: "Narrative Consistent", val: coherence.narrative_consistent },
              { label: "Tone Consistent", val: coherence.tone_consistent },
              { label: "CTA Aligned", val: coherence.cta_aligned },
            ].map(({ label, val }) => (
              <div key={label} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13 }}>
                <span style={{ fontWeight: 700, color: val ? "var(--accent-green)" : "var(--accent-red)" }}>
                  {val ? "✓" : "✗"}
                </span>
                <span style={{ color: "var(--text-secondary)" }}>{label}</span>
              </div>
            ))}
          </div>
          {coherence.issues && coherence.issues.length > 0 && (
            <div style={{ padding: "0 20px 14px" }}>
              {coherence.issues.map((issue, i) => (
                <div key={i} style={{
                  fontSize: 12, color: "var(--accent-red)", marginBottom: 4,
                  paddingLeft: 12, borderLeft: "3px solid #fca5a5",
                }}>{issue}</div>
              ))}
            </div>
          )}
        </div>
      )}

      {Object.keys(scores).length === 0 && (
        <div style={{ textAlign: "center", padding: "50px 40px", color: "var(--text-muted)" }}>
          <div style={{ fontSize: 32, marginBottom: 12, opacity: 0.4 }}>◈</div>
          <div style={{ fontSize: 14 }}>Run the pipeline to see quality scores</div>
        </div>
      )}
    </div>
  );
}

function ScoreBar({ label, weight, score }) {
  const color = score >= 85 ? "var(--accent-green)" : score >= 70 ? "var(--accent-yellow)" : score > 0 ? "var(--accent-red)" : "var(--border-strong)";
  const barBg = score >= 85 ? "#d1fae5" : score >= 70 ? "var(--accent-yellow-light)" : score > 0 ? "#fee2e2" : "var(--bg-primary)";

  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span style={{ fontSize: 13, color: "var(--text-secondary)", fontWeight: 500 }}>{label}</span>
          <span style={{ fontSize: 10, color: "var(--text-muted)", background: "var(--bg-primary)", padding: "1px 6px", borderRadius: 20, fontWeight: 600 }}>{weight}</span>
        </div>
        <span style={{
          fontSize: 13, fontWeight: 800, color,
          padding: "2px 8px", borderRadius: 6, background: barBg,
        }}>{score > 0 ? `${score}` : "—"}</span>
      </div>
      <div style={{ height: 6, borderRadius: 4, background: "var(--bg-primary)" }}>
        <div style={{
          height: 6, borderRadius: 4, background: color,
          width: `${score}%`, transition: "width 0.6s ease",
          minWidth: score > 0 ? 6 : 0,
        }} />
      </div>
    </div>
  );
}
