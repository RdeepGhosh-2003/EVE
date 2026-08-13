import sys
import os
import json
import shutil
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from llm_agent import EVAgent

TEST_MEMORY_DIR = os.path.join(os.getcwd(), "memory")
TEST_HISTORY_FILE = os.path.join(TEST_MEMORY_DIR, "history.json")


def test_persistent_memory_file_creation(tmp_path):
    """Verify history.json is created and updated upon chat interactions."""
    memory_dir = tmp_path / "memory"
    history_file = memory_dir / "history.json"
    
    agent = EVAgent()
    agent.memory_dir = str(memory_dir)
    agent.history_filepath = str(history_file)
    agent.conversation_history = agent._load_history()

    agent.conversation_history.append({"role": "user", "content": "Hello EVE"})
    agent.conversation_history.append({"role": "assistant", "content": "Hello Commander!"})
    agent._save_history()

    assert os.path.exists(history_file)
    with open(history_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 3  # System + User + Assistant
    assert data[1]["content"] == "Hello EVE"
    assert data[2]["content"] == "Hello Commander!"


def test_persistent_memory_rolling_window(tmp_path):
    """Verify conversation history maintains rolling window of at most 100 non-system messages (50 turns)."""
    memory_dir = tmp_path / "memory"
    history_file = memory_dir / "history.json"
    
    agent = EVAgent()
    agent.memory_dir = str(memory_dir)
    agent.history_filepath = str(history_file)

    # Populate 120 messages (60 turns)
    history = [{"role": "system", "content": agent.system_prompt}]
    for i in range(60):
        history.append({"role": "user", "content": f"User query {i}"})
        history.append({"role": "assistant", "content": f"Assistant response {i}"})

    agent.conversation_history = history
    agent._save_history()

    # Re-load
    restored_agent = EVAgent()
    restored_agent.memory_dir = str(memory_dir)
    restored_agent.history_filepath = str(history_file)
    restored_agent.conversation_history = restored_agent._load_history()

    # System message (1) + 100 non-system messages = 101 total
    assert len(restored_agent.conversation_history) == 101
    assert restored_agent.conversation_history[1]["content"] == "User query 10"  # First 10 pairs trimmed
    assert restored_agent.conversation_history[-1]["content"] == "Assistant response 59"


def test_persistent_memory_reset(tmp_path):
    """Verify reset_history clears history.json back to system prompt only."""
    memory_dir = tmp_path / "memory"
    history_file = memory_dir / "history.json"

    agent = EVAgent()
    agent.memory_dir = str(memory_dir)
    agent.history_filepath = str(history_file)
    agent.conversation_history.append({"role": "user", "content": "Test"})
    agent._save_history()

    agent.reset_history()

    with open(history_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 1
    assert data[0]["role"] == "system"
