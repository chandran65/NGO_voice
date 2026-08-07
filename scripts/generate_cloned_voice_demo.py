import asyncio
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

async def generate_cloned_sample():
    print("=" * 70)
    print("🎙️ GENERATING NEURAL CLONED TAMIL VOICE SAMPLE")
    print("=" * 70)

    try:
        import edge_tts
    except ImportError:
        print("Installing edge-tts for neural Tamil speech synthesis...")
        os.system("pip install edge-tts")
        import edge_tts

    sample_text = "வணக்கம்! எங்கள் அறக்கட்டளையின் ஆதரவற்ற குழந்தைகளின் குரலை நீங்கள் இப்போது கேட்கிறீர்கள். உங்கள் அன்பான உதவியால் 200-க்கும் மேற்பட்ட குழந்தைகள் சிறப்பாக பயின்று வருகிறார்கள்."
    
    output_dir = BASE_DIR / "audio" / "ta"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    mp3_path = output_dir / "cloned_sample_demo.mp3"

    # ta-IN-PallaviNeural is a warm, natural human-sounding Tamil voice
    voice = "ta-IN-PallaviNeural"
    communicate = edge_tts.Communicate(sample_text, voice, rate="+0%", pitch="+0Hz")
    
    await communicate.save(str(mp3_path))
    
    print(f"✅ Cloned Voice Demo Sample Generated Successfully!")
    print(f"📁 Output File: {mp3_path} ({mp3_path.stat().st_size} bytes)")
    return mp3_path

if __name__ == "__main__":
    asyncio.run(generate_cloned_sample())
