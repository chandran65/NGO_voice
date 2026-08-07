import os
from pathlib import Path
from typing import Dict, List, Any

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

# Check for primary user audio folder at D:\DSM Project\audio first
EXTERNAL_AUDIO_DIR = PROJECT_ROOT / "audio"
if EXTERNAL_AUDIO_DIR.exists() and EXTERNAL_AUDIO_DIR.is_dir():
    AUDIO_DIR = EXTERNAL_AUDIO_DIR
else:
    AUDIO_DIR = BASE_DIR / "audio"

DB_PATH = BASE_DIR / "voice_fundraiser.db"

# Supported Languages (Default: Tamil)
SUPPORTED_LANGUAGES = {
    "ta": "Tamil",
    "en": "English"
}

# Confidence Thresholds
HIGH_CONFIDENCE_THRESHOLD = 0.70
CLARIFICATION_THRESHOLD = 0.50

# NGO Fundraising Outbound Campaign Intents Registry
INTENTS_REGISTRY: Dict[str, Dict[str, Any]] = {
    "GREETING": {
        "code": "GREETING",
        "name": "Greeting & NGO Pitch",
        "description_en": "General greeting and NGO fundraising outbound pitch.",
        "description_ta": "வணக்கம் மற்றும் அறக்கட்டளை அழைப்பு நல்வரவு செய்தி.",
        "file_name": "greeting.mp3",
        "chunk_ta": "வணக்கம்! எங்கள் குழந்தைகள் இல்ல அறக்கட்டளையிலிருந்து அழைக்கிறோம். ஆதரவற்ற குழந்தைகளின் கல்வி மற்றும் உணவு உதவி தொடர்பாக பேசுகிறோம்.",
        "chunk_en": "Hello! Calling from our children's home foundation regarding support for orphaned children's education and nutrition.",
        "phrases_en": [
            "hello", "hi", "hey", "good morning", "good afternoon", "vanakkam", "greetings", "hello agent"
        ],
        "phrases_ta": [
            "வணக்கம் சார்", "வணக்கம் மேடம்", "வணக்கம் நலமா", "ஹலோ சார்", "வணக்கம்", "வரவேற்பு", "வந்தனம்", "காலை வணக்கம்", "சார் நான் பேசுறது கேக்குதா சார்"
        ]
    },
    "DONATION_USAGE": {
        "code": "DONATION_USAGE",
        "name": "Donation Utilization",
        "description_en": "Details on how donated funds and resources are utilized for children.",
        "description_ta": "நன்கொடை பணம் மற்றும் உதவிகள் எவ்வாறு பயன்படுத்தப்படுகின்றன.",
        "file_name": "donation_usage.mp3",
        "chunk_ta": "உங்கள் நன்கொடை பணம் 100% முழுமையாக ஆதரவற்ற 200+ குழந்தைகளின் கல்வி, சத்தான உணவு மற்றும் மருத்துவ சிகிச்சைக்கு மட்டுமே பயன்படுத்தப்படுகிறது.",
        "chunk_en": "Your donation will be 100% utilized for children's education, nutritious meals, and healthcare.",
        "phrases_en": [
            "how is donation used", "where does money go", "how funds spent", "donation utilization",
            "how do you use my money", "financial transparency", "fund usage", "where is money utilized"
        ],
        "phrases_ta": [
            "நன்கொடை பணம்", "பணம் எப்படி பயன்படும்", "எதுக்கு செலவு", "நன்கொடை செலவு", "பயன்பாடு",
            "பணம் என்ன ஆகும்", "நன்கொடை எவ்வாறு பயன்படுத்தப்படுகிறது", "பணம் செலவழிக்கிறீர்கள்", "பணம் எப்படி செலவு பண்றீங்க"
        ]
    },
    "TAX_BENEFITS": {
        "code": "TAX_BENEFITS",
        "name": "80G Tax Exemption Benefits",
        "description_en": "Information about 80G tax exemption certificates for donations.",
        "description_ta": "80G வருமான வரி விலக்கு மற்றும் சான்றிதழ் விவரங்கள்.",
        "file_name": "tax_benefits.mp3",
        "chunk_ta": "எங்கள் அறக்கட்டளைக்கு நீங்கள் அளிக்கும் நன்கொடைகளுக்கு வருமான வரிச் சட்டம் 80G-ன் கீழ் 50% வரி விலக்கு பெறலாம்.",
        "chunk_en": "All monetary donations made to our trust are eligible for 50% tax exemption under Section 80G of the Income Tax Act.",
        "phrases_en": [
            "tax exemption", "80g certificate", "tax deduction", "income tax benefit",
            "do i get 80g", "tax rebate", "80g exemption"
        ],
        "phrases_ta": [
            "80g வருமான வரி விலக்கு", "வரி விலக்கு சான்றிதழ்", "வரி விலக்கு", "80g", "80ஜி",
            "இன்கம் டாக்ஸ்", "வரி சலுகை", "சான்றிதழ்", "டாக்ஸ் டிடக்ஷன்", "வரி விலக்கு கிடைக்குமா"
        ]
    },
    "PAYMENT_LINK": {
        "code": "PAYMENT_LINK",
        "name": "Send UPI / GPay Payment Link",
        "description_en": "Sending instant SMS or WhatsApp payment link for donation (UPI/GPay/PhonePe).",
        "description_ta": "நன்கொடை செலுத்த SMS அல்லது வாட்ஸ்அப் மூலம் UPI லிங்க் அனுப்புதல்.",
        "file_name": "payment_link.mp3",
        "chunk_ta": "உங்கள் மொபைல் எண்ணிற்கு ஆன்லைனில் பாதுகாப்பாக நன்கொடை செலுத்த SMS மூலம் UPI லிங்க் அனுப்பியுள்ளேன். GPay அல்லது PhonePe மூலம் செலுத்தலாம்.",
        "chunk_en": "I have sent an instant secure UPI payment link via SMS to your mobile number.",
        "phrases_en": [
            "send payment link", "how to donate online", "gpay payment link", "sms link",
            "send upi link", "pay online link", "whatsapp donation link"
        ],
        "phrases_ta": [
            "லிங்க் அனுப்புங்க", "ஆன்லைன்ல செலுத்தணும்", "எஸ்எம்எஸ் லிங்க் அனுப்புங்க", "ஜிபே லிங்க்",
            "வாட்ஸ்அப் லிங்க்", "பேமெண்ட் லிங்க்", "எப்படி ஆன்லைன்ல நன்கொடை தர்றது", "லிங்க் வருமா"
        ]
    },
    "SPONSOR_CHILD": {
        "code": "SPONSOR_CHILD",
        "name": "Sponsor a Child Plan",
        "description_en": "Options to sponsor a child's complete monthly education and food (Rs 1,500/month).",
        "description_ta": "ஒரு குழந்தையின் கல்வி மற்றும் உணவை மாதந்தோறும் ஆதரிக்கும் திட்டம்.",
        "file_name": "sponsor_child.mp3",
        "chunk_ta": "மாதம் 1,500 ரூபாய் வழங்கி ஒரு குழந்தையின் பள்ளி கட்டணம், புத்தகம் மற்றும் உணவை நீங்கள் முழுமையாக ஸ்பான்சர் செய்யலாம்.",
        "chunk_en": "You can sponsor a child's complete education, books, and meals for Rs. 1,500 per month.",
        "phrases_en": [
            "sponsor a child", "adopt child education", "1500 per month", "child sponsorship",
            "educational support", "feed a child", "monthly child support"
        ],
        "phrases_ta": [
            "ஒரு குழந்தைக்கு மாதம் 1500 ரூபாய்", "குழந்தை படிப்பு", "ஒரு குழந்தையை படிக்க வைக்க",
            "மாதம் 1500", "குழந்தை ஆதரவு", "ஸ்பான்சர்ஷிப்", "குழந்தை தத்தெடுப்பு", "கல்வி உதவி", "ஒரு குழந்தைக்கு உணவு"
        ]
    },
    "ADDRESS_UPDATE": {
        "code": "ADDRESS_UPDATE",
        "name": "Update Address & Contact Details",
        "description_en": "Updating donor residential address or email for sending tax receipts.",
        "description_ta": "கொடையாளரின் இருப்பிட முகவரி அல்லது தொடர்பு எண்களை மாற்றுதல்.",
        "file_name": "address_update.mp3",
        "chunk_ta": "உங்கள் முகவரி மாற்றக் கோரிக்கை பதிவு செய்யப்பட்டது. சரிபார்ப்பிற்காக SMS மூலம் விபரக் படிவம் அனுப்பப்பட்டுள்ளது.",
        "chunk_en": "Your address update request has been registered. An update verification form has been sent via SMS.",
        "phrases_en": [
            "update my address", "change location address", "change phone number", "update email",
            "correct address for receipt"
        ],
        "phrases_ta": [
            "முகவரி மாற்ற வேண்டும்", "அட்ரஸ் மாத்தணும்", "போன் நம்பர் மாத்தணும்", "அட்ரஸ் சேஞ்ச்",
            "முகவரி திருத்தம்", "என் புதிய முகவரி"
        ]
    },
    "CALLBACK_REQUEST": {
        "code": "CALLBACK_REQUEST",
        "name": "Schedule Callback Request",
        "description_en": "Scheduling a convenient time for donor relationship officer to call back.",
        "description_ta": "கொடையாளருக்கு வசதியான நேரத்தில் மீண்டும் அழைப்பு பெற பதிவு செய்தல்.",
        "file_name": "callback_request.mp3",
        "chunk_ta": "சரி, உங்கள் கோரிக்கை பதிவு செய்யப்பட்டது. எங்கள் அறக்கட்டளை பிரதிநிதி உங்களை உங்களுக்கு வசதியான நேரத்தில் தொடர்புகொள்வார்.",
        "chunk_en": "Sure, your callback request is registered. Our representative will call you back at your preferred time.",
        "phrases_en": [
            "call me later", "busy right now", "call back in evening", "schedule callback",
            "call tomorrow", "not convenient time"
        ],
        "phrases_ta": [
            "அப்புறம் கூப்பிடுங்க", "இப்போ பிஸியா இருக்கேன்", "நாளைக்கு கால் பண்ணுங்க", "சாயங்காலம் கூப்பிடுங்க",
            "வேற டைம்ல பேசுங்க", "அப்புறம் பேசுறேன்", "கால் பேக் பண்ணுங்க"
        ]
    },
    "RECEIPT_REQUEST": {
        "code": "RECEIPT_REQUEST",
        "name": "80G Donation Receipt",
        "description_en": "How to claim or receive an official 80G tax receipt after donation.",
        "description_ta": "நன்கொடை அளித்த பின் அதிகாரப்பூர்வ 80G ரசீது பெறுவது எப்படி.",
        "file_name": "receipt_request.mp3",
        "chunk_ta": "நன்கொடை செலுத்திய பின் உங்கள் பெயர் மற்றும் ஸ்கிரீன்ஷாட் அனுப்பினால் 24 மணி நேரத்தில் 80G அதிகாரப்பூர்வ ரசீது வாட்ஸ்அப் அல்லது இமெயிலில் அனுப்பப்படும்.",
        "chunk_en": "After donating, please share your confirmation screenshot to receive an official 80G receipt within 24 hours.",
        "phrases_en": [
            "donation receipt", "get receipt", "invoice confirmation", "whatsapp receipt", "official receipt"
        ],
        "phrases_ta": [
            "வாட்ஸ்அப்ல ஸ்கிரீன்ஷாட் அனுப்புங்க ரசீது அனுப்பிடுவாங்க", "ரசீது தருவீங்களா", "நன்கொடை ரசீது",
            "பில் சான்று", "ரசீது எப்போ வரும்", "ரசீது பெற", "ரசீது அனுப்புவீங்களா"
        ]
    },
    "COMPLAINT": {
        "code": "COMPLAINT",
        "name": "Donor Complaint / Grievance",
        "description_en": "Handling donor complaints or grievances (Triggers Human Escalation).",
        "description_ta": "கொடையாளர் புகார்கள் மற்றும் குறைதீர்ப்பு (உடனடி அதிகாரியிடம் ஒப்படைப்பு).",
        "file_name": "supervisor_escalation.mp3",
        "chunk_ta": "உங்கள் புகாரை நாங்கள் தீவிரமாக எடுத்துக்கொள்கிறோம். உங்கள் அழைப்பை அறக்கட்டளையின் மேலதிகாரியிடம் மாற்றுகிறேன்.",
        "chunk_en": "We take your concern seriously. Transferring your call to a senior foundation manager.",
        "phrases_en": [
            "complaint", "wrong charge", "fraud call", "bad service", "dissatisfied", "report issue", "grievance"
        ],
        "phrases_ta": [
            "புகார்", "தவறான சேவை", "மோசமான சர்வீஸ்", "கேம்பளைண்ட்", "பணம் பிடிச்சுட்டாங்க",
            "பிரச்சனை", "ஏமாத்துறீங்களா", "புகார் பதிவு பண்ணுங்க"
        ]
    },
    "AGENT_REQUEST": {
        "code": "AGENT_REQUEST",
        "name": "Speak to Human Officer",
        "description_en": "Donor explicitly asking to speak with a human fundraising officer.",
        "description_ta": "கொடையாளர் நேரடியாக மனித அதிகாரியிடம் பேச விரும்புதல்.",
        "file_name": "supervisor_escalation.mp3",
        "chunk_ta": "நிச்சயமாக. உங்கள் அழைப்பை அறக்கட்டளையின் நேரடி அதிகாரியிடம் மாற்றுகிறேன், தயவுசெய்து காத்திருக்கவும்.",
        "chunk_en": "Certainly. Transferring your call directly to a live fundraising representative. Please stay on the line.",
        "phrases_en": [
            "talk to human agent", "connect to representative", "speak to manager", "transfer call",
            "human support", "ngo officer", "connect me to person"
        ],
        "phrases_ta": [
            "மனித முகவரிடம் பேச வேண்டும்", "ஆளு கிட்ட பேசணும்", "ஏஜென்ட் கிட்ட மாத்துங்க", "அதிகாரி கிட்ட பேசுறேன்",
            "ஹியூமன் சப்போர்ட்", "ஆபிசர் கிட்ட மாத்துங்க", "பிரதிநிதி கூட பேசணும்", "நேரடியா பேசணும்", "நேரடியா ஏஜென்ட் கூட பேசுறேன்", "ஏஜென்ட் கூட பேசுறேன்"
        ]
    },
    "ABOUT_HOME": {
        "code": "ABOUT_HOME",
        "name": "About Children & Elder Home",
        "description_en": "Information about the children's shelter, elders, and foundation history.",
        "description_ta": "குழந்தைகள் மற்றும் முதியவர்கள் இல்லம் பற்றிய தகவல்கள்.",
        "file_name": "about_home.mp3",
        "chunk_ta": "எங்கள் அறக்கட்டளை 2012 முதல் 200-க்கும் மேற்பட்ட ஆதரவற்ற குழந்தைகளுக்கு உணவு, கல்வி மற்றும் தங்குமிடம் வழங்கி வருகிறது.",
        "chunk_en": "Our foundation has been providing shelter, education, and nutrition to over 200 children since 2012.",
        "phrases_en": [
            "about organization", "about home", "children shelter", "who are you", "what do you do",
            "tell me about foundation", "trust history"
        ],
        "phrases_ta": [
            "இல்லம் பற்றி", "அறக்கட்டளை பற்றி", "அறக்கட்டளை பத்தி", "உங்களோட அறக்கட்டளை பத்தி சொல்லுங்க", "உங்க இல்லத்தை பற்றி சொல்லுங்க", "இல்லத்தை பற்றி சொல்லுங்க",
            "உங்களைப் பத்தி", "யார் நீங்கள்", "என்ன பண்றீங்க", "குழந்தைகள் இல்லம்", "அறக்கட்டளை விவரம்"
        ]
    },
    "NUMBER_SOURCE": {
        "code": "NUMBER_SOURCE",
        "name": "How Did You Get My Number",
        "description_en": "Explaining how the donor's phone number was obtained for outbound call.",
        "description_ta": "கொடையாளரின் தொலைபேசி எண் எவ்வாறு பெறப்பட்டது என்பதற்கான விளக்கம்.",
        "file_name": "number_source.mp3",
        "chunk_ta": "எங்கள் அறக்கட்டளையின் பொது நன்கொடையாளர்கள் மற்றும் ஆதரவாளர்கள் பட்டியலிலிருந்து உங்கள் தொடர்பு எண் பெறப்பட்டது.",
        "chunk_en": "Your contact number was retrieved from our registered donor directory.",
        "phrases_en": [
            "how did you get my number", "where did you get my number", "who gave you my number"
        ],
        "phrases_ta": [
            "என் நம்பர் எப்படி கிடைச்சது", "என் போன் நம்பர் எப்படி வந்தது", "எங்க இருந்து நம்பர் எடுத்தீங்க", "நம்பர் யாரு கொடுத்தா"
        ]
    },
    "SUPERVISOR_ESCALATION": {
        "code": "SUPERVISOR_ESCALATION",
        "name": "Human Agent Handoff",
        "description_en": "Played during call transfer to live human agent.",
        "description_ta": "அழைப்பை நேரடி மனித முகவருக்கு மாற்றுவதற்கான அறிவிப்பு.",
        "file_name": "supervisor_escalation.mp3",
        "chunk_ta": "உங்கள் அழைப்பை அறக்கட்டளையின் நேரடி அதிகாரியிடம் மாற்றுகிறேன். தயவுசெய்து இணைப்பில் காத்திருக்கவும்.",
        "chunk_en": "Transferring your call to a live fundraising representative with full context. Please hold on.",
        "phrases_en": [],
        "phrases_ta": []
    },
    "FALLBACK_UNKNOWN": {
        "code": "FALLBACK_UNKNOWN",
        "name": "Ambiguous / General Fallback",
        "description_en": "Played when intent is unclear or confidence is low.",
        "description_ta": "தெளிவில்லாத அல்லது வரையறுக்கப்படாத கேள்விகளுக்கான பொதுவான பதில்.",
        "file_name": "supervisor_escalation.mp3",
        "chunk_ta": "மன்னிக்கவும், தாங்கள் கூறியதை என்னால் சரியாக விளங்கிக்கொள்ள முடியவில்லை. தெளிவுபடுத்த ஒரு முறை கூற முடியுமா?",
        "chunk_en": "Apologies, I couldn't understand that clearly. Could you please clarify your request?",
        "phrases_en": [],
        "phrases_ta": []
    }
}
