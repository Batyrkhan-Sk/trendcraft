from __future__ import annotations

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User, UserProfile

DEMO_EMAIL = "demo@trendcraft.app"


def get_current_user(
    db: Session = Depends(get_db),
    x_user_email: str | None = Header(default=None, alias="X-User-Email"),
) -> User:
    """Resolve the acting user.

    Single-tenant by design for now: the header selects an account and one is
    created on first sight. Swap this function for real session/JWT verification
    and nothing else in the API has to change.
    """
    email = x_user_email or DEMO_EMAIL
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(email=email, name=email.split("@")[0])
        db.add(user)
        db.flush()
        db.add(UserProfile(user_id=user.id))
        db.commit()
        db.refresh(user)
    return user


def get_profile_dict(user: User) -> dict:
    p = user.profile
    if p is None:
        return {}
    return {
        "niche": p.niche,
        "sub_niches": p.sub_niches or [],
        "audience": p.audience,
        "audience_age": p.audience_age,
        "platforms": p.platforms or [],
        "content_types": p.content_types or [],
        "goal": p.goal,
        "languages": p.languages or ["en"],
        "country": p.country,
        "preferred_style": p.preferred_style,
        "production_capacity": p.production_capacity or "medium",
    }
