const API_BASE = "/api";

export async function runPipeline(trigger = "seasonal_spring") {
  const res = await fetch(`${API_BASE}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ trigger }),
  });
  if (!res.ok) throw new Error(`Pipeline failed: ${res.statusText}`);
  return res.json();
}

export async function getResult(runId) {
  const res = await fetch(`${API_BASE}/result/${runId}`);
  if (!res.ok) throw new Error(`Result not found: ${res.statusText}`);
  return res.json();
}

export async function getLogs(runId) {
  const res = await fetch(`${API_BASE}/logs/${runId}`);
  if (!res.ok) throw new Error(`Logs not found: ${res.statusText}`);
  return res.json();
}

export async function listRuns() {
  const res = await fetch(`${API_BASE}/runs`);
  if (!res.ok) throw new Error(`Failed to list runs: ${res.statusText}`);
  return res.json();
}

export async function healthCheck() {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}
