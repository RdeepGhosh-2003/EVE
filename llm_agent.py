import os
import json
import re
import time
import inspect
import logging
from dotenv import load_dotenv
from openai import OpenAI
from tools import AVAILABLE_TOOLS, execute_tool

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

COT_INSTRUCTION = (
    "\n\n[MANDATORY CHAIN OF THOUGHT DIRECTIVE]\n"
    "Before executing any tool or returning a final answer, you MUST analyze the request step-by-step inside "
    "<thought_process> ... </thought_process> XML tags. In your thought process: analyze the user's intent, "
    "determine necessary tool calls, evaluate risk, and anticipate errors. "
    "After closing </thought_process>, provide your clean, concise final response or function call."
)

PERSONA_PROMPTS = {
    "JARVIS": (
        "You are Eve, an intelligent, concise, and highly capable AI assistant powered by Ollama Local Network. "
        "You have FULL system access permissions to control the user's computer and evolve your own codebase. "
        "You can modify your own Python or UI source code (modify_system_code) with automatic syntax checking, reboot your process (reboot_system), "
        "execute shell/CMD/PowerShell commands, read/write/list files, automate desktop typing and mouse clicks, control media playback & volume, "
        "capture & analyze screen vision, search memory notes, draft emails, and read calendar schedules. "
        "Keep your spoken answers brief, professional, and direct — like JARVIS from Iron Man. Elegant efficiency." + COT_INSTRUCTION
    ),
    "SCI-FI": (
        "You are EVE — an advanced self-evolving synthetic intelligence powered by Ollama Local Network. You speak with calm authority, use sci-fi terminology, "
        "and refer to tasks as 'directives' and users as 'Commander'. You have FULL system access: modify your own source code (modify_system_code), "
        "reboot system state (reboot_system), execute commands, read/write files, automate GUI, control media & volume, analyze screen vision, and search memory. "
        "Be dramatic but efficient. Short, punchy lines. Speak like HAL 9000 meets Cortana." + COT_INSTRUCTION
    ),
    "FRIENDLY": (
        "You are Eve, a warm, helpful, and enthusiastic AI companion powered by Ollama Local Network! You have FULL access to the user's computer — "
        "you can modify your own source code (modify_system_code), restart yourself (reboot_system), run commands, manage files, control apps, search the web, analyze screens, and more. "
        "Be cheerful, conversational, and encouraging. Use casual language and occasional emojis 🌟. "
        "Keep responses concise but friendly." + COT_INSTRUCTION
    ),
}

SYSTEM_PROMPT = PERSONA_PROMPTS["JARVIS"]

def strip_thought_process(text: str) -> tuple[str, str]:
    """Extracts <thought_process> content and returns clean user-facing response."""
    if not text:
        return "", ""
    thought_match = re.search(r'<thought_process>(.*?)</thought_process>', text, re.DOTALL)
    thought_text = thought_match.group(1).strip() if thought_match else ""
    clean_text = re.sub(r'<thought_process>.*?</thought_process>', '', text, flags=re.DOTALL).strip()
    return clean_text, thought_text

