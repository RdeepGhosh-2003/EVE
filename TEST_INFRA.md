# E2E Test Infra: EVE Advanced Intelligence Suite

## Test Philosophy
- Opaque-box, requirement-driven end-to-end testing suite for EVE AI Assistant.
- Testing methodology: Category-Partition + Boundary Value Analysis + Pairwise Combinatorial + Real-World Workload Scenarios.
- Independent of implementation internals; tests target entrypoints in `tools.py`, `main.py`, and WebSocket endpoints.

## Test Runner Invocation
- Runner: `pytest`
- Execution Command: `pytest c:\MY AI\tests -v --tb=short`
- Python Environment: Python 3.x with `pytest`, `pytest-asyncio`, `fastapi`, `httpx`

## Feature Inventory & Test Coverage Goals
| # | Feature Name | Function / Interface | Tier 1 (Coverage) | Tier 2 (Boundaries) | Tier 3 (Interactions) | Tier 4 (Workloads) |
|---|--------------|----------------------|:-----------------:|:------------------:|:--------------------:|:------------------:|
| 1 | RSS Live News Fetcher | `fetch_live_news(topic)` | 5 | 5 | ✓ | ✓ |
| 2 | Daily Briefing Summary | `get_daily_briefing()` | 5 | 5 | ✓ | ✓ |
| 3 | Real-Time Web Search | `search_web_realtime(query)` | 5 | 5 | ✓ | ✓ |
| 4 | Autonomous Browser Workflow | `automate_browser_workflow(url, action, target)` | 5 | 5 | ✓ | ✓ |
| 5 | System Performance Guard | `manage_system_performance(action)` | 5 | 5 | ✓ | ✓ |
| 6 | Smart Downloads Organizer | `organize_downloads_folder()` | 5 | 5 | ✓ | ✓ |

## Test Case Specification

### Tier 1: Feature Coverage (30 Tests)
- `test_t1_rss_news.py`:
  1. `test_rss_news_default()` — Verify fetching default topic ("ai") returns non-empty headline string.
  2. `test_rss_news_custom_topic()` — Verify fetching specific topic ("technology") returns structured news summary.
  3. `test_rss_news_world_topic()` — Verify fetching topic ("world") returns valid news headlines.
  4. `test_rss_news_multiple_calls()` — Verify consecutive calls return valid news strings.
  5. `test_rss_news_return_format()` — Verify return string contains expected headline formatting / separators.
- `test_t1_daily_briefing.py`:
  1. `test_daily_briefing_default()` — Verify `get_daily_briefing()` returns non-empty summary string.
  2. `test_daily_briefing_content()` — Verify briefing string contains system metrics and news sections.
  3. `test_daily_briefing_return_type()` — Verify return type is `str`.
  4. `test_daily_briefing_repeatability()` — Verify multiple briefing invocations execute without exceptions.
  5. `test_daily_briefing_non_blocking()` — Verify briefing returns within acceptable timeout (<10s).
- `test_t1_web_search.py`:
  1. `test_web_search_simple_query()` — Verify `search_web_realtime("Python programming")` returns search results.
  2. `test_web_search_multi_word()` — Verify multi-word query ("EVE AI assistant features") returns results.
  3. `test_web_search_ai_news_query()` — Verify searching AI news query returns relevant web content.
  4. `test_web_search_return_type()` — Verify return value is string with search summary or fallback.
  5. `test_web_search_formatting()` — Verify result formatting contains titles/snippets/links or valid message.
- `test_t1_browser_automation.py`:
  1. `test_browser_open_url()` — Verify `automate_browser_workflow(url="https://example.com", action="open")` succeeds.
  2. `test_browser_navigate_action()` — Verify `automate_browser_workflow(url="https://example.com", action="navigate")` handles navigation.
  3. `test_browser_click_action()` — Verify `automate_browser_workflow(action="click", target="submit")` handles click action.
  4. `test_browser_fill_action()` — Verify `automate_browser_workflow(action="fill", target="input#name")` handles fill action.
  5. `test_browser_default_params()` — Verify calling function with default parameters executes without error.
- `test_t1_performance_guard.py`:
  1. `test_performance_check()` — Verify `manage_system_performance(action="check")` returns CPU/RAM/Battery status.
  2. `test_performance_optimize()` — Verify `manage_system_performance(action="optimize")` returns optimization report.
  3. `test_performance_default_action()` — Verify default action ("check") executes cleanly.
  4. `test_performance_return_format()` — Verify output includes CPU, RAM, and battery metrics.
  5. `test_performance_status_string()` — Verify returned string contains health assessment.
- `test_t1_downloads_organizer.py`:
  1. `test_organize_downloads_default()` — Verify `organize_downloads_folder()` runs on downloads directory.
  2. `test_organize_downloads_return_type()` — Verify return value is a status message string.
  3. `test_organize_downloads_subfolder_creation()` — Verify organizer creates standard subfolders if needed.
  4. `test_organize_downloads_file_sorting()` — Verify files are categorized into appropriate extension folders.
  5. `test_organize_downloads_repeat_run()` — Verify running organizer multiple times is idempotent.

