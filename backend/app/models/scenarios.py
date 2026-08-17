from sqlalchemy import JSON, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, new_id


class Scenario(Base, TimestampMixin):
    """A trending format adapted to one user's niche, with a full shooting plan."""

    __tablename__ = "scenarios"
    __table_args__ = (Index("ix_scenarios_user_created", "user_id", "created_at"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    trend_id: Mapped[str | None] = mapped_column(ForeignKey("trends.id", ondelete="SET NULL"))

    title: Mapped[str] = mapped_column(String(260), nullable=False)
    hook: Mapped[str] = mapped_column(Text, default="")
    concept: Mapped[str] = mapped_column(Text, default="")
    #: [{"start": 0, "end": 3, "label": "Hook", "script": "...", "direction": "..."}]
    script_structure: Mapped[list] = mapped_column(JSON, default=list)
    caption: Mapped[str | None] = mapped_column(Text)
    hashtags: Mapped[list] = mapped_column(JSON, default=list)
    call_to_action: Mapped[str] = mapped_column(Text, default="")
    suggested_duration_sec: Mapped[int] = mapped_column(Float, default=30)
    suggested_audio: Mapped[str | None] = mapped_column(Text)

    difficulty: Mapped[str] = mapped_column(String(16), default="medium")
    why_it_could_work: Mapped[list] = mapped_column(JSON, default=list)
    derived_from: Mapped[str | None] = mapped_column(Text)

    #: Full "How to Record This Video" payload — shots, camera, editing, storyboard.
    recording_guide: Mapped[dict] = mapped_column(JSON, default=dict)

    platform: Mapped[str | None] = mapped_column(String(24))
    niche: Mapped[str | None] = mapped_column(String(64))
    goal: Mapped[str | None] = mapped_column(String(64))
    generator_model: Mapped[str | None] = mapped_column(String(80))
    kind: Mapped[str] = mapped_column(String(24), default="scenario")  # scenario | recreation
