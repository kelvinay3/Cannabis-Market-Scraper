from celery import Celery
from celery.schedules import crontab
from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "cannabis_intel",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.scrape_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="America/New_York",
    enable_utc=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    result_expires=86400,
)

celery_app.conf.beat_schedule = {
    # Scrape all active sources every 15 minutes
    "scrape-all-sources": {
        "task": "app.tasks.scrape_tasks.scrape_all_sources",
        "schedule": crontab(minute="*/15"),
    },
    # Weekly CRC registry sync — Sunday 2am ET
    "sync-crc-registry": {
        "task": "app.tasks.scrape_tasks.sync_crc_registry",
        "schedule": crontab(hour=2, minute=0, day_of_week="sun"),
    },
    # Daily deal expiry check — midnight ET
    "expire-stale-deals": {
        "task": "app.tasks.scrape_tasks.expire_stale_deals",
        "schedule": crontab(hour=0, minute=5),
    },
    # Alert evaluation — every 20 minutes
    "evaluate-alerts": {
        "task": "app.tasks.scrape_tasks.evaluate_pending_alerts",
        "schedule": crontab(minute="*/20"),
    },
}
