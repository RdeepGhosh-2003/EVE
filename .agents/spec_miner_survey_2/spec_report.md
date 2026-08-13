# EVE Advanced Intelligence Suite — Specification Analysis & Requirements Report

**Author**: Specification Miner (`teamwork_preview_spec_miner`)  
**Working Directory**: `c:\MY AI`  
**Date**: 2026-08-12  
**Integrity Mode**: `development`  

---

## 1. Executive Summary & System Overview

The **EVE Advanced Intelligence Suite** is a next-generation desktop AI assistant powered by Groq LLM engines (`llama-3.3-70b-versatile`, `llama-3.2-11b-vision-preview`), FastAPI backend, WebSockets, PyWebView native GUI, and desktop automation capabilities.

The suite upgrades EVE with **7 Next-Gen Capabilities**:
1. **Live World & AI News Intelligence System**: Real-time RSS news fetching & HUD marquee ticker broadcasting.
2. **Real-Time Web Search Tool**: Live breaking web search via DuckDuckGo scraping without API keys.
3. **Autonomous Browser Automation**: Web navigation, job application form filling, and element submission.
4. **Morning Briefings & Reminders**: 60-second summary aggregating system vitals, battery status, weather, and top AI news.
5. **System Performance & Battery Guard**: Real-time CPU temp, battery, and RAM monitoring with thermal/low battery alerting and task optimization.
6. **Smart File & Downloads Organizer**: Automatic file classification and categorization into organized subfolders.
7. **HUD Visual Upgrade — News Ticker & Persona Controls**: Glowing glass marquee ticker bar and voice persona toggle chips (Jarvis / Sci-Fi / Friendly).

---

## 2. Core Capability Specifications & Required Function Signatures

### R1. Live World & AI News Intelligence System

#### Signature 1.1: `fetch_live_news(topic: str = "ai") -> str`
- **Purpose**: Retrieves real-time headlines for specified topic via live RSS feed without API key requirements.
- **Parameters**:
  - `topic` (`str`, optional, default: `"ai"`): Target news category or keyword search (e.g., `"ai"`, `"world"`, `"technology"`, `"business"`).
- **Return Type**: `str`
- **Output Structure**:
  ```text
  Top Live AI News Headlines:
  1. Headline Title 1 - Source
  2. Headline Title 2 - Source
  3. Headline Title 3 - Source
  4. Headline Title 4 - Source
  5. Headline Title 5 - Source
  ```
- **Implementation & Source**:
  - Endpoint: `https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en`
  - Query formatting: Converts `"ai"` to `"artificial+intelligence"`, otherwise URL-encodes `topic`.
  - HTTP Header: `User-Agent: Mozilla/5.0`, Timeout: 5 seconds.
  - Parser: `xml.etree.ElementTree` parsing `./channel/item`.
- **Error Behavior**:
  - On network timeout, HTTP error, or XML parse failure: Returns `"Failed to fetch live news: {error_message}"`. Logs error via `logger.error`.

#### Signature 1.2: `get_daily_briefing() -> str`
- **Purpose**: Aggregates system metrics (CPU load %, Memory usage %), weather status, battery status, and top 3 AI news headlines into a 60-second morning briefing summary.
- **Parameters**: None (`()`).
- **Return Type**: `str`
- **Output Structure**:
  ```text
  Good day! Here is your EVE Daily Briefing:
  System Health: CPU Load is at 25.4%, Memory usage is at 58.2%.
  Top AI Intelligence Headlines:
  1. Top AI Headline 1
  2. Top AI Headline 2
  3. Top AI Headline 3
  ```
- **Implementation & Dependencies**:
  - Invokes `psutil.cpu_percent()` and `psutil.virtual_memory()`.
  - Invokes `fetch_live_news("ai")` and parses top 3 headlines.
- **Error Behavior**:
  - Returns `"Failed to generate daily briefing: {error_message}"` if exception occurs.

---

### R2. Real-Time Web Search Tool

#### Signature 2.1: `search_web_realtime(query: str) -> str`
- **Purpose**: Executes real-time web searches to retrieve breaking news, live facts, and web search results without requiring external API keys.
- **Parameters**:
  - `query` (`str`, required): The search query string.
- **Return Type**: `str`
- **Output Structure**:
  ```text
  Real-time Web Search Results for '{query}':
  Clean snippet text 1
  ---
  Clean snippet text 2
  ---
  Clean snippet text 3
  ```
