"""Persistence helpers for run outputs and standalone audit artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


OUTPUTS_DIR = Path("data/outputs")
AUDITS_DIR = OUTPUTS_DIR / "audits"


def get_run_output_path(run_id: str) -> Path:
    return OUTPUTS_DIR / f"run_{run_id}.json"


def get_run_audit_path(run_id: str) -> Path:
    return AUDITS_DIR / f"audit_{run_id}.json"


def save_run_artifacts(result: Dict[str, Any]) -> Dict[str, str]:
    """Persist a run bundle JSON and a separate audit JSON file."""
    run_id = result.get("run_id", "unknown")

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    AUDITS_DIR.mkdir(parents=True, exist_ok=True)

    output_path = get_run_output_path(run_id)
    audit_path = get_run_audit_path(run_id)

    with output_path.open("w") as f:
        json.dump(
            {
                "campaign_metadata": result.get("campaign_metadata", {}),
                "final_bundle": result.get("final_bundle", {}),
                "scores": result.get("scores", {}),
                "trend_narratives": result.get("trend_narratives", []),
                "audit_log": result.get("audit_log", []),
            },
            f,
            indent=2,
            default=str,
        )

    with audit_path.open("w") as f:
        json.dump(
            {
                "run_id": run_id,
                "campaign_metadata": result.get("campaign_metadata", {}),
                "entries": result.get("audit_log", []),
                "total_entries": len(result.get("audit_log", [])),
            },
            f,
            indent=2,
            default=str,
        )

    return {
        "output_path": str(output_path),
        "audit_path": str(audit_path),
    }


def load_audit_entries(run_id: str) -> Dict[str, Any] | None:
    """Load a standalone audit artifact if it exists."""
    audit_path = get_run_audit_path(run_id)
    if not audit_path.exists():
        return None

    with audit_path.open() as f:
        return json.load(f)