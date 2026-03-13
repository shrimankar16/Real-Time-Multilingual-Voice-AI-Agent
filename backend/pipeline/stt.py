"""Speech-to-Text using faster-whisper (runs locally)."""
import io
import logging
import time

logger = logging.getLogger(__name__)

# Lazy-load model to avoid slow import at startup
_model = None


def _get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        from app.config import WHISPER_MODEL
        logger.info("Loading Whisper model '%s' …", WHISPER_MODEL)
        _model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
        logger.info("Whisper model loaded.")
    return _model


def transcribe(audio_bytes: bytes) -> tuple[str, str, float]:
    """
    Transcribe audio bytes to text.

    Returns:
        (transcribed_text, detected_language_code, duration_ms)
    """
    start = time.perf_counter()
    model = _get_model()

    # faster-whisper accepts file paths or file-like objects
    audio_file = io.BytesIO(audio_bytes)
    segments, info = model.transcribe(
        audio_file, 
        beam_size=1, 
        best_of=1,
        condition_on_previous_text=False
    )

    text = " ".join(seg.text for seg in segments).strip()
    language = info.language  # e.g., "en", "hi", "ta"
    duration_ms = round((time.perf_counter() - start) * 1000, 2)

    logger.info("STT [%s] (%.1f ms): %s", language, duration_ms, text[:100])
    return text, language, duration_ms