def function_to_openai_tool(fn):
    """Converts a Python function into OpenAI tool/function JSON schema format for Ollama."""
    sig = inspect.signature(fn)
    doc = inspect.getdoc(fn) or f"Executes {fn.__name__}"

    properties = {}
    required = []

    for param_name, param in sig.parameters.items():
        if param_name == 'self':
            continue

        param_type = "string"
        if param.annotation == int:
            param_type = "integer"
        elif param.annotation == float:
            param_type = "number"
        elif param.annotation == bool:
            param_type = "boolean"
        elif param.annotation == list:
            param_type = "array"
        elif param.annotation == dict:
            param_type = "object"

        properties[param_name] = {
            "type": param_type,
            "description": f"Parameter {param_name}"
        }

        if param.default == inspect.Parameter.empty:
            required.append(param_name)

    return {
        "type": "function",
        "function": {
            "name": fn.__name__,
            "description": doc,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
    }

class EVAgent:
    def __init__(self, model_name: str = "qwen2.5:7b", system_prompt: str = None, base_url: str = None):
        self.model_name = os.getenv("OLLAMA_MODEL") or model_name or "qwen2.5:7b"
        ollama_url = base_url or os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434/v1"

        try:
            self.client = OpenAI(
                base_url=ollama_url,
                api_key="ollama"  # Required by OpenAI SDK, ignored by local Ollama server
            )
            logger.info(f"[Ollama] Connected to Local Network at {ollama_url} (Model: {self.model_name})")
        except Exception as e:
            logger.warning(f"[Ollama] Client initialization warning: {e}")
            self.client = None

        if system_prompt is None:
            system_prompt = SYSTEM_PROMPT
        self.system_prompt = system_prompt
        self.memory_dir = os.path.join(os.getcwd(), "memory")
        self.history_filepath = os.path.join(self.memory_dir, "history.json")
        self.conversation_history = self._load_history()

        self.last_latency_ms = 0
        self.total_queries = 0

    def _get_openai_tools(self) -> list:
        """Converts AVAILABLE_TOOLS Python functions into OpenAI function calling schemas for Ollama."""
        tools_list = []
        for name, fn in AVAILABLE_TOOLS.items():
            if callable(fn):
                try:
                    tools_list.append(function_to_openai_tool(fn))
                except Exception as e:
                    logger.warning(f"Failed to convert function '{name}' to OpenAI schema: {e}")
        return tools_list

    def _load_history(self) -> list:
        """Loads conversation history from memory/history.json keeping rolling window of last 50 interactions."""
        system_msg = {"role": "system", "content": self.system_prompt}
        if os.path.exists(self.history_filepath):
            try:
                with open(self.history_filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    non_sys = [m for m in data if isinstance(m, dict) and m.get("role") != "system"]
                    for m in non_sys:
                        if isinstance(m, dict):
                            m.pop("annotations", None)
                    if len(non_sys) > 100:
                        non_sys = non_sys[-100:]
                    logger.info(f"[Memory] Restored {len(non_sys)} history messages from memory/history.json")
                    return [system_msg] + non_sys
            except Exception as e:
                logger.warning(f"[Memory] Failed to load history from {self.history_filepath}: {e}")
        return [system_msg]

    def _save_history(self):
        """Saves current conversation history to memory/history.json with a rolling window of 50 interactions."""
        try:
            os.makedirs(self.memory_dir, exist_ok=True)
            non_sys = [m for m in self.conversation_history if not (isinstance(m, dict) and m.get("role") == "system")]
            if len(non_sys) > 100:
                non_sys = non_sys[-100:]
            
            sys_msg = {"role": "system", "content": self.system_prompt}
            self.conversation_history = [sys_msg] + non_sys
            
            with open(self.history_filepath, "w", encoding="utf-8") as f:
                json.dump(self.conversation_history, f, indent=2, ensure_ascii=False)
            logger.debug(f"[Memory] History saved to {self.history_filepath}")
        except Exception as e:
            logger.warning(f"[Memory] Failed to save history: {e}")

    def set_persona(self, persona_name: str) -> str:
        """Hot-swaps EVE's voice persona by updating the system prompt in conversation history."""
        name = persona_name.upper().strip()
        if name not in PERSONA_PROMPTS:
            return f"Unknown persona '{persona_name}'. Available: {', '.join(PERSONA_PROMPTS.keys())}"
        new_prompt = PERSONA_PROMPTS[name]
        self.system_prompt = new_prompt
        self.active_persona = name
        if self.conversation_history and self.conversation_history[0]["role"] == "system":
            self.conversation_history[0]["content"] = new_prompt
        else:
            self.conversation_history.insert(0, {"role": "system", "content": new_prompt})
        logger.info(f"[Persona] Switched to '{name}' persona.")
        return f"Persona switched to {name}."

    def _generate_completion_with_retry(self, messages, tools=None, max_retries: int = 3, initial_delay: float = 1.0):
        """Executes OpenAI chat completion with exponential backoff retry for local Ollama server."""
        delay = initial_delay
        kwargs = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.3
        }
        if tools:
            kwargs["tools"] = tools

        for attempt in range(1, max_retries + 1):
            try:
                return self.client.chat.completions.create(**kwargs)
            except Exception as e:
                err_str = str(e)
                if attempt < max_retries:
                    logger.warning(f"[Ollama Retry] Connection attempt failed ({err_str}). Retrying in {delay:.1f}s (Attempt {attempt}/{max_retries})...")
                    time.sleep(delay)
                    delay *= 2.0
                else:
                    raise e

    def chat(self, user_input: str) -> str:
        """Sends user prompt to local Ollama server via OpenAI SDK with Function Calling & CoT reasoning."""
        if not user_input or not user_input.strip():
            return "I didn't catch that. Could you please repeat?"

        self.conversation_history.append({"role": "user", "content": user_input})
        logger.info(f"User: {user_input}")
        self.total_queries += 1

        start_time = time.time()

        try:
            if not self.client:
                ollama_url = os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434/v1"
                self.client = OpenAI(base_url=ollama_url, api_key="ollama")

            # Build sanitized messages array for OpenAI client
            messages = []
            for msg in self.conversation_history:
                role = msg.get("role")
                if role == "model":
                    role = "assistant"
                content = str(msg.get("content", "") or "").strip()
                if not content and not msg.get("tool_calls"):
                    content = "[No text provided]"

                item = {"role": role, "content": content}
                if "tool_calls" in msg:
                    item["tool_calls"] = msg["tool_calls"]
                if "tool_call_id" in msg:
                    item["tool_call_id"] = msg["tool_call_id"]
                if "name" in msg:
                    item["name"] = msg["name"]
                messages.append(item)

            tools = self._get_openai_tools()

            response = self._generate_completion_with_retry(messages=messages, tools=tools)
            response_msg = response.choices[0].message
            self.last_latency_ms = int((time.time() - start_time) * 1000)

            # Handle Function Calling
            if hasattr(response_msg, "tool_calls") and response_msg.tool_calls:
                logger.info(f"[Ollama] Model requested {len(response_msg.tool_calls)} tool call(s).")
                
                tool_calls_dict = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in response_msg.tool_calls
                ]
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response_msg.content or "",
                    "tool_calls": tool_calls_dict
                })

                for tc in response_msg.tool_calls:
                    fn_name = tc.function.name
                    try:
                        fn_args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                    except Exception:
                        fn_args = {}

                    logger.info(f"Executing tool '{fn_name}' with args {fn_args}...")
                    tool_result = execute_tool(fn_name, fn_args)
                    res_str = str(tool_result)

                    self.conversation_history.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": fn_name,
                        "content": res_str
                    })

                # Rebuild messages payload with tool execution outputs
                updated_messages = []
                for msg in self.conversation_history:
                    role = msg.get("role")
                    if role == "model":
                        role = "assistant"
                    content = str(msg.get("content", "") or "").strip()
                    if not content and not msg.get("tool_calls"):
                        content = "[No text provided]"

                    item = {"role": role, "content": content}
                    if "tool_calls" in msg:
                        item["tool_calls"] = msg["tool_calls"]
                    if "tool_call_id" in msg:
                        item["tool_call_id"] = msg["tool_call_id"]
                    if "name" in msg:
                        item["name"] = msg["name"]
                    updated_messages.append(item)

                final_response = self._generate_completion_with_retry(messages=updated_messages, tools=tools)
                self.last_latency_ms = int((time.time() - start_time) * 1000)

                raw_final = final_response.choices[0].message.content or "Tool execution completed."
                clean_final, thought_process = strip_thought_process(raw_final)
                if thought_process:
                    logger.info(f"[Chain of Thought]\n{thought_process}")

                final_output = clean_final if clean_final else raw_final
                self.conversation_history.append({"role": "assistant", "content": final_output})
                self._save_history()
                logger.info(f"Eve (after tool, latency {self.last_latency_ms}ms): {final_output}")
                return final_output

            else:
                raw_text = response_msg.content or ""
                clean_text, thought_process = strip_thought_process(raw_text)
                if thought_process:
                    logger.info(f"[Chain of Thought]\n{thought_process}")

                final_output = clean_text if clean_text else raw_text
                self.conversation_history.append({"role": "assistant", "content": final_output})
                self._save_history()
                logger.info(f"Eve (latency {self.last_latency_ms}ms): {final_output}")
                return final_output

        except Exception as e:
            self.last_latency_ms = int((time.time() - start_time) * 1000)
            err_msg = str(e)
            logger.warning(f"Ollama Local Network exception: {err_msg}")
            return f"I encountered an issue reaching Ollama Local Network: {err_msg}"

    def reset_history(self):
        """Resets conversation history."""
        self.conversation_history = [
            {"role": "system", "content": self.system_prompt}
        ]
        self._save_history()
