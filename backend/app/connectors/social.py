"""TikTok and Instagram connectors.

Neither platform offers a public discovery API: TikTok's Research API is limited
to approved academic institutions, and the Instagram Graph API only reaches
accounts you own. Broad discovery therefore has to go through a third-party
dataset provider (Apify, Bright Data, Ensemble and similar all expose a
compatible request shape).

Rather than hard-coding one vendor, both connectors talk to a configurable HTTP
endpoint and normalise a small, documented response envelope. Point
``TIKTOK_PROVIDER_URL`` / ``INSTAGRAM_PROVIDER_URL`` at your provider and map its
fields in :func:`_normalise` if they differ.

Expected envelope::

    {"items": [{"id", "url", "caption", "created_at", "duration",
                "views", "likes", "comments", "shares", "saves",
                "thumbnail", "sound", "hashtags": [...],
                "author": {"handle", "name", "avatar", "followers",
                           "median_views", "country", "language"}}]}
"""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timedelta, timezone

import httpx

from app.connectors.base import NotConfigured, PlatformConnector, RawCreator, RawVideo

logger = logging.getLogger(__name__)


def _parse_time(value) -> datetime:
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            pass
    return datetime.now(timezone.utc)


class ProviderBackedConnector(PlatformConnector):
    """Shared implementation for platforms reached through a dataset vendor."""

    env_url: str
    env_token: str

    def __init__(self) -> None:
        self.endpoint = os.getenv(self.env_url)
        self.token = os.getenv(self.env_token)

    def check(self) -> None:
        if not self.endpoint:
            raise NotConfigured(
                f"{self.env_url} is not set — {self.platform} discovery needs a data provider"
            )

    def fetch_recent(
        self,
        *,
        niche: str | None = None,
        since: datetime | None = None,
        limit: int = 100,
        region: str | None = None,
    ) -> list[RawVideo]:
        self.check()
        since = since or datetime.now(timezone.utc) - timedelta(days=7)

        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        with httpx.Client(timeout=60.0) as http:
            resp = http.post(
                self.endpoint,
                headers=headers,
                json={
                    "platform": self.platform,
                    "query": niche or "",
                    "since": since.isoformat(),
                    "limit": limit,
                    "region": region,
                },
            )
            resp.raise_for_status()
            payload = resp.json()

        items = payload.get("items", payload if isinstance(payload, list) else [])
        return [self._normalise(item, niche, region) for item in items]

    def _normalise(self, item: dict, niche: str | None, region: str | None) -> RawVideo:
        author = item.get("author") or {}
        caption = item.get("caption") or ""
        return RawVideo(
            platform=self.platform,
            external_id=str(item.get("id")),
            url=item.get("url") or "",
            creator=RawCreator(
                platform=self.platform,
                handle=author.get("handle") or "unknown",
                display_name=author.get("name"),
                avatar_url=author.get("avatar"),
                followers=int(author.get("followers") or 0),
                baseline_median_views=int(author.get("median_views") or 0),
                niche=niche,
                country=author.get("country") or region,
                language=author.get("language"),
            ),
            published_at=_parse_time(item.get("created_at")),
            duration_sec=float(item.get("duration") or 0),
            caption=caption,
            hashtags=item.get("hashtags") or re.findall(r"#(\w+)", caption),
            thumbnail_url=item.get("thumbnail"),
            views=int(item.get("views") or 0),
            likes=int(item.get("likes") or 0),
            comments=int(item.get("comments") or 0),
            shares=int(item.get("shares") or 0),
            saves=int(item.get("saves") or 0),
            country=author.get("country") or region,
            language=author.get("language") or "en",
            niche=niche,
            sound_name=item.get("sound"),
        )


class TikTokConnector(ProviderBackedConnector):
    platform = "tiktok"
    env_url = "TIKTOK_PROVIDER_URL"
    env_token = "TIKTOK_PROVIDER_TOKEN"


class InstagramConnector(ProviderBackedConnector):
    platform = "instagram"
    env_url = "INSTAGRAM_PROVIDER_URL"
    env_token = "INSTAGRAM_PROVIDER_TOKEN"

# Registration is decided in app/connectors/__init__.py, which picks between
# these and the Apify-backed connectors based on which credentials exist.
