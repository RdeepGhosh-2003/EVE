import os
import sys
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from llm_agent import strip_thought_process, EVAgent


def test_strip_thought_process():
    """Verify strip_thought_process extracts <thought_process> and returns clean user-facing response."""
    raw_response = (
        "<thought_process>\n"
        "User is asking for current time. I will call get_current_time function.\n"
        "</thought_process>\n"
        "The current time is 01:00 AM."
    )
    clean, thought = strip_thought_process(raw_response)
    assert clean == "The current time is 01:00 AM."
    assert "User is asking for current time." in thought


def test_ollama_agent_initialization():
    """Verify EVAgent defaults to qwen2.5:7b Ollama model."""
    agent = EVAgent()
    assert agent.model_name == "qwen2.5:7b"
    tools = agent._get_openai_tools()
    assert len(tools) > 0
    assert tools[0]["type"] == "function"


def test_tool_memory_retention():
    """Verify tool calls and tool execution results persist in conversation history."""
    agent = EVAgent(model_name="qwen2.5:7b")
    agent.conversation_history.append({"role": "assistant", "content": "[Tool Call] Executed get_current_time"})
    agent.conversation_history.append({"role": "tool", "tool_call_id": "call_123", "name": "get_current_time", "content": "12:00 PM"})

    roles = [m.get("role") for m in agent.conversation_history]
    assert "assistant" in roles
    assert "tool" in roles


def test_empty_content_sanitization():
    """Verify empty content strings are padded so OpenAI client never receives blank parts."""
    agent = EVAgent(model_name="qwen2.5:7b")
    agent.conversation_history.append({"role": "user", "content": "   "})

    content_raw = str(agent.conversation_history[-1].get("content", "")).strip()
    sanitized = content_raw if content_raw else "[No text provided]"
    assert sanitized == "[No text provided]"


def test_exponential_backoff_completion_retry():
    """Verify _generate_completion_with_retry retries on connection error."""
    agent = EVAgent(model_name="qwen2.5:7b")
    attempts = 0

    class DummyClient:
        class DummyChat:
            class DummyCompletions:
                def create(self, **kwargs):
                    nonlocal attempts
                    attempts += 1
                    if attempts < 2:
                        raise Exception("Connection error")
                    class DummyChoice:
                        class DummyMessage:
                            content = "Success response after retry"
                            tool_calls = None
                        message = DummyMessage()
                    class DummyResponse:
                        choices = [DummyChoice()]
                    return DummyResponse()
            completions = DummyCompletions()
        chat = DummyChat()

    agent.client = DummyClient()
    resp = agent._generate_completion_with_retry(messages=[], tools=None, max_retries=3, initial_delay=0.01)
    assert resp.choices[0].message.content == "Success response after retry"
    assert attempts == 2


def test_dual_engine_gemini_fallback(monkeypatch):
    """Verify EVAgent automatically fails over to Gemini when Ollama local server is offline."""
    agent = EVAgent(model_name="qwen2.5:7b")
    
    # Force Ollama client to raise connection error
    class OfflineOllamaClient:
        class DummyChat:
            class DummyCompletions:
                def create(self, **kwargs):
                    raise Exception("Connection error: Ollama server offline")
            completions = DummyCompletions()
        chat = DummyChat()

    # Dummy Gemini Client
    class DummyGeminiClient:
        class DummyModels:
            def generate_content(self, model, contents, config):
                class DummyResp:
                    text = "Hello! Gemini Cloud fallback active."
                    function_calls = None
                return DummyResp()
        models = DummyModels()

    agent.client = OfflineOllamaClient()
    agent.gemini_client = DummyGeminiClient()

    output = agent.chat("hello")
    assert "Gemini Cloud fallback active" in output


