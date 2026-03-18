"""Unit tests for claim linker."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.pipeline.tools.claim_linker import extract_factual_claims, find_best_source_match


def test_extract_factual_claims():
    text = "Searches increased 29% year-over-year. Your skin will thank you. The #1 trend of 2026."
    claims = extract_factual_claims(text)
    assert len(claims) >= 2  # "29%" and "#1" should be caught
    assert any("29%" in c for c in claims)


def test_extract_skips_creative():
    text = "Your skin will thank you. A smart investment in your barrier."
    claims = extract_factual_claims(text)
    assert len(claims) == 0  # No factual indicators


def test_source_matching():
    source_claims = [
        {"claim": "Google searches increased 29% year-over-year", "source_id": "src_007", "source_name": "Google Trends"},
    ]
    result = find_best_source_match("Barrier repair searches surged 29% YoY", source_claims, threshold=0.3)
    assert result["matched"] is True
    assert result["source_id"] == "src_007"


if __name__ == "__main__":
    test_extract_factual_claims()
    test_extract_skips_creative()
    test_source_matching()
    print("✅ All claim linker tests passed!")
