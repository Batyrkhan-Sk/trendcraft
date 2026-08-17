from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Platform = Literal["instagram", "tiktok", "youtube"]
TrendStatus = Literal["emerging", "growing", "viral", "declining"]
Level = Literal["low", "medium", "high"]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- content -----------------------------------------------------------------


class CreatorOut(ORMModel):
    id: str
    platform: str
    handle: str
    display_name: str | None = None
    avatar_url: str | None = None
    followers: int = 0
    baseline_median_views: int = 0


class VideoAnalysisOut(ORMModel):
    hook: str | None = None
    topic: str | None = None
    content_format: str | None = None
    narrative_structure: list[str] = []
    speaking_style: str | None = None
    visual_style: str | None = None
    editing_patterns: list[str] = []
    caption_style: str | None = None
    call_to_action: str | None = None
    emotional_tone: str | None = None
    audio_style: str | None = None
    target_audience: str | None = None
    main_message: str | None = None
    opening_frames: str | None = None
    key_moments: list[dict[str, Any]] = []
    production_difficulty: str | None = None
    extraction_model: str | None = None
    is_fallback: bool = False


class VideoOut(ORMModel):
    id: str
    platform: str
    external_id: str
    url: str
    thumbnail_url: str | None = None
    caption: str | None = None
    hashtags: list[str] = []
    published_at: datetime
    duration_sec: float
    views: int
    likes: int
    comments: int
    shares: int
    saves: int
    engagement_rate: float = 0.0
    niche: str | None = None
    language: str | None = None
    country: str | None = None
    sound_name: str | None = None
    creator: CreatorOut | None = None
    analysis: VideoAnalysisOut | None = None
    #: Populated when the video is returned in the context of a trend.
    similarity: float | None = None
    creator_lift: float | None = None


# --- trends ------------------------------------------------------------------


class TrendSnapshotOut(ORMModel):
    captured_at: datetime
    video_count: int
    creator_count: int
    total_views: int
    avg_engagement_rate: float
    trend_score: float


class TrendSummary(ORMModel):
    id: str
    slug: str
    name: str
    summary: str = ""
    format_pattern: str | None = None
    status: TrendStatus
    competition_level: Level
    trend_score: float
    opportunity_score: float
    video_count: int
    creator_count: int
    avg_views: int
    median_views: int
    avg_engagement_rate: float
    growth_24h: float
    growth_7d: float
    creator_normalized_lift: float
    median_duration_sec: float
    platforms: list[str] = []
    niches: list[str] = []
    countries: list[str] = []
    languages: list[str] = []
    content_types: list[str] = []
    production_difficulty: Level
    adaptability: Level
    first_seen_at: datetime | None = None
    last_computed_at: datetime | None = None
    #: Short adoption history for the card sparkline.
    sparkline: list[float] = []
    exemplars: list[VideoOut] = []
    # Feed-only fields
    relevance_score: float | None = None
    relevance_reasons: list[str] | None = None
    feed_score: float | None = None


class TrendDetail(TrendSummary):
    why_it_works: list[dict[str, Any]] = []
    format_structure: list[dict[str, Any]] = []
    common_elements: list[str] = []
    score_breakdown: dict[str, Any] = {}
    opportunity_explanation: list[str] = []
    snapshots: list[TrendSnapshotOut] = []
    videos: list[VideoOut] = []


class TrendListOut(BaseModel):
    items: list[TrendSummary]
    total: int
    facets: dict[str, list[str]] = {}


# --- profile -----------------------------------------------------------------


class ProfileIn(BaseModel):
    niche: str | None = None
    sub_niches: list[str] = []
    audience: str | None = None
    audience_age: str | None = None
    platforms: list[str] = []
    content_types: list[str] = []
    goal: str | None = None
    languages: list[str] = ["en"]
    country: str | None = None
    preferred_style: str | None = None
    production_capacity: Level | None = "medium"
    notes: str | None = None


