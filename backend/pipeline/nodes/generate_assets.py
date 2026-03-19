"""
Generate Assets Node
====================
Phase 2 core. Orchestrates 4 creative agents to generate
all campaign assets.

Key behaviors:
  - On FIRST PASS: generates all 4 assets
  - On RETRY: regenerates ONLY assets that failed scoring
    (passing assets are preserved — never re-generate what works)
  - Feedback injection: failed assets get their scoring feedback
    appended to the prompt via the self-correction mechanism

This is the node that loops — route_decision sends control
back here with updated feedback when assets fail scoring.
"""

import yaml
from typing import Dict, Any, List

from backend.agents.ads_agent import AdsAgent
from backend.agents.video_agent import VideoAgent
from backend.agents.image_agent import ImageAgent
from backend.agents.blog_agent import BlogAgent
from backend.registries.product_truth import ProductTruthRegistry
from backend.pipeline.state import AssetOutput
from backend.observability.audit_log import create_audit_entry


def _load_brand_voice() -> str:
    """
    Load brand voice config and assemble the system prompt.
    
    This reads brand_voice.yaml and constructs the system prompt
    that every creative agent uses. The system prompt includes:
      - Brand personality
      - Tone dimensions (formality, confidence, humor, innovation)
      - Audience definition
      - Forbidden patterns
      - Few-shot examples
      - Trend positioning guidance
    """
    with open("config/brand_voice.yaml", "r") as f:
        config = yaml.safe_load(f)

    voice = config.get("voice", {})
    audience = config.get("audience", {})
    forbidden = config.get("forbidden_patterns", {})
    examples = config.get("few_shot_examples", {})
    trend_voice = config.get("trend_voice", {})

    # Assemble few-shot examples
    good_examples = "\n".join(
        f'  ✅ "{ex["text"]}"\n     Why: {ex["why"]}'
        for ex in examples.get("excellent", [])
    )
    bad_examples = "\n".join(
        f'  ❌ "{ex["text"]}"\n     Issue: {ex["issue"]}\n     Fix: {ex["fix"]}'
        for ex in examples.get("poor", [])
    )

    # Assemble forbidden patterns
    forbidden_text = ""
    for pattern_name, pattern_data in forbidden.items():
        forbidden_text += f"\n  {pattern_name.upper()}: {pattern_data.get('description', '')}"
        forbidden_text += f"\n    Examples to AVOID: {', '.join(pattern_data.get('examples', [])[:2])}"
        forbidden_text += f"\n    Correction: {pattern_data.get('correction', '')}"

    # Assemble trend positioning
    trend_do = "\n".join(f"  - {d}" for d in trend_voice.get("positioning", {}).get("do", []))
    trend_dont = "\n".join(f"  - {d}" for d in trend_voice.get("positioning", {}).get("dont", []))

    system_prompt = f"""You are the creative voice of Dr. Jart+, a Korean dermatological skincare brand where "Doctor Joins Art."

YOUR VOICE: {voice.get('personality', '')}

TONE DIMENSIONS:
- Formality: {voice.get('dimensions', {}).get('formality', {}).get('calibration', '')}
- Confidence: {voice.get('dimensions', {}).get('confidence', {}).get('calibration', '')}
- Humor: {voice.get('dimensions', {}).get('humor', {}).get('calibration', '')}
- Innovation: {voice.get('dimensions', {}).get('innovation', {}).get('calibration', '')}

AUDIENCE: {audience.get('primary_age', '18-35')}, {audience.get('mindset', '')}
Speak to them as: {audience.get('tone_toward_audience', 'Inclusive, gender-neutral')}

FORBIDDEN PATTERNS (violating these will FAIL brand alignment scoring):
{forbidden_text}

TREND POSITIONING:
Narrative: {trend_voice.get('narrative', '')}
DO:
{trend_do}
DON'T:
{trend_dont}

EXAMPLES OF EXCELLENT COPY:
{good_examples}

EXAMPLES OF POOR COPY (avoid these patterns):
{bad_examples}
"""
    return system_prompt


def _build_context(
    state: Dict[str, Any],
    product_truth: ProductTruthRegistry,
) -> Dict[str, Any]:
    """
    Build the context dict that gets injected into every agent's prompt.
    
    This is the KNOWLEDGE layer — product truth + trend data.
    Same context for all 4 agents, ensuring consistency.
    """
    # Get trend narratives (from narrative_synth node)
    # Falls back to raw source claims if narratives haven't been generated yet
    trend_narratives = state.get("trend_narratives", [])
    
    if not trend_narratives:
        # Fallback: extract key claims from filtered records
        filtered = state.get("filtered_records", [])
        trend_narratives = []
        for record in filtered[:5]:
            if isinstance(record, dict):
                claims = record.get("key_claims", [])
            else:
                claims = record.key_claims
            trend_narratives.extend(claims[:2])

    # Get sourced claims for grounding
    filtered = state.get("filtered_records", [])
    sourced_claims = []
    for record in filtered:
        if isinstance(record, dict):
            for claim in record.get("key_claims", []):
                source_name = record.get("source_name", "Unknown")
                sourced_claims.append(f"{claim} (source: {source_name})")
        else:
            for claim in record.key_claims:
                sourced_claims.append(f"{claim} (source: {record.source_name})")

    return {
        "product": product_truth.get_product_context(),
        "product_name": product_truth.product.get("name", "Dr. Jart+ product"),
        "product_line": product_truth.product.get("line", "Dr. Jart+"),
        "product_brand": product_truth.product.get("brand", "Dr. Jart+"),
        "trend_narratives": trend_narratives,
        "sourced_claims": sourced_claims,
        "competitor_gaps": [
            f"{c['name']}: {c['positioning_gap']}"
            for c in product_truth.competitors
        ],
    }


