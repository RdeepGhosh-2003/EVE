import sys
import os
from unittest.mock import patch, MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools import automate_browser_workflow

def test_browser_none_url():
    """
    Verify automate_browser_workflow handles url=None by defaulting to fallback URL.
    Verifies boundary case where url is None or omitted during 'open' action.
    """
    with patch("webbrowser.open") as mock_open:
        result = automate_browser_workflow(url=None, action="open")
        assert isinstance(result, str)
        assert "Opened web page: https://indeed.com." in result
        mock_open.assert_called_once_with("https://indeed.com")

def test_browser_invalid_url_format():
    """
    Verify automate_browser_workflow handles malformed URL format strings without throwing exception.
    Verifies boundary case where url lacks standard http/https prefix.
    """
    with patch("webbrowser.open") as mock_open:
        result = automate_browser_workflow(url="invalid_domain_string", action="open")
        assert isinstance(result, str)
        assert "https://invalid_domain_string" in result
        mock_open.assert_called_once_with("https://invalid_domain_string")

def test_browser_invalid_action():
    """
    Verify automate_browser_workflow returns error status for unsupported action strings.
    Verifies boundary case for invalid/unknown action parameter values.
    """
    result = automate_browser_workflow(action="fly_to_moon")
    assert isinstance(result, str)
    assert result == "Unsupported browser workflow action 'fly_to_moon'."

def test_browser_missing_target():
    """
    Verify automate_browser_workflow handles fill_form action when target is None.
    Verifies boundary case where required target parameter is missing/None.
    """
    result = automate_browser_workflow(action="fill_form", target=None)
    assert isinstance(result, str)
    assert result == "Please specify target text to type."

def test_browser_special_char_target():
    """
    Verify automate_browser_workflow handles special character strings in target parameter safely.
    Verifies boundary case for target strings containing special characters, quotes, and whitespace.
    """
    special_target = "User@123! #$%^&*()_+ {}:\"<>?~`"
    with patch("pyautogui.write") as mock_write:
        result = automate_browser_workflow(action="fill_form", target=special_target)
        assert isinstance(result, str)
        assert f"Typed input '{special_target}' into active web field." in result
        mock_write.assert_called_once_with(special_target, interval=0.04)

def test_browser_non_http_urls():
    """
    Verify automate_browser_workflow preserves non-HTTP scheme URLs (e.g. ftp://) without prepending https://.
    Verifies boundary case for non-HTTP URI schemes.
    """
    with patch("webbrowser.open") as mock_open:
        result = automate_browser_workflow(url="ftp://files.example.com", action="open")
        assert isinstance(result, str)
        assert "Opened web page: ftp://files.example.com." in result
        mock_open.assert_called_once_with("ftp://files.example.com")

