"""
API Routes
==========
REST endpoints for the React frontend.

POST /api/run          — Trigger a pipeline run
GET  /api/result/{id}  — Get full results for a run
GET  /api/logs/{id}    — Get audit log for a run
GET  /api/health       — Health check
"""

import json
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, BackgroundTasks

from backend.api.models import (
    RunRequest, RunResponse, BundleResponse, AuditLogResponse,
    ALLOWED_MODELS, ALLOWED_IMAGE_GENERATORS, ALLOWED_VIDEO_GENERATORS,
    ALLOWED_RUN_MODES, ALLOWED_RETRY_POLICIES,
)
from backend.pipeline.graph import run_pipeline
from backend.observability.run_storage import save_run_artifacts, load_audit_entries

router = APIRouter()

# In-memory store for run results (production would use a database)
_run_results = {}


def _execute_pipeline(trigger: str, run_id_holder: dict):
    """Background task that runs the pipeline."""
    try:
        result = run_pipeline(trigger=trigger)
        run_id = result.get("run_id", "unknown")
        run_id_holder["run_id"] = run_id
        _run_results[run_id] = result
        save_run_artifacts(result)

    except Exception as e:
        print(f"Pipeline error: {e}")
        _run_results[run_id_holder.get("run_id", "error")] = {"error": str(e)}


@router.get("/health")
def health():
    return {"status": "healthy", "pipeline": "ready"}


#@router.post("/run", response_model=RunResponse)

import threading

_active_runs = {}

def _run_in_background(
    run_id: str,
    trigger: str,
    product: str = "ceramidin_cream",
    generation_model: str = "claude-sonnet-4-20250514",
    judge_model: str = "claude-sonnet-4-20250514",
    image_generator: str = "midjourney-v6",
    video_generator: str = "runway-gen4",
    run_mode: str = "creative",
    retry_policy: str = "production_selective",
):
    """Execute pipeline in a background thread."""
    try:
        _active_runs[run_id] = {"status": "running"}
        result = run_pipeline(
            trigger=trigger,
            product=product,
            generation_model=generation_model,
            judge_model=judge_model,
            image_generator=image_generator,
            video_generator=video_generator,
            run_mode=run_mode,
            retry_policy=retry_policy,
        )
        actual_id = result.get("run_id", run_id)
        _run_results[actual_id] = result
        _active_runs[run_id] = {"status": "complete", "actual_run_id": actual_id}
        save_run_artifacts(result)

    except Exception as e:
        print(f"Pipeline error: {e}")
        _active_runs[run_id] = {"status": "failed", "error": str(e)}


@router.post("/run", response_model=RunResponse)
def trigger_run(request: RunRequest):
    """Start a pipeline run in the background. Returns immediately."""
    run_id = str(__import__("uuid").uuid4())[:8]
    thread = threading.Thread(
        target=_run_in_background,
        args=(
            run_id,
            request.trigger,
            request.product,
            request.generation_model,
            request.judge_model or request.generation_model,
            request.image_generator,
            request.video_generator,
            request.run_mode,
            request.retry_policy,
        ),
        daemon=True,
    )
    thread.start()
    return RunResponse(
        run_id=run_id,
        status="running",
        message="Pipeline started. Poll /api/status/{run_id} for progress.",
    )


@router.get("/models")
def list_model_and_generator_options():
    """Return allowlisted model and generator options for the frontend."""
    return {
        "generation_models": ALLOWED_MODELS,
        "judge_models": ALLOWED_MODELS,
        "image_generators": ALLOWED_IMAGE_GENERATORS,
        "video_generators": ALLOWED_VIDEO_GENERATORS,
        "run_modes": ALLOWED_RUN_MODES,
        "retry_policies": ALLOWED_RETRY_POLICIES,
        "defaults": {
            "generation_model": "claude-sonnet-4-20250514",
            "judge_model": "claude-sonnet-4-20250514",
            "image_generator": "midjourney-v6",
            "video_generator": "runway-gen4",
            "run_mode": "creative",
            "retry_policy": "production_selective",
        },
    }


@router.get("/status/{run_id}")
def get_status(run_id: str):
    """Poll this endpoint to check if a run is complete."""
    # Check active runs
    if run_id in _active_runs:
        info = _active_runs[run_id]
        if info["status"] == "complete":
            actual_id = info.get("actual_run_id", run_id)
            result = _run_results.get(actual_id, {})
            meta = result.get("campaign_metadata", {})
            return {
                "run_id": actual_id,
                "status": "complete",
                "assets_passed": meta.get("assets_passed", 0),
                "total_iterations": meta.get("total_iterations", 0),
                "human_review": meta.get("assets_in_human_review", 0),
            }
        elif info["status"] == "failed":
            return {"run_id": run_id, "status": "failed", "error": info.get("error")}
        else:
            return {"run_id": run_id, "status": "running"}

    return {"run_id": run_id, "status": "not_found"}

@router.get("/result/{run_id}", response_model=BundleResponse)
def get_result(run_id: str):
    """Get full results for a pipeline run."""
    # Check memory first
    if run_id in _run_results:
        result = _run_results[run_id]
        return BundleResponse(
            campaign_metadata=result.get("campaign_metadata", {}),
            final_bundle=result.get("final_bundle", {}),
            scores=result.get("scores", {}),
            trend_narratives=result.get("trend_narratives", []),
            audit_log_count=len(result.get("audit_log", [])),
        )

    # Check disk
    filepath = f"data/outputs/run_{run_id}.json"
    if os.path.exists(filepath):
        with open(filepath) as f:
            data = json.load(f)
        return BundleResponse(
            campaign_metadata=data.get("campaign_metadata", {}),
            final_bundle=data.get("final_bundle", {}),
            scores=data.get("scores", {}),
            trend_narratives=data.get("trend_narratives", []),
            audit_log_count=len(data.get("audit_log", [])),
        )

    raise HTTPException(status_code=404, detail=f"Run {run_id} not found")


@router.get("/logs/{run_id}", response_model=AuditLogResponse)
def get_logs(run_id: str):
    """Get audit log for a pipeline run."""
    if run_id in _run_results:
        logs = _run_results[run_id].get("audit_log", [])
        return AuditLogResponse(run_id=run_id, entries=logs, total_entries=len(logs))

    audit_data = load_audit_entries(run_id)
    if audit_data:
        return AuditLogResponse(
            run_id=run_id,
            entries=audit_data.get("entries", []),
            total_entries=audit_data.get("total_entries", len(audit_data.get("entries", []))),
        )

    filepath = f"data/outputs/run_{run_id}.json"
    if os.path.exists(filepath):
        with open(filepath) as f:
            data = json.load(f)
        logs = data.get("audit_log", [])
        return AuditLogResponse(run_id=run_id, entries=logs, total_entries=len(logs))

    raise HTTPException(status_code=404, detail=f"Run {run_id} not found")


@router.get("/runs")
def list_runs():
    """List all available pipeline runs."""
    runs = []
    output_dir = Path("data/outputs")
    if output_dir.exists():
        for f in sorted(output_dir.glob("run_*.json"), reverse=True):
            with open(f) as fh:
                data = json.load(fh)
                meta = data.get("campaign_metadata", {})
                runs.append({
                    "run_id": meta.get("run_id", f.stem),
                    "status": meta.get("status", "unknown"),
                    "trigger": meta.get("trigger", "unknown"),
                    "assets_passed": meta.get("assets_passed", 0),
                    "completed_at": meta.get("completed_at", ""),
                })
    return {"runs": runs}
