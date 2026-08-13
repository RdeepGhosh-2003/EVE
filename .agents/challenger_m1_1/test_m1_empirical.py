"""
Empirical Stress Test Harness for Milestone M1 in tools.py
Target functions: fetch_live_news, get_daily_briefing, search_web_realtime, automate_browser_workflow, manage_system_performance, organize_downloads_folder
"""

import sys
import unittest
from unittest.mock import patch, MagicMock
import urllib.error
import urllib.request
import ssl
import os
import shutil
import tempfile

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import tools

class TestR1LiveNewsAndBriefing(unittest.TestCase):
    def test_fetch_live_news_empty_topic(self):
        res1 = tools.fetch_live_news("")
        self.assertIsInstance(res1, str)
        self.assertTrue(len(res1) > 0)
        
        res2 = tools.fetch_live_news("   ")
        self.assertIsInstance(res2, str)
        self.assertTrue(len(res2) > 0)

    def test_fetch_live_news_special_chars(self):
        res = tools.fetch_live_news("!@#$%^&*()_+ '<script>alert(1)</script>'")
        self.assertIsInstance(res, str)
        self.assertTrue(len(res) > 0)

    def test_fetch_live_news_unicode(self):
        res = tools.fetch_live_news("🤖 AI 人工知能 🚀 🤖")
        self.assertIsInstance(res, str)
        self.assertTrue(len(res) > 0)

    @patch("urllib.request.urlopen")
    def test_fetch_live_news_all_feeds_timeout(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError("Connection timed out")
        res = tools.fetch_live_news("ai")
        self.assertIsInstance(res, str)
        self.assertIn("Failed to fetch live news", res)

    @patch("urllib.request.urlopen")
    def test_fetch_live_news_primary_fails_secondary_succeeds(self, mock_urlopen):
        valid_rss = b"""<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Test RSS</title>
                <item>
                    <title>AI Breakthrough &amp; Future &lt;b&gt;News&lt;/b&gt;</title>
                </item>
            </channel>
        </rss>"""
        
        mock_response = MagicMock()
        mock_response.read.return_value = valid_rss
        mock_response.__enter__.return_value = mock_response

        mock_urlopen.side_effect = [urllib.error.URLError("Primary feed down"), mock_response]

        res = tools.fetch_live_news("ai")
        self.assertIn("Top Live AI News Headlines", res)
        self.assertIn("AI Breakthrough & Future News", res)

    def test_get_daily_briefing_resilience(self):
        with patch("tools.fetch_live_news", side_effect=Exception("RSS network failure")):
            briefing = tools.get_daily_briefing()
            self.assertIsInstance(briefing, str)
            self.assertIn("System Health:", briefing)
            self.assertIn("Top AI Intelligence Headlines:", briefing)
            self.assertIn("1. Live AI news headlines currently unavailable", briefing)


class TestR2SearchWebRealtime(unittest.TestCase):
    def test_search_web_empty_queries(self):
        res1 = tools.search_web_realtime("")
        self.assertEqual(res1, "No search results found for ''.")
        
        res2 = tools.search_web_realtime("   ")
        self.assertEqual(res2, "No search results found for ''.")

    def test_search_web_sql_html_injection(self):
        res1 = tools.search_web_realtime("SELECT * FROM users; DROP TABLE users; --")
        self.assertIsInstance(res1, str)
        
        res2 = tools.search_web_realtime("<script>alert('xss')</script>")
        self.assertIsInstance(res2, str)

    @patch("urllib.request.urlopen")
    def test_search_web_unquoting_ddg_post(self, mock_urlopen):
        ddg_html = """
        <html><body>
        <a class="result__a" href="/l/?uddg=https%3A%2F%2Fpython.org%2Fnews">Python <b>News</b> &amp; Updates</a>
        <a class="result__snippet">Official <i>Python</i> news and announcements.</a>
        </body></html>
        """
        mock_resp = MagicMock()
        mock_resp.read.return_value = ddg_html.encode('utf-8')
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        res = tools.search_web_realtime("python news")
        self.assertIn("Real-time Web Search Results for 'python news'", res)
        self.assertIn("Title: Python News & Updates", res)
        self.assertIn("URL: https://python.org/news", res)
        self.assertIn("Snippet: Official Python news and announcements.", res)


class TestR3AutomateBrowserWorkflow(unittest.TestCase):
    def test_automate_browser_invalid_action(self):
        res = tools.automate_browser_workflow(action="invalid_action_xyz")
        self.assertIn("Unsupported browser workflow action 'invalid_action_xyz'", res)

    @patch("webbrowser.open")
    def test_automate_browser_non_http_urls(self, mock_webbrowser_open):
        res1 = tools.automate_browser_workflow(url="ftp://files.example.com", action="open")
        # Demonstrating empirical check for URL scheme handling
        print(f"DEBUG non-http URL result: {res1}")
        self.assertIn("ftp://files.example.com", res1)
        self.assertNotIn("https://ftp://", res1)

    @patch("pyautogui.click")
    def test_automate_browser_invalid_screen_coordinates(self, mock_click):
        res1 = tools.automate_browser_workflow(action="click", target="abc,def")
        self.assertIn("Clicked mouse at current cursor position", res1)
        
        res2 = tools.automate_browser_workflow(action="click", target="100,200")
        self.assertIn("Clicked browser element at screen coordinates (100, 200)", res2)

    @patch("urllib.request.urlopen")
    def test_automate_browser_ssl_scraping_error_fallback(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b"<html><body><p>Secure Page Content</p></body></html>"
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        res = tools.automate_browser_workflow(url="https://self-signed.badssl.com", action="scrape")
        self.assertIn("Scraped text from https://self-signed.badssl.com", res)
        self.assertIn("Secure Page Content", res)
        
        kwargs = mock_urlopen.call_args[1] if mock_urlopen.call_args else {}
        if "context" in kwargs:
            self.assertEqual(kwargs["context"].verify_mode, ssl.CERT_NONE)


class TestR4ManageSystemPerformance(unittest.TestCase):
    def test_manage_system_performance_actions(self):
        res_check = tools.manage_system_performance(action="check")
        self.assertIn("System Status:", res_check)

        res_clean = tools.manage_system_performance(action="clean")
        self.assertIn("Performance optimized", res_clean)

        res_top = tools.manage_system_performance(action="top_processes")
        self.assertIn("Top 5 Memory Consuming Processes", res_top)

        res_kill_empty = tools.manage_system_performance(action="kill", target=None)
        self.assertIn("Please specify a process name or PID to terminate", res_kill_empty)

        res_invalid = tools.manage_system_performance(action="unknown_action")
        self.assertIn("System Status:", res_invalid)


class TestR5OrganizeDownloadsFolder(unittest.TestCase):
    def test_organize_downloads_folder_mock(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("os.path.expanduser", return_value=os.path.dirname(tmpdir)):
                with patch("os.path.join", side_effect=lambda a, b: os.path.join(tmpdir) if b == "Downloads" else os.path.join(a, b)):
                    # Create mock downloads files
                    os.makedirs(tmpdir, exist_ok=True)
                    with open(os.path.join(tmpdir, "test.pdf"), "w") as f:
                        f.write("doc")
                    with open(os.path.join(tmpdir, "test.png"), "w") as f:
                        f.write("img")
                    with open(os.path.join(tmpdir, "file.tmp"), "w") as f:
                        f.write("incomplete")
                    
                    res = tools.organize_downloads_folder()
                    self.assertIn("Organized Downloads folder", res)

if __name__ == "__main__":
    unittest.main(verbosity=2)
