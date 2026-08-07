import os
import logging
from pathlib import Path
from typing import Tuple
from app.config import AUDIO_DIR, BASE_DIR, INTENTS_REGISTRY

logger = logging.getLogger(__name__)

SUPPORTED_AUDIO_EXTENSIONS = [".mp3", ".wav", ".aac", ".ogg", ".m4a"]

class AudioRetrievalService:
    def __init__(self):
        self.primary_audio_dir = AUDIO_DIR
        self.fallback_audio_dir = BASE_DIR / "audio"

    def get_audio_path(self, intent_code: str, language: str = "ta") -> Tuple[str, str]:
        """
        Retrieves matching pre-recorded audio relative path and absolute file path.
        Prioritizes high-compatibility .mp3 files and defaults to Tamil ('ta').
        """
        lang_code = language if language in ["en", "ta"] else "ta"
        
        intent_info = INTENTS_REGISTRY.get(intent_code, INTENTS_REGISTRY["SUPERVISOR_ESCALATION"])
        base_filename = Path(intent_info["file_name"]).stem # e.g. 'donation_usage'

        search_dirs = [
            (self.primary_audio_dir / lang_code),
            (self.fallback_audio_dir / lang_code)
        ]

        # 1. Search for matching base_filename with .mp3 extension first
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue

            mp3_candidate = search_dir / f"{base_filename}.mp3"
            if mp3_candidate.exists():
                rel_path = f"audio/{lang_code}/{mp3_candidate.name}"
                return rel_path, str(mp3_candidate)

            for ext in SUPPORTED_AUDIO_EXTENSIONS:
                candidate = search_dir / f"{base_filename}{ext}"
                if candidate.exists():
                    rel_path = f"audio/{lang_code}/{candidate.name}"
                    return rel_path, str(candidate)

        # 2. Fallback supervisor escalation audio if file missing
        rel_path = f"audio/{lang_code}/supervisor_escalation.mp3"
        abs_fallback = self.fallback_audio_dir / lang_code / "supervisor_escalation.mp3"
        return rel_path, str(abs_fallback)
