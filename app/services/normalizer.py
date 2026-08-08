import re
import unicodedata
import logging
from typing import Dict

logger = logging.getLogger(__name__)

# Common Tanglish to English/Tamil mappings
TANGLISH_MAP: Dict[str, str] = {
    "naan": "நான்",
    "nan": "நான்",
    "donation": "donation",
    "panna": "பண்ண",
    "virumburen": "விரும்புகிறேன்",
    "virumbugiren": "விரும்புகிறேன்",
    "gpay": "gpay",
    "g-pay": "gpay",
    "googlepay": "gpay",
    "google pay": "gpay",
    "phonepe": "phonepe",
    "phone pe": "phonepe",
    "upi": "upi",
    "receipt": "receipt",
    "raseedhu": "ரசீது",
    "rasithu": "ரசீது",
    "tax": "tax",
    "80g": "80g",
    "80ஜி": "80g",
    "80-g": "80g",
    "80 g": "80g",
    "use": "யூஸ்",
    "aagudhu": "ஆகுது",
    "aaguthu": "ஆகுது",
    "kettan": "கேட்டேன்",
    "ketaen": "கேட்டேன்",
    "agent": "ஏஜென்ட்",
    "officer": "அதிகாரி",
    "human": "ஹியூமன்",
    "complaint": "புகார்",
    "address": "முகவரி",
    "callback": "கால்பேக்",
    "number": "எண்",
    "phone": "போன்",
    "sponsor": "ஸ்பான்சர்",
    "child": "குழந்தை",
    "children": "குழந்தைகள்",
    "home": "இல்லம்",
}

# STT fillers to strip during normalization
STT_FILLERS = [
    r'(\b|\s|^)(சார்|மேடம்|ஹலோ|அப்படியா|இருங்க|ம்ம்+|ஆங்+|pls|please)(\b|\s|$)'
]

class TextNormalizer:
    @staticmethod
    def normalize(text: str, language: str = "ta") -> str:
        """
        Normalizes raw transcript string:
        1. Unicode normalization (NFKC)
        2. Lowercasing & trimming
        3. Noise/Punctuation removal & STT filler filtering
        4. Tanglish & common speech error mapping
        5. Whitespace collapsing
        """
        if not text:
            return ""

        # 1. Unicode NFKC normalization
        norm = unicodedata.normalize("NFKC", text)
        norm = norm.lower().strip()

        # 2. Filter STT speech filler noise
        for pattern in STT_FILLERS:
            norm = re.sub(pattern, " ", norm, flags=re.IGNORECASE)

        # 3. Clean non-alphanumeric noise while keeping Tamil unicode range (\u0B80-\u0BFF)
        norm = re.sub(r'[^\w\s\u0B80-\u0BFF]', ' ', norm)

        # 4. Split tokens & apply Tanglish / standard word normalization
        tokens = norm.split()
        normalized_tokens = []
        for token in tokens:
            # Check mapping dictionary
            mapped = TANGLISH_MAP.get(token, token)
            normalized_tokens.append(mapped)

        # 5. Remove adjacent duplicate tokens (speech stutter fix e.g. "விவரங்களை விவரங்களை")
        dedup_tokens = []
        for tok in normalized_tokens:
            if not dedup_tokens or dedup_tokens[-1] != tok:
                dedup_tokens.append(tok)

        result = " ".join(dedup_tokens).strip()
        logger.debug(f"Normalized: '{text}' -> '{result}'")
        return result
