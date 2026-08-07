import os
import sys
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def restore_original_human_voices():
    print("Mapping 11 Original Human WhatsApp Voice Recordings to Intent Audio Files...")
    
    dirs = [
        BASE_DIR / "audio" / "ta",
        BASE_DIR.parent / "audio" / "ta"
    ]

    # Exact timestamp to intent file map for original human recordings
    human_voice_map = {
        "9.54.36": "greeting",
        "10.42.28": "about_home",
        "10.43.24": "number_source",
        "10.44.15": "donation_usage",
        "10.45.04": "tax_benefits",
        "10.45.46": "payment_link",
        "10.46.35": "sponsor_child",
        "10.47.21": "address_update",
        "10.48.00": "callback_request",
        "10.48.33": "receipt_request",
        "9.51.29": "supervisor_escalation"
    }

    for target_dir in dirs:
        if not target_dir.exists():
            target_dir.mkdir(parents=True, exist_ok=True)

        whatsapp_files = list(target_dir.glob("WhatsApp Audio*")) + list((BASE_DIR / "audio" / "ta").glob("WhatsApp Audio*"))
        
        for wa_file in whatsapp_files:
            for ts_key, intent_stem in human_voice_map.items():
                if ts_key in wa_file.name:
                    # Save as original format and also copy as primary .mp3 / .aac alias
                    dest_mp3 = target_dir / f"{intent_stem}.mp3"
                    dest_orig = target_dir / f"{intent_stem}{wa_file.suffix}"
                    
                    shutil.copy2(wa_file, dest_orig)
                    shutil.copy2(wa_file, dest_mp3)
                    print(f"Restored Human Voice: '{wa_file.name}' => {dest_mp3.name} ({wa_file.stat().st_size} bytes)")
                    break

    print("All Original Human Voice Recordings Restored Successfully!")

if __name__ == "__main__":
    restore_original_human_voices()
