# EVE HUD Dashboard Survey & Architectural Analysis Report

**Author**: HUD Dashboard UI Explorer (`teamwork_preview_explorer`)  
**Target Path**: `c:\MY AI\dashboard`  
**Date**: August 12, 2026  

---

## Executive Summary

This report presents a thorough investigation of the EVE HUD Dashboard UI structure located at `c:\MY AI\dashboard`, along with its integration points across `main.py`, `audio_handler.py`, `llm_agent.py`, and `tools.py`.

The HUD dashboard is a modern, real-time glassmorphic single-page web app rendered via HTML5, CSS3, Three.js 3D WebGL particle sphere, and standard WebSockets. The dashboard receives live telemetry, weather metrics, local network device blips, terminal feeds, state changes, and live news ticker updates from the FastAPI python backend.

Key recommendations for upcoming UI/UX upgrades include:
1. **Glowing Glass Marquee Ticker Enhancement**: Enhancing `.news-marquee-bar` at the top of the workspace with neon cyan ambient glow, hover pause capability, and WebSocket broadcast synchronization.
2. **Interactive Voice Persona Toggle Chips**: Transforming the static `PERSONA` chip in the header into interactive toggle chips (`JARVIS`, `SCI-FI`, `FRIENDLY`), styled with distinct neon visual accents and connected via WebSocket payload to backend Edge-TTS voice mapping and LLM system prompt persona presets.

---

## 1. Dashboard File & Component Architecture

The dashboard directory (`c:\MY AI\dashboard`) contains 3 core web assets:

| File | Size | Role / Functionality |
|---|---|---|
| `index.html` | ~8.8 KB | DOM structure: Header metrics, News Marquee Bar, 3-Column Main Grid (Telemetry, Weather, 3D Orb, Terminal, Radar), Modal Dialog. |
| `style.css` | ~15.0 KB | Glassmorphism styling (`backdrop-filter: blur(20px)`), dark slate theme, neon color tokens, custom keyframe animations, grid layouts. |
| `script.js` | ~24.3 KB | Client-side controller: WebSocket connection, Web Audio API SFX engine, Three.js 3D orb rendering, 2D Canvas Radar animation, DOM telemetry updates. |

### DOM Structure Breakdown (`index.html`)

1. **Header (`.app-header.glass-card`)** [lines 16-39]
   - Brand logo (`.logo-dot`, `.brand-title`: "EVE").
   - Header metrics container (`.header-metrics`):
     - `LATENCY` (`#stat-latency` - e.g., `420 ms`)
     - `QUERIES` (`#stat-queries` - e.g., `12`)
     - `PERSONA` (`#persona-val` - currently static `JARVIS`)
   - Controls (`.header-controls`):
     - Digital clock (`#digital-clock`)
     - Power Off button (`#btn-shutdown`)

2. **Live News Intelligence Marquee Bar (`.news-marquee-bar.glass-card`)** [lines 42-47]
   - Live badge (`.news-badge`: "LIVE NEWS").
   - Marquee wrapper & scrolling text (`#news-marquee-text.news-marquee-text`).

3. **Main Grid (`.app-main`)** [lines 50-153] — 3-Column Grid (`295px 1fr 280px`):
   - **Left Column (`.col-left`)**:
     - System Telemetry Card (`.panel-card`): CPU Load (`#cpu-val`, `#cpu-bar`), CPU Temp (`#cpu-temp-val`, `#cpu-temp-bar`), RAM (`#ram-val`, `#ram-bar`), Network Rx/Tx (`#net-rx`, `#net-tx`).
     - Google Weather Card (`.weather-card`): Day/City header (`#weather-day-header`), Huge temp display (`#weather-temp`), Weather condition (`#weather-cond`), 7-Column hourly forecast timeline (`#hourly-timeline`).
   - **Center Column (`.col-center`)**:
     - State Pills (`#badge-idle`, `#badge-listening`, `#badge-thinking`, `#badge-speaking`).
     - Freely floating 3D WebGL Neural Orb (`#three-container`, `#ambient-glow`).
     - Spectrum waveform visualizer (`#waveform`).
   - **Right Column (`.col-right`)**:
     - Live Terminal Feed (`#terminal-feed`): User speech, EVE replies, Tool execution logs.
     - Local Network Radar Card (`#radar-canvas`, `#device-list`).

