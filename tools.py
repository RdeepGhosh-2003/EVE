import os
import sys
import ast
import io
import re
import html
import json
import time
import shutil
import base64
import datetime
import subprocess
import platform
import webbrowser
import logging
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from email.mime.text import MIMEText
from PIL import Image, ImageGrab, ImageDraw
import pyautogui
from groq import Groq
import psutil

# Disable PyAutoGUI failsafe for automated hotkey triggers
pyautogui.FAILSAFE = False

from memory_handler import MemoryHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

memory_handler = MemoryHandler()
pending_email_draft = None

def get_current_time() -> str:
    """Returns exact current date and time."""
    try:
        now = datetime.datetime.now()
        formatted_time = now.strftime("%A, %B %d, %Y at %I:%M %p")
        return f"The current date and time is {formatted_time}."
    except Exception as e:
        return f"Error retrieving current time: {str(e)}"

def open_calculator() -> str:
    """Uses subprocess to open system calculator across platforms."""
    try:
        current_os = platform.system().lower()
        if "windows" in current_os:
            subprocess.Popen(["calc.exe"])
        elif "darwin" in current_os:
            subprocess.Popen(["open", "-a", "Calculator"])
        elif "linux" in current_os:
            for calc_cmd in ["gnome-calculator", "kcalc", "xcalc", "galculator"]:
                try:
                    subprocess.Popen([calc_cmd])
                    break
                except FileNotFoundError:
                    continue
            else:
                return "Failed to find standard calculator app on Linux."
        else:
            return f"Unsupported OS: {current_os}"
        return "Opening calculator now."
    except Exception as e:
        return f"Failed to open calculator: {str(e)}"

def open_application(app_name: str) -> str:
    """Launches Google Chrome, web browsers, websites, or desktop applications."""
    try:
        app_clean = app_name.lower().strip()
        current_os = platform.system().lower()

        if "chrome" in app_clean or "browser" in app_clean or "google" in app_clean:
            if "windows" in current_os:
                try:
                    subprocess.Popen(["start", "chrome"], shell=True)
                except Exception:
                    webbrowser.open("https://www.google.com")
            elif "darwin" in current_os:
                subprocess.Popen(["open", "-a", "Google Chrome"])
            else:
                webbrowser.open("https://www.google.com")
            logger.info("[Tool: open_application] Opened Google Chrome.")
            return "Opening Chrome now."

        elif "notepad" in app_clean or "text editor" in app_clean:
            if "windows" in current_os:
                subprocess.Popen(["notepad.exe"])
            elif "darwin" in current_os:
                subprocess.Popen(["open", "-a", "TextEdit"])
            else:
                subprocess.Popen(["gedit"])
            return "Opening Notepad now."

        elif "calculator" in app_clean or "calc" in app_clean:
            return open_calculator()

        elif "cmd" in app_clean or "terminal" in app_clean or "command prompt" in app_clean:
            if "windows" in current_os:
                subprocess.Popen(["start", "cmd"], shell=True)
            elif "darwin" in current_os:
                subprocess.Popen(["open", "-a", "Terminal"])
            else:
                subprocess.Popen(["x-terminal-emulator"])
            return "Opening terminal now."

        elif app_clean.startswith("http://") or app_clean.startswith("https://") or ".com" in app_clean or ".org" in app_clean or ".net" in app_clean:
            url = app_name if app_clean.startswith("http") else f"https://{app_clean}"
            webbrowser.open(url)
            return f"Opening {app_name} in your browser now."

        else:
            if "windows" in current_os:
                subprocess.Popen(["start", app_name], shell=True)
            elif "darwin" in current_os:
                subprocess.Popen(["open", "-a", app_name])
            else:
                subprocess.Popen([app_name])
            logger.info(f"[Tool: open_application] Launched '{app_name}'.")
            return f"Opening {app_name} now."

    except Exception as e:
        logger.error(f"Error opening application '{app_name}': {e}")
        return f"Failed to open '{app_name}': {str(e)}"

def save_memory(topic: str, text: str) -> str:
    """Saves persistent note to Google Drive 'Eve_Memories' folder or local backup."""
    return memory_handler.save_memory(topic, text)

def search_memory(query: str) -> str:
    """Searches notes saved in Google Drive 'Eve_Memories' folder or local backup."""
    return memory_handler.search_memory(query)

def draft_email(recipient_email: str, subject: str, body: str) -> str:
    """Drafts an email for human-in-the-loop verbal confirmation before sending via Gmail API."""
    global pending_email_draft
    pending_email_draft = {
        "recipient": recipient_email,
        "subject": subject,
        "body": body
    }
    logger.info(f"Email drafted for {recipient_email}. Awaiting human confirmation.")
    return (
        f"CONFIRMATION_REQUIRED: I have prepared an email to {recipient_email} with subject '{subject}'. "
        f"Please confirm verbally if I should send it."
    )

