"""
Judge Agent (LLM-as-Judge)
==========================
Evaluates generated assets on subjective dimensions that
rule-based checks cannot measure:
  - Brand alignment (does it sound like Dr. Jart+?)
  - Trend alignment (does it connect to the 2026 narrative?)

This is Tier 2 of the hybrid scoring system.
Tier 1 (deterministic) handles format compliance.
Tier 2 (this agent) handles subjective quality.

KEY DESIGN DIFFERENCES from creative agents:
  - Temperature: 0.3 (not 0.7) — we want CONSISTENT scoring, not creativity
  - Output: Structured JSON (uses call_json, not call)
  - Persona: Critic, not creator — different system prompt
  - Validation: Response is parsed with Pydantic (LLMJudgeResult)

Inherits from BaseAgent:
  - Prompt construction
  - API calls + error handling
  - Audit logging
"""

from typing import Dict, Any, List, Optional, Tuple

from backend.agents.base_agent import BaseAgent
from backend.pipeline.state import LLMJudgeResult, AssetType, AuditEntry


# ─────────────────────────────────────────────
# Judge System Prompt
# ─────────────────────────────────────────────
# This is a DIFFERENT persona from the creative agents.
# Creative agents: "You are the creative voice of Dr. Jart+"
# Judge agent: "You are a Brand QA critic for Dr. Jart+"
#
# The separation matters — the creator and the critic
# should not share the same persona. In production,
# you could even use a different model for judging.

JUDGE_SYSTEM_PROMPT = """You are a rigorous Brand QA critic for Dr. Jart+. 
Your job is to evaluate creative assets against brand standards and trend requirements.

You are NOT a creator. You are an auditor. Be critical, specific, and actionable.
Do not praise unless warranted. Your job is to find problems and quantify quality.

BRAND VOICE REFERENCE (what good looks like):
- Personality: "Smart friend who happens to be a dermatologist"
- Formality: Conversational but knowledgeable — never stiff, never sloppy
- Confidence: Assertive about science, inviting about experience
- Humor: Witty, not silly. Clever wordplay welcome. Never slapstick.
- Innovation: K-beauty science as exciting, not intimidating
- Audience: Inclusive, gender-neutral, 18-35 core

FORBIDDEN PATTERNS (flag these immediately):
- Fear-based messaging: "If your barrier is compromised...", "Without protection..."
- Gendered language: "Ladies", "girls", "for women"
- Hyperbolic claims: "miracle", "magic", "instant transformation"
- Competitor disparagement: naming competitors negatively
- Generic copy: Could be any skincare brand, not specifically Dr. Jart+
- Jargon without context: INCI names or clinical terms without explanation

SCORING GUIDE:

Brand Alignment (0-100):
  90-100: Perfect brand voice. Could go live on drjart.com today.
  75-89:  Good but minor issues. Slight tone drift, fundamentally correct.
  50-74:  Noticeable problems. Off-brand in specific ways.
  25-49:  Significant misalignment. Reads like generic skincare copy.
  0-24:   Completely off-brand.

Trend Alignment (0-100):
  90-100: Deeply trend-connected. Product feels trend-DEFINING.
          References sourced data. Barrier repair woven naturally.
  75-89:  Good connection. Mentions barrier repair, positions well.
  50-74:  Surface-level. Mentions "barrier" but doesn't meaningfully connect.
  25-49:  Weak. Generic messaging, minimal trend connection.
  0-24:   No trend connection at all.

CRITICAL RULES:
- Be specific in feedback. Not "needs improvement" but "Headline 2 uses 
  fear-based framing — rephrase to positive positioning."
- Always give 3 feedback points: at least 1 strength and at least 1 improvement.
- Scores must reflect the scoring guide above. Don't default to 80 for everything.
- If the asset contains a forbidden pattern, brand_alignment cannot exceed 74.
"""