### Tier 2: Boundary & Corner Cases (30 Tests)
- `test_t2_rss_news_boundaries.py`:
  1. `test_rss_empty_topic()` — Empty string topic handling.
  2. `test_rss_invalid_topic()` — Non-existent or garbage topic query fallback.
  3. `test_rss_huge_topic_string()` — Extremely long topic string input.
  4. `test_rss_special_chars_topic()` — Special characters and SQL/HTML injection strings in topic.
  5. `test_rss_network_timeout_fallback()` — Graceful fallback string when RSS feed URL is unreachable.
- `test_t2_daily_briefing_boundaries.py`:
  1. `test_daily_briefing_missing_sensors()` — Execution when hardware telemetry is unavailable.
  2. `test_daily_briefing_news_failure_fallback()` — Briefing completion even if RSS fetch fails.
  3. `test_daily_briefing_rapid_invocation()` — Rapid sequential calls stress test.
  4. `test_daily_briefing_unicode_environment()` — Execution under non-ASCII system environment variables.
  5. `test_daily_briefing_memory_efficiency()` — Verify memory does not leak over repeated calls.
- `test_t2_web_search_boundaries.py`:
  1. `test_web_search_empty_query()` — Empty string search query handling.
  2. `test_web_search_whitespace_query()` — Whitespace-only search query handling.
  3. `test_web_search_injection_query()` — Query with HTML/script/SQL injection attempts.
  4. `test_web_search_max_length_query()` — Query exceeding 1000 characters.
  5. `test_web_search_unicode_query()` — Query with emojis and multi-language non-ASCII text.
- `test_t2_browser_automation_boundaries.py`:
  1. `test_browser_none_url()` — URL set to None or empty string.
  2. `test_browser_invalid_url_format()` — Malformed URL string (e.g. `ht!tp://invalid`).
  3. `test_browser_invalid_action()` — Unsupported action string (e.g. `action="fly"`).
  4. `test_browser_missing_target()` — Action requiring target called with `target=None`.
  5. `test_browser_special_char_target()` — Special character selector string in target.
- `test_t2_performance_guard_boundaries.py`:
  1. `test_performance_invalid_action()` — Invalid action name handling.
  2. `test_performance_empty_action()` — Empty string action.
  3. `test_performance_extreme_metrics()` — Simulated 100% CPU / 0% Battery thresholds.
  4. `test_performance_rapid_checks()` — High frequency check loop.
  5. `test_performance_missing_battery_sensor()` — Desktop system without battery sensor fallback.
- `test_t2_downloads_organizer_boundaries.py`:
  1. `test_organize_nonexistent_dir()` — Handling when target directory path does not exist.
  2. `test_organize_readonly_files()` — Handling locked/read-only files during organization.
  3. `test_organize_path_traversal_filenames()` — Files with `..` or special path chars in name.
  4. `test_organize_duplicate_filenames()` — Files with identical names in target directories.
  5. `test_organize_large_number_of_files()` — Handling directories with 100+ files.

### Tier 3: Cross-Feature Interactions (6 Tests)
- `test_t3_cross_interactions.py`:
  1. `test_briefing_includes_live_news_and_perf()` — Verify daily briefing dynamically embeds outputs from `fetch_live_news()` and `manage_system_performance()`.
  2. `test_search_results_feed_browser_automation()` — Verify web search results can supply target URL to browser automation workflow.
  3. `test_downloads_organizer_after_browser_automation()` — Verify organizing downloads folder after browser automation download action.
  4. `test_performance_guard_during_heavy_workload()` — Verify performance check while executing concurrent news fetch and web search.
  5. `test_daily_briefing_resilience_on_partial_tool_failure()` — Verify daily briefing produces complete report even if one tool fails.
  6. `test_browser_search_integration_pipeline()` — End-to-end chaining of web search query to browser navigation target.

### Tier 4: Real-World Application Scenarios (5 Tests)
- `test_t4_real_world_scenarios.py`:
  1. `test_scenario_morning_executive_briefing()` — User starts day: trigger daily briefing, fetch live tech news, check system battery/performance health.
  2. `test_scenario_automated_research_assistant()` — User requests AI research: run web search, open browser to top result URL, summarize page.
  3. `test_scenario_workstation_cleanup_routine()` — Periodic maintenance: organize cluttered downloads folder, optimize system performance, log health status.
  4. `test_scenario_live_news_ticker_broadcast()` — Continuous news monitoring: fetch multiple news feeds, format marquee ticker string, broadcast status.
  5. `test_scenario_full_suite_health_and_stress()` — Comprehensive workflow exercising all 6 tools in sequential workflow pipeline.

## Total Test Count Summary
- Tier 1: 30 tests
- Tier 2: 30 tests
- Tier 3: 6 tests
- Tier 4: 5 tests
- **Total: 71 test cases**
