"""
Image Prompt Agent
==================
Generates image generation prompts optimized for Midjourney v6,
GPT Image 1, Adobe Firefly, or Flux.

Output is a single prompt string with:
  - Visual direction (subject, composition, lighting)
  - Product-specific details (packaging, texture)
  - Style/mood direction
  - Generator-specific flags (--ar, --style, --v)

All target generators available through Pencil's model aggregation.

Inherits from BaseAgent:
  - Prompt construction
  - API calls + error handling
  - Audit logging
"""

import re
from typing import Dict, Any, List, Optional, Tuple

from backend.agents.base_agent import BaseAgent
from backend.prompting.generator_adapters import image_generator_instructions
from backend.pipeline.state import AssetOutput, AuditEntry


class ImageAgent(BaseAgent):
    """
    Generates image generation prompts for product photography.
    
    Output: A single prompt string ready to paste into an image generator.
    """

    def __init__(
        self,
        system_prompt: str,
        model: Optional[str] = None,
        target_generator: str = "midjourney-v6",
        temperature: float = 0.8,
    ):
        super().__init__(
            name="generate_assets.image",
            system_prompt=system_prompt,
            model=model,
            temperature=temperature,   # Tuned by run mode (creative/demo)
            max_tokens=800,    # Image prompts are concise — one dense paragraph + flags
        )
        self.target_generator = target_generator

    def get_task_prompt(self, product_name: str = "Dr. Jart+ product") -> str:
        """Image-specific generation instruction."""
        generator_notes = image_generator_instructions(self.target_generator)
        return f"""Generate an image generation prompt optimized for {self.target_generator} 
    for {product_name}.

    TARGET GENERATOR GUIDANCE:
    {generator_notes}

FORMAT REQUIREMENTS:
- Single prompt paragraph (no scene breakdown — this is a still image)
    - Include a ratio marker and style/version marker at the end (e.g., --ar [ratio] --style raw --v 6)
- Recommended aspect ratio: --ar 1:1 for social, --ar 4:5 for Instagram feed
- No text overlays in the image (text will be added in post-production)

CREATIVE REQUIREMENTS:
- Product-centric editorial beauty photography
- Show the actual Ceramidin™ product in its signature industrial-inspired teal and yellow packaging
- Include a visual metaphor for the 5-ceramide barrier complex (e.g., translucent layers, 
  protective shield, building blocks, stacked translucent films)
- Korean minimalist aesthetic — clean, warm, premium
- Soft diffused studio lighting with warm neutral tones
- The image should feel like it belongs in a Vogue Korea beauty editorial
- Connect to barrier repair visually, not just through text

VISUAL DETAILS TO INCLUDE:
- Product placement (how and where the product appears)
- Surface/background description
- Lighting direction and quality
- One hero visual element that represents the barrier concept
- Overall mood and color temperature

OUTPUT FORMAT:
Write the complete prompt as a single paragraph, followed by the markers on the same line.
Do not add explanations, commentary, or multiple options. One prompt only.

Example structure (DO NOT copy this — create original):
[Subject and composition]. [Product details]. [Visual metaphor]. [Lighting and mood]. 
[Background and styling]. [Photography style reference]. --ar 1:1 --style raw --v 6"""

    def generate(
        self,
        context: Dict[str, Any],
        feedback: List[str] = None,
    ) -> Tuple[AssetOutput, AuditEntry]:
        """
        Generate an image prompt.
        
        Args:
            context: Product truth, trend narratives, sourced claims
            feedback: Corrections from previous scoring failure (if retry)
        
        Returns:
            Tuple of (AssetOutput, AuditEntry)
        """
        response_text, audit = self.call(
            task=self.get_task_prompt(context.get("product_name", "Dr. Jart+ product")),
            context=context,
            feedback=feedback,
        )

        parsed = self.parse_response(response_text)

        # Enrich audit
        audit.metadata["has_ar_flag"] = parsed.get("has_ar_flag", False)
        audit.metadata["has_style_flag"] = parsed.get("has_style_flag", False)
        audit.metadata["has_version_flag"] = parsed.get("has_version_flag", False)
        audit.metadata["mentions_product"] = parsed.get("mentions_product", False)
        audit.metadata["prompt_length"] = parsed.get("prompt_length", 0)
        audit.metadata["parse_success"] = parsed.get("parse_success", False)

        asset = AssetOutput(
            content=response_text,
            generated_at=audit.timestamp,
            model_used=audit.metadata.get("resolved_model", self.model),
            prompt_hash=audit.prompt_hash,
        )

        return asset, audit

    def parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Validate image prompt structure.
        
        Image prompts are simpler than other assets — a single block
        of text with flags. The parser checks:
          - Midjourney flags present (--ar, --style, --v)
          - Product mentioned
          - Reasonable prompt length (not too short, not too long)
        
        Unlike ads_agent (which extracts lines) or video_agent (which 
        checks sections), this parser validates a single text block.
        Three different formats, three different parsing strategies.
        """
        text = response_text.strip()
        text_lower = text.lower()

        # Check for Midjourney flags
        has_ar_flag = "--ar" in text
        has_style_flag = "--style" in text or "--s " in text
        has_version_flag = "--v " in text or "--version" in text

        # Extract the aspect ratio value if present
        ar_match = re.search(r"--ar\s+(\d+:\d+)", text)
        ar_value = ar_match.group(1) if ar_match else None

        # Check product mention
        mentions_product = (
            "ceramidin" in text_lower
            or "dr. jart" in text_lower
            or "dr jart" in text_lower
        )

        # Check for photography/style language
        has_style_direction = any(
            keyword in text_lower
            for keyword in [
                "photography", "editorial", "studio", "lighting",
                "product shot", "close-up", "beauty", "minimalist",
                "aesthetic", "cinematic", "lifestyle",
            ]
        )

        # Prompt length check
        # Good Midjourney prompts are typically 50-500 words
        word_count = len(text.split())
        reasonable_length = 30 <= word_count <= 600

        parse_success = (
            has_ar_flag
            and mentions_product
            and reasonable_length
        )

        return {
            "has_ar_flag": has_ar_flag,
            "ar_value": ar_value,
            "has_style_flag": has_style_flag,
            "has_version_flag": has_version_flag,
            "mentions_product": mentions_product,
            "has_style_direction": has_style_direction,
            "prompt_length": word_count,
            "reasonable_length": reasonable_length,
            "parse_success": parse_success,
        }