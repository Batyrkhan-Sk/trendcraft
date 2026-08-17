"""End-to-end pipeline orchestration.

    collect → normalise → analyse → embed → cluster → score → narrate → persist

Each stage is independently callable so the scheduler can run them at different
cadences: collection every few hours, analysis continuously as a queue drain, and
the full re-cluster nightly.
"""

from __future__ import annotations

import logging
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai import embeddings
from app.core.config import settings
from app.connectors import NotConfigured, RawVideo, get_connector
from app.db.base import utcnow
from app.models import (
    Creator,
    Trend,
    TrendSnapshot,
    TrendVideo,
    Video,
    VideoAnalysis,
    VideoMetric,
)
from app.services import clustering, extraction, narrative, scoring

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Stage 1–2: collection and normalisation
# ---------------------------------------------------------------------------


def _upsert_creator(db: Session, raw: RawVideo) -> Creator:
    rc = raw.creator
    creator = db.scalar(
        select(Creator).where(Creator.platform == rc.platform, Creator.handle == rc.handle)
    )
    if creator is None:
        creator = Creator(
            platform=rc.platform,
            handle=rc.handle,
            display_name=rc.display_name,
            avatar_url=rc.avatar_url,
            followers=rc.followers,
            baseline_median_views=rc.baseline_median_views,
            niche=rc.niche,
            country=rc.country,
            language=rc.language,
        )
        db.add(creator)
        db.flush()
    else:
        creator.followers = rc.followers or creator.followers
        creator.display_name = rc.display_name or creator.display_name
        creator.avatar_url = rc.avatar_url or creator.avatar_url
        if rc.baseline_median_views:
            creator.baseline_median_views = rc.baseline_median_views
    return creator


def refresh_creator_baseline(db: Session, creator: Creator) -> None:
    """Recompute the creator's typical view count from their collected videos.

    Only run when the platform did not supply one. Uses the median so a single
    outlier — which is precisely what we are trying to detect — cannot inflate the
    denominator and hide itself.
    """
    views = db.scalars(
        select(Video.views)
        .where(Video.creator_id == creator.id)
        .order_by(Video.published_at.desc())
        .limit(30)
    ).all()
    if len(views) >= 3:
        creator.baseline_median_views = int(statistics.median(views))


def ingest_platform(
    db: Session,
    platform: str,
    *,
    niche: str | None = None,
    since: datetime | None = None,
    limit: int = 100,
    region: str | None = None,
    language: str | None = None,
    min_views: int | None = None,
) -> dict:
    """Collect from one platform and persist normalised rows.

    ``region`` and ``language`` are forwarded when the connector supports them;
    connectors that do not accept them are called without, so adding a new
    platform never has to implement the full option surface.
    """
    connector = get_connector(platform)
    options = {"niche": niche, "since": since, "limit": limit, "region": region}
    if language:
        options["language"] = language
    if min_views is not None:
        options["min_views"] = min_views
    try:
        try:
            raw_videos = connector.fetch_recent(**options)
        except TypeError:
            # Older/simpler connectors accept only the core four arguments.
            for optional in ("min_views", "language"):
                options.pop(optional, None)
            raw_videos = connector.fetch_recent(**options)
    except NotConfigured as exc:
        logger.info("Skipping %s: %s", platform, exc)
        return {"platform": platform, "skipped": str(exc), "ingested": 0, "updated": 0}

    ingested = updated = 0
    touched_creators: set[str] = set()

    for raw in raw_videos:
        creator = _upsert_creator(db, raw)
        touched_creators.add(creator.id)

        video = db.scalar(
            select(Video).where(
                Video.platform == raw.platform, Video.external_id == raw.external_id
            )
        )
        if video is None:
            video = Video(
                platform=raw.platform,
                external_id=raw.external_id,
                creator_id=creator.id,
                url=raw.url,
                thumbnail_url=raw.thumbnail_url,
                caption=raw.caption,
                hashtags=raw.hashtags,
                published_at=raw.published_at,
                duration_sec=raw.duration_sec,
                country=raw.country,
                language=raw.language,
                niche=raw.niche,
                content_type=raw.content_type,
                sound_name=raw.sound_name,
            )
            db.add(video)
            db.flush()
            ingested += 1
        else:
            updated += 1

        video.views, video.likes = raw.views, raw.likes
        video.comments, video.shares, video.saves = raw.comments, raw.shares, raw.saves
        video.collected_at = utcnow()

        # Every collection writes a metric row; velocity is the delta between them.
        db.add(
            VideoMetric(
                video_id=video.id,
                captured_at=utcnow(),
                views=raw.views,
                likes=raw.likes,
                comments=raw.comments,
                shares=raw.shares,
            )
        )
        for captured_at, views in raw.view_history:
            db.add(VideoMetric(video_id=video.id, captured_at=captured_at, views=views))

    for creator_id in touched_creators:
        creator = db.get(Creator, creator_id)
        if creator and not creator.baseline_median_views:
            refresh_creator_baseline(db, creator)

    db.commit()
    return {"platform": platform, "ingested": ingested, "updated": updated}


