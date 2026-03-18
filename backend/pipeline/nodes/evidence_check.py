"""
Evidence Sufficiency Check Node
===============================
Decides whether there's enough grounded data to proceed
with asset generation.

Three outcomes:
  SUFFICIENT (≥6 records, ≥3 categories) → proceed
  WEAK (3-5 records OR <3 categories) → add synthetic supplements, proceed
  POOR (<3 records) → stop pipeline, escalate

This prevents the system from generating content built on thin evidence.
The task brief explicitly allows synthetic content "when real-world
sourced content is scarce or insufficient" — this node operationalizes that rule.
"""

import yaml
from typing import Dict, Any, List

from backend.pipeline.state import SourceRecord, EvidenceDecision
from backend.observability.audit_log import create_audit_entry


def _load_evidence_thresholds() -> Dict[str, Any]:
    """Load thresholds from sources.yaml."""
    with open("config/sources.yaml", "r") as f:
        config = yaml.safe_load(f)
    return config.get("evidence_thresholds", {})


def _generate_synthetic_record(
    missing_category: str,
    record_index: int,
) -> Dict[str, Any]:
    """
    Generate a synthetic source record to fill a category gap.
    
    In production, this would call an LLM to generate plausible
    trend data. For the MVP, we generate a structured placeholder
    that's clearly tagged as synthetic.
    
    The key rule: synthetic records are ALWAYS tagged as synthetic=True.
    They fill narrative gaps but are never treated as primary evidence.
    """
    synthetic_templates = {
        "beauty_editorial": {
            "title": f"Synthetic: Beauty Editorial Trend Signal on Barrier Repair",
            "source_name": "Synthetic (Beauty Editorial)",
            "key_claims": [
                "Beauty editors increasingly recommend ceramide-based barrier repair over aggressive exfoliation",
                "The shift from 10-step routines to barrier-first minimalism continues in 2026",
            ],
            "trend_tags": ["barrier_repair", "ceramide", "synthetic"],
        },
        "dermatologist_content": {
            "title": f"Synthetic: Dermatologist Consensus on Ceramide Barrier Repair",
            "source_name": "Synthetic (Dermatologist Consensus)",
            "key_claims": [
                "Board-certified dermatologists recommend ceramide-rich moisturizers as first-line barrier repair",
                "Ceramides, panthenol, and niacinamide form the gold standard for barrier restoration",
            ],
            "trend_tags": ["dermatologist_endorsed", "ceramide", "synthetic"],
        },
        "social_signal": {
            "title": f"Synthetic: Social Media Barrier Repair Trend",
            "source_name": "Synthetic (Social Listening)",
            "key_claims": [
                "Consumer conversations shifting from aggressive actives to gentle barrier support",
                "UGC creators promoting simplified routines centered on barrier health",
            ],
            "trend_tags": ["social_trend", "barrier_repair", "synthetic"],
        },
        "competitor_tracking": {
            "title": f"Synthetic: Competitive Landscape for Barrier Products",
            "source_name": "Synthetic (Competitor Analysis)",
            "key_claims": [
                "Major competitors expanding ceramide product lines signals growing market demand",
                "Positioning gap exists for brands combining K-beauty heritage with clinical barrier repair",
            ],
            "trend_tags": ["competitor_signal", "ceramide", "synthetic"],
        },
        "retail_data": {
            "title": f"Synthetic: Retail Search Trends for Barrier Repair",
            "source_name": "Synthetic (Retail Intelligence)",
            "key_claims": [
                "Search volume for barrier repair products showing sustained year-over-year growth",
                "Ceramide moisturizer category outpacing general skincare growth",
            ],
            "trend_tags": ["market_growth", "ceramide", "synthetic"],
        },
        "kbeauty_intelligence": {
            "title": f"Synthetic: K-Beauty Barrier Repair Signals",
            "source_name": "Synthetic (K-Beauty Intelligence)",
            "key_claims": [
                "Korean beauty market trending toward ceramide-centric barrier formulations",
                "Olive Young bestseller trends indicate barrier repair as dominant category",
            ],
            "trend_tags": ["kbeauty", "barrier_repair", "synthetic"],
        },
    }

    template = synthetic_templates.get(missing_category, {
        "title": f"Synthetic: General Barrier Repair Trend Data",
        "source_name": "Synthetic (General)",
        "key_claims": ["Barrier repair continues as a dominant skincare trend in 2026"],
        "trend_tags": ["barrier_repair", "synthetic"],
    })

    return {
        "id": f"syn_{record_index:03d}",
        "title": template["title"],
        "source_url": "synthetic://generated",
        "source_name": template["source_name"],
        "category": missing_category,
        "publish_date": "2026-03-15",
        "relevance_score": 0.70,  # Lower than real records — intentionally
        "key_claims": template["key_claims"],
        "competitor_mentions": [],
        "trend_tags": template["trend_tags"],
        "product_link_rationale": "Synthetic supplement to fill category gap in sourced data",
        "synthetic": True,  # ALWAYS tagged
    }


