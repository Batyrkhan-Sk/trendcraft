"""Background job queue.

Cadences are deliberately different per stage:

* **collect** every 3h — platform data does not move faster than that, and the
  YouTube quota (10k units/day, 100 per search) will not tolerate polling.
* **analyse** every 10 min — a queue drain. Video analysis is the slow, expensive
  stage, so it runs continuously in small batches instead of in one nightly spike.
* **rebuild** nightly — cluster boundaries only need to be correct once a day.
* **refresh_metrics** hourly — cheap re-reads of counters on recent videos, which
  is what makes view velocity a real measurement rather than a lifetime average.
"""

from __future__ import annotations

import logging

from celery import Celery
from celery.schedules import crontab

from app.ai import client
from app.core.config import settings
from app.db.session import SessionLocal
from app.pipeline import runner

logger = logging.getLogger(__name__)

celery_app = Celery("trendcraft", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=1800,
    worker_max_tasks_per_child=50,
    beat_schedule={
        "collect-every-3h": {
            "task": "trendcraft.collect",
            "schedule": crontab(minute=0, hour="*/3"),
        },
        "analyze-every-10min": {
            "task": "trendcraft.analyze",
            "schedule": crontab(minute="*/10"),
        },
        "refresh-metrics-hourly": {
            "task": "trendcraft.refresh_metrics",
            "schedule": crontab(minute=30),
        },
        # Once a day, just after the free-tier quota resets. The whole day's
        # allowance goes to upgrading heuristic rows, most-visible first.
        "upgrade-fallbacks-daily": {
            "task": "trendcraft.upgrade_fallbacks",
            "schedule": crontab(minute=30, hour=8),
            "kwargs": {"limit": 40},
        },
        "rebuild-trends-nightly": {
            "task": "trendcraft.rebuild_trends",
            "schedule": crontab(minute=15, hour=3),
        },
    },
)

DEFAULT_NICHES = [
    "ai",
    "technology",
    "productivity",
    "business",
    "fitness",
    "food",
    "finance",
    "beauty",
]


@celery_app.task(name="trendcraft.collect")
def collect(platforms: list[str] | None = None, niches: list[str] | None = None) -> dict:
    with SessionLocal() as db:
        results = []
        for platform in platforms or ["youtube", "tiktok", "instagram"]:
            for niche in niches or DEFAULT_NICHES:
                results.append(runner.ingest_platform(db, platform, niche=niche, limit=50))
        return {"results": results}


@celery_app.task(name="trendcraft.analyze")
def analyze(limit: int = 40) -> dict:
    with SessionLocal() as db:
        return runner.analyze_pending(db, limit=limit)


@celery_app.task(name="trendcraft.upgrade_fallbacks")
def upgrade_fallbacks(limit: int = 40) -> dict:
    """Spend the day's model quota re-analysing the most visible heuristic rows.

    The exhaustion breaker is per-process and nothing else clears it, so a worker
    that hit the wall yesterday would skip every video today without ever issuing
    a request. Reset it here: this task is the start of a fresh quota day.
    """
    client.reset_exhausted()
    with SessionLocal() as db:
        return runner.upgrade_fallbacks(db, limit=limit)


@celery_app.task(name="trendcraft.refresh_metrics")
def refresh_metrics() -> dict:
    """Re-read counters on recent videos so velocity has fresh deltas."""
    with SessionLocal() as db:
        return runner.ingest_platform(db, "youtube", limit=50)


@celery_app.task(name="trendcraft.rebuild_trends")
def rebuild_trends(lookback_days: int = 30) -> dict:
    with SessionLocal() as db:
        return runner.rebuild_trends(db, lookback_days=lookback_days)


@celery_app.task(name="trendcraft.full_pipeline")
def full_pipeline() -> dict:
    with SessionLocal() as db:
        return runner.run_full_pipeline(db, niches=DEFAULT_NICHES)
