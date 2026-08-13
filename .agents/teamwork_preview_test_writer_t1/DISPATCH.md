## 2026-08-12T17:07:45+05:30

Objective: Write Tier 1 (Feature Coverage) test scripts in `c:\MY AI\tests\`.

Create the following 6 test files in `c:\MY AI\tests\`:
1. `test_t1_rss_news.py` (5 tests for fetch_live_news)
2. `test_t1_daily_briefing.py` (5 tests for get_daily_briefing)
3. `test_t1_web_search.py` (5 tests for search_web_realtime)
4. `test_t1_browser_automation.py` (5 tests for automate_browser_workflow)
5. `test_t1_performance_guard.py` (5 tests for manage_system_performance)
6. `test_t1_downloads_organizer.py` (5 tests for organize_downloads_folder)

Requirements:
- Read c:\MY AI\TEST_INFRA.md and c:\MY AI\PROJECT.md for test specifications and interface contracts.
- Import `sys` and append `c:\MY AI` to `sys.path` so `tools.py` can be imported.
- Handle cases gracefully where `tools.py` or functions are in development using try/except or pytest assertions, but test actual function calls when `tools.py` is present.
- Include docstrings for each test detailing what feature requirement it verifies.
- Ensure pytest can discover and run all tests with exit code 0 or proper assertion results.
