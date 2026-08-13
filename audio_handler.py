import os
import io
import time
import asyncio
import logging
from dotenv import load_dotenv
import speech_recognition as sr
from groq import Groq
import edge_tts
import pygame

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HALLUCINATION_BLOCKLIST = {
    "", "thank you.", "thank you", "thanks for watching", "subscribe",
    "thanks.", "thanks", "am", "you", "so", "bye", "mb", "thank you very much.",
    "subtitles by the amara.org community", "subtitles", "undertekster av amara.org-gemenskapen",
    "undertekster", "undertekster av amara.org"
}

def is_hallucination(text: str) -> bool:
    """Checks if transcribed text is a Whisper hallucination or background static artifact."""
    if not text:
        return True
    cleaned = text.lower().strip()
    if cleaned in HALLUCINATION_BLOCKLIST:
        return True
    # Filter out non-ASCII garbage
    ascii_chars = sum(1 for c in cleaned if c.isascii())
    if len(cleaned) > 0 and (ascii_chars / len(cleaned)) < 0.65:
        return True
    return False

class AudioHandler:
    def __init__(self, amplitude_callback=None, error_callback=None):
        self.amplitude_callback = amplitude_callback
        self.error_callback = error_callback
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            logger.warning("GROQ_API_KEY not found in environment or .env file!")
        self.groq_client = Groq(api_key=api_key) if api_key else None
        
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 600
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self.recognizer.phrase_time_limit = 10

        self.is_speaking = False
        self.interrupted = False
        self.mic_busy = False

        self.oww_model = None
        try:
            import openwakeword
            from openwakeword.model import Model
            self.oww_model = Model(inference_framework="onnx")
            logger.info("[OpenWakeWord] Initialized local open-source wake word model engine.")
        except Exception as e:
            logger.warning(f"[OpenWakeWord] Open-source wake word model init fallback: {e}")

        try:
            pygame.mixer.init()
        except Exception as e:
            logger.warning(f"Failed to initialize pygame mixer: {e}")

    def compute_rms_chunks(self, filename: str, chunk_duration_ms: int = 50):
        """Computes normalized RMS audio amplitude chunks for 50ms intervals."""
        try:
            import soundfile as sf
            import numpy as np
            data, samplerate = sf.read(filename)
            if data.ndim > 1:
                data = data.mean(axis=1)
            chunk_samples = int(samplerate * (chunk_duration_ms / 1000.0))
            if chunk_samples <= 0:
                return [], 50
            num_chunks = max(1, len(data) // chunk_samples)
            rms_list = []
            for i in range(num_chunks):
                chunk = data[i * chunk_samples : (i + 1) * chunk_samples]
                rms = float(np.sqrt(np.mean(chunk**2))) if len(chunk) > 0 else 0.0
                rms_list.append(rms)
            max_rms = max(rms_list) if rms_list and max(rms_list) > 0 else 1.0
            normalized = [min(1.0, r / max_rms) for r in rms_list]
            return normalized, chunk_duration_ms
        except Exception as e:
            logger.warning(f"Could not compute audio amplitude RMS: {e}")
            return [], 50

    def listen_for_wakeword(self) -> bool:
        """Blocks passively and waits for wake word using OpenWakeWord local model or energy gate fallback."""
        if self.oww_model:
            pa = None
            audio_stream = None
            try:
                import pyaudio
                import numpy as np

                CHUNK = 1280
                pa = pyaudio.PyAudio()
                audio_stream = pa.open(
                    rate=16000,
                    channels=1,
                    format=pyaudio.paInt16,
                    input=True,
                    frames_per_buffer=CHUNK
                )
                logger.info("[OpenWakeWord] Blocking & listening passively for open-source wake word...")
                start_time = time.time()

                while True:
                    if time.time() - start_time > 10:
                        return False

                    data = audio_stream.read(CHUNK, exception_on_overflow=False)
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    prediction = self.oww_model.predict(audio_data)

                    for mdl_name, score in prediction.items():
                        if score >= 0.35:
                            logger.info(f"[OpenWakeWord] Local Wake word detected! Model: '{mdl_name}', score={score:.2f}")
                            return True

            except Exception as e:
                logger.warning(f"[OpenWakeWord] Passive listener exception, fallback to energy gate: {e}")
                time.sleep(0.5)
            finally:
                if audio_stream is not None:
                    try:
                        audio_stream.stop_stream()
                        audio_stream.close()
                    except Exception as stream_err:
                        logger.warning(f"Error closing audio stream: {stream_err}")
                if pa is not None:
                    try:
                        pa.terminate()
                    except Exception as pa_err:
                        logger.warning(f"Error terminating PyAudio instance: {pa_err}")

        # Fallback passive energy gate when model is loading or omitted:
        try:
            with sr.Microphone() as source:
                self.recognizer.energy_threshold = 600
                self.recognizer.dynamic_energy_threshold = True
                logger.info("[Passive Gate] Calibrating ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                logger.info("[Passive Gate] Waiting for voice activity...")
                audio_data = self.recognizer.listen(source, phrase_time_limit=5, timeout=5)
                return True
        except sr.WaitTimeoutError:
            return False
        except Exception as e:
            logger.warning(f"[Passive Gate] Mic check: {e}")
            time.sleep(0.5)
            return False

    def record_and_transcribe(self) -> str:
        """Records user command ONE time and transcribes using Groq Whisper API, applying hallucination filtering."""
        self.mic_busy = True
        try:
            try:
                with sr.Microphone() as source:
                    self.recognizer.energy_threshold = 600
                    self.recognizer.dynamic_energy_threshold = True
                    logger.info("[Eve] Recording command ONE time via Groq Whisper...")
                    audio_data = self.recognizer.listen(source, phrase_time_limit=10, timeout=8)
            except sr.WaitTimeoutError:
                logger.info("[Eve] Command recording timed out with no speech.")
                return ""
            except Exception as mic_err:
                logger.error(f"[Audio Lock Error] Mic stream busy or inaccessible: {mic_err}")
                if self.error_callback:
                    try:
                        self.error_callback(f"[ERROR] Mic stream busy: {mic_err}")
                    except Exception:
                        pass
                return ""

            api_key = os.getenv("GROQ_API_KEY")
            if api_key:
                if not self.groq_client:
                    self.groq_client = Groq(api_key=api_key)

                logger.info("[Eve] Transcribing recorded audio via Groq 'whisper-large-v3'...")
                wav_bytes = audio_data.get_wav_data(convert_rate=16000, convert_width=2)
                transcription_res = self.groq_client.audio.transcriptions.create(
                    file=("speech.wav", wav_bytes),
                    model="whisper-large-v3",
                    response_format="text"
                )
                raw_text = transcription_res.strip() if isinstance(transcription_res, str) else getattr(transcription_res, "text", "").strip()
            else:
                logger.info("[Eve] GROQ_API_KEY missing/deleted. Using free Google SpeechRecognition fallback...")
                raw_text = self.recognizer.recognize_google(audio_data).strip()
            
            # Apply Hallucination Filter
            if is_hallucination(raw_text):
                logger.info(f"[Hallucination Blocked] Filtered out garbage transcription: '{raw_text}'")
                return ""

            logger.info(f"[Eve] Transcribed Valid Command: '{raw_text}'")
            return raw_text

        except Exception as e:
            logger.error(f"[Eve] Error during Groq transcription: {e}")
            return ""
        finally:
            self.mic_busy = False

    listen_and_transcribe = record_and_transcribe

    async def _generate_tts_async(self, text: str, voice: str, output_filename: str):
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_filename)

    def speak_text(self, text: str, voice: str = "en-US-AvaNeural", output_filename: str = "temp_eve_response.mp3"):
        """Generates TTS audio and plays back with barge-in interruption capability & amplitude callbacks."""
        if not text or not text.strip():
            return

        logger.info(f"[Eve Speaking]: {text}")
        try:
            asyncio.run(self._generate_tts_async(text, voice, output_filename))
        except Exception as e:
            logger.error(f"Error generating Edge-TTS: {e}")
            print(f"Eve: {text}")
            return

        self.is_speaking = True
        self.interrupted = False

        try:
            rms_list, chunk_ms = self.compute_rms_chunks(output_filename)
            if not pygame.mixer.get_init():
                pygame.mixer.init()

            pygame.mixer.music.load(output_filename)
            pygame.mixer.music.play()
            start_time = time.time()

            while pygame.mixer.music.get_busy():
                if self.interrupted:
                    logger.info("[Barge-in Interrupt] User interrupted speech playback.")
                    pygame.mixer.music.stop()
                    break
                
                elapsed_ms = int((time.time() - start_time) * 1000)
                chunk_idx = elapsed_ms // chunk_ms
                if rms_list and chunk_idx < len(rms_list):
                    amp = rms_list[chunk_idx]
                    if self.amplitude_callback:
                        try:
                            self.amplitude_callback(amp)
                        except Exception:
                            pass
                time.sleep(0.04)

            pygame.mixer.music.unload()
        except Exception as e:
            logger.error(f"Error playing TTS audio: {e}")
        finally:
            self.is_speaking = False
            if self.amplitude_callback:
                try:
                    self.amplitude_callback(0.0)
                except Exception:
                    pass
            if os.path.exists(output_filename):
                try:
                    os.remove(output_filename)
                except Exception:
                    pass

    def stop_speaking(self):
        """Immediately stops ongoing speech playback."""
        if self.is_speaking:
            self.interrupted = True
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
