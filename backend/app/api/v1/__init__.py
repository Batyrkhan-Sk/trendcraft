from fastapi import APIRouter

from app.api.v1 import (
    analytics,
    feed,
    pipeline,
    profile,
    saved,
    scenarios,
    trends,
    videos,
)

api_router = APIRouter()
api_router.include_router(trends.router)
api_router.include_router(videos.router)
api_router.include_router(scenarios.router)
api_router.include_router(feed.router)
api_router.include_router(profile.router)
api_router.include_router(saved.router)
api_router.include_router(analytics.router)
api_router.include_router(pipeline.router)

__all__ = ["api_router"]
