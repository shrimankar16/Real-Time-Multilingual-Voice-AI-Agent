"""Session and persistent memory management."""
import json
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import Patient

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Redis-backed session memory (with in-memory fallback)
# ---------------------------------------------------------------------------
_redis_client = None
_memory_store: dict[str, dict] = {}  # fallback in-memory store


def _get_redis():
    """Try to connect to Redis; return None if unavailable."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        import redis
        from app.config import REDIS_URL
        _redis_client = redis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=0.2, socket_timeout=0.2)
        _redis_client.ping()
        logger.info("✅ Redis connected.")
        return _redis_client
    except Exception:
        logger.warning("⚠️  Redis unavailable – using in-memory session store.")
        _redis_client = False  # sentinel: don't retry
        return None


class SessionMemory:
    """Per-conversation session memory with Redis TTL (or in-memory fallback)."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.key = f"session:{session_id}"

    def get(self) -> dict:
        """Retrieve current session state."""
        r = _get_redis()
        if r:
            data = r.get(self.key)
            return json.loads(data) if data else self._default()
        return _memory_store.get(self.key, self._default())

    def save(self, data: dict) -> None:
        """Persist session state."""
        from app.config import SESSION_TTL_SECONDS
        r = _get_redis()
        if r:
            r.setex(self.key, SESSION_TTL_SECONDS, json.dumps(data, default=str))
        else:
            _memory_store[self.key] = data

    def add_message(self, role: str, content: str) -> None:
        """Append a message to conversation history."""
        state = self.get()
        state["messages"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
        })
        self.save(state)

    def set_language(self, lang: str) -> None:
        """Set the detected language for this session."""
        state = self.get()
        state["language"] = lang
        self.save(state)

    def get_language(self) -> str:
        """Get the session language."""
        return self.get().get("language", "en")

    def _default(self) -> dict:
        return {"messages": [], "language": "en", "pending_booking": None}


# ---------------------------------------------------------------------------
# Persistent memory (SQLite-backed patient data)
# ---------------------------------------------------------------------------

class PersistentMemory:
    """Patient preferences and history stored in SQLite."""

    @staticmethod
    def get_or_create_patient(db: Session, name: str, phone: str) -> Patient:
        """Retrieve existing patient or create a new one."""
        patient = db.query(Patient).filter(Patient.phone == phone).first()
        if not patient:
            patient = Patient(name=name, phone=phone)
            db.add(patient)
            db.commit()
            db.refresh(patient)
            logger.info("Created new patient: %s (%s)", name, phone)
        return patient

    @staticmethod
    def update_language(db: Session, phone: str, language: str) -> None:
        """Update a patient's language preference."""
        patient = db.query(Patient).filter(Patient.phone == phone).first()
        if patient:
            patient.language_preference = language
            db.commit()
            logger.info("Updated language for %s to %s", phone, language)

    @staticmethod
    def get_patient_language(db: Session, phone: str) -> str | None:
        """Get a patient's stored language preference."""
        patient = db.query(Patient).filter(Patient.phone == phone).first()
        return patient.language_preference if patient else None
