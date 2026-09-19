from langdetect import DetectorFactory, detect

DetectorFactory.seed = 0

SUPPORTED = {
    "en": "English",
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
    "bn": "Bengali",
    "mr": "Marathi",
    "gu": "Gujarati",
    "kn": "Kannada",
    "ml": "Malayalam",
    "or": "Odia",
    "pa": "Punjabi",
}


def detect_language(text: str) -> str:
    try:
        lang = detect(text)
        return lang if lang in SUPPORTED else "en"
    except Exception:
        return "en"


def translate_text(text: str, src_lang: str, tgt_lang: str = "en") -> str:
    if not text or src_lang == tgt_lang:
        return text
    try:
        from deep_translator import GoogleTranslator

        return GoogleTranslator(source=src_lang, target=tgt_lang).translate(text)
    except Exception:
        return text


def translate_standard_fields(data: dict, tgt_lang: str) -> dict:
    if tgt_lang == "en":
        return data
    out = dict(data)
    for key in ("title", "abstract"):
        if out.get(key):
            out[key] = translate_text(out[key], "en", tgt_lang)
    return out