# ---------------------------------------------------------------------------
# Stage 3–5: AI analysis and embeddings
# ---------------------------------------------------------------------------


def analyze_pending(
    db: Session,
    limit: int = 50,
    *,
    allow_video: bool = True,
    allow_llm: bool = True,
    concurrency: int | None = None,
) -> dict:
    """Analyse videos that have no analysis yet, then embed them."""
    pending = db.scalars(
        select(Video)
        .outerjoin(VideoAnalysis, VideoAnalysis.video_id == Video.id)
        .where(VideoAnalysis.id.is_(None))
        .order_by(Video.published_at.desc())
        .limit(limit)
    ).all()

    if not pending:
        return {"analyzed": 0}

    def payload_for(video: Video) -> dict:
        return {
            "platform": video.platform,
            "external_id": video.external_id,
            "url": video.url,
            "caption": video.caption,
            "hashtags": video.hashtags,
            "duration_sec": video.duration_sec,
            "niche": video.niche,
            "sound_name": video.sound_name,
        }

    # Native video analysis is ~30s per video, almost all of it waiting on the
    # model. Running them serially makes this stage the whole pipeline's
    # bottleneck, so fan out — but keep it bounded, since the ceiling here is the
    # provider's rate limit rather than local CPU.
    workers = max(1, min(concurrency or settings.analysis_concurrency, len(pending)))
    records: list[tuple[Video, dict]] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(
                extraction.analyze_video,
                payload_for(v),
                allow_video=allow_video,
                allow_llm=allow_llm,
            ): v
            for v in pending
        }
        for future in as_completed(futures):
            video = futures[future]
            try:
                records.append((video, future.result()))
            except Exception as exc:
                # One bad video must not abort the batch; it stays unanalysed and
                # is picked up by the next run.
                logger.warning("Analysis failed for %s: %s", video.url, exc)

    if not records:
        return {"analyzed": 0}

    # Batch the embedding call — one request for the whole page of videos.
    signatures = [embeddings.format_signature(analysis) for _, analysis in records]
    vectors = embeddings.embed_many(signatures)

    for (video, analysis), vector in zip(records, vectors):
        db.add(
            VideoAnalysis(
                video_id=video.id,
                hook=analysis.get("hook"),
                topic=analysis.get("topic"),
                content_format=analysis.get("content_format"),
                narrative_structure=analysis.get("narrative_structure") or [],
                speaking_style=analysis.get("speaking_style"),
                visual_style=analysis.get("visual_style"),
                editing_patterns=analysis.get("editing_patterns") or [],
                caption_style=analysis.get("caption_style"),
                call_to_action=analysis.get("call_to_action"),
                emotional_tone=analysis.get("emotional_tone"),
                audio_style=analysis.get("audio_style"),
                target_audience=analysis.get("target_audience"),
                main_message=analysis.get("main_message"),
                opening_frames=analysis.get("opening_frames"),
                key_moments=analysis.get("key_moments") or [],
                production_difficulty=analysis.get("production_difficulty"),
                extraction_model=analysis.get("extraction_model"),
                is_fallback=bool(analysis.get("is_fallback")),
                embedding=vector,
            )
        )

    db.commit()
    return {"analyzed": len(records)}


# ---------------------------------------------------------------------------
# Stage 6–8: clustering, scoring, narrative
# ---------------------------------------------------------------------------


