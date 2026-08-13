# EVE — Advanced Synthetic Intelligence & System Documentation
> **Live Project Changelog & Architecture Reference Document**  
> *Last Updated: August 13, 2026*

---

## 📌 Executive Summary

**EVE** (Environmental Voice Entity) is a state-of-the-art, self-evolving, hands-free AI Desktop Assistant and Synthetic Intelligence suite built with **Python**, **FastAPI**, **WebSockets**, **Google Gemini 2.5**, and a sleek **Dark Glassmorphic WebGL HUD Interface**.

This document serves as a persistent, date-stamped log of all features implemented, bugs fixed, tools integrated, and architectural milestones achieved throughout development.

---

## 🗓️ Chronological Development Log & Milestones

### 📅 August 11, 2026 — Core Architecture & HUD Foundation
- **FastAPI & WebSocket Server (`main.py`)**: Established async backend serving static dashboard files and handling real-time bi-directional telemetry streaming.
- **Dark Glassmorphic HUD Interface (`dashboard/`)**: Developed HTML5/CSS3 interface featuring ambient status pulses, system telemetry bars, live terminal feed, and Google weather card.
- **Three.js 3D WebGL Audio Orb (`script.js`)**: Rendered interactive 1,200-particle sphere with color states (`IDLE` blue, `LISTENING` cyan, `THINKING` purple, `SPEAKING` green).
- **Hands-Free Speech Engine (`audio_handler.py`)**: Integrated SpeechRecognition with Groq Whisper-large-v3 and Edge-TTS voice output with barge-in speech interruption.
- **System Telemetry Monitor**: Implemented CPU load, RAM usage, CPU temperature (WMI/OpenHardwareMonitor), and network I/O tracking via `psutil`.

---

### 📅 August 12, 2026 — Advanced Automations, Upgrades & Fixes

#### 1. Phase 1 Upgrades
- **Persistent Conversation Memory**: Implemented history restoration and automatic saving in `memory/history.json` with a rolling window of 50 interactions (100 messages).
- **Multi-Monitor Display Detection**: Integrated `screeninfo` to automatically center native `pywebview` window on primary monitor.
- **Proactive Health Monitor**: Added background thread monitoring CPU temperature (>80°C) and battery level (<20% unplugged) with 5-minute alert cooldowns.

#### 2. Phase 2 Upgrades
- **Passive Always-On Wake Word Engine**: Integrated `pvporcupine` for keyword detection ("bumblebee", "porcupine", "jarvis").
- **Real-Time Orb Lip-Syncing**: Developed 50ms chunk RMS audio amplitude calculation during TTS playback, streaming `speaking_amplitude` WebSocket events at 20Hz.
- **Responsive HUD Layout**: Added `@media` breakpoint queries for tablet and mobile viewports.

#### 3. Phase 3 Upgrades
- **Playwright Web Automation (`automate_browser_workflow`)**: Implemented headless browser control for web page scraping, navigation, and form filling.
- **Real SMTP Email Sending (`send_email_gmail`)**: Integrated `smtplib` and `EmailMessage` for real email dispatch.
- **Local JSON Calendar Integration (`check_schedule`)**: Built schedule manager reading/writing `memory/calendar.json`.
- **Real-Time Web Search (`search_web_realtime`)**: Integrated SerpAPI with fallback to DuckDuckGo scraping.

#### 4. Critical Fixes & Emergency Overhauls
- **Groq API `annotations` Key Sanitization**: Built payload cleaner in `llm_agent.py` stripping unsupported keys to prevent HTTP 400 rejection errors.
- **News Ticker Removal**: Stripped live news ticker to reduce CPU/network overhead and reclaim vertical viewport height.
- **Audio Loop State Machine Refactoring**: Fixed PyAudio stream locks by enforcing strict state flow (Step A: Passive Wait -> Step B: Record ONE command -> Step C: Transcribe -> Step D: Reset).
- **Whisper Hallucination Filter**: Implemented `is_hallucination()` blocking static noise artifacts ("thank you", "subscribe", "undertekster", etc.).
- **Microphone Sensitivity**: Set `energy_threshold = 600` for noise rejection.
- **UI Layout Overhaul**: Rebalanced flex heights and compacted weather timeline pills to prevent panel clipping.

---

### 📅 August 13, 2026 — Supreme Upgrades & Self-Evolution

#### 1. Self-Evolution Engine (`tools.py` & `llm_agent.py`)
- **`modify_system_code`**: Added AST syntax checking (`ast.parse()`) for Python files before writing to disk, and automatic timestamped backups saved to `memory/backups/{filename}_{timestamp}.bak`.
- **`reboot_system`**: Implemented graceful process restart via `os.execl(sys.executable, sys.executable, *sys.argv)`.

