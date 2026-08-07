import os
import sys
import shutil
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from app.config import PROJECT_ROOT, INTENTS_REGISTRY
from app.services.intent import IntentClassifier

AUDIO_TA_DIR = PROJECT_ROOT / "audio" / "ta"

def inspect_and_rename_audio_files():
    print(f"Inspecting audio directory: {AUDIO_TA_DIR}")
    if not AUDIO_TA_DIR.exists():
        print("Directory does not exist!")
        return

    files = [f for f in AUDIO_TA_DIR.iterdir() if f.is_file()]
    print(f"Found {len(files)} files in {AUDIO_TA_DIR}:")
    for idx, f in enumerate(files, 1):
        print(f"{idx}. {f.name} ({f.stat().st_size} bytes)")

    # Try loading whisper STT engine
    whisper_model = None
    try:
        import faster_whisper
        print("\nLoading faster-whisper STT model...")
        whisper_model = faster_whisper.WhisperModel("tiny", device="cpu", compute_type="int8")
        print("faster-whisper loaded successfully!")
    except Exception as e:
        print(f"faster-whisper not available: {e}")

    try:
        if whisper_model is None:
            import whisper
            print("Loading openai-whisper STT model...")
            whisper_model = whisper.load_model("base")
            print("openai-whisper loaded successfully!")
    except Exception as e:
        print(f"openai-whisper not available: {e}")

    classifier = IntentClassifier()
    mapping_results = []

    for file_path in files:
        filename = file_path.name
        # Skip if already renamed to clean intent name
        if any(filename.startswith(intent_info["file_name"].split('.')[0]) for intent_info in INTENTS_REGISTRY.values()):
            print(f"\nSkipping already renamed file: {filename}")
            continue

        transcription = ""
        print(f"\n--------------------------------------------------")
        print(f"Processing File: {filename}")

        if whisper_model:
            try:
                # Transcribe with whisper
                if hasattr(whisper_model, 'transcribe'):
                    if hasattr(whisper_model, 'WhisperModel') or 'faster_whisper' in str(type(whisper_model)):
                        segments, info = whisper_model.transcribe(str(file_path), language="ta")
                        transcription = " ".join([segment.text for segment in segments]).strip()
                    else:
                        res = whisper_model.transcribe(str(file_path), language="ta")
                        transcription = res.get("text", "").strip()
            except Exception as ex:
                print(f"Whisper transcription error for {filename}: {ex}")

        print(f"Transcription: '{transcription}'")
        
        intent, lang, conf = classifier.classify(transcription, "ta")
        intent_info = INTENTS_REGISTRY.get(intent, INTENTS_REGISTRY["FALLBACK_UNKNOWN"])
        target_ext = file_path.suffix
        new_filename = f"{intent_info['file_name'].split('.')[0]}{target_ext}"
        new_filepath = AUDIO_TA_DIR / new_filename

        print(f"Classified Intent: {intent} ({intent_info['name']})")
        print(f"Target Filename: {new_filename}")

        mapping_results.append({
            "original": file_path,
            "transcription": transcription,
            "intent": intent,
            "new_filepath": new_filepath,
            "new_filename": new_filename
        })

    # Execute Renaming
    print("\n==================================================")
    print("        EXECUTING FILE RENAMING MAPPING           ")
    print("==================================================")

    for item in mapping_results:
        orig_path = item["original"]
        dest_path = item["new_filepath"]
        
        # If dest file exists and is different, backup or overwrite
        if dest_path.exists() and dest_path != orig_path:
            print(f"Overwriting existing target: {dest_path.name}")
            dest_path.unlink()

        print(f"Renaming: '{orig_path.name}' ---> '{dest_path.name}'")
        try:
            orig_path.rename(dest_path)
        except Exception as e:
            print(f"Failed to rename {orig_path.name}: {e}")

if __name__ == "__main__":
    inspect_and_rename_audio_files()
