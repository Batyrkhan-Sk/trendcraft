"""Raw social content: creators, videos, metric snapshots and AI analyses.

Everything here is platform-agnostic on purpose — a connector normalises whatever
a platform returns into this shape, so adding a new platform never touches the
trend engine downstream.
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
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.db.base import Base, TimestampMixin, new_id

PLATFORMS = ("instagram", "tiktok", "youtube")


class Creator(Base, TimestampMixin):
    __tablename__ = "creators"
    __table_args__ = (UniqueConstraint("platform", "handle", name="uq_creator_platform_handle"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    platform: Mapped[str] = mapped_column(String(24), nullable=False)
    handle: Mapped[str] = mapped_column(String(120), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(200))
    avatar_url: Mapped[str | None] = mapped_column(Text)
    followers: Mapped[int] = mapped_column(BigInteger, default=0)

    #: Rolling median view count of the creator's recent posts. This is the
    #: denominator for creator-normalised performance — it is what stops the
    #: engine from mistaking "large account" for "trending format".
    baseline_median_views: Mapped[int] = mapped_column(BigInteger, default=0)

    niche: Mapped[str | None] = mapped_column(String(64))
    country: Mapped[str | None] = mapped_column(String(8))
    language: Mapped[str | None] = mapped_column(String(8))

    videos: Mapped[list["Video"]] = relationship(back_populates="creator")


class Video(Base, TimestampMixin):
    __tablename__ = "videos"
    __table_args__ = (
        UniqueConstraint("platform", "external_id", name="uq_video_platform_external"),
        Index("ix_videos_published_at", "published_at"),
        Index("ix_videos_platform_niche", "platform", "niche"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    platform: Mapped[str] = mapped_column(String(24), nullable=False)
    external_id: Mapped[str] = mapped_column(String(120), nullable=False)
    creator_id: Mapped[str] = mapped_column(ForeignKey("creators.id", ondelete="CASCADE"))

    url: Mapped[str] = mapped_column(Text, nullable=False)
    thumbnail_url: Mapped[str | None] = mapped_column(Text)
    caption: Mapped[str | None] = mapped_column(Text)
    hashtags: Mapped[list] = mapped_column(JSON, default=list)

    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_sec: Mapped[float] = mapped_column(Float, default=0.0)

    views: Mapped[int] = mapped_column(BigInteger, default=0)
    likes: Mapped[int] = mapped_column(BigInteger, default=0)
    comments: Mapped[int] = mapped_column(BigInteger, default=0)
    shares: Mapped[int] = mapped_column(BigInteger, default=0)
    saves: Mapped[int] = mapped_column(BigInteger, default=0)

    country: Mapped[str | None] = mapped_column(String(8))
    language: Mapped[str | None] = mapped_column(String(8))
    niche: Mapped[str | None] = mapped_column(String(64))
    content_type: Mapped[str | None] = mapped_column(String(48))

    sound_name: Mapped[str | None] = mapped_column(String(200))
    collected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    creator: Mapped[Creator] = relationship(back_populates="videos")
    analysis: Mapped["VideoAnalysis | None"] = relationship(
        back_populates="video", uselist=False, cascade="all, delete-orphan"
    )
    metrics: Mapped[list["VideoMetric"]] = relationship(
        back_populates="video", cascade="all, delete-orphan", order_by="VideoMetric.captured_at"
    )

    @property
    def engagement_rate(self) -> float:
        if not self.views:
            return 0.0
        return (self.likes + self.comments + self.shares + self.saves) / self.views


class VideoMetric(Base):
    """Point-in-time metric snapshot. Velocity and growth are derived from these."""

    __tablename__ = "video_metrics"
    __table_args__ = (Index("ix_video_metrics_video_time", "video_id", "captured_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    video_id: Mapped[str] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"))
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    views: Mapped[int] = mapped_column(BigInteger, default=0)
    likes: Mapped[int] = mapped_column(BigInteger, default=0)
    comments: Mapped[int] = mapped_column(BigInteger, default=0)
    shares: Mapped[int] = mapped_column(BigInteger, default=0)

    video: Mapped[Video] = relationship(back_populates="metrics")


class VideoAnalysis(Base, TimestampMixin):
    """AI-extracted understanding of what a video actually *is*.

    Populated by the vision + transcript + LLM extraction stage. The embedding is
    built from the semantic fields (hook, format, structure, message) rather than
    the caption, so clustering groups *formats* instead of topics.
    """

    __tablename__ = "video_analyses"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    video_id: Mapped[str] = mapped_column(
        ForeignKey("videos.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    hook: Mapped[str | None] = mapped_column(Text)
    topic: Mapped[str | None] = mapped_column(Text)
    content_format: Mapped[str | None] = mapped_column(String(160))
    narrative_structure: Mapped[list] = mapped_column(JSON, default=list)
    speaking_style: Mapped[str | None] = mapped_column(String(120))
    visual_style: Mapped[str | None] = mapped_column(String(160))
    editing_patterns: Mapped[list] = mapped_column(JSON, default=list)
    caption_style: Mapped[str | None] = mapped_column(String(160))
    call_to_action: Mapped[str | None] = mapped_column(Text)
    emotional_tone: Mapped[str | None] = mapped_column(String(80))
    audio_style: Mapped[str | None] = mapped_column(String(160))
    target_audience: Mapped[str | None] = mapped_column(String(160))
    main_message: Mapped[str | None] = mapped_column(Text)

    #: Literal description of the opening 3–5 seconds — the single highest-signal
    #: segment for whether a format works.
    opening_frames: Mapped[str | None] = mapped_column(Text)
    #: [{"t": 0.0, "label": "...", "why": "..."}]
    key_moments: Mapped[list] = mapped_column(JSON, default=list)

    transcript: Mapped[str | None] = mapped_column(Text)
    production_difficulty: Mapped[str | None] = mapped_column(String(16))  # low | medium | high
    extraction_model: Mapped[str | None] = mapped_column(String(80))
    is_fallback: Mapped[bool] = mapped_column(Boolean, default=False)

    embedding: Mapped[list[float] | None] = mapped_column(Vector(settings.embedding_dim))

    video: Mapped[Video] = relationship(back_populates="analysis")
