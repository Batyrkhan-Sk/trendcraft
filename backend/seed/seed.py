"""Seed a realistic corpus and run the real trend engine over it.

    python -m seed.seed [--reset]

What this does and does not do:

* **Does** write creators, videos, metric histories and AI analyses that look like
  what the connectors and the extraction stage would produce.
* **Does** then call the production ``rebuild_trends`` — clustering, aggregation,
  scoring, status classification and the opportunity score are all computed for
  real. Nothing on the dashboard is a hard-coded number.
* **Does not** invent trend rankings. If the archetypes were changed, the scores
  and statuses would change with them.

Hand-written narrative sections from ``archetypes.py`` are applied only when no
Gemini key is configured; with a key, the LLM writes them.
"""

from __future__ import annotations

import argparse
import math
import random
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, text

from app.ai import client as llm
from app.ai import embeddings
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import (
    Creator,
    Trend,
    TrendVideo,
    User,
    UserProfile,
    Video,
    VideoAnalysis,
    VideoMetric,
)
from app.pipeline import runner
from seed.archetypes import ARCHETYPES, BY_KEY

RNG = random.Random(20260817)

#: How each phase distributes its videos across the last 28 days. The engine reads
#: adoption growth from the 7-day vs prior-7-day counts, so these fractions are
#: what actually produce "emerging" versus "declining" — the labels are derived,
#: never assigned.
PHASE_WINDOWS = {
    # (days 0-6, days 7-13, days 14-27) as fractions of the archetype's videos
    "emerging": (0.62, 0.24, 0.14),
    "growing": (0.48, 0.30, 0.22),
    "viral": (0.38, 0.32, 0.30),
    "declining": (0.16, 0.40, 0.44),
}

#: Multiplier on a creator's baseline views. Drives creator-normalised lift, which
#: is the signal that separates "this format works" from "this account is big".
PHASE_LIFT = {
    "emerging": (1.6, 3.4),
    "growing": (1.5, 3.0),
    "viral": (1.2, 2.2),
    "declining": (0.7, 1.3),
}

HANDLE_PARTS = [
    "nova", "atlas", "kite", "vertex", "harbor", "lumen", "orbit", "ridge", "flint",
    "canvas", "delta", "ember", "quill", "north", "vector", "aspen", "cobalt", "juno",
    "prism", "marlow", "sable", "tundra", "wren", "zephyr", "onyx", "clover", "brio",
]
HANDLE_SUFFIX = ["builds", "daily", "studio", "lab", "notes", "hq", "makes", "irl", "co", ""]

FIRST_NAMES = [
    "Mara", "Dev", "Ines", "Kofi", "Lena", "Tomas", "Ayo", "Sana", "Nils", "Rhea",
    "Idris", "Paula", "Yuki", "Omar", "Freya", "Bruno", "Nadia", "Theo", "Alma", "Kian",
    "Zara", "Milo", "Runa", "Ravi", "Elif", "Noor", "Jonas", "Cleo",
]


def _handle(used: set[str]) -> str:
    while True:
        h = f"{RNG.choice(HANDLE_PARTS)}{RNG.choice(HANDLE_SUFFIX)}"
        if RNG.random() < 0.3:
            h += str(RNG.randint(2, 99))
        if h not in used:
            used.add(h)
            return h


def _fill_hook(archetype: dict) -> str:
    template = RNG.choice(archetype["hooks"])
    return template.format(
        noun=RNG.choice(archetype.get("nouns", ["workflow"])),
        tool=RNG.choice(archetype.get("tools", ["the tool"])),
        thing=RNG.choice(archetype.get("things", ["it"])),
        practice=RNG.choice(archetype.get("practices", ["that"])),
        action=RNG.choice(archetype.get("actions", ["starting out"])),
        role=RNG.choice(archetype.get("roles", ["creator"])),
        niche=RNG.choice(archetype["niches"]),
        n=RNG.choice([3, 6, 12, 30, 47, 90, 128]),
    )


