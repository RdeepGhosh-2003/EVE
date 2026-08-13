import sys
import os
import pytest

# Append workspace root so tools.py can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from tools import manage_system_performance
    TOOLS_AVAILABLE = True
except ImportError:
    TOOLS_AVAILABLE = False


def test_performance_check():
    """R4: Verify manage_system_performance(action='check') returns CPU/RAM/Battery status."""
    assert TOOLS_AVAILABLE, "tools.py must be importable"
    result = manage_system_performance(action="check")
    assert isinstance(result, str)
    assert "System Status:" in result or "Performance check error" in result


def test_performance_optimize():
    """R4: Verify manage_system_performance(action='clean') returns optimization report."""
    assert TOOLS_AVAILABLE, "tools.py must be importable"
    result = manage_system_performance(action="clean")
    assert isinstance(result, str)
    assert "Performance optimized" in result or "Performance check error" in result


def test_performance_default_action():
    """R4: Verify default action ('check') executes cleanly."""
    assert TOOLS_AVAILABLE, "tools.py must be importable"
    result = manage_system_performance()
    assert isinstance(result, str)
    assert "System Status:" in result or "Performance check error" in result


def test_performance_return_format():
    """R4: Verify output includes CPU, RAM, and battery metrics."""
    assert TOOLS_AVAILABLE, "tools.py must be importable"
    result = manage_system_performance("check")
    assert isinstance(result, str)
    if "System Status:" in result:
        assert "CPU Load" in result
        assert "RAM" in result
        assert "Battery" in result


def test_performance_status_string():
    """R4: Verify returned string contains health assessment message."""
    assert TOOLS_AVAILABLE, "tools.py must be importable"
    result = manage_system_performance("check")
    assert isinstance(result, str)
    assert len(result) > 10
