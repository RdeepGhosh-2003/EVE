import sys
import os
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_openwakeword_engine_initialization():
    """Verify AudioHandler initializes openwakeword or falls back cleanly to passive energy gate."""
    from audio_handler import AudioHandler
    handler = AudioHandler()
    assert hasattr(handler, "oww_model")
    assert hasattr(handler, "listen_for_wakeword")
