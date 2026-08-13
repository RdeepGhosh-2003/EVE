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
    """Verify EVAgent defaults to gemini-2.5-pro model."""
    agent = EVAgent(model_name="gemini-2.5-pro")
    assert agent.model_name == "gemini-2.5-pro"
    tools = agent._get_gemini_tools()
    assert len(tools) > 0
