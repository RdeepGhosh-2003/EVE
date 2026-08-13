## 2026-08-12T17:07:45Z
Task Assignment for Tier 3 and Tier 4 Tests.

Objective: Write Tier 3 (Cross-Feature Interactions) and Tier 4 (Real-World Workloads) test scripts in `c:\MY AI\tests\`.

Create the following 2 test files in `c:\MY AI\tests\`:
1. `test_t3_cross_interactions.py` (6 tests for cross-feature interactions)
2. `test_t4_real_world_scenarios.py` (5 tests for end-to-end user workflows)

Requirements:
- Read c:\MY AI\TEST_INFRA.md and c:\MY AI\PROJECT.md for test specifications and interface contracts.
- Import `sys` and append `c:\MY AI` to `sys.path` so `tools.py` can be imported.
- Tier 3 tests: verify interaction between daily briefing + live news + performance guard, search + browser automation, browser automation + downloads organizer, etc.
- Tier 4 tests: end-to-end user workflow pipelines (Morning Executive Briefing, Automated Research Assistant, Workstation Cleanup Routine, Live News Ticker Broadcast, Full System Health & Cleanup Pipeline).
- Include docstrings for each test detailing the workflow scenario.
- Ensure pytest can discover and run all tests cleanly.