def _publish_schedule(phase: str, count: int, now: datetime) -> list[datetime]:
    """Publish times for one archetype, allocated to windows deterministically.

    Sampling each video independently would leave the 7-day vs prior-7-day counts
    to chance, and on a 14-video format that swings the reported growth rate by
    hundreds of percent. Allocating exact counts per window makes the seeded
    lifecycle reproducible while the *rate itself* is still computed by the
    engine from the resulting dates.
    """
    recent_share, mid_share, _ = PHASE_WINDOWS[phase]
    n_recent = round(count * recent_share)
    n_mid = round(count * mid_share)
    n_old = max(0, count - n_recent - n_mid)

    dates: list[datetime] = []
    # Spread evenly inside each window with a little jitter, so day-level counts
    # stay stable but publish times are not artificially regular.
    for n, (lo, hi) in ((n_recent, (0.2, 6.9)), (n_mid, (7.0, 13.9)), (n_old, (14.0, 27.5))):
        for i in range(n):
            frac = (i + 0.5) / max(1, n)
            days = lo + frac * (hi - lo) + RNG.uniform(-0.25, 0.25)
            dates.append(now - timedelta(days=max(0.1, min(27.9, days))))

    RNG.shuffle(dates)
    return dates


def build_corpus(db, now: datetime) -> dict[str, str]:
    """Insert creators, videos, metrics and analyses. Returns video_id -> archetype key."""
    used_handles: set[str] = set()
    archetype_of: dict[str, str] = {}
    pending: list[tuple[Video, dict]] = []

    for archetype in ARCHETYPES:
        lo_lift, hi_lift = PHASE_LIFT[archetype["phase"]]
        mean_lift = (lo_lift + hi_lift) / 2
        lo_views, hi_views = archetype["base_views"]

        creators: list[Creator] = []
        for _ in range(archetype["creators"]):
            platform = RNG.choice(archetype["platforms"])
            idx = RNG.randrange(len(archetype["countries"]))

            # Work backwards from the reach the format actually achieves: pick a
            # log-uniform target within the band, then set the creator's baseline
            # so a typical video lands there. Doing it this way keeps
            # creator-normalised lift a real signal — deriving views from an
            # unrelated follower distribution and clamping to the band would
            # flatten every creator onto the same number.
            target = math.exp(RNG.uniform(math.log(lo_views), math.log(hi_views)))
            baseline = max(600, int(target / mean_lift))
            # Typical short-form reach sits well under follower count.
            followers = int(baseline / RNG.uniform(0.05, 0.22))

            creators.append(
                Creator(
                    platform=platform,
                    handle=_handle(used_handles),
                    display_name=f"{RNG.choice(FIRST_NAMES)} {RNG.choice(['R.', 'K.', 'M.', 'S.', 'L.'])}",
                    followers=followers,
                    baseline_median_views=baseline,
                    niche=RNG.choice(archetype["niches"]),
                    country=archetype["countries"][idx],
                    language=archetype["languages"][idx],
                )
            )
        db.add_all(creators)
        db.flush()
        RNG.shuffle(creators)

        publish_dates = _publish_schedule(archetype["phase"], archetype["videos"], now)

        for i in range(archetype["videos"]):
            # Cycle rather than sample: real format adoption spreads across many
            # creators posting once or twice each, and random sampling would let a
            # single creator own five of fourteen videos — which would then look
            # like one person's series rather than a trend.
            creator = creators[i % len(creators)]
            published = publish_dates[i]
            age_hours = max(2.0, (now - published).total_seconds() / 3600)

            lift = RNG.uniform(lo_lift, hi_lift)
            views = max(1_200, int(creator.baseline_median_views * lift))

            engagement = RNG.uniform(*archetype["engagement"])
            interactions = int(views * engagement)
            likes = int(interactions * RNG.uniform(0.70, 0.84))
            comments = int(interactions * RNG.uniform(0.05, 0.11))
            shares = int(interactions * RNG.uniform(0.05, 0.14))
            saves = max(0, interactions - likes - comments - shares)

            hook = _fill_hook(archetype)
            duration = round(RNG.uniform(*archetype["duration"]), 1)
            idx = RNG.randrange(len(archetype["countries"]))

            video = Video(
                platform=creator.platform,
                external_id=f"{archetype['key']}-{i}-{RNG.randrange(10**8):08d}",
                creator_id=creator.id,
                url=_url(creator.platform, creator.handle),
                thumbnail_url=None,
                caption=f"{hook} {archetype['cta']}",
                hashtags=_hashtags(archetype),
                published_at=published,
                duration_sec=duration,
                views=views,
                likes=likes,
                comments=comments,
                shares=shares,
                saves=saves,
                country=archetype["countries"][idx],
                language=archetype["languages"][idx],
                niche=creator.niche,
                content_type=archetype["content_type"],
                sound_name=_sound(archetype),
                collected_at=now,
            )
            db.add(video)
            db.flush()
            archetype_of[video.id] = archetype["key"]

            # Three metric points 24h apart. Two would give view velocity; the
            # third is what lets the engine measure whether the format's velocity
            # is rising or falling — the real 24-hour momentum signal.
            #
            # Every individual video decelerates; what differs between formats is
            # how fast, and how many fresh videos are entering. Jitter per video
            # so a format's momentum is an aggregate of varied curves rather than
            # one constant repeated N times.
            base_decay = 0.62 if archetype["phase"] in ("emerging", "growing") else 0.34
            decay = min(0.88, max(0.12, base_decay + RNG.uniform(-0.10, 0.10)))

            for captured, v in (
                (now - timedelta(hours=48), _views_at(views, age_hours, 48, decay)),
                (now - timedelta(hours=24), _views_at(views, age_hours, 24, decay)),
                (now, views),
            ):
                ratio = v / views if views else 0
                db.add(
                    VideoMetric(
                        video_id=video.id,
                        captured_at=captured,
                        views=v,
                        likes=int(likes * ratio),
                        comments=int(comments * ratio),
                        shares=int(shares * ratio),
                    )
                )

            pending.append((video, _analysis_payload(archetype, hook, duration)))

    # Batch the embeddings — one call for the whole corpus.
    signatures = [embeddings.format_signature(a) for _, a in pending]
    vectors = embeddings.embed_many(signatures)
    for (video, analysis), vector in zip(pending, vectors):
        db.add(
            VideoAnalysis(
                video_id=video.id,
                embedding=vector,
                extraction_model="seed",
                is_fallback=False,
                **analysis,
            )
        )

    db.commit()
    return archetype_of


