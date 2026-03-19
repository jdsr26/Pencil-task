"""End-to-end pipeline smoke tests with mocked LLM provider."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.pipeline.graph import run_pipeline


class FakeProvider:
    def complete(self, model, system_prompt, user_prompt, max_tokens, temperature):
        lower = user_prompt.lower()

        if "rigorous brand qa critic" in system_prompt.lower():
            return _Resp(
                '{"brand_alignment": 92, "trend_alignment": 90, "feedback": ['
                '"Strong product-brand linkage", "Clear trend relevance", "Good structure"]}'
            )

        if "trend analyst" in system_prompt.lower():
            return _Resp(
                "NARRATIVE 1: Consumers prioritize barrier-first routines over complicated layering.\n"
                "NARRATIVE 2: Dermatology voices emphasize resilient barrier care with clinically grounded ingredients.\n"
                "NARRATIVE 3: Search and social momentum indicate strong market demand for this category."
            )

        product = "Ceramidin"
        if "cicapair" in lower or "tiger grass" in lower:
            product = "Cicapair"
        elif "dermask" in lower or "micro jet" in lower:
            product = "Dermask"

        if "responsive search ad" in lower or "headline 1" in lower:
            return _Resp(
                f"HEADLINE 1: Dr. Jart {product} Glow\n"
                "HEADLINE 2: Repair Your Barrier\n"
                "HEADLINE 3: Clinical K-Beauty Care\n"
                "DESCRIPTION 1: Dr. Jart formula strengthens skin barrier with science-backed hydration.\n"
                "DESCRIPTION 2: Barrier-first care for resilient skin in 2026 trend conversations.\n"
                "DESCRIPTION 3: Shop now for daily repair and comfort with dermatologist-tested care."
            )

        if "video generation prompt" in lower or "scene 1" in lower:
            return _Resp(
                f"TITLE: Dr. Jart {product} Barrier Story\n"
                "DURATION: 15 seconds\n"
                "ASPECT RATIO: 9:16\n\n"
                "SCENE 1 (0-5s): Close-up of dry skin texture transitioning to smooth barrier glow.\n"
                f"SCENE 2 (5-10s): {product} product hero with creamy texture and barrier-layer visual motif.\n"
                "SCENE 3 (10-15s): Dr. Jart product shot with clear shop-now end card.\n\n"
                "TEXT OVERLAYS:\n"
                "- Scene 1: Barrier First\n"
                "- Scene 2: Science + Comfort\n"
                "- Scene 3: Shop Now\n\n"
                "MOOD: Confident, modern, restorative\n"
                "COLOR PALETTE: Warm neutrals with clean clinical highlights\n"
                "MUSIC DIRECTION: Light percussive electronic pulse with hopeful rise"
            )

        if "image generation prompt" in lower:
            return _Resp(
                f"Dr. Jart {product} editorial product photography, clean studio composition, "
                "barrier-layer visual metaphor with translucent stacked films, soft diffused light, "
                "warm neutral palette, premium Korean minimalist mood --ar 4:5 --style raw --v 6"
            )

        if "seo-optimized blog post" in lower:
            body = " ".join([
                "Dr. Jart barrier care supports resilient skin with trend-aware routine design."
                for _ in range(120)
            ])
            return _Resp(
                "META DESCRIPTION: Dr. Jart barrier-first skincare guide for 2026 with trend-grounded routine advice.\n\n"
                "# Dr. Jart Barrier-First 2026 Guide\n\n"
                "## Why Barrier Care Matters\n\n"
                + body
                + "\n\n## Product Spotlight\n\n"
                + body
                + "\n\n## How To Use It\n\n"
                + body
                + "\n\n## Conclusion\n\nShop now and build your daily Dr. Jart routine."
            )

        return _Resp("Default response")


class _Resp:
    def __init__(self, text):
        self.text = text
        self.stop_reason = "end_turn"
        self.input_tokens = 100
        self.output_tokens = 200


def _inject_fake_provider(monkeypatch):
    monkeypatch.setattr("backend.agents.base_agent.get_provider", lambda _model: FakeProvider())


def test_pipeline_smoke_cicapair_spring(monkeypatch):
    _inject_fake_provider(monkeypatch)

    result = run_pipeline(
        trigger="seasonal_spring",
        product="cicapair_treatment",
        generation_model="claude-sonnet-4-20250514",
        judge_model="claude-sonnet-4-20250514",
        image_generator="gpt-image-1",
        video_generator="veo-3",
    )

    assert len(result.get("filtered_records", [])) > 0
    assert result.get("evidence_decision") != "poor"
    meta = result.get("campaign_metadata", {})
    assert meta.get("anchor_product") == "cicapair_treatment"
    assert meta.get("video_generator") == "veo-3"
    assert meta.get("image_generator") == "gpt-image-1"


def test_pipeline_smoke_dermask_competitor(monkeypatch):
    _inject_fake_provider(monkeypatch)

    result = run_pipeline(
        trigger="event_competitor_launch",
        product="dermask_micro_jet",
        generation_model="claude-sonnet-4-20250514",
        judge_model="claude-sonnet-4-20250514",
        image_generator="midjourney-v6",
        video_generator="runway-gen4",
    )

    assert len(result.get("filtered_records", [])) > 0
    assert result.get("evidence_decision") != "poor"
    meta = result.get("campaign_metadata", {})
    assert meta.get("anchor_product") == "dermask_micro_jet"
    assert meta.get("trigger") == "event_competitor_launch"
