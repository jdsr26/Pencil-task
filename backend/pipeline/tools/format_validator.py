"""
Format Validator Tool
=====================
Validates structural format compliance for each asset type.
Runs all deterministic checks defined in scoring_rubric.yaml.

Returns a list of DeterministicCheckDetail results — one per check.
The score_deterministic node aggregates these into a DeterministicResult.

Each asset type has its own validation function because
each format has different structural requirements.
"""

import re
from typing import List

from backend.pipeline.state import DeterministicCheckDetail
from backend.pipeline.tools.char_counter import (
    validate_max_length,
    validate_exact_count,
    validate_word_count_range,
)
from backend.pipeline.tools.keyword_checker import (
    check_keywords_present,
    check_keywords_absent,
)


def validate_ads(
    content: str,
    parsed: dict,
    blocked_language: List[str],
) -> List[DeterministicCheckDetail]:
    """
    Run all format checks for Google Ads asset.
    
    Args:
        content: Raw generated content
        parsed: Output from ads_agent.parse_response()
                Contains 'headlines' and 'descriptions' lists
        blocked_language: Forbidden terms from product_truth.yaml
    
    Returns:
        List of all check results
    """
    checks = []
    headlines = parsed.get("headlines", [])
    descriptions = parsed.get("descriptions", [])

    # Check 1: Headline count
    checks.append(
        validate_exact_count(headlines, 3, "headline_count", "headlines")
    )

    # Checks 2-4: Individual headline character counts
    for i, headline in enumerate(headlines[:3], start=1):
        checks.append(
            validate_max_length(headline, 30, f"headline_{i}_char_count")
        )
    
    # Pad with fails if fewer than 3 headlines were parsed
    for i in range(len(headlines) + 1, 4):
        checks.append(DeterministicCheckDetail(
            check_name=f"headline_{i}_char_count",
            passed=False,
            expected="≤30 characters",
            actual="headline not found",
            message=f"Headline {i} is missing — parser could not extract it",
        ))

    # Check 5: Description count
    checks.append(
        validate_exact_count(descriptions, 3, "description_count", "descriptions")
    )

    # Checks 6-8: Individual description character counts
    for i, desc in enumerate(descriptions[:3], start=1):
        checks.append(
            validate_max_length(desc, 90, f"description_{i}_char_count")
        )
    
    # Pad with fails if fewer than 3 descriptions were parsed
    for i in range(len(descriptions) + 1, 4):
        checks.append(DeterministicCheckDetail(
            check_name=f"description_{i}_char_count",
            passed=False,
            expected="≤90 characters",
            actual="description not found",
            message=f"Description {i} is missing — parser could not extract it",
        ))

    # Check 9: Product name mentioned
    checks.append(
        check_keywords_present(
            content,
            ["Ceramidin", "Dr. Jart", "Dr Jart"],
            "contains_product_name",
            require_all=False,  # at least ONE must be present
        )
    )

    # Check 10: No blocked language
    checks.append(
        check_keywords_absent(
            content,
            blocked_language,
            "no_blocked_language",
        )
    )

    return checks


def validate_video(
    content: str,
    parsed: dict,
    blocked_language: List[str],
) -> List[DeterministicCheckDetail]:
    """
    Run all format checks for Video Prompt asset.
    
    Args:
        content: Raw generated content
        parsed: Output from video_agent.parse_response()
        blocked_language: Forbidden terms from product_truth.yaml
    """
    checks = []

    # Check 1: Aspect ratio specified
    checks.append(DeterministicCheckDetail(
        check_name="specifies_aspect_ratio",
        passed=parsed.get("has_aspect_ratio", False),
        expected="Must mention aspect ratio (9:16, 16:9, or 1:1)",
        actual="found" if parsed.get("has_aspect_ratio") else "not found",
        message="OK" if parsed.get("has_aspect_ratio") else "No aspect ratio specified",
    ))

    # Check 2: Duration specified
    checks.append(DeterministicCheckDetail(
        check_name="specifies_duration",
        passed=parsed.get("has_duration", False),
        expected="Must specify video duration",
        actual="found" if parsed.get("has_duration") else "not found",
        message="OK" if parsed.get("has_duration") else "No duration specified",
    ))

    # Check 3: Scene breakdown present
    scene_count = parsed.get("scene_count", 0)
    checks.append(DeterministicCheckDetail(
        check_name="has_scene_breakdown",
        passed=scene_count >= 2,
        expected="≥2 distinct scenes",
        actual=f"{scene_count} scenes found",
        message="OK" if scene_count >= 2 else "Insufficient scene breakdown",
    ))

    # Check 4: Product mentioned
    checks.append(
        check_keywords_present(
            content,
            ["Ceramidin", "Dr. Jart", "Dr Jart"],
            "mentions_product",
            require_all=False,
        )
    )

    # Check 5: Mood/style direction
    checks.append(DeterministicCheckDetail(
        check_name="specifies_mood_or_style",
        passed=parsed.get("has_mood", False) or parsed.get("has_color_palette", False),
        expected="Must include mood or style direction",
        actual="found" if (parsed.get("has_mood") or parsed.get("has_color_palette")) else "not found",
        message="OK" if (parsed.get("has_mood") or parsed.get("has_color_palette")) else "No mood or style direction found",
    ))

    # Check 6: No blocked language
    checks.append(
        check_keywords_absent(content, blocked_language, "no_blocked_language")
    )

    return checks


