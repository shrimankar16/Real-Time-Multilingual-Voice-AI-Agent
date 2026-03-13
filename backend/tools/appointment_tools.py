"""Appointment management tools for the LangChain agent."""
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Appointment, Doctor, Slot

logger = logging.getLogger(__name__)


def _get_db() -> Session:
    return SessionLocal()


def get_available_slots(doctor_name: str, date: str = "") -> str:
    """
    Get available appointment slots for a doctor.

    Args:
        doctor_name: Full or partial name of the doctor (e.g., "Sharma", "Dr. Sharma").
        date: Optional date in YYYY-MM-DD format. If empty, returns slots for all upcoming days.

    Returns:
        A formatted string listing available slots.
    """
    db = _get_db()
    try:
        # Find doctor by partial name match
        doctor = db.query(Doctor).filter(
            Doctor.name.ilike(f"%{doctor_name.replace('Dr.', '').replace('Dr', '').strip()}%")
        ).first()

        if not doctor:
            return f"No doctor found matching '{doctor_name}'. Available doctors: Dr. Sharma (Cardiology), Dr. Priya (Dermatology), Dr. Ravi (Orthopedics)."

        query = db.query(Slot).filter(
            Slot.doctor_id == doctor.id,
            Slot.is_booked == False,
            Slot.start_time > datetime.utcnow(),
        )

        if date:
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d").date()
                query = query.filter(
                    Slot.start_time >= datetime(target_date.year, target_date.month, target_date.day),
                    Slot.start_time < datetime(target_date.year, target_date.month, target_date.day + 1 if target_date.day < 28 else 1),
                )
            except ValueError:
                pass

        slots = query.order_by(Slot.start_time).limit(10).all()

        if not slots:
            return f"No available slots found for {doctor.name}. They may be fully booked."

        slot_list = "\n".join(
            f"  • {s.start_time.strftime('%Y-%m-%d %I:%M %p')} – {s.end_time.strftime('%I:%M %p')}"
            for s in slots
        )
        return f"Available slots for {doctor.name} ({doctor.specialty}):\n{slot_list}"
    finally:
        db.close()


def book_appointment(patient_name: str, patient_phone: str, doctor_name: str, slot_time: str, language: str = "en") -> str:
    """
    Book an appointment for a patient.

    Args:
        patient_name: Full name of the patient.
        patient_phone: Phone number of the patient.
        doctor_name: Name of the doctor.
        slot_time: Desired slot start time in 'YYYY-MM-DD HH:MM' format (24-hour).
        language: Language code (en, hi, ta).

    Returns:
        Confirmation message or conflict information with alternatives.
    """
    db = _get_db()
    try:
        # Find doctor
        doctor = db.query(Doctor).filter(
            Doctor.name.ilike(f"%{doctor_name.replace('Dr.', '').replace('Dr', '').strip()}%")
        ).first()

        if not doctor:
            return f"Doctor '{doctor_name}' not found. Available: Dr. Sharma, Dr. Priya, Dr. Ravi."

        # Parse requested time
        try:
            requested_time = datetime.strptime(slot_time, "%Y-%m-%d %H:%M")
        except ValueError:
            return f"Invalid time format '{slot_time}'. Please use YYYY-MM-DD HH:MM (24hr)."

        # Prevent booking in the past
        if requested_time < datetime.utcnow():
            return "Cannot book appointments in the past. Please choose a future time."

        # Find the matching slot
        slot = db.query(Slot).filter(
            Slot.doctor_id == doctor.id,
            Slot.start_time == requested_time,
        ).first()

        if not slot:
            return f"No slot exists at {slot_time} for {doctor.name}. Please check available slots first."

        # Check if already booked (conflict)
        if slot.is_booked:
            # Suggest alternatives
            alternatives = db.query(Slot).filter(
                Slot.doctor_id == doctor.id,
                Slot.is_booked == False,
                Slot.start_time > requested_time,
            ).order_by(Slot.start_time).limit(3).all()

            if alternatives:
                alt_list = ", ".join(
                    a.start_time.strftime("%I:%M %p") for a in alternatives
                )
                return (
                    f"CONFLICT: {doctor.name} is already booked at {slot_time}. "
                    f"Next available slots: {alt_list}. Would you like to book one of these?"
                )
            return f"CONFLICT: {doctor.name} is fully booked around that time. No nearby alternatives available."

        # Book the slot
        slot.is_booked = True
        appointment = Appointment(
            patient_name=patient_name,
            patient_phone=patient_phone,
            doctor_id=doctor.id,
            slot_id=slot.id,
            status="confirmed",
            language=language,
        )
        db.add(appointment)
        db.commit()

        return (
            f"✅ Appointment confirmed!\n"
            f"  Patient: {patient_name}\n"
            f"  Doctor: {doctor.name} ({doctor.specialty})\n"
            f"  Time: {slot.start_time.strftime('%Y-%m-%d %I:%M %p')} – {slot.end_time.strftime('%I:%M %p')}\n"
            f"  Appointment ID: {appointment.id}"
        )
    finally:
        db.close()


