import os
import sys
import wave
import math
import struct
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from app.config import PROJECT_ROOT

AUDIO_DIRS = [
    PROJECT_ROOT / "audio" / "ta",
    PROJECT_ROOT / "audio" / "en",
    PROJECT_ROOT / "voice_fundraiser_poc" / "audio" / "ta",
    PROJECT_ROOT / "voice_fundraiser_poc" / "audio" / "en"
]

def apply_telephony_filter_to_file(mp3_path: Path):
    """
    Applies telephony acoustic filter to make voice sound like an authentic phone call.
    """
    try:
        from pydub import AudioSegment
        from pydub.effects import normalize, low_pass_filter, high_pass_filter

        sound = AudioSegment.from_file(str(mp3_path))
        
        # 1. Apply High Pass Filter (cut sub-bass below 300Hz like telephone mic)
        filtered = high_pass_filter(sound, 300)
        
        # 2. Apply Low Pass Filter (cut harsh highs above 3400Hz like 8kHz telephony codec)
        filtered = low_pass_filter(filtered, 3400)
        
        # 3. Apply subtle compression & normalization for warm human telephone vocal presence
        filtered = normalize(filtered)
        
        # Overwrite file with warm telephone acoustic audio
        filtered.export(str(mp3_path), format="mp3", bitrate="128k")
        print(f" -> Applied Telephony Human Filter: {mp3_path.name}")
    except Exception as e:
        print(f" -> Telephony filter error for {mp3_path.name}: {e}")

def process_all_files():
    print("==================================================")
    print(" APPLYING TELEPHONY ACOUSTIC HUMAN VOICE FILTER   ")
    print("==================================================")

    for audio_dir in AUDIO_DIRS:
        if not audio_dir.exists():
            continue
        print(f"\nFiltering Audio in: {audio_dir}")
        mp3_files = list(audio_dir.glob("*.mp3"))
        for mp3_path in mp3_files:
            apply_telephony_filter_to_file(mp3_path)

    print("\n==================================================")
    print(" TELEPHONY HUMAN FILTER APPLIED SUCCESSFULLY!    ")
    print("==================================================")

if __name__ == "__main__":
    process_all_files()
