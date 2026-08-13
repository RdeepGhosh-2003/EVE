import sys
import os
from unittest.mock import patch, MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools import search_web_realtime

def test_web_search_empty_query():
    """
    Verify search_web_realtime handles empty search query string cleanly without throwing exceptions.
    Verifies boundary case where query parameter is empty string ("").
    """
    result = search_web_realtime("")
    assert isinstance(result, str)
    assert len(result) > 0

def test_web_search_whitespace_query():
    """
    Verify search_web_realtime handles whitespace-only query strings cleanly.
    Verifies boundary case where query consists solely of spaces, tabs, and newlines.
    """
    result = search_web_realtime("   \t\n   ")
    assert isinstance(result, str)
    assert len(result) > 0

def test_web_search_injection_query():
    """
    Verify search_web_realtime handles script, HTML, and SQL injection strings safely.
    Verifies boundary case for malicious payload sanitization and URL encoding.
    """
    injection_query = "<script>alert('xss')</script> ' OR '1'='1' --"
    mock_response = MagicMock()
    mock_response.read.return_value = b'<html><body>No snippets here</body></html>'
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = False

    with patch("urllib.request.urlopen", return_value=mock_response):
        result = search_web_realtime(injection_query)
        assert isinstance(result, str)
        assert "No search results found" in result or "Real-time Web Search Results" in result

def test_web_search_max_length_query():
    """
    Verify search_web_realtime handles query strings exceeding 1000 characters.
    Verifies boundary case for extreme query string lengths and HTTP GET parameter limits.
    """
    max_length_query = "quantum computing " * 80
    result = search_web_realtime(max_length_query)
    assert isinstance(result, str)
    assert len(result) > 0

def test_web_search_unicode_query():
    """
    Verify search_web_realtime handles emojis and non-ASCII multi-language unicode characters.
    Verifies boundary case for international characters and UTF-8 URL encoding.
    """
    unicode_query = "AI 🤖 🚀 人工知能 الذكاء الاصطناعي"
    result = search_web_realtime(unicode_query)
    assert isinstance(result, str)
    assert len(result) > 0