def cancel_appointment(appointment_id: int) -> str:
    """
    Cancel an existing appointment by its ID.

    Args:
        appointment_id: The unique appointment ID.

    Returns:
        Confirmation of cancellation.
    """
    db = _get_db()
    try:
        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appointment:
            return f"No appointment found with ID {appointment_id}."

        if appointment.status == "cancelled":
            return f"Appointment {appointment_id} is already cancelled."

        # Free the slot
        slot = db.query(Slot).filter(Slot.id == appointment.slot_id).first()
        if slot:
            slot.is_booked = False

        appointment.status = "cancelled"
        db.commit()

        return f"✅ Appointment {appointment_id} has been cancelled. The slot is now available."
    finally:
        db.close()


def reschedule_appointment(appointment_id: int, new_slot_time: str) -> str:
    """
    Reschedule an existing appointment to a new time.

    Args:
        appointment_id: The appointment ID to reschedule.
        new_slot_time: New desired time in 'YYYY-MM-DD HH:MM' format (24-hour).

    Returns:
        Confirmation or error message.
    """
    db = _get_db()
    try:
        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appointment:
            return f"No appointment found with ID {appointment_id}."

        doctor = db.query(Doctor).filter(Doctor.id == appointment.doctor_id).first()

        # Parse new time
        try:
            new_time = datetime.strptime(new_slot_time, "%Y-%m-%d %H:%M")
        except ValueError:
            return f"Invalid time format. Please use YYYY-MM-DD HH:MM."

        if new_time < datetime.utcnow():
            return "Cannot reschedule to a past time."

        # Find new slot
        new_slot = db.query(Slot).filter(
            Slot.doctor_id == appointment.doctor_id,
            Slot.start_time == new_time,
        ).first()

        if not new_slot:
            return f"No slot at {new_slot_time} for {doctor.name}."

        if new_slot.is_booked:
            return f"CONFLICT: The slot at {new_slot_time} is already booked for {doctor.name}."

        # Free old slot
        old_slot = db.query(Slot).filter(Slot.id == appointment.slot_id).first()
        if old_slot:
            old_slot.is_booked = False

        # Book new slot
        new_slot.is_booked = True
        appointment.slot_id = new_slot.id
        appointment.status = "confirmed"
        db.commit()

        return (
            f"✅ Appointment {appointment_id} rescheduled!\n"
            f"  New time: {new_slot.start_time.strftime('%Y-%m-%d %I:%M %p')} – "
            f"{new_slot.end_time.strftime('%I:%M %p')}"
        )
    finally:
        db.close()


def get_patient_history(patient_phone: str) -> str:
    """
    Get appointment history for a patient by phone number.

    Args:
        patient_phone: The patient's phone number.

    Returns:
        Formatted list of past and upcoming appointments.
    """
    db = _get_db()
    try:
        appointments = (
            db.query(Appointment)
            .filter(Appointment.patient_phone == patient_phone)
            .order_by(Appointment.created_at.desc())
            .limit(10)
            .all()
        )

        if not appointments:
            return f"No appointment history found for phone number {patient_phone}."

        lines = [f"Appointment history for {patient_phone}:"]
        for apt in appointments:
            doctor = db.query(Doctor).filter(Doctor.id == apt.doctor_id).first()
            slot = db.query(Slot).filter(Slot.id == apt.slot_id).first()
            time_str = slot.start_time.strftime("%Y-%m-%d %I:%M %p") if slot else "N/A"
            lines.append(
                f"  • ID:{apt.id} | {doctor.name} | {time_str} | Status: {apt.status}"
            )
        return "\n".join(lines)
    finally:
        db.close()
