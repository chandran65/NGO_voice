import os
import sys
import argparse
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from app.config import INTENTS_REGISTRY, PROJECT_ROOT
from app.services.elevenlabs_tts import ElevenLabsTTSService

TA_AUDIO_DIR = PROJECT_ROOT / "audio" / "ta"
EN_AUDIO_DIR = PROJECT_ROOT / "audio" / "en"
POC_TA_AUDIO_DIR = PROJECT_ROOT / "voice_fundraiser_poc" / "audio" / "ta"
POC_EN_AUDIO_DIR = PROJECT_ROOT / "voice_fundraiser_poc" / "audio" / "en"

def generate_all_elevenlabs(api_key: str, voice_id: str = "21m00Tcm4TlvDq8ikWAM"):
    print("==================================================")
    print(" ELEVENLABS HYPER-REALISTIC VOICE GENERATION      ")
    print("==================================================")

    service = ElevenLabsTTSService(api_key=api_key)
    if not service.is_available():
        print("ERROR: Invalid ElevenLabs API Key.")
        return

    for intent_code, data in INTENTS_REGISTRY.items():
        if intent_code in ["FALLBACK_UNKNOWN"]:
            continue

        file_name = data["file_name"]
        
        # 1. Tamil Audio Generation
        ta_text = data.get("chunk_ta") or data.get("description_ta")
        if ta_text:
            out_path_ta = TA_AUDIO_DIR / file_name
            out_poc_ta = POC_TA_AUDIO_DIR / file_name
            print(f"\nGenerating [TA] {intent_code}...")
            print(f" -> Text: '{ta_text}'")
            res = service.generate_speech_mp3(ta_text, voice_id=voice_id, output_path=out_path_ta)
            if res:
                with open(out_poc_ta, "wb") as f:
                    f.write(res)
                print(f" -> SUCCESS: Saved {out_path_ta.name} ({len(res)} bytes)")

        # 2. English Audio Generation
        en_text = data.get("chunk_en") or data.get("description_en")
        if en_text:
            out_path_en = EN_AUDIO_DIR / file_name
            out_poc_en = POC_EN_AUDIO_DIR / file_name
            print(f"\nGenerating [EN] {intent_code}...")
            print(f" -> Text: '{en_text}'")
            res = service.generate_speech_mp3(en_text, voice_id=voice_id, output_path=out_path_en)
            if res:
                with open(out_poc_en, "wb") as f:
                    f.write(res)
                print(f" -> SUCCESS: Saved {out_path_en.name} ({len(res)} bytes)")

    print("\n==================================================")
    print(" ALL ELEVENLABS HUMAN VOICES GENERATED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate ElevenLabs Hyper-Realistic Voices")
    parser.add_argument("--api-key", type=str, help="ElevenLabs API Key", default=os.getenv("ELEVENLABS_API_KEY"))
    parser.add_argument("--voice-id", type=str, help="ElevenLabs Voice ID", default="21m00Tcm4TlvDq8ikWAM")
    args = parser.parse_args()

    if not args.api_key:
        print("Usage: python scripts/generate_elevenlabs_responses.py --api-key YOUR_ELEVENLABS_API_KEY")
        sys.exit(1)

    generate_all_elevenlabs(api_key=args.api_key, voice_id=args.voice_id)
