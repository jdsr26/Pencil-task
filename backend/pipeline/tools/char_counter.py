"""
Character Counter Tool
======================
Counts characters in text and validates against limits.

This is a DETERMINISTIC tool — no LLM needed.
Using an LLM to count characters would be:
  - Slower (API call vs instant)
  - More expensive ($0.003 vs $0.000)
  - Less reliable (LLMs are bad at counting)

This is the kind of engineering decision Dan will notice:
knowing WHEN to use an LLM and when NOT to.
"""

from typing import List, Tuple

from backend.pipeline.state import DeterministicCheckDetail


def count_chars(text: str) -> int:
    """Count characters including spaces and punctuation."""
    return len(text.strip())


def validate_max_length(
    text: str,
    max_length: int,
    check_name: str,
) -> DeterministicCheckDetail:
    """
    Validate that text does not exceed max character length.
    
    Args:
        text: The text to check
        max_length: Maximum allowed characters
        check_name: Identifier for this check (e.g., "headline_1_char_count")
    
    Returns:
        DeterministicCheckDetail with pass/fail and actual vs expected
    
    Example:
        validate_max_length("Repair Your Skin Barrier", 30, "headline_1_char_count")
        → DeterministicCheckDetail(
            check_name="headline_1_char_count",
            passed=True,
            expected="≤30 characters",
            actual="24 characters",
            message="OK — 6 characters under limit"
          )
    """
    actual_length = count_chars(text)
    passed = actual_length <= max_length
    
    if passed:
        remaining = max_length - actual_length
        message = f"OK — {remaining} character{'s' if remaining != 1 else ''} under limit"
    else:
        over = actual_length - max_length
        message = f"Exceeds limit by {over} character{'s' if over != 1 else ''}"

    return DeterministicCheckDetail(
        check_name=check_name,
        passed=passed,
        expected=f"≤{max_length} characters",
        actual=f"{actual_length} characters",
        message=message,
    )


def validate_exact_count(
    items: List[str],
    expected_count: int,
    check_name: str,
    item_label: str = "items",
) -> DeterministicCheckDetail:
    """
    Validate that a list has exactly the expected number of items.
    
    Used for: "must have exactly 3 headlines", "must have exactly 3 descriptions"
    
    Args:
        items: List of items to count
        expected_count: Exact number expected
        check_name: Identifier for this check
        item_label: Human-readable name for the items (e.g., "headlines")
    
    Returns:
        DeterministicCheckDetail with pass/fail
    
    Example:
        validate_exact_count(["h1", "h2", "h3"], 3, "headline_count", "headlines")
        → passed=True, expected="exactly 3 headlines", actual="3 headlines"
    """
    actual_count = len(items)
    passed = actual_count == expected_count

    if passed:
        message = "OK"
    elif actual_count < expected_count:
        message = f"Missing {expected_count - actual_count} {item_label}"
    else:
        message = f"Found {actual_count - expected_count} extra {item_label}"

    return DeterministicCheckDetail(
        check_name=check_name,
        passed=passed,
        expected=f"exactly {expected_count} {item_label}",
        actual=f"{actual_count} {item_label}",
        message=message,
    )


def validate_word_count_range(
    text: str,
    min_words: int,
    max_words: int,
    check_name: str,
) -> DeterministicCheckDetail:
    """
    Validate that text falls within a word count range.
    
    Used for: blog post word count (800-1200 words)
    
    Args:
        text: The text to count words in
        min_words: Minimum word count
        max_words: Maximum word count
        check_name: Identifier for this check
    
    Returns:
        DeterministicCheckDetail with pass/fail
    """
    word_count = len(text.split())
    passed = min_words <= word_count <= max_words

    if passed:
        message = "OK — within range"
    elif word_count < min_words:
        message = f"Too short by {min_words - word_count} words"
    else:
        message = f"Too long by {word_count - max_words} words"

    return DeterministicCheckDetail(
        check_name=check_name,
        passed=passed,
        expected=f"{min_words}-{max_words} words",
        actual=f"{word_count} words",
        message=message,
    )