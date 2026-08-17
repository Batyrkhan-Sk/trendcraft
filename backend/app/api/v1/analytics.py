from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.serializers import trend_to_summary
from app.db.session import get_db
from app.models import Creator, Trend, TrendSnapshot, Video, VideoAnalysis
from app.schemas import AnalyticsOut, TrendSummary

router = APIRouter(prefix="/analytics", tags=["analytics"])

SCORE_BUCKETS = [(0, 20), (20, 40), (40, 60), (60, 80), (80, 101)]


@router.get("", response_model=AnalyticsOut)
def analytics(db: Session = Depends(get_db)) -> AnalyticsOut:
    trends = db.scalars(select(Trend)).all()

    totals = {
        "trends": len(trends),
        "videos": db.scalar(select(func.count()).select_from(Video)) or 0,
        "analyzed_videos": db.scalar(select(func.count()).select_from(VideoAnalysis)) or 0,
        "creators": db.scalar(select(func.count()).select_from(Creator)) or 0,
        "total_reach": sum(t.avg_views * t.video_count for t in trends),
        "avg_trend_score": round(
            sum(t.trend_score for t in trends) / max(1, len(trends)), 1
        ),
        "avg_opportunity": round(
            sum(t.opportunity_score for t in trends) / max(1, len(trends)), 1
        ),
    }

    platform_counts: dict[str, dict] = defaultdict(lambda: {"trends": 0, "videos": 0})
    for t in trends:
        for p in t.platforms or []:
            platform_counts[p]["trends"] += 1
            platform_counts[p]["videos"] += t.video_count
    by_platform = [
        {"platform": k, **v}
        for k, v in sorted(platform_counts.items(), key=lambda kv: -kv[1]["trends"])
    ]

    status_counts: dict[str, int] = defaultdict(int)
    for t in trends:
        status_counts[t.status] += 1
    by_status = [
        {"status": s, "count": status_counts.get(s, 0)}
        for s in ("emerging", "growing", "viral", "declining")
    ]

    niche_stats: dict[str, dict] = defaultdict(
        lambda: {"trends": 0, "opportunity_total": 0.0, "videos": 0}
    )
    for t in trends:
        for n in t.niches or []:
            niche_stats[n]["trends"] += 1
            niche_stats[n]["opportunity_total"] += t.opportunity_score
            niche_stats[n]["videos"] += t.video_count
    by_niche = sorted(
        [
            {
                "niche": k,
                "trends": v["trends"],
                "videos": v["videos"],
                "avg_opportunity": round(v["opportunity_total"] / max(1, v["trends"]), 1),
            }
            for k, v in niche_stats.items()
        ],
        key=lambda d: -d["trends"],
    )[:12]

    movers = sorted(trends, key=lambda t: -t.growth_7d)[:8]

    distribution = [
        {
            "bucket": f"{lo}-{min(hi, 100)}",
            "count": len([t for t in trends if lo <= t.opportunity_score < hi]),
        }
        for lo, hi in SCORE_BUCKETS
    ]

    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    rows = db.execute(
        select(
            func.date_trunc("day", TrendSnapshot.captured_at).label("day"),
            func.sum(TrendSnapshot.video_count),
            func.sum(TrendSnapshot.creator_count),
        )
        .where(TrendSnapshot.captured_at >= cutoff)
        .group_by("day")
        .order_by("day")
    ).all()
    timeline = [
        {"date": day.date().isoformat(), "videos": int(videos or 0), "creators": int(creators or 0)}
        for day, videos, creators in rows
    ]

    return AnalyticsOut(
        totals=totals,
        by_platform=by_platform,
        by_status=by_status,
        by_niche=by_niche,
        top_movers=[TrendSummary(**trend_to_summary(db, t, exemplars=1)) for t in movers],
        score_distribution=distribution,
        adoption_timeline=timeline,
    )
