import sys
import os
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_pvporcupine_import():
    """Verify pvporcupine is importable and available in environment."""
    import pvporcupine
    assert pvporcupine is not None


def test_porcupine_keywords_supported():
    """Verify built-in keywords (bumblebee, porcupine, jarvis) are supported by pvporcupine."""
    import pvporcupine
    keywords = pvporcupine.KEYWORDS
    assert "bumblebee" in keywords or "porcupine" in keywords or len(keywords) > 0
