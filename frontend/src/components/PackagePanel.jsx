export default function PackagePanel({ result }) {
  const meta = result?.campaign_metadata || {};
  const bundle = result?.final_bundle || {};

  const deliverables = [
    { key: "ads", label: "Google Ads Set", format: "RSA: 3 headlines + 3 descriptions" },
    { key: "video", label: "Video Prompt", format: "15s vertical scene breakdown" },
    { key: "image", label: "Image Prompt", format: "Midjourney v6 optimized" },
    { key: "blog", label: "Blog Post", format: "Markdown + SEO elements" },
  ];

  return (
    <div>
      <h2 style={{ fontSize: 22, fontWeight: 800, color: "var(--text-primary)", marginBottom: 4 }}>Phase 4: Packaging</h2>
      <p style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 24 }}>Campaign-ready deliverable bundle + metadata</p>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 24 }}>
        {deliverables.map(d => {
          const asset = bundle[d.key] || {};
          return (
            <div key={d.key} style={{ background: "var(--bg-card)", borderRadius: 12, padding: 16, border: `1px solid ${asset.passed ? "rgba(0,212,170,0.2)" : "var(--border)"}` }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                <span style={{ fontSize: 14, fontWeight: 700, color: "var(--text-primary)" }}>{d.label}</span>
                <span style={{ fontSize: 11, color: asset.passed ? "var(--accent)" : "var(--text-muted)", fontWeight: 700 }}>
                  {asset.status === "approved" ? "Ready ✓" : asset.status || "Pending"}
                </span>
              </div>
              <div style={{ fontSize: 11, color: "var(--text-muted)" }}>{d.format}</div>
              {asset.composite_score > 0 && (
                <div style={{ fontSize: 11, color: "var(--text-secondary)", marginTop: 4 }}>Score: {asset.composite_score?.toFixed(1)} · v{asset.version}</div>
              )}
            </div>
          );
        })}
      </div>

      {/* Campaign metadata */}
      {meta.run_id && (
        <div style={{ background: "var(--bg-secondary)", borderRadius: 10, padding: 16, border: "1px solid var(--border)" }}>
          <div style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 1.2, marginBottom: 8 }}>campaign_metadata.json</div>
          <pre style={{ fontSize: 11, color: "#5a9e6f", margin: 0, lineHeight: 1.6, maxHeight: 400, overflow: "auto" }}>
            {JSON.stringify(meta, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
