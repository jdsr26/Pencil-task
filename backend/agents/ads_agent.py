"""
Google Ads Agent
================
Generates Responsive Search Ad sets (3 headlines + 3 descriptions)
for Dr. Jart+ Ceramidin™ campaigns.

Inherits from BaseAgent:
  - Prompt construction
  - API calls + error handling
  - Audit logging

This file only defines:
  - The ads-specific task prompt
  - Output parsing (extract headlines + descriptions)
  - Format-specific configuration (max_tokens, temperature)
"""

import re
from typing import Dict, Any, List, Optional, Tuple

from backend.agents.base_agent import BaseAgent
from backend.pipeline.state import AssetOutput, AuditEntry


class AdsAgent(BaseAgent):
    """
    Generates Google Ads Responsive Search Ad sets.
    
    Output format:
        HEADLINE 1: [text]
        HEADLINE 2: [text]
        HEADLINE 3: [text]
        DESCRIPTION 1: [text]
        DESCRIPTION 2: [text]
        DESCRIPTION 3: [text]
    """

    def __init__(self, system_prompt: str, model: Optional[str] = None):
        super().__init__(
            name="generate_assets.ads",
            system_prompt=system_prompt,
            model=model,
            temperature=0.7,   # Creative enough for good copy, constrained enough for brand safety
            max_tokens=1000,   # Ads are short — no need for large output window
        )

    def get_task_prompt(self, product_name: str = "Dr. Jart+ product") -> str:
        """
        The ads-specific generation instruction.
        This is the TASK section of the prompt.
        Context and corrections are handled by base_agent.build_prompt().
        """
        return f"""Generate a Google Ads Responsive Search Ad set for {product_name}.

FORMAT REQUIREMENTS (strict):
- Exactly 3 headlines, each ≤30 characters
- Exactly 3 descriptions, each ≤90 characters
- Character counts include spaces and punctuation

CREATIVE REQUIREMENTS:
- Lead with benefit, support with science
- At least one headline must reference barrier repair or ceramides
- At least one description must reference the 2026 skincare trend narrative
- Position Ceramidin™ as trend-DEFINING (we started this), not trend-chasing
- Include product name (Ceramidin™ or Dr. Jart+) in at least one headline
- No fear-based messaging — frame positively (what the product BUILDS)

OUTPUT FORMAT (use this exact format — the parser depends on it):
HEADLINE 1: [your headline text]
HEADLINE 2: [your headline text]
HEADLINE 3: [your headline text]
DESCRIPTION 1: [your description text]
DESCRIPTION 2: [your description text]
DESCRIPTION 3: [your description text]

Write ONLY the 6 lines above. No explanations, no commentary, no extra text."""

    def generate(
        self,
        context: Dict[str, Any],
        feedback: List[str] = None,
    ) -> Tuple[AssetOutput, AuditEntry]:
        """
        Generate a Google Ads set.
        
        Args:
            context: Dict containing product truth, trend narratives, etc.
                     Passed directly to base_agent.build_prompt() as the
                     knowledge layer.
            feedback: List of corrections from previous scoring failure.
                     If present, this is a retry — corrections are appended
                     to the prompt automatically by base_agent.build_prompt().
        
        Returns:
            Tuple of (AssetOutput, AuditEntry)
        """
        # Call the LLM through base class
        response_text, audit = self.call(
            task=self.get_task_prompt(context.get("product_name", "Dr. Jart+ product")),
            context=context,
            feedback=feedback,
        )

        # Parse the response into structured format
        parsed = self.parse_response(response_text)

        # Update audit with parse results
        audit.metadata["parsed_headlines"] = len(parsed.get("headlines", []))
        audit.metadata["parsed_descriptions"] = len(parsed.get("descriptions", []))
        audit.metadata["parse_success"] = parsed.get("parse_success", False)

        # Create the asset output
        asset = AssetOutput(
            content=response_text,
            generated_at=audit.timestamp,
            model_used=self.model,
            prompt_hash=audit.prompt_hash,
        )

        return asset, audit

    def parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Extract headlines and descriptions from the LLM response.
        
        This parser is intentionally forgiving — LLMs sometimes add
        minor formatting variations. We handle:
          - "HEADLINE 1:" and "Headline 1:" (case variations)
          - Extra whitespace
          - Missing colons
          - Lines with or without numbering
        
        Returns:
            Dict with 'headlines', 'descriptions', and 'parse_success'
        """
        headlines = []
        descriptions = []

        for line in response_text.strip().split("\n"):
            line = line.strip()
            if not line:
                continue

            # Match headline patterns: "HEADLINE 1: text" or "Headline 1: text"
            headline_match = re.match(
                r"^(?:HEADLINE|Headline|headline)\s*\d*\s*[:\.]\s*(.+)$", line
            )
            if headline_match:
                headlines.append(headline_match.group(1).strip())
                continue

            # Match description patterns: "DESCRIPTION 1: text" or "Description 1: text"
            desc_match = re.match(
                r"^(?:DESCRIPTION|Description|description)\s*\d*\s*[:\.]\s*(.+)$", line
            )
            if desc_match:
                descriptions.append(desc_match.group(1).strip())
                continue

        return {
            "headlines": headlines,
            "descriptions": descriptions,
            "parse_success": len(headlines) >= 3 and len(descriptions) >= 3,
        }