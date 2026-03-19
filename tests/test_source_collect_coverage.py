"""Tests for trigger/product-aware source coverage from YAML packs."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.pipeline.nodes.source_collect import source_collect


def test_cicapair_has_product_pack_records():
    state = {
        "trigger": "manual",
        "product": "cicapair_treatment",
        "audit_log": [],
    }

    out = source_collect(state)
    filtered = out.get("filtered_records", [])

    assert len(filtered) >= 3
    assert any(r.get("id", "").startswith("cfg_cica_") for r in filtered)


def test_competitor_trigger_prioritizes_categories_and_has_competitor_record():
    state = {
        "trigger": "event_competitor_launch",
        "product": "ceramidin_cream",
        "audit_log": [],
    }

    out = source_collect(state)
    filtered = out.get("filtered_records", [])

    allowed = {"competitor_tracking", "retail_data", "beauty_editorial"}
    categories = {r.get("category") for r in filtered}

    assert categories.issubset(allowed)
    assert "competitor_tracking" in categories
