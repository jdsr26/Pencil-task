"""Unit tests for user-selected model wiring and validation."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from pydantic import ValidationError

from backend.api.models import RunRequest, ALLOWED_MODELS
from backend.pipeline.graph import create_initial_state


def test_run_request_defaults_to_sonnet():
    req = RunRequest()
    assert req.generation_model == "claude-sonnet-4-20250514"
    assert req.judge_model is None
    assert req.image_generator == "midjourney-v6"
    assert req.video_generator == "runway-gen4"


def test_run_request_rejects_unsupported_generation_model():
    with pytest.raises(ValidationError):
        RunRequest(generation_model="gpt-5")


def test_run_request_rejects_unsupported_judge_model():
    with pytest.raises(ValidationError):
        RunRequest(judge_model="not-a-real-model")


def test_run_request_accepts_allowlisted_models():
    req = RunRequest(
        generation_model=ALLOWED_MODELS[0],
        judge_model=ALLOWED_MODELS[2],
    )
    assert req.generation_model == ALLOWED_MODELS[0]
    assert req.judge_model == ALLOWED_MODELS[2]


def test_initial_state_includes_selected_models():
    state = create_initial_state(
        trigger="seasonal_spring",
        product="ceramidin_cream",
        generation_model="claude-opus-4-20250514",
        judge_model="claude-haiku-3-5-20241022",
        image_generator="gpt-image-1",
        video_generator="veo-3",
    )
    assert state["generation_model"] == "claude-opus-4-20250514"
    assert state["judge_model"] == "claude-haiku-3-5-20241022"
    assert state["image_generator"] == "gpt-image-1"
    assert state["video_generator"] == "veo-3"


def test_run_request_rejects_unsupported_generators():
    with pytest.raises(ValidationError):
        RunRequest(image_generator="stable-diffusion-xl")

    with pytest.raises(ValidationError):
        RunRequest(video_generator="pika")
