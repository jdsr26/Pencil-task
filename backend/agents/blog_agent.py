"""
Blog Post Agent
===============
Generates SEO-optimized blog posts (~1000 words) for
Dr. Jart+ Ceramidin™ campaigns.

Output is a full markdown blog post with:
  - SEO title
  - Meta description (≤155 chars)
  - H2/H3 structured sections
  - Product mentions grounded in product truth
  - CTA (call to action)
  - Trend data references grounded in sourced records

This is the longest asset and the most structurally complex.
The deterministic scorer has the most checks for this format.

Inherits from BaseAgent:
  - Prompt construction
  - API calls + error handling  
  - Audit logging
"""

import re
from typing import Dict, Any, List, Optional, Tuple

from backend.agents.base_agent import BaseAgent
from backend.pipeline.state import AssetOutput, AuditEntry


class BlogAgent(BaseAgent):
    """
    Generates full blog posts in markdown format.
    
    Output structure:
        META DESCRIPTION: [≤155 chars]
        
        # [Title]
        
        [Introduction paragraph]
        
        ## [Section heading]
        [Section content]
        
        ## [Section heading]
        [Section content]
        
        ... (3-4 sections)
        
        ## [Conclusion with CTA]
    """

    def __init__(self, system_prompt: str, model: Optional[str] = None, temperature: float = 0.7):
        super().__init__(
            name="generate_assets.blog",
            system_prompt=system_prompt,
            model=model,
            temperature=temperature,
            max_tokens=4000,   # Blog posts are ~1000 words — need generous output window
        )

    def get_task_prompt(self, product_name: str = "Dr. Jart+ product") -> str:
        """Blog-specific generation instruction."""
        return f"""Generate an SEO-optimized blog post for Dr. Jart+ about {product_name} and the most relevant 2026 skincare trend.

FORMAT REQUIREMENTS (strict):
- Start with META DESCRIPTION on the first line (≤155 characters)
- Title as H1 (# Title) 
- Use H2 (## Heading) for main sections
- Use H3 (### Subheading) for subsections where needed
- Total word count: 800-1200 words
- Must include a clear CTA (call to action) in the conclusion
- Write in markdown format

STRUCTURE (follow this outline):
1. META DESCRIPTION: [one-line SEO description, ≤155 characters]

2. # [SEO-optimized, compelling title]
   Make the title specific to the 2026 trend, not generic skincare.
   Good: "Why Dermatologists Say Barrier Repair Is the Only Skincare Trend That Matters in 2026"
   Bad: "How to Take Care of Your Skin"

3. ## Introduction (~150 words)
   Hook with the trend shift — the era of over-exfoliation is over.
   Position barrier repair as the foundation of all other skincare.
   Cite specific trend data from the sourced records.

4. ## What Is Your Skin Barrier? (~200 words)
   Educational, accessible explanation.
   Use the "brick and mortar" analogy — ceramides are the mortar
   that holds the skin cells (bricks) together.
   Reference dermatologist consensus from sourced data.

5. ## Why 2026 Is the Year of Barrier-First Skincare (~250 words)
   Trend analysis anchored to sourced data:
   - Google Trends increase (searches up 29% YoY)
   - K-beauty Olive Young charts dominated by barrier products
   - TikTok #skinbarrier movement (700M+ views)
   - Dermatologist social media advocacy
   - The shift from "slugging" to targeted ceramide repair
   IMPORTANT: Every statistic or trend claim must come from the 
   sourced trend data provided in your context. Do not invent numbers.

6. ## Product Spotlight: Built for This Moment (~300 words)
   Product deep-dive:
   - 5-ceramide complex — what each ceramide does
   - Panthenol for soothing
   - Buttery-rich, non-greasy texture
   - Clinical testing and dermatologist backing
   Position as trend-DEFINING: "We didn't discover ceramides because 
   of TikTok. We've been doing this since Day 1."
   Subtly acknowledge the competitive landscape without naming competitors.
   IMPORTANT: Only use product claims that appear in the product truth data.

7. ## Conclusion + CTA (~100 words)
   Reinforce the "skin longevity" narrative.
    Suggest a simple routine with the anchor product.
   Clear CTA: link to product page, encourage trial.

SEO REQUIREMENTS:
- Naturally incorporate these keywords: "Dr. Jart+", 
    "2026 skincare trend", and anchor-product-relevant terms from context.
- Use keywords in at least 2 H2 headings
- Keep paragraphs short (3-4 sentences max) for readability
- Write for someone who researches before buying — informed, not dumbed down

GROUNDING RULES:
- Every statistic must trace back to sourced trend data in your context
- Every product claim must match the approved claims in product truth
- Do not invent numbers, percentages, or studies
- If you reference a trend, it must be from the sourced records

OUTPUT: Write the complete blog post in markdown format.
Start with META DESCRIPTION on the very first line."""

    def generate(
        self,
        context: Dict[str, Any],
        feedback: List[str] = None,
    ) -> Tuple[AssetOutput, AuditEntry]:
        """
        Generate a blog post.
        
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

        # Enrich audit with parse results
        audit.metadata["word_count"] = parsed.get("word_count", 0)
        audit.metadata["h2_count"] = parsed.get("h2_count", 0)
        audit.metadata["h3_count"] = parsed.get("h3_count", 0)
        audit.metadata["has_meta_description"] = parsed.get("has_meta_description", False)
        audit.metadata["meta_description_length"] = parsed.get("meta_description_length", 0)
        audit.metadata["has_cta"] = parsed.get("has_cta", False)
        audit.metadata["product_mentions"] = parsed.get("product_mention_count", 0)
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
        Extract structural elements from the blog post.
        
        The blog parser is the most detailed because the blog has
        the most format requirements:
          - Word count (800-1200)
          - H2 headings present
          - Meta description present and within length
          - Product mentions (minimum 3)
          - CTA present
          - Title present
        
        This is extraction + structural validation.
        Content quality is evaluated by the LLM judge.
        """
        text = response_text.strip()
        text_lower = text.lower()
        lines = text.split("\n")

        # ─── Word Count ───
        # Count words in the body (exclude meta description line)
        body_text = text
        # Remove the meta description line from word count
        for line in lines:
            if line.strip().upper().startswith("META DESCRIPTION"):
                body_text = text.replace(line, "", 1)
                break
        word_count = len(body_text.split())

        # ─── Meta Description ───
        has_meta_description = False
        meta_description_length = 0
        meta_description_text = ""

        for line in lines:
            stripped = line.strip()
            # Match: "META DESCRIPTION: text" or "Meta Description: text"
            meta_match = re.match(
                r"^(?:META\s*DESCRIPTION|Meta\s*[Dd]escription|meta\s*description)\s*[:]\s*(.+)$",
                stripped,
            )
            if meta_match:
                has_meta_description = True
                meta_description_text = meta_match.group(1).strip()
                meta_description_length = len(meta_description_text)
                break

        # ─── Headings ───
        # H1: lines starting with "# " (but not "## ")
        h1_count = len(re.findall(r"^# (?!#)", text, re.MULTILINE))

        # H2: lines starting with "## " (but not "### ")
        h2_headings = re.findall(r"^## (?!#)(.+)$", text, re.MULTILINE)
        h2_count = len(h2_headings)

        # H3: lines starting with "### "
        h3_count = len(re.findall(r"^### .+$", text, re.MULTILINE))

        # ─── Product Mentions ───
        # Count how many times the product is mentioned
        ceramidin_count = len(re.findall(r"(?i)ceramidin", text))
        drjart_count = len(re.findall(r"(?i)dr\.?\s*jart", text))
        product_mention_count = ceramidin_count + drjart_count

        # ─── CTA (Call to Action) ───
        cta_keywords = [
            "shop now", "try", "discover", "explore", "visit",
            "get yours", "add to", "find out", "learn more",
            "start your", "grab", "pick up", "order",
            "drjart.com", "available at",
        ]
        has_cta = any(keyword in text_lower for keyword in cta_keywords)

        # ─── SEO Keywords ───
        seo_keywords = [
            "skin barrier repair",
            "ceramide moisturizer",
            "barrier cream",
            "skin barrier",
        ]
        seo_keyword_count = sum(
            1 for keyword in seo_keywords if keyword in text_lower
        )

        # ─── Parse Success ───
        # Minimum structural requirements met
        parse_success = (
            word_count >= 500           # at least half the target — parser is forgiving
            and h2_count >= 2           # at least 2 section headings
            and has_meta_description    # meta description exists
            and product_mention_count >= 1  # product is mentioned at least once
        )

        return {
            "word_count": word_count,
            "h1_count": h1_count,
            "h2_count": h2_count,
            "h2_headings": h2_headings,
            "h3_count": h3_count,
            "has_meta_description": has_meta_description,
            "meta_description_text": meta_description_text,
            "meta_description_length": meta_description_length,
            "product_mention_count": product_mention_count,
            "ceramidin_mentions": ceramidin_count,
            "drjart_mentions": drjart_count,
            "has_cta": has_cta,
            "seo_keyword_count": seo_keyword_count,
            "parse_success": parse_success,
        }
"""

---

## Key Differences from Other Agents

**1. `max_tokens=4000` — the largest output window**

A 1000-word blog post is roughly 1300-1500 tokens. But the LLM also generates markdown formatting, the meta description, and headings. 4000 tokens gives comfortable headroom. If you set this to 1000, the blog would get cut off mid-sentence — a common production bug.

**2. The task prompt has GROUNDING RULES**

This is unique to the blog agent:
```
GROUNDING RULES:
- Every statistic must trace back to sourced trend data in your context
- Every product claim must match the approved claims in product truth
- Do not invent numbers, percentages, or studies
"""