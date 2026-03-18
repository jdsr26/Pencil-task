export default function ScorePanel({ result }) {
  const scores = result?.scores || {};
  const labels = { ads: "Google Ads", video: "Video Prompt", image: "Image Prompt", blog: "Blog Post" };

  return (
    <div>
      <h2 style={{ fontSize: 22, fontWeight: 800, color: "var(--text-primary)", marginBottom: 4 }}>Phase 3: Quality Scoring</h2>
      <p style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 24 }}>Hybrid scoring: deterministic (Tier 1) + LLM judge (Tier 2) → composite</p>

      {Object.entries(labels).map(([key, label]) => {
        const score = scores[key] || {};
        const det = score.deterministic || {};
        const llm = score.llm_judge || {};
        const composite = score.composite || 0;
        const passed = score.passed || false;
        const feedback = score.all_feedback || [];

        return (
          <div key={key} style={{ background: "var(--bg-card)", borderRadius: 12, padding: 16, marginBottom: 12, border: `1px solid ${passed ? "rgba(0,212,170,0.2)" : "var(--border)"}` }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
              <span style={{ fontSize: 14, fontWeight: 700, color: "var(--text-primary)" }}>{label}</span>
              <span style={{ padding: "4px 12px", borderRadius: 6, fontSize: 13, fontWeight: 800, background: passed ? "rgba(0,212,170,0.12)" : "rgba(255,82,82,0.12)", color: passed ? "var(--accent)" : "var(--accent-red)" }}>
                {composite.toFixed?.(1) || "0.0"} — {passed ? "PASS ✓" : "FAIL ✗"}
              </span>
            </div>

            <ScoreBar label="Format (25%)" score={det.score || 0} />
            <ScoreBar label="Brand (40%)" score={llm.brand_alignment || 0} />
            <ScoreBar label="Trend (35%)" score={llm.trend_alignment || 0} />

            {feedback.length > 0 && (
              <div style={{ marginTop: 10 }}>
                <div style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 1.2, marginBottom: 6 }}>Feedback</div>
                {feedback.map((f, i) => (
                  <div key={i} style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 4, paddingLeft: 10, borderLeft: "2px solid var(--border)" }}>{f}</div>
                ))}
              </div>
            )}

            {/* Deterministic check details */}
            {det.checks && det.checks.length > 0 && (
              <div style={{ marginTop: 10 }}>
                <div style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 1.2, marginBottom: 6 }}>Format Checks</div>
                {det.checks.map((c, i) => (
                  <div key={i} style={{ fontSize: 11, color: c.passed ? "var(--accent)" : "var(--accent-red)", marginBottom: 2 }}>
                    {c.passed ? "✅" : "❌"} {c.check_name}: {c.actual} (expected: {c.expected})
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function ScoreBar({ label, score }) {
  const color = score >= 85 ? "var(--accent)" : score >= 70 ? "var(--accent-yellow)" : "var(--accent-red)";
  return (
    <div style={{ marginBottom: 8 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
        <span style={{ fontSize: 11, color: "var(--text-secondary)" }}>{label}</span>
        <span style={{ fontSize: 11, color, fontWeight: 700 }}>{score}/100</span>
      </div>
      <div style={{ height: 5, borderRadius: 3, background: "var(--border)" }}>
        <div style={{ height: 5, borderRadius: 3, background: color, width: `${score}%`, transition: "width 0.5s" }} />
      </div>
    </div>
  );
}
