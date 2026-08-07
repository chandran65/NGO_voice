import os
import io
import glob
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import speech_recognition as sr
from app.services.stt import convert_audio_to_wav_bytes

def transcribe_all_whatsapp_files():
    print("=" * 70)
    print("🎙️ TRANSCRIBING ORIGINAL WHATSAPP RECORDED AUDIO FILES")
    print("=" * 70)

    audio_dir = BASE_DIR / "audio" / "ta"
    files = sorted(list(audio_dir.glob("WhatsApp Audio*.aac")) + list(audio_dir.glob("WhatsApp Audio*.ogg")))
    
    r = sr.Recognizer()
    
    for f in files:
        file_name = f.name
        try:
            with open(f, "rb") as raw:
                audio_bytes = raw.read()
            wav_bytes = convert_audio_to_wav_bytes(audio_bytes)
            
            with sr.AudioFile(io.BytesIO(wav_bytes)) as source:
                audio_data = r.record(source)
                text = r.recognize_google(audio_data, language="ta-IN")
                print(f"📄 '{file_name}' ({f.stat().st_size} bytes):")
                print(f"   🗣️ Spoken Tamil: \"{text}\"\n")
        except Exception as e:
            print(f"❌ Error transcribing '{file_name}': {e}\n")

if __name__ == "__main__":
    transcribe_all_whatsapp_files()
