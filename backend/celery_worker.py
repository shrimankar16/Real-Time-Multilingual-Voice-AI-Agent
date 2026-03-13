"""Celery worker configuration for background campaign jobs."""
import os
import sys

# Ensure the backend directory is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Environment setup (so we don't need app.config)
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    from celery import Celery
    from app.config import CELERY_BROKER_URL

    celery_app = Celery(
        "voice_ai_campaigns",
        broker=CELERY_BROKER_URL,
        backend=CELERY_BROKER_URL,
    )

    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
    )

    @celery_app.task(name="campaigns.reminder")
    def task_reminder_campaign():
        """Celery task: Run appointment reminder campaign."""
        from scheduling.campaigns import run_reminder_campaign
        return run_reminder_campaign()

    @celery_app.task(name="campaigns.followup")
    def task_followup_campaign():
        """Celery task: Run follow-up campaign."""
        from scheduling.campaigns import run_followup_campaign
        return run_followup_campaign()

    print("✅ Celery worker configured. Run with: celery -A celery_worker worker --loglevel=info")

except ImportError:
    print("⚠️  Celery not installed. Campaign background jobs disabled.")
    celery_app = None
