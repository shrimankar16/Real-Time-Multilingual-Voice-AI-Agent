"""SQLAlchemy models for the clinic database."""
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    specialty = Column(String(100), nullable=False)

    slots = relationship("Slot", back_populates="doctor", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="doctor")

    def __repr__(self) -> str:
        return f"<Doctor {self.name} – {self.specialty}>"


class Slot(Base):
    __tablename__ = "slots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    is_booked = Column(Boolean, default=False)

    doctor = relationship("Doctor", back_populates="slots")

    def __repr__(self) -> str:
        return f"<Slot {self.start_time} – {self.end_time} booked={self.is_booked}>"


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_name = Column(String(100), nullable=False)
    patient_phone = Column(String(20), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    slot_id = Column(Integer, ForeignKey("slots.id"), nullable=False)
    status = Column(String(20), default="confirmed")  # confirmed | cancelled | rescheduled
    language = Column(String(10), default="en")
    created_at = Column(DateTime, default=datetime.utcnow)

    doctor = relationship("Doctor", back_populates="appointments")
    slot = relationship("Slot")

    def __repr__(self) -> str:
        return f"<Appointment {self.patient_name} with Dr.{self.doctor_id} – {self.status}>"


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), unique=True, nullable=False)
    language_preference = Column(String(10), default="en")
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Patient {self.name} ({self.phone})>"
