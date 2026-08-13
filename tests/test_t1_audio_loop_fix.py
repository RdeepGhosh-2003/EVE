import sys
import os
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from audio_handler import is_hallucination, AudioHandler


def test_hallucination_filter():
    """Verify is_hallucination correctly identifies Whisper static hallucinations and passes real commands."""
    # Blocked hallucinations
    assert is_hallucination("")
    assert is_hallucination("thank you")
    assert is_hallucination("Thank you.")
    assert is_hallucination("thanks for watching")
    assert is_hallucination("subscribe")
    assert is_hallucination("am")

    # Valid user commands
    assert not is_hallucination("What is the weather today?")
    assert not is_hallucination("Open calculator")
    assert not is_hallucination("Search for latest AI news")
    assert not is_hallucination("Check system performance")


def test_audio_handler_energy_threshold():
    """Verify AudioHandler sets energy threshold to 600 for static noise rejection."""
    handler = AudioHandler()
    assert handler.recognizer.energy_threshold == 600
    assert handler.recognizer.dynamic_energy_threshold is True
