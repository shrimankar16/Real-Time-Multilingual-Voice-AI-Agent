"""Celery tasks for outbound campaign scheduling."""
import logging
from datetime import datetime, timedelta

from app.database import SessionLocal
from app.models import Appointment, Doctor, Slot

logger = logging.getLogger(__name__)


def _get_celery_app():
    """Lazy import to avoid circular deps when Celery is not installed."""
    try:
        from celery_worker import celery_app
        return celery_app
    except ImportError:
        return None


def run_reminder_campaign() -> list[dict]:
    """
    Fetch appointments for the next 24 hours and simulate reminder calls.

    Returns:
        List of reminder results.
    """
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        tomorrow = now + timedelta(hours=24)

        upcoming = (
            db.query(Appointment)
            .join(Slot)
            .filter(
                Appointment.status == "confirmed",
                Slot.start_time >= now,
                Slot.start_time <= tomorrow,
            )
            .all()
        )

        results = []
        for apt in upcoming:
            doctor = db.query(Doctor).filter(Doctor.id == apt.doctor_id).first()
            slot = db.query(Slot).filter(Slot.id == apt.slot_id).first()
            reminder = {
                "appointment_id": apt.id,
                "patient_name": apt.patient_name,
                "patient_phone": apt.patient_phone,
                "doctor": doctor.name if doctor else "Unknown",
                "time": slot.start_time.isoformat() if slot else "Unknown",
                "language": apt.language,
                "status": "reminder_sent",
                "message": f"Reminder: You have an appointment with {doctor.name} at {slot.start_time.strftime('%I:%M %p') if slot else 'N/A'} tomorrow.",
            }
            results.append(reminder)
            logger.info("📞 Reminder sent: %s → %s", apt.patient_phone, reminder["message"])

        logger.info("✅ Reminder campaign complete: %d reminders sent.", len(results))
        return results
    finally:
        db.close()


def run_followup_campaign() -> list[dict]:
    """
    Fetch appointments from the last 7 days and simulate follow-up calls.

    Returns:
        List of follow-up results.
    """
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)

        past = (
            db.query(Appointment)
            .join(Slot)
            .filter(
                Appointment.status == "confirmed",
                Slot.start_time >= week_ago,
                Slot.start_time < now,
            )
            .all()
        )

        results = []
        for apt in past:
            doctor = db.query(Doctor).filter(Doctor.id == apt.doctor_id).first()
            followup = {
                "appointment_id": apt.id,
                "patient_name": apt.patient_name,
                "patient_phone": apt.patient_phone,
                "doctor": doctor.name if doctor else "Unknown",
                "language": apt.language,
                "status": "followup_sent",
                "message": f"Follow-up: How was your visit with {doctor.name}? Please let us know if you need a follow-up.",
            }
            results.append(followup)
            logger.info("📞 Follow-up sent: %s → %s", apt.patient_phone, followup["message"])

        logger.info("✅ Follow-up campaign complete: %d follow-ups sent.", len(results))
        return results
    finally:
        db.close()
