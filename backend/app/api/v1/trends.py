from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Text, func, or_, select
from sqlalchemy.orm import Session

from app.api.serializers import trend_to_detail, trend_to_summary
from app.db.session import get_db
from app.models import Trend
from app.schemas import TrendDetail, TrendListOut

router = APIRouter(prefix="/trends", tags=["trends"])

SortKey = Literal["opportunity", "trend_score", "growth_7d", "growth_24h", "engagement", "recency", "videos"]

SORT_COLUMNS = {
    "opportunity": Trend.opportunity_score.desc(),
    "trend_score": Trend.trend_score.desc(),
    "growth_7d": Trend.growth_7d.desc(),
    "growth_24h": Trend.growth_24h.desc(),
    "engagement": Trend.avg_engagement_rate.desc(),
    "recency": Trend.first_seen_at.desc(),
    "videos": Trend.video_count.desc(),
}


def _json_array_contains(column, value: str):
    """Portable ``value IN json_array`` check.

    The JSON columns hold plain string arrays, so a containment test against the
    text form is both correct and index-free-cheap at this table size. Swap for a
    ``jsonb ? :value`` operator if these tables grow past a few hundred thousand
    rows.
    """
    return column.cast(Text).ilike(f'%"{value}"%')


@router.get("", response_model=TrendListOut)
def list_trends(
    db: Session = Depends(get_db),
    platform: str | None = Query(None),
    niche: str | None = Query(None),
    country: str | None = Query(None),
    language: str | None = Query(None),
    content_type: str | None = Query(None),
    status: str | None = Query(None),
    competition: str | None = Query(None),
    difficulty: str | None = Query(None),
    min_growth: float | None = Query(None, description="Minimum 7-day growth, e.g. 0.25 for +25%"),
    min_engagement: float | None = Query(None, description="Minimum engagement rate, e.g. 0.06"),
    min_duration: float | None = Query(None),
    max_duration: float | None = Query(None),
    since_days: int | None = Query(None, description="Only trends first seen in the last N days"),
    q: str | None = Query(None, description="Free-text search over name, pattern and summary"),
    sort: SortKey = Query("opportunity"),
    limit: int = Query(48, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> TrendListOut:
    stmt = select(Trend)

    if platform:
        stmt = stmt.where(_json_array_contains(Trend.platforms, platform))
    if niche:
        stmt = stmt.where(_json_array_contains(Trend.niches, niche))
    if country:
        stmt = stmt.where(_json_array_contains(Trend.countries, country))
    if language:
        stmt = stmt.where(_json_array_contains(Trend.languages, language))
    if content_type:
        stmt = stmt.where(_json_array_contains(Trend.content_types, content_type))
    if status:
        stmt = stmt.where(Trend.status.in_(status.split(",")))
    if competition:
        stmt = stmt.where(Trend.competition_level.in_(competition.split(",")))
    if difficulty:
        stmt = stmt.where(Trend.production_difficulty.in_(difficulty.split(",")))
    if min_growth is not None:
        stmt = stmt.where(Trend.growth_7d >= min_growth)
    if min_engagement is not None:
        stmt = stmt.where(Trend.avg_engagement_rate >= min_engagement)
    if min_duration is not None:
        stmt = stmt.where(Trend.median_duration_sec >= min_duration)
    if max_duration is not None:
        stmt = stmt.where(Trend.median_duration_sec <= max_duration)
    if since_days is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)
        stmt = stmt.where(Trend.first_seen_at >= cutoff)
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(
            or_(
                Trend.name.ilike(pattern),
                Trend.format_pattern.ilike(pattern),
                Trend.summary.ilike(pattern),
            )
        )

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.order_by(SORT_COLUMNS[sort]).limit(limit).offset(offset)).all()

    return TrendListOut(
        items=[trend_to_summary(db, t) for t in rows],
        total=total,
        facets=_facets(db),
    )


def _facets(db: Session) -> dict[str, list[str]]:
    """Distinct filter values, derived from what is actually in the data."""
    trends = db.scalars(select(Trend)).all()

    def collect(attr: str) -> list[str]:
        values: dict[str, int] = {}
        for t in trends:
            for v in getattr(t, attr) or []:
                values[v] = values.get(v, 0) + 1
        return [k for k, _ in sorted(values.items(), key=lambda kv: -kv[1])]

    return {
        "platforms": collect("platforms"),
        "niches": collect("niches"),
        "countries": collect("countries"),
        "languages": collect("languages"),
        "content_types": collect("content_types"),
        "statuses": sorted({t.status for t in trends}),
        "competition_levels": sorted({t.competition_level for t in trends}),
        "difficulties": sorted({t.production_difficulty for t in trends}),
    }


@router.get("/{trend_ref}", response_model=TrendDetail)
def get_trend(trend_ref: str, db: Session = Depends(get_db)) -> TrendDetail:
    trend = db.scalar(select(Trend).where(or_(Trend.id == trend_ref, Trend.slug == trend_ref)))
    if trend is None:
        raise HTTPException(status_code=404, detail="Trend not found")
    return TrendDetail(**trend_to_detail(db, trend))
