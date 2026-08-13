import sys
import os
import psutil
from unittest.mock import patch, MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools import get_daily_briefing

def test_daily_briefing_missing_sensors():
    """
    Verify get_daily_briefing handles missing hardware telemetry or failing psutil sensors gracefully.
    Verifies boundary condition when system hardware sensors raise exceptions.
    """
    with patch("psutil.cpu_percent", side_effect=RuntimeError("Hardware sensor unavailable")):
        result = get_daily_briefing()
        assert isinstance(result, str)
        assert result.startswith("Failed to generate daily briefing:")

def test_daily_briefing_news_failure_fallback():
    """
    Verify get_daily_briefing completes briefing generation even if fetch_live_news fails.
    Verifies boundary case where dependent RSS news component returns failure error text.
    """
    with patch("tools.fetch_live_news", return_value="Failed to fetch live news: Connection reset"):
        result = get_daily_briefing()
        assert isinstance(result, str)
        assert "Good day! Here is your EVE Daily Briefing:" in result
        assert "System Health:" in result

def test_daily_briefing_rapid_invocation():
    """
    Verify get_daily_briefing handles rapid sequential calls in a tight loop without state corruption.
    Verifies boundary case for high-frequency repeated execution.
    """
    results = [get_daily_briefing() for _ in range(10)]
    assert len(results) == 10
    for res in results:
        assert isinstance(res, str)
        assert len(res) > 0

def test_daily_briefing_unicode_environment():
    """
    Verify get_daily_briefing executes safely when environment variables contain non-ASCII unicode.
    Verifies boundary case for internationalized system environments.
    """
    unicode_env = dict(os.environ)
    unicode_env["USER"] = "Ünïcödë_Usër_ñáümä"
    unicode_env["LANG"] = "ja_JP.UTF-8"
    
    with patch.dict(os.environ, unicode_env, clear=True):
        result = get_daily_briefing()
        assert isinstance(result, str)
        assert len(result) > 0

def test_daily_briefing_memory_efficiency():
    """
    Verify get_daily_briefing retains memory stability and does not leak excessive memory over repeated calls.
    Verifies boundary condition for resource leak prevention over 30 iterations.
    """
    process = psutil.Process(os.getpid())
    mem_before = process.memory_info().rss
    
    for _ in range(30):
        get_daily_briefing()
        
    mem_after = process.memory_info().rss
    # Allow reasonable memory variance (less than 15 MB growth)
    mem_diff_mb = (mem_after - mem_before) / (1024 * 1024)
    assert mem_diff_mb < 15.0
