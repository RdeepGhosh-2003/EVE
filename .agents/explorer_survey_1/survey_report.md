# EVE Backend Codebase Survey & Capability Integration Blueprint

**Author**: Teamwork Preview Explorer (`teamwork_preview_explorer`)  
**Date**: 2026-08-12  
**Target Repository**: `c:\MY AI`  
**Working Directory**: `c:\MY AI\.agents\explorer_survey_1`  

---

## 1. Executive Summary

The EVE AI Assistant backend is a multithreaded Python application built around a **FastAPI + Uvicorn** server, a **Groq LLM agent** (`llama-3.3-70b-versatile`), **Edge-TTS / SpeechRecognition / Whisper voice loop**, **pywebview** native GUI window, and a **WebSocket connection manager** broadcasting real-time telemetry, state changes, weather, news ticker, and tool execution events.

All system tools are defined in `tools.py` using a dual-registration pattern (`AVAILABLE_TOOLS` map + `GROQ_TOOLS` OpenAI-compatible schema array), dispatched by `execute_tool()`, and intercepted in `main.py` by `hud_execute_tool()` for real-time WebSocket HUD notifications.

---

## 2. Component Analysis & Capability Mapping

### 2.1 Dependencies (`requirements.txt`)
- **Speech & Audio**: `SpeechRecognition`, `pyaudio`, `edge-tts`, `pygame`, `soundfile`, `numpy`
- **LLM & Cloud**: `groq`, `python-dotenv`, `google-api-python-client`, `google-auth-httplib2`, `google-auth-oauthlib`, `requests`
- **Automation & Hardware**: `pyautogui`, `Pillow`, `psutil`, `scapy`, `wmi`
- **Web & Interface**: `fastapi`, `uvicorn`, `websockets`, `pywebview`

### 2.2 Core Modules Mapping

| Module | File Path | Primary Responsibilities |
|---|---|---|
| **Tools Module** | `tools.py` (841 lines) | System automation functions (time, calc, apps, files, email, vision AI, volume, CLI execution), 7 Advanced Intelligence Suite tools, tool registry dictionaries (`AVAILABLE_TOOLS`, `GROQ_TOOLS`), dispatch mechanism (`execute_tool`). |
| **Main Server** | `main.py` (475 lines) | FastAPI web server (`/`, `/dashboard`), WebSocket endpoint (`/ws`), `ConnectionManager` event broadcaster, WMI/psutil hardware CPU temp & telemetry, Open-Meteo weather fetch, background loops (`background_monitor_loop`, `eve_voice_loop`), pywebview native window launcher (`launch_native_window`). |
| **LLM Agent** | `llm_agent.py` (179 lines) | `EVAgent` class managing conversation history, Groq chat completion API with native JSON tool calls, fallback tool parser (`parse_fallback_tool_call` for JSON/XML tags), latency tracking (`last_latency_ms`). |
| **Audio Handler** | `audio_handler.py` (122 lines) | `AudioHandler` class for hands-free ambient speech listening via `speech_recognition`, transcription via Groq `whisper-large-v3`, TTS generation via `edge-tts` (`en-US-AvaNeural`), and audio playback via `pygame.mixer` with barge-in interruption (`stop_speaking`). |
| **Memory Handler** | `memory_handler.py` (158 lines) | `MemoryHandler` class managing persistent memory notes saved to Google Drive root folder (`Eve_Memories`) via Drive API v3, with automatic local fallback storage (`Eve_Memories_Local`). |

---

## 3. Tool Registration & Execution Patterns

