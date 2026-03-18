"""
Route Decision Node
===================
The smartest node in the pipeline. Makes routing decisions
based on scoring results.

Five possible outcomes:
  1. ALL PASS + COHERENT → route to package (happy path)
  2. ALL PASS + INCOHERENT → diagnose coherence failure, route to package with diagnosis
  3. INDIVIDUAL FAIL → inject feedback, route back to generate_assets
  4. PATTERN FAILURE → diagnose upstream cause, DON'T retry
  5. MAX RETRIES → move to human review queue, route to package

This node also performs UPSTREAM FAULT DIAGNOSIS:
  If ≥3 assets fail on the SAME dimension, the problem isn't
  the individual assets — it's upstream (bad source data,
  weak narrative, drifting brand voice). Retrying won't help.
  The system identifies WHERE to look, not just WHAT failed.

This is what separates "prompt engineer" from
"engineer of LLM behavior."
"""

import yaml
from typing import Dict, Any, List, Tuple

from backend.observability.audit_log import create_audit_entry


def _load_thresholds() -> Dict[str, Any]:
    """Load retry limits and circuit breaker config."""
    with open("config/scoring_rubric.yaml", "r") as f:
        config = yaml.safe_load(f)
    return config.get("threshold", {})


def _get_failing_assets(scores: Dict[str, Any]) -> List[str]:
    """Get list of asset types that failed scoring."""
    failing = []
    for asset_type in ["ads", "video", "image", "blog"]:
        score_data = scores.get(asset_type, {})
        if isinstance(score_data, dict):
            if not score_data.get("passed", False):
                failing.append(asset_type)
    return failing


def _get_passing_assets(scores: Dict[str, Any]) -> List[str]:
    """Get list of asset types that passed scoring."""
    passing = []
    for asset_type in ["ads", "video", "image", "blog"]:
        score_data = scores.get(asset_type, {})
        if isinstance(score_data, dict):
            if score_data.get("passed", False):
                passing.append(asset_type)
    return passing


