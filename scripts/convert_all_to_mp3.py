import os
import sys
import subprocess
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from gtts import gTTS
from app.config import PROJECT_ROOT, INTENTS_REGISTRY

AUDIO_DIRS = [
    PROJECT_ROOT / "audio" / "ta",
    PROJECT_ROOT / "audio" / "en",
    PROJECT_ROOT / "voice_fundraiser_poc" / "audio" / "ta",
    PROJECT_ROOT / "voice_fundraiser_poc" / "audio" / "en"
]

TAMIL_SPEECH_TEXTS = {
    "greeting.mp3": "வணக்கம்! எங்கள் குழந்தைகள் இல்ல அறக்கட்டளைக்கு நல்வரவு. உங்களுக்கு எவ்வாறு உதவலாம்?",
    "about_home.mp3": "எங்கள் இல்லத்தில் 200-க்கும் மேற்பட்ட குழந்தைகளுக்கு தங்குமிடம், கல்வி மற்றும் மருத்துவ உதவிகளை வழங்கி வருகிறோம்.",
    "donation_usage.mp3": "உங்கள் நன்கொடை பணம் நேரடியாக குழந்தைகளின் கல்வி, உணவு மற்றும் அவசர மருத்துவ செலவுகளுக்கு பயன்படுத்தப்படுகிறது.",
    "tax_benefits.mp3": "எங்களுக்கு வழங்கப்படும் நன்கொடைகளுக்கு வருமான வரிச் சட்டம் 80G-யின் கீழ் 50 சதவீத வரி விலக்கு சான்றிதழ் வழங்கப்படும்.",
    "payment_methods.mp3": "நீங்கள் ஜிபே, போன்பே, UPI, அல்லது நேரடி வங்கி கணக்கு மாற்றம் மூலமாக சுலபமாக பணம் செலுத்தலாம்.",
    "sponsor_child.mp3": "ஒரு குழந்தையின் உணவிற்கும் கல்விக்கும் மாதம் 1,500 ரூபாய் ஆதரவு அளிக்கலாம்.",
    "volunteer.mp3": "எங்கள் இல்லத்தில் வார இறுதிகளில் குழந்தைகளுக்கு பாடம் சொல்லித்தர தன்னார்வலராக இணையலாம்.",
    "visiting_hours.mp3": "செவ்வாய் முதல் ஞாயிறு வரை காலை 10 மணி முதல் மாலை 5 மணி வரை பார்வையாளர்கள் வரலாம்.",
    "annual_report.mp3": "எங்கள் ஆண்டறிக்கை மற்றும் தணிக்கை கணக்கு விவரங்கள் இணையதளத்தில் வெளிப்படையாக வெளியிடப்பட்டுள்ளன.",
    "receipt_request.mp3": "நன்கொடை செலுத்திய 24 மணி நேரத்திற்குள் உங்களது அதிகாரப்பூர்வ வரி ரசீது வாட்ஸ்அப் அல்லது மின்னஞ்சலில் அனுப்பப்படும்.",
    "contact_us.mp3": "எங்களை தொடர்பு கொள்ள தொலைபேசி எண் 9876543210 அல்லது மின்னஞ்சல் வழியே தொடர்பு கொள்ளலாம்.",
    "supervisor_escalation.mp3": "நான் சமீபத்தில் தான் பணியில் சேர்ந்தேன். உங்கள் கேள்விக்கு பதில் அளிக்க எனது மேலதிகாரி அடுத்த 3 முதல் 5 நிமிடங்களில் உங்களை தொடர்புகொள்வார். நன்றி!",
    "fallback.mp3": "நான் சமீபத்தில் தான் பணியில் சேர்ந்தேன். உங்கள் கேள்விக்கு பதில் அளிக்க எனது மேலதிகாரி அடுத்த 3 முதல் 5 நிமிடங்களில் உங்களை தொடர்புகொள்வார். நன்றி!"
}

