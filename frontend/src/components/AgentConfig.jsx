export default function AgentConfig({ agent }) {
  if (!agent) return null;

  return (
    <div style={{ background: "var(--bg-card)", borderRadius: 12, padding: 20, border: "1px solid var(--border)", marginBottom: 16 }}>
      <div style={{ fontSize: 15, fontWeight: 700, color: "var(--accent)", marginBottom: 10, display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ width: 8, height: 8, borderRadius: "50%", background: "var(--accent)" }} />
        {agent.name}
      </div>
      {agent.instructions && (
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 1.2, marginBottom: 4 }}>Instructions</div>
          <div style={{ fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.6 }}>{agent.instructions}</div>
        </div>
      )}
      <div style={{ display: "flex", gap: 20 }}>
        {agent.knowledge && (
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 1.2, marginBottom: 4 }}>Knowledge</div>
            {agent.knowledge.map((k, i) => (
              <div key={i} style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 2 }}>📄 {k}</div>
            ))}
          </div>
        )}
        {agent.tools && (
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 1.2, marginBottom: 4 }}>Tools</div>
            {agent.tools.map((t, i) => (
              <div key={i} style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 2 }}>🔧 {t}</div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
