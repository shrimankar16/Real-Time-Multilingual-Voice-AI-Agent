"""Text-to-Speech using edge-tts (free Microsoft TTS)."""
import asyncio
import io
import logging
import time

import edge_tts

from app.config import TTS_VOICES, DEFAULT_LANGUAGE

logger = logging.getLogger(__name__)


def _get_voice(language: str) -> str:
    """Map language code to an edge-tts voice name."""
    return TTS_VOICES.get(language, TTS_VOICES[DEFAULT_LANGUAGE])


async def _synthesize_async(text: str, language: str) -> tuple[bytes, float]:
    """Async synthesis via edge-tts."""
    start = time.perf_counter()
    voice = _get_voice(language)
    communicate = edge_tts.Communicate(text, voice)

    audio_buffer = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_buffer.write(chunk["data"])

    audio_bytes = audio_buffer.getvalue()
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    logger.info("TTS [%s] (%.1f ms): %d bytes", language, duration_ms, len(audio_bytes))
    return audio_bytes, duration_ms


def synthesize(text: str, language: str = "en") -> tuple[bytes, float]:
    """
    Convert text to speech audio bytes (MP3 format).

    Returns:
        (audio_bytes, duration_ms)
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If called from within an async context, create a new thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, _synthesize_async(text, language))
                return future.result()
        else:
            return loop.run_until_complete(_synthesize_async(text, language))
    except RuntimeError:
        return asyncio.run(_synthesize_async(text, language))
