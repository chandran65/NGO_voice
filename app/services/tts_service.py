import os
import io
import asyncio
import hashlib
import logging
from pathlib import Path
from typing import Tuple
from app.config import AUDIO_DIR
from app.services.elevenlabs_tts import ElevenLabsTTSService

logger = logging.getLogger(__name__)

TTS_AUDIO_DIR = AUDIO_DIR / "tts"
TTS_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

class DynamicTTSService:
    @staticmethod
    def generate_tts_audio(text: str, language: str = "ta") -> Tuple[str, str]:
        """
        Generates dynamic studio-quality human voice audio for personalized responses.
        Uses ElevenLabs / Microsoft Edge Neural Voice ('ta-IN-PallaviNeural') / gTTS.
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

        # 1. Try ElevenLabs Voice Cloning if API key present
        eleven_labs = ElevenLabsTTSService()
        if eleven_labs.is_available():
            try:
                audio_bytes = eleven_labs.generate_speech_mp3(text, output_path=abs_path)
                if audio_bytes and abs_path.exists():
                    logger.info(f"Generated ElevenLabs human cloned speech for '{text[:30]}...' -> {rel_path}")
                    return rel_path, str(abs_path)
            except Exception as e:
                logger.warning(f"ElevenLabs synthesis note: {e}")

        # 2. Try Microsoft Edge Neural Voice (Studio Quality Tamil Speaker ta-IN-PallaviNeural)
        try:
            import edge_tts
            voice = "ta-IN-PallaviNeural" if language == "ta" else "en-IN-NeerjaNeural"
            
            async def _synthesize():
                communicate = edge_tts.Communicate(text, voice)
                await communicate.save(str(abs_path))
                
            asyncio.run(_synthesize())
            if abs_path.exists():
                logger.info(f"Generated Edge Neural Tamil Speech ({voice}) -> {rel_path}")
                return rel_path, str(abs_path)
        except Exception as e:
            logger.warning(f"Edge-TTS synthesis note ({e}), falling back to gTTS.")

        # 3. Fallback gTTS
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang=language, slow=False)
            tts.save(str(abs_path))
            logger.info(f"Generated dynamic gTTS audio -> {rel_path}")
            return rel_path, str(abs_path)
        except Exception as e:
            logger.warning(f"gTTS audio generation note: {e}")

        default_rel = f"audio/{language}/greeting.mp3"
        default_abs = AUDIO_DIR / language / "greeting.mp3"
        return default_rel, str(default_abs)
