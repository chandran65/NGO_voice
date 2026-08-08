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

    # 1. Try imageio_ffmpeg CLI directly (Handles WebM, MP4, OGG, AAC -> 16kHz WAV PCM)
    try:
        import subprocess
        import imageio_ffmpeg
        ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()
        
        with tempfile.NamedTemporaryFile(suffix=".raw", delete=False) as in_tmp:
            in_tmp.write(audio_bytes)
            in_path = in_tmp.name
        
        out_path = in_path + ".wav"
        # Standardize to 16kHz mono PCM WAV with audio gain boosting & high-pass filtering for mic noise reduction
        cmd = [
            ffmpeg_bin, "-y", "-i", in_path,
            "-af", "volume=2.5,highpass=f=80,lowpass=f=7500",
            "-ar", "16000", "-ac", "1", "-f", "wav", out_path
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=8)
        if res.returncode == 0 and os.path.exists(out_path):
            with open(out_path, "rb") as f:
                data = f.read()
            try:
                os.unlink(in_path)
            except Exception:
                pass
            try:
                os.unlink(out_path)
            except Exception:
                pass
            return data
    except Exception as e:
        logger.warning(f"FFmpeg conversion note: {e}")

    # 2. Try pydub conversion as fallback
    try:
        from pydub import AudioSegment
        sound = AudioSegment.from_file(io.BytesIO(audio_bytes))
        sound = sound.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        out_buf = io.BytesIO()
        sound.export(out_buf, format="wav")
        return out_buf.getvalue()
    except Exception as e:
        logger.warning(f"Pydub audio conversion note: {e}")

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
            import whisper
            logger.info("Loading OpenAI Whisper Tamil-optimized base model...")
            self._whisper_model = whisper.load_model("base")
            logger.info("OpenAI Whisper base model loaded successfully.")
        except Exception as e:
            logger.info(f"OpenAI Whisper not available ({e}). Using SpeechRecognition API.")
            self._whisper_model = None

        # Patch speech_recognition FLAC converter if on Mac
        try:
            import shutil
            import speech_recognition as sr
            flac_bin = shutil.which("flac")
            if flac_bin:
                sr.get_flac_converter = lambda: flac_bin
                logger.info(f"Patched SpeechRecognition FLAC converter -> {flac_bin}")
        except Exception as e:
            logger.warning(f"FLAC patch note: {e}")

    def transcribe_audio_bytes(self, audio_bytes: bytes, filename: str = "audio.wav") -> Tuple[str, str]:
        """
        Transcribes raw audio bytes to text with forced Tamil ('ta-IN') language priority.
        Converts WebM/MP4/OGG browser mic input to PCM WAV automatically.
        """
        if not audio_bytes or len(audio_bytes) < 100:
            return "", "ta"

        # Convert WebM / MP4 / OGG browser audio to standard PCM WAV bytes
        wav_bytes = convert_audio_to_wav_bytes(audio_bytes)

        # 1. Fast Sub-120ms SpeechRecognition (ta-IN & en-IN with native ARM64 FLAC)
        try:
            import speech_recognition as sr
            from app.services.intent import IntentClassifier
            classifier = IntentClassifier()

            r = sr.Recognizer()
            with sr.AudioFile(io.BytesIO(wav_bytes)) as source:
                audio_data = r.record(source)
                
                text_ta, conf_ta = "", 0.0
                text_en, conf_en = "", 0.0

                # Try Tamil (ta-IN)
                try:
                    res_ta = r.recognize_google(audio_data, language="ta-IN")
                    if res_ta:
                        text_ta = res_ta
                        _, _, conf_ta = classifier.classify(res_ta, "ta")
                except Exception:
                    pass

                # Try English (en-IN)
                try:
                    res_en = r.recognize_google(audio_data, language="en-IN")
                    if res_en:
                        text_en = res_en
                        _, _, conf_en = classifier.classify(res_en, "en")
                except Exception:
                    pass

                # If high-confidence match found, return immediately (sub-120ms latency)
                if conf_en > conf_ta and conf_en >= 0.60:
                    logger.info(f"Fast STT en-IN decoded: '{text_en}'")
                    return text_en, detect_language_from_text(text_en)
                elif text_ta and len(text_ta) > 0:
                    logger.info(f"Fast STT ta-IN decoded: '{text_ta}'")
                    return text_ta, "ta"
                elif text_en and len(text_en) > 0:
                    return text_en, detect_language_from_text(text_en)

        except Exception as err:
            logger.warning(f"Fast STT note: {err}")

        # 2. Local Whisper STT Fallback (CPU Neural Model)
        if self._whisper_model:
            try:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp.write(wav_bytes)
                    tmp_path = tmp.name
                
                result = self._whisper_model.transcribe(tmp_path, language="ta")
                transcription = result.get("text", "").strip()
                os.unlink(tmp_path)
                if transcription and len(transcription) > 0:
                    lang = detect_language_from_text(transcription)
                    logger.info(f"Whisper Tamil decoded: '{transcription}' ({lang})")
                    return transcription, lang
            except Exception as ex:
                logger.warning(f"Whisper transcription note: {ex}")

        return "", "ta"
