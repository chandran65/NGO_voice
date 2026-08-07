import os
import sys
import shutil
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
except Exception:
    pass

BACKUP_DIR = Path(r"D:\DSM Project\audio\ta_original_backup")
TA_AUDIO_DIR = Path(r"D:\DSM Project\audio\ta")
POC_TA_AUDIO_DIR = Path(__file__).resolve().parent.parent / "audio" / "ta"

MAP = {
    "WhatsApp Audio 2026-08-01 at 9.54.36 AM.aac": ["greeting.mp3", "about_home.mp3", "donation_usage.mp3"],
    "WhatsApp Audio 2026-08-01 at 10.43.24 AM.aac": ["tax_benefits.mp3"],
    "WhatsApp Audio 2026-08-01 at 10.44.15 AM.aac": ["payment_methods.mp3"],
    "WhatsApp Audio 2026-08-01 at 10.45.04 AM.aac": ["sponsor_child.mp3"],
    "WhatsApp Audio 2026-08-01 at 10.45.46 AM.aac": ["visiting_hours.mp3", "volunteer.mp3"],
    "WhatsApp Audio 2026-08-01 at 10.46.35 AM.ogg": ["supervisor_escalation.mp3", "fallback.mp3"]
}

def convert_to_mp3(src_path: Path, dest_mp3_path: Path):
    import subprocess
    cmd = ["ffmpeg", "-y", "-i", str(src_path), "-ar", "44100", "-ac", "2", "-b:a", "128k", str(dest_mp3_path)]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
    if res.returncode == 0 and dest_mp3_path.exists():
        print(f" -> Converted {src_path.name} => {dest_mp3_path.name} ({dest_mp3_path.stat().st_size} bytes)")
        return True
    else:
        print(f" -> Conversion failed for {src_path.name}: {res.stderr.decode('utf-8', errors='ignore')}")
        return False

def process():
    print("==================================================")
    print(" MAPPING & CONVERTING ORIGINAL WHATSAPP RECORDINGS")
    print("==================================================")

    TA_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    POC_TA_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    for src_name, target_mp3s in MAP.items():
        src_path = BACKUP_DIR / src_name
        if not src_path.exists():
            print(f"File not found: {src_name}")
            continue

        for mp3_name in target_mp3s:
            out_file1 = TA_AUDIO_DIR / mp3_name
            out_file2 = POC_TA_AUDIO_DIR / mp3_name
            if convert_to_mp3(src_path, out_file1):
                shutil.copy(str(out_file1), str(out_file2))

    print("\n==================================================")
    print(" ALL ORIGINAL RECORDINGS MAPPED & INSTALLED AS MP3!")
    print("==================================================")

if __name__ == "__main__":
    process()
