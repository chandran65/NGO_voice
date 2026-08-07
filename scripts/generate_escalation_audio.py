import os
import sys
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

def generate_number_source_audio():
    print("==================================================")
    print(" GENERATING NUMBER SOURCE & INTENT AUDIO FILES    ")
    print("==================================================")

    ta_number_source_text = "எங்கள் குழந்தைகள் இல்ல அறக்கட்டளையின் பொது நன்கொடையாளர்கள் பட்டியல் மற்றும் சேவை ஆதரவாளர்கள் கோப்பிலிருந்து உங்கள் தொடர்பு எண் பெறப்பட்டது. உங்கள் ஆதரவு எங்களுக்கு மிகவும் முக்கியமானது."
    en_number_source_text = "Your contact number was obtained from our public donor directory and supporter registry. We reach out to caring individuals to support children's welfare."

    try:
        from gtts import gTTS
        has_gtts = True
    except ImportError:
        has_gtts = False

    for audio_dir in AUDIO_DIRS:
        audio_dir.mkdir(parents=True, exist_ok=True)
        lang = "ta" if "ta" in audio_dir.parts else "en"
        text = ta_number_source_text if lang == "ta" else en_number_source_text
        out_file = audio_dir / "number_source.mp3"

        if has_gtts:
            try:
                tts = gTTS(text=text, lang=lang, slow=False)
                tts.save(str(out_file))
                print(f" -> SUCCESS: Generated [{lang.upper()}] {out_file.name}")
            except Exception as e:
                print(f" -> gTTS error ({e}), preserving file.")
        else:
            print(f" -> gTTS not available, skipped generating {out_file.name}")

if __name__ == "__main__":
    generate_number_source_audio()
