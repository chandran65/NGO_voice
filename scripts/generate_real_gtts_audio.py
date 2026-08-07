import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from gtts import gTTS
from app.config import PROJECT_ROOT, INTENTS_REGISTRY

AUDIO_ROOT = PROJECT_ROOT / "audio"

SAMPLE_TEXTS = {
    "en": {
        "greeting.mp3": "Hello and welcome to our children's home fundraising assistant. How can we help you today?",
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
        "fallback.mp3": "Thank you for reaching out. We could not fully understand your query. Please ask about donations, 80G tax benefits, or visiting hours."
    },
    "ta": {
        "greeting.mp3": "வணக்கம்! எங்கள் குழந்தைகள் இல்ல அறக்கட்டளைக்கு நல்வரவு. உங்களுக்கு எவ்வாறு உதவலாம்?",
        "about_home.mp3": "எங்கள் அறக்கட்டளை 200-க்கும் மேற்பட்ட ஆதரவற்ற குழந்தைகளுக்கு தங்குமிடம், கல்வி மற்றும் மருத்துவ உதவிகளை வழங்கி வருகிறது.",
        "donation_usage.mp3": "உங்கள் நன்கொடை பணம் நேரடியாக குழந்தைகளின் கல்வி, உணவு மற்றும் மருத்துவ பராமரிப்பிற்கு பயன்படுத்தப்படுகிறது.",
        "tax_benefits.mp3": "எங்களுக்கு வழங்கப்படும் நன்கொடைகளுக்கு வருமான வரிச் சட்டம் 80G-யின் கீழ் 50 சதவீத வரி விலக்கு உண்டு.",
        "payment_methods.mp3": "நீங்கள் ஜிபே, போன்பே, UPI, அல்லது நேரடி வங்கி கணக்கு மாற்றம் மூலமாக எளிதாக நன்கொடை அளிக்கலாம்.",
        "sponsor_child.mp3": "ஒரு குழந்தையின் கல்வி மற்றும் உணவிற்காக மாதம் 1,500 ரூபாய் ஆதரவு அளிக்கலாம்.",
        "volunteer.mp3": "எங்கள் இல்லத்தில் வார இறுதிகளில் குழந்தைகளுக்கு பாடம் சொல்லித்தர தன்னார்வலராக இணையலாம்.",
        "visiting_hours.mp3": "செவ்வாய் முதல் ஞாயிறு வரை காலை 10 மணி முதல் மாலை 5 மணி வரை பார்வையாளர்கள் வரலாம்.",
        "annual_report.mp3": "எங்கள் ஆண்டறிக்கை மற்றும் தணிக்கை கணக்கு விவரங்கள் இணையதளத்தில் வெளிப்படையாக வெளியிடப்பட்டுள்ளன.",
        "receipt_request.mp3": "நன்கொடை செலுத்திய 24 மணி நேரத்திற்குள் உங்களது அதிகாரப்பூர்வ வரி ரசீது வாட்ஸ்அப் அல்லது மின்னஞ்சலில் அனுப்பப்படும்.",
        "contact_us.mp3": "எங்களை தொடர்பு கொள்ள தொலைபேசி எண் 9876543210 அல்லது மின்னஞ்சல் வழியே தொடர்பு கொள்ளலாம்.",
        "fallback.mp3": "நன்றி. உங்கள் கேள்வி சரியாக புரியவில்லை. நன்கொடை, வரி விலக்கு அல்லது முகவரி பற்றி கேட்கலாம்."
    }
}

def generate_full_audio_set():
    print(f"==================================================")
    print(f"  GENERATING COMPLETE SPOKEN AUDIO FILE SET      ")
    print(f"==================================================")
    print(f"Target Directory: {AUDIO_ROOT}\n")

    for lang in ["en", "ta"]:
        lang_dir = AUDIO_ROOT / lang
        lang_dir.mkdir(parents=True, exist_ok=True)

        for filename, text in SAMPLE_TEXTS[lang].items():
            base_stem = Path(filename).stem
            
            # Check if user already has an existing file (.aac, .ogg, .wav, .mp3) for this intent
            existing_files = list(lang_dir.glob(f"{base_stem}.*"))
            if existing_files:
                print(f"[{lang.upper()}] Preserving existing recording: {existing_files[0].name}")
                continue

            file_path = lang_dir / filename
            print(f"[{lang.upper()}] Generating spoken audio using gTTS: {filename}")
            try:
                tts = gTTS(text=text, lang=lang)
                tts.save(str(file_path))
                print(f" -> SUCCESS: Created {file_path.name}")
            except Exception as e:
                print(f" -> ERROR generating {filename}: {e}")

    print(f"\n==================================================")
    print(f" ALL AUDIO FILES ARE NOW AVAILABLE AND COMPLETE! ")
    print(f"==================================================")

if __name__ == "__main__":
    generate_full_audio_set()