def send_email_gmail(recipient_email: str, subject: str, body: str) -> str:
    """Sends an email using real SMTP (SMTP_USER/SMTP_PASS in .env) or fallback to Gmail API / draft log."""
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))

    if smtp_user and smtp_pass:
        try:
            import smtplib
            from email.message import EmailMessage
            msg = EmailMessage()
            msg["From"] = smtp_user
            msg["To"] = recipient_email
            msg["Subject"] = subject
            msg.set_content(body)
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            logger.info(f"Email successfully sent to {recipient_email} via SMTP ({smtp_host}).")
            return f"Email successfully sent to {recipient_email} via SMTP."
        except Exception as se:
            logger.warning(f"SMTP send error: {se}")
            return f"Failed to send email via SMTP: {str(se)}"

    token_path = "token.json"
    if not os.path.exists(token_path):
        logger.info(f"[Email Draft Log] To: {recipient_email} | Subject: {subject}")
        return (
            f"SMTP credentials not configured in environment (SMTP_USER/SMTP_PASS in .env). "
            f"Draft logged for {recipient_email}:\nSubject: {subject}\nBody: {body}"
        )

    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        creds = Credentials.from_authorized_user_file(token_path, ['https://www.googleapis.com/auth/gmail.send'])
        service = build('gmail', 'v1', credentials=creds)

        message = MIMEText(body)
        message['to'] = recipient_email
        message['subject'] = subject
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        sent_msg = service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
        logger.info(f"Gmail message sent! ID: {sent_msg.get('id')}")
        return f"Email successfully sent to {recipient_email} via Gmail."
    except Exception as e:
        logger.error(f"Error sending email via Gmail API: {e}")
        return f"Failed to send email via Gmail API: {str(e)}"

send_email = send_email_gmail

def _take_screenshot_image():
    """Helper method to take desktop screenshot with graceful fallback."""
    try:
        return ImageGrab.grab()
    except Exception:
        try:
            return pyautogui.screenshot()
        except Exception:
            img = Image.new("RGB", (1280, 720), color=(15, 23, 42))
            d = ImageDraw.Draw(img)
            d.text((400, 350), "EVE System Screen Capture Buffer", fill=(255, 255, 255))
            return img

def capture_screen(filename: str = "screen_capture.png") -> str:
    """Captures the current desktop screen and saves it as an image file."""
    try:
        screenshot = _take_screenshot_image()
        output_path = os.path.join(os.getcwd(), filename)
        screenshot.save(output_path)
        logger.info(f"Screen captured and saved to '{output_path}'.")
        return f"Screen captured successfully and saved to {output_path}."
    except Exception as e:
        logger.error(f"Failed to capture screen: {e}")
        return f"Failed to capture screen: {str(e)}"

def capture_and_analyze_screen(query: str = "Describe what is on the screen") -> str:
    """Captures desktop screenshot and uses Groq Multimodal AI (llama-3.2-11b-vision-preview) to analyze screen contents."""
    try:
        screenshot = _take_screenshot_image()
        buffer = io.BytesIO()
        screenshot.convert("RGB").save(buffer, format="JPEG", quality=85)
        base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return "GROQ_API_KEY is missing. Cannot analyze screen."

        client = Groq(api_key=api_key)
        logger.info(f"[Vision AI] Sending screen capture to llama-3.2-11b-vision-preview with query: '{query}'")

        response = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": query},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.3,
            max_tokens=300
        )

        analysis_text = response.choices[0].message.content.strip()
        logger.info(f"[Vision AI Result]: {analysis_text}")
        return analysis_text
    except Exception as e:
        logger.error(f"Screen vision analysis failed: {e}")
        return f"Failed to analyze screen vision: {str(e)}"

def manage_media_volume(action: str, level: int = None) -> str:
    """Controls system media playback and volume levels using system hotkeys."""
    try:
        act = action.lower().strip()
        if act in ["play_pause", "play", "pause", "toggle"]:
            pyautogui.press('playpause')
            return "Toggled media play/pause."
        elif act in ["next", "next_track", "skip"]:
            pyautogui.press('nexttrack')
            return "Skipped to next media track."
        elif act in ["previous", "prev", "prev_track", "back"]:
            pyautogui.press('prevtrack')
            return "Went back to previous media track."
        elif act in ["volume_up", "vol_up", "louder"]:
            pyautogui.press('volumeup', presses=5)
            return "Increased system volume."
        elif act in ["volume_down", "vol_down", "quieter"]:
            pyautogui.press('volumedown', presses=5)
            return "Decreased system volume."
        elif act in ["mute", "unmute", "silence"]:
            pyautogui.press('volumemute')
            return "Toggled system volume mute."
        else:
            return f"Unsupported media action '{action}'. Supported actions: play_pause, next, previous, volume_up, volume_down, mute."
    except Exception as e:
        logger.error(f"Error managing media/volume: {e}")
        return f"Failed to control media volume: {str(e)}"

def execute_system_command(command: str) -> str:
    """Executes a system shell / PowerShell / CMD command on the local computer and returns output."""
    try:
        logger.info(f"[Tool: execute_system_command] Executing: '{command}'")
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, timeout=15).decode('utf-8', errors='ignore')
        return output.strip() if output.strip() else "Command executed successfully with no output."
    except subprocess.CalledProcessError as e:
        return f"Command error (exit code {e.returncode}):\n{e.output.decode('utf-8', errors='ignore').strip()}"
    except Exception as e:
        return f"Failed to execute system command: {str(e)}"

