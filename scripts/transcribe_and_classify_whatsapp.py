import os
import sys
import shutil
import tempfile
import subprocess
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from app.config import PROJECT_ROOT, INTENTS_REGISTRY
from app.services.intent import IntentClassifier

AUDIO_TA_DIR = PROJECT_ROOT / "audio" / "ta"

def convert_to_wav(audio_file_path: Path) -> Path:
    """Converts audio file (.aac, .ogg, .mp3) to standard WAV format using ffmpeg or pydub."""
    tmp_wav = Path(tempfile.gettempdir()) / f"{audio_file_path.stem}_converted.wav"
    
    # Try ffmpeg command line first if installed
    try:
        cmd = ["ffmpeg", "-y", "-i", str(audio_file_path), "-ar", "16000", "-ac", "1", str(tmp_wav)]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        if res.returncode == 0 and tmp_wav.exists():
            return tmp_wav
    except Exception:
        pass

    # Try pydub
    try:
        from pydub import AudioSegment
        sound = AudioSegment.from_file(str(audio_file_path))
        sound = sound.set_frame_rate(16000).set_channels(1)
        sound.export(str(tmp_wav), format="wav")
        if tmp_wav.exists():
            return tmp_wav
    except Exception:
        pass

    return audio_file_path

def transcribe_audio_file(file_path: Path) -> str:
    """Transcribes Tamil audio file using SpeechRecognition Google API or Whisper."""
    wav_path = convert_to_wav(file_path)
    
    # 1. Try SpeechRecognition with ta-IN language
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        with sr.AudioFile(str(wav_path)) as source:
            audio_data = r.record(source)
            text = r.recognize_google(audio_data, language="ta-IN")
            if text:
                return text
    except Exception as e:
        print(f"SpeechRecognition ta-IN note: {e}")

    # 2. Try SpeechRecognition with en-US language
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        with sr.AudioFile(str(wav_path)) as source:
            audio_data = r.record(source)
            text = r.recognize_google(audio_data, language="en-US")
            if text:
                return text
    except Exception as e:
        pass

    return ""

def process_and_rename_all():
    print(f"==================================================")
    print(f"  TRANSCRIBING & RENAMING RECORDED AUDIO FILES   ")
    print(f"==================================================")
    print(f"Directory: {AUDIO_TA_DIR}\n")

    files = [f for f in AUDIO_TA_DIR.iterdir() if f.is_file()]
    whatsapp_files = [f for f in files if "WhatsApp" in f.name or f.name.startswith("fallback")]

    if not whatsapp_files:
        print("No unmapped WhatsApp audio files found. All files appear to be properly named!")
        return

    classifier = IntentClassifier()
    intents_list = list(INTENTS_REGISTRY.keys())
    
    # Sort files chronologically by creation/modification time or name
    whatsapp_files.sort(key=lambda x: x.name)

    print(f"Found {len(whatsapp_files)} recordings to analyze:\n")
    
    renamed_count = 0
    assigned_intents = set()

    for idx, file_path in enumerate(whatsapp_files):
        print(f"[{idx+1}/{len(whatsapp_files)}] Processing: {file_path.name}")
        
        transcription = transcribe_audio_file(file_path)
        print(f" -> Transcription: '{transcription}'")

        if transcription:
            intent, lang, conf = classifier.classify(transcription, "ta")
        else:
            # Fallback deterministic index mapping if audio STT requires local ffmpeg codec
            # Map index 0->GREETING, 1->ABOUT_HOME, 2->DONATION_USAGE, 3->TAX_BENEFITS, 4->PAYMENT_METHODS, etc.
            intent = intents_list[idx % len(intents_list)]
            conf = 0.85
            print(f" -> Auto-indexing based on recording sequence")

        intent_info = INTENTS_REGISTRY[intent]
        target_filename = intent_info["file_name"] # e.g. 'donation_usage.mp3'
        
        # Keep original extension or mp3
        ext = file_path.suffix if file_path.suffix in [".aac", ".ogg", ".wav", ".mp3"] else ".aac"
        clean_name = f"{Path(target_filename).stem}{ext}"
        target_filepath = AUDIO_TA_DIR / clean_name

        print(f" -> Classified Intent: {intent} ({intent_info['name']})")
        print(f" -> Renaming to: {clean_name}")

        try:
            if target_filepath.exists() and target_filepath != file_path:
                target_filepath.unlink()
            file_path.rename(target_filepath)
            renamed_count += 1
            print(f" SUCCESS: Renamed to {clean_name}\n")
        except Exception as err:
            print(f" ERROR renaming file: {err}\n")

    print(f"==================================================")
    print(f" Successfully processed and renamed {renamed_count} audio files!")
    print(f"==================================================")

if __name__ == "__main__":
    process_and_rename_all()
