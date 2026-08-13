## 2026-08-12T11:40:33Z
Task:
Implement and enhance the M1 Intelligence Tools Module in `c:\MY AI\tools.py` based on the Explorer reports:
1. R1: Refactor `fetch_live_news(topic)` with multi-feed RSS fallback and html.unescape. Refactor `get_daily_briefing()` to aggregate CPU, RAM, Battery level, Weather forecast (wttr.in fallback), and top AI headlines.
2. R2: Refactor `search_web_realtime(query)` to use HTTP POST against `https://html.duckduckgo.com/html/` with form-encoded `q` data, extracting Title, decoded target URL, and Snippet cleanly.
3. R3: Refactor `automate_browser_workflow(url, action, target)` supporting open, scrape (text extraction via bs4 with SSL fallback), fill_form, click (coordinates or mouse), submit, and screenshot (calling capture_screen).
4. R4: Refactor `manage_system_performance(action, target)` supporting check (CPU/RAM/Disk/Battery/WMI Thermal Zone temp), clean (temp file cleanup + gc.collect), top_processes (top 5 process memory list via psutil), and kill (process termination by PID/name).
5. R5: Refactor `organize_downloads_folder()` using `shutil.move()`, resolving name collisions, skipping incomplete download extensions (`.crdownload`, `.tmp`), ignoring hidden files/folders, and supporting Images, Documents, Executables, Archives, Code, Media categories.
6. Update `AVAILABLE_TOOLS` dictionary and `GROQ_TOOLS` schema definitions in `tools.py` for all 6 M1 tools.
7. Run syntax checks (`python -m py_compile tools.py`) and verification script/tests to confirm functionality.

Write your handoff report to `c:\MY AI\.agents\worker_m1_1\handoff.md`.
