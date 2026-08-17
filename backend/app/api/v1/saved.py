from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.serializers import scenario_to_dict, trend_to_summary
from app.db.session import get_db
from app.models import SavedItem, Scenario, Trend, User
from app.schemas import SavedOut, SaveIn

router = APIRouter(prefix="/saved", tags=["saved"])


@router.get("", response_model=list[SavedOut])
def list_saved(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    entity_type: str | None = Query(None),
) -> list[SavedOut]:
    stmt = select(SavedItem).where(SavedItem.user_id == user.id)
    if entity_type:
        stmt = stmt.where(SavedItem.entity_type == entity_type)
    rows = db.scalars(stmt.order_by(SavedItem.created_at.desc())).all()

    out = []
    for row in rows:
        entry = {
            "id": row.id,
            "entity_type": row.entity_type,
            "entity_id": row.entity_id,
            "note": row.note,
            "created_at": row.created_at,
            "trend": None,
            "scenario": None,
        }
        if row.entity_type == "trend":
            trend = db.get(Trend, row.entity_id)
            if trend:
                entry["trend"] = trend_to_summary(db, trend)
        elif row.entity_type == "scenario":
            scenario = db.get(Scenario, row.entity_id)
            if scenario:
                entry["scenario"] = scenario_to_dict(scenario)
        out.append(entry)
    return out


@router.post("", response_model=SavedOut, status_code=201)
def save(
    payload: SaveIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SavedOut:
    existing = db.scalar(
        select(SavedItem).where(
            SavedItem.user_id == user.id,
            SavedItem.entity_type == payload.entity_type,
            SavedItem.entity_id == payload.entity_id,
        )
    )
    if existing:
        existing.note = payload.note or existing.note
        db.commit()
        db.refresh(existing)
        return SavedOut.model_validate(existing)

    item = SavedItem(
        user_id=user.id,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        note=payload.note,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return SavedOut.model_validate(item)


@router.delete("/{entity_type}/{entity_id}", status_code=204)
def unsave(
    entity_type: str,
    entity_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    item = db.scalar(
        select(SavedItem).where(
            SavedItem.user_id == user.id,
            SavedItem.entity_type == entity_type,
            SavedItem.entity_id == entity_id,
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Not saved")
    db.delete(item)
    db.commit()