class ProfileOut(ProfileIn, ORMModel):
    id: str | None = None
    user_id: str | None = None


class UserOut(ORMModel):
    id: str
    email: str
    name: str | None = None
    profile: ProfileOut | None = None


# --- generation --------------------------------------------------------------


class ScenarioRequest(BaseModel):
    trend_id: str | None = Field(
        default=None, description="Omit to let the engine pick the best-fitting trends."
    )
    niche: str | None = None
    audience: str | None = None
    audience_age: str | None = None
    platform: str | None = None
    goal: str | None = None
    preferred_style: str | None = None
    topic: str | None = None
    languages: list[str] = ["en"]
    production_capacity: Level | None = "medium"
    count: int = Field(default=3, ge=1, le=6)
    include_recording_guide: bool = True


class ScriptBeat(BaseModel):
    start: float
    end: float
    label: str
    script: str = ""
    direction: str = ""


class ShotOut(BaseModel):
    index: int
    label: str
    start: float
    end: float
    shot_type: str
    camera: str
    action: str
    spoken: str | None = None
    on_screen_text: str | None = None
    lighting: str | None = None
    editing: str
    storyboard_frame: str


class StoryboardFrame(BaseModel):
    frame: int
    timecode: str
    start: float
    end: float
    label: str
    shot_type: str = ""
    description: str = ""
    on_screen_text: str = ""


class RecordingGuideOut(BaseModel):
    shots: list[ShotOut] = []
    camera_setup: dict[str, Any] = {}
    editing_blueprint: dict[str, Any] = {}
    gear: list[str] = []
    common_mistakes: list[str] = []
    estimated_shoot_minutes: int | None = None
    estimated_edit_minutes: int | None = None
    storyboard: list[StoryboardFrame] = []
    generator_model: str | None = None


class ScenarioOut(ORMModel):
    id: str | None = None
    trend_id: str | None = None
    trend_name: str | None = None
    title: str
    hook: str
    concept: str
    script_structure: list[ScriptBeat] = []
    caption: str | None = None
    hashtags: list[str] = []
    call_to_action: str = ""
    suggested_duration_sec: float = 30
    suggested_audio: str | None = None
    difficulty: Level = "medium"
    why_it_could_work: list[str] = []
    derived_from: str | None = None
    recording_guide: RecordingGuideOut | None = None
    platform: str | None = None
    niche: str | None = None
    goal: str | None = None
    kind: str = "scenario"
    generator_model: str | None = None
    created_at: datetime | None = None


class ScenarioListOut(BaseModel):
    items: list[ScenarioOut]
    total: int


# --- saved / analytics -------------------------------------------------------


class SaveIn(BaseModel):
    entity_type: Literal["trend", "scenario", "video"]
    entity_id: str
    note: str | None = None


class SavedOut(ORMModel):
    id: int
    entity_type: str
    entity_id: str
    note: str | None = None
    created_at: datetime
    trend: TrendSummary | None = None
    scenario: ScenarioOut | None = None


class DashboardOut(BaseModel):
    rising_fast: list[TrendSummary] = []
    best_opportunities: list[TrendSummary] = []
    in_your_niche: list[TrendSummary] = []
    cross_platform: list[TrendSummary] = []
    recommended_scenarios: list[ScenarioOut] = []
    recently_saved: list[SavedOut] = []
    stats: dict[str, Any] = {}


class AnalyticsOut(BaseModel):
    totals: dict[str, Any]
    by_platform: list[dict[str, Any]]
    by_status: list[dict[str, Any]]
    by_niche: list[dict[str, Any]]
    top_movers: list[TrendSummary]
    score_distribution: list[dict[str, Any]]
    adoption_timeline: list[dict[str, Any]]


class PipelineRunIn(BaseModel):
    platforms: list[str] | None = None
    niches: list[str] | None = None
    analyze_limit: int = 100
    async_run: bool = True
