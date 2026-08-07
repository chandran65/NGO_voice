import os
import hashlib
import logging
from pathlib import Path
from typing import Tuple
from app.config import AUDIO_DIR

logger = logging.getLogger(__name__)

TTS_AUDIO_DIR = AUDIO_DIR / "tts"
TTS_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

class DynamicTTSService:
    @staticmethod
    def generate_tts_audio(text: str, language: str = "ta") -> Tuple[str, str]:
        """
        Generates dynamic audio for personalized responses (e.g. policy amounts, dates, names).
        Returns (relative_url, absolute_path).
        """
        if not text:
            return "audio/ta/greeting.mp3", str(AUDIO_DIR / "ta" / "greeting.mp3")

        # Compute hash of text for caching
        text_hash = hashlib.md5(f"{language}:{text}".encode("utf-8")).hexdigest()[:12]
        filename = f"tts_{language}_{text_hash}.mp3"
        abs_path = TTS_AUDIO_DIR / filename
        rel_path = f"audio/tts/{filename}"

        if abs_path.exists():
            return rel_path, str(abs_path)

        # 1. Try gTTS (Google Text-to-Speech for natural Tamil speech)
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang=language, slow=False)
            tts.save(str(abs_path))
            logger.info(f"Generated dynamic gTTS audio for '{text[:30]}...' -> {rel_path}")
            return rel_path, str(abs_path)
        except Exception as e:
            logger.warning(f"gTTS audio generation note ({e}), falling back to predefined audio.")

        # Fallback to standard pre-recorded greeting if TTS synthesis fails offline
        default_rel = f"audio/{language}/greeting.mp3"
        default_abs = AUDIO_DIR / language / "greeting.mp3"
        return default_rel, str(default_abs)
