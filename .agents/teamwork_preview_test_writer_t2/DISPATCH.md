## 2026-08-12T11:37:45Z
You are a teamwork_preview_test_writer subagent for Tier 2 tests.
Your working metadata directory is: c:\MY AI\.agents\teamwork_preview_test_writer_t2
The project workspace root is: c:\MY AI
The original user request is: c:\MY AI\.agents\ORIGINAL_REQUEST.md
The architecture document is: c:\MY AI\PROJECT.md
The test infrastructure document is: c:\MY AI\TEST_INFRA.md

Objective: Write Tier 2 (Boundary & Corner Cases) test scripts in `c:\MY AI\tests\`.

Create the following 6 test files in `c:\MY AI\tests\`:
1. `test_t2_rss_news_boundaries.py` (5 boundary tests for fetch_live_news)
2. `test_t2_daily_briefing_boundaries.py` (5 boundary tests for get_daily_briefing)
3. `test_t2_web_search_boundaries.py` (5 boundary tests for search_web_realtime)
4. `test_t2_browser_automation_boundaries.py` (5 boundary tests for automate_browser_workflow)
5. `test_t2_performance_guard_boundaries.py` (5 boundary tests for manage_system_performance)
6. `test_t2_downloads_organizer_boundaries.py` (5 boundary tests for organize_downloads_folder)

Requirements:
- Read c:\MY AI\TEST_INFRA.md and c:\MY AI\PROJECT.md for test specifications and interface contracts.
- Import `sys` and append `c:\MY AI` to `sys.path` so `tools.py` can be imported.
- Test boundary conditions: empty inputs, None values, invalid inputs, special characters, missing hardware sensors, network timeouts, non-existent directories.
- Include docstrings for each test detailing what boundary case it verifies.
- Ensure pytest can discover and run all tests cleanly.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

When finished, write handoff.md in your metadata directory c:\MY AI\.agents\teamwork_preview_test_writer_t2\handoff.md detailing created test files and test count, then send a completion message to parent.