def automate_keyboard_mouse(action: str, target: str = None, x: int = None, y: int = None) -> str:
    """Automates keyboard hotkeys, text typing, or mouse clicks on the desktop."""
    try:
        act = action.lower().strip()
        if act == "type":
            if not target:
                return "Please specify text to type."
            pyautogui.write(target, interval=0.03)
            return f"Typed text: '{target}'."
        elif act in ["hotkey", "press_keys"]:
            if not target:
                return "Please specify hotkey combinations (e.g. 'ctrl,c' or 'win,r')."
            keys = [k.strip() for k in target.split(',')]
            pyautogui.hotkey(*keys)
            return f"Pressed keyboard hotkey combination: {target}."
        elif act in ["click", "mouse_click"]:
            if x is not None and y is not None:
                pyautogui.click(x, y)
                return f"Clicked mouse at coordinates ({x}, {y})."
            else:
                pyautogui.click()
                return "Clicked mouse at current cursor position."
        else:
            return f"Unsupported desktop automation action '{action}'. Use 'type', 'hotkey', or 'click'."
    except Exception as e:
        return f"Failed to perform desktop automation: {str(e)}"

def manage_file_system(action: str, path: str, content: str = None) -> str:
    """Reads, writes, creates, or lists files and directories on the local file system."""
    try:
        act = action.lower().strip()
        abs_path = os.path.abspath(path)

        if act in ["read", "read_file"]:
            if not os.path.exists(abs_path):
                return f"File does not exist at {abs_path}"
            with open(abs_path, 'r', encoding='utf-8', errors='ignore') as f:
                data = f.read()
            return f"Contents of {abs_path}:\n{data[:2000]}"

        elif act in ["write", "write_file", "create_file"]:
            if content is None:
                content = ""
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"File written successfully at {abs_path}."

        elif act in ["list", "list_dir", "ls"]:
            if not os.path.exists(abs_path):
                return f"Directory does not exist at {abs_path}"
            items = os.listdir(abs_path)
            return f"Contents of directory {abs_path}:\n" + "\n".join(items[:50])

        elif act in ["mkdir", "create_dir"]:
            os.makedirs(abs_path, exist_ok=True)
            return f"Directory created at {abs_path}."

        else:
            return f"Unsupported file action '{action}'. Use 'read', 'write', 'list', or 'mkdir'."
    except Exception as e:
        return f"File system error: {str(e)}"

# ==========================================
# 7 ADVANCED INTELLIGENCE SUITE TOOLS
# ==========================================

