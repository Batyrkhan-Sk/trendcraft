from sqlalchemy import JSON, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, new_id


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(160))

    profile: Mapped["UserProfile | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class UserProfile(Base, TimestampMixin):
    """Onboarding answers. Drives the personalised feed ranking."""

    __tablename__ = "user_profiles"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    niche: Mapped[str | None] = mapped_column(String(64))
    sub_niches: Mapped[list] = mapped_column(JSON, default=list)
    audience: Mapped[str | None] = mapped_column(String(160))
    audience_age: Mapped[str | None] = mapped_column(String(32))
    platforms: Mapped[list] = mapped_column(JSON, default=list)
    content_types: Mapped[list] = mapped_column(JSON, default=list)
    goal: Mapped[str | None] = mapped_column(String(64))
    languages: Mapped[list] = mapped_column(JSON, default=list)
    country: Mapped[str | None] = mapped_column(String(8))
    preferred_style: Mapped[str | None] = mapped_column(String(120))
    production_capacity: Mapped[str | None] = mapped_column(String(16))  # low | medium | high
    notes: Mapped[str | None] = mapped_column(Text)

    user: Mapped[User] = relationship(back_populates="profile")


class SavedItem(Base, TimestampMixin):
    __tablename__ = "saved_items"
    __table_args__ = (
        UniqueConstraint("user_id", "entity_type", "entity_id", name="uq_saved_entity"),
        Index("ix_saved_user", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    entity_type: Mapped[str] = mapped_column(String(24))  # trend | scenario | video
    entity_id: Mapped[str] = mapped_column(String(32))
    note: Mapped[str | None] = mapped_column(Text)