def evidence_check(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node function.
    
    Evaluates whether the filtered source records provide
    sufficient evidence for responsible content generation.
    
    Args:
        state: Current pipeline state with filtered_records
    
    Returns:
        Partial state update with evidence decision + any synthetic records
    """
    thresholds = _load_evidence_thresholds()
    sufficient_config = thresholds.get("sufficient", {})
    weak_config = thresholds.get("weak", {})

    min_records_sufficient = sufficient_config.get("min_records", 6)
    min_categories_sufficient = sufficient_config.get("min_categories", 3)
    min_records_weak = weak_config.get("min_records", 3)
    min_categories_weak = weak_config.get("min_categories", 2)

    # Get filtered records
    filtered_records = state.get("filtered_records", [])
    record_count = len(filtered_records)

    # Get categories covered
    categories = set()
    for record in filtered_records:
        if isinstance(record, dict):
            categories.add(record.get("category", ""))
        else:
            categories.add(record.category)
    category_count = len(categories)

    # ─── MAKE DECISION ───
    synthetic_records = []

    if record_count >= min_records_sufficient and category_count >= min_categories_sufficient:
        decision = EvidenceDecision.SUFFICIENT
        decision_detail = (
            f"Sufficient evidence: {record_count} records across "
            f"{category_count} categories (thresholds: ≥{min_records_sufficient} records, "
            f"≥{min_categories_sufficient} categories)"
        )

    elif record_count >= min_records_weak:
        decision = EvidenceDecision.WEAK
        
        # Identify missing categories and generate synthetic supplements
        all_categories = {
            "beauty_editorial", "dermatologist_content", "social_signal",
            "competitor_tracking", "retail_data", "kbeauty_intelligence",
        }
        missing = all_categories - categories
        
        for i, missing_cat in enumerate(missing):
            synthetic = _generate_synthetic_record(missing_cat, i + 1)
            synthetic_records.append(synthetic)
        
        decision_detail = (
            f"Weak evidence: {record_count} records across {category_count} categories. "
            f"Missing categories: {missing}. "
            f"Generated {len(synthetic_records)} synthetic supplements (tagged)."
        )

    else:
        decision = EvidenceDecision.POOR
        decision_detail = (
            f"Poor evidence: only {record_count} records across {category_count} categories. "
            f"Minimum required: {min_records_weak} records. "
            "Pipeline will stop — insufficient data for responsible generation."
        )

    # ─── AUDIT ───
    audit = create_audit_entry(
        node="evidence_check",
        action="sufficiency_evaluation",
        input_snapshot={
            "record_count": record_count,
            "category_count": category_count,
            "categories": list(categories),
        },
        output_snapshot={
            "decision": decision.value,
            "detail": decision_detail,
            "synthetic_added": len(synthetic_records),
        },
        metadata={
            "thresholds": {
                "sufficient": {"records": min_records_sufficient, "categories": min_categories_sufficient},
                "weak": {"records": min_records_weak, "categories": min_categories_weak},
            },
        },
    )

    # If weak, add synthetic records to filtered_records
    updated_filtered = list(filtered_records)
    if decision == EvidenceDecision.WEAK:
        updated_filtered.extend(synthetic_records)

    return {
        "evidence_decision": decision.value,
        "synthetic_records": synthetic_records,
        "filtered_records": updated_filtered,
        "audit_log": state.get("audit_log", []) + [audit.model_dump()],
        "status": f"evidence_{decision.value}",
    }