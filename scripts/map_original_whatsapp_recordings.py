import os
import sys
import shutil
import subprocess
import tempfile
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from app.config import PROJECT_ROOT, INTENTS_REGISTRY

AUDIO_TA_DIR = PROJECT_ROOT / "audio" / "ta"
BACKUP_DIR = PROJECT_ROOT / "audio" / "ta_original_backup"

def map_and_preserve_original_recordings():
    print(f"==================================================")
    print(f" MAPPING & PRESERVING ORIGINAL WHATSAPP AUDIO     ")
    print(f"==================================================")
    
    if not AUDIO_TA_DIR.exists():
        print("AUDIO_TA_DIR does not exist.")
        return

    # 1. Create a safe backup directory for original recordings
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    whatsapp_files = sorted([f for f in AUDIO_TA_DIR.iterdir() if f.is_file() and "WhatsApp" in f.name])
    
    print(f"Found {len(whatsapp_files)} original WhatsApp recordings in {AUDIO_TA_DIR}:")
    for f in whatsapp_files:
        print(f" - {f.name} ({f.stat().st_size} bytes)")
        # Copy to backup directory
        shutil.copy2(f, BACKUP_DIR / f.name)

    print(f"\nSaved safe backup of all original files to: {BACKUP_DIR}")

    # Mapping order for the 11 original WhatsApp voice recordings to predefined intents
    INTENT_MAPPING_ORDER = [
        "GREETING",          # 1. 9.51.29 AM / 9.54.36 AM
        "ABOUT_HOME",        # 2. 10.42.28 AM
        "DONATION_USAGE",    # 3. 10.43.24 AM
        "TAX_BENEFITS",      # 4. 10.44.15 AM
        "PAYMENT_METHODS",  # 5. 10.45.04 AM
        "SPONSOR_CHILD",     # 6. 10.45.46 AM
        "VOLUNTEER",         # 7. 10.46.35 AM
        "VISITING_HOURS",    # 8. 10.47.21 AM
        "ANNUAL_REPORT",     # 9. 10.48.00 AM
        "RECEIPT_REQUEST",   # 10. 10.48.33 AM
        "CONTACT_US"         # 11. Final Contact
    ]

    print("\n--------------------------------------------------")
    print("Creating intent audio files from original WhatsApp recordings:")
    print("--------------------------------------------------")

    for idx, orig_file in enumerate(whatsapp_files):
        if idx < len(INTENT_MAPPING_ORDER):
            intent_code = INTENT_MAPPING_ORDER[idx]
            intent_info = INTENTS_REGISTRY[intent_code]
            
            # Target extension matches original recording extension (.aac or .ogg)
            ext = orig_file.suffix
            clean_filename = f"{Path(intent_info['file_name']).stem}{ext}"
            target_path = AUDIO_TA_DIR / clean_filename

            print(f"[{idx+1}/{len(whatsapp_files)}] '{orig_file.name}'")
            print(f"  --> Mapped to Intent: {intent_code} ({intent_info['name']})")
            print(f"  --> Target File: {clean_filename}")

            # Copy original file to clean target filename (preserving original WhatsApp file untouched!)
            shutil.copy2(orig_file, target_path)

    print("\n==================================================")
    print(" SUCCESSFULLY MAPPED ORIGINAL RECORDINGS!        ")
    print("==================================================")

if __name__ == "__main__":
    map_and_preserve_original_recordings()
