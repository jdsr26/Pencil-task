"""
Video Prompt Agent
==================
Generates video generation prompts (15-second vertical social ads)
for Dr. Jart+ Ceramidin™ campaigns.

Output is a structured scene-by-scene prompt ready for:
  - Runway Gen4
  - Google Veo 3
  - Sora
All available through Pencil's model aggregation layer.

Inherits from BaseAgent:
  - Prompt construction
  - API calls + error handling
  - Audit logging
"""

import re
from typing import Dict, Any, List, Optional, Tuple

from backend.agents.base_agent import BaseAgent
from backend.pipeline.state import AssetOutput, AuditEntry


class VideoAgent(BaseAgent):
    """
    Generates video generation prompts with scene-by-scene breakdowns.
    
    Output format:
        TITLE: [video title]
        DURATION: [length]
        ASPECT RATIO: [ratio]
        
        SCENE 1 (0-5s): [visual description]
        SCENE 2 (5-10s): [visual description]
        SCENE 3 (10-15s): [visual description]
        
        TEXT OVERLAYS: [on-screen text per scene]
        MOOD: [overall mood/feeling]
        COLOR PALETTE: [colors]
        MUSIC DIRECTION: [audio guidance]
    """

    def __init__(self, system_prompt: str, model: Optional[str] = None):
        super().__init__(
            name="generate_assets.video",
            system_prompt=system_prompt,
            model=model,
            temperature=0.7,
            max_tokens=1500,   # Video prompts need more space for scene descriptions
        )

    def get_task_prompt(self) -> str:
        """Video-specific generation instruction."""
        return """Generate a video generation prompt for a 15-second vertical social media ad 
for Dr. Jart+ Ceramidin™ Skin Barrier Moisturizing Cream.

FORMAT REQUIREMENTS (strict):
- Duration: 15 seconds
- Aspect ratio: 9:16 (vertical, for TikTok/Instagram Reels/YouTube Shorts)
- Must include scene-by-scene breakdown with timestamps
- Must include text overlay copy
- Must include mood, color palette, and music direction

CREATIVE REQUIREMENTS:
- Show the product's buttery-rich texture being applied to skin
- Include a visual metaphor for barrier building/reinforcement (the 5-ceramide complex)
- Dr. Jart+ signature aesthetic: clinical meets creative, warm Korean minimalism
- End with product shot + brand mark
- Connect to the 2026 barrier repair / skin longevity narrative
- No fear-based messaging — show what the product BUILDS, not what happens without it
- Feel premium, confident, and modern

OUTPUT FORMAT (use this exact structure):
TITLE: [video concept title]
DURATION: 15 seconds
ASPECT RATIO: 9:16

SCENE 1 (0-5s): [detailed visual description — what the camera sees, lighting, movement]
SCENE 2 (5-10s): [detailed visual description]
SCENE 3 (10-15s): [detailed visual description]

TEXT OVERLAYS:
- Scene 1: [on-screen text, if any]
- Scene 2: [on-screen text]
- Scene 3: [on-screen text + CTA]

MOOD: [overall feeling and emotional direction]
COLOR PALETTE: [specific colors and tones]
MUSIC DIRECTION: [audio style, tempo, instruments, reference]

Write ONLY the prompt structure above. No explanations or commentary."""

    def generate(
        self,
        context: Dict[str, Any],
        feedback: List[str] = None,
    ) -> Tuple[AssetOutput, AuditEntry]:
        """
        Generate a video prompt.
        
        Args:
            context: Product truth, trend narratives, sourced claims
            feedback: Corrections from previous scoring failure (if retry)
        
        Returns:
            Tuple of (AssetOutput, AuditEntry)
        """
        response_text, audit = self.call(
            task=self.get_task_prompt(),
            context=context,
            feedback=feedback,
        )

        # Parse the response
        parsed = self.parse_response(response_text)

        # Enrich audit with parse results
        audit.metadata["parsed_scenes"] = parsed.get("scene_count", 0)
        audit.metadata["has_mood"] = parsed.get("has_mood", False)
        audit.metadata["has_color_palette"] = parsed.get("has_color_palette", False)
        audit.metadata["has_music"] = parsed.get("has_music", False)
        audit.metadata["parse_success"] = parsed.get("parse_success", False)

        asset = AssetOutput(
            content=response_text,
            generated_at=audit.timestamp,
            model_used=self.model,
            prompt_hash=audit.prompt_hash,
        )

        return asset, audit

    def parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Extract structured elements from the video prompt.
        
        Checks for:
          - Scene breakdowns (with timestamps)
          - Mood/color/music direction
          - Aspect ratio and duration mentions
        
        This parser validates STRUCTURE, not QUALITY.
        Quality evaluation is done by the LLM judge.
        """
        text_lower = response_text.lower()
        
        # Count scenes — look for "SCENE 1", "Scene 2", etc.
        scene_pattern = re.findall(
            r"(?:SCENE|Scene|scene)\s*\d+", response_text
        )
        scene_count = len(scene_pattern)

        # Check for required sections
        has_mood = any(
            keyword in text_lower 
            for keyword in ["mood:", "mood -", "overall mood", "feeling:"]
        )
        
        has_color_palette = any(
            keyword in text_lower 
            for keyword in ["color palette:", "colour palette:", "colors:", "palette:"]
        )
        
        has_music = any(
            keyword in text_lower 
            for keyword in ["music direction:", "music:", "audio:", "sound:"]
        )
        
        has_aspect_ratio = any(
            keyword in text_lower 
            for keyword in ["9:16", "16:9", "1:1", "aspect ratio"]
        )
        
        has_duration = any(
            keyword in text_lower 
            for keyword in ["15 second", "15-second", "15s", ":15", "duration"]
        )
        
        has_text_overlays = any(
            keyword in text_lower 
            for keyword in ["text overlay", "on-screen text", "text:", "overlay:"]
        )

        # Parse success = has scenes + the key creative direction elements
        parse_success = (
            scene_count >= 2
            and has_aspect_ratio
            and has_duration
        )

        return {
            "scene_count": scene_count,
            "has_mood": has_mood,
            "has_color_palette": has_color_palette,
            "has_music": has_music,
            "has_aspect_ratio": has_aspect_ratio,
            "has_duration": has_duration,
            "has_text_overlays": has_text_overlays,
            "parse_success": parse_success,
        }