from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_profile_dict
from app.api.serializers import scenario_to_dict, trend_to_summary
from app.db.session import get_db
from app.models import SavedItem, Scenario, Trend, User
from app.schemas import DashboardOut, TrendListOut, TrendSummary
from app.services.personalization import rank_for_user

router = APIRouter(tags=["feed"])


@router.get("/feed", response_model=TrendListOut)
def for_you(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    limit: int = Query(24, ge=1, le=100),
) -> TrendListOut:
    """The personalised "For You" feed."""
    profile = get_profile_dict(user)
    trends = db.scalars(select(Trend).order_by(Trend.opportunity_score.desc()).limit(120)).all()
    summaries = [trend_to_summary(db, t) for t in trends]
    ranked = rank_for_user(summaries, profile, limit=limit)
    return TrendListOut(items=[TrendSummary(**t) for t in ranked], total=len(ranked))


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DashboardOut:
    """Everything the "Your Content Intelligence" home screen needs, in one call."""
    profile = get_profile_dict(user)
    all_trends = db.scalars(select(Trend)).all()
    summaries = [trend_to_summary(db, t) for t in all_trends]
    by_id = {s["id"]: s for s in summaries}

    rising = sorted(
        [s for s in summaries if s["status"] in ("emerging", "growing")],
        key=lambda s: -s["growth_7d"],
    )[:6]
    best = sorted(summaries, key=lambda s: -s["opportunity_score"])[:6]

    ranked = rank_for_user(summaries, profile)
    niche = (profile.get("niche") or "").lower()
    in_niche = [
        s
        for s in ranked
        if niche and niche in {n.lower() for n in s.get("niches", [])}
    ][:6] or ranked[:6]

    cross = sorted(
        [s for s in summaries if len(s["platforms"]) >= 2],
        key=lambda s: (-len(s["platforms"]), -s["opportunity_score"]),
    )[:6]

    scenarios = db.scalars(
        select(Scenario)
        .where(Scenario.user_id == user.id)
        .order_by(Scenario.created_at.desc())
        .limit(4)
    ).all()

    saved_rows = db.scalars(
        select(SavedItem)
        .where(SavedItem.user_id == user.id)
        .order_by(SavedItem.created_at.desc())
        .limit(6)
    ).all()
    saved = []
    for row in saved_rows:
        entry = {
            "id": row.id,
            "entity_type": row.entity_type,
            "entity_id": row.entity_id,
            "note": row.note,
            "created_at": row.created_at,
            "trend": None,
            "scenario": None,
        }
        if row.entity_type == "trend" and row.entity_id in by_id:
            entry["trend"] = by_id[row.entity_id]
        elif row.entity_type == "scenario":
            s = db.get(Scenario, row.entity_id)
            if s:
                entry["scenario"] = scenario_to_dict(s)
        saved.append(entry)

    stats = {
        "tracked_trends": len(summaries),
        "videos_analyzed": sum(s["video_count"] for s in summaries),
        "creators_tracked": sum(s["creator_count"] for s in summaries),
        "rising_count": len([s for s in summaries if s["status"] in ("emerging", "growing")]),
        "viral_count": len([s for s in summaries if s["status"] == "viral"]),
        "avg_opportunity": round(
            sum(s["opportunity_score"] for s in summaries) / max(1, len(summaries)), 1
        ),
        "profile_complete": bool(profile.get("niche")),
    }

    return DashboardOut(
        rising_fast=[TrendSummary(**s) for s in rising],
        best_opportunities=[TrendSummary(**s) for s in best],
        in_your_niche=[TrendSummary(**s) for s in in_niche],
        cross_platform=[TrendSummary(**s) for s in cross],
        recommended_scenarios=[scenario_to_dict(s) for s in scenarios],
        recently_saved=saved,
        stats=stats,
    )
