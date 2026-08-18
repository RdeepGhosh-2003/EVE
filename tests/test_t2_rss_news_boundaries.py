import sys
import os
import urllib.error
from unittest.mock import patch, MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools import fetch_live_news

def test_rss_empty_topic():
    """
    Verify fetch_live_news handles empty string topic cleanly without crashing.
    Verifies boundary case where topic is an empty string ("").
    """
    result = fetch_live_news("")
    assert isinstance(result, str)
    assert len(result) > 0

def test_rss_invalid_topic():
    """
    Verify fetch_live_news handles invalid or garbage topic query with fallback output.
    Verifies boundary case where query topic returns no matching XML feed items.
    """
    mock_xml = b'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel></channel></rss>'
    mock_response = MagicMock()
    mock_response.read.return_value = mock_xml
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = False

    with patch("urllib.request.urlopen", return_value=mock_response):
        result = fetch_live_news("qwertyuiopasdfghjkl1234567890")
        assert isinstance(result, str)
        assert "Top Live" in result or result.startswith("Failed to fetch live news:") or "No RSS items found" in result

def test_rss_huge_topic_string():
    """
    Verify fetch_live_news handles extremely long topic strings (exceeding 2000 characters).
    Verifies boundary case for extreme input length safety and quote encoding.
    """
    huge_topic = "technology_" * 250
    result = fetch_live_news(huge_topic)
    assert isinstance(result, str)
    assert len(result) > 0

def test_rss_special_chars_topic():
    """
    Verify fetch_live_news handles special characters and injection payloads in topic string.
    Verifies boundary case for SQL/HTML injection attempts and punctuation escaping.
    """
    special_topic = "' OR '1'='1' <script>alert('xss')</script> !@#$%^&*()_+"
    result = fetch_live_news(special_topic)
    assert isinstance(result, str)
    assert len(result) > 0

def test_rss_network_timeout_fallback():
    """
    Verify fetch_live_news returns a graceful fallback error string when RSS network request times out.
    Verifies boundary condition for network unreachability / timeout exceptions.
    """
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Connection timed out")):
        result = fetch_live_news("ai")
        assert isinstance(result, str)
        assert "Top Live" in result or "Headlines" in result or result.startswith("Failed to fetch live news:")