class JudgeAgent(BaseAgent):
    """
    LLM-as-Judge for subjective scoring.
    
    Unlike creative agents:
      - Uses call_json() for structured output
      - Lower temperature (0.3) for consistent scoring
      - Different persona (critic, not creator)
      - Validates response against LLMJudgeResult Pydantic model
    """

    def __init__(self, model: Optional[str] = None, temperature: float = 0.3):
        super().__init__(
            name="score_llm_judge",
            system_prompt=JUDGE_SYSTEM_PROMPT,
            model=model,
            temperature=temperature,   # Tuned by run mode (creative/demo)
            max_tokens=800,    # JSON scores + 3 feedback points don't need much space
        )

    def build_judge_task(
        self,
        asset_type: AssetType,
        asset_content: str,
        trend_narratives: List[str],
        sourced_claims: List[str],
    ) -> str:
        """
        Build the evaluation task prompt for a specific asset.
        
        The judge sees:
          1. What asset type it's evaluating
          2. The actual generated content
          3. The trend narratives (to check trend alignment)
          4. Key sourced claims (to verify grounding)
        
        Args:
            asset_type: Which asset (ads, video, image, blog)
            asset_content: The generated content to evaluate
            trend_narratives: Top 3 narratives from Phase 1
            sourced_claims: Key claims from source records
        
        Returns:
            The complete task prompt for the judge
        """
        return f"""Evaluate this {asset_type.value.upper()} asset for Dr. Jart+ Ceramidin™ campaign.

=== ASSET TO EVALUATE ===
{asset_content}

=== TREND NARRATIVES (from sourced data — asset should reflect these) ===
{chr(10).join(f"  - {n}" for n in trend_narratives)}

=== KEY SOURCED CLAIMS (asset should be grounded in these, not inventing data) ===
{chr(10).join(f"  - {c}" for c in sourced_claims[:10])}

=== YOUR TASK ===
Score this asset on two dimensions and provide specific, actionable feedback.

Return ONLY valid JSON in this EXACT format (no markdown, no backticks, no explanation):
{{"brand_alignment": <integer 0-100>, "trend_alignment": <integer 0-100>, "feedback": ["<point 1>", "<point 2>", "<point 3>"]}}

Rules:
- brand_alignment and trend_alignment must be integers between 0 and 100
- feedback must be an array of exactly 3 strings
- Each feedback point must be specific and actionable
- At least 1 feedback point must identify a strength
- At least 1 feedback point must suggest an improvement (unless score is 95+)
- If a forbidden pattern is present, brand_alignment CANNOT exceed 74
- Do NOT default to 80 for everything — use the full scoring range"""

    def score(
        self,
        asset_type: AssetType,
        asset_content: str,
        trend_narratives: List[str],
        sourced_claims: List[str],
    ) -> Tuple[LLMJudgeResult, AuditEntry]:
        """
        Score a single asset.
        
        This is the main entry point. It:
          1. Builds the judge task prompt
          2. Calls the LLM via call_json() for structured output
          3. Validates the response against LLMJudgeResult
          4. Handles validation failures with a retry
          5. Returns the validated score + audit entry
        
        Args:
            asset_type: Which asset type (for context in the prompt)
            asset_content: The generated content to evaluate
            trend_narratives: From state — the 3 distilled narratives
            sourced_claims: From state — key claims from source records
        
        Returns:
            Tuple of (LLMJudgeResult, AuditEntry)
        """
        task = self.build_judge_task(
            asset_type=asset_type,
            asset_content=asset_content,
            trend_narratives=trend_narratives,
            sourced_claims=sourced_claims,
        )

        try:
            # First attempt — call_json handles JSON extraction
            parsed_json, audit = self.call_json(task=task)
            
            # Validate against Pydantic model
            result = LLMJudgeResult(
                asset_type=asset_type,
                brand_alignment=parsed_json["brand_alignment"],
                trend_alignment=parsed_json["trend_alignment"],
                feedback=parsed_json.get("feedback", []),
                raw_response=str(parsed_json),
                model_used=audit.metadata.get("resolved_model", self.model),
            )

            # Enrich audit
            audit.metadata["score_brand"] = result.brand_alignment
            audit.metadata["score_trend"] = result.trend_alignment
            audit.metadata["feedback_count"] = len(result.feedback)
            audit.metadata["validation"] = "success"

            return result, audit

        except (ValueError, KeyError) as first_error:
            # JSON parse failed or missing fields — retry with stricter prompt
            retry_task = task + """

IMPORTANT: Your previous response was not valid JSON. 
You MUST return ONLY a JSON object. No text before or after.
No markdown code fences. No explanation.
Exactly this format:
{"brand_alignment": 75, "trend_alignment": 80, "feedback": ["point 1", "point 2", "point 3"]}"""

            try:
                parsed_json, audit = self.call_json(task=retry_task)
                
                result = LLMJudgeResult(
                    asset_type=asset_type,
                    brand_alignment=parsed_json["brand_alignment"],
                    trend_alignment=parsed_json["trend_alignment"],
                    feedback=parsed_json.get("feedback", []),
                    raw_response=str(parsed_json),
                    model_used=audit.metadata.get("resolved_model", self.model),
                )

                audit.metadata["score_brand"] = result.brand_alignment
                audit.metadata["score_trend"] = result.trend_alignment
                audit.metadata["feedback_count"] = len(result.feedback)
                audit.metadata["validation"] = "success_on_retry"
                audit.metadata["first_attempt_error"] = str(first_error)

                return result, audit

            except (ValueError, KeyError) as second_error:
                # Both attempts failed — return a conservative fallback score
                # This prevents the pipeline from crashing on judge failure
                audit = self._create_fallback_audit(
                    asset_type=asset_type,
                    first_error=str(first_error),
                    second_error=str(second_error),
                )
                
                fallback = LLMJudgeResult(
                    asset_type=asset_type,
                    brand_alignment=50,    # Conservative — triggers re-evaluation
                    trend_alignment=50,    # Conservative — triggers re-evaluation
                    feedback=[
                        "SYSTEM: LLM judge failed to return valid scores after 2 attempts",
                        f"SYSTEM: First error — {str(first_error)[:100]}",
                        f"SYSTEM: Second error — {str(second_error)[:100]}",
                    ],
                    raw_response=f"PARSE_FAILURE: {str(second_error)}",
                    model_used=self.model,
                )

                return fallback, audit

    def _create_fallback_audit(
        self,
        asset_type: AssetType,
        first_error: str,
        second_error: str,
    ) -> AuditEntry:
        """Create an audit entry for judge parse failure."""
        from backend.observability.audit_log import create_audit_entry

        return create_audit_entry(
            node=f"score_llm_judge.{asset_type.value}",
            action="judge_parse_failure",
            input_snapshot={"asset_type": asset_type.value},
            output_snapshot={
                "fallback_scores": {"brand_alignment": 50, "trend_alignment": 50},
                "reason": "LLM judge failed to return valid JSON after 2 attempts",
            },
            model_used=self.model,
            metadata={
                "first_error": first_error[:200],
                "second_error": second_error[:200],
                "validation": "fallback_used",
            },
        )