4. **Floating Radar Modal (`#radar-modal`)** [lines 156-170]
   - Node detail view (`#modal-ip`, `#modal-host`, `#modal-ping`, `#btn-ping-device`).

---

## 2. WebSocket Communication & Backend Integration

### Backend Server (`main.py`)
- **FastAPI Server**: Mounts `/dashboard` static directory and serves `/ws` WebSocket route [lines 84-110].
- **ConnectionManager**: Manages active WebSocket clients and provides `broadcast_json(data)` and thread-safe `send_event(event_type, value)` [lines 52-82].
- **Background Tasks**:
  - `background_monitor_loop()` [lines 298-347]: Emits `telemetry` every 2s, `weather` every 5m, `news_ticker` every 2m, and `network_devices` continuously.
  - `eve_voice_loop()` [lines 350-435]: Emits `state` (`IDLE`, `LISTENING`, `THINKING`, `SPEAKING`), `user_speech`, `eve_speech`, `tool_call`, and `latency`.

### WebSocket Event Payloads Received by `script.js` [lines 627-676]

| Event `type` | Payload Format | Front-End Render Action |
|---|---|---|
| `state` | `{"type":"state","value":"LISTENING"}` | Updates state badges, orb color/speed, ambient glow, plays wake chime. |
| `telemetry` | `{"type":"telemetry","cpu":14.2,"ram":48.1,"cpu_temp":45.0,"rx_kb":12.4,"tx_kb":3.1}` | Interpolates counter values (`animateCounter`), updates bar width percentages. |
| `news_ticker` | `{"type":"news_ticker","value":"1. Headline 1 /// 2. Headline 2"}` | Updates `#news-marquee-text.textContent`. |
| `weather` | `{"type":"weather", "day_header":"...", "temp_c":23, "hourly":[...]}` | Populates weather card and 7-column hourly pills. |
| `network_devices` | `{"type":"network_devices","devices":[{"ip":"192.168.1.1","host":"Gateway"}]}` | Updates radar canvas blips and device list items. |
| `latency` | `{"type":"latency","ms":340,"queries":8}` | Updates header metrics (`#stat-latency`, `#stat-queries`). |
| `user_speech` | `{"type":"user_speech","value":"..."}` | Appends user speech line to `#terminal-feed`. |
| `eve_speech` | `{"type":"eve_speech","value":"..."}` | Appends assistant response line to `#terminal-feed`. |
| `tool_call` | `{"type":"tool_call","value":"fetch_live_news"}` | Appends tool log to feed, plays audio tool chime. |

---

## 3. News Marquee Ticker: Analysis & Integration Design

### Current State
The marquee ticker container already exists in `index.html` (lines 42-47) and is styled in `style.css` (lines 161-202). In `main.py` (lines 245-254), `update_news_ticker()` fetches news via `tools.fetch_live_news("ai")` and broadcasts JSON `{"type": "news_ticker", "value": cached_news_ticker}`. In `script.js` (lines 655-656), `ws.onmessage` updates `#news-marquee-text.textContent`.

### Recommended Enhancements for Glowing Glass Marquee Ticker

1. **Enhanced Glassmorphic Glowing CSS (`style.css`)**:
   ```css
   .news-marquee-bar {
       display: flex;
       align-items: center;
       padding: 3px 14px;
       gap: 12px;
       overflow: hidden;
       height: 28px;
       border-radius: 8px;
       background: rgba(15, 23, 42, 0.65);
       border: 1px solid rgba(0, 255, 204, 0.25);
       box-shadow: 0 0 15px rgba(0, 255, 204, 0.12), inset 0 0 10px rgba(0, 255, 204, 0.05);
       backdrop-filter: blur(20px);
   }

   .news-badge {
       font-size: 0.58rem;
       font-weight: 700;
       color: #00ffcc;
       background: rgba(0, 255, 204, 0.15);
       border: 1px solid #00ffcc;
       padding: 2px 7px;
       border-radius: 4px;
       white-space: nowrap;
       letter-spacing: 1.5px;
       box-shadow: 0 0 8px rgba(0, 255, 204, 0.4);
   }

   .news-marquee-wrapper:hover .news-marquee-text {
       animation-play-state: paused;
       cursor: pointer;
   }
   ```

