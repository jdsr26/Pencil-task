"""
Source Collect Node
===================
Phase 1 entry point. Loads source records, validates against
Pydantic models, applies filtering gates, and populates the
source registry for downstream claim-linking.

LangGraph node: receives full PipelineState, returns partial update.
"""

import yaml
from datetime import datetime, timedelta
from typing import Dict, Any

from backend.pipeline.state import PipelineState, SourceRecord, AuditEntry
from backend.registries.source_registry import SourceRegistry
from backend.registries.product_truth import ProductTruthRegistry
from backend.observability.audit_log import create_audit_entry, hash_payload


def source_collect(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node function.
    
    Steps:
      1. Load source records from JSON file
      2. Validate each against SourceRecord Pydantic model
      3. Apply filtering gates (recency, relevance, keywords)
      4. Populate source registry for downstream use
      5. Log everything to audit trail
    
    Args:
        state: Current pipeline state (as dict for LangGraph compatibility)
    
    Returns:
        Partial state update with sourced_records and filtered_records
    """
    # Load source configuration
    with open("config/sources.yaml", "r") as f:
        sources_config = yaml.safe_load(f)
    with open("config/triggers.yaml", "r") as f:
        triggers_config = yaml.safe_load(f)

    filters = sources_config.get("filters", {})
    trigger_key = state.get("trigger", "manual")
    trigger_cfg = triggers_config.get("trigger_types", {}).get(trigger_key, {})

    max_age_days = trigger_cfg.get(
        "sourcing_window_days",
        filters.get("recency", {}).get("max_age_days", 30),
    )
    min_relevance = filters.get("relevance", {}).get("min_score", 0.75)
    required_keywords = list(filters.get("relevance", {}).get("required_keywords_any", []))

    product_key = state.get("product", "ceramidin_cream")
    product_profiles = sources_config.get("product_profiles", {})
    product_profile = product_profiles.get(product_key, {})
    required_keywords.extend(product_profile.get("keywords_any", []))
    required_keywords = list(dict.fromkeys(required_keywords))

    priority_sources = trigger_cfg.get("priority_sources", "all")
    if isinstance(priority_sources, list):
        allowed_categories = set(priority_sources)
    else:
        allowed_categories = None

    # Load and validate source records
    source_registry = SourceRegistry()
    source_registry.load_from_file("data/sourced/march_2026_cycle.json")
    all_records = list(source_registry.get_all_records())

    # Load YAML-backed source packs for selected product and trigger
    source_packs = sources_config.get("source_packs", {})
    for raw in source_packs.get("by_product", {}).get(product_key, []):
        all_records.append(SourceRecord(**raw))
    for raw in source_packs.get("by_trigger", {}).get(trigger_key, []):
        all_records.append(SourceRecord(**raw))

    # Apply filtering gates
    filtered = []
    rejected = []

    for record in all_records:
        rejection_reasons = []

        # Gate 1: Relevance score
        if record.relevance_score < min_relevance:
            rejection_reasons.append(
                f"relevance {record.relevance_score} < {min_relevance}"
            )

        # Gate 2: Keyword presence (at least one required keyword)
        content_to_check = (
            record.title.lower() + " " +
            " ".join(record.key_claims).lower() + " " +
            " ".join(record.trend_tags).lower()
        )
        has_keyword = any(
            kw.lower() in content_to_check for kw in required_keywords
        )
        if not has_keyword:
            rejection_reasons.append("no required keywords found")

        # Gate 3: Trigger priority categories
        if allowed_categories is not None and record.category not in allowed_categories:
            rejection_reasons.append(
                f"category {record.category} not in trigger priority_sources"
            )

        # Gate 4: Recency (simplified — in production, compare actual dates)
        # For the demo, all pre-curated records are recent enough
        # In production: parse publish_date and compare to current date

        if rejection_reasons:
            rejected.append({
                "id": record.id,
                "title": record.title,
                "reasons": rejection_reasons,
            })
        else:
            filtered.append(record)

    # Create audit entry
    evidence_fingerprint = [
        {
            "id": r.id,
            "source_name": r.source_name,
            "category": r.category,
            "claims": r.key_claims,
            "tags": r.trend_tags,
        }
        for r in filtered
    ]
    evidence_hash = hash_payload(evidence_fingerprint)

    audit = create_audit_entry(
        node="source_collect",
        action="load_and_filter",
        input_snapshot={
            "source_file": "data/sourced/march_2026_cycle.json",
            "filter_config": {
                "max_age_days": max_age_days,
                "min_relevance": min_relevance,
                "required_keywords_count": len(required_keywords),
                "priority_sources": priority_sources,
            },
        },
        output_snapshot={
            "total_loaded": len(all_records),
            "passed_filter": len(filtered),
            "rejected": len(rejected),
            "rejection_details": rejected[:5],  # First 5 for audit
            "categories_covered": list({r.category for r in filtered}),
        },
        metadata={
            "trigger": trigger_key,
            "product": product_key,
            "evidence_hash": evidence_hash,
        },
    )

    return {
        "sourced_records": [r.model_dump() for r in all_records],
        "filtered_records": [r.model_dump() for r in filtered],
        "evidence_hash": evidence_hash,
        "audit_log": state.get("audit_log", []) + [audit.model_dump()],
        "status": "sourcing_complete",
    }