"""YouTube Shorts connector — YouTube Data API v3.

This one is fully functional with nothing but an API key, which makes it the
reference implementation for the connector contract.

Caveat worth knowing: the API has no "is a Short" flag. The accepted approach is
to filter on duration (<= 180s since the 2024 limit change) after a search, which
is what ``fetch_recent`` does. Quota cost is 100 units per search call plus 1 per
videos.list, against a default 10,000/day budget — roughly 90 searches a day, so
the scheduler spaces niche sweeps rather than polling.
"""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timedelta, timezone

import httpx

from app.connectors.base import (
    NotConfigured,
    PlatformConnector,
    RawCreator,
    RawVideo,
    register,
)

logger = logging.getLogger(__name__)

API = "https://www.googleapis.com/youtube/v3"

#: YouTube's own Shorts ceiling since the 2024 change.
MAX_SHORT_SECONDS = 180

#: The window this product actually cares about. Below ~8s a clip has no
#: structure to extract — there is no hook/payoff arc to detect. Above ~90s the
#: content is long-form talking that happens to be posted vertically, and it
#: dilutes format clusters with one-off monologues. Callers can widen this, but
#: the default is what makes clusters coherent.
DEFAULT_MIN_SECONDS = 8
DEFAULT_MAX_SECONDS = 90

#: Reach floor. A format is evidenced by videos that actually travelled — a
#: 1,400-view clip tells us nothing about whether the structure works.
DEFAULT_MIN_VIEWS = 100_000

#: Escape hatch for genuinely emerging videos. A two-day-old video with 30k views
#: has not cleared the absolute floor but is accumulating at ~600 views/hour,
#: which is the signal the product exists to catch. Either test admits a video.
DEFAULT_MIN_VIEWS_PER_HOUR = 500.0

_DURATION_RE = re.compile(
    r"P(?:(?P<days>\d+)D)?T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?"
)


def parse_iso8601_duration(value: str) -> float:
    match = _DURATION_RE.fullmatch(value or "")
    if not match:
        return 0.0
    parts = {k: int(v) for k, v in match.groupdict(default="0").items()}
    return (
        parts["days"] * 86400 + parts["hours"] * 3600 + parts["minutes"] * 60 + parts["seconds"]
    )


class YouTubeConnector(PlatformConnector):
    platform = "youtube"

    def __init__(self) -> None:
        # Falls back to GOOGLE_API_KEY so one key can serve Gemini and YouTube.
        self.api_key = os.getenv("YOUTUBE_API_KEY") or os.getenv("GOOGLE_API_KEY")

    def check(self) -> None:
        if not self.api_key:
            raise NotConfigured("YOUTUBE_API_KEY (or GOOGLE_API_KEY) is required")

    def fetch_recent(
        self,
        *,
        niche: str | None = None,
        since: datetime | None = None,
        limit: int = 50,
        region: str | None = None,
        language: str | None = None,
        min_duration: float = DEFAULT_MIN_SECONDS,
        max_duration: float = DEFAULT_MAX_SECONDS,
        min_views: int = DEFAULT_MIN_VIEWS,
        min_views_per_hour: float = DEFAULT_MIN_VIEWS_PER_HOUR,
    ) -> list[RawVideo]:
        self.check()
        # 21 days, not 7: a one-week window gives videos no time to accumulate
        # views, and leaves the prior-week comparison empty so every growth rate
        # degenerates to the same "no baseline" value.
        since = since or datetime.now(timezone.utc) - timedelta(days=21)

        with httpx.Client(timeout=30.0) as http:
            search = http.get(
                f"{API}/search",
                params={
                    "key": self.api_key,
                    "part": "snippet",
                    "type": "video",
                    "videoDuration": "short",  # < 4 minutes; narrowed further below
                    "order": "viewCount",
                    "publishedAfter": since.astimezone(timezone.utc).isoformat().replace(
                        "+00:00", "Z"
                    ),
                    "maxResults": min(50, limit),
                    "q": niche or "shorts",
                    # Without these, "order=viewCount" ranks globally and the
                    # result set skews to whichever regions post the most volume
                    # — which produces a corpus with no shared format at all.
                    **({"regionCode": region} if region else {}),
                    **({"relevanceLanguage": language} if language else {}),
                },
            )
            search.raise_for_status()
            items = search.json().get("items", [])
            video_ids = [i["id"]["videoId"] for i in items if i.get("id", {}).get("videoId")]
            if not video_ids:
                return []

            detail = http.get(
                f"{API}/videos",
                params={
                    "key": self.api_key,
                    "part": "snippet,statistics,contentDetails",
                    "id": ",".join(video_ids),
                },
            )
            detail.raise_for_status()
            videos = detail.json().get("items", [])

            channel_ids = list({v["snippet"]["channelId"] for v in videos})
            channels = {}
            for start in range(0, len(channel_ids), 50):
                chunk = channel_ids[start : start + 50]
                resp = http.get(
                    f"{API}/channels",
                    params={
                        "key": self.api_key,
                        "part": "snippet,statistics",
                        "id": ",".join(chunk),
                    },
                )
                resp.raise_for_status()
                for c in resp.json().get("items", []):
                    channels[c["id"]] = c

        results: list[RawVideo] = []
        for v in videos:
            duration = parse_iso8601_duration(v["contentDetails"]["duration"])
            if not (min_duration <= duration <= min(max_duration, MAX_SHORT_SECONDS)):
                continue

            snippet = v["snippet"]
            stats = v.get("statistics", {})
            channel = channels.get(snippet["channelId"], {})
            channel_stats = channel.get("statistics", {})

            views = int(stats.get("viewCount", 0) or 0)
            published_at = datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00"))
            age_hours = max(
                1.0, (datetime.now(timezone.utc) - published_at).total_seconds() / 3600
            )
            # Admit a video if it has real reach OR is climbing fast for its age.
            # The second test is what keeps genuinely emerging content in scope
            # instead of only ever surfacing what already won.
            if views < min_views and (views / age_hours) < min_views_per_hour:
                continue

            results.append(
                RawVideo(
                    platform=self.platform,
                    external_id=v["id"],
                    url=f"https://www.youtube.com/shorts/{v['id']}",
                    creator=RawCreator(
                        platform=self.platform,
                        handle=(
                            channel.get("snippet", {}).get("customUrl")
                            or snippet["channelId"]
                        ).lstrip("@"),
                        display_name=snippet.get("channelTitle"),
                        avatar_url=channel.get("snippet", {})
                        .get("thumbnails", {})
                        .get("default", {})
                        .get("url"),
                        followers=int(channel_stats.get("subscriberCount", 0) or 0),
                        niche=niche,
                        country=channel.get("snippet", {}).get("country"),
                        language=snippet.get("defaultAudioLanguage"),
                    ),
                    published_at=published_at,
                    duration_sec=duration,
                    caption=f"{snippet.get('title', '')}\n{snippet.get('description', '')}".strip(),
                    hashtags=re.findall(r"#(\w+)", snippet.get("description", "")),
                    thumbnail_url=snippet.get("thumbnails", {}).get("high", {}).get("url"),
                    views=views,
                    likes=int(stats.get("likeCount", 0) or 0),
                    comments=int(stats.get("commentCount", 0) or 0),
                    # YouTube exposes neither shares nor saves.
                    shares=0,
                    saves=0,
                    country=region,
                    language=(
                        snippet.get("defaultAudioLanguage") or language or "en"
                    ).split("-")[0],
                    niche=niche,
                )
            )
        return results


register(YouTubeConnector())
