import os
import sys
import requests
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def clone_voice_with_elevenlabs(api_key: str, name: str = "NGO_Tamil_Fundraiser_Voice"):
    """
    Clones recorded WhatsApp audio files into a custom ElevenLabs Voice Model.
    """
    url = "https://api.elevenlabs.io/v1/voices/add"
    headers = {
        "xi-api-key": api_key
    }

    # Audio sample files to train the clone
    sample_files = [
        BASE_DIR / "audio" / "ta" / "greeting.mp3",
        BASE_DIR / "audio" / "ta" / "about_home.mp3",
        BASE_DIR / "audio" / "ta" / "donation_usage.mp3"
    ]

    files = []
    for sf in sample_files:
        if sf.exists():
            files.append(("files", (sf.name, open(sf, "rb"), "audio/mpeg")))

    data = {
        "name": name,
        "description": "Tamil NGO Voice Fundraiser Cloned Voice Model",
        "labels": '{"accent": "Tamil", "gender": "Female", "use_case": "NGO Outbound Calling"}'
    }

    print(f"🚀 Uploading {len(files)} human audio samples to ElevenLabs for Instant Voice Cloning...")
    response = requests.post(url, headers=headers, data=data, files=files)

    if response.status_code == 200:
        res_json = response.json()
        voice_id = res_json.get("voice_id")
        print(f"🎉 Voice Cloned Successfully!")
        print(f"👉 YOUR NEW CLONED VOICE ID: {voice_id}")
        print(f"\nTo use this cloned voice in your app, set this environment variable:")
        print(f"set ELEVENLABS_VOICE_ID={voice_id}")
        return voice_id
    else:
        print(f"❌ ElevenLabs Voice Cloning Error [{response.status_code}]: {response.text}")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        key = sys.argv[1]
        clone_voice_with_elevenlabs(key)
    else:
        print("Usage: python scripts/clone_human_voice.py <YOUR_ELEVENLABS_API_KEY>")