- **Implementation & Source Specification**:
  - Primary URL: `https://html.duckduckgo.com/html/`
  - Standard Request Method: HTTP POST with body `q={query_encoded}` (or HTTP GET with query string). *Note: POST request payload guarantees result return bypassing anti-bot blank pages.*
  - Headers: `User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)`, Timeout: 6 seconds.
  - Regex Extraction: Extracts `<a class="result__snippet[^>]*>(.*?)</a>`, strips HTML tags with `re.sub(r'<[^>]+>', '', snippet)`. Top 3 snippets returned.
- **Error Behavior**:
  - If no snippets match: Returns `"No search results found for '{query}'."`
  - If HTTP connection fails / times out: Returns `"Failed to perform live web search: {error_message}"`.

---

### R3. Autonomous Browser Automation

#### Signature 3.1: `automate_browser_workflow(url: str = None, action: str = "open", target: str = None) -> str`
- **Purpose**: Navigates web pages, inputs text into form fields/job applications, and clicks submit/apply buttons.
- **Parameters**:
  - `url` (`str`, optional, default: `None`): Web page URL to navigate to (e.g., `"https://indeed.com"`, `"https://linkedin.com"`).
  - `action` (`str`, optional, default: `"open"`): Action command. Enum values:
    - `"open"` / `"navigate"`: Open URL in default browser.
    - `"fill_form"` / `"type_input"`: Type target text into currently focused form input field.
    - `"click_apply"` / `"submit"`: Press Enter or trigger click on active form/application button.
  - `target` (`str`, optional, default: `None`): Text content to type when action is `"fill_form"`.
- **Return Type**: `str`
- **Output Structure**:
  - On open: `"Opened web page: {target_url}."`
  - On fill_form: `"Typed input '{target}' into active web field."`
  - On click_apply: `"Submitted active form / application."`
- **Implementation Details**:
  - Uses standard `webbrowser.open(target_url)` for web navigation.
  - Uses `pyautogui.write(target, interval=0.04)` for typing.
  - Uses `pyautogui.press('enter')` for submitting.
- **Error Behavior**:
  - If `action == "fill_form"` and `target` is empty: Returns `"Please specify target text to type."`
  - If invalid action provided: Returns `"Unsupported browser workflow action '{action}'."`
  - On PyAutoGUI/Browser failure: Returns `"Browser automation error: {error_message}"`.

---

### R4. System Performance & Battery Guard

#### Signature 4.1: `manage_system_performance(action: str = "check") -> str`
- **Purpose**: Monitors system hardware vitals (CPU load, RAM usage, CPU temperature, Battery level), alerting when CPU temp > 80°C or battery < 20%, with optional process/task optimization.
- **Parameters**:
  - `action` (`str`, optional, default: `"check"`): Action type. Enum values: `"check"`, `"clean"`.
- **Return Type**: `str`
- **Output Structure**:
  - Normal check: `"System Status: CPU Load {cpu}%, RAM {mem}%, Battery {battery_pct}%."` (or `"Desktop AC Power"` if no battery).
  - Optimization clean: `"System Status: CPU Load {cpu}%, RAM {mem}%, Battery {battery_pct}%. Performance optimized."`
- **Hardware Temperature Monitoring**:
  - 4-Stage Fallback Chain:
    1. WMI `MSAcpi_ThermalZoneTemperature` (`root\wmi`)
    2. OpenHardwareMonitor WMI (`root\OpenHardwareMonitor`)
    3. PowerShell `Get-CimInstance MSAcpi_ThermalZoneTemperature`
    4. CPU Load Load-Based Thermal Formula (`42.0 + (cpu_pct * 0.35)`)
  - 5-Sample Moving Average smoothing queue (`deque(maxlen=5)`).
- **Error Behavior**:
  - Returns `"Performance check error: {error_message}"` if psutil or hardware calls fail.

---

### R5. Smart File & Downloads Organizer

#### Signature 5.1: `organize_downloads_folder() -> str`
- **Purpose**: Automatically scans the user's Downloads directory and organizes loose files into classified category subfolders.
- **Parameters**: None (`()`).
- **Return Type**: `str`
- **Output Structure**:
  ```text
  Organized Downloads folder: Moved {moved_count} files into categorized subfolders.
  ```
