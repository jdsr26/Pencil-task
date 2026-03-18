"""Unit tests for Pydantic state validation."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pydantic import ValidationError
from backend.pipeline.state import SourceRecord, AssetOutput, LLMJudgeResult, AssetType


def test_source_record_valid():
    record = SourceRecord(
        id="test_001", title="Test", source_url="http://test.com",
        source_name="Test", category="beauty_editorial", publish_date="2026-01-01",
        relevance_score=0.85, key_claims=["test claim"], trend_tags=["test"],
        product_link_rationale="test rationale"
    )
    assert record.relevance_score == 0.85


def test_source_record_invalid_score():
    try:
        SourceRecord(
            id="test", title="Test", source_url="http://test.com",
            source_name="Test", category="test", publish_date="2026-01-01",
            relevance_score=1.5,  # Invalid — must be <= 1.0
            key_claims=[], trend_tags=[], product_link_rationale="test"
        )
        assert False, "Should have raised ValidationError"
    except ValidationError:
        pass


def test_asset_output_defaults():
    asset = AssetOutput()
    assert asset.content == ""
    assert asset.version == 1
    assert asset.feedback_history == []


def test_llm_judge_bounds():
    try:
        LLMJudgeResult(asset_type=AssetType.ADS, brand_alignment=150)
        assert False, "Should have raised ValidationError"
    except ValidationError:
        pass


if __name__ == "__main__":
    test_source_record_valid()
    test_source_record_invalid_score()
    test_asset_output_defaults()
    test_llm_judge_bounds()
    print("✅ All state validation tests passed!")
