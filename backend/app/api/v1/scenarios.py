from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_profile_dict
from app.api.serializers import scenario_to_dict, trend_to_detail
from app.db.session import get_db
from app.models import Scenario, Trend, User
from app.schemas import ScenarioListOut, ScenarioOut, ScenarioRequest
from app.services import generation
from app.services.personalization import rank_for_user

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


def _resolve_trend(db: Session, ref: str) -> Trend:
    trend = db.scalar(select(Trend).where(or_(Trend.id == ref, Trend.slug == ref)))
    if trend is None:
        raise HTTPException(status_code=404, detail="Trend not found")
    return trend


def _trend_payload(db: Session, trend: Trend) -> dict:
    """Flatten a trend into the shape the generators expect."""
    detail = trend_to_detail(db, trend, video_limit=8)
    detail["example_hooks"] = [
        v["analysis"]["hook"]
        for v in detail["videos"]
        if v.get("analysis") and v["analysis"].get("hook")
    ][:5]
    return detail


def _merge_profile(user: User, request: ScenarioRequest) -> dict:
    """Request fields win; the stored onboarding profile fills the gaps."""
    profile = get_profile_dict(user)
    overrides = {
        "niche": request.niche,
        "audience": request.audience,
        "audience_age": request.audience_age,
        "goal": request.goal,
        "preferred_style": request.preferred_style,
        "topic": request.topic,
        "production_capacity": request.production_capacity,
    }
    merged = {**profile, **{k: v for k, v in overrides.items() if v}}
    if request.platform:
        merged["platform"] = request.platform
        merged["platforms"] = [request.platform]
    elif merged.get("platforms"):
        merged["platform"] = merged["platforms"][0]
    if request.languages:
        merged["languages"] = request.languages
    return merged


@router.post("/generate", response_model=ScenarioListOut)
def generate(
    request: ScenarioRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    persist: bool = Query(True),
) -> ScenarioListOut:
    """Adapt a trending format to the caller's niche.

    Without ``trend_id`` the engine picks the trend that best fits the merged
    profile, so the generator is usable straight from onboarding.
    """
    profile = _merge_profile(user, request)

    if request.trend_id:
        trend = _resolve_trend(db, request.trend_id)
    else:
        candidates = db.scalars(
            select(Trend).order_by(Trend.opportunity_score.desc()).limit(40)
        ).all()
        if not candidates:
            raise HTTPException(status_code=409, detail="No trends available yet — run the pipeline")
        ranked = rank_for_user([_summary_for_ranking(t) for t in candidates], profile, limit=1)
        trend = db.get(Trend, ranked[0]["id"])

    payload = _trend_payload(db, trend)
    raw = generation.generate_scenarios(payload, profile, count=request.count)

    out: list[dict] = []
    for item in raw:
        if request.include_recording_guide:
            item["recording_guide"] = generation.generate_recording_guide(payload, item, profile)

        record = Scenario(
            user_id=user.id,
            trend_id=trend.id,
            title=item.get("title", "")[:260],
            hook=item.get("hook", ""),
            concept=item.get("concept", ""),
            script_structure=item.get("script_structure", []),
            caption=item.get("caption"),
            hashtags=item.get("hashtags", []),
            call_to_action=item.get("call_to_action", ""),
            suggested_duration_sec=item.get("suggested_duration_sec", 30),
            suggested_audio=item.get("suggested_audio"),
            difficulty=item.get("difficulty", "medium"),
            why_it_could_work=item.get("why_it_could_work", []),
            derived_from=item.get("derived_from"),
            recording_guide=item.get("recording_guide") or {},
            platform=profile.get("platform"),
            niche=profile.get("niche"),
            goal=profile.get("goal"),
            generator_model=item.get("generator_model"),
            kind=item.get("kind", "scenario"),
        )
        if persist:
            db.add(record)
            db.flush()
        out.append(scenario_to_dict(record, trend_name=trend.name))

    if persist:
        db.commit()
    return ScenarioListOut(items=[ScenarioOut(**s) for s in out], total=len(out))


