"""
FastAPI application — REST API and voice conversation endpoint.

Endpoints:
  POST /api/converse          — Send audio, get audio response + metadata
  POST /api/converse/text     — Send text, get text response (for testing)
  GET  /api/doctors           — List all doctors
  GET  /api/slots/{doctor_id} — Available slots for a doctor
  GET  /api/appointments      — List all appointments
  POST /api/campaigns/trigger — Trigger an outbound campaign
"""
import base64
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import DEFAULT_LANGUAGE
from app.database import SessionLocal, seed_database
from app.models import Appointment, Doctor, Slot
from agents.voice_agent import get_agent
from latency.tracker import LatencyTracker
from memory.memory_manager import SessionMemory
from pipeline.language import detect_language
from pipeline.stt import transcribe
from pipeline.tts import synthesize

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("voice-ai")


# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Seed DB on startup."""
    seed_database()
    logger.info("🚀 Voice AI Agent backend started.")
    yield
    logger.info("👋 Shutting down.")


app = FastAPI(
    title="Voice AI Agent — Clinical Appointment Booking",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Voice conversation endpoint (audio in → audio out)
# ---------------------------------------------------------------------------
@app.post("/api/converse")
async def converse(
    audio: UploadFile = File(...),
    session_id: str = Form(default=""),
):
    """
    Full voice pipeline:
    1. Speech-to-Text (faster-whisper)
    2. Language detection
    3. Agent reasoning + tool calling
    4. Text-to-Speech (edge-tts)

    Returns JSON with audio (base64), transcript, reasoning, and latency.
    """
    tracker = LatencyTracker()

    if not session_id:
        session_id = str(uuid.uuid4())

    session = SessionMemory(session_id)

    # --- 1. STT ---
    tracker.start("stt_ms")
    audio_bytes = await audio.read()
    text, stt_language, _ = transcribe(audio_bytes)
    tracker.stop("stt_ms")

    if not text.strip():
        return JSONResponse({"error": "Could not transcribe audio. Please try again."}, status_code=400)

    # --- 2. Language detection ---
    tracker.start("language_detection_ms")
    # Use Whisper's detected language if available, else detect from text
    language = stt_language if stt_language in {"en", "hi", "ta"} else detect_language(text)
    # Preserve language across session
    stored_lang = session.get_language()
    if stored_lang and stored_lang != "en":
        language = stored_lang
    session.set_language(language)
    tracker.stop("language_detection_ms")

    # --- 3. Agent reasoning ---
    tracker.start("agent_reasoning_ms")
    agent = get_agent()
    result = agent.process(session_id, text, language)
    response_text = result["response"]
    tool_calls = result["tool_calls"]
    tracker.stop("agent_reasoning_ms")

    # Save messages to session
    session.add_message("user", text)
    session.add_message("assistant", response_text)

    # --- 4. TTS ---
    tracker.start("tts_ms")
    tts_audio, _ = synthesize(response_text, language)
    tts_audio_b64 = base64.b64encode(tts_audio).decode("utf-8")
    tracker.stop("tts_ms")

    # --- Latency report ---
    latency = tracker.report()
    logger.info("📊 Latency report: %s", latency)

    return {
        "session_id": session_id,
        "user_text": text,
        "agent_response": response_text,
        "language": language,
        "tool_calls": tool_calls,
        "audio_base64": tts_audio_b64,
        "latency": latency,
    }


# ---------------------------------------------------------------------------
# Text conversation endpoint (for testing without mic)
# ---------------------------------------------------------------------------
@app.post("/api/converse/text")
async def converse_text(
    text: str = Form(...),
    session_id: str = Form(default=""),
    language: str = Form(default=""),
):
    """Text-only conversation endpoint for testing."""
    tracker = LatencyTracker()

    if not session_id:
        session_id = str(uuid.uuid4())

    session = SessionMemory(session_id)

    # Language detection
    tracker.start("language_detection_ms")
    if not language:
        language = detect_language(text)
    session.set_language(language)
    tracker.stop("language_detection_ms")

    # Agent reasoning
    tracker.start("agent_reasoning_ms")
    agent = get_agent()
    result = agent.process(session_id, text, language)
    tracker.stop("agent_reasoning_ms")

    session.add_message("user", text)
    session.add_message("assistant", result["response"])

    # TTS
    tracker.start("tts_ms")
    tts_audio, _ = synthesize(result["response"], language)
    tts_audio_b64 = base64.b64encode(tts_audio).decode("utf-8")
    tracker.stop("tts_ms")

    latency = tracker.report()

    return {
        "session_id": session_id,
        "user_text": text,
        "agent_response": result["response"],
        "language": language,
        "tool_calls": result["tool_calls"],
        "audio_base64": tts_audio_b64,
        "latency": latency,
    }


# ---------------------------------------------------------------------------
# REST endpoints for dashboard
# ---------------------------------------------------------------------------
@app.get("/api/doctors")
def list_doctors():
    """List all doctors with their specialties."""
    db = SessionLocal()
    try:
        doctors = db.query(Doctor).all()
        return [
            {"id": d.id, "name": d.name, "specialty": d.specialty}
            for d in doctors
        ]
    finally:
        db.close()


@app.get("/api/slots/{doctor_id}")
def list_slots(doctor_id: int):
    """List available slots for a specific doctor."""
    db = SessionLocal()
    try:
        slots = (
            db.query(Slot)
            .filter(
                Slot.doctor_id == doctor_id,
                Slot.is_booked == False,
                Slot.start_time > datetime.utcnow(),
            )
            .order_by(Slot.start_time)
            .limit(20)
            .all()
        )
        return [
            {
                "id": s.id,
                "start_time": s.start_time.isoformat(),
                "end_time": s.end_time.isoformat(),
            }
            for s in slots
        ]
    finally:
        db.close()


@app.get("/api/appointments")
def list_appointments():
    """List all appointments with doctor info."""
    db = SessionLocal()
    try:
        appointments = (
            db.query(Appointment)
            .order_by(Appointment.created_at.desc())
            .limit(50)
            .all()
        )
        result = []
        for apt in appointments:
            doctor = db.query(Doctor).filter(Doctor.id == apt.doctor_id).first()
            slot = db.query(Slot).filter(Slot.id == apt.slot_id).first()
            result.append({
                "id": apt.id,
                "patient_name": apt.patient_name,
                "patient_phone": apt.patient_phone,
                "doctor_name": doctor.name if doctor else "Unknown",
                "doctor_specialty": doctor.specialty if doctor else "",
                "slot_time": slot.start_time.isoformat() if slot else "",
                "status": apt.status,
                "language": apt.language,
                "created_at": apt.created_at.isoformat() if apt.created_at else "",
            })
        return result
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Campaign trigger
# ---------------------------------------------------------------------------
@app.post("/api/campaigns/trigger")
def trigger_campaign(campaign_type: str = Form(default="reminder")):
    """
    Trigger an outbound campaign.
    Types: 'reminder' (upcoming appointments) or 'followup' (past appointments).
    """
    from scheduling.campaigns import run_reminder_campaign, run_followup_campaign

    if campaign_type == "reminder":
        results = run_reminder_campaign()
    elif campaign_type == "followup":
        results = run_followup_campaign()
    else:
        return JSONResponse({"error": f"Unknown campaign type: {campaign_type}"}, status_code=400)

    return {"campaign_type": campaign_type, "results": results, "count": len(results)}


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/api/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}
