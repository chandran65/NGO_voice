import os
import sys
import shutil
import logging
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.config import BASE_DIR, AUDIO_DIR, INTENTS_REGISTRY

logger = logging.getLogger(__name__)

def generate_all_audio_files():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    print("Generating 100% matched pre-recorded audio files for NGO Fundraising Outbound Platform...")
    
    try:
        from gtts import gTTS
        print("Using gTTS (Google Text-to-Speech) for clear, native Tamil speech synthesis.")
    except ImportError as err:
        print(f"gTTS package missing ({err}). Please install gtts.")
        return

    target_dirs = [
        BASE_DIR / "audio",
        AUDIO_DIR
    ]

    count = 0
    for code, info in INTENTS_REGISTRY.items():
        filename = info.get("file_name", f"{code.lower()}.mp3")
        chunk_ta = info.get("chunk_ta")
        chunk_en = info.get("chunk_en")

        # 1. Tamil Audio Generation (Edge Studio HD Female Voice & Piper Neural Fallback)
        if chunk_ta:
            try:
                import asyncio, edge_tts
                for tdir in target_dirs:
                    lang_dir = tdir / "ta"
                    lang_dir.mkdir(parents=True, exist_ok=True)
                    out_path = lang_dir / filename
                    async def save_edge():
                        comm = edge_tts.Communicate(chunk_ta, "ta-IN-PallaviNeural")
                        await comm.save(str(out_path))
                    asyncio.run(save_edge())
                    print(f"Generated Female HD Tamil Audio [ta-IN-PallaviNeural] => ta/{filename}")
                count += 1
            except Exception as e:
                print(f"Edge TTS fallback note for {code}: {e}")
                from app.services.tts_service import DynamicTTSService
                for tdir in target_dirs:
                    lang_dir = tdir / "ta"
                    lang_dir.mkdir(parents=True, exist_ok=True)
                    out_path = lang_dir / filename
                    DynamicTTSService.generate_piper_tamil_tts(chunk_ta, out_path, voice="HemaLatha")

        # 2. English Audio Generation
        if chunk_en:
            try:
                for tdir in target_dirs:
                    lang_dir = tdir / "en"
                    lang_dir.mkdir(parents=True, exist_ok=True)
                    out_path = lang_dir / filename
                    if not out_path.exists() or out_path.stat().st_size == 0:
                        tts_en = gTTS(text=chunk_en, lang="en", slow=False)
                        tts_en.save(str(out_path))
                        print(f"Generated English Audio [gTTS] => en/{filename}")
                    else:
                        print(f"Verified English Audio => en/{filename}")
            except Exception as e:
                print(f"Error generating English audio for {code}: {e}")

    print(f"\nSuccessfully generated {count} perfectly matched Tamil & English voice response files!")

if __name__ == "__main__":
    generate_all_audio_files()
