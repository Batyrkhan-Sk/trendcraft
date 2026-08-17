"""Trend clusters — the unit of intelligence the product sells.

A trend is a *content format* discovered by clustering video analyses, not a
hashtag and not a single viral video.
"""

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.db.base import Base, TimestampMixin, new_id

TREND_STATUSES = ("emerging", "growing", "viral", "declining")
COMPETITION_LEVELS = ("low", "medium", "high")


class Trend(Base, TimestampMixin):
    __tablename__ = "trends"
    __table_args__ = (
        Index("ix_trends_scores", "trend_score", "opportunity_score"),
        Index("ix_trends_status", "status"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    slug: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)

    name: Mapped[str] = mapped_column(String(220), nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="")
    #: Human-readable pattern label, e.g. "I replaced X with AI / tested X for 7 days"
    format_pattern: Mapped[str | None] = mapped_column(Text)

    #: [{"title": "...", "detail": "...", "principle": "curiosity_gap"}]
    why_it_works: Mapped[list] = mapped_column(JSON, default=list)
    #: [{"start": 0, "end": 3, "label": "Hook", "detail": "..."}]
    format_structure: Mapped[list] = mapped_column(JSON, default=list)
    #: Structural fingerprint shared by cluster members
    common_elements: Mapped[list] = mapped_column(JSON, default=list)

    status: Mapped[str] = mapped_column(String(16), default="emerging")
    competition_level: Mapped[str] = mapped_column(String(16), default="medium")

    trend_score: Mapped[float] = mapped_column(Float, default=0.0)
    opportunity_score: Mapped[float] = mapped_column(Float, default=0.0)
    #: Full breakdown of every signal that produced the two scores above, so the
    #: UI can explain the number instead of asserting it.
    score_breakdown: Mapped[dict] = mapped_column(JSON, default=dict)

    video_count: Mapped[int] = mapped_column(Integer, default=0)
    creator_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_views: Mapped[int] = mapped_column(BigInteger, default=0)
    median_views: Mapped[int] = mapped_column(BigInteger, default=0)
    avg_engagement_rate: Mapped[float] = mapped_column(Float, default=0.0)
    growth_24h: Mapped[float] = mapped_column(Float, default=0.0)
    growth_7d: Mapped[float] = mapped_column(Float, default=0.0)
    creator_normalized_lift: Mapped[float] = mapped_column(Float, default=1.0)
    median_duration_sec: Mapped[float] = mapped_column(Float, default=0.0)

    platforms: Mapped[list] = mapped_column(JSON, default=list)
    niches: Mapped[list] = mapped_column(JSON, default=list)
    countries: Mapped[list] = mapped_column(JSON, default=list)
    languages: Mapped[list] = mapped_column(JSON, default=list)
    content_types: Mapped[list] = mapped_column(JSON, default=list)

    production_difficulty: Mapped[str] = mapped_column(String(16), default="medium")
    adaptability: Mapped[str] = mapped_column(String(16), default="medium")

    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_computed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    centroid: Mapped[list[float] | None] = mapped_column(Vector(settings.embedding_dim))

    members: Mapped[list["TrendVideo"]] = relationship(
        back_populates="trend", cascade="all, delete-orphan"
    )
    snapshots: Mapped[list["TrendSnapshot"]] = relationship(
        back_populates="trend", cascade="all, delete-orphan", order_by="TrendSnapshot.captured_at"
    )


class TrendVideo(Base):
    __tablename__ = "trend_videos"
    __table_args__ = (Index("ix_trend_videos_trend", "trend_id", "similarity"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trend_id: Mapped[str] = mapped_column(ForeignKey("trends.id", ondelete="CASCADE"))
    video_id: Mapped[str] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"))
    similarity: Mapped[float] = mapped_column(Float, default=0.0)
    #: Representative example surfaced on the breakdown page.
    is_exemplar: Mapped[bool] = mapped_column(Boolean, default=False)
    #: Creator-normalised multiple for this specific video (views / creator baseline).
    creator_lift: Mapped[float] = mapped_column(Float, default=1.0)

    trend: Mapped[Trend] = relationship(back_populates="members")


class TrendSnapshot(Base):
    """Daily rollup powering the growth sparklines and velocity deltas."""

    __tablename__ = "trend_snapshots"
    __table_args__ = (Index("ix_trend_snapshots_trend_time", "trend_id", "captured_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trend_id: Mapped[str] = mapped_column(ForeignKey("trends.id", ondelete="CASCADE"))
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    video_count: Mapped[int] = mapped_column(Integer, default=0)
    creator_count: Mapped[int] = mapped_column(Integer, default=0)
    total_views: Mapped[int] = mapped_column(BigInteger, default=0)
    avg_engagement_rate: Mapped[float] = mapped_column(Float, default=0.0)
    trend_score: Mapped[float] = mapped_column(Float, default=0.0)

    trend: Mapped[Trend] = relationship(back_populates="snapshots")
