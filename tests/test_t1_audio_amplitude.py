import sys
import os
import wave
import struct
import tempfile
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from audio_handler import AudioHandler


def test_compute_rms_chunks_wav(tmp_path):
    """Verify compute_rms_chunks correctly computes normalized RMS audio amplitude for 50ms frames."""
    wav_path = tmp_path / "test_audio.wav"
    sample_rate = 16000
    duration_s = 1.0  # 1 second = 20 x 50ms chunks
    
    # Generate 440 Hz sine wave
    import math
    frames = []
    for i in range(int(sample_rate * duration_s)):
        value = int(16000 * math.sin(2 * math.pi * 440 * i / sample_rate))
        frames.append(struct.pack('<h', value))
    
    with wave.open(str(wav_path), 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b''.join(frames))

    handler = AudioHandler()
    rms_chunks, chunk_ms = handler.compute_rms_chunks(str(wav_path), chunk_duration_ms=50)

    assert len(rms_chunks) > 0
    assert chunk_ms == 50
    for val in rms_chunks:
        assert 0.0 <= val <= 1.0


def test_audio_amplitude_callback(tmp_path):
    """Verify amplitude_callback receives normalized amplitude values during audio processing."""
    received = []

    def dummy_callback(amp):
        received.append(amp)

    handler = AudioHandler(amplitude_callback=dummy_callback)
    
    # Simulate callback
    handler.amplitude_callback(0.75)
    assert len(received) == 1
    assert received[0] == 0.75
