"""Language detection and translation utilities."""
import logging

from langdetect import detect, LangDetectException
from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)

SUPPORTED_LANGUAGES = {"en", "hi", "ta"}

LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "ta": "Tamil",
}


def detect_language(text: str) -> str:
    """
    Detect language of the text. Returns ISO 639-1 code.
    Falls back to 'en' if detection fails or language is unsupported.
    """
    try:
        lang = detect(text)
        if lang in SUPPORTED_LANGUAGES:
            return lang
        logger.info("Detected unsupported language '%s', falling back to 'en'", lang)
        return "en"
    except LangDetectException:
        logger.warning("Language detection failed, falling back to 'en'")
        return "en"


def translate_text(text: str, source: str, target: str) -> str:
    """Translate text between languages using Google Translate (free)."""
    if source == target:
        return text
    try:
        translated = GoogleTranslator(source=source, target=target).translate(text)
        logger.info("Translated [%s→%s]: %s → %s", source, target, text[:50], translated[:50])
        return translated
    except Exception as e:
        logger.error("Translation failed: %s", e)
        return text  # return original if translation fails
