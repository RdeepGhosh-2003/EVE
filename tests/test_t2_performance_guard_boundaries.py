import sys
import os
from unittest.mock import patch, MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools import manage_system_performance

def test_performance_invalid_action():
    """
    Verify manage_system_performance handles invalid or unrecognized action strings without throwing errors.
    Verifies boundary case for unsupported action input parameter.
    """
    result = manage_system_performance(action="invalid_action_xyz")
    assert isinstance(result, str)
    assert "System Status: CPU Load" in result

def test_performance_empty_action():
    """
    Verify manage_system_performance handles an empty string action parameter cleanly.
    Verifies boundary case where action is empty string ("").
    """
    result = manage_system_performance(action="")
    assert isinstance(result, str)
    assert "System Status: CPU Load" in result

def test_performance_extreme_metrics():
    """
    Verify manage_system_performance correctly formats output under 100% CPU/RAM load and 0% battery.
    Verifies boundary case for extreme sensor threshold values.
    """
    mock_bat = MagicMock()
    mock_bat.percent = 0.0

    mock_mem = MagicMock()
    mock_mem.percent = 100.0

    with patch("psutil.cpu_percent", return_value=100.0), \
         patch("psutil.virtual_memory", return_value=mock_mem), \
         patch("psutil.sensors_battery", return_value=mock_bat):
        result = manage_system_performance(action="check")
        assert isinstance(result, str)
        assert "CPU Load 100.0%" in result
        assert "RAM 100.0%" in result
        assert "Battery 0%" in result

def test_performance_rapid_checks():
    """
    Verify manage_system_performance handles high-frequency rapid invocations without performance degradation.
    Verifies boundary case for fast repeated status polling (20 iterations).
    """
    results = [manage_system_performance(action="check") for _ in range(20)]
    assert len(results) == 20
    for res in results:
        assert isinstance(res, str)
        assert "System Status:" in res

def test_performance_missing_battery_sensor():
    """
    Verify manage_system_performance provides fallback string on desktop hardware lacking battery sensors.
    Verifies boundary condition when psutil.sensors_battery() returns None.
    """
    with patch("psutil.sensors_battery", return_value=None):
        result = manage_system_performance(action="check")
        assert isinstance(result, str)
        assert "Battery Desktop AC Power" in result

def test_performance_whitespace_target():
    """
    Verify manage_system_performance handles whitespace-only target in kill action without terminating processes.
    Verifies boundary case where target is '   '.
    """
    result = manage_system_performance(action="kill", target="   ")
    assert isinstance(result, str)
    assert result == "Please specify a process name or PID to terminate."

def test_performance_non_string_action():
    """
    Verify manage_system_performance handles non-string action inputs (e.g. integer) safely.
    Verifies boundary case for non-string action argument.
    """
    result = manage_system_performance(action=123)
    assert isinstance(result, str)
    assert "System Status:" in result

