import re
import os
import sys
import tempfile
import logging
import io
import wave
from pathlib import Path
from typing import Tuple

logger = logging.getLogger(__name__)

def convert_audio_to_wav_bytes(audio_bytes: bytes) -> bytes:
    """
    Converts incoming browser microphone bytes (WebM, MP4, OGG, AAC, WAV)
    to standard 16kHz mono 16-bit PCM WAV bytes for SpeechRecognition / Whisper.
    """
    if not audio_bytes:
        return b""

    # If already a valid PCM WAV file
    if audio_bytes.startswith(b"RIFF") and b"WAVE" in audio_bytes[:16]:
        return audio_bytes

    # 1. Try pydub conversion
    try:
        from pydub import AudioSegment
        sound = AudioSegment.from_file(io.BytesIO(audio_bytes))
        sound = sound.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        out_buf = io.BytesIO()
        sound.export(out_buf, format="wav")
        return out_buf.getvalue()
    except Exception as e:
        logger.warning(f"Pydub audio conversion note: {e}")

    # 2. Try ffmpeg CLI if installed
    try:
        import subprocess
        with tempfile.NamedTemporaryFile(suffix=".raw", delete=False) as in_tmp:
            in_tmp.write(audio_bytes)
            in_path = in_tmp.name
        
        out_path = in_path + ".wav"
        cmd = ["ffmpeg", "-y", "-i", in_path, "-ar", "16000", "-ac", "1", "-f", "wav", out_path]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
        if res.returncode == 0 and os.path.exists(out_path):
            with open(out_path, "rb") as f:
                data = f.read()
            os.unlink(in_path)
            os.unlink(out_path)
            return data
    except Exception as e:
        logger.warning(f"FFmpeg CLI note: {e}")

    return audio_bytes

def detect_language_from_text(text: str) -> str:
    """
    Detects language based on script inspection and vocabulary.
    Defaults strongly to Tamil ('ta').
    """
    if not text:
        return "ta"
    
    tamil_chars = len(re.findall(r'[\u0B80-\u0BFF]', text))
    total_alpha = len(re.findall(r'[\w]', text))
    
    if total_alpha > 0 and (tamil_chars / total_alpha) > 0.05:
        return "ta"
    
    ta_transliterated = ["vanakkam", "nandri", "kuzhandhaigal", "nankodai", "arasiyil", "panam", "seithu", "eppadi", "varam", "panga", "kelvi", "vari", "kodukka"]
    words = text.lower().split()
    if any(w in ta_transliterated for w in words):
        return "ta"
        
    english_phrases = ["donation usage", "tax exemption", "80g certificate", "sponsor child", "visiting hours", "contact info", "galaxy rocket"]
    clean_lower = text.lower()
    if any(p in clean_lower for p in english_phrases):
        return "en"

    return "ta"

class STTService:
    def __init__(self):
        self._whisper_model = None
        self._load_stt_engine()

    def _load_stt_engine(self):
        try:
            import faster_whisper
            logger.info("Loading faster-whisper STT model (Tamil optimized)...")
            self._whisper_model = faster_whisper.WhisperModel("tiny", device="cpu", compute_type="int8")
            logger.info("faster-whisper model loaded successfully.")
        except Exception as e:
            logger.info(f"Faster-whisper not available ({e}). Using SpeechRecognition Speech API.")
            self._whisper_model = None

    def transcribe_audio_bytes(self, audio_bytes: bytes, filename: str = "audio.wav") -> Tuple[str, str]:
        """
        Transcribes raw audio bytes to text with forced Tamil ('ta-IN') language priority.
        Converts WebM/MP4/OGG browser mic input to PCM WAV automatically.
        """
        if not audio_bytes or len(audio_bytes) < 100:
            return "", "ta"

        # Convert WebM / MP4 / OGG browser audio to standard PCM WAV bytes
        wav_bytes = convert_audio_to_wav_bytes(audio_bytes)

        if self._whisper_model:
            try:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp.write(wav_bytes)
                    tmp_path = tmp.name
                
                segments, info = self._whisper_model.transcribe(tmp_path, language="ta", beam_size=5)
                transcription = " ".join([segment.text for segment in segments]).strip()
                os.unlink(tmp_path)
                if transcription:
                    return transcription, "ta"
            except Exception as ex:
                logger.warning(f"Whisper transcription failed, falling back: {ex}")

        # SpeechRecognition Google Speech API fallback (ta-IN)
        try:
            import speech_recognition as sr
            r = sr.Recognizer()
            with sr.AudioFile(io.BytesIO(wav_bytes)) as source:
                audio_data = r.record(source)
                
                # 1. Try Tamil (ta-IN) first
                try:
                    text = r.recognize_google(audio_data, language="ta-IN")
                    if text:
                        logger.info(f"SpeechRecognition ta-IN decoded: '{text}'")
                        return text, "ta"
                except Exception:
                    pass

                # 2. Try English (en-IN) second
                try:
                    text = r.recognize_google(audio_data, language="en-IN")
                    if text:
                        lang = detect_language_from_text(text)
                        return text, lang
                except Exception:
                    pass
        except Exception as err:
            logger.warning(f"SpeechRecognition audio file read note: {err}")

        return "", "ta"