def generate_assets(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node function.
    
    Orchestrates all 4 creative agents. Handles both:
      - First pass: generate all 4 assets
      - Retry: regenerate ONLY failed assets with feedback injection
    
    Args:
        state: Current pipeline state
    
    Returns:
        Partial state update with generated assets + audit entries
    """
    # Load configs — use the anchor product selected for this run
    system_prompt = _load_brand_voice()
    product_key = state.get("product", "ceramidin_cream")
    product_truth = ProductTruthRegistry(product_key=product_key)

    # Build shared context (same for all agents)
    context = _build_context(state, product_truth)

    generation_model = state.get("generation_model", "claude-sonnet-4-20250514")
    image_generator = state.get("image_generator", "midjourney-v6")
    video_generator = state.get("video_generator", "runway-gen4")

    # Initialize agents
    agents = {
        "ads": AdsAgent(system_prompt=system_prompt, model=generation_model),
        "video": VideoAgent(
            system_prompt=system_prompt,
            model=generation_model,
            target_generator=video_generator,
        ),
        "image": ImageAgent(
            system_prompt=system_prompt,
            model=generation_model,
            target_generator=image_generator,
        ),
        "blog": BlogAgent(system_prompt=system_prompt, model=generation_model),
    }

    # Get current state
    current_assets = state.get("assets", {})
    current_scores = state.get("scores", {})
    iteration_counts = state.get("iteration_counts", {
        "ads": 0, "video": 0, "image": 0, "blog": 0
    })
    audit_entries = []

    # Generate each asset
    for asset_type, agent in agents.items():

        # ─── SKIP assets that already PASSED scoring ───
        # This is critical for retry behavior:
        # Only regenerate what failed, preserve what passed.
        asset_score = current_scores.get(asset_type, {})
        if isinstance(asset_score, dict):
            already_passed = asset_score.get("passed", False)
        else:
            already_passed = getattr(asset_score, "passed", False)

        if already_passed:
            # This asset passed — don't touch it
            audit = create_audit_entry(
                node=f"generate_assets.{asset_type}",
                action="skipped_passed_asset",
                input_snapshot={"reason": "Asset already passed scoring"},
                output_snapshot={"version": _get_version(current_assets, asset_type)},
                metadata={"iteration": iteration_counts.get(asset_type, 0)},
            )
            audit_entries.append(audit.model_dump())
            continue

        # ─── GET FEEDBACK for retry ───
        # If this is a retry, extract feedback from the previous score
        feedback = _get_feedback(current_assets, asset_type)

        # ─── GENERATE ───
        try:
            asset_output, audit = agent.generate(
                context=context,
                feedback=feedback if feedback else None,
            )

            # Update version number
            current_version = _get_version(current_assets, asset_type)
            new_version = current_version + 1 if feedback else 1
            asset_output.version = new_version

            # Preserve feedback history
            if feedback:
                asset_output.feedback_history = feedback

            # Store in state
            current_assets[asset_type] = asset_output.model_dump()

            # Update iteration count
            iteration_counts[asset_type] = iteration_counts.get(asset_type, 0) + 1

            audit_entries.append(audit.model_dump())

        except RuntimeError as e:
            # Agent failed (API error after retries)
            error_audit = create_audit_entry(
                node=f"generate_assets.{asset_type}",
                action="generation_failed",
                input_snapshot={"asset_type": asset_type},
                output_snapshot={"error": str(e)},
                metadata={
                    "iteration": iteration_counts.get(asset_type, 0),
                    "had_feedback": feedback is not None,
                },
            )
            audit_entries.append(error_audit.model_dump())

            # Store error state so pipeline doesn't crash
            current_assets[asset_type] = AssetOutput(
                content=f"GENERATION_FAILED: {str(e)}",
                version=_get_version(current_assets, asset_type) + 1,
                feedback_history=feedback or [],
            ).model_dump()

    return {
        "assets": current_assets,
        "iteration_counts": iteration_counts,
        "audit_log": state.get("audit_log", []) + audit_entries,
        "status": "generation_complete",
    }


def _get_feedback(assets: Dict, asset_type: str) -> List[str]:
    """
    Extract feedback history from a previous version of an asset.
    
    This is what drives the self-correction mechanism.
    If the asset was scored and failed, its all_feedback list
    was copied into feedback_history by route_decision.
    """
    asset = assets.get(asset_type, {})
    if isinstance(asset, dict):
        return asset.get("feedback_history", [])
    return getattr(asset, "feedback_history", [])


def _get_version(assets: Dict, asset_type: str) -> int:
    """Get the current version number of an asset."""
    asset = assets.get(asset_type, {})
    if isinstance(asset, dict):
        return asset.get("version", 0)
    return getattr(asset, "version", 0)