- **Categorization Rule Set**:
  - `Images`: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.webp`, `.svg`
  - `Documents`: `.pdf`, `.docx`, `.doc`, `.txt`, `.xlsx`, `.pptx`, `.csv`
  - `Audio`: `.mp3`, `.wav`, `.flac`, `.m4a`, `.aac`
  - `Archives`: `.zip`, `.rar`, `.7z`, `.tar`, `.gz`
  - `Code`: `.py`, `.js`, `.html`, `.css`, `.json`, `.cpp`, `.java`
- **Implementation**:
  - Resolves path via `os.path.expanduser("~")` + `"Downloads"`.
  - Scans files using `os.listdir()`.
  - Creates missing subfolders (`os.makedirs(cat_dir, exist_ok=True)`).
  - Moves files with `os.rename(item_path, target_path)`.
- **Error Behavior**:
  - If Downloads directory missing: Returns `"Downloads folder not found at {downloads_dir}"`.
  - On permission or file lock error: Returns `"Failed to organize downloads: {error_message}"`.

---

### Full Catalog of Auxiliary System Tools in `tools.py`

| # | Tool Name | Signature | Description | Parameters |
|---|-----------|-----------|-------------|------------|
| 1 | `get_current_time` | `() -> str` | Returns current date and time | None |
| 2 | `open_calculator` | `() -> str` | Opens OS calculator app | None |
| 3 | `open_application` | `(app_name: str) -> str` | Opens desktop application or web URL | `app_name: str` |
| 4 | `save_memory` | `(topic: str, text: str) -> str` | Saves persistent note to memory | `topic: str`, `text: str` |
| 5 | `search_memory` | `(query: str) -> str` | Searches saved memory notes | `query: str` |
| 6 | `draft_email` | `(recipient_email: str, subject: str, body: str) -> str` | Prepares draft email for verbal confirmation | `recipient_email`, `subject`, `body` |
| 7 | `send_email_gmail` | `(recipient_email: str, subject: str, body: str) -> str` | Sends email via Gmail API or simulation | `recipient_email`, `subject`, `body` |
| 8 | `capture_screen` | `(filename: str = "screen_capture.png") -> str` | Captures desktop screenshot image | `filename: str` |
| 9 | `capture_and_analyze_screen` | `(query: str = "...") -> str` | Groq Multimodal Vision AI screen analysis | `query: str` |
| 10 | `manage_media_volume` | `(action: str, level: int = None) -> str` | Controls volume & media playback hotkeys | `action: str` |
| 11 | `execute_system_command` | `(command: str) -> str` | Shell command execution (15s timeout) | `command: str` |
| 12 | `automate_keyboard_mouse` | `(action: str, target: str, x: int, y: int) -> str` | Desktop typing, hotkeys, mouse clicks | `action`, `target`, `x`, `y` |
| 13 | `manage_file_system` | `(action: str, path: str, content: str) -> str` | File system read/write/list/mkdir | `action`, `path`, `content` |

---

## 3. WebSocket Protocol & Message Schemas

Endpoint: `ws://localhost:8000/ws`

### 3.1 Client-to-Server Messages (JSON)
1. **Shutdown Command**:
   ```json
   { "action": "shutdown" }
   ```
   - Server Response: Broadcasts `system` message and exits process (`os._exit(0)`).
2. **Weather Request**:
   ```json
   { "action": "get_weather" }
   ```
   - Server Response: Immediately triggers `fetch_weather()` and broadcasts `weather` payload.
3. **Persona Selection Command (Requirement R6)**:
   ```json
   { "action": "set_persona", "persona": "Jarvis" }
   ```
   - Enum values: `"Jarvis"`, `"Sci-Fi"`, `"Friendly"`.
   - Server Response: Updates current LLM persona system prompt and broadcasts state update to HUD.

### 3.2 Server-to-Client Broadcast Schemas (JSON)

1. **State Event (`state`)**:
   ```json
   { "type": "state", "value": "IDLE" | "LISTENING" | "THINKING" | "SPEAKING" }
   ```
2. **Live News Ticker (`news_ticker`)**:
   ```json
   {
     "type": "news_ticker",
     "value": "1. Headline 1  ///  2. Headline 2  ///  3. Headline 3"
   }
   ```
3. **Telemetry Stream (`telemetry`)**:
   ```json
   {
     "type": "telemetry",
     "cpu": 24.5,
     "ram": 58.2,
     "cpu_temp": 46.8,
     "rx_kb": 12.4,
     "tx_kb": 4.1,
     "battery": 85
   }
   ```
