"""Platform connector contract.

Adding a platform means writing one module that yields :class:`RawVideo` and
registering it. Nothing downstream — extraction, clustering, scoring — knows which
platform a video came from beyond the ``platform`` string, so the trend engine
never needs to change.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


class NotConfigured(RuntimeError):
    """Raised when a connector lacks the credentials it needs."""


@dataclass
class RawCreator:
    platform: str
    handle: str
    display_name: str | None = None
    avatar_url: str | None = None
    followers: int = 0
    #: Median views of the creator's recent posts. If a platform cannot supply it,
    #: the ingest stage estimates it from the creator's own collected videos.
    baseline_median_views: int = 0
    niche: str | None = None
    country: str | None = None
    language: str | None = None


@dataclass
class RawVideo:
    platform: str
    external_id: str
    url: str
    creator: RawCreator
    published_at: datetime
    duration_sec: float = 0.0
    caption: str | None = None
    hashtags: list[str] = field(default_factory=list)
    thumbnail_url: str | None = None
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    country: str | None = None
    language: str | None = None
    niche: str | None = None
    content_type: str | None = None
    sound_name: str | None = None
    #: Optional prior metric observations, oldest first, used for velocity.
    view_history: list[tuple[datetime, int]] = field(default_factory=list)
    #: Populated when the media had to be downloaded for multimodal analysis.
    local_path: str | None = None


class PlatformConnector(ABC):
    platform: str

    @abstractmethod
    def fetch_recent(
        self,
        *,
        niche: str | None = None,
        since: datetime | None = None,
        limit: int = 100,
        region: str | None = None,
    ) -> list[RawVideo]:
        """Return recently published short-form videos."""

    def healthy(self) -> bool:
        try:
            self.check()
            return True
        except NotConfigured:
            return False

    def check(self) -> None:
        """Raise :class:`NotConfigured` if credentials are missing."""
        return


_REGISTRY: dict[str, PlatformConnector] = {}


def register(connector: PlatformConnector) -> PlatformConnector:
    _REGISTRY[connector.platform] = connector
    return connector


def get_connector(platform: str) -> PlatformConnector:
    if platform not in _REGISTRY:
        raise KeyError(f"no connector registered for platform '{platform}'")
    return _REGISTRY[platform]


def all_connectors() -> dict[str, PlatformConnector]:
    return dict(_REGISTRY)