ENGLISH_SPEECH_TEXTS = {
    "greeting.mp3": "Hello and welcome to our children's home foundation. How can we assist your donation inquiry today?",
    "about_home.mp3": "Our foundation provides shelter, quality education, and healthcare for over 200 underprivileged children.",
    "donation_usage.mp3": "Your generous donations directly fund child nutrition, school tuition fees, books, and emergency medical care.",
    "tax_benefits.mp3": "All monetary donations made to our trust are eligible for 50 percent tax exemption under section 80G of the Income Tax Act.",
    "payment_methods.mp3": "You can donate securely via UPI using GPay, PhonePe, or Paytm, as well as direct bank wire transfers and credit cards.",
    "sponsor_child.mp3": "Sponsoring a child costs 1,500 rupees per month, covering complete educational material, daily meals, and uniform.",
    "volunteer.mp3": "We welcome volunteers! You can help by teaching weekend classes, organizing activities, or supporting our operations.",
    "visiting_hours.mp3": "Visitors are welcome from Tuesday to Sunday between 10 AM and 5 PM. Please call ahead to schedule your visit.",
    "annual_report.mp3": "Our annual audited balance sheet and impact report are published publicly on our website for complete transparency.",
    "receipt_request.mp3": "An official tax receipt will be instantly emailed and WhatsApped to you within 24 hours of your donation confirmation.",
    "contact_us.mp3": "You can contact our support team at phone 9876543210 or email support@childrenhome.org.",
    "supervisor_escalation.mp3": "I joined the organization recently. My supervisor will call you back in 3 to 5 minutes regarding your query. Thank you!",
    "fallback.mp3": "I joined the organization recently. My supervisor will call you back in 3 to 5 minutes regarding your query. Thank you!"
}

def convert_and_fix_all_audio_files():
    print("==================================================")
    print(" CONVERTING ALL AUDIO TO HIGH-COMPATIBILITY MP3   ")
    print("==================================================")

    for audio_dir in AUDIO_DIRS:
        audio_dir.mkdir(parents=True, exist_ok=True)
        is_tamil = "ta" in str(audio_dir)
        speech_dict = TAMIL_SPEECH_TEXTS if is_tamil else ENGLISH_SPEECH_TEXTS
        lang_code = "ta" if is_tamil else "en"

        print(f"\nProcessing Folder: {audio_dir}")

        # 1. Clean up old raw .aac and .ogg files that cause browser HTML5 decoding errors
        raw_files = list(audio_dir.glob("*.aac")) + list(audio_dir.glob("*.ogg"))
        for raw in raw_files:
            print(f" -> Removing raw non-standard browser format: {raw.name}")
            try:
                raw.unlink()
            except Exception:
                pass

        # 2. Generate clean spoken MP3 files for all intents
        for filename, speech_text in speech_dict.items():
            mp3_path = audio_dir / filename
            
            # Re-generate clean MP3 if file size is around 110,294 bytes (old synthetic beep) or missing
            need_generate = True
            if mp3_path.exists():
                size = mp3_path.stat().st_size
                if size != 110294 and size > 5000:
                    need_generate = False

            if need_generate:
                print(f" -> Generating crystal clear spoken MP3: {filename}")
                try:
                    tts = gTTS(text=speech_text, lang=lang_code)
                    tts.save(str(mp3_path))
                    print(f"    SUCCESS: Created {filename} ({mp3_path.stat().st_size} bytes)")
                except Exception as e:
                    print(f"    ERROR generating {filename}: {e}")
            else:
                print(f" -> Preserved valid spoken audio: {filename} ({mp3_path.stat().st_size} bytes)")

    print("\n==================================================")
    print(" ALL AUDIO FILES CONVERTED TO CRYSTAL CLEAR MP3! ")
    print("==================================================")

if __name__ == "__main__":
    convert_and_fix_all_audio_files()