def _build_signal(video: Video, creator: Creator, history: list[VideoMetric]) -> scoring.VideoSignal:
    return scoring.VideoSignal(
        video_id=video.id,
        platform=video.platform,
        published_at=video.published_at,
        views=video.views,
        likes=video.likes,
        comments=video.comments,
        shares=video.shares,
        saves=video.saves,
        duration_sec=video.duration_sec,
        creator_id=creator.id,
        creator_baseline_views=creator.baseline_median_views,
        creator_followers=creator.followers,
        niche=video.niche or creator.niche,
        country=video.country or creator.country,
        language=video.language or creator.language,
        content_type=video.content_type,
        view_history=[(m.captured_at, m.views) for m in history],
    )


def rebuild_trends(db: Session, *, lookback_days: int = 30, narrate: bool = True) -> dict:
    """Re-cluster the corpus and rewrite the trend table.

    Full rebuild rather than incremental: cluster boundaries genuinely move as
    new videos arrive, and a nightly rebuild over a 30-day window is cheap enough
    that keeping stale boundaries is not worth the complexity.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)

    rows = db.execute(
        select(Video, VideoAnalysis, Creator)
        .join(VideoAnalysis, VideoAnalysis.video_id == Video.id)
        .join(Creator, Creator.id == Video.creator_id)
        .where(Video.published_at >= cutoff)
    ).all()

    if not rows:
        return {"trends": 0, "videos": 0, "reason": "no analysed videos in window"}

    metrics_by_video: dict[str, list[VideoMetric]] = {}
    for metric in db.scalars(
        select(VideoMetric).where(VideoMetric.video_id.in_([r[0].id for r in rows]))
    ).all():
        metrics_by_video.setdefault(metric.video_id, []).append(metric)
    for history in metrics_by_video.values():
        history.sort(key=lambda m: m.captured_at)

    ids = [r[0].id for r in rows]
    vectors = [list(r[1].embedding or []) for r in rows]
    if any(not v for v in vectors):
        return {"trends": 0, "videos": len(ids), "reason": "some analyses are missing embeddings"}

    clusters = clustering.cluster_embeddings(ids, vectors)
    if not clusters:
        return {"trends": 0, "videos": len(ids), "reason": "no cluster met the minimum size"}

    by_id = {r[0].id: r for r in rows}

    # Preserve identity across rebuilds so saved trends and their URLs survive.
    existing = {t.slug: t for t in db.scalars(select(Trend)).all()}
    kept_slugs: set[str] = set()
    now = utcnow()

    for cluster in clusters:
        members = [by_id[vid] for vid in cluster.members]
        signals = [
            _build_signal(video, creator, metrics_by_video.get(video.id, []))
            for video, _, creator in members
        ]
        agg = scoring.build_aggregates(signals, now)

        difficulty = scoring.infer_production_difficulty(
            [a.production_difficulty for _, a, _ in members if a.production_difficulty],
            agg.median_duration_sec,
        )
        scored = scoring.score_trend(agg, difficulty)

        analyses = [
            {
                "hook": a.hook,
                "topic": a.topic,
                "content_format": a.content_format,
                "narrative_structure": a.narrative_structure,
                "visual_style": a.visual_style,
                "editing_patterns": a.editing_patterns,
                "emotional_tone": a.emotional_tone,
                "main_message": a.main_message,
                "duration_sec": v.duration_sec,
            }
            for v, a, _ in members
        ]
        stats = {
            **scored["score_breakdown"]["inputs"],
            "median_duration_sec": agg.median_duration_sec,
            "niches": agg.niches,
            "platforms": agg.platforms,
            "production_difficulty": difficulty,
        }
        story = (
            narrative.describe_cluster(analyses, stats)
            if narrate
            else narrative._fallback_narrative(analyses, stats)
        )

        slug = narrative.build_slug(story["name"], kept_slugs)
        kept_slugs.add(slug)
        trend = existing.get(slug) or Trend(slug=slug)
        if trend.id is None or slug not in existing:
            db.add(trend)

        trend.name = story["name"]
        trend.summary = story.get("summary", "")
        trend.format_pattern = story.get("format_pattern")
        trend.why_it_works = story.get("why_it_works", [])
        trend.format_structure = story.get("format_structure", [])
        trend.common_elements = story.get("common_elements", [])

        trend.status = scored["status"]
        trend.competition_level = scored["competition_level"]
        trend.trend_score = scored["trend_score"]
        trend.opportunity_score = scored["opportunity_score"]
        trend.score_breakdown = scored["score_breakdown"]
        trend.adaptability = scored["adaptability"]
        trend.production_difficulty = difficulty

        trend.video_count = agg.video_count
        trend.creator_count = agg.creator_count
        trend.avg_views = agg.avg_views
        trend.median_views = agg.median_views
        trend.avg_engagement_rate = agg.avg_engagement_rate
        trend.growth_24h = agg.growth_24h
        trend.growth_7d = agg.growth_7d
        trend.creator_normalized_lift = agg.median_creator_lift
        trend.median_duration_sec = agg.median_duration_sec

        trend.platforms = agg.platforms
        trend.niches = agg.niches
        trend.countries = agg.countries
        trend.languages = agg.languages
        trend.content_types = agg.content_types

        trend.centroid = cluster.centroid
        trend.first_seen_at = trend.first_seen_at or min(s.published_at for s in signals)
        trend.last_computed_at = now
        db.flush()

        db.query(TrendVideo).filter(TrendVideo.trend_id == trend.id).delete()
        for rank, (video_id, similarity) in enumerate(
            zip(cluster.members, cluster.similarities)
        ):
            signal = next(s for s in signals if s.video_id == video_id)
            db.add(
                TrendVideo(
                    trend_id=trend.id,
                    video_id=video_id,
                    similarity=similarity,
                    is_exemplar=rank < 4,
                    creator_lift=round(signal.creator_lift, 3),
                )
            )

        db.add(
            TrendSnapshot(
                trend_id=trend.id,
                captured_at=now,
                video_count=agg.video_count,
                creator_count=agg.creator_count,
                total_views=sum(s.views for s in signals),
                avg_engagement_rate=agg.avg_engagement_rate,
                trend_score=scored["trend_score"],
            )
        )

    # Trends whose cluster disappeared this run are stale, not merely inactive.
    for slug, trend in existing.items():
        if slug not in kept_slugs:
            db.delete(trend)

    db.commit()
    return {"trends": len(clusters), "videos": len(ids)}


def backfill_snapshots(db: Session, trend: Trend, days: int = 14) -> None:
    """Reconstruct a trend's history from its members' publish dates.

    Used after a cold start so the sparklines are not empty on day one. Real
    snapshots from :func:`rebuild_trends` take over from the next run.
    """
    member_ids = [m.video_id for m in trend.members]
    if not member_ids:
        return
    videos = db.scalars(select(Video).where(Video.id.in_(member_ids))).all()
    now = datetime.now(timezone.utc)

    for offset in range(days, 0, -1):
        as_of = now - timedelta(days=offset)
        published = [v for v in videos if v.published_at <= as_of]
        if not published:
            continue
        db.add(
            TrendSnapshot(
                trend_id=trend.id,
                captured_at=as_of,
                video_count=len(published),
                creator_count=len({v.creator_id for v in published}),
                # Views accrue over time, so discount older observations rather
                # than pretending each video had its final count on day one.
                total_views=int(sum(v.views for v in published) * (1 - offset / (days * 1.6))),
                avg_engagement_rate=statistics.mean([v.engagement_rate for v in published]),
                trend_score=0.0,
            )
        )


def run_full_pipeline(
    db: Session,
    *,
    platforms: list[str] | None = None,
    niches: list[str] | None = None,
    analyze_limit: int = 100,
) -> dict:
    platforms = platforms or ["youtube", "tiktok", "instagram"]
    niches = niches or [None]

    collection = []
    for platform in platforms:
        for niche in niches:
            collection.append(ingest_platform(db, platform, niche=niche))

    analysis = analyze_pending(db, limit=analyze_limit)
    trends = rebuild_trends(db)

    total_videos = db.scalar(select(func.count()).select_from(Video)) or 0
    return {
        "collection": collection,
        "analysis": analysis,
        "trends": trends,
        "corpus_size": total_videos,
    }
