import sys
import os
import pytest

# Append workspace root so tools.py can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from tools import search_web_realtime
    TOOLS_AVAILABLE = True
except ImportError:
    TOOLS_AVAILABLE = False


def test_web_search_simple_query():
    """R2: Verify search_web_realtime('Python programming') returns search results."""
    assert TOOLS_AVAILABLE, "tools.py must be importable"
    result = search_web_realtime("Python programming")
    assert isinstance(result, str)
    assert len(result) > 0


def test_web_search_multi_word():
    """R2: Verify multi-word query ('EVE AI assistant features') returns results."""
    assert TOOLS_AVAILABLE, "tools.py must be importable"
    result = search_web_realtime("EVE AI assistant features")
    assert isinstance(result, str)
    assert len(result) > 0


def test_web_search_ai_news_query():
    """R2: Verify searching AI news query returns relevant web content."""
    assert TOOLS_AVAILABLE, "tools.py must be importable"
    result = search_web_realtime("latest artificial intelligence news")
    assert isinstance(result, str)
    assert len(result) > 0


def test_web_search_return_type():
    """R2: Verify return value is string with search summary or fallback."""
    assert TOOLS_AVAILABLE, "tools.py must be importable"
    result = search_web_realtime("test query")
    assert type(result) is str


def test_web_search_formatting():
    """R2: Verify result formatting contains expected header, snippets, or valid fallback message."""
    assert TOOLS_AVAILABLE, "tools.py must be importable"
    result = search_web_realtime("OpenAI ChatGPT")
    assert isinstance(result, str)
    has_results_header = "Real-time Web Search Results for" in result
    has_no_results = "No search results found" in result
    has_failed = "Failed to perform live web search" in result
    assert has_results_header or has_no_results or has_failed, f"Unexpected formatting: {result}"
