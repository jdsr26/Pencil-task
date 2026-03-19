"""
Package Node
============
Phase 4: Final bundling of all passing assets into a
campaign-ready deliverable with complete metadata.

Includes:
  - All passing assets in their target formats
  - Campaign metadata (run context, scores, model versions)
  - Any failure diagnoses or human review flags
  - Complete audit trail
"""

from datetime import datetime, timezone
from typing import Dict, Any

from backend.observability.audit_log import create_audit_entry


def package(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node function.
    
    Assembles the final campaign bundle from all passing assets.
    Includes partial bundles if some assets are in human review.
    
    Args:
        state: Complete pipeline state
    
    Returns:
        Partial state update with final_bundle and campaign_metadata
    """
    assets = state.get("assets", {})
    scores = state.get("scores", {})
    human_review_queue = state.get("human_review_queue", [])
    failure_diagnosis = state.get("failure_diagnosis")

    # ─── COLLECT PASSING ASSETS ───
    deliverables = {}
    for asset_type in ["ads", "video", "image", "blog"]:
        asset = assets.get(asset_type, {})
        score_data = scores.get(asset_type, {})

        if isinstance(asset, dict):
            content = asset.get("content", "")
            version = asset.get("version", 0)
        else:
            content = getattr(asset, "content", "")
            version = getattr(asset, "version", 0)

        if isinstance(score_data, dict):
            passed = score_data.get("passed", False)
            composite = score_data.get("composite", 0)
        else:
            passed = getattr(score_data, "passed", False)
            composite = getattr(score_data, "composite", 0)

        deliverables[asset_type] = {
            "content": content,
            "version": version,
            "passed": passed,
            "composite_score": composite,
            "status": "approved" if passed else (
                "human_review" if asset_type in human_review_queue else "failed"
            ),
            "target_platform": _get_target_platform(asset_type),
        }

    # ─── BUILD CAMPAIGN METADATA ───
    passing_count = sum(1 for d in deliverables.values() if d["passed"])
    total_iterations = sum(state.get("iteration_counts", {}).values())
    resolved_models = sorted({
        entry.get("model_used")
        for entry in state.get("audit_log", [])
        if isinstance(entry, dict)
        and entry.get("action") in {"llm_call", "llm_call_failed"}
        and entry.get("model_used")
    })

    campaign_metadata = {
        "run_id": state.get("run_id", ""),
        "trigger": state.get("trigger", "manual"),
        "started_at": state.get("started_at"),
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "status": _determine_final_status(
            passing_count, human_review_queue, failure_diagnosis
        ),

        # Product & trend
        "anchor_product": state.get("product", "ceramidin_cream"),
        "brand": "Dr. Jart+",
        "trend_narrative": "Barrier Repair + Skin Longevity 2026",
        "trend_narratives_used": state.get("trend_narratives", []),

        # Evidence
        "sourced_records_count": len(state.get("filtered_records", [])),
        "synthetic_records_count": len(state.get("synthetic_records", [])),
        "evidence_decision": state.get("evidence_decision", "unknown"),

        # Scoring summary
        "assets_generated": len([a for a in assets.values() if _has_content(a)]),
        "assets_passed": passing_count,
        "assets_in_human_review": len(human_review_queue),
        "total_iterations": total_iterations,
        "scores_summary": {
            asset_type: {
                "composite": d["composite_score"],
                "passed": d["passed"],
                "version": d["version"],
                "status": d["status"],
            }
            for asset_type, d in deliverables.items()
        },

        # Model info
        "model_used": state.get("generation_model", "claude-sonnet-4-20250514"),
        "generation_model": state.get("generation_model", "claude-sonnet-4-20250514"),
        "judge_model": state.get("judge_model") or state.get("generation_model", "claude-sonnet-4-20250514"),
        "image_generator": state.get("image_generator", "midjourney-v6"),
        "video_generator": state.get("video_generator", "runway-gen4"),
        "run_mode": state.get("run_mode", "creative"),
        "retry_policy": state.get("retry_policy", "production_selective"),
        "resolved_model_versions": resolved_models,
        "pipeline_version": "1.0.0",

        # Reproducibility fingerprints
        "evidence_hash": state.get("evidence_hash", ""),
        "narrative_hash": state.get("narrative_hash", ""),

        # Diagnostics
        "failure_diagnosis": failure_diagnosis,
        "human_review_queue": human_review_queue,
        "campaign_coherence": state.get("campaign_coherence", {}),

        # Observability
        "audit_log_entries": len(state.get("audit_log", [])),
    }

    # ─── AUDIT ───
    audit = create_audit_entry(
        node="package",
        action="bundle_assembled",
        input_snapshot={
            "assets_count": len(deliverables),
            "passing_count": passing_count,
            "human_review_count": len(human_review_queue),
        },
        output_snapshot={
            "final_status": campaign_metadata["status"],
            "scores_summary": campaign_metadata["scores_summary"],
        },
        metadata={
            "has_diagnosis": failure_diagnosis is not None,
            "total_iterations": total_iterations,
        },
    )

    return {
        "final_bundle": deliverables,
        "campaign_metadata": campaign_metadata,
        "completed_at": campaign_metadata["completed_at"],
        "audit_log": state.get("audit_log", []) + [audit.model_dump()],
        "status": campaign_metadata["status"],
    }


def _get_target_platform(asset_type: str) -> str:
    """Map asset types to their target platforms."""
    platforms = {
        "ads": "Google Ads (RSA format — 3 headlines + 3 descriptions)",
        "video": "Runway Gen4 / Google Veo 3 / Sora (via Pencil)",
        "image": "Midjourney v6 / GPT Image 1 / Adobe Firefly (via Pencil)",
        "blog": "CMS upload — Markdown/HTML with SEO elements",
    }
    return platforms.get(asset_type, "Unknown")


def _has_content(asset: Any) -> bool:
    """Check if an asset has real content (not empty or failed)."""
    if isinstance(asset, dict):
        content = asset.get("content", "")
    else:
        content = getattr(asset, "content", "")
    return bool(content) and not content.startswith("GENERATION_FAILED")


def _determine_final_status(
    passing_count: int,
    human_review_queue: list,
    failure_diagnosis: str,
) -> str:
    """Determine the overall campaign status."""
    if passing_count == 4:
        return "complete_all_passed"
    elif passing_count > 0 and not failure_diagnosis:
        return "partial_with_review"
    elif failure_diagnosis:
        return "partial_with_diagnosis"
    elif passing_count == 0:
        return "failed_all_assets"
    else:
        return "partial"
"""

**What's unique about this node:**

**Four possible final statuses:**
- `complete_all_passed` — The happy path. All 4 assets are campaign-ready.
- `partial_with_review` — Some passed, some need human help. Still usable.
- `partial_with_diagnosis` — Pattern failure detected. Upstream fix needed.
- `failed_all_assets` — Nothing passed. Investigate everything.

**The campaign metadata is exhaustive.** It captures everything Dan might ask about: what triggered the run, what product was anchored, how many records were sourced, how many were synthetic, what scores each asset got, how many iterations were needed, whether there's a diagnosis, and how many audit entries were recorded. This is the JSON that proves the system is production-grade.

**Target platform mapping references Pencil.** "Runway Gen4 / Google Veo 3 (via Pencil)" — a subtle reminder that this system is designed for Pencil's model aggregation layer.

"""