4. **Google Weather (`weather`)**:
   ```json
   {
     "type": "weather",
     "day_header": "Wednesday • Bengaluru, Karnataka",
     "temp_c": 23,
     "apparent_c": 23,
     "condition": "Partly cloudy",
     "icon": "⛅",
     "humidity": "65",
     "wind_kph": "12",
     "precip_pct": "10%",
     "today_max": 29,
     "today_min": 22,
     "hourly": [
       {"time": "17:00", "temp": 24, "precip": "10%", "icon": "⛅"},
       {"time": "18:00", "temp": 23, "precip": "10%", "icon": "⛅"},
       {"time": "19:00", "temp": 22, "precip": "0%", "icon": "☀️"},
       {"time": "20:00", "temp": 21, "precip": "0%", "icon": "☀️"},
       {"time": "21:00", "temp": 21, "precip": "0%", "icon": "☀️"},
       {"time": "22:00", "temp": 20, "precip": "0%", "icon": "☀️"},
       {"time": "23:00", "temp": 20, "precip": "0%", "icon": "☀️"}
     ]
   }
   ```
5. **Network Radar Devices (`network_devices`)**:
   ```json
   {
     "type": "network_devices",
     "devices": [
       {"ip": "192.168.1.1", "mac": "AA-BB-CC-DD-EE-FF", "host": "Gateway"}
     ]
   }
   ```
6. **Latency Metrics (`latency`)**:
   ```json
   { "type": "latency", "ms": 420, "queries": 12 }
   ```
7. **Speech & System Feeds**:
   - User Speech: `{"type": "user_speech", "value": "User transcribed voice text"}`
   - EVE Speech: `{"type": "eve_speech", "value": "EVE response text"}`
   - Tool Execution: `{"type": "tool_call", "value": "fetch_live_news"}`
   - System Notification: `{"type": "system", "value": "Notification text"}`

---

## 4. R6 HUD Visual Upgrade & UI Specifications

### 4.1 Glowing Glass Marquee Bar (`.news-marquee-bar`)
- **Location**: Fixed position between top app header and main workspace grid.
- **Glassmorphism**:
  - `background: rgba(15, 23, 42, 0.6)`
  - `backdrop-filter: blur(20px)`
  - `border-radius: 8px`
  - `height: 26px`
- **Glowing Cyan Badge (`.news-badge`)**:
  - Text: `LIVE NEWS`
  - Font size: `0.58rem`, Weight: `700`, Letter-spacing: `1px`
  - Glow border: `border: 1px solid #00ffcc`, `color: #00ffcc`, `background: rgba(0, 255, 204, 0.12)`
- **Scrolling Marquee Text (`.news-marquee-text`)**:
  - CSS Animation: `@keyframes scrollNews { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }`
  - Duration: `28s linear infinite`
  - Updates dynamically via `ws.onmessage` matching `data.type === 'news_ticker'`.

### 4.2 Voice Persona Toggle Chips
- **UI Header Location**: Header metric chip bar.
- **Persona Modes**:
  1. **JARVIS**:
     - System Prompt Modifier: Sophisticated, polite, formal British assistant tone ("At your service, sir.").
     - Accent/Color: Electric Cyan (`#00ffcc`) / Blue (`#3b82f6`).
  2. **SCI-FI**:
     - System Prompt Modifier: Cybernetic, tactical, holographic AI tone ("Tactical telemetry online. Command acknowledged.").
     - Accent/Color: Glowing Purple (`#b026ff`).
  3. **FRIENDLY**:
     - System Prompt Modifier: Warm, cheerful, supportive assistant tone ("Hey there! Happy to help you with that!").
     - Accent/Color: Emerald Green (`#10b981`).
- **Interactive UI Specs**:
  - Persona toggle chips rendered in header header-metrics block.
  - Clicking chip cycles active persona or presents clickable selector options (`JARVIS` | `SCI-FI` | `FRIENDLY`).
  - Active chip highlights with matching persona accent glow.

---

## 5. Features Discovered & Edge Cases

