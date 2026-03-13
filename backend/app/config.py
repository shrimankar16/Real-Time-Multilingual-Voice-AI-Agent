"""Application configuration using environment variables."""
import os
from pathlib import Path

from dotenv import load_dotenv

# --- Paths ---
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env from the backend directory
load_dotenv(BASE_DIR / ".env")
DATABASE_PATH = BASE_DIR / "clinic.db"

# --- LLM ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")

# --- Whisper STT ---
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "tiny")

# --- Redis (optional) ---
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", "1800"))  # 30 min

# --- Celery (optional) ---
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)

# --- TTS Voice mapping ---
TTS_VOICES = {
    "en": "en-US-AriaNeural",
    "hi": "hi-IN-SwaraNeural",
    "ta": "ta-IN-PallaviNeural",
}

DEFAULT_LANGUAGE = "en"
