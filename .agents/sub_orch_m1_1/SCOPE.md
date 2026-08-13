# Scope: Milestone M1 — Intelligence Tools Module

## Architecture
- Implementation target: `tools.py` in project root (`c:\MY AI\tools.py`)
- Standardized tool return format and integration with function execution dispatcher.
- Function registry: `AVAILABLE_TOOLS` dictionary.
- Schema registry: `GROQ_TOOLS` list.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | R1: fetch_live_news & get_daily_briefing | Live news fetcher by topic & daily summary briefing | M1 | ORIGINAL_REQUEST.md |
| 2 | R2: search_web_realtime | Realtime Web search using DuckDuckGo POST scraper | M1 | ORIGINAL_REQUEST.md |
| 3 | R3: automate_browser_workflow | Browser automation worker (url, action, target) | M1 | ORIGINAL_REQUEST.md |
| 4 | R4: manage_system_performance | System performance monitor and manager | M1 | ORIGINAL_REQUEST.md |
| 5 | R5: organize_downloads_folder | Downloads folder organizer by file type | M1 | ORIGINAL_REQUEST.md |
| 6 | Registry Update | Register tools in AVAILABLE_TOOLS and GROQ_TOOLS | M1 | ORIGINAL_REQUEST.md |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | M1 | Intelligence Tools Module in tools.py | none | IN_PROGRESS |

## Interface Contracts
### tools.py Internal Contracts
- `fetch_live_news(topic: str)`
- `get_daily_briefing()`
- `search_web_realtime(query: str)`
- `automate_browser_workflow(url: str, action: str, target: str)`
- `manage_system_performance(action: str)`
- `organize_downloads_folder()`
- `AVAILABLE_TOOLS`: dict mapping tool name string to function.
- `GROQ_TOOLS`: list of tool schema dicts.