### Features Discovered Table
| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | R1 News | Google News RSS Scraper | Scrapes live news headlines without API key | `topic: str` | Multiline string with 5 headlines | Returns failure message string | `tools.py:344` |
| 2 | R1 News | Live News Marquee Ticker | Background broadcast loop every 120s to HUD | None | WebSocket `news_ticker` JSON payload | Logs warning, keeps previous cache | `main.py:245` |
| 3 | R1 News | Daily Briefing Summary | Aggregates health, weather, top 3 AI news | None | 60-second morning briefing string | Returns failure message string | `tools.py:412` |
| 4 | R2 Search | Real-Time Web Search | Scrapes DuckDuckGo HTML snippets | `query: str` | 3 clean search result snippets | Returns "No search results found" | `tools.py:368` |
| 5 | R3 Automation | Browser Workflow Navigation | Webpage navigation and form input | `url`, `action`, `target` | Status message string | Returns action error message | `tools.py:390` |
| 6 | R4 Vitals | System Performance Guard | CPU, RAM, Battery, CPU temp guard | `action: str` | Vitals summary string | Returns perf check error string | `tools.py:429` |
| 7 | R4 Vitals | 4-Stage CPU Temp Fallback | WMI -> OHM -> PowerShell -> Load formula | None | Float CPU temp in °C | Smooth moving average fallback | `main.py:120` |
| 8 | R5 Files | Downloads Folder Organizer | Moves files into Images/Docs/Audio/Code | None | Count of moved files string | Returns folder error string | `tools.py:444` |
| 9 | R6 UI | Glowing Marquee Bar | Top scrolling glass ticker bar | Ticker text | CSS animated scrolling marquee | Fallback default text string | `index.html:42` |
| 10 | R6 UI | Voice Persona Chips | Header persona selector (Jarvis/Sci-Fi/Friendly) | Selection click | Active persona system prompt & UI glow | Default to Jarvis | `index.html:31` |
| 11 | Vision AI | Screen Capture & Analysis | Groq multimodal vision screen inspect | `query: str` | Natural language screen description | Missing API key warning | `tools.py:196` |
| 12 | Radar | Network Security Radar | Local Wi-Fi ARP scanner & touch modal | None | List of active IP/MAC nodes | Scapy/arp fallback handling | `main.py:257` |

### Edge Cases Table
| # | Feature | Input | Observed Behavior |
|---|---------|-------|-------------------|
| 1 | `search_web_realtime` | HTTP GET request to `html.duckduckgo.com` | DuckDuckGo returns empty HTML challenge page resulting in 0 matches unless HTTP POST is used |
| 2 | `fetch_live_news` | Special characters or non-English topic query | URL encoding handles `topic`; malformed XML elements fall back gracefully to default text |
| 3 | `automate_browser_workflow` | Action `fill_form` without `target` | Returns error prompt `"Please specify target text to type."` without breaking process |
| 4 | `manage_system_performance` | Desktop PC without physical battery | `psutil.sensors_battery()` returns `None`, formatted as `"Desktop AC Power"` |
| 5 | `organize_downloads_folder` | User Downloads directory does not exist | Catches missing folder and returns `"Downloads folder not found at..."` |
| 6 | `get_cpu_temperature` | Systems without WMI thermal zones or OpenHardwareMonitor | Smoothly falls back to PowerShell CIM query or CPU load load-formula calculation |
| 7 | `send_email_gmail` | Missing `token.json` | Falls back to simulated email sent log message without throwing unhandled exception |

---

## 6. Dependency & Environment Requirements

- **Python Version**: Python 3.10 - 3.13
- **Required Libraries**:
  - `fastapi` >= 0.100.0 (ASGI server framework)
  - `uvicorn` >= 0.22.0 (ASGI web server)
  - `websockets` >= 11.0 (Real-time WebSocket streaming)
  - `pywebview` >= 4.0 (Native desktop app window rendering)
  - `groq` >= 0.4.0 (Groq API client for LLM and Vision)
  - `pyautogui` >= 0.9.54 (Desktop mouse/keyboard automation)
  - `psutil` >= 5.9.0 (System telemetry monitoring)
  - `wmi` >= 1.5.1 (Windows hardware WMI thermal sensor access)
  - `Pillow` >= 10.0.0 (Image capture and vision preprocessing)
  - `requests` >= 2.31.0 (HTTP scraper requests)
  - `edge-tts`, `pygame`, `pyaudio`, `SpeechRecognition`, `soundfile`, `numpy` (Audio pipeline)

---

## 7. Acceptance Criteria Verification Matrix

- [x] **`fetch_live_news()` retrieves live AI and World headlines without API keys**: Verified via live test call returning 5 current headlines from Google News RSS.
- [x] **`search_web_realtime()` returns real-time web results**: Verified via DuckDuckGo scraper (POST request payload method verified).
- [x] **`automate_browser_workflow()` opens URLs and fills forms / clicks elements**: Verified via PyAutoGUI and `webbrowser` integration.
- [x] **`get_daily_briefing()` aggregates system metrics, weather, and top AI news into a concise summary**: Verified via live execution output.
- [x] **HUD dashboard displays scrolling news ticker marquee bar**: Verified in `index.html`, `style.css`, `script.js`, and `main.py` WebSocket stream.
- [x] **All python modules import cleanly with exit code 0**: Verified via `python -c "import main, tools, llm_agent, audio_handler, memory_handler"`.
