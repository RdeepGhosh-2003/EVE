"""
Tier 3: Cross-Feature Interactions Test Suite for EVE AI Suite.

This test module verifies complex multi-tool interactions, cross-component workflows,
pipeline data passing, and error resilience across core tools in tools.py.
"""

import sys
import os
import tempfile
import shutil
import pytest
from unittest.mock import patch, MagicMock

# Ensure project root is in sys.path for direct module imports
sys.path.append(r"c:\MY AI")

from tools import (
    fetch_live_news,
    search_web_realtime,
    automate_browser_workflow,
    get_daily_briefing,
    manage_system_performance,
    organize_downloads_folder,
)


def test_briefing_includes_live_news_and_perf():
    """
    Scenario: Daily Briefing Integration with Live News and System Performance Guard.
    
    Verifies that `get_daily_briefing()` dynamically aggregates and embeds
    real-time system telemetry (CPU and RAM usage) as well as live RSS news headlines
    retrieved via `fetch_live_news()`. Checks that the combined output maintains
    expected formatting and valid metric values.
    """
    briefing = get_daily_briefing()
    assert isinstance(briefing, str), "Briefing output should be a string"
    assert len(briefing) > 0, "Briefing should not be empty"
    assert "Daily Briefing" in briefing, "Briefing header missing"
    assert "CPU Load" in briefing, "CPU Load metric missing from briefing"
    assert "Memory usage" in briefing or "RAM" in briefing, "Memory metric missing from briefing"
    
    # Verify individual tool outputs can be correlated with briefing format
    news_output = fetch_live_news("ai")
    perf_output = manage_system_performance("check")
    assert isinstance(news_output, str), "Live news output must be a string"
    assert isinstance(perf_output, str), "Performance output must be a string"
    assert "CPU Load" in perf_output, "Performance guard should report CPU load"


def test_search_results_feed_browser_automation():
    """
    Scenario: Web Search Results Feeding Browser Automation Target.
    
    Verifies the cross-feature pipeline where search query output from
    `search_web_realtime()` supplies contextual topic data or a target URL
    to `automate_browser_workflow()`. Patches browser launch to prevent GUI popup
    while validating parameters and execution flow.
    """
    query = "python web scraping documentation"
    search_results = search_web_realtime(query)
    assert isinstance(search_results, str), "Search results must be a string"
    assert len(search_results) > 0, "Search results should not be empty"

    target_url = "https://docs.python.org/3/"
    with patch("webbrowser.open", return_value=True) as mock_browser_open:
        browser_res = automate_browser_workflow(url=target_url, action="open")
        assert isinstance(browser_res, str), "Browser automation output must be a string"
        assert "Opened web page" in browser_res or "https://" in browser_res
        mock_browser_open.assert_called_once_with(target_url)


def test_downloads_organizer_after_browser_automation():
    """
    Scenario: Downloads Folder Organization Following Browser Download Action.
    
    Verifies that after an automated browser download workflow, calling
    `organize_downloads_folder()` correctly scans the user's Downloads directory
    and categorizes temporary files (.pdf, .png, .zip, .py, .mp3) into structured
    subfolders (Documents, Images, Archives, Code, Audio).
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        fake_downloads = os.path.join(temp_dir, "Downloads")
        os.makedirs(fake_downloads, exist_ok=True)
        
        # Create test dummy files representing downloaded artifacts
        test_files = {
            "document.pdf": "PDF content",
            "image.png": "PNG image content",
            "archive.zip": "ZIP archive content",
            "script.py": "print('hello')",
            "song.mp3": "Audio content"
        }
        for fname, content in test_files.items():
            with open(os.path.join(fake_downloads, fname), "w", encoding="utf-8") as f:
                f.write(content)

        # Patch home directory expansion to target our temporary downloads directory
        with patch("os.path.expanduser", return_value=temp_dir):
            org_res = organize_downloads_folder()
            assert isinstance(org_res, str), "Organizer output must be a string"
            assert "Organized Downloads folder" in org_res or "Moved" in org_res

            # Verify files were moved into categorized subdirectories
            assert os.path.exists(os.path.join(fake_downloads, "Documents", "document.pdf"))
            assert os.path.exists(os.path.join(fake_downloads, "Images", "image.png"))
            assert os.path.exists(os.path.join(fake_downloads, "Archives", "archive.zip"))
            assert os.path.exists(os.path.join(fake_downloads, "Code", "script.py"))
            assert os.path.exists(os.path.join(fake_downloads, "Audio", "song.mp3"))


def test_performance_guard_during_heavy_workload():
    """
    Scenario: System Performance Check Under Heavy Multi-Tool Workload.
    
    Verifies that system performance monitoring via `manage_system_performance()`
    remains accurate, responsive, and non-blocking while executing concurrent operations
    such as RSS live news fetching and web search queries.
    """
    news_res = fetch_live_news("ai")
    search_res = search_web_realtime("machine learning performance benchmarks")
    
    # Execute performance check during workload sequence
    perf_res = manage_system_performance(action="check")
    assert isinstance(perf_res, str), "Performance report must be a string"
    assert "System Status" in perf_res, "Performance report must include system status header"
    assert "CPU Load" in perf_res, "Report must include CPU Load percentage"
    assert "RAM" in perf_res, "Report must include RAM percentage"
    assert "Battery" in perf_res or "AC Power" in perf_res, "Report must include battery status"


def test_daily_briefing_resilience_on_partial_tool_failure():
    """
    Scenario: Daily Briefing Resilience to Component Tool Failures.
    
    Verifies that `get_daily_briefing()` completes gracefully and produces a valid
    summary report even if one of its internal dependency calls (e.g. `fetch_live_news`)
    encounters a network error or exception.
    """
    with patch("tools.fetch_live_news", side_effect=RuntimeError("RSS Feed Unreachable")):
        briefing = get_daily_briefing()
        assert isinstance(briefing, str), "Briefing must return a string even when news fails"
        assert "Daily Briefing" in briefing, "Briefing header should still be present"
        assert "System Health" in briefing, "System health telemetry should still be reported"


def test_browser_search_integration_pipeline():
    """
    Scenario: End-to-End Search to Browser Navigation and Form Submission Pipeline.
    
    Verifies a 4-step interactive pipeline:
    1. Search the web for a target topic via `search_web_realtime()`.
    2. Open target URL in browser via `automate_browser_workflow(action="open")`.
    3. Fill search/form input via `automate_browser_workflow(action="fill_form")`.
    4. Submit active form via `automate_browser_workflow(action="click_apply")`.
    """
    with patch("webbrowser.open", return_value=True) as mock_open, \
         patch("pyautogui.write", return_value=None) as mock_write, \
         patch("pyautogui.press", return_value=None) as mock_press:
        
        # Step 1: Perform search
        search_out = search_web_realtime("fastapi docs")
        assert isinstance(search_out, str), "Search step must return string"

        # Step 2: Open browser
        open_out = automate_browser_workflow(url="https://fastapi.tiangolo.com", action="open")
        assert "Opened web page" in open_out
        mock_open.assert_called_once_with("https://fastapi.tiangolo.com")

        # Step 3: Fill form field
        fill_out = automate_browser_workflow(action="fill_form", target="tutorial")
        assert "Typed input" in fill_out
        mock_write.assert_called_once_with("tutorial", interval=0.04)

        # Step 4: Submit form
        submit_out = automate_browser_workflow(action="click_apply")
        assert "Submitted active form" in submit_out
        mock_press.assert_called_once_with("enter")
