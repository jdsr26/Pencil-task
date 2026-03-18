"""
Score LLM Judge Node
====================
Phase 3, Tier 2: Subjective quality evaluation via LLM-as-judge.

For each asset, this node:
  1. Calls the judge agent for brand_alignment + trend_alignment scores
  2. Combines with Tier 1 deterministic scores to calculate composite
  3. Applies weights from scoring_rubric.yaml
  4. Makes pass/fail decision against threshold
  5. Merges all feedback (deterministic + LLM) into all_feedback list

The composite formula:
  composite = (deterministic * 0.25) + (brand_alignment * 0.40) + (trend_alignment * 0.35)

Pass threshold: composite >= 85 (configurable in scoring_rubric.yaml)
"""

import yaml
from typing import Dict, Any, List

from backend.pipeline.state import (
    AssetType,
    AssetScore,
    LLMJudgeResult,
    DeterministicResult,
    SourceRecord,
)
from backend.agents.judge_agent import JudgeAgent
from backend.observability.audit_log import create_audit_entry


def _load_scoring_config() -> Dict[str, Any]:
    """Load scoring weights and thresholds from config."""
    with open("config/scoring_rubric.yaml", "r") as f:
        return yaml.safe_load(f)


def _calculate_composite(
    deterministic_score: float,
    brand_alignment: int,
    trend_alignment: int,
    weights: Dict[str, float],
) -> float:
    """
    Calculate the weighted composite score.
    
    Formula:
      composite = (deterministic * weight_format)
               + (brand_alignment * weight_brand)
               + (trend_alignment * weight_trend)
    
    Args:
        deterministic_score: 0-100 from Tier 1 (format checks)
        brand_alignment: 0-100 from Tier 2 LLM judge
        trend_alignment: 0-100 from Tier 2 LLM judge
        weights: From scoring_rubric.yaml
    
    Returns:
        Composite score 0-100
    """
    w_format = weights.get("format_compliance", 0.25)
    w_brand = weights.get("brand_alignment", 0.40)
    w_trend = weights.get("trend_alignment", 0.35)

    composite = (
        deterministic_score * w_format
        + brand_alignment * w_brand
        + trend_alignment * w_trend
    )

    return round(composite, 1)


def _merge_feedback(
    deterministic_failures: List[str],
    llm_feedback: List[str],
) -> List[str]:
    """
    Merge feedback from both scoring tiers into one list.
    
    This merged list is what gets injected into the retry prompt
    if the asset fails. The generation agent sees ALL reasons
    for failure — both format issues AND subjective issues.
    
    Deterministic failures are prefixed with [FORMAT] and
    LLM feedback with [QUALITY] so the generation agent can
    distinguish between them.
    """
    merged = []

    for failure in deterministic_failures:
        merged.append(f"[FORMAT] {failure}")

    for fb in llm_feedback:
        # Skip system/error messages from judge fallback
        if fb.startswith("SYSTEM:"):
            merged.append(fb)
        else:
            merged.append(f"[QUALITY] {fb}")

    return merged


