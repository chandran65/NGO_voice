import os
import requests
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Default ElevenLabs Voice IDs
# Multilingual v2 supports Tamil, Hindi, English with natural human cadence & breathing
DEFAULT_ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Rachel / Custom Multilingual
ELEVENLABS_MODEL_ID = "eleven_multilingual_v2"

class ElevenLabsTTSService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        self.base_url = "https://api.elevenlabs.io/v1/text-to-speech"

    def is_available(self) -> bool:
        return bool(self.api_key)

    def generate_speech_mp3(self, text: str, voice_id: Optional[str] = None, output_path: Optional[Path] = None) -> Optional[bytes]:
        """
        Generates hyper-realistic human speech using ElevenLabs Multilingual v2 API.
        Saves to output_path if provided, and returns raw MP3 bytes.
        """
        if not self.api_key:
            logger.warning("ElevenLabs API Key not found. Set ELEVENLABS_API_KEY environment variable.")
            return None

        target_voice_id = voice_id or DEFAULT_ELEVENLABS_VOICE_ID
        url = f"{self.base_url}/{target_voice_id}"

        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }

        payload = {
            "text": text,
            "model_id": ELEVENLABS_MODEL_ID,
            "voice_settings": {
                "stability": 0.45,
                "similarity_boost": 0.85,
                "style": 0.20,
                "use_speaker_boost": True
            }
        }

        try:
            logger.info(f"Calling ElevenLabs API for text: '{text[:30]}...' using model {ELEVENLABS_MODEL_ID}")
            response = requests.post(url, json=payload, headers=headers, timeout=20)
            
            if response.status_code == 200:
                audio_bytes = response.content
                if output_path:
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, "wb") as f:
                        f.write(audio_bytes)
                    logger.info(f"Successfully saved ElevenLabs human audio: {output_path} ({len(audio_bytes)} bytes)")
                return audio_bytes
            else:
                logger.error(f"ElevenLabs API Error [{response.status_code}]: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Failed to generate speech with ElevenLabs: {e}")
            return None
