import sys
import os
from unittest.mock import patch
import pytest

# Append workspace root so tools.py can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from tools import automate_browser_workflow
    TOOLS_AVAILABLE = True
except ImportError:
    TOOLS_AVAILABLE = False


def test_browser_open_url():
    """R3: Verify automate_browser_workflow(url='https://example.com', action='open') succeeds."""
    assert TOOLS_AVAILABLE, "tools.py must be importable"
    with patch("webbrowser.open") as mock_open:
        result = automate_browser_workflow(url="https://example.com", action="open")
        assert isinstance(result, str)
        assert "Opened web page: https://example.com" in result
        mock_open.assert_called_once_with("https://example.com")


def test_browser_navigate_action():
    """R3: Verify automate_browser_workflow(url='https://example.com', action='navigate') handles navigation."""
    assert TOOLS_AVAILABLE, "tools.py must be importable"
    with patch("webbrowser.open") as mock_open:
        result = automate_browser_workflow(url="https://example.com", action="navigate")
        assert isinstance(result, str)
        assert "Opened web page: https://example.com" in result
        mock_open.assert_called_once_with("https://example.com")


def test_browser_click_action():
    """R3: Verify automate_browser_workflow(action='click_apply', target='submit') handles click/submit action."""
    assert TOOLS_AVAILABLE, "tools.py must be importable"
    with patch("pyautogui.press") as mock_press:
        result = automate_browser_workflow(action="click_apply", target="submit")
        assert isinstance(result, str)
        assert "Submitted active form" in result
        mock_press.assert_called_once_with("enter")


def test_browser_fill_action():
    """R3: Verify automate_browser_workflow(action='fill_form', target='John Doe') handles fill action."""
    assert TOOLS_AVAILABLE, "tools.py must be importable"
    with patch("pyautogui.write") as mock_write:
        result = automate_browser_workflow(action="fill_form", target="John Doe")
        assert isinstance(result, str)
        assert "Typed input 'John Doe'" in result
        mock_write.assert_called_once_with("John Doe", interval=0.04)


def test_browser_default_params():
    """R3: Verify calling function with default parameters executes without error."""
    assert TOOLS_AVAILABLE, "tools.py must be importable"
    with patch("webbrowser.open") as mock_open:
        result = automate_browser_workflow()
        assert isinstance(result, str)
        assert "Opened web page" in result
        mock_open.assert_called_once()
