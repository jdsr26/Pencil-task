"""
Claim Linker Tool
=================
Traces factual claims in generated content back to their sources.
This is the GROUNDING VERIFICATION layer.

Two ground truth stores:
  1. Source Registry — external trend data (Phase 1 records)
  2. Product Truth — approved product claims (product_truth.yaml)

If a claim can't be linked to either store, it's flagged as
potentially hallucinated. This doesn't mean it's wrong — it means
it's UNGROUNDED, and a human or the LLM judge should verify it.

This tool is most important for the BLOG asset, which is the
longest and most likely to contain factual claims (statistics,
trend references, ingredient facts, competitor mentions).

Design principle:
  "Every factual or trend-derived claim must be traceable.
   Creative expression must be brand-consistent, but does not
   need 1:1 source attribution."
"""

import re
from typing import List, Dict, Tuple
from difflib import SequenceMatcher

from backend.pipeline.state import SourceRecord, DeterministicCheckDetail


def extract_factual_claims(content: str) -> List[str]:
    """
    Extract sentences that contain factual claims from generated content.
    
    A "factual claim" is a sentence that contains:
      - Numbers or percentages (29%, $540M, 700M+, #1)
      - Statistical language (increased, growth, projected, survey)
      - Trend references (2026, trending, year-over-year)
      - Product-specific claims (5 ceramides, clinically tested)
      - Comparative statements (more than, leading, #1, best-selling)
    
    Creative/emotional sentences are NOT extracted:
      - "Your skin will thank you" (emotional, not factual)
      - "A smart investment in your barrier" (creative metaphor)
    
    Returns:
        List of sentences that likely contain factual claims
    """
    # Split content into sentences
    # Handle common abbreviations to avoid false splits
    text = content.replace("Dr.", "Dr").replace("fl.", "fl").replace("oz.", "oz")
    sentences = re.split(r'[.!?]\s+', text)
    
    factual_indicators = [
        # Numbers and statistics
        r'\d+%',               # percentages: 29%, 200%
        r'\$[\d,.]+',          # dollar amounts: $540M, $48
        r'\d+M\+?',           # large numbers: 700M+
        r'#\d+',              # rankings: #1
        r'\d+\s*(?:year|month|week|day)',  # time periods
        
        # Statistical language
        r'(?:increase|decrease|grow|surge|decline|project|rise|drop)',
        r'(?:year-over-year|YoY|CAGR|market size)',
        r'(?:survey|study|research|report|data|statistic)',
        r'(?:according to|found that|shows that)',
        
        # Trend references  
        r'(?:2025|2026|trending|trend)',
        
        # Product claims
        r'(?:\d+[\s-]ceramide|\d+\s*ceramides)',  # "5 ceramides", "5-ceramide"
        r'(?:clinically\s+(?:tested|proven)|dermatologist[\s-](?:tested|backed))',
        r'(?:fragrance[\s-]free|hypoallergenic)',
        
        # Comparative/superlative
        r'(?:#1|number one|best[\s-]sell|leading|most popular|top[\s-]rated)',
    ]
    
    factual_sentences = []
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 15:  # Skip very short fragments
            continue
        
        for pattern in factual_indicators:
            if re.search(pattern, sentence, re.IGNORECASE):
                factual_sentences.append(sentence)
                break  # Don't add the same sentence twice
    
    return factual_sentences


def find_best_source_match(
    claim: str,
    source_claims: List[Dict[str, str]],
    threshold: float = 0.45,
) -> Dict[str, any]:
    """
    Find the best matching source claim for a given output claim.
    
    Uses SequenceMatcher for fuzzy string matching. This isn't
    exact match — it finds the closest source claim even when
    the LLM paraphrased the original data.
    
    Args:
        claim: The claim from generated content
        source_claims: List of dicts with 'claim' and 'source_id' keys
        threshold: Minimum similarity score to count as a match (0-1)
                  0.45 is deliberately lenient — we want to catch
                  paraphrased references, not just exact copies.
    
    Returns:
        Dict with 'matched', 'source_id', 'source_claim', 'similarity'
        If no match found: 'matched' is False
    """
    claim_lower = claim.lower().strip()
    best_match = {
        "matched": False,
        "source_id": None,
        "source_claim": None,
        "similarity": 0.0,
    }

    for source_item in source_claims:
        source_text = source_item["claim"].lower().strip()
        
        # Calculate similarity
        similarity = SequenceMatcher(None, claim_lower, source_text).ratio()
        
        if similarity > best_match["similarity"]:
            best_match = {
                "matched": similarity >= threshold,
                "source_id": source_item["source_id"],
                "source_claim": source_item["claim"],
                "similarity": round(similarity, 3),
            }

    return best_match