def validate_image(
    content: str,
    parsed: dict,
    blocked_language: List[str],
) -> List[DeterministicCheckDetail]:
    """
    Run all format checks for Image Prompt asset.
    
    Args:
        content: Raw generated content
        parsed: Output from image_agent.parse_response()
        blocked_language: Forbidden terms from product_truth.yaml
    """
    checks = []

    # Check 1: --ar flag present
    checks.append(DeterministicCheckDetail(
        check_name="includes_ar_flag",
        passed=parsed.get("has_ar_flag", False),
        expected="Must include --ar flag",
        actual=f"--ar {parsed.get('ar_value', 'N/A')}" if parsed.get("has_ar_flag") else "not found",
        message="OK" if parsed.get("has_ar_flag") else "Missing --ar aspect ratio flag",
    ))

    # Check 2: --style or --v flag present
    has_flags = parsed.get("has_style_flag", False) or parsed.get("has_version_flag", False)
    checks.append(DeterministicCheckDetail(
        check_name="includes_style_or_version_flag",
        passed=has_flags,
        expected="Must include --style or --v flag",
        actual="found" if has_flags else "not found",
        message="OK" if has_flags else "Missing --style or --v flag",
    ))

    # Check 3: Product mentioned
    checks.append(
        check_keywords_present(
            content,
            ["Ceramidin", "Dr. Jart", "Dr Jart"],
            "mentions_product",
            require_all=False,
        )
    )

    # Check 4: Photography/style direction present
    checks.append(DeterministicCheckDetail(
        check_name="specifies_photography_style",
        passed=parsed.get("has_style_direction", False),
        expected="Must specify visual/photography style",
        actual="found" if parsed.get("has_style_direction") else "not found",
        message="OK" if parsed.get("has_style_direction") else "No photography style specified",
    ))

    # Check 5: No blocked language
    checks.append(
        check_keywords_absent(content, blocked_language, "no_blocked_language")
    )

    return checks


def validate_blog(
    content: str,
    parsed: dict,
    blocked_language: List[str],
) -> List[DeterministicCheckDetail]:
    """
    Run all format checks for Blog Post asset.
    Most checks of any asset type — blogs have the most structural requirements.
    
    Args:
        content: Raw generated content
        parsed: Output from blog_agent.parse_response()
        blocked_language: Forbidden terms from product_truth.yaml
    """
    checks = []

    # Check 1: Word count in range
    checks.append(
        validate_word_count_range(
            content, 800, 1200, "word_count_range"
        )
    )

    # Check 2: Has H2 headings
    h2_count = parsed.get("h2_count", 0)
    checks.append(DeterministicCheckDetail(
        check_name="has_h2_headings",
        passed=h2_count >= 2,
        expected="≥2 H2 headings (## in markdown)",
        actual=f"{h2_count} H2 headings found",
        message="OK" if h2_count >= 2 else f"Only {h2_count} H2 heading(s) — need at least 2",
    ))

    # Check 3: Has meta description
    checks.append(DeterministicCheckDetail(
        check_name="has_meta_description",
        passed=parsed.get("has_meta_description", False),
        expected="Must include meta description",
        actual="found" if parsed.get("has_meta_description") else "not found",
        message="OK" if parsed.get("has_meta_description") else "No meta description found",
    ))

    # Check 4: Meta description length
    meta_length = parsed.get("meta_description_length", 0)
    if parsed.get("has_meta_description"):
        checks.append(
            validate_max_length(
                parsed.get("meta_description_text", ""),
                155,
                "meta_description_length",
            )
        )
    else:
        checks.append(DeterministicCheckDetail(
            check_name="meta_description_length",
            passed=False,
            expected="≤155 characters",
            actual="no meta description to measure",
            message="Cannot check length — meta description is missing",
        ))

    # Check 5: Product mentioned at least 3 times
    product_count = parsed.get("product_mention_count", 0)
    checks.append(DeterministicCheckDetail(
        check_name="product_mention_frequency",
        passed=product_count >= 3,
        expected="≥3 mentions of Ceramidin™ or Dr. Jart+",
        actual=f"{product_count} mentions",
        message="OK" if product_count >= 3 else f"Only {product_count} mention(s) — need at least 3",
    ))

    # Check 6: Has CTA
    checks.append(DeterministicCheckDetail(
        check_name="has_cta",
        passed=parsed.get("has_cta", False),
        expected="Must include a call to action",
        actual="found" if parsed.get("has_cta") else "not found",
        message="OK" if parsed.get("has_cta") else "No call to action detected",
    ))

    # Check 7: No blocked language
    checks.append(
        check_keywords_absent(content, blocked_language, "no_blocked_language")
    )

    return checks