"""Database engine, session factory, and seeding logic."""
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import DATABASE_PATH
from app.models import Base, Doctor, Slot

# ---------------------------------------------------------------------------
# Engine & Session
# ---------------------------------------------------------------------------
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    """FastAPI dependency that yields a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------
DOCTORS = [
    {"name": "Dr. Sharma", "specialty": "Cardiology"},
    {"name": "Dr. Priya", "specialty": "Dermatology"},
    {"name": "Dr. Ravi", "specialty": "Orthopedics"},
]

SLOT_START_HOUR = 9   # 9 AM
SLOT_END_HOUR = 17    # 5 PM
SLOT_DURATION_MIN = 30
DAYS_AHEAD = 7


def _generate_slots(doctor_id: int) -> list[Slot]:
    """Generate 30-min slots for the next DAYS_AHEAD days."""
    slots: list[Slot] = []
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    for day_offset in range(DAYS_AHEAD):
        day = today + timedelta(days=day_offset)
        current = day.replace(hour=SLOT_START_HOUR)
        end_of_day = day.replace(hour=SLOT_END_HOUR)
        while current < end_of_day:
            slot_end = current + timedelta(minutes=SLOT_DURATION_MIN)
            slots.append(
                Slot(
                    doctor_id=doctor_id,
                    start_time=current,
                    end_time=slot_end,
                    is_booked=False,
                )
            )
            current = slot_end
    return slots


def seed_database() -> None:
    """Create tables and seed doctors + slots if the DB is empty."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Doctor).count() == 0:
            for doc_data in DOCTORS:
                doctor = Doctor(**doc_data)
                db.add(doctor)
                db.flush()  # get doctor.id
                slots = _generate_slots(doctor.id)
                db.add_all(slots)
            db.commit()
            print(f"✅ Seeded {len(DOCTORS)} doctors with slots for {DAYS_AHEAD} days.")
        else:
            print("ℹ️  Database already seeded.")
    finally:
        db.close()