def _views_at(total_views: int, age_hours: float, hours_ago: float, decay: float) -> int:
    """How many views this video had ``hours_ago`` hours in the past.

    Accrual is modelled as a saturating curve — cumulative share by age *t* is
    ``1 - decay^(t/24)`` — so a video earns most of its views in its first day and
    flattens after. Normalising by the value at the video's current age makes the
    present-day figure land exactly on ``total_views``.

    A lower ``decay`` means a steeper, faster-flattening curve: the video was
    pushed hard and then dropped.
    """
    age_then = age_hours - hours_ago
    if age_then <= 0:
        return 0  # The video did not exist yet.
    cumulative_then = 1 - decay ** (age_then / 24.0)
    cumulative_now = 1 - decay ** (max(age_hours, 0.1) / 24.0)
    if cumulative_now <= 0:
        return 0
    return int(total_views * (cumulative_then / cumulative_now))


def _url(platform: str, handle: str) -> str:
    token = f"{RNG.randrange(10**11):011d}"
    return {
        "tiktok": f"https://www.tiktok.com/@{handle}/video/{token}",
        "instagram": f"https://www.instagram.com/reel/{token[:11]}/",
        "youtube": f"https://www.youtube.com/shorts/{token[:11]}",
    }[platform]


def _hashtags(archetype: dict) -> list[str]:
    base = [archetype["content_type"], *archetype["niches"][:2]]
    return [f"#{t.replace(' ', '')}" for t in base] + ["#creator"]


def _sound(archetype: dict) -> str | None:
    if "trending audio" in (archetype["analysis"].get("audio_style") or ""):
        return RNG.choice(["original sound - shifted", "sped up phonk edit", "ambient drop v3"])
    return None


