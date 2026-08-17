from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.ai import client as llm
from app.connectors import all_connectors
from app.core.config import settings
from app.db.session import SessionLocal, get_db
from app.pipeline import runner
from app.schemas import PipelineRunIn

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.get("/status")
def status(db: Session = Depends(get_db)) -> dict:
    """What the system can currently do, and with which providers."""
    return {
        "connectors": {
            name: {"healthy": c.healthy(), "platform": c.platform}
            for name, c in all_connectors().items()
        },
        "ai": {
            "llm_configured": llm.available(),
            "llm_model": settings.llm_model,
            "vision_model": settings.vision_model,
            "embedding_provider": settings.embedding_provider
            if llm.available()
            else "local (no API key)",
            "embedding_dim": settings.embedding_dim,
        },
        "engine": {
            "min_cluster_size": settings.min_cluster_size,
            "cluster_similarity_threshold": settings.cluster_similarity_threshold,
            "trend_half_life_hours": settings.trend_half_life_hours,
        },
    }


def _run(payload: PipelineRunIn) -> None:
    with SessionLocal() as db:
        runner.run_full_pipeline(
            db,
            platforms=payload.platforms,
            niches=payload.niches,
            analyze_limit=payload.analyze_limit,
        )


@router.post("/run")
def run(payload: PipelineRunIn, background: BackgroundTasks) -> dict:
    """Trigger collection → analysis → clustering → scoring.

    Runs in-process by default so the platform is operable without a Celery
    worker; production deployments call the ``trendcraft.full_pipeline`` task.
    """
    if payload.async_run:
        background.add_task(_run, payload)
        return {"queued": True}
    with SessionLocal() as db:
        return runner.run_full_pipeline(
            db,
            platforms=payload.platforms,
            niches=payload.niches,
            analyze_limit=payload.analyze_limit,
        )


@router.post("/rebuild-trends")
def rebuild(lookback_days: int = 30, db: Session = Depends(get_db)) -> dict:
    return runner.rebuild_trends(db, lookback_days=lookback_days)


@router.post("/analyze")
def analyze(limit: int = 50, db: Session = Depends(get_db)) -> dict:
    return runner.analyze_pending(db, limit=limit)
