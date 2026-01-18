import os
from celery import Celery
from config import settings

# Get Redis URL from settings or environment
REDIS_URL = settings.REDIS_URL or os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Initialize Celery app
celery_app = Celery(
    "nalytiq_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
)

if __name__ == "__main__":
    celery_app.start()