def _analysis_payload(archetype: dict, hook: str, duration: float) -> dict:
    a = archetype["analysis"]
    beats = a["narrative_structure"]
    return {
        "hook": hook,
        "topic": RNG.choice(archetype["topics"]),
        "content_format": a["content_format"],
        "narrative_structure": beats,
        "speaking_style": a["speaking_style"],
        "visual_style": a["visual_style"],
        "editing_patterns": a["editing_patterns"],
        "caption_style": a["caption_style"],
        "call_to_action": archetype["cta"],
        "emotional_tone": a["emotional_tone"],
        "audio_style": a["audio_style"],
        "target_audience": a["target_audience"],
        "main_message": hook,
        "opening_frames": (
            f"Opens on {a['visual_style'].split(',')[0]} with the line \"{hook}\" delivered "
            "before any context is given."
        ),
        "key_moments": [
            {"t": 0.0, "label": "Hook lands", "why": "Promise stated before any setup."},
            {
                "t": round(duration * 0.45, 1),
                "label": beats[len(beats) // 2].title(),
                "why": "Densest information point; carries the mid-video retention.",
            },
            {
                "t": round(duration * 0.82, 1),
                "label": "Payoff",
                "why": "Result is shown rather than described.",
            },
        ],
        "production_difficulty": a["production_difficulty"],
    }


def apply_handwritten_narratives(db, archetype_of: dict[str, str]) -> int:
    """Attach the authored narrative to each trend by majority archetype.

    Only runs in offline mode. Clusters are matched to archetypes by looking at
    which archetype most of their members came from — if clustering had split or
    merged archetypes, the mismatch would show up here rather than being papered
    over.
    """
    patched = 0
    for trend in db.scalars(select(Trend)).all():
        member_ids = [m.video_id for m in db.scalars(
            select(TrendVideo).where(TrendVideo.trend_id == trend.id)
        ).all()]
        keys = Counter(archetype_of.get(vid) for vid in member_ids if archetype_of.get(vid))
        if not keys:
            continue
        key, count = keys.most_common(1)[0]
        purity = count / max(1, len(member_ids))
        narrative = BY_KEY[key]["narrative"]

        trend.name = narrative["name"]
        trend.format_pattern = narrative["format_pattern"]
        trend.summary = narrative["summary"]
        trend.common_elements = narrative["common_elements"]
        trend.why_it_works = narrative["why_it_works"]
        trend.format_structure = narrative["format_structure"]
        trend.slug = key.replace("_", "-")
        patched += 1
        print(f"  · {narrative['name']:<40} {len(member_ids):>3} videos  purity {purity:.0%}")
    db.commit()
    return patched


def seed_demo_user(db) -> None:
    user = db.scalar(select(User).where(User.email == "demo@trendcraft.app"))
    if user is None:
        user = User(email="demo@trendcraft.app", name="Demo")
        db.add(user)
        db.flush()
    if user.profile is None:
        db.add(
            UserProfile(
                user_id=user.id,
                niche="ai",
                sub_niches=["automation", "developer tools"],
                audience="Founders and operators adopting AI tooling",
                audience_age="25-34",
                platforms=["tiktok", "youtube"],
                content_types=["tutorial", "experiment"],
                goal="audience_growth",
                languages=["en"],
                country="US",
                preferred_style="Direct, no-fluff, screen-recording heavy",
                production_capacity="low",
            )
        )
    db.commit()


def reset_schema() -> None:
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed TrendCraft with a realistic corpus")
    parser.add_argument("--reset", action="store_true", help="drop and recreate all tables first")
    args = parser.parse_args()

    if args.reset:
        print("Resetting schema…")
        reset_schema()
    else:
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        Base.metadata.create_all(bind=engine)

    now = datetime.now(timezone.utc)
    online = llm.available()
    print(f"Gemini configured: {online} (narratives will be {'generated' if online else 'authored'})")

    with SessionLocal() as db:
        if db.scalar(select(Video).limit(1)) and not args.reset:
            print("Corpus already present. Re-run with --reset to rebuild.")
            return 0

        print("Building corpus…")
        archetype_of = build_corpus(db, now)
        total = len(archetype_of)
        print(f"  {total} videos across {len(ARCHETYPES)} formats")

        print("Clustering and scoring…")
        result = runner.rebuild_trends(db, lookback_days=30, narrate=online)
        print(f"  {result}")

        if not online:
            print("Applying authored narratives…")
            apply_handwritten_narratives(db, archetype_of)

        print("Backfilling snapshot history…")
        for trend in db.scalars(select(Trend)).all():
            runner.backfill_snapshots(db, trend, days=14)
        db.commit()

        seed_demo_user(db)

        print("\nTrends:")
        for t in db.scalars(select(Trend).order_by(Trend.opportunity_score.desc())).all():
            print(
                f"  {t.opportunity_score:>5.1f} opp | {t.trend_score:>5.1f} trend | "
                f"{t.status:<10} | {t.competition_level:<6} | {t.growth_7d * 100:>+6.0f}%/wk | "
                f"{t.video_count:>3} videos | {t.name}"
            )

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
