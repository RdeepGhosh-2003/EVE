import sys
import time
import os
import asyncio
import logging
import threading
import subprocess
import urllib.request
import json
import re
import socket
import datetime
from collections import deque
from typing import List
from dotenv import load_dotenv
import psutil

try:
    import wmi
    wmi_obj = wmi.WMI(namespace="root\\wmi")
except Exception:
    wmi_obj = None

try:
    import wmi
    ohm_wmi = wmi.WMI(namespace="root\\OpenHardwareMonitor")
except Exception:
    ohm_wmi = None

load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import uvicorn

from audio_handler import AudioHandler
from llm_agent import EVAgent
import tools

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("EVE")

app = FastAPI(title="EVE")

cached_weather_data = None

cached_telemetry_data = None

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.loop = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")
        if cached_weather_data:
            await websocket.send_json({"type": "weather", **cached_weather_data})
        if cached_telemetry_data:
            await websocket.send_json({"type": "telemetry", **cached_telemetry_data})

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_json(self, data: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(data)
            except Exception:
                self.disconnect(connection)

    def send_event(self, event_type: str, value):
        data = {"type": event_type, "value": value} if isinstance(value, str) else {"type": event_type, **value}
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self.broadcast_json(data), self.loop)

manager = ConnectionManager()

dashboard_dir = os.path.join(os.getcwd(), "dashboard")
app.mount("/dashboard", StaticFiles(directory=dashboard_dir, html=True), name="dashboard")

@app.get("/")
async def root():
    return RedirectResponse(url="/dashboard")

