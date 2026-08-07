import os
import sys
import shutil
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.config import BASE_DIR, AUDIO_DIR, INTENTS_REGISTRY
from app.services.stt import STTService, convert_audio_to_wav_bytes
from app.services.intent import IntentClassifier

def map_recorded_whatsapp_audio():
    local_ta_dir = BASE_DIR / "audio" / "ta"
    external_ta_dir = AUDIO_DIR / "ta"
    
    print(f"Scanning recorded Tamil WhatsApp audio files in: {local_ta_dir} and {external_ta_dir}")
    
    stt = STTService()
    classifier = IntentClassifier()

    whatsapp_files = sorted(list(local_ta_dir.glob("WhatsApp Audio*")) + list(external_ta_dir.glob("WhatsApp Audio*")))
    # Remove duplicates
    whatsapp_files = list({f.name: f for f in whatsapp_files}.values())
    whatsapp_files = sorted(whatsapp_files, key=lambda x: x.name)
    if not whatsapp_files:
        print("No WhatsApp Audio files found to map.")
        return

    print(f"Found {len(whatsapp_files)} human recorded audio files.")
    
    # Explicit timestamp mapping table for recorded human Tamil WhatsApp audio files
    timestamp_map = {
        "9.54.36": "greeting.mp3",
        "10.42.28": "about_home.mp3",
        "10.43.24": "number_source.mp3",
        "10.44.15": "donation_usage.mp3",
        "10.45.04": "tax_benefits.mp3",
        "10.45.46": "payment_link.mp3",
        "10.46.35": "sponsor_child.mp3",
        "10.47.21": "address_update.mp3",
        "10.48.00": "callback_request.mp3",
        "10.48.33": "receipt_request.mp3",
        "9.51.29": "supervisor_escalation.mp3"
    }

    mapped_count = 0
    for audio_file in whatsapp_files:
        try:
            target_filename = None
            for ts_key, filename in timestamp_map.items():
                if ts_key in audio_file.name:
                    target_filename = filename
                    break

            if target_filename:
                for target_dir in [local_ta_dir, external_ta_dir]:
                    target_dir.mkdir(parents=True, exist_ok=True)
                    dest_file = target_dir / target_filename
                    shutil.copy2(audio_file, dest_file)

                print(f"Mapped recorded voice '{audio_file.name}' => {target_filename}")
                mapped_count += 1

        except Exception as e:
            print(f"   Error processing {audio_file.name}: {e}")

    print(f"\nSuccessfully mapped {mapped_count} human recorded voice files to intent audio repository!")

if __name__ == "__main__":
    map_recorded_whatsapp_audio()