#### 2. LLM Engine Upgrade to Google Gemini 2.5 & Chain of Thought
- **Google GenAI SDK Integration**: Upgraded core LLM engine to **`gemini-2.5-pro`** using `google-genai` client.
- **Mandatory Chain of Thought (`<thought_process>`)**: Added `[MANDATORY CHAIN OF THOUGHT DIRECTIVE]` instructing EVE to reason inside `<thought_process>` XML tags.
- **Invisible Thought Stripping**: Added `strip_thought_process()` to log reasoning internally while presenting clean text in the UI/terminal.
- **Function Calling Conversion**: Mapped Python functions directly to Gemini's `types.GenerateContentConfig(tools=...)`.

#### 3. Taskbar Clearance & Layout Finalization
- **Network Radar Removal**: Removed Network Radar to allow Live Terminal feed to expand to 100% column height.
- **Compact Window & 40px Margin**: Adjusted native window size to `1150x620` with `avail_h` taskbar offset detection, and added a fixed 40px bottom margin inside `.app-container`.

---

## 🛠️ Complete Tools & Capabilities Inventory

| Tool Name | Module | Description |
| :--- | :--- | :--- |
| `modify_system_code` | `tools.py` | Modifies Python/UI source code with AST syntax validation and automatic timestamped backups. |
| `reboot_system` | `tools.py` | Restarts the main Python process to load newly evolved code into active memory. |
| `search_web_realtime` | `tools.py` | Performs live web searches via SerpAPI / DuckDuckGo. |
| `automate_browser_workflow` | `tools.py` | Controls Playwright headless Chromium for web scraping, form filling, and navigation. |
| `send_email_gmail` | `tools.py` | Sends emails via SMTP using configured Gmail credentials. |
| `check_schedule` | `tools.py` | Reads, adds, and deletes calendar events stored in `memory/calendar.json`. |
| `manage_system_performance` | `tools.py` | Checks telemetry, cleans temporary files, lists top processes, or kills a process. |
| `organize_downloads_folder` | `tools.py` | Automatically categorizes and moves files in Downloads into classified subfolders. |
| `execute_system_command` | `tools.py` | Executes shell, CMD, or PowerShell commands. |
| `automate_keyboard_mouse` | `tools.py` | Performs PyAutoGUI key presses, text typing, or mouse clicks. |
| `manage_file_system` | `tools.py` | Reads, writes, creates directories, or lists files across the OS. |
| `capture_and_analyze_screen` | `tools.py` | Captures desktop screenshot and analyzes visual content using Multimodal Vision AI. |
| `manage_media_volume` | `tools.py` | Controls system volume (up/down/mute) and media playback (play/pause/next/prev). |
| `save_memory` / `search_memory` | `tools.py` | Stores and retrieves persistent long-term notes via `MemoryHandler`. |
| `get_daily_briefing` | `tools.py` | Generates a 60-second summary of telemetry, weather, and schedule. |
| `get_current_time` | `tools.py` | Returns formatted current date and time. |
| `open_application` / `open_calculator` | `tools.py` | Launches desktop software (Chrome, Notepad, Calculator) or opens URLs. |

---

## 🧰 Full Technology Stack

### Backend & Core Logic
- **Language**: Python 3.13
- **LLM Engine**: Google GenAI SDK (`google-genai`), Model: `gemini-2.5-pro`
- **Web Framework**: FastAPI & Uvicorn
- **WebSockets**: Real-time bi-directional JSON streaming (`ConnectionManager`)
- **Native GUI Window**: `pywebview` & `screeninfo`

### Audio & Speech Processing
- **Wake Word Detection**: `pvporcupine` (Keywords: "bumblebee", "porcupine", "jarvis")
- **Speech-to-Text**: SpeechRecognition + Groq Whisper (`whisper-large-v3`)
- **Text-to-Speech**: `edge-tts` (Voice: `en-US-AvaNeural`)
- **Audio Amplitude Lip-Syncing**: `soundfile` & `numpy` RMS chunk calculation
- **Audio Playback**: `pygame.mixer`

### Frontend Dashboard
- **Structure & Logic**: HTML5, Vanilla JavaScript (ES6+), WebSockets API
- **Styling**: Vanilla CSS3 (CSS Variables, Flexbox, CSS Grid, Glassmorphism, Backdrop Filters)
- **3D Graphics**: Three.js WebGL Particle System (1,200 particles)

### Testing & Verification
- **Test Framework**: `pytest` (97 Automated Tests passing — 100% pass rate)

---

## 📈 Quality & Testing Metrics

- **Total Test Suite**: `97 passed, 0 failed` across unit and integration tests in `tests/`.
- **Test Coverage Areas**: Calendar JSON CRUD, SMTP Email Dispatch, Playwright Browser Scraping, SerpAPI Search, System Health Monitor, Audio Loop Flow Controls, Hallucination Filter, Self-Evolution AST Validation, and Gemini Chain of Thought parsing.