@app.post("/api/shutdown")
async def http_shutdown():
    """HTTP REST endpoint to shut down EVE process when POWER OFF button is clicked."""
    logger.info("Received HTTP shutdown request. Terminating EVE process...")
    manager.send_event("system", {"value": "Shutdown command received via UI button. Powering off EVE..."})
    def _exit():
        time.sleep(0.5)
        os._exit(0)
    threading.Thread(target=_exit, daemon=True).start()
    return {"status": "shutting_down"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            text_data = await websocket.receive_text()
            try:
                payload = json.loads(text_data)
                if payload.get("action") == "shutdown":
                    logger.info("Received WebSocket shutdown request. Exiting...")
                    manager.send_event("system", {"value": "Shutdown command received. Powering off EVE..."})
                    await asyncio.sleep(0.5)
                    os._exit(0)
                elif payload.get("action") == "get_weather":
                    fetch_weather()
                elif payload.get("action") == "set_persona":
                    persona_name = payload.get("persona", "JARVIS")
                    if eve_agent_instance is not None:
                        result = eve_agent_instance.set_persona(persona_name)
                        manager.send_event("persona_changed", {"value": persona_name.upper()})
                        logger.info(f"[WebSocket] {result}")
                    else:
                        logger.warning("[WebSocket] Persona change received but EVE agent not yet initialized.")
            except Exception as ex:
                logger.warning(f"Error handling WebSocket message: {ex}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Wrap tools execution to broadcast tool call events
original_execute_tool = tools.execute_tool
def hud_execute_tool(tool_name: str, tool_args: dict = None) -> str:
    manager.send_event("tool_call", {"value": tool_name})
    return original_execute_tool(tool_name, tool_args)
tools.execute_tool = hud_execute_tool

cpu_temp_history = deque(maxlen=5)

def get_cpu_temperature():
    """Reads hardware CPU temperature via 4-stage Windows fallback & 5-sample Moving Average smoothing."""
    raw_temp = None

    try:
        if wmi_obj:
            zones = wmi_obj.MSAcpi_ThermalZoneTemperature()
            if zones:
                temps = [(z.CurrentTemperature / 10.0) - 273.15 for z in zones]
                valid_temps = [t for t in temps if 10.0 <= t <= 110.0]
                if valid_temps:
                    raw_temp = max(valid_temps)
    except Exception:
        pass

    if raw_temp is None:
        try:
            if ohm_wmi:
                sensors = ohm_wmi.Sensor()
                temps = [s.Value for s in sensors if s.SensorType == 'Temperature' and 'CPU' in s.Name]
                if temps:
                    raw_temp = max(temps)
        except Exception:
            pass

    if raw_temp is None:
        try:
            cmd = 'powershell "Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature | Select-Object -ExpandProperty CurrentTemperature"'
            out = subprocess.check_output(cmd, shell=True, timeout=2).decode('utf-8').strip()
            vals = [float(v) for v in out.split() if v.replace('.', '', 1).isdigit()]
            if vals:
                temps = [(v / 10.0) - 273.15 for v in vals]
                valid_temps = [t for t in temps if 10.0 <= t <= 110.0]
                if valid_temps:
                    raw_temp = max(valid_temps)
        except Exception:
            pass

    if raw_temp is None:
        cpu_pct = psutil.cpu_percent(interval=None) or 0.0
        raw_temp = round(42.0 + (cpu_pct * 0.35), 1)

    if raw_temp is None or not isinstance(raw_temp, (int, float)):
        raw_temp = 42.0

    cpu_temp_history.append(raw_temp)
    smoothed_temp = round(sum(cpu_temp_history) / len(cpu_temp_history), 1)
    return smoothed_temp

WMO_WEATHER_MAP = {
    0: ("Clear sky", "☀️"), 1: ("Mainly clear", "☀️"), 2: ("Partly cloudy", "⛅"), 3: ("Overcast", "☁️"),
    45: ("Foggy", "🌫️"), 48: ("Rime fog", "🌫️"), 51: ("Light drizzle", "🌧️"), 61: ("Slight rain", "🌧️"),
    63: ("Moderate rain", "🌧️"), 80: ("Rain showers", "🌧️"), 95: ("Thunderstorm", "🌩️")
}

def fetch_weather():
    """Fetches live weather for Bengaluru using Open-Meteo API with 7-column hourly timeline."""
    global cached_weather_data
    try:
        url = "https://api.open-meteo.com/v1/forecast?latitude=12.9716&longitude=77.5946&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m&hourly=temperature_2m,precipitation_probability,weather_code&daily=temperature_2m_max,temperature_2m_min&timezone=Asia%2FKolkata"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            curr = data.get('current', {})
            daily = data.get('daily', {})
            hourly = data.get('hourly', {})

            temp_c = round(curr.get('temperature_2m', 23))
            apparent_temp = round(curr.get('apparent_temperature', temp_c))
            humidity = round(curr.get('relative_humidity_2m', 65))
            wind_kph = round(curr.get('wind_speed_10m', 12))
            precip = round(curr.get('precipitation', 0.0), 1)
            code = curr.get('weather_code', 0)

            cond_str, icon_str = WMO_WEATHER_MAP.get(code, ("Partly cloudy", "⛅"))

            max_temps = daily.get('temperature_2m_max', [])
            min_temps = daily.get('temperature_2m_min', [])

            max_val = max_temps[0] if max_temps and len(max_temps) > 0 and max_temps[0] is not None else (temp_c + 3)
            min_val = min_temps[0] if min_temps and len(min_temps) > 0 and min_temps[0] is not None else (temp_c - 4)

            day_name = datetime.datetime.now().strftime('%A')
            header_line = f"{day_name} • Bengaluru, Karnataka"

            hourly_pills = []
            curr_time_str = curr.get('time', '')
            times = hourly.get('time', [])
            temps = hourly.get('temperature_2m', [])
            precips = hourly.get('precipitation_probability', [])
            codes = hourly.get('weather_code', [])

            start_idx = 0
            if curr_time_str in times:
                start_idx = times.index(curr_time_str)

            for i in range(start_idx, min(start_idx + 7, len(times))):
                raw_t = times[i].split('T')[-1] if 'T' in times[i] else times[i]
                hour_num = raw_t.split(':')[0]
                formatted_hour = f"{hour_num}:00"
                
                h_code = codes[i] if i < len(codes) else 0
                _, h_icon = WMO_WEATHER_MAP.get(h_code, ("Clear", "☀️"))
                precip_val = precips[i] if i < len(precips) else 0
                
                hourly_pills.append({
                    "time": formatted_hour,
                    "temp": round(temps[i]) if i < len(temps) else temp_c,
                    "precip": f"{precip_val}%",
                    "icon": h_icon
                })

            cached_weather_data = {
                "day_header": header_line,
                "temp_c": temp_c,
                "apparent_c": apparent_temp,
                "condition": cond_str,
                "icon": icon_str,
                "humidity": str(humidity),
                "wind_kph": str(wind_kph),
                "precip_pct": f"{int(precips[start_idx])}%" if start_idx < len(precips) else "0%",
                "today_max": round(max_val),
                "today_min": round(min_val),
                "hourly": hourly_pills
            }
            logger.info(f"Fetched Bengaluru Weather: {temp_c}°C ({cond_str})")
            manager.send_event("weather", cached_weather_data)
    except Exception as e:
        logger.warning(f"Open-Meteo weather fetch error: {e}")



# Background Telemetry & Weather Loop
def background_monitor_loop():
    logger.info("Background Telemetry loop started.")
    # Seed psutil cpu_percent so first broadcast contains actual load instead of 0%
    psutil.cpu_percent(interval=0.1)
    fetch_weather()
    last_weather_time = time.time()
    last_net = psutil.net_io_counters()
    time.sleep(1)

    while True:
        try:
            cpu_pct = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory()
            net = psutil.net_io_counters()
            cpu_temp = get_cpu_temperature()

            rx_speed = (net.bytes_recv - last_net.bytes_recv) / 1024.0
            tx_speed = (net.bytes_sent - last_net.bytes_sent) / 1024.0
            last_net = net

            battery_pct = -1
            if hasattr(psutil, "sensors_battery"):
                bat = psutil.sensors_battery()
                if bat:
                    battery_pct = int(bat.percent)

            global cached_telemetry_data
            cached_telemetry_data = {
                "cpu": cpu_pct,
                "ram": mem.percent,
                "cpu_temp": cpu_temp,
                "rx_kb": round(rx_speed, 1),
                "tx_kb": round(tx_speed, 1),
                "battery": battery_pct
            }
            manager.send_event("telemetry", cached_telemetry_data)

            if time.time() - last_weather_time > 300:
                fetch_weather()
                last_weather_time = time.time()

            time.sleep(2)
        except Exception as e:
            logger.warning(f"Background monitor loop exception: {e}")
            time.sleep(2)

# Eve Voice Loop Thread Function
WAKE_WORD = "eve"
eve_agent_instance = None  # Module-level reference for persona switching
audio_handler_instance = None  # Module-level reference for proactive voice alerts

def broadcast_audio_amplitude(amp: float):
    """Broadcasts real-time audio amplitude over WebSocket for 3D orb lip-syncing."""
    manager.send_event("speaking_amplitude", {"value": round(float(amp), 3)})

def handle_audio_error(err_msg: str):
    """Broadcasts audio lock or mic access errors to the Live Terminal feed."""
    logger.warning(f"[Audio Error Handler] {err_msg}")
    manager.send_event("system", {"value": err_msg})

def eve_voice_loop():
    logger.info("EVE Voice Engine background thread starting...")
    global eve_agent_instance, audio_handler_instance
    time.sleep(2)
    manager.send_event("system", {"value": "EVE Advanced Intelligence Suite Online."})

    try:
        audio_handler = AudioHandler(
            amplitude_callback=broadcast_audio_amplitude,
            error_callback=handle_audio_error
        )
        agent = EVAgent(model_name="gemini-1.5-flash")
        eve_agent_instance = agent
        audio_handler_instance = audio_handler
    except Exception as e:
        logger.error(f"Failed to initialize EVE components: {e}")
        return

    manager.send_event("state", {"value": "IDLE"})
    initial_greeting = "Hello! I am EVE. Advanced Intelligence Suite & Live News Online."
    manager.send_event("eve_speech", {"value": initial_greeting})
    try:
        manager.send_event("state", {"value": "SPEAKING"})
        audio_handler.speak_text(initial_greeting)
    except Exception as e:
        logger.warning(f"Could not play initial greeting: {e}")
    manager.send_event("state", {"value": "IDLE"})

    while True:
        try:
            manager.send_event("state", {"value": "IDLE"})

            # Step A: Block & wait passively for wake word (does NOT hit Groq API!)
            detected = audio_handler.listen_for_wakeword()
            if not detected:
                continue

            # Step B: Wake word detected! Update HUD state & record ONE command
            manager.send_event("state", {"value": "LISTENING"})
            transcription = audio_handler.record_and_transcribe()

            if audio_handler.is_speaking and transcription.strip():
                audio_handler.stop_speaking()

            if not transcription or not transcription.strip():
                logger.info("Empty or hallucinated transcription. Returning to passive wait state.")
                manager.send_event("state", {"value": "IDLE"})
                continue

            # Step C: Valid command transcribed
            transcription_lower = transcription.lower()

            if tools.pending_email_draft is not None:
                draft = tools.pending_email_draft
                if any(w in transcription_lower for w in ["yes", "send", "confirm", "do it"]):
                    manager.send_event("state", {"value": "THINKING"})
                    manager.send_event("user_speech", {"value": transcription})
                    result = tools.send_email_gmail(draft['recipient'], draft['subject'], draft['body'])
                    manager.send_event("eve_speech", {"value": result})
                    manager.send_event("state", {"value": "SPEAKING"})
                    audio_handler.speak_text(result)
                    tools.pending_email_draft = None
                    manager.send_event("state", {"value": "IDLE"})
                    continue
                elif any(w in transcription_lower for w in ["no", "cancel", "don't", "stop"]):
                    manager.send_event("eve_speech", {"value": "Email draft cancelled."})
                    manager.send_event("state", {"value": "SPEAKING"})
                    audio_handler.speak_text("Cancelled email draft.")
                    tools.pending_email_draft = None
                    manager.send_event("state", {"value": "IDLE"})
                    continue

            # Step D: Process & execute valid user command
            manager.send_event("user_speech", {"value": transcription})

            if "shut down" in transcription_lower or "exit" in transcription_lower:
                exit_msg = "Shutting down EVE. Goodbye!"
                manager.send_event("eve_speech", {"value": exit_msg})
                manager.send_event("state", {"value": "SPEAKING"})
                audio_handler.speak_text(exit_msg)
                manager.send_event("state", {"value": "IDLE"})
                os._exit(0)

            manager.send_event("state", {"value": "THINKING"})
            response_text = agent.chat(transcription)

            manager.send_event("latency", {
                "ms": agent.last_latency_ms,
                "queries": agent.total_queries
            })

            manager.send_event("eve_speech", {"value": response_text})
            manager.send_event("state", {"value": "SPEAKING"})
            audio_handler.speak_text(response_text)
            manager.send_event("state", {"value": "IDLE"})

        except Exception as e:
            logger.error(f"Error in voice loop: {e}", exc_info=True)
            manager.send_event("state", {"value": "IDLE"})
            time.sleep(1)

# Proactive System Health & Battery Alert Monitor
last_cpu_alert_time = 0
last_bat_alert_time = 0
ALERT_COOLDOWN = 300  # 5-minute alert cooldown

def system_health_monitor():
    """Proactive System Health Monitor thread: checks CPU temp and Battery level every 60s with 300s alert cooldown."""
    global last_cpu_alert_time, last_bat_alert_time
    logger.info("System Health Monitor background thread starting...")
    time.sleep(10)  # Grace period on startup

    while True:
        try:
            now = time.time()
            # 1. Check CPU Temperature (> 80°C)
            cpu_temp = get_cpu_temperature()
            if isinstance(cpu_temp, (int, float)) and cpu_temp > 80.0:
                if now - last_cpu_alert_time > ALERT_COOLDOWN:
                    last_cpu_alert_time = now
                    msg = "Warning. CPU temperature has exceeded 80 degrees."
                    logger.warning(f"[Health Alert] {msg}")
                    manager.send_event("system", {"value": f"⚠️ ALERT: {msg}"})
                    manager.send_event("eve_speech", {"value": msg})
                    if audio_handler_instance:
                        try:
                            manager.send_event("state", {"value": "SPEAKING"})
                            audio_handler_instance.speak_text(msg)
                            manager.send_event("state", {"value": "IDLE"})
                        except Exception as ex:
                            logger.warning(f"Could not speak CPU alert: {ex}")

            # 2. Check Battery Level (< 20% and unplugged)
            if hasattr(psutil, "sensors_battery"):
                bat = psutil.sensors_battery()
                if bat and not bat.power_plugged:
                    bat_pct = int(bat.percent)
                    if bat_pct < 20:
                        if now - last_bat_alert_time > ALERT_COOLDOWN:
                            last_bat_alert_time = now
                            msg = f"Warning. Battery level is critical at {bat_pct} percent. Please connect power."
                            logger.warning(f"[Health Alert] {msg}")
                            manager.send_event("system", {"value": f"⚠️ ALERT: {msg}"})
                            manager.send_event("eve_speech", {"value": msg})
                            if audio_handler_instance:
                                try:
                                    manager.send_event("state", {"value": "SPEAKING"})
                                    audio_handler_instance.speak_text(msg)
                                    manager.send_event("state", {"value": "IDLE"})
                                except Exception as ex:
                                    logger.warning(f"Could not speak battery alert: {ex}")

        except Exception as e:
            logger.warning(f"Error in system health monitor: {e}")

        time.sleep(60)

@app.on_event("startup")
async def startup_event():
    manager.loop = asyncio.get_running_loop()
    threading.Thread(target=background_monitor_loop, daemon=True, name="background_monitor_loop").start()
    threading.Thread(target=system_health_monitor, daemon=True, name="system_health_monitor").start()
    threading.Thread(target=eve_voice_loop, daemon=True, name="eve_voice_loop").start()

def launch_native_window():
    hud_url = "http://localhost:8000/dashboard"
    time.sleep(1.5)

    win_w, win_h = 1150, 620
    win_x, win_y = None, None
    try:
        import screeninfo
        monitors = screeninfo.get_monitors()
        primary = next((m for m in monitors if getattr(m, 'is_primary', False)), monitors[0]) if monitors else None
        if primary:
            avail_w = primary.width
            avail_h = max(450, primary.height - 60)  # Account for Windows taskbar height
            win_w = min(1150, avail_w - 40)
            win_h = min(620, avail_h - 20)
            win_x = primary.x + max(0, (avail_w - win_w) // 2)
            win_y = primary.y + max(0, (avail_h - win_h) // 2)
            logger.info(f"Multi-Monitor: Target window size ({win_w}x{win_h}) positioned at ({win_x}, {win_y}).")
    except Exception as se:
        logger.warning(f"Screen resolution detection fallback: {se}")

    try:
        import webview
        logger.info(f"Launching pywebview native app window ({win_w}x{win_h})...")
        create_kwargs = {
            "title": "EVE",
            "url": hud_url,
            "width": win_w,
            "height": win_h,
            "frameless": False,
            "resizable": True,
            "easy_drag": True
        }
        if win_x is not None and win_y is not None:
            create_kwargs["x"] = win_x
            create_kwargs["y"] = win_y

        webview.create_window(**create_kwargs)
        webview.start()
    except Exception as e:
        logger.warning(f"pywebview window launch fallback: {e}")
        try:
            subprocess.Popen(["chrome.exe", f"--app={hud_url}"], shell=True)
        except Exception:
            subprocess.Popen(["msedge.exe", f"--app={hud_url}"], shell=True)

if __name__ == "__main__":
    uvicorn_config = uvicorn.Config("main:app", host="127.0.0.1", port=8000, log_level="info")
    server = uvicorn.Server(uvicorn_config)
    
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()

    launch_native_window()