### 3.1 Dual-Registry Architecture (`tools.py`)
1. **Execution Map (`AVAILABLE_TOOLS`)**:
   ```python
   AVAILABLE_TOOLS = {
       "get_current_time": get_current_time,
       "open_calculator": open_calculator,
       "open_application": open_application,
       "save_memory": save_memory,
       "search_memory": search_memory,
       "draft_email": draft_email,
       "capture_screen": capture_screen,
       "capture_and_analyze_screen": capture_and_analyze_screen,
       "manage_media_volume": manage_media_volume,
       "execute_system_command": execute_system_command,
       "automate_keyboard_mouse": automate_keyboard_mouse,
       "manage_file_system": manage_file_system,
       "fetch_live_news": fetch_live_news,
       "search_web_realtime": search_web_realtime,
       "automate_browser_workflow": automate_browser_workflow,
       "get_daily_briefing": get_daily_briefing,
       "manage_system_performance": manage_system_performance,
       "organize_downloads_folder": organize_downloads_folder
   }
   ```
2. **LLM Function Schema Array (`GROQ_TOOLS`)**:
   List of OpenAI-compatible function definition dictionaries (`type: "function"`, `function: {name, description, parameters}`).

3. **Dispatcher Function (`execute_tool`)**:
   ```python
   def execute_tool(tool_name: str, tool_args: dict = None) -> str:
       if tool_name in AVAILABLE_TOOLS:
           fn = AVAILABLE_TOOLS[tool_name]
           try:
               return fn(**tool_args) if tool_args else fn()
           except Exception as e:
               return f"Error executing tool '{tool_name}': {str(e)}"
       return f"Unknown tool '{tool_name}'"
   ```

### 3.2 Main Server Tool Wrapper Interceptor (`main.py`)
`main.py` monkey-patches `tools.execute_tool` at startup to broadcast WebSocket HUD events whenever a tool is invoked:
```python
original_execute_tool = tools.execute_tool
def hud_execute_tool(tool_name: str, tool_args: dict = None) -> str:
    manager.send_event("tool_call", {"value": tool_name})
    return original_execute_tool(tool_name, tool_args)
tools.execute_tool = hud_execute_tool
```

---

## 4. WebSocket Server & State Broadcast System

### 4.1 Connection Manager (`ConnectionManager` in `main.py`)
- Tracks connected clients in `active_connections: List[WebSocket]`.
- Implements thread-safe event emission via `send_event(event_type, value)`:
  ```python
  def send_event(self, event_type: str, value):
      data = {"type": event_type, "value": value} if isinstance(value, str) else {"type": event_type, **value}
      if self.loop and self.loop.is_running():
          asyncio.run_coroutine_threadsafe(self.broadcast_json(data), self.loop)
  ```

### 4.2 WebSocket Event Protocol

| Event Type | Payload Format | Trigger Source |
|---|---|---|
| `telemetry` | `{cpu, ram, cpu_temp, rx_kb, tx_kb, battery}` | `background_monitor_loop` (every 2s) |
| `weather` | `{day_header, temp_c, apparent_c, condition, icon, humidity, wind_kph, precip_pct, today_max, today_min, hourly}` | Open-Meteo API (every 5m / on connect / on WS request) |
| `news_ticker` | `{value: "Headline 1 /// Headline 2 /// ..."}` | `update_news_ticker()` (every 2m) |
| `network_devices` | `{devices: [{ip, mac, host}]}` | `scan_local_network()` |
| `state` | `{value: "IDLE" \| "LISTENING" \| "THINKING" \| "SPEAKING"}` | `eve_voice_loop` state transitions |
| `user_speech` | `{value: "transcription text"}` | `eve_voice_loop` after wake-word detection |
| `eve_speech` | `{value: "response text"}` | `eve_voice_loop` before TTS playback |
| `latency` | `{ms, queries}` | `eve_voice_loop` after LLM response |
| `tool_call` | `{value: "tool_name"}` | `hud_execute_tool` wrapper |
| `system` | `{value: "system notification text"}` | Startup / Shutdown events |

---

## 5. Background Loops & Multithreading Architecture

`main.py` spawns two daemon background threads at application startup (`@app.on_event("startup")`):

1. **`background_monitor_loop`**:
   - Polling interval: 2 seconds.
   - Reads hardware CPU temp (via 4-tier fallback: MSAcpi WMI -> OpenHardwareMonitor WMI -> PowerShell CIM -> psutil CPU estimate + 5-sample moving average).
   - Monitors network RX/TX KB/s, RAM %, Battery %.
   - Triggers weather update every 5 minutes and RSS news ticker update every 2 minutes.
   - Executes ARP / Scapy network security scan.