2. **Parsing & Dynamic Continuous Animation Reset (`script.js`)**:
   ```javascript
   else if (data.type === 'news_ticker' && newsMarqueeText) {
       const tickerContent = typeof data.value === 'string' ? data.value : (data.value && data.value.value ? data.value.value : '');
       newsMarqueeText.textContent = tickerContent;
       // Reflow animation to prevent jumpiness on update
       newsMarqueeText.style.animation = 'none';
       newsMarqueeText.offsetHeight; // trigger DOM reflow
       newsMarqueeText.style.animation = 'scrollNews 30s linear infinite';
   }
   ```

---

## 4. Voice Persona Toggle Chips: Analysis & Integration Design

### Current State
In `index.html` (lines 30-33), persona is shown as a static metric chip:
```html
<div class="metric-chip">
    <span class="chip-label">PERSONA</span>
    <span id="persona-val" class="chip-val blue">JARVIS</span>
</div>
```
There are no click handlers or backend voice switching handlers connected to this metric chip yet.

### Upgrade Specifications: Voice Persona Toggle Chips

The requirement calls for 3 persona presets:
1. **JARVIS**: Calm, authoritative, highly competent British AI assistant.
   - **TTS Voice**: `en-GB-RyanNeural` (or `en-US-ChristopherNeural`).
   - **Color Theme**: Neon Cyan / Royal Blue (`#3b82f6`).
   - **System Prompt Accent**: Concise, formal, system diagnostic tone.
2. **SCI-FI**: Futuristic, tactical, cyberpunk synthetic AI persona.
   - **TTS Voice**: `en-US-GuyNeural` (or `en-US-SteffanNeural`).
   - **Color Theme**: Glowing Purple / Magenta (`#b026ff`).
   - **System Prompt Accent**: Tactical status report phrasing.
3. **FRIENDLY**: Warm, cheerful, conversational AI companion.
   - **TTS Voice**: `en-US-AvaNeural` (or `en-US-EmmaNeural`).
   - **Color Theme**: Emerald Green (`#10b981`).
   - **System Prompt Accent**: Empathetic, supportive, conversational.

---

### Implementation Plan for Voice Persona Control

#### A. DOM Modification (`index.html`)
Replace the static `PERSONA` metric chip in `.header-metrics` with an interactive toggle group:

```html
<div class="persona-chip-group">
    <span class="chip-label">VOICE PERSONA</span>
    <div class="persona-toggle-chips">
        <button class="persona-btn active" data-persona="JARVIS">JARVIS</button>
        <button class="persona-btn" data-persona="SCI-FI">SCI-FI</button>
        <button class="persona-btn" data-persona="FRIENDLY">FRIENDLY</button>
    </div>
</div>
```

#### B. CSS Styling (`style.css`)
```css
.persona-chip-group {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 3px;
}

.persona-toggle-chips {
    display: flex;
    gap: 4px;
    background: rgba(255, 255, 255, 0.03);
    padding: 2px 4px;
    border-radius: 8px;
    border: 1px solid var(--card-border);
}

.persona-btn {
    background: transparent;
    border: 1px solid transparent;
    color: var(--text-grey);
    font-size: 0.62rem;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 6px;
    cursor: pointer;
    letter-spacing: 0.5px;
    transition: all 0.25s ease;
}

.persona-btn:hover {
    color: var(--text-white);
    background: rgba(255, 255, 255, 0.06);
}

/* Active Persona Neon Variations */
.persona-btn.active[data-persona="JARVIS"] {
    color: #3b82f6;
    background: rgba(59, 130, 246, 0.15);
    border-color: #3b82f6;
    box-shadow: 0 0 10px rgba(59, 130, 246, 0.3);
}

.persona-btn.active[data-persona="SCI-FI"] {
    color: #b026ff;
    background: rgba(176, 38, 255, 0.15);
    border-color: #b026ff;
    box-shadow: 0 0 10px rgba(176, 38, 255, 0.3);
}

.persona-btn.active[data-persona="FRIENDLY"] {
    color: #10b981;
    background: rgba(16, 185, 129, 0.15);
    border-color: #10b981;
    box-shadow: 0 0 10px rgba(16, 185, 129, 0.3);
}
```

