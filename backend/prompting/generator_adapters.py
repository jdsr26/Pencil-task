"""Adapters for generator-specific prompt instructions (image/video)."""

from typing import Dict


IMAGE_GENERATORS: Dict[str, str] = {
    "midjourney-v6": "Midjourney v6",
    "flux-1.1-pro": "Flux 1.1 Pro",
    "gpt-image-1": "GPT Image 1",
}

VIDEO_GENERATORS: Dict[str, str] = {
    "runway-gen4": "Runway Gen-4",
    "veo-3": "Google Veo 3",
    "sora": "OpenAI Sora",
}


def image_generator_instructions(generator: str) -> str:
    if generator == "flux-1.1-pro":
        return (
            "Target generator: Flux 1.1 Pro. Use a dense cinematic prompt with explicit camera and lighting cues. "
            "Include an aspect-ratio marker (e.g., --ar 4:5) and one style marker to preserve deterministic checks."
        )
    if generator == "gpt-image-1":
        return (
            "Target generator: GPT Image 1. Use natural-language visual directives with high specificity. "
            "Include an aspect-ratio marker (e.g., --ar 1:1) and one style/version marker for compatibility checks."
        )

    return (
        "Target generator: Midjourney v6. Include Midjourney flags at the end: --ar [ratio] --style raw --v 6."
    )


def video_generator_instructions(generator: str) -> str:
    if generator == "veo-3":
        return (
            "Target generator: Google Veo 3. Use physically grounded motion language and explicit scene transitions."
        )
    if generator == "sora":
        return (
            "Target generator: OpenAI Sora. Use cinematic temporal continuity cues and precise camera movement instructions."
        )

    return "Target generator: Runway Gen-4. Use concise scene blocks with strong visual direction and edit rhythm."