2. **`eve_voice_loop`**:
   - Hands-free voice state machine loop.
   - Listens via `AudioHandler.listen_and_transcribe()` (Microphone -> Groq Whisper API).
   - Handles email human-in-the-loop verbal confirmation flow (`tools.pending_email_draft`).
   - Checks wake word (`"eve"`).
   - Queries `EVAgent.chat(transcription)`.
   - Speaks response via `AudioHandler.speak_text()` (`edge-tts` + `pygame.mixer`).

---

## 6. Capability Integration Blueprint (Requirements R1 - R5)

### R1: Live World & AI News Intelligence System
- **Function**: `fetch_live_news(topic: str = "ai") -> str` in `tools.py`
  - Current state: Google News RSS fetcher via `urllib.request` and `xml.etree.ElementTree`.
  - Enhancements: Add multi-feed aggregation (Google News RSS, TechCrunch AI RSS, HackerNews RSS) with fallback mechanisms.
- **WebSocket Broadcast**: `update_news_ticker()` in `main.py`
  - Periodically fetches headlines, formats ticker string separated by `"  ///  "`, broadcasts `news_ticker` WS event every 120s.
- **Daily Briefing**: `get_daily_briefing() -> str` in `tools.py`
  - Aggregates CPU/RAM metrics, weather condition, battery state, and top 3 headlines.

### R2: Real-Time Web Search Tool
- **Function**: `search_web_realtime(query: str) -> str` in `tools.py`
  - Current state: DuckDuckGo HTML scraper using regex snippet extraction.
  - Enhancements: Handle user queries cleanly, handle HTTP headers and timeouts gracefully, return clear markdown-formatted search snippets. Ensure complete definition in `GROQ_TOOLS` & `AVAILABLE_TOOLS`.

### R3: Autonomous Browser Automation
- **Function**: `automate_browser_workflow(url: str = None, action: str = "open", target: str = None) -> str` in `tools.py`
  - Current state: Native `webbrowser` open + `pyautogui` input/hotkey actions.
  - Enhancements: Expand supported actions (`open`, `fill_form`, `click_apply`, `search_jobs`). Implement robust target handling and error recovery.

### R4: System Performance & Battery Guard
- **Function**: `manage_system_performance(action: str = "check") -> str` in `tools.py`
  - Current state: Reads CPU %, RAM %, Battery %.
  - Enhancements: Alert condition checks (CPU temp > 80°C, battery < 20%), support `clean` action to report/terminate excessive processes.
- **Main Loop Integration**: `background_monitor_loop()` in `main.py`
  - Inspect `cpu_temp` and `battery_pct` every cycle. Send proactive WS alert event (`performance_alert`) when CPU temp > 80°C or battery < 20%.

### R5: Smart File & Downloads Organizer
- **Function**: `organize_downloads_folder() -> str` in `tools.py`
  - Current state: Categorizes `~/Downloads` files into Images, Documents, Audio, Archives, Code.
  - Enhancements: Ensure path resolution works cross-platform, handles permission errors gracefully, and returns detailed counts of organized files. Verify presence in `AVAILABLE_TOOLS` and `GROQ_TOOLS`.

---

## 7. Verification Standards & Test Strategy

To verify backend integrity after any edits:
1. **Import Verification**:
   `python -c "import tools, main, llm_agent, audio_handler, memory_handler; print('All modules imported cleanly')"`
2. **Tool Execution Verification**:
   `python -c "import tools; print(tools.fetch_live_news('ai')); print(tools.search_web_realtime('python news')); print(tools.get_daily_briefing()); print(tools.manage_system_performance('check')); print(tools.organize_downloads_folder())"`
3. **WebSocket & Fast-API Dry Run**:
   `python -c "from main import app; print(app.title)"`
