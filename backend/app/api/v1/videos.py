from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.serializers import video_to_dict
from app.db.session import get_db
from app.models import Video
from app.schemas import VideoOut

router = APIRouter(prefix="/videos", tags=["videos"])


@router.get("", response_model=list[VideoOut])
def list_videos(
    db: Session = Depends(get_db),
    platform: str | None = Query(None),
    niche: str | None = Query(None),
    limit: int = Query(40, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[VideoOut]:
    stmt = select(Video)
    if platform:
        stmt = stmt.where(Video.platform == platform)
    if niche:
        stmt = stmt.where(Video.niche == niche)
    rows = db.scalars(
        stmt.order_by(Video.published_at.desc()).limit(limit).offset(offset)
    ).all()
    return [VideoOut(**video_to_dict(v)) for v in rows]


@router.get("/stats")
def stats(db: Session = Depends(get_db)) -> dict:
    rows = db.execute(
        select(Video.platform, func.count(), func.sum(Video.views)).group_by(Video.platform)
    ).all()
    return {
        "by_platform": [
            {"platform": p, "videos": int(c), "views": int(v or 0)} for p, c, v in rows
        ]
    }


@router.get("/{video_id}", response_model=VideoOut)
def get_video(video_id: str, db: Session = Depends(get_db)) -> VideoOut:
    video = db.get(Video, video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    return VideoOut(**video_to_dict(video))
