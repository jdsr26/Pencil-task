import { useState } from "react";

const ASSETS = [
  { key: "ads", label: "Google Ads", icon: "◈", color: "var(--accent-blue)", bg: "var(--accent-blue-light)" },
  { key: "video", label: "Video Prompt", icon: "▶", color: "var(--accent-red)", bg: "var(--accent-red-light)" },
  { key: "image", label: "Image Prompt", icon: "◧", color: "var(--accent-purple)", bg: "var(--accent-purple-light)" },
  { key: "blog", label: "Blog Post", icon: "≡", color: "var(--accent-green)", bg: "var(--accent-green-light)" },
];

export default function GeneratePanel({ result }) {
  const [selected, setSelected] = useState("ads");
  const bundle = result?.final_bundle || {};
  const asset = bundle[selected] || {};
  const meta = ASSETS.find(a => a.key === selected);

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <div style={{ display: "inline-flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
          <span style={{ padding: "3px 10px", borderRadius: 20, fontSize: 11, fontWeight: 700, color: "var(--accent)", background: "var(--accent-light)", textTransform: "uppercase", letterSpacing: 0.8 }}>Phase 2</span>
        </div>
        <h2 style={{ fontSize: 26, fontWeight: 800, color: "var(--text-primary)", marginBottom: 6 }}>Creative Generation</h2>
        <p style={{ fontSize: 14, color: "var(--text-muted)", maxWidth: 560, lineHeight: 1.6 }}>
          Four specialized creative agents generate tone-compliant, trend-aligned assets across platforms.
        </p>
      </div>

      {/* Asset tabs */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10, marginBottom: 24 }}>
        {ASSETS.map(a => {
          const assetData = bundle[a.key] || {};
          const isSelected = selected === a.key;
          return (
            <button
              key={a.key}
              onClick={() => setSelected(a.key)}
              style={{
                padding: "14px 16px",
                borderRadius: 12,
                border: `2px solid ${isSelected ? a.color : "var(--border)"}`,
                background: isSelected ? a.bg : "var(--bg-card)",
                color: isSelected ? a.color : "var(--text-secondary)",
                fontSize: 13,
                fontWeight: 700,
                textAlign: "left",
                boxShadow: isSelected ? `0 4px 14px ${a.color}22` : "var(--shadow-sm)",
                transition: "all 0.2s",
              }}
            >
              <div style={{ fontSize: 18, marginBottom: 6, opacity: isSelected ? 1 : 0.5 }}>{a.icon}</div>
              <div>{a.label}</div>
              {assetData.passed !== undefined && (
                <div style={{ fontSize: 11, marginTop: 4, fontWeight: 600, color: assetData.passed ? "var(--accent-green)" : "var(--accent-red)" }}>
                  {assetData.passed ? "✓ Passed" : "✗ Failed"}
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* Asset content */}
      {asset.content ? (
        <div>
          {/* Asset metadata */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10, marginBottom: 16 }}>
            <MiniStat label="Version" value={`v${asset.version}`} color="var(--text-secondary)" />
            <MiniStat
              label="Status"
              value={asset.status}
              color={asset.passed ? "var(--accent-green)" : "var(--accent-red)"}
              bg={asset.passed ? "var(--accent-green-light)" : "var(--accent-red-light)"}
            />
            <MiniStat
              label="Score"
              value={asset.composite_score?.toFixed(1) ?? "0.0"}
              color={asset.passed ? "var(--accent-green)" : "var(--accent-red)"}
              bg={asset.passed ? "var(--accent-green-light)" : "var(--accent-red-light)"}
            />
            <MiniStat label="Platform" value={asset.target_platform?.split("(")[0]?.trim() ?? "—"} color="var(--accent-blue)" bg="var(--accent-blue-light)" />
          </div>

          {/* Generated content */}
          <div style={{
            background: "var(--bg-card)",
            borderRadius: 14,
            border: `1px solid ${asset.passed ? "#a7f3d0" : "var(--border)"}`,
            overflow: "hidden",
            boxShadow: "var(--shadow-sm)",
          }}>
            <div style={{
              padding: "12px 20px",
              borderBottom: "1px solid var(--border)",
              background: asset.passed ? "var(--accent-green-light)" : "var(--bg-primary)",
              display: "flex",
              alignItems: "center",
              gap: 8,
            }}>
              <span style={{ fontSize: 14 }}>{meta?.icon}</span>
              <span style={{ fontSize: 12, fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: 0.8 }}>
                Generated Output · {meta?.label}
              </span>
              {asset.passed !== undefined && (
                <span style={{
                  marginLeft: "auto",
                  padding: "3px 10px",
                  borderRadius: 20,
                  fontSize: 11,
                  fontWeight: 700,
                  color: asset.passed ? "var(--accent-green)" : "var(--accent-red)",
                  background: asset.passed ? "#d1fae5" : "#fee2e2",
                }}>
                  {asset.passed ? "✓ Approved" : "✗ Needs Review"}
                </span>
              )}
            </div>
            <div style={{ padding: "20px 24px" }}>
              <pre style={{
                fontSize: 13,
                color: "var(--text-secondary)",
                whiteSpace: "pre-wrap",
                lineHeight: 1.8,
                margin: 0,
                fontFamily: "var(--font-sans)",
              }}>{asset.content}</pre>
            </div>
          </div>
        </div>
      ) : (
        <div style={{ textAlign: "center", padding: "50px 40px", color: "var(--text-muted)" }}>
          <div style={{ fontSize: 32, marginBottom: 12, opacity: 0.4 }}>✦</div>
          <div style={{ fontSize: 14 }}>Run the pipeline to generate assets</div>
        </div>
      )}
    </div>
  );
}

function MiniStat({ label, value, color, bg }) {
  return (
    <div style={{
      background: bg || "var(--bg-card)",
      borderRadius: 10,
      padding: "12px 14px",
      border: "1px solid var(--border)",
      boxShadow: "var(--shadow-sm)",
    }}>
      <div style={{ fontSize: 11, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 0.8, marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 14, fontWeight: 700, color, textTransform: "capitalize" }}>{value}</div>
    </div>
  );
}