def _diagnose_failure_pattern(scores: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Detect if multiple assets fail on the SAME scoring dimension.
    
    This is upstream fault diagnosis. If 3+ assets all fail on
    trend_alignment, the problem isn't the individual prompts —
    it's the narrative synthesis or source data.
    
    Returns:
        Tuple of (pattern_detected: bool, diagnosis: str)
    """
    # Collect per-dimension failures across all assets
    brand_failures = 0
    trend_failures = 0
    format_failures = 0

    for asset_type in ["ads", "video", "image", "blog"]:
        score_data = scores.get(asset_type, {})
        if not isinstance(score_data, dict):
            continue
        
        if score_data.get("passed", True):
            continue  # Only look at failing assets

        # Check which dimension dragged the score down
        llm_judge = score_data.get("llm_judge", {})
        deterministic = score_data.get("deterministic", {})

        # Brand alignment below 75 = brand failure
        if isinstance(llm_judge, dict) and llm_judge.get("brand_alignment", 100) < 75:
            brand_failures += 1

        # Trend alignment below 75 = trend failure
        if isinstance(llm_judge, dict) and llm_judge.get("trend_alignment", 100) < 75:
            trend_failures += 1

        # Deterministic score below 75 = format failure
        if isinstance(deterministic, dict) and deterministic.get("score", 100) < 75:
            format_failures += 1

    # Circuit breaker: 3+ assets failing on same dimension = pattern
    if trend_failures >= 3:
        return True, (
            "PATTERN FAILURE — TREND ALIGNMENT: "
            f"{trend_failures}/4 assets scored below 75 on trend alignment. "
            "Root cause is likely upstream: narrative synthesis may be weak, "
            "or sourced data doesn't provide enough trend signal. "
            "ACTION: Review Phase 1 source data and Phase 2 narrative synthesis. "
            "Do NOT retry individual assets — the input data needs improvement."
        )

    if brand_failures >= 3:
        return True, (
            "PATTERN FAILURE — BRAND ALIGNMENT: "
            f"{brand_failures}/4 assets scored below 75 on brand alignment. "
            "Root cause is likely in the brand voice enforcement layer: "
            "system prompt may need updating, few-shot examples may be stale, "
            "or the tone dimensions need recalibration. "
            "ACTION: Review brand_voice.yaml system prompt and few-shot examples. "
            "Do NOT retry individual assets — the voice profile needs adjustment."
        )

    if format_failures >= 3:
        return True, (
            "PATTERN FAILURE — FORMAT COMPLIANCE: "
            f"{format_failures}/4 assets scored below 75 on format compliance. "
            "Root cause is likely in the prompt templates: "
            "format specifications may be unclear, or the output format "
            "instructions need to be more explicit. "
            "ACTION: Review agent task prompts and format requirements. "
            "Do NOT retry individual assets — the templates need fixing."
        )

    return False, ""


def _check_max_retries(
    failing_assets: List[str],
    iteration_counts: Dict[str, int],
    max_retries: int,
) -> Tuple[List[str], List[str]]:
    """
    Split failing assets into retryable vs exhausted.
    
    Args:
        failing_assets: Asset types that failed scoring
        iteration_counts: How many times each has been generated
        max_retries: Maximum allowed attempts
    
    Returns:
        Tuple of (retryable: list, exhausted: list)
    """
    retryable = []
    exhausted = []

    for asset_type in failing_assets:
        attempts = iteration_counts.get(asset_type, 0)
        if attempts >= max_retries:
            exhausted.append(asset_type)
        else:
            retryable.append(asset_type)

    return retryable, exhausted


def _inject_feedback_for_retry(
    assets: Dict[str, Any],
    scores: Dict[str, Any],
    retryable: List[str],
) -> Dict[str, Any]:
    """
    Copy scoring feedback into asset's feedback_history
    so the generation agent receives corrections on retry.
    
    This is the BRIDGE between scoring and self-correction.
    The feedback flows: score → asset.feedback_history → generation prompt.
    """
    for asset_type in retryable:
        score_data = scores.get(asset_type, {})
        all_feedback = []
        
        if isinstance(score_data, dict):
            all_feedback = score_data.get("all_feedback", [])

        asset = assets.get(asset_type, {})
        if isinstance(asset, dict):
            # Accumulate feedback — don't replace, append
            existing = asset.get("feedback_history", [])
            asset["feedback_history"] = existing + all_feedback
            # Reset passed flag so generate_assets knows to regenerate
            assets[asset_type] = asset

        # Also reset the score's passed flag
        if isinstance(score_data, dict):
            score_data["passed"] = False

    return assets


def _build_human_review_entry(
    asset_type: str,
    assets: Dict[str, Any],
    scores: Dict[str, Any],
    iteration_counts: Dict[str, int],
) -> Dict[str, Any]:
    """
    Build a detailed human review queue entry for an exhausted asset.
    
    Includes everything a human reviewer needs:
      - The final version of the asset
      - All scores across all attempts
      - Complete feedback history
      - Recommendation for what to fix
    """
    asset = assets.get(asset_type, {})
    score_data = scores.get(asset_type, {})

    content = asset.get("content", "") if isinstance(asset, dict) else ""
    version = asset.get("version", 0) if isinstance(asset, dict) else 0
    feedback_history = asset.get("feedback_history", []) if isinstance(asset, dict) else []

    composite = score_data.get("composite", 0) if isinstance(score_data, dict) else 0
    all_feedback = score_data.get("all_feedback", []) if isinstance(score_data, dict) else []

    return {
        "asset_type": asset_type,
        "final_version": version,
        "attempts": iteration_counts.get(asset_type, 0),
        "final_composite_score": composite,
        "content_preview": content[:300] + "..." if len(content) > 300 else content,
        "all_feedback": all_feedback,
        "feedback_history": feedback_history,
        "recommendation": _generate_recommendation(asset_type, score_data),
    }


def _generate_recommendation(asset_type: str, score_data: Dict) -> str:
    """Generate a human-readable recommendation for what to fix."""
    if not isinstance(score_data, dict):
        return "Unable to generate recommendation — score data missing."

    llm_judge = score_data.get("llm_judge", {})
    deterministic = score_data.get("deterministic", {})

    issues = []

    # Check which dimension is weakest
    if isinstance(llm_judge, dict):
        brand = llm_judge.get("brand_alignment", 0)
        trend = llm_judge.get("trend_alignment", 0)
        if brand < 75:
            issues.append(f"Brand alignment is low ({brand}/100) — review tone and voice compliance")
        if trend < 75:
            issues.append(f"Trend alignment is low ({trend}/100) — strengthen connection to barrier repair narrative")

    if isinstance(deterministic, dict):
        det_score = deterministic.get("score", 0)
        if det_score < 75:
            failures = deterministic.get("failures", [])
            issues.append(f"Format compliance is low ({det_score}/100) — fix: {'; '.join(failures[:3])}")

    if not issues:
        return "Asset is close to passing — minor adjustments needed across dimensions."

    return " | ".join(issues)


def route_decision(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node function.
    
    Analyzes all scores and decides the next step:
      1. All pass → "package" (done!)
      2. Pattern failure → "package" with diagnosis (don't retry upstream issues)
      3. Individual fails, retries left → "generate_assets" (retry with feedback)
      4. Max retries exceeded → "package" with human review queue
    
    Returns a special key "next_node" that graph.py uses
    for conditional routing.
    
    Args:
        state: Current pipeline state with scores for all assets
    
    Returns:
        Partial state update including routing decision
    """
    thresholds = _load_thresholds()
    max_retries = thresholds.get("max_retries", 3)
    circuit_breaker = thresholds.get("circuit_breaker_count", 3)

    scores = state.get("scores", {})
    assets = state.get("assets", {})
    iteration_counts = state.get("iteration_counts", {})
    human_review_queue = state.get("human_review_queue", [])
    campaign_coherence = state.get("campaign_coherence", {})

    # ─── STEP 1: Who passed? Who failed? ───
    failing = _get_failing_assets(scores)
    passing = _get_passing_assets(scores)

    # ─── STEP 1b: Check campaign-level coherence (Tier 3) ───
    # Even if all individual assets pass, incoherence across the bundle is a failure.
    coherence_issues = []
    if isinstance(campaign_coherence, dict) and not campaign_coherence.get("coherent", True):
        coherence_issues = campaign_coherence.get("issues", [])

    # ─── STEP 2: Check for PATTERN FAILURE (upstream diagnosis) ───
    pattern_detected, diagnosis = _diagnose_failure_pattern(scores)

    # Append coherence diagnosis to pattern diagnosis if both triggered
    if coherence_issues:
        coherence_note = (
            "CAMPAIGN COHERENCE FAILURE: Assets passed individual scoring but "
            f"failed cross-asset consistency checks: {'; '.join(coherence_issues)}. "
            "Review narrative synthesis to ensure consistent product + tone signal."
        )
        diagnosis = (diagnosis + " | " + coherence_note) if diagnosis else coherence_note
        pattern_detected = True

    # ─── STEP 3: Check retry limits ───
    retryable, exhausted = _check_max_retries(failing, iteration_counts, max_retries)

    # ─── STEP 4: Build human review entries for exhausted assets ───
    new_review_entries = []
    for asset_type in exhausted:
        entry = _build_human_review_entry(
            asset_type, assets, scores, iteration_counts
        )
        new_review_entries.append(entry)
        human_review_queue.append(asset_type)

    # ─── STEP 5: ROUTING DECISION ───
    if len(failing) == 0 and not coherence_issues:
        # ✅ ALL PASS — individual scoring + campaign coherence both clear
        next_node = "package"
        decision = "all_passed"
        decision_detail = f"All 4 assets passed scoring and campaign coherence check. Passing: {passing}"

    elif len(failing) == 0 and coherence_issues:
        # ⚠️ COHERENCE FAILURE — individual assets passed but bundle is incoherent.
        # Retrying individual assets won't fix this — the issue is upstream
        # (narrative synthesis or brand voice drift across asset types).
        next_node = "package"
        decision = "coherence_failure"
        decision_detail = diagnosis

    elif pattern_detected:
        # ⚠️ PATTERN FAILURE — don't retry, diagnose upstream
        next_node = "package"
        decision = "pattern_failure"
        decision_detail = diagnosis
        # Don't inject feedback — retrying won't fix an upstream issue

    elif len(retryable) > 0:
        # 🔄 INDIVIDUAL FAILS — retry with targeted feedback
        next_node = "generate_assets"
        decision = "retry"
        decision_detail = (
            f"Retrying {len(retryable)} asset(s): {retryable}. "
            f"Passed: {passing}. "
            f"Exhausted (→ human review): {exhausted if exhausted else 'none'}."
        )
        # Inject feedback into assets for retry
        assets = _inject_feedback_for_retry(assets, scores, retryable)

    else:
        # 🛑 ALL FAILING ASSETS EXHAUSTED — nothing left to retry
        next_node = "package"
        decision = "max_retries_exhausted"
        decision_detail = (
            f"All failing assets exhausted max retries ({max_retries}). "
            f"Passed: {passing}. "
            f"Sent to human review: {exhausted}."
        )

    # ─── AUDIT ───
    audit = create_audit_entry(
        node="route_decision",
        action=decision,
        input_snapshot={
            "passing_assets": passing,
            "failing_assets": failing,
            "iteration_counts": iteration_counts,
            "max_retries": max_retries,
        },
        output_snapshot={
            "next_node": next_node,
            "decision": decision,
            "detail": decision_detail,
            "retryable": retryable,
            "exhausted": exhausted,
            "pattern_detected": pattern_detected,
            "human_review_entries": len(new_review_entries),
        },
        metadata={
            "diagnosis": diagnosis if pattern_detected else None,
            "human_review_queue": human_review_queue,
        },
    )

    return {
        "assets": assets,
        "scores": scores,
        "human_review_queue": human_review_queue,
        "failure_diagnosis": diagnosis if pattern_detected else state.get("failure_diagnosis"),
        "next_node": next_node,  # Used by graph.py for conditional routing
        "audit_log": state.get("audit_log", []) + [audit.model_dump()],
        "status": f"route_decision_{decision}",
    }