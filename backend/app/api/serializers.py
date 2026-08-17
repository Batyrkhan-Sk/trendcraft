"""ORM -> API dict conversion.

Kept out of the routers so the shape the frontend consumes is defined in exactly
one place.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Scenario, Trend, TrendVideo, Video
from app.services.scoring import explain_opportunity


def video_to_dict(video: Video, *, similarity: float | None = None,
                  creator_lift: float | None = None) -> dict:
    analysis = video.analysis
    return {
        "id": video.id,
        "platform": video.platform,
        "external_id": video.external_id,
        "url": video.url,
        "thumbnail_url": video.thumbnail_url,
        "caption": video.caption,
        "hashtags": video.hashtags or [],
        "published_at": video.published_at,
        "duration_sec": video.duration_sec,
        "views": video.views,
        "likes": video.likes,
        "comments": video.comments,
        "shares": video.shares,
        "saves": video.saves,
        "engagement_rate": round(video.engagement_rate, 5),
        "niche": video.niche,
        "language": video.language,
        "country": video.country,
        "sound_name": video.sound_name,
        "similarity": similarity,
        "creator_lift": creator_lift,
        "creator": {
            "id": video.creator.id,
            "platform": video.creator.platform,
            "handle": video.creator.handle,
            "display_name": video.creator.display_name,
            "avatar_url": video.creator.avatar_url,
            "followers": video.creator.followers,
            "baseline_median_views": video.creator.baseline_median_views,
        }
        if video.creator
        else None,
        "analysis": {
            "hook": analysis.hook,
            "topic": analysis.topic,
            "content_format": analysis.content_format,
            "narrative_structure": analysis.narrative_structure or [],
            "speaking_style": analysis.speaking_style,
            "visual_style": analysis.visual_style,
            "editing_patterns": analysis.editing_patterns or [],
            "caption_style": analysis.caption_style,
            "call_to_action": analysis.call_to_action,
            "emotional_tone": analysis.emotional_tone,
            "audio_style": analysis.audio_style,
            "target_audience": analysis.target_audience,
            "main_message": analysis.main_message,
            "opening_frames": analysis.opening_frames,
            "key_moments": analysis.key_moments or [],
            "production_difficulty": analysis.production_difficulty,
            "extraction_model": analysis.extraction_model,
            "is_fallback": analysis.is_fallback,
        }
        if analysis
        else None,
    }


def _sparkline(trend: Trend, points: int = 14) -> list[float]:
    """Cumulative adoption curve, normalised to 0–1 for the card chart."""
    snaps = sorted(trend.snapshots, key=lambda s: s.captured_at)[-points:]
    if not snaps:
        return []
    counts = [float(s.video_count) for s in snaps]
    hi = max(counts) or 1.0
    return [round(c / hi, 3) for c in counts]


def trend_to_summary(db: Session, trend: Trend, *, exemplars: int = 3) -> dict:
    data = {
        "id": trend.id,
        "slug": trend.slug,
        "name": trend.name,
        "summary": trend.summary or "",
        "format_pattern": trend.format_pattern,
        "status": trend.status,
        "competition_level": trend.competition_level,
        "trend_score": trend.trend_score,
        "opportunity_score": trend.opportunity_score,
        "video_count": trend.video_count,
        "creator_count": trend.creator_count,
        "avg_views": trend.avg_views,
        "median_views": trend.median_views,
        "avg_engagement_rate": trend.avg_engagement_rate,
        "growth_24h": trend.growth_24h,
        "growth_7d": trend.growth_7d,
        "creator_normalized_lift": trend.creator_normalized_lift,
        "median_duration_sec": trend.median_duration_sec,
        "platforms": trend.platforms or [],
        "niches": trend.niches or [],
        "countries": trend.countries or [],
        "languages": trend.languages or [],
        "content_types": trend.content_types or [],
        "production_difficulty": trend.production_difficulty,
        "adaptability": trend.adaptability,
        "first_seen_at": trend.first_seen_at,
        "last_computed_at": trend.last_computed_at,
        "sparkline": _sparkline(trend),
        "exemplars": [],
    }
    if exemplars:
        rows = db.execute(
            select(Video, TrendVideo)
            .join(TrendVideo, TrendVideo.video_id == Video.id)
            .where(TrendVideo.trend_id == trend.id, TrendVideo.is_exemplar.is_(True))
            .order_by(TrendVideo.similarity.desc())
            .limit(exemplars)
        ).all()
        data["exemplars"] = [
            video_to_dict(v, similarity=tv.similarity, creator_lift=tv.creator_lift)
            for v, tv in rows
        ]
    return data


def trend_to_detail(db: Session, trend: Trend, *, video_limit: int = 24) -> dict:
    data = trend_to_summary(db, trend, exemplars=4)
    rows = db.execute(
        select(Video, TrendVideo)
        .join(TrendVideo, TrendVideo.video_id == Video.id)
        .where(TrendVideo.trend_id == trend.id)
        .order_by(TrendVideo.similarity.desc())
        .limit(video_limit)
    ).all()

    data.update(
        {
            "why_it_works": trend.why_it_works or [],
            "format_structure": trend.format_structure or [],
            "common_elements": trend.common_elements or [],
            "score_breakdown": trend.score_breakdown or {},
            "opportunity_explanation": explain_opportunity(
                {
                    "score_breakdown": trend.score_breakdown or {},
                    "competition_level": trend.competition_level,
                    "adaptability": trend.adaptability,
                    "production_difficulty": trend.production_difficulty,
                }
            ),
            "snapshots": [
                {
                    "captured_at": s.captured_at,
                    "video_count": s.video_count,
                    "creator_count": s.creator_count,
                    "total_views": s.total_views,
                    "avg_engagement_rate": s.avg_engagement_rate,
                    "trend_score": s.trend_score,
                }
                for s in sorted(trend.snapshots, key=lambda s: s.captured_at)
            ],
            "videos": [
                video_to_dict(v, similarity=tv.similarity, creator_lift=tv.creator_lift)
                for v, tv in rows
            ],
        }
    )
    return data


def scenario_to_dict(scenario: Scenario, trend_name: str | None = None) -> dict:
    return {
        "id": scenario.id,
        "trend_id": scenario.trend_id,
        "trend_name": trend_name,
        "title": scenario.title,
        "hook": scenario.hook,
        "concept": scenario.concept,
        "script_structure": scenario.script_structure or [],
        "caption": scenario.caption,
        "hashtags": scenario.hashtags or [],
        "call_to_action": scenario.call_to_action,
        "suggested_duration_sec": scenario.suggested_duration_sec,
        "suggested_audio": scenario.suggested_audio,
        "difficulty": scenario.difficulty,
        "why_it_could_work": scenario.why_it_could_work or [],
        "derived_from": scenario.derived_from,
        "recording_guide": scenario.recording_guide or None,
        "platform": scenario.platform,
        "niche": scenario.niche,
        "goal": scenario.goal,
        "kind": scenario.kind,
        "generator_model": scenario.generator_model,
        "created_at": scenario.created_at,
    }