def link_claims_to_sources(
    content: str,
    source_records: List[SourceRecord],
    approved_claims: List[str],
) -> Dict[str, any]:
    """
    Full claim-linking pipeline.
    
    1. Extract factual claims from content
    2. For each claim, search source records AND product truth
    3. Classify as: linked (grounded), partially linked, or unlinked (potentially hallucinated)
    
    Args:
        content: The generated asset content
        source_records: Phase 1 source records
        approved_claims: Approved claims from product_truth.yaml
    
    Returns:
        Dict with:
          - 'total_claims': number of factual claims found
          - 'linked': claims matched to a source or product truth
          - 'unlinked': claims with no source match (potential hallucination)
          - 'grounding_score': percentage of claims that are linked
          - 'details': per-claim breakdown for the audit trail
    """
    # Step 1: Extract factual claims
    claims = extract_factual_claims(content)
    
    if not claims:
        return {
            "total_claims": 0,
            "linked": [],
            "unlinked": [],
            "grounding_score": 100.0,  # No claims = nothing to ground = clean
            "details": [],
        }

    # Step 2: Build searchable claim list from sources
    source_claims = []
    for record in source_records:
        for claim in record.key_claims:
            source_claims.append({
                "claim": claim,
                "source_id": record.id,
                "source_name": record.source_name,
            })
    
    # Add product truth as a source
    for approved in approved_claims:
        source_claims.append({
            "claim": approved,
            "source_id": "product_truth",
            "source_name": "Product Truth Registry",
        })

    # Step 3: Link each claim
    linked = []
    unlinked = []
    details = []

    for claim in claims:
        match = find_best_source_match(claim, source_claims)
        
        detail = {
            "claim": claim,
            "matched": match["matched"],
            "source_id": match["source_id"],
            "source_claim": match["source_claim"],
            "similarity": match["similarity"],
        }
        details.append(detail)

        if match["matched"]:
            linked.append(detail)
        else:
            unlinked.append(detail)

    # Step 4: Calculate grounding score
    grounding_score = (len(linked) / len(claims)) * 100 if claims else 100.0

    return {
        "total_claims": len(claims),
        "linked": linked,
        "unlinked": unlinked,
        "grounding_score": round(grounding_score, 1),
        "details": details,
    }


def create_grounding_check(
    content: str,
    source_records: List[SourceRecord],
    approved_claims: List[str],
) -> DeterministicCheckDetail:
    """
    Create a DeterministicCheckDetail for the grounding verification.
    
    This integrates with the deterministic scoring pipeline.
    A grounding score ≥70% passes (some paraphrasing is expected).
    
    Args:
        content: Generated asset content
        source_records: Phase 1 source records
        approved_claims: From product_truth.yaml
    
    Returns:
        DeterministicCheckDetail for the scoring pipeline
    """
    result = link_claims_to_sources(content, source_records, approved_claims)
    
    grounding_score = result["grounding_score"]
    total = result["total_claims"]
    linked_count = len(result["linked"])
    unlinked_count = len(result["unlinked"])
    
    # Pass threshold: 70% of factual claims must be grounded
    passed = grounding_score >= 70.0 or total == 0
    
    if total == 0:
        message = "No factual claims detected — grounding check not applicable"
    elif passed:
        message = f"{linked_count}/{total} claims grounded ({grounding_score}%)"
    else:
        # Include the unlinked claims in the message for feedback
        unlinked_texts = [u["claim"][:80] for u in result["unlinked"][:3]]
        message = (
            f"Only {linked_count}/{total} claims grounded ({grounding_score}%). "
            f"Ungrounded claims: {'; '.join(unlinked_texts)}"
        )

    return DeterministicCheckDetail(
        check_name="claim_grounding",
        passed=passed,
        expected="≥70% of factual claims grounded in source data or product truth",
        actual=f"{grounding_score}% grounded ({linked_count}/{total} claims)",
        message=message,
    )
"""

---

## Why This Tool Matters — The Hallucination Story

Without this tool, your anti-hallucination story is: "I told the LLM not to make things up." That's a prompt instruction. It's hope.

With this tool, your anti-hallucination story is:

> "Every factual claim in the generated content is verified against two ground truth stores — the source registry and the product truth registry. The blog says 'searches up 29% year-over-year' — the claim linker traces that to source record src_007 from Google Trends with 0.82 similarity. If a claim can't be linked to any source, it's flagged as ungrounded. The system doesn't delete it — it flags it for the judge and the feedback loop."

That's a verification system, not a prompt instruction. Dan will see the difference immediately.

## How It Works Step by Step

**Step 1: Extract factual claims**

The blog post might say:
```
"Ceramide barrier repair is the #1 skincare trend of 2026. Google searches 
for 'skin barrier repair' increased 29% year-over-year, reaching approximately 
71,000 monthly searches. Dr. Jart+ Ceramidin™ Cream contains a 5-ceramide 
complex that strengthens and repairs the skin barrier. Your skin will thank you."
"""