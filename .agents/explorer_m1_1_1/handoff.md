# Handoff Report — Explorer M1.1 (R1 & R2 Intelligence Tools Analysis)

**Agent Identity**: `explorer_m1_1_1` (teamwork_preview_explorer)  
**Target File**: `c:\MY AI\tools.py`  
**Scope**: Milestone M1.1 — R1 (`fetch_live_news`, `get_daily_briefing`) & R2 (`search_web_realtime`)

---

## 1. Observation

### 1.1 Existing Codebase & `tools.py` Structure
- `c:\MY AI\tools.py` exists (841 lines, 33,741 bytes).
- Imports present: `os`, `io`, `re`, `base64`, `datetime`, `subprocess`, `platform`, `webbrowser`, `logging`, `urllib.request`, `urllib.parse`, `xml.etree.ElementTree as ET`, `psutil`, `groq`, `pyautogui`, `PIL`, `MemoryHandler`.
- Key registries present in `tools.py`:
  - `AVAILABLE_TOOLS` dict (lines 477-496) mapping function names to implementations.
  - `GROQ_TOOLS` list (lines 499-826) containing JSON schemas for OpenAI/Groq function calling.
  - `execute_tool(tool_name: str, tool_args: dict = None)` dispatcher (lines 831-840).

### 1.2 Current Implementation of R1 Tools in `tools.py`
- **`fetch_live_news(topic: str = "ai")` (lines 344-367)**:
  ```python
  def fetch_live_news(topic: str = "ai") -> str:
      """Fetches real-time World and AI news headlines via live Google News RSS feed."""
      try:
          q = "artificial+intelligence" if "ai" in topic.lower() else urllib.parse.quote(topic)
          rss_url = f"https://news.google.com/rss/search?q={q}&hl=en-IN&gl=IN&ceid=IN:en"
          req = urllib.request.Request(rss_url, headers={"User-Agent": "Mozilla/5.0"})
          
          with urllib.request.urlopen(req, timeout=5) as resp:
              xml_data = resp.read()
              root = ET.fromstring(xml_data)
              items = root.findall('./channel/item')[:5]

              news_list = []
              for idx, item in enumerate(items, 1):
                  title = item.find('title').text if item.find('title') is not None else 'Headline'
                  news_list.append(f"{idx}. {title}")

              result = f"Top Live {topic.upper()} News Headlines:\n" + "\n".join(news_list)
              logger.info(f"[Tool: fetch_live_news] Retrieved {len(news_list)} headlines for '{topic}'")
              return result
      except Exception as e:
          logger.error(f"Failed to fetch news: {e}")
          return f"Failed to fetch live news: {str(e)}"
  ```
- **`get_daily_briefing()` (lines 412-427)**:
  ```python
  def get_daily_briefing() -> str:
      """Aggregates system health, weather forecast, battery level, and top 3 AI headlines into a 60-second morning briefing summary."""
      try:
          cpu = psutil.cpu_percent(interval=None)
          mem = psutil.virtual_memory().percent
          news_text = fetch_live_news("ai")
          headlines = news_text.split('\n')[1:4]

          briefing = (
              f"Good day! Here is your EVE Daily Briefing:\n"
              f"System Health: CPU Load is at {cpu}%, Memory usage is at {mem}%.\n"
              f"Top AI Intelligence Headlines:\n" + "\n".join(headlines)
          )
          return briefing
      except Exception as e:
          return f"Failed to generate daily briefing: {str(e)}"
  ```

### 1.3 Current Implementation of R2 Tool in `tools.py`
- **`search_web_realtime(query: str)` (lines 368-389)**:
  ```python
  def search_web_realtime(query: str) -> str:
      """Searches the live web using DuckDuckGo to get real-time information, breaking news, or search results."""
      try:
          q_enc = urllib.parse.quote(query)
          url = f"https://html.duckduckgo.com/html/?q={q_enc}"
          req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
          
          with urllib.request.urlopen(req, timeout=6) as resp:
              html = resp.read().decode('utf-8', errors='ignore')
              snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', html, re.DOTALL)
              clean_snippets = [re.sub(r'<[^>]+>', '', s).strip() for s in snippets[:3]]

              if clean_snippets:
                  result = f"Real-time Web Search Results for '{query}':\n" + "\n---\n".join(clean_snippets)
                  logger.info(f"[Tool: search_web_realtime] Found {len(clean_snippets)} search results for '{query}'")
                  return result
              else:
                  return f"No search results found for '{query}'."
      except Exception as e:
          logger.error(f"Failed live web search: {e}")
          return f"Failed to perform live web search: {str(e)}"
  ```

### 1.4 Dependencies (`c:\MY AI\requirements.txt`)
- Standard library modules used: `urllib.request`, `urllib.parse`, `xml.etree.ElementTree`, `re`, `html`, `datetime`.
- Third-party packages present in `requirements.txt`: `requests`, `psutil`, `groq`, `pyautogui`, `fastapi`, `uvicorn`, `websockets`.

---

