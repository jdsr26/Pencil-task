"""Unit tests for deterministic scoring tools."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.pipeline.tools.char_counter import validate_max_length, validate_exact_count
from backend.pipeline.tools.keyword_checker import check_keywords_present, check_keywords_absent


def test_headline_under_limit():
    result = validate_max_length("Repair Your Barrier", 30, "test")
    assert result.passed is True
    assert result.actual == "19 characters"


def test_headline_over_limit():
    result = validate_max_length("This Is A Very Long Headline That Exceeds", 30, "test")
    assert result.passed is False
    assert "Exceeds" in result.message


def test_exact_count_pass():
    result = validate_exact_count(["a", "b", "c"], 3, "test", "items")
    assert result.passed is True


def test_exact_count_fail():
    result = validate_exact_count(["a", "b"], 3, "test", "items")
    assert result.passed is False
    assert "Missing" in result.message


def test_keyword_present():
    result = check_keywords_present("Ceramidin™ Cream", ["Ceramidin", "Dr. Jart"], "test")
    assert result.passed is True


def test_keyword_absent_clean():
    result = check_keywords_absent("Great skincare product", ["miracle", "cure"], "test")
    assert result.passed is True


def test_keyword_absent_found():
    result = check_keywords_absent("This miracle cure works", ["miracle", "cure"], "test")
    assert result.passed is False
    assert "miracle" in result.message


if __name__ == "__main__":
    test_headline_under_limit()
    test_headline_over_limit()
    test_exact_count_pass()
    test_exact_count_fail()
    test_keyword_present()
    test_keyword_absent_clean()
    test_keyword_absent_found()
    print("✅ All tests passed!")
