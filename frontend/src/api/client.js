const API_BASE = "/api";

export async function runPipeline(
  trigger = "seasonal_spring",
  {
    product = "ceramidin_cream",
    generationModel = "claude-sonnet-4-20250514",
    judgeModel = "claude-sonnet-4-20250514",
    imageGenerator = "midjourney-v6",
    videoGenerator = "runway-gen4",
    runMode = "creative",
    retryPolicy = "production_selective",
  } = {}
) {
  const res = await fetch(`${API_BASE}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      trigger,
      product,
      generation_model: generationModel,
      judge_model: judgeModel,
      image_generator: imageGenerator,
      video_generator: videoGenerator,
      run_mode: runMode,
      retry_policy: retryPolicy,
    }),
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

export async function getModelOptions() {
  const res = await fetch(`${API_BASE}/models`);
  if (!res.ok) throw new Error(`Failed to load model options: ${res.statusText}`);
  return res.json();
}
