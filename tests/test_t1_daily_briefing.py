import sys
import os
import time
import pytest

# Append workspace root so tools.py can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from tools import get_daily_briefing
    TOOLS_AVAILABLE = True
except ImportError:
    TOOLS_AVAILABLE = False


def test_daily_briefing_default():
    """R1: Verify get_daily_briefing() returns a non-empty summary string."""
    assert TOOLS_AVAILABLE, "tools.py must be importable"
    result = get_daily_briefing()
    assert isinstance(result, str)
    assert len(result) > 0


def test_daily_briefing_content():
    """R1: Verify briefing string contains system metrics or failure status."""
    assert TOOLS_AVAILABLE, "tools.py must be importable"
    result = get_daily_briefing()
    assert isinstance(result, str)
    # Check for expected content markers
    has_system_health = "System Health:" in result or "CPU" in result
    has_failed = "Failed to generate daily briefing" in result
    assert has_system_health or has_failed, f"Unexpected briefing content: {result}"


def test_daily_briefing_return_type():
    """R1: Verify return type of get_daily_briefing() is string."""
    assert TOOLS_AVAILABLE, "tools.py must be importable"
    result = get_daily_briefing()
    assert type(result) is str


def test_daily_briefing_repeatability():
    """R1: Verify multiple briefing invocations execute without exceptions."""
    assert TOOLS_AVAILABLE, "tools.py must be importable"
    res1 = get_daily_briefing()
    res2 = get_daily_briefing()
    assert isinstance(res1, str) and len(res1) > 0
    assert isinstance(res2, str) and len(res2) > 0


def test_daily_briefing_non_blocking():
    """R1: Verify briefing returns within acceptable timeout (<10 seconds)."""
    assert TOOLS_AVAILABLE, "tools.py must be importable"
    start_time = time.time()
    result = get_daily_briefing()
    duration = time.time() - start_time
    assert isinstance(result, str)
    assert duration < 10.0, f"get_daily_briefing took {duration:.2f}s, exceeding 10s limit"
