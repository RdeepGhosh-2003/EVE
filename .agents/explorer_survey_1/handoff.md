# Handoff Report — Codebase Backend Explorer (`explorer_survey_1`)

**Target**: EVE Backend Suite Architecture Survey & Integration Mapping  
**Working Directory**: `c:\MY AI\.agents\explorer_survey_1`  
**Date**: 2026-08-12  

---

## 1. Observation

1. **Workspace Files**:
   - `c:\MY AI\tools.py` (841 lines): Defines system functions (`get_current_time`, `open_calculator`, `open_application`, `save_memory`, `search_memory`, `draft_email`, `send_email_gmail`, `capture_screen`, `capture_and_analyze_screen`, `manage_media_volume`, `execute_system_command`, `automate_keyboard_mouse`, `manage_file_system`) and 7 Advanced Intelligence Suite functions (`fetch_live_news`, `search_web_realtime`, `automate_browser_workflow`, `get_daily_briefing`, `manage_system_performance`, `organize_downloads_folder`). Contains `AVAILABLE_TOOLS` dict (lines 477-496), `GROQ_TOOLS` list (lines 499-826), and `execute_tool()` function (lines 831-840).
   - `c:\MY AI\main.py` (475 lines): FastAPI app on port 8000. Contains `ConnectionManager` class (lines 52-81), `/ws` WebSocket endpoint (lines 91-110), tool call wrapper `hud_execute_tool` (lines 112-116), `get_cpu_temperature()` (lines 120-164), `fetch_weather()` (lines 172-243), `update_news_ticker()` (lines 245-255), `scan_local_network()` (lines 257-296), `background_monitor_loop()` (lines 298-347), `eve_voice_loop()` (lines 350-435), and `launch_native_window()` (lines 443-466).
   - `c:\MY AI\llm_agent.py` (179 lines): `EVAgent` class using Groq API (`llama-3.3-70b-versatile`). Passes `GROQ_TOOLS` to Groq chat completions, handles native tool calls (`response_message.tool_calls`), and implements fallback tool parser `parse_fallback_tool_call()` (lines 23-61).
   - `c:\MY AI\audio_handler.py` (122 lines): `AudioHandler` class using `speech_recognition` microphone input, Groq Whisper (`whisper-large-v3`) transcription, `edge-tts` speech generation (`en-US-AvaNeural`), and `pygame.mixer` playback with barge-in interruption.
   - `c:\MY AI\memory_handler.py` (158 lines): `MemoryHandler` class supporting Google Drive root folder (`Eve_Memories`) note storage/retrieval via Google Drive API v3, with local folder fallback (`Eve_Memories_Local`).
   - `c:\MY AI\requirements.txt` (22 lines): Includes `SpeechRecognition`, `pyaudio`, `groq`, `python-dotenv`, `edge-tts`, `pygame`, `soundfile`, `numpy`, `google-api-python-client`, `google-auth-httplib2`, `google-auth-oauthlib`, `Pillow`, `pyautogui`, `fastapi`, `uvicorn`, `websockets`, `pywebview`, `psutil`, `scapy`, `wmi`, `requests`.

---

## 2. Logic Chain

1. **Architecture Pattern**:
   - `tools.py` acts as the single source of truth for tool implementations and tool metadata schemas (`AVAILABLE_TOOLS`, `GROQ_TOOLS`).
   - `llm_agent.py` imports `GROQ_TOOLS` and `execute_tool` from `tools.py` to handle LLM tool calls.
   - `main.py` monkey-patches `tools.execute_tool` with `hud_execute_tool` during initialization so that every tool invocation automatically broadcasts a `tool_call` WebSocket event to the HUD frontend dashboard.
   - `main.py` manages state and telemetry across two background threads: `background_monitor_loop` (telemetry, CPU temp, network devices, periodic weather and news ticker broadcasts) and `eve_voice_loop` (speech state machine, listening, STT, LLM invocation, barge-in TTS speech).

2. **Integration Plan for R1 - R5**:
   - **R1 (Live News & Ticker)**: `fetch_live_news(topic)` in `tools.py` retrieves RSS news. `update_news_ticker()` in `main.py` runs every 120s and broadcasts `"news_ticker"` via WebSocket. `get_daily_briefing()` in `tools.py` aggregates system metrics, weather, and top 3 headlines.
   - **R2 (Real-Time Web Search)**: `search_web_realtime(query)` in `tools.py` scrapes DuckDuckGo HTML snippets cleanly and returns search results.
   - **R3 (Autonomous Browser Automation)**: `automate_browser_workflow(url, action, target)` in `tools.py` opens URLs, fills form fields, and submits forms using `webbrowser` and `pyautogui`.
   - **R4 (System Performance & Battery Guard)**: `manage_system_performance(action)` in `tools.py` checks CPU, RAM, battery. `background_monitor_loop` in `main.py` evaluates CPU temp (> 80°C) and battery (< 20%) to send WS alert events (`performance_alert`).
   - **R5 (Downloads Organizer)**: `organize_downloads_folder()` in `tools.py` categorizes files in `~/Downloads` into Images, Documents, Audio, Archives, and Code subfolders.

---

## 3. Caveats

- Hardware CPU temperature detection relies on WMI / OpenHardwareMonitor / PowerShell fallback logic; on systems without ACPI thermal sensors, it uses a psutil CPU load estimation curve (`42.0 + (cpu_pct * 0.35)`).
- Gmail and Google Drive features attempt OAuth authentication using `credentials.json` / `token.json` if available; otherwise, they gracefully fall back to local disk storage (`Eve_Memories_Local`) or simulated email output.
- Web search tool relies on DuckDuckGo HTML scraping; ensure network requests handle User-Agent headers and connection timeouts cleanly.

---

## 4. Conclusion

The EVE backend architecture is fully mapped, clean, modular, and ready for capability integration or verification. The existing codebase at `c:\MY AI` already contains core implementation skeletons for `fetch_live_news`, `search_web_realtime`, `automate_browser_workflow`, `get_daily_briefing`, `manage_system_performance`, and `organize_downloads_folder` inside `tools.py`, as well as WebSocket broadcasting mechanisms inside `main.py`.

---

## 5. Verification Method

To independently verify backend integrity and tool registration:

1. **Clean Import Check**:
   ```powershell
   python -c "import tools, main, llm_agent, audio_handler, memory_handler; print('All EVE backend modules imported successfully.')"
   ```

2. **Tool Schema & Dispatch Check**:
   ```powershell
   python -c "import tools; print(f'Available Tools: {len(tools.AVAILABLE_TOOLS)}'); print(f'Groq Tools Definitions: {len(tools.GROQ_TOOLS)}')"
   ```

3. **Sample Tool Execution**:
   ```powershell
   python -c "import tools; print(tools.get_current_time()); print(tools.manage_system_performance('check'))"
   ```