def score_llm_judge(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node function.
    
    Runs the LLM judge on each asset, calculates composite scores,
    and makes pass/fail decisions.
    
    Only scores assets that:
      - Have content (not empty or failed)
      - Haven't already passed (skip on retry)
    
    Args:
        state: Current pipeline state
    
    Returns:
        Partial state update with complete scores per asset
    """
    # Load config
    rubric_config = _load_scoring_config()
    weights = rubric_config.get("weights", {})
    threshold = rubric_config.get("threshold", {}).get("composite_pass", 85)

    # Initialize judge
    judge = JudgeAgent()

    # Get trend narratives and sourced claims for the judge
    trend_narratives = state.get("trend_narratives", [])
    
    # Build sourced claims list for the judge to check grounding
    filtered_records = state.get("filtered_records", [])
    sourced_claims = []
    for record in filtered_records:
        if isinstance(record, dict):
            sourced_claims.extend(record.get("key_claims", []))
        else:
            sourced_claims.extend(record.key_claims)

    assets = state.get("assets", {})
    current_scores = state.get("scores", {})
    audit_entries = []

    for asset_type in ["ads", "video", "image", "blog"]:
        asset = assets.get(asset_type, {})

        # Get content
        if isinstance(asset, dict):
            content = asset.get("content", "")
        else:
            content = getattr(asset, "content", "")

        # ─── SKIP empty/failed assets ───
        if not content or content.startswith("GENERATION_FAILED"):
            # Deterministic scoring already created a failing score
            # Just ensure we have a complete AssetScore
            if asset_type not in current_scores:
                current_scores[asset_type] = {}
            
            score_data = current_scores[asset_type]
            if isinstance(score_data, dict) and "llm_judge" not in score_data:
                score_data["llm_judge"] = LLMJudgeResult(
                    asset_type=AssetType(asset_type),
                    brand_alignment=0,
                    trend_alignment=0,
                    feedback=["Asset was not generated — cannot evaluate"],
                ).model_dump()
                score_data["composite"] = 0.0
                score_data["passed"] = False
                score_data["all_feedback"] = ["Asset was not generated successfully"]
            
            continue

        # ─── SKIP assets that already passed ───
        score_data = current_scores.get(asset_type, {})
        if isinstance(score_data, dict) and score_data.get("passed", False):
            audit = create_audit_entry(
                node=f"score_llm_judge.{asset_type}",
                action="skipped_passed_asset",
                input_snapshot={"reason": "Asset already passed scoring"},
                output_snapshot={"composite": score_data.get("composite", 0)},
            )
            audit_entries.append(audit.model_dump())
            continue

        # ─── RUN LLM JUDGE ───
        try:
            judge_result, judge_audit = judge.score(
                asset_type=AssetType(asset_type),
                asset_content=content,
                trend_narratives=trend_narratives,
                sourced_claims=sourced_claims,
            )
            audit_entries.append(judge_audit.model_dump())

        except Exception as e:
            # Judge completely failed — use conservative fallback
            judge_result = LLMJudgeResult(
                asset_type=AssetType(asset_type),
                brand_alignment=50,
                trend_alignment=50,
                feedback=[f"SYSTEM: Judge error — {str(e)[:100]}"],
            )
            error_audit = create_audit_entry(
                node=f"score_llm_judge.{asset_type}",
                action="judge_error",
                input_snapshot={"asset_type": asset_type},
                output_snapshot={"error": str(e)[:200]},
            )
            audit_entries.append(error_audit.model_dump())

        # ─── GET DETERMINISTIC SCORE ───
        if asset_type not in current_scores:
            current_scores[asset_type] = {}
        
        score_data = current_scores[asset_type]
        
        det_data = score_data.get("deterministic", {})
        if isinstance(det_data, dict):
            deterministic_score = det_data.get("score", 0.0)
            deterministic_failures = det_data.get("failures", [])
        else:
            deterministic_score = getattr(det_data, "score", 0.0)
            deterministic_failures = getattr(det_data, "failures", [])

        # ─── CALCULATE COMPOSITE ───
        composite = _calculate_composite(
            deterministic_score=deterministic_score,
            brand_alignment=judge_result.brand_alignment,
            trend_alignment=judge_result.trend_alignment,
            weights=weights,
        )

        passed = composite >= threshold

        # ─── MERGE ALL FEEDBACK ───
        all_feedback = _merge_feedback(
            deterministic_failures=deterministic_failures,
            llm_feedback=judge_result.feedback,
        )

        # ─── STORE COMPLETE SCORE ───
        score_data["llm_judge"] = judge_result.model_dump()
        score_data["composite"] = composite
        score_data["passed"] = passed
        score_data["asset_type"] = asset_type
        score_data["all_feedback"] = all_feedback
        current_scores[asset_type] = score_data

        # ─── AUDIT ───
        scoring_audit = create_audit_entry(
            node=f"score_llm_judge.{asset_type}",
            action="composite_score_calculated",
            input_snapshot={
                "deterministic_score": deterministic_score,
                "brand_alignment": judge_result.brand_alignment,
                "trend_alignment": judge_result.trend_alignment,
                "weights": weights,
            },
            output_snapshot={
                "composite": composite,
                "passed": passed,
                "threshold": threshold,
                "margin": round(composite - threshold, 1),
                "feedback_count": len(all_feedback),
            },
            metadata={
                "all_feedback": all_feedback,
                "judge_validation": judge_audit.metadata.get("validation", "unknown")
                    if 'judge_audit' in dir() else "unknown",
            },
        )
        audit_entries.append(scoring_audit.model_dump())

    return {
        "scores": current_scores,
        "audit_log": state.get("audit_log", []) + audit_entries,
        "status": "llm_scoring_complete",
    }