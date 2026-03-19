"""Provider abstraction for Anthropic, OpenAI, and Gemini style models."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx
from anthropic import Anthropic


@dataclass
class ProviderResponse:
    text: str
    stop_reason: Optional[str]
    input_tokens: int
    output_tokens: int
    resolved_model: Optional[str] = None
    provider_family: Optional[str] = None
    raw: Any = None


class BaseProvider:
    def complete(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> ProviderResponse:
        raise NotImplementedError()


class AnthropicProvider(BaseProvider):
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment.")
        self.client = Anthropic(api_key=api_key)

    def complete(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> ProviderResponse:
        response = self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        response_text = ""
        for block in response.content:
            if block.type == "text":
                response_text += block.text

        return ProviderResponse(
            text=response_text,
            stop_reason=response.stop_reason,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            resolved_model=getattr(response, "model", model),
            provider_family="anthropic",
            raw=response,
        )


class OpenAIProvider(BaseProvider):
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment.")

    def complete(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> ProviderResponse:
        with httpx.Client(timeout=60) as client:
            response = client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            response.raise_for_status()
            data = response.json()

        choice = data["choices"][0]
        content = choice["message"]["content"]
        if isinstance(content, list):
            content = "".join(part.get("text", "") for part in content if isinstance(part, dict))

        usage = data.get("usage", {})
        return ProviderResponse(
            text=content or "",
            stop_reason=choice.get("finish_reason"),
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            resolved_model=data.get("model", model),
            provider_family="openai",
            raw=data,
        )


class GeminiProvider(BaseProvider):
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment.")

    def complete(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> ProviderResponse:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        with httpx.Client(timeout=60) as client:
            response = client.post(url, params={"key": self.api_key}, json=payload)
            response.raise_for_status()
            data = response.json()

        candidates = data.get("candidates", [])
        if not candidates:
            raise ValueError("Gemini response did not contain candidates.")

        first = candidates[0]
        parts = first.get("content", {}).get("parts", [])
        text = "".join(part.get("text", "") for part in parts if isinstance(part, dict))

        usage = data.get("usageMetadata", {})
        return ProviderResponse(
            text=text,
            stop_reason=first.get("finishReason"),
            input_tokens=usage.get("promptTokenCount", 0),
            output_tokens=usage.get("candidatesTokenCount", 0),
            resolved_model=data.get("modelVersion", model),
            provider_family="gemini",
            raw=data,
        )


def resolve_provider_family(model_id: str) -> str:
    model = (model_id or "").lower()
    if model.startswith("claude"):
        return "anthropic"
    if model.startswith("gpt") or model.startswith("o1") or model.startswith("o3"):
        return "openai"
    if model.startswith("gemini"):
        return "gemini"

    return "unknown"


def get_provider(model_id: str) -> BaseProvider:
    family = resolve_provider_family(model_id)
    if family == "anthropic":
        return AnthropicProvider()
    if family == "openai":
        return OpenAIProvider()
    if family == "gemini":
        return GeminiProvider()

    raise ValueError(f"Unsupported model provider for model '{model_id}'.")
