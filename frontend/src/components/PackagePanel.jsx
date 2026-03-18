export default function PackagePanel({ result }) {
  const meta = result?.campaign_metadata || {};
  const bundle = result?.final_bundle || {};

  const deliverables = [
    { key: "ads", label: "Google Ads Set", icon: "◈", format: "RSA: 3 headlines + 3 descriptions", color: "var(--accent-blue)", bg: "var(--accent-blue-light)" },
    { key: "video", label: "Video Prompt", icon: "▶", format: "15-second vertical scene breakdown", color: "var(--accent-red)", bg: "var(--accent-red-light)" },
    { key: "image", label: "Image Prompt", icon: "◧", format: "Midjourney v6 optimized prompt", color: "var(--accent-purple)", bg: "var(--accent-purple-light)" },
    { key: "blog", label: "Blog Post", icon: "≡", format: "Markdown + SEO elements", color: "var(--accent-green)", bg: "var(--accent-green-light)" },
  ];

  const allPassed = deliverables.every(d => bundle[d.key]?.passed);
  const passedCount = deliverables.filter(d => bundle[d.key]?.passed).length;

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <div style={{ display: "inline-flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
          <span style={{ padding: "3px 10px", borderRadius: 20, fontSize: 11, fontWeight: 700, color: "var(--accent-purple)", background: "var(--accent-purple-light)", textTransform: "uppercase", letterSpacing: 0.8 }}>Phase 4</span>
        </div>
        <h2 style={{ fontSize: 26, fontWeight: 800, color: "var(--text-primary)", marginBottom: 6 }}>Campaign Package</h2>
        <p style={{ fontSize: 14, color: "var(--text-muted)", maxWidth: 560, lineHeight: 1.6 }}>
          Campaign-ready deliverable bundle — all assets packaged and ready for publishing.
        </p>
      </div>

      {/* Summary banner */}
      {meta.status && (
        <div style={{
          background: allPassed ? "var(--gradient-success)" : "var(--gradient-brand)",
          borderRadius: 14,
          padding: "18px 24px",
          marginBottom: 24,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          boxShadow: allPassed ? "0 4px 16px rgba(16,185,129,0.3)" : "0 4px 16px rgba(99,102,241,0.3)",
        }}>
          <div>
            <div style={{ fontSize: 12, fontWeight: 600, color: "rgba(255,255,255,0.7)", marginBottom: 4, textTransform: "uppercase", letterSpacing: 0.8 }}>Bundle Status</div>
            <div style={{ fontSize: 18, fontWeight: 800, color: "#fff" }}>
              {allPassed ? "✓ All Deliverables Ready" : `${passedCount} of 4 Deliverables Ready`}
            </div>
          </div>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: 36, fontWeight: 900, color: "#fff" }}>{passedCount}/4</div>
            <div style={{ fontSize: 12, color: "rgba(255,255,255,0.7)" }}>assets approved</div>
          </div>
        </div>
      )}

      {/* Deliverable cards */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginBottom: 24 }}>
        {deliverables.map(d => {
          const asset = bundle[d.key] || {};
          const ready = asset.status === "approved" || asset.passed;
          return (
            <div key={d.key} style={{
              background: "var(--bg-card)",
              borderRadius: 14,
              padding: "18px 20px",
              border: `1px solid ${ready ? "#a7f3d0" : "var(--border)"}`,
              boxShadow: "var(--shadow-sm)",
            }}>
              <div style={{ display: "flex", alignItems: "flex-start", gap: 14, marginBottom: 12 }}>
                <div style={{
                  width: 44, height: 44, borderRadius: 12, flexShrink: 0,
                  background: ready ? "var(--accent-green-light)" : d.bg,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 20, color: ready ? "var(--accent-green)" : d.color,
                }}>{d.icon}</div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 14, fontWeight: 700, color: "var(--text-primary)", marginBottom: 2 }}>{d.label}</div>
                  <div style={{ fontSize: 12, color: "var(--text-muted)" }}>{d.format}</div>
                </div>
                <span style={{
                  padding: "4px 10px",
                  borderRadius: 20,
                  fontSize: 11,
                  fontWeight: 700,
                  color: ready ? "var(--accent-green)" : "var(--text-muted)",
                  background: ready ? "var(--accent-green-light)" : "var(--bg-primary)",
                  border: `1px solid ${ready ? "#6ee7b7" : "var(--border)"}`,
                  flexShrink: 0,
                }}>
                  {ready ? "✓ Ready" : asset.status || "Pending"}
                </span>
              </div>
              {asset.composite_score > 0 && (
                <div style={{
                  display: "flex", gap: 12,
                  padding: "10px 12px",
                  background: "var(--bg-primary)",
                  borderRadius: 8,
                  fontSize: 12,
                }}>
                  <span style={{ color: "var(--text-muted)" }}>Score:</span>
                  <span style={{ fontWeight: 700, color: ready ? "var(--accent-green)" : "var(--accent-yellow)" }}>{asset.composite_score?.toFixed(1)}</span>
                  <span style={{ color: "var(--border-strong)" }}>·</span>
                  <span style={{ color: "var(--text-muted)" }}>Version:</span>
                  <span style={{ fontWeight: 700, color: "var(--text-secondary)" }}>v{asset.version}</span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Campaign metadata */}
      {meta.run_id && (
        <div style={{
          background: "var(--bg-card)",
          borderRadius: 14,
          border: "1px solid var(--border)",
          overflow: "hidden",
          boxShadow: "var(--shadow-sm)",
        }}>
          <div style={{
            padding: "12px 20px",
            borderBottom: "1px solid var(--border)",
            background: "var(--bg-primary)",
            display: "flex", alignItems: "center", gap: 8,
          }}>
            <span style={{ fontSize: 12, fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: 0.8 }}>
              Campaign Metadata
            </span>
            <span style={{ fontSize: 11, color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>campaign_metadata.json</span>
          </div>
          <div style={{ padding: "16px 20px" }}>
            <pre style={{
              fontSize: 12,
              color: "#059669",
              margin: 0,
              lineHeight: 1.7,
              maxHeight: 360,
              overflow: "auto",
              fontFamily: "var(--font-mono)",
            }}>
              {JSON.stringify(meta, null, 2)}
            </pre>
          </div>
        </div>
      )}

      {!result && (
        <div style={{ textAlign: "center", padding: "50px 40px", color: "var(--text-muted)" }}>
          <div style={{ fontSize: 32, marginBottom: 12, opacity: 0.4 }}>▣</div>
          <div style={{ fontSize: 14 }}>Run the pipeline to package deliverables</div>
        </div>
      )}
    </div>
  );
}
