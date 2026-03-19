"""Unit tests for provider-family resolution."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.llm.providers import resolve_provider_family


def test_provider_family_resolution():
    assert resolve_provider_family("claude-sonnet-4-20250514") == "anthropic"
    assert resolve_provider_family("gpt-4o-mini") == "openai"
    assert resolve_provider_family("gemini-1.5-flash") == "gemini"
    assert resolve_provider_family("unknown-model") == "unknown"