#### C. Client-Side Wireup (`script.js`)
Add click event handlers to emit persona updates over WebSocket and handle server persona confirmations:

```javascript
// Persona Chip Event Listeners
const personaBtns = document.querySelectorAll('.persona-btn');
personaBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const persona = btn.getAttribute('data-persona');
        updatePersonaUI(persona);
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ action: 'set_persona', persona: persona }));
        }
    });
});

function updatePersonaUI(personaName) {
    personaBtns.forEach(btn => {
        if (btn.getAttribute('data-persona') === personaName) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}
```

#### D. Backend Backend Dispatcher (`main.py`, `audio_handler.py`, `llm_agent.py`)

1. **`audio_handler.py` Modifications**:
   - Add persona voice mapping dictionary:
     ```python
     PERSONA_VOICES = {
         "JARVIS": "en-GB-RyanNeural",
         "SCI-FI": "en-US-GuyNeural",
         "FRIENDLY": "en-US-AvaNeural"
     }
     self.current_persona = "JARVIS"
     ```
   - In `speak_text(text, voice=None)`: default `voice` to `PERSONA_VOICES.get(self.current_persona, "en-GB-RyanNeural")`.

2. **`llm_agent.py` Modifications**:
   - Store system prompt templates per persona:
     ```python
     PERSONA_PROMPTS = {
         "JARVIS": "You are Eve operating in JARVIS mode: calm, concise, highly analytical, formal British AI assistant tone...",
         "SCI-FI": "You are Eve operating in SCI-FI mode: tactical, futuristic, sleek cyberpunk AI operating voice...",
         "FRIENDLY": "You are Eve operating in FRIENDLY mode: warm, encouraging, conversational AI companion..."
     }
     ```
   - Add method `set_persona(persona_name)` to dynamically update `self.system_prompt` and refresh `self.conversation_history[0]`.

3. **`main.py` WebSocket Handler**:
   In `websocket_endpoint` [lines 97-107]:
   ```python
   elif payload.get("action") == "set_persona":
       persona = payload.get("persona", "JARVIS").upper()
       logger.info(f"Switching voice persona to: {persona}")
       if hasattr(audio_handler, "current_persona"):
           audio_handler.current_persona = persona
       if hasattr(agent, "set_persona"):
           agent.set_persona(persona)
       manager.send_event("system", {"value": f"Voice Persona set to {persona}"})
       manager.send_event("persona_updated", {"persona": persona})
   ```

---

## 5. Verification Plan

1. **HTML & CSS Linting / Inspection**:
   - Ensure grid dimensions (`295px 1fr 280px`) remain responsive without scrollbars on standard 1080p and laptop screens (1280x780 pywebview).
2. **WebSocket Message Validation**:
   - Verify `news_ticker` payload broadcasts correctly without breaking ticker scroll.
   - Verify `set_persona` payload triggers backend persona change and TTS voice updates.
3. **TTS Audio Playback Verification**:
   - Test `speak_text()` with each of the three voice parameters (`en-GB-RyanNeural`, `en-US-GuyNeural`, `en-US-AvaNeural`).

---

**Report Conclusion**: The existing HUD dashboard architecture is exceptionally clean and well-structured. Implementing the glowing glass marquee ticker and the interactive voice persona toggle chips requires minimal non-breaking additions across HTML, CSS, JS, and Python WebSocket handlers.
