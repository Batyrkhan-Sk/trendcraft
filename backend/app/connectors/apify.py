"""Apify-backed TikTok and Instagram connectors.

Apify runs community "actors" (scrapers) and hands back a dataset. We use the
synchronous endpoint::

    POST /v2/acts/{actor}/run-sync-get-dataset-items?token=…

which starts a run, waits for it, and returns the dataset items in one call. That
keeps the connector stateless at the cost of a run-duration ceiling — Apify caps
synchronous runs at 300s, so ``limit`` should stay modest per call. For large
sweeps, run the actor asynchronously and poll instead.

Actor output schemas are **not** stable across actors or versions, which is why
normalisation lives in one clearly-marked method per platform rather than being
spread through the ingest path. If you switch actors, that method is the only
thing to rewrite.

Cost note: actor runs consume Apify platform credits (the free plan grants $5/mo).
A 50-result TikTok run is typically a few cents.
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.connectors.base import NotConfigured, PlatformConnector, RawCreator, RawVideo

logger = logging.getLogger(__name__)

APIFY_API = "https://api.apify.com/v2"

#: Apify addresses actors with a tilde in URLs ("user~actor-name").
DEFAULT_TIKTOK_ACTOR = "clockworks~tiktok-scraper"
# The general instagram-scraper searches hashtags, but Instagram no longer
# exposes usable data that way: measured on this account, hashtag results were
# ~95% still images, and likesCount came back as -1/0/1 because logged-out
# scrapes cannot see real engagement. The dedicated Reel scraper works off
# profiles and returns genuine play counts, likes and durations.
DEFAULT_INSTAGRAM_ACTOR = "apify~instagram-reel-scraper"


def _parse_time(value: Any) -> datetime:
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def _int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


class ApifyConnector(PlatformConnector):
    """Shared plumbing: auth, the sync run call, and post-filtering."""

    actor_env: str
    default_actor: str

    def __init__(self) -> None:
        self.token = os.getenv("APIFY_TOKEN")
        self.actor = os.getenv(self.actor_env) or self.default_actor

    def check(self) -> None:
        if not self.token:
            raise NotConfigured("APIFY_TOKEN is not set")

    def _run_actor(self, payload: dict, timeout: float = 300.0) -> list[dict]:
        self.check()
        url = f"{APIFY_API}/acts/{self.actor}/run-sync-get-dataset-items"
        with httpx.Client(timeout=timeout + 30) as http:
            resp = http.post(
                url,
                # Header auth, not ?token=. A token in the query string ends up in
                # exception messages, access logs and crash reports — this call
                # already leaked one into a traceback before the switch.
                headers={"Authorization": f"Bearer {self.token}"},
                params={"timeout": int(timeout)},
                json=payload,
            )

            if resp.status_code in (401, 403):
                raise NotConfigured(
                    f"Apify rejected the run for '{self.actor}' ({resp.status_code}): "
                    f"{self._error_detail(resp)}"
                )
            if resp.status_code == 402:
                raise NotConfigured("Apify credit exhausted — top up or wait for the monthly reset")
            if resp.status_code == 404:
                raise NotConfigured(f"Apify actor '{self.actor}' not found or not accessible")
            resp.raise_for_status()
            data = resp.json()
        return data if isinstance(data, list) else data.get("items", [])

    @staticmethod
    def _error_detail(resp: httpx.Response) -> str:
        """Apify puts the useful message in the body, not the status line."""
        try:
            return str(resp.json().get("error", {}).get("message", resp.text))[:200]
        except Exception:
            return resp.text[:200]

    def fetch_recent(
        self,
        *,
        niche: str | None = None,
        since: datetime | None = None,
        limit: int = 50,
        region: str | None = None,
        language: str | None = None,
        min_views: int = 100_000,
        min_views_per_hour: float = 500.0,
        min_duration: float = 8.0,
        max_duration: float = 90.0,
    ) -> list[RawVideo]:
        since = since or datetime.now(timezone.utc) - timedelta(days=21)
        items = self._run_actor(self._build_input(niche, limit, region))

        results: list[RawVideo] = []
        now = datetime.now(timezone.utc)
        for item in items:
            try:
                video = self._normalise(item, niche, region)
            except Exception as exc:
                logger.debug("Skipping unparseable %s item: %s", self.platform, exc)
                continue
            if video is None:
                continue

            # Same quality gates as the YouTube connector, applied here rather
            # than downstream so the corpus stays comparable across platforms.
            if not (min_duration <= video.duration_sec <= max_duration):
                continue
            if video.published_at < since:
                continue
            age_hours = max(1.0, (now - video.published_at).total_seconds() / 3600)
            if video.views < min_views and (video.views / age_hours) < min_views_per_hour:
                continue

            results.append(video)
        return results

    def _build_input(self, niche: str | None, limit: int, region: str | None) -> dict:
        raise NotImplementedError

    def _normalise(self, item: dict, niche: str | None, region: str | None) -> RawVideo | None:
        raise NotImplementedError


class ApifyTikTokConnector(ApifyConnector):
    """Defaults to the ``clockworks/tiktok-scraper`` actor."""

    platform = "tiktok"
    actor_env = "APIFY_TIKTOK_ACTOR"
    default_actor = DEFAULT_TIKTOK_ACTOR

    def _build_input(self, niche: str | None, limit: int, region: str | None) -> dict:
        payload: dict[str, Any] = {
            "resultsPerPage": min(limit, 100),
            # We only ever need metadata — downloading media would multiply both
            # the run time and the credit cost for no benefit.
            "shouldDownloadVideos": False,
            "shouldDownloadCovers": False,
            "shouldDownloadSubtitles": False,
            "shouldDownloadSlideshowImages": False,
            # Restrict search to the video tab. Unfiltered TikTok search returns
            # mostly photo slideshows — measured at 33 of 50 on a sample query —
            # and those have no duration, no structure, and nothing to analyse.
            "searchSection": "/video",
            # Filter by date at the actor rather than locally, so the result
            # budget is not spent on posts we are about to discard. Measured
            # median age of unfiltered search results was 53 days.
            "oldestPostDateUnified": (
                datetime.now(timezone.utc) - timedelta(days=21)
            ).strftime("%Y-%m-%d"),
        }
        if niche:
            payload["searchQueries"] = [niche]
        else:
            payload["hashtags"] = ["fyp"]
        if region:
            payload["proxyCountryCode"] = region
        return payload

    def _normalise(self, item: dict, niche: str | None, region: str | None) -> RawVideo | None:
        # Photo carousels carry no duration and no narrative structure, so they
        # are not this product's unit of analysis. Rejecting them explicitly is
        # clearer than letting the duration gate drop them for the wrong reason.
        if item.get("isSlideshow"):
            return None
        author = item.get("authorMeta") or {}
        meta = item.get("videoMeta") or {}
        handle = author.get("name") or author.get("uniqueId")
        external_id = str(item.get("id") or "")
        if not handle or not external_id:
            return None

        return RawVideo(
            platform=self.platform,
            external_id=external_id,
            url=item.get("webVideoUrl") or f"https://www.tiktok.com/@{handle}/video/{external_id}",
            creator=RawCreator(
                platform=self.platform,
                handle=handle,
                display_name=author.get("nickName"),
                avatar_url=author.get("avatar"),
                followers=_int(author.get("fans")),
                niche=niche,
                country=author.get("region") or region,
            ),
            published_at=_parse_time(item.get("createTimeISO") or item.get("createTime")),
            duration_sec=float(meta.get("duration") or 0),
            caption=item.get("text"),
            hashtags=[h.get("name") for h in (item.get("hashtags") or []) if h.get("name")],
            thumbnail_url=meta.get("coverUrl") or meta.get("originalCoverUrl"),
            views=_int(item.get("playCount")),
            likes=_int(item.get("diggCount")),
            comments=_int(item.get("commentCount")),
            shares=_int(item.get("shareCount")),
            # TikTok exposes saves as "collect", which YouTube has no analogue for.
            saves=_int(item.get("collectCount")),
            country=author.get("region") or region,
            # The actor detects the caption's language; far more reliable than
            # inferring it from the search query's locale.
            language=(item.get("textLanguage") or "").split("-")[0] or None,
            niche=niche,
            sound_name=(item.get("musicMeta") or {}).get("musicName"),
        )


class ApifyInstagramConnector(ApifyConnector):
    """Reels from a watched set of accounts, via ``apify/instagram-reel-scraper``.

    **Discovery on Instagram is account-based, not query-based.** TikTok and
    YouTube let us search a topic and surface creators we have never seen; here we
    must name the accounts up front. Coverage is therefore only as good as the
    seed list, and this connector cannot discover a format from an unknown
    creator the way the other two can. That is an Instagram limitation, not a
    design choice — hashtag discovery was tested first and returns unusable data.

    Override the seed list with ``INSTAGRAM_SEED_ACCOUNTS`` as JSON:
    ``{"fitness": ["user1", "user2"], "ai": ["user3"]}``
    """

    platform = "instagram"
    actor_env = "APIFY_INSTAGRAM_ACTOR"
    default_actor = DEFAULT_INSTAGRAM_ACTOR

    #: Starter watchlist per niche. Replace with accounts relevant to you — these
    #: are only a sensible default so the connector is not inert out of the box.
    SEED_ACCOUNTS: dict[str, list[str]] = {
        "ai": ["aiadvantage", "riley_brown_ai", "heyjackward"],
        "productivity": ["aliabdaal", "thomasjfrank", "easlo"],
        "business": ["garyvee", "thefutur", "codiesanchez"],
        "fitness": ["jeffnippard", "mrandmrsmuscle", "meowmeix"],
        "food": ["joshuaweissman", "thegoldenbalance", "cookingwithlynja"],
        "design": ["thefutur", "flux_academy", "dann.petty"],
    }

    def _accounts_for(self, niche: str | None) -> list[str]:
        override = os.getenv("INSTAGRAM_SEED_ACCOUNTS")
        table = self.SEED_ACCOUNTS
        if override:
            try:
                table = json.loads(override)
            except json.JSONDecodeError:
                logger.warning("INSTAGRAM_SEED_ACCOUNTS is not valid JSON; using defaults")

        if niche:
            key = niche.lower().strip()
            if key in table:
                return table[key]
            # Fall back to any niche whose name appears in the query.
            for name, accounts in table.items():
                if name in key or key in name:
                    return accounts
        # No niche match: sample across the whole watchlist.
        return [a for accounts in table.values() for a in accounts][:12]

    def _build_input(self, niche: str | None, limit: int, region: str | None) -> dict:
        accounts = self._accounts_for(niche)
        per_profile = max(3, min(limit // max(1, len(accounts)), 30))
        return {
            "username": accounts,
            "resultsLimit": per_profile,
            "onlyPostsNewerThan": (
                datetime.now(timezone.utc) - timedelta(days=21)
            ).strftime("%Y-%m-%d"),
            "skipPinnedPosts": True,
            # includeSharesCount and includeTranscript are billed as extras on
            # this actor. Shares would feed the conversation signal, but they are
            # left off by default so a run's cost stays predictable.
        }

    def _normalise(self, item: dict, niche: str | None, region: str | None) -> RawVideo | None:
        if item.get("type") != "Video":
            return None
        shortcode = item.get("shortCode")
        if not shortcode:
            return None

        caption = item.get("caption") or ""
        return RawVideo(
            platform=self.platform,
            external_id=str(shortcode),
            url=item.get("url") or f"https://www.instagram.com/reel/{shortcode}/",
            creator=RawCreator(
                platform=self.platform,
                handle=item.get("ownerUsername") or "unknown",
                display_name=item.get("ownerFullName"),
                followers=_int(item.get("ownerFollowersCount")),
                niche=niche,
                country=region,
            ),
            published_at=_parse_time(item.get("timestamp")),
            duration_sec=float(item.get("videoDuration") or 0),
            caption=caption,
            hashtags=item.get("hashtags") or re.findall(r"#(\w+)", caption),
            thumbnail_url=item.get("displayUrl"),
            # playCount is the headline number Instagram surfaces, and the direct
            # analogue of TikTok's playCount and YouTube's viewCount. videoViewCount
            # is a stricter internal metric and runs materially lower.
            views=_int(item.get("videoPlayCount") or item.get("videoViewCount")),
            likes=_int(item.get("likesCount")),
            comments=_int(item.get("commentsCount")),
            # Only present when includeSharesCount is enabled on the run.
            shares=_int(item.get("sharesCount")),
            saves=0,
            country=region,
            language=None,
            niche=niche,
            sound_name=(item.get("musicInfo") or {}).get("song_name"),
        )
