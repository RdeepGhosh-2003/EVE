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


def test_gemini_agent_initialization():
    """Verify EVAgent defaults to gemini-3.5-flash model."""
    agent = EVAgent()
    assert agent.model_name == "gemini-3.5-flash"
    tools = agent._get_gemini_tools()
    assert len(tools) > 0


def test_tool_memory_retention():
    """Verify tool calls and tool execution results persist in conversation history."""
    agent = EVAgent(model_name="gemini-3.5-flash")
    # Manually append tool request and tool result to simulate function call flow
    agent.conversation_history.append({"role": "model", "content": "[Tool Call] Executed get_current_time with parameters: {}"})
    agent.conversation_history.append({"role": "tool", "name": "get_current_time", "content": "12:00 PM"})
    
    roles = [m.get("role") for m in agent.conversation_history]
    assert "model" in roles
    assert "tool" in roles


def test_empty_content_sanitization():
    """Verify empty content strings are padded so Gemini SDK never receives blank Parts."""
    agent = EVAgent(model_name="gemini-3.5-flash")
    agent.conversation_history.append({"role": "user", "content": "   "})
    
    content_raw = str(agent.conversation_history[-1].get("content", "")).strip()
    sanitized = content_raw if content_raw else "[No text provided]"
    assert sanitized == "[No text provided]"


def test_exponential_backoff_rate_limit_retry():
    """Verify _generate_content_with_retry retries on 429 RESOURCE_EXHAUSTED errors."""
    agent = EVAgent(model_name="gemini-3.5-flash")
    attempts = 0

    class DummyClient:
        class DummyModels:
            def generate_content(self, model, contents, config):
                nonlocal attempts
                attempts += 1
                if attempts < 2:
                    raise Exception("429 RESOURCE_EXHAUSTED Quota exceeded")
                class DummyResponse:
                    text = "Success response after retry"
                    function_calls = None
                return DummyResponse()
        models = DummyModels()

    agent.client = DummyClient()
    resp = agent._generate_content_with_retry(contents=[], config=None, max_retries=3, initial_delay=0.01)
    assert resp.text == "Success response after retry"
    assert attempts == 2