## 2. Logic Chain

### 2.1 Analysis of R1: News Fetching & Daily Briefing

1. **`fetch_live_news(topic)` Gaps**:
   - **Single Feed Vulnerability**: Currently relies solely on `https://news.google.com/rss/search?q=...`. If Google News RSS times out or returns HTTP 429/503, the tool fails without trying fallback RSS feeds (such as HackerNews RSS `https://news.ycombinator.com/rss` or TechCrunch AI RSS `https://techcrunch.com/category/artificial-intelligence/feed/`).
   - **HTML Entity Artifacts**: Google News RSS titles frequently contain raw unescaped HTML entities (e.g. `&quot;`, `&#39;`, `&amp;`). Applying `html.unescape()` is required for clean display and TTS reading.
   - **Source & Link Attribution**: Currently only extracts title text. Including source name or URL link enhances LLM context and HUD news ticker display.

2. **`get_daily_briefing()` Gaps**:
   - **Missing Battery Status**: `ORIGINAL_REQUEST.md` (R4/R1) & `PROJECT.md` specify monitoring battery level (<20% alert threshold). `get_daily_briefing()` currently checks CPU and RAM, but omits battery state (`psutil.sensors_battery()`).
   - **Missing Weather Info**: `PROJECT.md` (Feature 2) states briefing aggregates "system metrics, weather, and AI news". Weather is currently absent. Adding a lightweight HTTP call to `https://wttr.in/?format=%C+%t` (with 3s timeout and fallback) satisfies this requirement.
   - **Fragile Line Splitting**: `news_text.split('\n')[1:4]` assumes `news_text` always has at least 4 lines. If news fetching fails or returns fewer lines, string splitting produces distorted output or index slices of error messages.
   - **Formatting & Structure**: Briefing needs clean, structured sections (System Health, Battery, Weather, Top AI Headlines) optimized for voice summary output.

### 2.2 Analysis of R2: DuckDuckGo Real-Time Web Search

1. **HTTP Method Defect (GET vs. POST)**:
   - `PROJECT.md` Feature 3 explicitly mandates: `search_web_realtime(query)` scrapes **DuckDuckGo POST** for live results.
   - Current implementation uses HTTP GET (`https://html.duckduckgo.com/html/?q=...`). DuckDuckGo's HTML search interface (`https://html.duckduckgo.com/html/`) is designed to accept HTTP POST requests with `Content-Type: application/x-www-form-urlencoded` and payload `q=<query>`.
   - HTTP GET on `html.duckduckgo.com` frequently triggers bot protection or redirects, whereas HTTP POST with a modern desktop User-Agent header returns the raw search result HTML reliably without API keys.

2. **Incomplete Field Extraction**:
   - Current regex `re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', html, re.DOTALL)` extracts ONLY snippets. Title and URL are lost.
   - A complete search result requires **Title**, **URL**, and **Snippet** for each result item.
   - Extraction strategy:
     - URL parameter in DDG link is encoded in `/l/?uddg=<actual_url>`. Decoding with `urllib.parse.unquote()` yields the actual destination URL.
     - Titles are contained in `<a class="result__a" ...>(.*?)</a>`.
     - Snippets are contained in `<a class="result__snippet" ...>(.*?)</a>` or `<td class="result-snippet">`.
     - All extracted strings must be stripped of HTML tags (`re.sub(r'<[^>]+>', '', text)`) and unescaped (`html.unescape()`).

3. **Fallback Endpoint**:
   - Primary: POST to `https://html.duckduckgo.com/html/`.
   - Secondary Fallback: POST to `https://lite.duckduckgo.com/lite/`.

---

## 3. Caveats

- **Network Dependency**: Both R1 and R2 depend on active internet connectivity. All HTTP calls MUST specify strict timeouts (3 to 6 seconds) to prevent blocking the LLM agent or FastAPI server engine.
- **Scraper Invalidation**: Web scrapers dependent on HTML regex patterns can break if DuckDuckGo updates class names. Robust fallback regexes and fallback endpoints (`lite.duckduckgo.com`) mitigate this risk.
- **Execution Constraints**: Command execution via `run_command` required user confirmation in this workspace. All recommendations are derived from static analysis of source files and standard library contract verification.

---

## 4. Conclusion & Recommendations

### 4.1 Recommended Refactored Implementation for `fetch_live_news` & `get_daily_briefing` (R1)