def _summary_for_ranking(trend: Trend) -> dict:
    return {
        "id": trend.id,
        "niches": trend.niches or [],
        "platforms": trend.platforms or [],
        "languages": trend.languages or [],
        "content_types": trend.content_types or [],
        "adaptability": trend.adaptability,
        "production_difficulty": trend.production_difficulty,
        "opportunity_score": trend.opportunity_score,
        "score_breakdown": trend.score_breakdown or {},
    }


@router.post("/recreate/{trend_ref}", response_model=ScenarioOut)
def recreate(
    trend_ref: str,
    request: ScenarioRequest | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ScenarioOut:
    """The "Recreate" button: one complete, ready-to-shoot package."""
    trend = _resolve_trend(db, trend_ref)
    profile = _merge_profile(user, request or ScenarioRequest())
    payload = _trend_payload(db, trend)

    item = generation.generate_recreation(payload, profile)
    record = Scenario(
        user_id=user.id,
        trend_id=trend.id,
        title=item.get("title", "")[:260],
        hook=item.get("hook", ""),
        concept=item.get("concept", ""),
        script_structure=item.get("script_structure", []),
        caption=item.get("caption"),
        hashtags=item.get("hashtags", []),
        call_to_action=item.get("call_to_action", ""),
        suggested_duration_sec=item.get("suggested_duration_sec", 30),
        suggested_audio=item.get("suggested_audio"),
        difficulty=item.get("difficulty", "medium"),
        why_it_could_work=item.get("why_it_could_work", []),
        derived_from=item.get("derived_from"),
        recording_guide=item.get("recording_guide") or {},
        platform=profile.get("platform"),
        niche=profile.get("niche"),
        goal=profile.get("goal"),
        generator_model=item.get("generator_model"),
        kind="recreation",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return ScenarioOut(**scenario_to_dict(record, trend_name=trend.name))


@router.get("", response_model=ScenarioListOut)
def list_scenarios(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    kind: str | None = Query(None),
    trend_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> ScenarioListOut:
    stmt = select(Scenario).where(Scenario.user_id == user.id)
    if kind:
        stmt = stmt.where(Scenario.kind == kind)
    if trend_id:
        stmt = stmt.where(Scenario.trend_id == trend_id)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(Scenario.created_at.desc()).limit(limit).offset(offset)
    ).all()

    names = {
        t.id: t.name
        for t in db.scalars(
            select(Trend).where(Trend.id.in_([r.trend_id for r in rows if r.trend_id]))
        ).all()
    }
    return ScenarioListOut(
        items=[ScenarioOut(**scenario_to_dict(r, names.get(r.trend_id))) for r in rows],
        total=total,
    )


@router.get("/{scenario_id}", response_model=ScenarioOut)
def get_scenario(scenario_id: str, db: Session = Depends(get_db)) -> ScenarioOut:
    scenario = db.get(Scenario, scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    trend = db.get(Trend, scenario.trend_id) if scenario.trend_id else None
    return ScenarioOut(**scenario_to_dict(scenario, trend.name if trend else None))


@router.post("/{scenario_id}/recording-guide", response_model=ScenarioOut)
def regenerate_recording_guide(
    scenario_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ScenarioOut:
    """Generate (or regenerate) the shooting plan for an existing scenario."""
    scenario = db.get(Scenario, scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    trend = db.get(Trend, scenario.trend_id) if scenario.trend_id else None
    if trend is None:
        raise HTTPException(status_code=409, detail="Scenario is not linked to a trend")

    payload = _trend_payload(db, trend)
    scenario.recording_guide = generation.generate_recording_guide(
        payload, scenario_to_dict(scenario), get_profile_dict(user)
    )
    db.commit()
    db.refresh(scenario)
    return ScenarioOut(**scenario_to_dict(scenario, trend.name))
