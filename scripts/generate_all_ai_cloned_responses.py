import sys
import os
import asyncio
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from app.services.ai_voice_cloner import AIVoiceClonerService, HUMAN_AUDIO_TRANSCRIPTS

def generate_all_ai_cloned_voices():
    print("=" * 75)
    print("🎙️ TRANSCRIBING RECORDED VOICE & SYNTHESIZING VIA AI MODEL")
    print("=" * 75)

    cloner = AIVoiceClonerService()
    output_dir = BASE_DIR / "audio" / "ta"
    output_dir.mkdir(parents=True, exist_ok=True)

    for intent_code, transcript in HUMAN_AUDIO_TRANSCRIPTS.items():
        print(f"\n⚙️ Processing [{intent_code}]...")
        print(f"   📄 Transcript: \"{transcript[:60]}...\"")
        
        res = cloner.synthesize_response(intent_code=intent_code, custom_text=transcript, language="ta")
        audio_bytes = res.get("audio_bytes")
        engine = res.get("engine")
        
        if audio_bytes:
            out_file = output_dir / f"{intent_code.lower()}_ai_cloned.mp3"
            with open(out_file, "wb") as f:
                f.write(audio_bytes)
            print(f"   ✅ Generated via [{engine}] => {out_file.name} ({len(audio_bytes)} bytes)")
        else:
            print(f"   ❌ Failed to generate audio for {intent_code}")

    print("\n🎉 ALL AI CLONED RESPONSES SYNTHESIZED SUCCESSFULLY!")

if __name__ == "__main__":
    generate_all_ai_cloned_voices()