def fetch_live_news(topic: str = "ai") -> str:
    """Fetches real-time World and AI news headlines via live RSS feeds with fallback."""
    try:
        topic_clean = topic.lower().strip() if topic else ""
        if "ai" in topic_clean or "artificial" in topic_clean or not topic_clean:
            rss_urls = [
                "https://news.google.com/rss/search?q=artificial+intelligence&hl=en-IN&gl=IN&ceid=IN:en",
                "https://techcrunch.com/category/artificial-intelligence/feed/",
                "https://news.ycombinator.com/rss"
            ]
            display_topic = topic.upper() if topic else "AI"
        elif "world" in topic_clean:
            rss_urls = [
                "https://news.google.com/rss/search?q=world+news&hl=en-IN&gl=IN&ceid=IN:en",
                "https://news.ycombinator.com/rss"
            ]
            display_topic = topic.upper()
        else:
            q_enc = urllib.parse.quote(topic)
            rss_urls = [
                f"https://news.google.com/rss/search?q={q_enc}&hl=en-IN&gl=IN&ceid=IN:en",
                "https://news.ycombinator.com/rss"
            ]
            display_topic = topic.upper()

        last_err = None
        for rss_url in rss_urls:
            try:
                req = urllib.request.Request(rss_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    xml_data = resp.read()
                    root = ET.fromstring(xml_data)
                    items = root.findall('./channel/item')[:5]

                    news_list = []
                    for idx, item in enumerate(items, 1):
                        title_elem = item.find('title')
                        if title_elem is not None and title_elem.text:
                            raw_title = title_elem.text
                            clean_title = html.unescape(re.sub(r'<[^>]+>', '', raw_title)).strip()
                            news_list.append(f"{idx}. {clean_title}")

                    if news_list:
                        result = f"Top Live {display_topic} News Headlines:\n" + "\n".join(news_list)
                        logger.info(f"[Tool: fetch_live_news] Retrieved {len(news_list)} headlines for '{topic}' from {rss_url}")
                        return result
            except Exception as e:
                last_err = e
                logger.warning(f"[fetch_live_news] Feed failed ({rss_url}): {e}")
                continue

        return f"Failed to fetch live news: {str(last_err or 'No RSS items found')}"
    except Exception as e:
        logger.error(f"Failed to fetch news: {e}")
        return f"Failed to fetch live news: {str(e)}"

def search_web_realtime(query: str) -> str:
    """Searches the live web using SerpAPI (if SERPAPI_API_KEY is present) or DuckDuckGo POST request fallback."""
    try:
        q_clean = query.strip() if query else ""
        if not q_clean:
            return "No search results found for ''."

        serp_key = os.getenv("SERPAPI_API_KEY")
        if serp_key:
            try:
                from serpapi import GoogleSearch
                params = {
                    "engine": "google",
                    "q": q_clean,
                    "api_key": serp_key,
                    "num": 4
                }
                search = GoogleSearch(params)
                res_dict = search.get_dict()
                organic = res_dict.get("organic_results", [])
                if organic:
                    res_lines = []
                    for idx, item in enumerate(organic[:4], 1):
                        t = item.get("title", "No Title")
                        l = item.get("link", "")
                        s = item.get("snippet", "")
                        res_lines.append(f"{idx}. [{t}]({l})\n   {s}")
                    logger.info(f"[SerpAPI Search] Retrieved {len(organic[:4])} results for '{q_clean}'.")
                    return f"Search Results for '{q_clean}':\n\n" + "\n\n".join(res_lines)
            except Exception as se:
                logger.warning(f"SerpAPI search fallback to DuckDuckGo: {se}")

        url = "https://html.duckduckgo.com/html/"
        data = urllib.parse.urlencode({"q": q_clean}).encode("utf-8")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        
        req = urllib.request.Request(url, data=data, headers=headers)
        
        with urllib.request.urlopen(req, timeout=6) as resp:
            html_raw = resp.read().decode('utf-8', errors='ignore')
            
            titles_urls = re.findall(r'<a class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html_raw, re.DOTALL)
            snippets = re.findall(r'<a class="result__snippet[^"]*"[^>]*>(.*?)</a>', html_raw, re.DOTALL)
            
            results = []
            max_results = min(len(titles_urls), len(snippets), 4)
            
            for i in range(max_results):
                raw_url, raw_title = titles_urls[i]
                raw_snippet = snippets[i]
                
                if "uddg=" in raw_url:
                    parsed_qs = urllib.parse.parse_qs(urllib.parse.urlparse(raw_url).query)
                    actual_url = parsed_qs.get("uddg", [raw_url])[0]
                else:
                    actual_url = raw_url
                    
                clean_title = html.unescape(re.sub(r'<[^>]+>', '', raw_title)).strip()
                clean_snippet = html.unescape(re.sub(r'<[^>]+>', '', raw_snippet)).strip()
                
                if clean_title and clean_snippet:
                    results.append(
                        f"{i+1}. Title: {clean_title}\n"
                        f"   URL: {actual_url}\n"
                        f"   Snippet: {clean_snippet}"
                    )
            
            if results:
                formatted_result = f"Real-time Web Search Results for '{query}':\n\n" + "\n\n".join(results)
                logger.info(f"[Tool: search_web_realtime] Retrieved {len(results)} search results via DDG POST for '{query}'")
                return formatted_result
            else:
                fallback_snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', html_raw, re.DOTALL)
                clean_fallback = [html.unescape(re.sub(r'<[^>]+>', '', s)).strip() for s in fallback_snippets[:3] if s.strip()]
                if clean_fallback:
                    result = f"Real-time Web Search Results for '{query}':\n" + "\n---\n".join(clean_fallback)
                    logger.info(f"[Tool: search_web_realtime] Found {len(clean_fallback)} snippet search results for '{query}'")
                    return result
                return f"No search results found for '{query}'."

    except Exception as e:
        logger.error(f"Failed live web search: {e}")
        return f"Failed to perform live web search: {str(e)}"

def automate_browser_workflow(url: str = None, action: str = "open", target: str = None) -> str:
    """Navigates web pages, fills job applications or form fields, scrapes web content, takes screenshots, and clicks elements."""
    try:
        act = str(action).lower().strip() if action else "open"
        if act in ["open", "navigate"]:
            if url:
                target_url = url if "://" in url else f"https://{url}"
            else:
                target_url = "https://indeed.com"
            webbrowser.open(target_url)
            return f"Opened web page: {target_url}."

        elif act in ["scrape", "read_page", "extract"]:
            if not url:
                return "Please specify a URL to scrape."
            target_url = url if "://" in url else f"https://{url}"

            # Playwright Headless Scraping with clean context closure
            try:
                from playwright.sync_api import sync_playwright
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    page.goto(target_url, timeout=12000)
                    html_content = page.content()
                    browser.close()

                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html_content, 'html.parser')
                    for element in soup(["script", "style", "nav", "footer"]):
                        element.extract()
                    page_text = ' '.join(soup.stripped_strings)
                    clean_text = ' '.join(page_text.split())
                    logger.info(f"[Playwright Scraped] {target_url} ({len(clean_text)} chars)")
                    return f"Page Content from {target_url}:\n{clean_text[:2500]}"
            except Exception as pe:
                logger.warning(f"Playwright scrape fallback to urllib/BS4: {pe}")

            import ssl
            try:
                from bs4 import BeautifulSoup
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                req = urllib.request.Request(target_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                with urllib.request.urlopen(req, context=ctx, timeout=8) as response:
                    html_content = response.read().decode('utf-8', errors='ignore')
                    soup = BeautifulSoup(html_content, 'html.parser')
                    for element in soup(["script", "style", "nav", "footer"]):
                        element.extract()
                    page_text = ' '.join(soup.stripped_strings)
                    clean_text = ' '.join(page_text.split())
                    return f"Page Content from {target_url}:\n{clean_text[:2500]}"
            except Exception as e:
                return f"Failed to scrape webpage at {target_url}: {str(e)}"
        elif act in ["fill_form", "type_input", "type"]:
            if target:
                pyautogui.write(target, interval=0.04)
                return f"Typed input '{target}' into active web field."
            else:
                return "Please specify target text to type."

        elif act in ["click", "click_element"]:
            if target and "," in target:
                try:
                    coords = [int(c.strip()) for c in target.split(",")]
                    if len(coords) == 2:
                        pyautogui.click(coords[0], coords[1])
                        return f"Clicked browser element at screen coordinates ({coords[0]}, {coords[1]})."
                except ValueError:
                    pass
            pyautogui.click()
            return "Clicked mouse at current cursor position."

        elif act in ["click_apply", "submit"]:
            pyautogui.press('enter')
            return "Submitted active form / application."

        elif act in ["screenshot", "capture"]:
            filename = target if target and target.endswith(".png") else "browser_screenshot.png"
            return capture_screen(filename)

        else:
            return f"Unsupported browser workflow action '{action}'."
    except Exception as e:
        logger.error(f"Browser automation error: {e}")
        return f"Browser automation error: {str(e)}"

def get_daily_briefing() -> str:
    """Aggregates system health, weather forecast, battery level, and top 3 AI headlines into a 60-second morning briefing summary."""
    try:
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory().percent
        bat = psutil.sensors_battery()
        bat_str = f"{int(bat.percent)}%" if bat else "Desktop AC Power"

        weather_str = "Weather information currently unavailable."
        try:
            w_req = urllib.request.Request("https://wttr.in/?format=%C+%t", headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(w_req, timeout=3) as w_resp:
                weather_data = w_resp.read().decode('utf-8', errors='ignore').strip()
                if weather_data and not weather_data.startswith("<!DOCTYPE") and not weather_data.startswith("<html>"):
                    weather_str = html.unescape(weather_data)
        except Exception as we:
            logger.debug(f"Weather fetch failed: {we}")

        try:
            news_text = fetch_live_news("ai")
            if isinstance(news_text, str) and not news_text.startswith("Failed"):
                lines = [line.strip() for line in news_text.split('\n') if line.strip() and not line.startswith("Top Live")]
                top_headlines = lines[:3] if lines else ["1. Live AI news headlines currently unavailable"]
            else:
                top_headlines = ["1. Live AI news headlines currently unavailable"]
        except Exception as e:
            logger.error(f"Failed to fetch live news for daily briefing: {e}")
            top_headlines = ["1. Live AI news headlines currently unavailable"]

        briefing = (
            f"Good day! Here is your EVE Daily Briefing:\n"
            f"System Health: CPU Load is at {cpu}%, Memory usage is at {mem}%, Battery: {bat_str}.\n"
            f"Current Weather: {weather_str}\n"
            f"Top AI Intelligence Headlines:\n" + "\n".join(top_headlines)
        )
        return briefing
    except Exception as e:
        return f"Failed to generate daily briefing: {str(e)}"

def manage_system_performance(action: str = "check", target: str = None) -> str:
    """Monitors CPU/RAM/Disk/Battery/Temp, cleans temporary files, lists top processes, or terminates specific processes."""
    try:
        act = str(action).lower().strip() if action else "check"
        target_str = str(target).strip() if target else ""

        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory().percent
        bat = psutil.sensors_battery()
        bat_str = f"{int(bat.percent)}%" if bat else "Desktop AC Power"

        disk_str = ""
        try:
            disk = psutil.disk_usage('/')
            disk_str = f", Disk {disk.percent}%"
        except Exception:
            try:
                disk = psutil.disk_usage(os.path.abspath(os.sep))
                disk_str = f", Disk {disk.percent}%"
            except Exception:
                disk_str = ""

        cpu_temp_str = ""
        if platform.system().lower() == "windows":
            try:
                cmd = ['powershell', '-Command', 'Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature -ErrorAction SilentlyContinue | Select-Object -ExpandProperty CurrentTemperature']
                out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=2).decode().strip()
                if out:
                    temps = [round((float(val)/10.0) - 273.15, 1) for val in out.splitlines() if val.strip().isdigit()]
                    if temps:
                        cpu_temp_str = f", CPU Temp {max(temps)}°C"
            except Exception:
                pass

        status_msg = f"System Status: CPU Load {cpu}%, RAM {mem}%{disk_str}{cpu_temp_str}, Battery {bat_str}."

        if act in ["clean", "cleanup", "optimize"]:
            import tempfile, gc
            temp_dir = tempfile.gettempdir()
            cleaned_files = 0
            for root, dirs, files in os.walk(temp_dir):
                for f in files:
                    try:
                        os.remove(os.path.join(root, f))
                        cleaned_files += 1
                    except Exception:
                        pass
                break
            gc.collect()
            return status_msg + " Performance optimized."

        elif act in ["top_processes", "processes", "top"]:
            procs = sorted([p.info for p in psutil.process_iter(['pid', 'name', 'memory_percent']) if p.info.get('name')], key=lambda x: x.get('memory_percent') or 0, reverse=True)[:5]
            proc_lines = [f"- {p['name']} (PID {p['pid']}): RAM {round(p['memory_percent'] or 0, 1)}%" for p in procs]
            return f"{status_msg}\nTop 5 Memory Consuming Processes:\n" + "\n".join(proc_lines)

        elif act in ["kill", "terminate", "stop"]:
            if not target_str:
                return "Please specify a process name or PID to terminate."
            killed = []
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    p_name = proc.info.get('name') or ''
                    p_pid = str(proc.info.get('pid'))
                    if p_pid == target_str or target_str.lower() in p_name.lower():
                        proc.terminate()
                        killed.append(f"{p_name} (PID {p_pid})")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            if killed:
                return f"Terminated background processes: {', '.join(killed)}."
            else:
                return f"No matching process found for target '{target_str}'."

        else:
            return status_msg

    except Exception as e:
        logger.error(f"Performance check error: {e}")
        return f"Performance check error: {str(e)}"

def organize_downloads_folder() -> str:
    """Organizes files in the Downloads folder into classified subfolders (Images, Documents, Executables, Archives, Code, Media)."""
    try:
        user_home = os.path.expanduser("~")
        downloads_dir = os.path.join(user_home, "Downloads")
        if not os.path.exists(downloads_dir):
            return f"Downloads folder not found at {downloads_dir}"

        categories = {
            "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico", ".tiff"],
            "Documents": [".pdf", ".docx", ".doc", ".txt", ".xlsx", ".pptx", ".csv", ".odt", ".rtf"],
            "Executables": [".exe", ".msi", ".bat", ".cmd", ".ps1", ".vbs", ".apk"],
            "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".iso"],
            "Code": [".py", ".js", ".ts", ".html", ".css", ".json", ".cpp", ".c", ".java", ".rs", ".go", ".sh", ".php", ".sql"],
            "Audio": [".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg"],
            "Media": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"]
        }
        ignore_exts = [".crdownload", ".tmp", ".part", ".download", ".p2p"]
        category_names = set(categories.keys())

        moved_count = 0
        for item in os.listdir(downloads_dir):
            if item in category_names or item.startswith("."):
                continue
            item_path = os.path.join(downloads_dir, item)
            if os.path.isfile(item_path):
                ext = os.path.splitext(item)[1].lower()
                if ext in ignore_exts:
                    continue
                for category, extensions in categories.items():
                    if ext in extensions:
                        cat_dir = os.path.join(downloads_dir, category)
                        os.makedirs(cat_dir, exist_ok=True)
                        dst_path = os.path.join(cat_dir, item)

                        if os.path.exists(dst_path):
                            base, extension = os.path.splitext(item)
                            counter = 1
                            while os.path.exists(os.path.join(cat_dir, f"{base}_{counter}{extension}")) and counter <= 100:
                                counter += 1
                            if counter > 100:
                                import time
                                timestamp = int(time.time())
                                dst_path = os.path.join(cat_dir, f"{base}_{timestamp}{extension}")
                            else:
                                dst_path = os.path.join(cat_dir, f"{base}_{counter}{extension}")

                        try:
                            shutil.move(item_path, dst_path)
                            moved_count += 1
                        except Exception as e:
                            logger.warning(f"Could not move download item '{item}': {e}")
                        break

        return f"Organized Downloads folder: Moved {moved_count} files into categorized subfolders."
    except Exception as e:
        logger.error(f"Failed to organize downloads: {e}")
        return f"Failed to organize downloads: {str(e)}"

def check_schedule(date: str = "today", action: str = "read", event_details: str = None) -> str:
    """Reads from or writes to the local JSON calendar database (memory/calendar.json)."""
    try:
        memory_dir = os.path.join(os.getcwd(), "memory")
        os.makedirs(memory_dir, exist_ok=True)
        calendar_path = os.path.join(memory_dir, "calendar.json")

        calendar_data = []
        if os.path.exists(calendar_path):
            try:
                with open(calendar_path, "r", encoding="utf-8") as f:
                    calendar_data = json.load(f)
                if not isinstance(calendar_data, list):
                    calendar_data = []
            except Exception:
                calendar_data = []

        act = str(action).lower().strip() if action else "read"
        d_str = str(date).lower().strip() if date else "today"

        import datetime
        if d_str == "today":
            target_date = datetime.date.today().isoformat()
        else:
            target_date = d_str

        if act in ["add", "create", "schedule"]:
            if not event_details:
                return "Please provide event details to schedule."
            new_event = {
                "id": str(int(time.time() * 1000)),
                "date": target_date,
                "event": event_details.strip(),
                "created_at": datetime.datetime.now().isoformat()
            }
            calendar_data.append(new_event)
            with open(calendar_path, "w", encoding="utf-8") as f:
                json.dump(calendar_data, f, indent=2, ensure_ascii=False)
            logger.info(f"[Calendar] Scheduled event on {target_date}: {event_details}")
            return f"Scheduled event on {target_date}: '{event_details}'."

        elif act in ["delete", "remove", "clear"]:
            if not event_details:
                return "Please specify event details or keyword to remove."
            initial_count = len(calendar_data)
            calendar_data = [e for e in calendar_data if not (event_details.lower() in e.get("event", "").lower())]
            removed = initial_count - len(calendar_data)
            with open(calendar_path, "w", encoding="utf-8") as f:
                json.dump(calendar_data, f, indent=2, ensure_ascii=False)
            return f"Removed {removed} matching event(s) from calendar."

        else:  # read
            matching = [e for e in calendar_data if e.get("date") == target_date or d_str == "all" or target_date in e.get("date", "")]
            if not matching:
                return f"No events scheduled for {d_str} ({target_date})."
            event_lines = [f"- {e.get('event')} (Date: {e.get('date')})" for e in matching]
            return f"Schedule for {target_date}:\n" + "\n".join(event_lines)

    except Exception as e:
        logger.error(f"Error accessing calendar: {e}")
        return f"Failed to access calendar: {str(e)}"

# Self-Evolution Auto-Coder Tool
def modify_system_code(file_path: str, new_content: str) -> str:
    """Modifies EVE's system source code with automatic timestamped backups and AST syntax validation for Python files."""
    try:
        if not file_path or not new_content:
            return "Error: file_path and new_content are required."

        abs_path = os.path.abspath(file_path)
        
        # AST Syntax Validation for Python files
        if abs_path.endswith(".py"):
            try:
                ast.parse(new_content)
            except SyntaxError as syn_err:
                logger.error(f"[AST Validation Failed] SyntaxError in proposed code for {file_path}: {syn_err}")
                return f"[SyntaxError Aborted] Failed AST syntax validation: {syn_err}. Code was NOT written to disk."

        # Backup creation
        backup_dir = os.path.join(os.getcwd(), "memory", "backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(abs_path)
        backup_path = os.path.join(backup_dir, f"{filename}_{timestamp}.bak")
        
        if os.path.exists(abs_path):
            shutil.copy2(abs_path, backup_path)
            logger.info(f"[Self-Evolution Backup] Created backup at {backup_path}")

        # Write new content
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        logger.info(f"[Self-Evolution] Updated source file: {abs_path}")
        return f"[Success] File {os.path.basename(abs_path)} successfully updated. Backup saved to memory/backups/{os.path.basename(backup_path)}. Call reboot_system() to apply changes."
    except Exception as e:
        logger.error(f"Failed to modify system code: {e}")
        return f"Error modifying code: {str(e)}"

# System Reboot Tool
def reboot_system() -> str:
    """Gracefully restarts the main EVE process to apply new source code changes into memory."""
    try:
        logger.info("[Self-Evolution Reboot] Initiating process reboot via os.execl...")
        def _exec_reboot():
            time.sleep(1)
            os.execl(sys.executable, sys.executable, *sys.argv)
        
        import threading
        t = threading.Thread(target=_exec_reboot, daemon=True)
        t.start()
        return "[Reboot Initiated] EVE is restarting process to apply code updates..."
    except Exception as e:
        logger.error(f"Reboot error: {e}")
        return f"Error rebooting system: {str(e)}"

AVAILABLE_TOOLS = {
    "get_current_time": get_current_time,
    "open_calculator": open_calculator,
    "open_application": open_application,
    "save_memory": save_memory,
    "search_memory": search_memory,
    "draft_email": draft_email,
    "send_email": send_email_gmail,
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
    "organize_downloads_folder": organize_downloads_folder,
    "check_schedule": check_schedule,
    "modify_system_code": modify_system_code,
    "reboot_system": reboot_system
}

# Groq / OpenAI Compatible Function Definitions
GROQ_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the exact current date and time.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_calculator",
            "description": "Open the system calculator application.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_application",
            "description": "Open a desktop application such as Chrome, Notepad, Terminal, or a website URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "Name of the application (e.g. 'chrome', 'notepad', 'cmd', 'calculator') or website URL"
                    }
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_memory",
            "description": "Save a persistent note or memory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Topic title for the memory note"
                    },
                    "text": {
                        "type": "string",
                        "description": "Memory note content to save"
                    }
                },
                "required": ["topic", "text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_memory",
            "description": "Search saved notes and memories.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query or keyword"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "draft_email",
            "description": "Draft an email to send via Gmail (requires confirmation).",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipient_email": {
                        "type": "string",
                        "description": "Recipient email address"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject"
                    },
                    "body": {
                        "type": "string",
                        "description": "Email message body"
                    }
                },
                "required": ["recipient_email", "subject", "body"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "capture_screen",
            "description": "Capture a screenshot of the user's desktop screen.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "capture_and_analyze_screen",
            "description": "Capture the desktop screen and use Multimodal Vision AI to describe or analyze what is currently visible.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Question or instructions about what to analyze on the screen (e.g., 'Describe what is on my screen', 'Read the text in the active window')"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "manage_media_volume",
            "description": "Control system media playback (play_pause, next, previous) and system volume (volume_up, volume_down, mute).",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action to perform: 'play_pause', 'next', 'previous', 'volume_up', 'volume_down', 'mute'",
                        "enum": ["play_pause", "next", "previous", "volume_up", "volume_down", "mute"]
                    }
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_system_command",
            "description": "Execute a shell / PowerShell / CMD command on the user's computer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The command line string to execute (e.g., 'dir', 'ipconfig', 'tasklist')"
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "automate_keyboard_mouse",
            "description": "Automate desktop user interaction: typing text, pressing hotkey combinations, or clicking screen coordinates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action type: 'type', 'hotkey', or 'click'",
                        "enum": ["type", "hotkey", "click"]
                    },
                    "target": {
                        "type": "string",
                        "description": "Text to type if action is 'type', or comma-separated keys if action is 'hotkey' (e.g. 'ctrl,c', 'win,r')"
                    },
                    "x": {
                        "type": "integer",
                        "description": "Screen X coordinate for mouse click"
                    },
                    "y": {
                        "type": "integer",
                        "description": "Screen Y coordinate for mouse click"
                    }
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "manage_file_system",
            "description": "Read, write, create, or list files and directories on the user's computer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action type: 'read', 'write', 'list', or 'mkdir'",
                        "enum": ["read", "write", "list", "mkdir"]
                    },
                    "path": {
                        "type": "string",
                        "description": "Absolute or relative file/directory path"
                    },
                    "content": {
                        "type": "string",
                        "description": "File text content if action is 'write'"
                    }
                },
                "required": ["action", "path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_live_news",
            "description": "Fetch real-time World and AI news headlines from live news feeds.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "News topic: 'ai', 'world', 'technology', 'business'"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web_realtime",
            "description": "Search the live web for real-time information, breaking events, or web queries.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Web search query"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "automate_browser_workflow",
            "description": "Navigate web pages, fill form fields, scrape page text, take screenshots, or click web elements.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Web page URL to navigate to or scrape"
                    },
                    "action": {
                        "type": "string",
                        "description": "Action: 'open', 'navigate', 'scrape', 'fill_form', 'click', 'click_apply', 'submit', 'screenshot'",
                        "enum": ["open", "navigate", "scrape", "fill_form", "click", "click_apply", "submit", "screenshot"]
                    },
                    "target": {
                        "type": "string",
                        "description": "Text to fill into form inputs, coordinates 'x,y' for click, or filename for screenshot"
                    }
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_daily_briefing",
            "description": "Get a 60-second summary briefing of system health, battery, current weather, and top 3 AI news headlines.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "manage_system_performance",
            "description": "Check CPU temperature, RAM usage, disk usage, and battery level, clean temporary files, list top processes, or terminate a process.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action: 'check', 'clean', 'top_processes', 'kill'",
                        "enum": ["check", "clean", "top_processes", "kill"]
                    },
                    "target": {
                        "type": "string",
                        "description": "Process name or PID to terminate if action is 'kill'"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "organize_downloads_folder",
            "description": "Organize files in the Downloads folder into classified category subfolders (Images, Documents, Executables, Archives, Code, Audio, Media).",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_schedule",
            "description": "Read, add, or remove calendar events from the local JSON calendar database (memory/calendar.json).",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format, 'today', or 'all'"
                    },
                    "action": {
                        "type": "string",
                        "description": "Action: 'read', 'add', 'delete'",
                        "enum": ["read", "add", "delete"]
                    },
                    "event_details": {
                        "type": "string",
                        "description": "Event description when adding or search keyword when deleting"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "modify_system_code",
            "description": "Modify EVE's own Python backend or UI frontend source code with automatic backup creation and AST syntax checking.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Target source file path (e.g. 'main.py', 'tools.py', 'dashboard/style.css')"
                    },
                    "new_content": {
                        "type": "string",
                        "description": "Complete new content string to write to the file"
                    }
                },
                "required": ["file_path", "new_content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "reboot_system",
            "description": "Restart the EVE process immediately to apply self-evolution code updates into active runtime memory.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

# Alias for backward compatibility
OLLAMA_TOOLS = GROQ_TOOLS

def execute_tool(tool_name: str, tool_args: dict = None) -> str:
    """Dispatches tool execution."""
    if tool_name in AVAILABLE_TOOLS:
        fn = AVAILABLE_TOOLS[tool_name]
        try:
            return fn(**tool_args) if tool_args else fn()
        except Exception as e:
            return f"Error executing tool '{tool_name}': {str(e)}"
    else:
        return f"Unknown tool '{tool_name}'"
