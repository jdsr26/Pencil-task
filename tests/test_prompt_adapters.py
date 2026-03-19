"""Unit tests for canonical prompt spec adapter rendering."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.prompting.adapters import (
    get_prompt_adapter,
    ClaudePromptAdapter,
    GPTPromptAdapter,
    GeminiPromptAdapter,
)
from backend.prompting.spec import PromptSpec


def test_adapter_selection_by_model_family():
    assert isinstance(get_prompt_adapter("claude-sonnet-4-20250514"), ClaudePromptAdapter)
    assert isinstance(get_prompt_adapter("gpt-4o"), GPTPromptAdapter)
    assert isinstance(get_prompt_adapter("gemini-1.5-pro"), GeminiPromptAdapter)


def test_claude_adapter_renders_sections():
    spec = PromptSpec(
        task="Generate ad headlines",
        context={"product": "Ceramidin"},
        feedback=["Avoid fear-based language"],
    )
    rendered = ClaudePromptAdapter().render(spec)
    assert "=== CONTEXT ===" in rendered
    assert "=== TASK ===" in rendered
    assert "=== CRITICAL CORRECTIONS FROM PREVIOUS ATTEMPT ===" in rendered


def test_gpt_adapter_renders_tags():
    spec = PromptSpec(task="Do thing", context={"a": "b"})
    rendered = GPTPromptAdapter().render(spec)
    assert "<context>" in rendered
    assert "<task>" in rendered


def test_gemini_adapter_renders_markdown_blocks():
    spec = PromptSpec(task="Do thing", context={"a": "b"})
    rendered = GeminiPromptAdapter().render(spec)
    assert "## Context" in rendered
    assert "## Task" in rendered
