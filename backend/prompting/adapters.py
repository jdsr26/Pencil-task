"""Model-specific prompt renderers built on a canonical PromptSpec."""

from __future__ import annotations

from typing import Any, Dict, List

from backend.prompting.spec import PromptSpec


class PromptAdapter:
    """Interface for converting PromptSpec into model-ready user prompts."""

    def render(self, spec: PromptSpec) -> str:
        raise NotImplementedError()

    @staticmethod
    def _render_context(context: Dict[str, Any]) -> str:
        context_parts: List[str] = []
        for key, value in context.items():
            if isinstance(value, list):
                items = "\n".join(f"  - {item}" for item in value)
                context_parts.append(f"{key.upper()}:\n{items}")
            elif isinstance(value, dict):
                items = "\n".join(f"  {k}: {v}" for k, v in value.items())
                context_parts.append(f"{key.upper()}:\n{items}")
            else:
                context_parts.append(f"{key.upper()}: {value}")
        return "\n\n".join(context_parts)

    @staticmethod
    def _render_feedback(feedback: List[str]) -> str:
        corrections = "\n".join(f"  - {fb}" for fb in feedback)
        return (
            "The previous version of this asset FAILED quality scoring.\n"
            "You MUST fix these specific issues:\n"
            f"{corrections}\n\n"
            "Do NOT repeat these mistakes. Address each correction explicitly."
        )


class ClaudePromptAdapter(PromptAdapter):
    """Section-based format tuned for Claude-style instruction following."""

    def render(self, spec: PromptSpec) -> str:
        sections: List[str] = []

        if spec.context:
            sections.append("=== CONTEXT ===\n" + self._render_context(spec.context))

        sections.append("=== TASK ===\n" + spec.task)

        if spec.feedback:
            sections.append(
                "=== CRITICAL CORRECTIONS FROM PREVIOUS ATTEMPT ===\n"
                + self._render_feedback(spec.feedback)
            )

        return "\n\n".join(sections)


class GPTPromptAdapter(PromptAdapter):
    """XML-tag style format often robust for GPT-family chat models."""

    def render(self, spec: PromptSpec) -> str:
        blocks: List[str] = []
        if spec.context:
            blocks.append("<context>\n" + self._render_context(spec.context) + "\n</context>")
        blocks.append("<task>\n" + spec.task + "\n</task>")
        if spec.feedback:
            blocks.append(
                "<corrections>\n" + self._render_feedback(spec.feedback) + "\n</corrections>"
            )
        return "\n\n".join(blocks)


class GeminiPromptAdapter(PromptAdapter):
    """Markdown-structured format for Gemini-family models."""

    def render(self, spec: PromptSpec) -> str:
        parts: List[str] = []
        if spec.context:
            parts.append("## Context\n" + self._render_context(spec.context))
        parts.append("## Task\n" + spec.task)
        if spec.feedback:
            parts.append("## Corrections\n" + self._render_feedback(spec.feedback))
        return "\n\n".join(parts)


def get_prompt_adapter(model_id: str) -> PromptAdapter:
    """Select prompt renderer by model family while keeping a stable spec."""

    model = (model_id or "").lower()
    if model.startswith("claude"):
        return ClaudePromptAdapter()
    if model.startswith("gpt") or model.startswith("o1") or model.startswith("o3"):
        return GPTPromptAdapter()
    if model.startswith("gemini"):
        return GeminiPromptAdapter()

    # Safe default: preserve existing claude section format.
    return ClaudePromptAdapter()