```python
import html

def fetch_live_news(topic: str = "ai") -> str:
    """Fetches real-time World and AI news headlines via live RSS feeds with fallback."""
    topic_clean = topic.lower().strip()
    
    # Define primary RSS URL based on topic
    if "ai" in topic_clean or "artificial" in topic_clean:
        rss_urls = [
            "https://news.google.com/rss/search?q=artificial+intelligence&hl=en-IN&gl=IN&ceid=IN:en",
            "https://techcrunch.com/category/artificial-intelligence/feed/",
            "https://news.ycombinator.com/rss"
        ]
    elif "world" in topic_clean:
        rss_urls = [
            "https://news.google.com/rss/search?q=world+news&hl=en-IN&gl=IN&ceid=IN:en",
            "https://news.ycombinator.com/rss"
        ]
    else:
        q_enc = urllib.parse.quote(topic)
        rss_urls = [
            f"https://news.google.com/rss/search?q={q_enc}&hl=en-IN&gl=IN&ceid=IN:en",
            "https://news.ycombinator.com/rss"
        ]

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
                    result = f"Top Live {topic.upper()} News Headlines:\n" + "\n".join(news_list)
                    logger.info(f"[Tool: fetch_live_news] Retrieved {len(news_list)} headlines for '{topic}' from {rss_url}")
                    return result
        except Exception as e:
            logger.warning(f"[fetch_live_news] Feed failed ({rss_url}): {e}")
            continue

    return f"Unable to fetch live news headlines for '{topic}' at this time."

def get_daily_briefing() -> str:
    """Aggregates system health, weather forecast, battery level, and top 3 AI headlines into a morning briefing summary."""
    try:
        # 1. System Health & Battery Metrics
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory().percent
        bat = psutil.sensors_battery()
        if bat:
            bat_str = f"{int(bat.percent)}% ({'Charging' if bat.power_plugged else 'Discharging'})"
        else:
            bat_str = "AC Desktop Power"

        # 2. Weather Info (with 3s timeout fallback)
        weather_str = "Weather information currently unavailable."
        try:
            w_req = urllib.request.Request("https://wttr.in/?format=%C+%t", headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(w_req, timeout=3) as w_resp:
                weather_data = w_resp.read().decode('utf-8').strip()
                if weather_data and not weather_data.startswith("<!DOCTYPE"):
                    weather_str = weather_data
        except Exception as we:
            logger.debug(f"Weather fetch failed: {we}")

        # 3. Top AI Headlines (safely parsed)
        news_text = fetch_live_news("ai")
        lines = [line.strip() for line in news_text.split('\n') if line.strip() and not line.startswith("Top Live")]
        top_headlines = lines[:3] if lines else ["No live headlines available."]

        briefing = (
            f"Good day! Here is your EVE Daily Briefing:\n"
            f"- System Health: CPU Load at {cpu}%, RAM Usage at {mem}%, Battery: {bat_str}.\n"
            f"- Current Weather: {weather_str}.\n"
            f"- Top AI Intelligence Headlines:\n" + "\n".join(top_headlines)
        )
        return briefing
    except Exception as e:
        logger.error(f"Failed to generate daily briefing: {e}")
        return f"Failed to generate daily briefing: {str(e)}"
```

---

### 4.2 Recommended Refactored Implementation for `search_web_realtime` (R2 DuckDuckGo POST Scraper)

```python
def search_web_realtime(query: str) -> str:
    """Searches the live web using DuckDuckGo POST scraper to get real-time information, title, URL, and snippets."""
    try:
        url = "https://html.duckduckgo.com/html/"
        data = urllib.parse.urlencode({"q": query}).encode("utf-8")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        
        req = urllib.request.Request(url, data=data, headers=headers)
        
        with urllib.request.urlopen(req, timeout=6) as resp:
            html_raw = resp.read().decode('utf-8', errors='ignore')
            
            # Regex for links & titles and snippets in DDG HTML POST response
            # DDG HTML result anchors: <a class="result__a" href="...">Title</a>
            # DDG HTML snippet anchors: <a class="result__snippet...">Snippet</a>
            
            titles_urls = re.findall(r'<a class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html_raw, re.DOTALL)
            snippets = re.findall(r'<a class="result__snippet[^"]*"[^>]*>(.*?)</a>', html_raw, re.DOTALL)
            
            results = []
            max_results = min(len(titles_urls), len(snippets), 4)
            
            for i in range(max_results):
                raw_url, raw_title = titles_urls[i]
                raw_snippet = snippets[i]
                
                # Extract actual target URL if DDG redirect wrapper is present (/l/?uddg=...)
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
                return f"No relevant web search results found for '{query}'."

    except Exception as e:
        logger.error(f"Failed live web search: {e}")
        return f"Failed to perform live web search: {str(e)}"
```

---

## 5. Verification Method

To verify the proposed implementations during synthesis or patch phase:

1. **Imports & Code Integrity Check**:
   - Run Python syntax check: `python -m py_compile tools.py` (Must exit with code 0).
2. **Tool Dispatcher Verification**:
   - Test execution via `execute_tool`:
     ```python
     from tools import execute_tool
     print(execute_tool("fetch_live_news", {"topic": "ai"}))
     print(execute_tool("get_daily_briefing", {}))
     print(execute_tool("search_web_realtime", {"query": "latest AI news"}))
     ```
3. **Schema Alignment Verification**:
   - Verify `"fetch_live_news"`, `"get_daily_briefing"`, and `"search_web_realtime"` exist in `AVAILABLE_TOOLS` dict and `GROQ_TOOLS` list.
   - Confirm required arguments match function signature.
