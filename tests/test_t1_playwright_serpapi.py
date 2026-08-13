import sys
import os
import pytest
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools import automate_browser_workflow, search_web_realtime


def test_playwright_imports():
    """Verify playwright sync API is importable."""
    from playwright.sync_api import sync_playwright
    assert sync_playwright is not None


def test_serpapi_imports():
    """Verify google-search-results serpapi is importable."""
    from serpapi import GoogleSearch
    assert GoogleSearch is not None


def test_browser_workflow_scrape_fallback():
    """Verify automate_browser_workflow scrape action returns page content or graceful message."""
    res = automate_browser_workflow(url="https://example.com", action="scrape")
    assert isinstance(res, str)
    assert len(res) > 0
