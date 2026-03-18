"""
Narrative Synthesis Node
========================
Distills the sourced data into 3 trend narratives.
These narratives are the creative bridge between raw data
and asset generation.

Each narrative is:
  - A one-sentence summary of a key trend
  - Grounded in specific source records
  - Connected to Ceramidin™ specifically

The generation agents receive these narratives as context,
ensuring all 4 assets tell a consistent, data-backed story.
"""

import yaml
from typing import Dict, Any, List

from backend.agents.base_agent import BaseAgent
from backend.registries.product_truth import ProductTruthRegistry
from backend.observability.audit_log import create_audit_entry


SYNTHESIS_PROMPT = """You are a trend analyst for Dr. Jart+ skincare brand.

Your task: Analyze the sourced trend data below and distill exactly 3 trend narratives 
that connect to Ceramidin™ Skin Barrier Moisturizing Cream.

Each narrative should be:
1. One clear sentence summarizing a key trend
2. Grounded in the specific source data provided
3. Connected to Ceramidin™'s positioning (5-ceramide barrier repair cream)

The 3 narratives should cover DIFFERENT angles:
- Narrative 1: The consumer/cultural shift (what people are doing differently)
- Narrative 2: The scientific/expert validation (what dermatologists are saying)
- Narrative 3: The market/competitive opportunity (where the growth is)

OUTPUT FORMAT (exactly 3 lines, one narrative per line):
NARRATIVE 1: [your narrative sentence]
NARRATIVE 2: [your narrative sentence]
NARRATIVE 3: [your narrative sentence]

Write ONLY the 3 narrative lines. No explanations or commentary."""


def narrative_synth(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node function.
    
    Takes all filtered source records and distills them into
    3 trend narratives using an LLM call.
    
    Falls back to extracting top claims if LLM call fails.
    
    Args:
        state: Current pipeline state with filtered_records
    
    Returns:
        Partial state update with trend_narratives
    """
    # Check evidence decision — if POOR, don't synthesize
    evidence_decision = state.get("evidence_decision", "sufficient")
    if evidence_decision == "poor":
        audit = create_audit_entry(
            node="narrative_synth",
            action="skipped_poor_evidence",
            input_snapshot={"evidence_decision": evidence_decision},
            output_snapshot={"narratives": []},
        )
        return {
            "trend_narratives": [],
            "audit_log": state.get("audit_log", []) + [audit.model_dump()],
            "status": "narrative_synth_skipped",
        }

    # Build context from filtered records
    filtered_records = state.get("filtered_records", [])
    
    source_context = []
    for record in filtered_records:
        if isinstance(record, dict):
            title = record.get("title", "")
            source = record.get("source_name", "")
            claims = record.get("key_claims", [])
            tags = record.get("trend_tags", [])
            rationale = record.get("product_link_rationale", "")
            is_synthetic = record.get("synthetic", False)
        else:
            title = record.title
            source = record.source_name
            claims = record.key_claims
            tags = record.trend_tags
            rationale = record.product_link_rationale
            is_synthetic = record.synthetic

        tag_str = "SYNTHETIC" if is_synthetic else "REAL"
        claims_str = "; ".join(claims[:3])
        source_context.append(
            f"[{tag_str}] {title} (source: {source})\n"
            f"  Claims: {claims_str}\n"
            f"  Tags: {', '.join(tags)}\n"
            f"  Product link: {rationale}"
        )

    # Load product context
    product_truth = ProductTruthRegistry()

    # Call LLM for synthesis
    try:
        agent = BaseAgent(
            name="narrative_synth",
            system_prompt=SYNTHESIS_PROMPT,
            temperature=0.5,   # Moderate — analytical, not creative
            max_tokens=500,
        )

        response_text, llm_audit = agent.call(
            task="Analyze the following sourced data and produce 3 trend narratives:",
            context={
                "sourced_data": "\n\n".join(source_context),
                "anchor_product": product_truth.get_product_context(),
            },
        )

        # Parse narratives
        narratives = _parse_narratives(response_text)

        audit = create_audit_entry(
            node="narrative_synth",
            action="narratives_generated",
            input_snapshot={
                "source_count": len(filtered_records),
                "synthetic_count": sum(
                    1 for r in filtered_records
                    if (isinstance(r, dict) and r.get("synthetic")) or
                       (not isinstance(r, dict) and r.synthetic)
                ),
            },
            output_snapshot={
                "narrative_count": len(narratives),
                "narratives": narratives,
            },
        )

        return {
            "trend_narratives": narratives,
            "audit_log": state.get("audit_log", []) + [llm_audit.model_dump(), audit.model_dump()],
            "status": "narrative_synth_complete",
        }

    except Exception as e:
        # Fallback: extract top claims directly from records
        narratives = _fallback_narratives(filtered_records)

        audit = create_audit_entry(
            node="narrative_synth",
            action="narratives_fallback",
            input_snapshot={"error": str(e)[:200]},
            output_snapshot={
                "narrative_count": len(narratives),
                "narratives": narratives,
                "method": "fallback_claim_extraction",
            },
        )

        return {
            "trend_narratives": narratives,
            "audit_log": state.get("audit_log", []) + [audit.model_dump()],
            "status": "narrative_synth_fallback",
        }


def _parse_narratives(response_text: str) -> List[str]:
    """
    Extract narratives from LLM response.
    Expects format: "NARRATIVE 1: [text]"
    Falls back to splitting by newlines if format doesn't match.
    """
    import re

    narratives = []
    for line in response_text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue

        # Try structured format first
        match = re.match(
            r"^(?:NARRATIVE|Narrative)\s*\d*\s*[:\.]\s*(.+)$", line
        )
        if match:
            narratives.append(match.group(1).strip())
        elif len(line) > 30 and not line.startswith("#"):
            # Fallback: treat any substantial line as a narrative
            narratives.append(line)

    return narratives[:3]  # Cap at 3


def _fallback_narratives(filtered_records: list) -> List[str]:
    """
    If LLM synthesis fails, extract the top 3 most relevant
    claims directly from source records.
    
    This ensures the pipeline can always produce narratives,
    even if the LLM is unavailable. The quality will be lower
    (raw claims vs synthesized narratives) but the pipeline won't stop.
    """
    claims_with_scores = []

    for record in filtered_records:
        if isinstance(record, dict):
            score = record.get("relevance_score", 0)
            claims = record.get("key_claims", [])
            synthetic = record.get("synthetic", False)
        else:
            score = record.relevance_score
            claims = record.key_claims
            synthetic = record.synthetic

        # Deprioritize synthetic records
        adjusted_score = score * 0.7 if synthetic else score

        for claim in claims[:2]:  # Top 2 claims per record
            claims_with_scores.append((claim, adjusted_score))

    # Sort by score descending, take top 3
    claims_with_scores.sort(key=lambda x: x[1], reverse=True)
    return [claim for claim, _ in claims_with_scores[:3]]