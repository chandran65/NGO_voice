import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from app.config import PROJECT_ROOT, INTENTS_REGISTRY

AUDIO_DIRS = [
    PROJECT_ROOT / "audio" / "ta",
    PROJECT_ROOT / "audio" / "en",
    PROJECT_ROOT / "voice_fundraiser_poc" / "audio" / "ta",
    PROJECT_ROOT / "voice_fundraiser_poc" / "audio" / "en"
]

def generate_concise_audio_chunks():
    print("==================================================")
    print(" GENERATING CONCISE 5-10 SECOND INTENT MP3 CHUNKS ")
    print("==================================================")

    try:
        from gtts import gTTS
        has_gtts = True
    except ImportError:
        has_gtts = False

    for audio_dir in AUDIO_DIRS:
        audio_dir.mkdir(parents=True, exist_ok=True)
        lang = "ta" if "ta" in audio_dir.parts else "en"

        for intent_code, data in INTENTS_REGISTRY.items():
            if intent_code in ["FALLBACK_UNKNOWN"]:
                continue
            
            chunk_text = data.get(f"chunk_{lang}", data.get("chunk_ta"))
            out_file = audio_dir / data["file_name"]

            if has_gtts and chunk_text:
                try:
                    tts = gTTS(text=chunk_text, lang=lang, slow=False)
                    tts.save(str(out_file))
                    print(f" -> Generated Concise [{lang.upper()}] Chunk: {intent_code} => {out_file.name} ({out_file.stat().st_size} bytes)")
                except Exception as e:
                    print(f" -> gTTS error ({e}) for {intent_code}")

    print("\n==================================================")
    print(" CONCISE INTENT MP3 CHUNKS GENERATED SUCCESSFULLY! ")
    print("==================================================")

if __name__ == "__main__":
    generate_concise_audio_chunks()
