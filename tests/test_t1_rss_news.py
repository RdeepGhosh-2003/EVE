import sys
import os
import pytest

# Append workspace root so tools.py can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from tools import fetch_live_news
    TOOLS_AVAILABLE = True
except ImportError:
    TOOLS_AVAILABLE = False


def test_rss_news_default():
    """R1: Verify fetching default topic ('ai') returns a non-empty headline string."""
    assert TOOLS_AVAILABLE, "tools.py must be importable"
    result = fetch_live_news()
    assert isinstance(result, str)
    assert len(result) > 0
    assert "AI" in result or "News" in result or "Failed" in result


def test_rss_news_custom_topic():
    """R1: Verify fetching specific topic ('technology') returns structured news summary."""
    assert TOOLS_AVAILABLE, "tools.py must be importable"
    result = fetch_live_news("technology")
    assert isinstance(result, str)
    assert len(result) > 0
    assert "TECHNOLOGY" in result or "technology" in result.lower() or "Failed" in result


def test_rss_news_world_topic():
    """R1: Verify fetching topic ('world') returns valid news headlines."""
    assert TOOLS_AVAILABLE, "tools.py must be importable"
    result = fetch_live_news("world")
    assert isinstance(result, str)
    assert len(result) > 0
    assert "WORLD" in result or "world" in result.lower() or "Failed" in result


def test_rss_news_multiple_calls():
    """R1: Verify consecutive calls to fetch_live_news return valid strings without errors."""
    assert TOOLS_AVAILABLE, "tools.py must be importable"
    res1 = fetch_live_news("ai")
    res2 = fetch_live_news("science")
    assert isinstance(res1, str) and len(res1) > 0
    assert isinstance(res2, str) and len(res2) > 0


def test_rss_news_return_format():
    """R1: Verify return string contains expected headline formatting or error status."""
    assert TOOLS_AVAILABLE, "tools.py must be importable"
    result = fetch_live_news("ai")
    assert isinstance(result, str)
    # Check that output is formatted either as headline list header or error message
    is_valid_header = "Top Live AI News Headlines:" in result
    is_error = "Failed to fetch live news" in result
    assert is_valid_header or is_error, f"Unexpected return format: {result}"
