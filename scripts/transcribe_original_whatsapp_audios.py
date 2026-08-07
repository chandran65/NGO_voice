import os
import sys
import io
import tempfile
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure ffmpeg binary path is added
try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
    print(" -> static_ffmpeg path added successfully.")
except Exception as e:
    print(" -> static_ffmpeg import note:", e)

BACKUP_DIR = Path(r"D:\DSM Project\audio\ta_original_backup")

def convert_to_wav(file_path: Path) -> bytes:
    """Converts aac/ogg to standard PCM WAV bytes using pydub or ffmpeg."""
    try:
        from pydub import AudioSegment
        sound = AudioSegment.from_file(str(file_path))
        sound = sound.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        out_buf = io.BytesIO()
        sound.export(out_buf, format="wav")
        return out_buf.getvalue()
    except Exception as e:
        print(f"Pydub convert error for {file_path.name}: {e}")

    try:
        import subprocess
        out_path = str(file_path) + ".wav"
        cmd = ["ffmpeg", "-y", "-i", str(file_path), "-ar", "16000", "-ac", "1", "-f", "wav", out_path]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        if res.returncode == 0 and os.path.exists(out_path):
            with open(out_path, "rb") as f:
                data = f.read()
            os.unlink(out_path)
            return data
    except Exception as e:
        print(f"FFmpeg convert error for {file_path.name}: {e}")

    return b""

def transcribe_audio_file(file_path: Path):
    print(f"\n--------------------------------------------------")
    print(f"FILE: {file_path.name} ({file_path.stat().st_size} bytes)")

    wav_bytes = convert_to_wav(file_path)
    if not wav_bytes:
        print(" -> ERROR: Could not convert audio to WAV.")
        return None

    transcription = ""
    # Try speech recognition
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        with sr.AudioFile(io.BytesIO(wav_bytes)) as source:
            audio_data = r.record(source)
            
            # 1. Try Tamil
            try:
                transcription = r.recognize_google(audio_data, language="ta-IN")
                print(f" -> TAMIL TRANSCRIPTION: '{transcription}'")
            except Exception as e:
                # 2. Try English
                try:
                    transcription = r.recognize_google(audio_data, language="en-IN")
                    print(f" -> ENGLISH TRANSCRIPTION: '{transcription}'")
                except Exception as e2:
                    print(f" -> STT Decoding note: {e2}")
    except Exception as err:
        print(f" -> SpeechRecognition error: {err}")

    return transcription

def main():
    print("==================================================")
    print(" TRANSCRIBING ALL ORIGINAL WHATSAPP RECORDINGS   ")
    print("==================================================")

    if not BACKUP_DIR.exists():
        print(f"Backup dir not found: {BACKUP_DIR}")
        return

    results = []
    files = sorted(list(BACKUP_DIR.glob("*.*")))
    for f in files:
        txt = transcribe_audio_file(f)
        results.append((f.name, f.stat().st_size, txt))

    print("\n==================================================")
    print("              TRANSCRIPTION SUMMARY               ")
    print("==================================================")
    for name, size, txt in results:
        print(f"File: {name} | Text: '{txt}'")

if __name__ == "__main__":
    main()
