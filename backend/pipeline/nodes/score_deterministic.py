"""
Score Deterministic Node
========================
Phase 3, Tier 1: Rule-based format compliance checks.
No LLM calls. Instant. Free. Deterministic.

For each asset, this node:
  1. Gets the parsed output from the agent's parser
  2. Runs all format checks from scoring_rubric.yaml
  3. Runs grounding verification (claim_linker) for blog
  4. Aggregates results into a DeterministicResult
  5. Logs everything to audit trail

The deterministic score feeds into the composite:
  composite = (deterministic * 0.25) + (brand * 0.40) + (trend * 0.35)
"""

from typing import Dict, Any, List

from backend.pipeline.state import (
    AssetType,
    DeterministicResult,
    DeterministicCheckDetail,
)
from backend.pipeline.tools.format_validator import (
    validate_ads,
    validate_video,
    validate_image,
    validate_blog,
)
from backend.pipeline.tools.claim_linker import create_grounding_check
from backend.registries.product_truth import ProductTruthRegistry
from backend.registries.source_registry import SourceRegistry
from backend.agents.ads_agent import AdsAgent
from backend.agents.video_agent import VideoAgent
from backend.agents.image_agent import ImageAgent
from backend.agents.blog_agent import BlogAgent
from backend.observability.audit_log import create_audit_entry


def _reparse_asset(asset_type: str, content: str) -> dict:
    """
    Re-run the agent's parser on the generated content.
    
    Why re-parse here instead of passing parsed data through state?
    Because the state stores raw content (the actual generated text),
    not parsed structures. This keeps the state clean and means
    the parser is the single source of truth for extraction.
    
    Each agent's parser extracts what its format needs:
      - ads: headlines list, descriptions list
      - video: scene count, has_mood, has_duration
      - image: has_ar_flag, has_style_flag
      - blog: word_count, h2_count, has_meta_description
    """
    # We instantiate agents just for their parsers — no LLM calls
    # The system_prompt doesn't matter here since we're only parsing
    parsers = {
        "ads": AdsAgent(system_prompt="").parse_response,
        "video": VideoAgent(system_prompt="").parse_response,
        "image": ImageAgent(system_prompt="").parse_response,
        "blog": BlogAgent(system_prompt="").parse_response,
    }

    parser = parsers.get(asset_type)
    if parser:
        return parser(content)
    return {}


def _run_checks(
    asset_type: str,
    content: str,
    parsed: dict,
    blocked_language: List[str],
    source_records: list,
    approved_claims: List[str],
) -> List[DeterministicCheckDetail]:
    """
    Run all deterministic checks for a given asset type.
    
    Dispatches to the appropriate validator based on asset type.
    Adds grounding check for blog (the most claim-heavy asset).
    """
    # Dispatch to format-specific validator
    if asset_type == "ads":
        checks = validate_ads(content, parsed, blocked_language)
    elif asset_type == "video":
        checks = validate_video(content, parsed, blocked_language)
    elif asset_type == "image":
        checks = validate_image(content, parsed, blocked_language)
    elif asset_type == "blog":
        checks = validate_blog(content, parsed, blocked_language)
        
        # Blog gets an EXTRA check: claim grounding verification
        # This is the anti-hallucination layer for factual content
        from backend.pipeline.state import SourceRecord
        source_record_objects = []
        for r in source_records:
            if isinstance(r, dict):
                source_record_objects.append(SourceRecord(**r))
            else:
                source_record_objects.append(r)
        
        grounding_check = create_grounding_check(
            content=content,
            source_records=source_record_objects,
            approved_claims=approved_claims,
        )
        checks.append(grounding_check)
    else:
        checks = []

    return checks


def score_deterministic(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node function.
    
    Runs rule-based checks on ALL generated assets.
    Only scores assets that have content (skips empty/failed).
    
    Args:
        state: Current pipeline state
    
    Returns:
        Partial state update with deterministic scores per asset
    """
    # Load product truth for blocked language list
    product_truth = ProductTruthRegistry()
    
    # Get source records for claim linking
    source_records = state.get("filtered_records", [])
    
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

        # Skip empty or failed assets
        if not content or content.startswith("GENERATION_FAILED"):
            # Create a failing score for missing/failed assets
            fail_result = DeterministicResult(
                asset_type=AssetType(asset_type),
                checks=[
                    DeterministicCheckDetail(
                        check_name="asset_exists",
                        passed=False,
                        expected="Generated content",
                        actual="No content or generation failed",
                        message="Asset was not generated successfully",
                    )
                ],
                checks_passed=0,
                checks_total=1,
                score=0.0,
                failures=["Asset was not generated successfully"],
            )
            
            # Initialize score dict for this asset if needed
            if asset_type not in current_scores:
                current_scores[asset_type] = {}
            if isinstance(current_scores[asset_type], dict):
                current_scores[asset_type]["deterministic"] = fail_result.model_dump()
            
            audit = create_audit_entry(
                node=f"score_deterministic.{asset_type}",
                action="skipped_missing_asset",
                input_snapshot={"asset_type": asset_type, "has_content": False},
                output_snapshot={"score": 0.0},
            )
            audit_entries.append(audit.model_dump())
            continue

        # ─── RE-PARSE the content ───
        parsed = _reparse_asset(asset_type, content)

        # ─── RUN ALL CHECKS ───
        checks = _run_checks(
            asset_type=asset_type,
            content=content,
            parsed=parsed,
            blocked_language=product_truth.blocked_language,
            source_records=source_records,
            approved_claims=product_truth.approved_claims,
        )

        # ─── AGGREGATE RESULTS ───
        checks_passed = sum(1 for c in checks if c.passed)
        checks_total = len(checks)
        score = (checks_passed / checks_total * 100) if checks_total > 0 else 0.0
        
        failures = [
            f"{c.check_name}: {c.message}"
            for c in checks if not c.passed
        ]

        result = DeterministicResult(
            asset_type=AssetType(asset_type),
            checks=checks,
            checks_passed=checks_passed,
            checks_total=checks_total,
            score=round(score, 1),
            failures=failures,
        )

        # ─── STORE IN STATE ───
        if asset_type not in current_scores:
            current_scores[asset_type] = {}
        if isinstance(current_scores[asset_type], dict):
            current_scores[asset_type]["deterministic"] = result.model_dump()

        # ─── AUDIT ───
        audit = create_audit_entry(
            node=f"score_deterministic.{asset_type}",
            action="format_compliance_check",
            input_snapshot={
                "asset_type": asset_type,
                "content_length": len(content),
                "parse_success": parsed.get("parse_success", False),
            },
            output_snapshot={
                "checks_passed": checks_passed,
                "checks_total": checks_total,
                "score": round(score, 1),
                "failures": failures,
            },
            metadata={
                "check_details": [
                    {
                        "name": c.check_name,
                        "passed": c.passed,
                        "expected": c.expected,
                        "actual": c.actual,
                    }
                    for c in checks
                ],
            },
        )
        audit_entries.append(audit.model_dump())

    return {
        "scores": current_scores,
        "audit_log": state.get("audit_log", []) + audit_entries,
        "status": "deterministic_scoring_complete",
    }