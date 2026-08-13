# Project: EVE Advanced Intelligence Suite

## Architecture
- `tools.py`: System tools, RSS news parser, DuckDuckGo search scraper, browser automation, performance monitoring, downloads organizer. Tool schemas (`GROQ_TOOLS`) and registry (`AVAILABLE_TOOLS`).
- `main.py`: FastAPI server, WebSocket manager (`ConnectionManager`), background telemetry & news ticker monitor loop, WebSocket `/ws` action dispatcher (`set_persona`, `get_weather`, etc.).
- `llm_agent.py`: `EVAgent` class, Groq API client, prompt persona switching (`set_persona_prompt`).
- `audio_handler.py`: `AudioHandler` class, Edge-TTS speech generation, voice selection (`set_voice`).
- `dashboard/`: HUD glassmorphic frontend (`index.html`, `style.css`, `script.js`). Glowing glass marquee news ticker, header voice persona toggle chips.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | RSS Live News Fetcher | `fetch_live_news(topic)` retrieves RSS headlines | M1 | ORIGINAL_REQUEST R1 |
| 2 | Daily Briefing Summary | `get_daily_briefing()` aggregates system metrics, weather, and AI news | M1 | ORIGINAL_REQUEST R1 |
| 3 | Real-Time Web Search | `search_web_realtime(query)` scrapes DuckDuckGo POST for live results | M1 | ORIGINAL_REQUEST R2 |
| 4 | Autonomous Browser Workflow | `automate_browser_workflow(url, action, target)` navigates, fills forms, clicks submit | M1 | ORIGINAL_REQUEST R3 |
| 5 | System Performance Guard | `manage_system_performance(action)` monitors CPU/RAM/Battery | M1 | ORIGINAL_REQUEST R4 |
| 6 | Smart Downloads Organizer | `organize_downloads_folder()` categorizes downloads into subfolders | M1 | ORIGINAL_REQUEST R5 |
| 7 | WebSocket News Broadcast | `update_news_ticker()` broadcasts ticker text over `/ws` | M2 | ORIGINAL_REQUEST R1 |
| 8 | Performance Telemetry Guard | `background_monitor_loop()` sends alerts on CPU temp > 80°C or battery < 20% | M2 | ORIGINAL_REQUEST R4 |
| 9 | Voice & Persona Switcher | Backend handler for `set_persona` action in `main.py`, `audio_handler.py`, and `llm_agent.py` | M2 | ORIGINAL_REQUEST R6 |
| 10 | Glowing Glass Marquee Ticker UI | Top HUD marquee bar (`.news-marquee-bar`) with cyan glow & reflow | M3 | ORIGINAL_REQUEST R6 |
| 11 | Voice Persona Toggle Chips UI | Interactive header chips (Jarvis / Sci-Fi / Friendly) sending WS payloads | M3 | ORIGINAL_REQUEST R6 |
| 12 | 100% E2E Test Suite Pass | Verification of all capabilities against test suite & adversarial hardening | M4 | Acceptance Criteria |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Intelligence Tools Module | `tools.py` tool functions & schema definitions | none | PLANNED |
| M2 | Server Engine & Persona Backend | `main.py`, `llm_agent.py`, `audio_handler.py` WebSocket & persona handlers | M1 | PLANNED |
| M3 | HUD Dashboard Frontend UI | `dashboard/index.html`, `dashboard/style.css`, `dashboard/script.js` | M2 | PLANNED |
| M4 | Final Milestone (E2E & Hardening) | Pass E2E test suite (Tiers 1-4) & Adversarial Hardening (Tier 5) | M1, M2, M3, E2E Track | PLANNED |

## Interface Contracts
### `tools.py` ↔ `llm_agent.py` / `main.py`
- `fetch_live_news(topic: str = "ai") -> str`
- `get_daily_briefing() -> str`
- `search_web_realtime(query: str) -> str`
- `automate_browser_workflow(url: str = None, action: str = "open", target: str = None) -> str`
- `manage_system_performance(action: str = "check") -> str`
- `organize_downloads_folder() -> str`

### `main.py` ↔ `dashboard/script.js` WebSocket (`ws://localhost:8000/ws`)
- Outgoing payload: `{"type": "news_ticker", "value": "<headline1>  ///  <headline2>..."}`
- Outgoing payload: `{"type": "performance_alert", "level": "warning", "message": "..."}`
- Incoming payload: `{"action": "set_persona", "persona": "Jarvis" | "Sci-Fi" | "Friendly"}`

### `main.py` ↔ `audio_handler.py` & `llm_agent.py`
- `audio_handler.set_voice(voice_id: str)`: `en-GB-RyanNeural` (Jarvis), `en-US-GuyNeural` (Sci-Fi), `en-US-AvaNeural` (Friendly)
- `llm_agent.set_persona_prompt(persona_name: str)`: System prompt tone configuration

## Code Layout
- `c:\MY AI\tools.py` — Intelligence tools & Groq schemas
- `c:\MY AI\main.py` — Server engine & WebSocket manager
- `c:\MY AI\llm_agent.py` — Groq LLM agent & prompt management
- `c:\MY AI\audio_handler.py` — Audio recording, Whisper STT & Edge-TTS engine
- `c:\MY AI\memory_handler.py` — Drive/local memory storage
- `c:\MY AI\dashboard\index.html` — Glassmorphic single page dashboard
- `c:\MY AI\dashboard\style.css` — CSS styling & animations
- `c:\MY AI\dashboard\script.js` — Client side WebSocket & UI interactions
- `c:\MY AI\tests\` — E2E Test Suite (managed by E2E Testing Track)
