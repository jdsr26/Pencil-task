"""
Keyword Checker Tool
====================
Checks for the presence or absence of specific keywords.

Two directions:
  - check_keywords_present: "At least one of these MUST be in the text"
    Used for: product name mention, trend language
  - check_keywords_absent: "NONE of these should be in the text"
    Used for: blocked language from product_truth.yaml

Case-insensitive matching by default.
"""

from typing import List

from backend.pipeline.state import DeterministicCheckDetail


def check_keywords_present(
    content: str,
    keywords: List[str],
    check_name: str,
    require_all: bool = False,
) -> DeterministicCheckDetail:
    """
    Check that required keywords are present in the content.
    
    Args:
        content: Text to search
        keywords: Keywords to look for
        check_name: Identifier for this check
        require_all: If True, ALL keywords must be present.
                     If False, at least ONE must be present.
    
    Returns:
        DeterministicCheckDetail with pass/fail
    
    Examples:
        # At least one product name must appear
        check_keywords_present(text, ["Ceramidin", "Dr. Jart"], "product_name", require_all=False)
        
        # All SEO keywords must appear
        check_keywords_present(text, ["barrier", "ceramide"], "seo_terms", require_all=True)
    """
    content_lower = content.lower()
    found = [kw for kw in keywords if kw.lower() in content_lower]
    missing = [kw for kw in keywords if kw.lower() not in content_lower]

    if require_all:
        passed = len(missing) == 0
        if passed:
            message = f"All {len(keywords)} keywords found"
        else:
            message = f"Missing: {', '.join(missing)}"
    else:
        passed = len(found) > 0
        if passed:
            message = f"Found: {', '.join(found)}"
        else:
            message = f"None of the required keywords found"

    return DeterministicCheckDetail(
        check_name=check_name,
        passed=passed,
        expected=f"{'all' if require_all else 'at least one'} of: {', '.join(keywords)}",
        actual=f"found {len(found)}/{len(keywords)}: {', '.join(found) if found else 'none'}",
        message=message,
    )


def check_keywords_absent(
    content: str,
    blocked_keywords: List[str],
    check_name: str,
) -> DeterministicCheckDetail:
    """
    Check that NO blocked keywords appear in the content.
    
    This is the anti-hallucination / brand-safety check.
    Blocked keywords come from product_truth.yaml's blocked_language list.
    
    Args:
        content: Text to search
        blocked_keywords: Terms that must NOT appear
        check_name: Identifier for this check
    
    Returns:
        DeterministicCheckDetail with pass/fail
    
    Example:
        check_keywords_absent(text, ["cure", "miracle", "magic"], "no_blocked_language")
        
        If text contains "miracle cream":
        → passed=False, actual="found blocked term: miracle"
    """
    content_lower = content.lower()
    found_blocked = []

    for keyword in blocked_keywords:
        if keyword.lower() in content_lower:
            found_blocked.append(keyword)

    passed = len(found_blocked) == 0

    if passed:
        message = f"No blocked terms found (checked {len(blocked_keywords)} terms)"
    else:
        message = f"BLOCKED terms detected: {', '.join(found_blocked)}"

    return DeterministicCheckDetail(
        check_name=check_name,
        passed=passed,
        expected=f"none of {len(blocked_keywords)} blocked terms",
        actual=f"found {len(found_blocked)} blocked term(s)" if found_blocked else "clean",
        message=message,
    )


def check_keyword_minimum_count(
    content: str,
    keyword: str,
    minimum: int,
    check_name: str,
) -> DeterministicCheckDetail:
    """
    Check that a keyword appears at least N times.
    
    Used for: "blog must mention Ceramidin™ at least 3 times"
    
    Args:
        content: Text to search
        keyword: The keyword to count
        minimum: Minimum required occurrences
        check_name: Identifier for this check
    
    Returns:
        DeterministicCheckDetail with pass/fail
    """
    import re
    count = len(re.findall(re.escape(keyword), content, re.IGNORECASE))
    passed = count >= minimum

    if passed:
        message = f"OK — found {count} occurrences"
    else:
        message = f"Only {count} occurrence(s), need at least {minimum}"

    return DeterministicCheckDetail(
        check_name=check_name,
        passed=passed,
        expected=f"≥{minimum} occurrences of '{keyword}'",
        actual=f"{count} occurrences",
        message=message,
    )