import { useState } from "react";

const ASSET_LABELS = { ads: "Google Ads", video: "Video Prompt", image: "Image Prompt", blog: "Blog Post" };

export default function GeneratePanel({ result }) {
  const [selected, setSelected] = useState("ads");
  const bundle = result?.final_bundle || {};
  const asset = bundle[selected] || {};

  return (
    <div>
      <h2 style={{ fontSize: 22, fontWeight: 800, color: "var(--text-primary)", marginBottom: 4 }}>Phase 2: Generation</h2>
      <p style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 24 }}>4 Creative Agents — each generates a tone-compliant, trend-aligned asset</p>

      {/* Asset tabs */}
      <div style={{ display: "flex", gap: 8, marginBottom: 20 }}>
        {Object.entries(ASSET_LABELS).map(([key, label]) => (
          <button key={key} onClick={() => setSelected(key)} style={{ padding: "8px 16px", borderRadius: 8, border: "1px solid", borderColor: selected === key ? "var(--accent)" : "var(--border)", background: selected === key ? "rgba(0,212,170,0.08)" : "transparent", color: selected === key ? "var(--accent)" : "var(--text-muted)", fontSize: 12, fontWeight: 600 }}>
            {label} {asset.passed ? "✓" : ""}
          </button>
        ))}
      </div>

      {/* Asset info */}
      {asset.content ? (
        <div>
          <div style={{ display: "flex", gap: 12, marginBottom: 16 }}>
            <MiniCard label="Version" value={`v${asset.version}`} />
            <MiniCard label="Status" value={asset.status} color={asset.passed ? "#00d4aa" : "#ff5252"} />
            <MiniCard label="Score" value={asset.composite_score?.toFixed(1) || "0"} color={asset.passed ? "#00d4aa" : "#ff5252"} />
            <MiniCard label="Platform" value={asset.target_platform?.split("(")[0]?.trim() || "—"} />
          </div>
          <div style={{ background: "var(--bg-card)", borderRadius: 12, padding: 20, border: `1px solid ${asset.passed ? "rgba(0,212,170,0.2)" : "var(--border)"}` }}>
            <div style={{ fontSize: 10, fontWeight: 700, color: "var(--accent)", textTransform: "uppercase", letterSpacing: 1.2, marginBottom: 10 }}>Generated Output</div>
            <pre style={{ fontSize: 12, color: "var(--text-secondary)", whiteSpace: "pre-wrap", lineHeight: 1.7, margin: 0 }}>{asset.content}</pre>
          </div>
        </div>
      ) : (
        <div style={{ color: "var(--text-muted)", fontSize: 12, padding: 40, textAlign: "center" }}>Run the pipeline to generate assets</div>
      )}
    </div>
  );
}

function MiniCard({ label, value, color = "var(--text-primary)" }) {
  return (
    <div style={{ background: "var(--bg-card)", borderRadius: 8, padding: "8px 12px", border: "1px solid var(--border)" }}>
      <div style={{ fontSize: 9, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 1 }}>{label}</div>
      <div style={{ fontSize: 13, fontWeight: 700, color, marginTop: 2 }}>{value}</div>
    </div>
  );
}
