"""
Campaign Coherence Score Node
=============================
Checks cross-asset consistency. Individual assets may pass
individually but conflict with each other.

This is a Tier 3 check — runs after per-asset scoring.
For MVP, this is a simplified version that checks basic consistency.
In production, this would use an LLM call to evaluate coherence.
"""

from typing import Dict, Any, List
from backend.pipeline.state import CampaignCoherence
from backend.observability.audit_log import create_audit_entry


def score_campaign(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node function.
    Checks cross-asset coherence using rule-based checks.
    """
    assets = state.get("assets", {})
    scores = state.get("scores", {})

    # Only check assets that have content
    asset_contents = {}
    for asset_type in ["ads", "video", "image", "blog"]:
        asset = assets.get(asset_type, {})
        content = asset.get("content", "") if isinstance(asset, dict) else ""
        if content and not content.startswith("GENERATION_FAILED"):
            asset_contents[asset_type] = content.lower()

    if len(asset_contents) < 2:
        # Not enough assets to check coherence
        coherence = CampaignCoherence(
            coherent=True,
            issues=["Insufficient assets for coherence check"],
            narrative_consistent=True,
            tone_consistent=True,
            product_consistent=True,
            cta_aligned=True,
        )
        audit = create_audit_entry(
            node="score_campaign",
            action="skipped_insufficient_assets",
            input_snapshot={"asset_count": len(asset_contents)},
            output_snapshot={"coherent": True},
        )
        return {
            "campaign_coherence": coherence.model_dump(),
            "audit_log": state.get("audit_log", []) + [audit.model_dump()],
        }

    issues = []

    # Resolve product terms from state — allows any anchor product to be checked
    product_key = state.get("product", "ceramidin_cream")
    product_term_map = {
        "ceramidin_cream": ["ceramidin", "dr. jart", "dr jart"],
        "cicapair_treatment": ["cicapair", "tiger grass", "dr. jart", "dr jart"],
        "dermask_micro_jet": ["dermask", "micro jet", "dr. jart", "dr jart"],
    }
    product_terms = product_term_map.get(product_key, ["dr. jart", "dr jart"])

    # Check 1: Product consistency — all assets mention the same product
    product_consistent = True
    for asset_type, content in asset_contents.items():
        if not any(term in content for term in product_terms):
            product_consistent = False
            issues.append(f"{asset_type} does not mention Ceramidin™ or Dr. Jart+")

    # Check 2: Narrative consistency — all assets reference barrier/ceramide
    narrative_terms = ["barrier", "ceramide", "repair", "skin barrier"]
    narrative_consistent = True
    for asset_type, content in asset_contents.items():
        if not any(term in content for term in narrative_terms):
            narrative_consistent = False
            issues.append(f"{asset_type} does not reference barrier repair narrative")

    # Check 3: CTA alignment — ensure no conflicting purchase signals
    # (e.g. one asset says "shop now" while another says "not available yet")
    unavailable_signals = ["coming soon", "not available", "out of stock", "waitlist"]
    available_signals = ["shop now", "buy now", "get it now", "available at", "order now"]
    has_unavailable = any(
        sig in content for content in asset_contents.values() for sig in unavailable_signals
    )
    has_available = any(
        sig in content for content in asset_contents.values() for sig in available_signals
    )
    cta_aligned = not (has_unavailable and has_available)
    if not cta_aligned:
        issues.append("CTA conflict: some assets signal availability while others signal unavailability")

    # Check 4: Tone consistency — detect forbidden patterns across assets
    # Full LLM-based tone scoring would run here in production
    forbidden_signals = ["cure", "prescription", "miracle", "guaranteed results", "instant transformation"]
    tone_consistent = True
    for asset_type, content in asset_contents.items():
        if any(sig in content for sig in forbidden_signals):
            tone_consistent = False
            issues.append(f"{asset_type} contains forbidden language that violates brand tone")

    coherent = product_consistent and narrative_consistent and tone_consistent and cta_aligned

    coherence = CampaignCoherence(
        coherent=coherent,
        issues=issues,
        narrative_consistent=narrative_consistent,
        tone_consistent=tone_consistent,
        product_consistent=product_consistent,
        cta_aligned=cta_aligned,
    )

    audit = create_audit_entry(
        node="score_campaign",
        action="coherence_check",
        input_snapshot={"assets_checked": list(asset_contents.keys())},
        output_snapshot={
            "coherent": coherent,
            "issues": issues,
            "product_consistent": product_consistent,
            "narrative_consistent": narrative_consistent,
        },
    )

    return {
        "campaign_coherence": coherence.model_dump(),
        "audit_log": state.get("audit_log", []) + [audit.model_dump()],
    }
