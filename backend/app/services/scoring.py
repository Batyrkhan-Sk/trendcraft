"""Trend scoring engine.

The product promise is that we surface formats that are *becoming* popular, not
formats that already won. Total view count is therefore never used directly as a
ranking signal — it only ever appears normalised, either by time (velocity) or by
the creator's own baseline (lift).

Nine signals feed the trend score. Each is squashed to 0–1 with an explicit,
documented curve so the resulting number can be explained back to the user
component by component (see :func:`score_trend` -> ``breakdown``).
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from app.core.config import settings

# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def log_scale(value: float, midpoint: float) -> float:
    """Map [0, inf) -> [0, 1) with 0.5 at ``midpoint``.

    Used for unbounded count-like quantities (views/hour, creator counts) where
    each order of magnitude should matter less than the previous one.
    """
    if value <= 0:
        return 0.0
    return clamp(math.log1p(value) / (2 * math.log1p(midpoint)))


def log_ratio(value: float, midpoint: float, decades: float = 1.5) -> float:
    """Map a quantity spanning many orders of magnitude to 0–1, centred on ``midpoint``.

    Prefer this over :func:`log_scale` when the input range covers several decades
    — follower counts run from 1e3 to 1e8, and ``log_scale`` compresses that whole
    span into roughly 0.3–0.7, which makes the signal useless. Here ``midpoint``
    maps to 0.5 and ``decades`` sets how many powers of ten reach the rails.
    """
    if value <= 0:
        return 0.0
    return clamp(0.5 + math.log10(value / midpoint) / (2 * decades))


def logistic(value: float, midpoint: float, steepness: float = 1.0) -> float:
    """Smooth S-curve centred on ``midpoint``. Used for ratios and growth rates."""
    try:
        return 1.0 / (1.0 + math.exp(-steepness * (value - midpoint)))
    except OverflowError:
        return 0.0 if value < midpoint else 1.0


def decay(hours_old: float, half_life: float) -> float:
    return 0.5 ** (max(0.0, hours_old) / half_life)


def safe_median(values: list[float], default: float = 0.0) -> float:
    return statistics.median(values) if values else default


# Engagement is scored relative to a per-platform baseline, because the platforms
# do not expose the same interactions at all — this is an API-surface difference,
# not an audience-behaviour one:
#
#   TikTok     likes + comments + shares + saves   (all four)
#   Instagram  likes + comments                    (shares/saves are private)
#   YouTube    likes + comments                    (no shares, no saves)
#
# Measured on this corpus: TikTok averages 11.9%, YouTube 1.9% — a 6x gap that is
# almost entirely the two missing interaction types. Using one baseline across
# platforms would permanently penalise every YouTube format for a signal it has
# no way to report. Re-derive these from your own corpus if it shifts; they are
# empirical, not universal constants.
PLATFORM_ENGAGEMENT_BASELINE = {
    "tiktok": 0.115,
    "instagram": 0.030,
    "youtube": 0.019,
}
DEFAULT_ENGAGEMENT_BASELINE = 0.03

# Weights sum to 1.0. Growth-oriented signals intentionally outweigh raw reach.
TREND_WEIGHTS = {
    "view_velocity": 0.16,
    "growth_rate": 0.20,
    "engagement_rate": 0.13,
    "conversation": 0.09,
    "creator_normalized": 0.15,
    "creator_adoption": 0.11,
    "cross_platform": 0.06,
    "recency": 0.06,
    "consistency": 0.04,
}

OPPORTUNITY_WEIGHTS = {
    "growth": 0.26,
    "engagement": 0.16,
    "low_competition": 0.18,
    "recency": 0.10,
    "cross_platform": 0.08,
    "adaptability": 0.12,
    "ease_of_production": 0.10,
}

DIFFICULTY_TO_EASE = {"low": 1.0, "medium": 0.6, "high": 0.25}
ADAPTABILITY_TO_SCORE = {"high": 1.0, "medium": 0.6, "low": 0.25}


@dataclass
class VideoSignal:
    """Everything the scorer needs to know about one cluster member."""

    video_id: str
    platform: str
    published_at: datetime
    views: int
    likes: int
    comments: int
    shares: int
    saves: int
    duration_sec: float
    creator_id: str
    creator_baseline_views: int
    creator_followers: int
    niche: str | None = None
    country: str | None = None
    language: str | None = None
    content_type: str | None = None
    #: (captured_at, views) history, oldest first.
    view_history: list[tuple[datetime, int]] = field(default_factory=list)

    @property
    def engagement_rate(self) -> float:
        if not self.views:
            return 0.0
        return (self.likes + self.comments + self.shares + self.saves) / self.views

    @property
    def conversation_rate(self) -> float:
        """Shares and saves signal intent to *use* the format, not just watch it."""
        if not self.views:
            return 0.0
        return (3 * self.shares + 2 * self.comments + 2 * self.saves) / self.views

    @property
    def creator_lift(self) -> float:
        """Views as a multiple of what this creator normally gets.

        A 40k-view video from a creator who averages 5k is a stronger format
        signal than a 2M-view video from a creator who always gets 2M.
        """
        baseline = self.creator_baseline_views or max(1, int(self.creator_followers * 0.08)) or 1
        return self.views / baseline

    def age_hours(self, now: datetime) -> float:
        return (now - self.published_at).total_seconds() / 3600.0

    def velocity(self, now: datetime) -> float:
        """Views per hour, measured over the most recent observation window.

        Falls back to lifetime average when no metric history exists.
        """
        if len(self.view_history) >= 2:
            (t0, v0), (t1, v1) = self.view_history[-2], self.view_history[-1]
            span = (t1 - t0).total_seconds() / 3600.0
            if span > 0:
                return max(0.0, (v1 - v0) / span)
        age = max(1.0, self.age_hours(now))
        return self.views / age

    def prior_velocity(self) -> float | None:
        """Views per hour over the window *before* the most recent one.

        ``None`` when there is not enough history to compare, which the caller
        must treat as "unknown" rather than as zero.
        """
        if len(self.view_history) < 3:
            return None
        (t0, v0), (t1, v1) = self.view_history[-3], self.view_history[-2]
        span = (t1 - t0).total_seconds() / 3600.0
        return max(0.0, (v1 - v0) / span) if span > 0 else None


@dataclass
class TrendAggregates:
    """Descriptive stats for a cluster, computed once and reused everywhere."""

    video_count: int
    creator_count: int
    avg_views: int
    median_views: int
    avg_engagement_rate: float
    median_velocity: float
    median_creator_lift: float
    median_conversation: float
    growth_24h: float
    growth_7d: float
    platforms: list[str]
    niches: list[str]
    countries: list[str]
    languages: list[str]
    content_types: list[str]
    median_duration_sec: float
    median_age_hours: float
    lift_consistency: float
    median_followers: int
    adoption_curve: list[dict]


def _distinct(values: list[str | None]) -> list[str]:
    seen: dict[str, int] = {}
    for v in values:
        if v:
            seen[v] = seen.get(v, 0) + 1
    return [k for k, _ in sorted(seen.items(), key=lambda kv: -kv[1])]


def adoption_growth(signals: list[VideoSignal], now: datetime, window_days: int = 7) -> float:
    """Relative change in *new videos adopting the format* between two windows.

    This is the headline "+184% this week" number. It measures format adoption by
    creators, which is what actually distinguishes a trend from a hit video.

    Only meaningful over multi-day windows: at a one-day resolution most formats
    see single-digit post counts, and the ratio between two noisy small integers
    is not a growth rate. Short-horizon movement is measured by
    :func:`velocity_growth` instead.
    """
    window = timedelta(days=window_days)
    recent = sum(1 for s in signals if now - s.published_at <= window)
    prior = sum(1 for s in signals if window < now - s.published_at <= 2 * window)
    if prior == 0:
        # No prior baseline: a burst from zero is real growth but unbounded, so cap
        # it rather than reporting infinity.
        return 2.0 if recent >= 3 else (1.0 if recent else 0.0)
    return (recent - prior) / prior


def velocity_growth(signals: list[VideoSignal]) -> float:
    """24-hour momentum: is the format as a whole gaining views faster than yesterday?

    Deliberately an *aggregate* comparison, not a median of per-video changes. An
    individual video's view rate only ever decays, so averaging per-video
    accelerations would report every format on earth as losing momentum. What
    actually moves is the total: a format with fresh videos entering can be
    accelerating in aggregate while every single member decelerates.
    """
    recent_total = 0.0
    prior_total = 0.0

    for s in signals:
        if len(s.view_history) < 3:
            continue
        (t0, v0), (t1, v1), (t2, v2) = s.view_history[-3:]
        prior_hours = (t1 - t0).total_seconds() / 3600.0
        recent_hours = (t2 - t1).total_seconds() / 3600.0
        if prior_hours <= 0 or recent_hours <= 0:
            continue
        prior_total += max(0.0, (v1 - v0) / prior_hours)
        recent_total += max(0.0, (v2 - v1) / recent_hours)

    if prior_total <= 0:
        # Nothing was moving yesterday; anything today is new momentum, but the
        # ratio is undefined so report a bounded value rather than infinity.
        return 1.0 if recent_total > 0 else 0.0

    # Clamp the tails so one runaway video cannot define the format's headline.
    return max(-0.95, min(3.0, (recent_total - prior_total) / prior_total))


def build_aggregates(signals: list[VideoSignal], now: datetime | None = None) -> TrendAggregates:
    now = now or datetime.now(timezone.utc)
    views = [s.views for s in signals]
    lifts = [s.creator_lift for s in signals]

    # Consistency: how reliably the format performs. High variance in lift means
    # the format works for some creators and not others — a riskier bet.
    if len(lifts) >= 3:
        spread = statistics.pstdev(lifts) / max(0.1, statistics.mean(lifts))
        consistency = clamp(1.0 - spread / 2.0)
    else:
        consistency = 0.5

    by_day: dict[str, int] = {}
    for s in signals:
        by_day[s.published_at.date().isoformat()] = (
            by_day.get(s.published_at.date().isoformat(), 0) + 1
        )
    curve = [{"date": d, "videos": c} for d, c in sorted(by_day.items())]

    return TrendAggregates(
        video_count=len(signals),
        creator_count=len({s.creator_id for s in signals}),
        avg_views=int(statistics.mean(views)) if views else 0,
        median_views=int(safe_median(views)),
        avg_engagement_rate=statistics.mean([s.engagement_rate for s in signals])
        if signals
        else 0.0,
        median_velocity=safe_median([s.velocity(now) for s in signals]),
        median_creator_lift=safe_median(lifts, 1.0),
        median_conversation=safe_median([s.conversation_rate for s in signals]),
        growth_24h=velocity_growth(signals),
        growth_7d=adoption_growth(signals, now, 7),
        platforms=_distinct([s.platform for s in signals]),
        niches=_distinct([s.niche for s in signals]),
        countries=_distinct([s.country for s in signals]),
        languages=_distinct([s.language for s in signals]),
        content_types=_distinct([s.content_type for s in signals]),
        median_duration_sec=safe_median([s.duration_sec for s in signals]),
        median_age_hours=safe_median([s.age_hours(now) for s in signals]),
        lift_consistency=consistency,
        median_followers=int(safe_median([float(s.creator_followers) for s in signals])),
        adoption_curve=curve,
    )


# ---------------------------------------------------------------------------
# Derived classifications
# ---------------------------------------------------------------------------


#: Competition midpoints. These are the one genuinely corpus-dependent set of
#: constants in the engine: "20 creators is average adoption" is true of a
#: single-region, single-window slice and would need re-fitting against a full
#: production corpus. They are named rather than inlined for exactly that reason.
#: Below this many distinct creators a format is still "emerging" — the sample is
#: too small for its growth rate to be treated as an established trajectory.
EMERGING_CREATOR_CEILING = 15

COMPETITION_CREATOR_MIDPOINT = 20
COMPETITION_VOLUME_MIDPOINT = 60
COMPETITION_FOLLOWER_MIDPOINT = 500_000


def classify_competition(agg: TrendAggregates) -> tuple[str, float]:
    """How crowded is this format already?

    Three inputs: how many creators have adopted it, how large those creators are
    (big accounts are harder to out-rank), and how much volume already exists.
    Adoption breadth carries the most weight — a format with many small creators
    is harder to stand out in than one with a few large ones, because the large
    ones are not competing for the same recommendation slots as a new entrant.

    Returns the label plus a 0–1 saturation value used by the opportunity score.
    """
    adoption = log_scale(agg.creator_count, midpoint=COMPETITION_CREATOR_MIDPOINT)
    account_size = log_ratio(agg.median_followers, midpoint=COMPETITION_FOLLOWER_MIDPOINT)
    volume = log_scale(agg.video_count, midpoint=COMPETITION_VOLUME_MIDPOINT)
    saturation = clamp(0.55 * adoption + 0.20 * account_size + 0.25 * volume)

    if saturation < 0.38:
        return "low", saturation
    if saturation < 0.56:
        return "medium", saturation
    return "high", saturation


def classify_status(agg: TrendAggregates, trend_score: float) -> str:
    """Emerging / Growing / Viral / Declining.

    Thresholds are expressed against *measured quantities* — reach, adoption
    breadth, growth — rather than against the composite score. The composite is a
    weighted average of squashed signals, so it lives in a narrow band (roughly
    40–75) and any absolute cut-off on it is arbitrary and brittle.

    Decline is checked first: a format can hold a high absolute reach for days
    after adoption has turned over, and that is exactly the state users must be
    warned away from rather than sold.
    """
    if agg.growth_7d < -0.15 or (agg.growth_24h < -0.45 and agg.growth_7d < 0.05):
        return "declining"

    reach = log_scale(agg.median_views, midpoint=400_000)
    broadly_adopted = agg.creator_count >= 20 and agg.video_count >= 20

    # Viral = large reach and wide adoption. Growth may have flattened; a format
    # at its peak is still viral, it is simply no longer an early opportunity.
    if reach >= 0.50 and broadly_adopted:
        return "viral"

    # Stage before momentum: a format only a handful of creators have touched is
    # emerging even when its growth rate is enormous, because a rate computed off
    # a base of three posts is not yet evidence of a trend.
    if agg.creator_count < EMERGING_CREATOR_CEILING and agg.growth_7d > 0:
        return "emerging"

    if agg.growth_7d >= 0.15 or (agg.growth_7d > 0.05 and trend_score >= 55):
        return "growing"

    # Anything left with wide adoption but no growth has plateaued rather than
    # emerged — calling it "emerging" would overstate the remaining window.
    if broadly_adopted:
        return "viral" if reach >= 0.35 else "declining"

    return "emerging"


def classify_adaptability(agg: TrendAggregates) -> str:
    """How well the format travels to a niche it did not start in.

    Proxied by observed niche spread — a format already working in four niches
    will almost certainly work in a fifth.
    """
    niches = len(agg.niches)
    if niches >= 4 and agg.lift_consistency > 0.4:
        return "high"
    if niches >= 2:
        return "medium"
    return "low"


def infer_production_difficulty(difficulties: list[str], median_duration: float) -> str:
    """Consensus difficulty across analysed members, nudged by length."""
    if not difficulties:
        return "medium"
    counts = {d: difficulties.count(d) for d in set(difficulties)}
    label = max(counts, key=lambda d: counts[d])
    if median_duration > 75 and label == "low":
        return "medium"
    return label


# ---------------------------------------------------------------------------
# Scores
# ---------------------------------------------------------------------------

SIGNAL_LABELS = {
    "view_velocity": "View velocity",
    "growth_rate": "Growth rate",
    "engagement_rate": "Engagement rate",
    "conversation": "Share & comment activity",
    "creator_normalized": "Creator-normalised lift",
    "creator_adoption": "Creator adoption",
    "cross_platform": "Cross-platform presence",
    "recency": "Recency",
    "consistency": "Historical consistency",
}


def score_trend(agg: TrendAggregates, production_difficulty: str = "medium") -> dict:
    """Return trend score, opportunity score and a full explanation of both."""
    primary_platform = agg.platforms[0] if agg.platforms else "tiktok"
    engagement_baseline = PLATFORM_ENGAGEMENT_BASELINE.get(
        primary_platform, DEFAULT_ENGAGEMENT_BASELINE
    )

    signals = {
        "view_velocity": log_scale(agg.median_velocity, midpoint=2_500),
        # Centred at +25% weekly adoption growth; ±100% saturates the curve.
        "growth_rate": logistic(agg.growth_7d, midpoint=0.25, steepness=2.6),
        "engagement_rate": clamp(agg.avg_engagement_rate / (engagement_baseline * 2)),
        "conversation": clamp(agg.median_conversation / 0.06),
        # 1.0x lift = the creator's normal performance = 0.5 on the curve.
        "creator_normalized": logistic(agg.median_creator_lift, midpoint=1.8, steepness=1.1),
        "creator_adoption": log_scale(agg.creator_count, midpoint=30),
        "cross_platform": clamp(len(agg.platforms) / 3.0),
        "recency": decay(agg.median_age_hours, settings.trend_half_life_hours),
        "consistency": agg.lift_consistency,
    }

    trend_score = 100.0 * sum(TREND_WEIGHTS[k] * v for k, v in signals.items())

    competition_level, saturation = classify_competition(agg)
    adaptability = classify_adaptability(agg)

    opportunity_signals = {
        "growth": signals["growth_rate"],
        "engagement": signals["engagement_rate"],
        "low_competition": 1.0 - saturation,
        "recency": signals["recency"],
        "cross_platform": signals["cross_platform"],
        "adaptability": ADAPTABILITY_TO_SCORE[adaptability],
        "ease_of_production": DIFFICULTY_TO_EASE.get(production_difficulty, 0.6),
    }
    opportunity_score = 100.0 * sum(
        OPPORTUNITY_WEIGHTS[k] * v for k, v in opportunity_signals.items()
    )

    status = classify_status(agg, trend_score)
    # A format past its peak is not an opportunity regardless of its raw numbers.
    if status == "declining":
        opportunity_score *= 0.65

    breakdown = {
        "trend_score": {
            "total": round(trend_score, 1),
            "components": [
                {
                    "key": key,
                    "label": SIGNAL_LABELS[key],
                    "value": round(value, 3),
                    "weight": TREND_WEIGHTS[key],
                    "contribution": round(100 * TREND_WEIGHTS[key] * value, 1),
                }
                for key, value in sorted(
                    signals.items(), key=lambda kv: -TREND_WEIGHTS[kv[0]] * kv[1]
                )
            ],
        },
        "opportunity_score": {
            "total": round(opportunity_score, 1),
            "components": [
                {
                    "key": key,
                    "label": key.replace("_", " ").capitalize(),
                    "value": round(value, 3),
                    "weight": OPPORTUNITY_WEIGHTS[key],
                    "contribution": round(100 * OPPORTUNITY_WEIGHTS[key] * value, 1),
                }
                for key, value in sorted(
                    opportunity_signals.items(), key=lambda kv: -OPPORTUNITY_WEIGHTS[kv[0]] * kv[1]
                )
            ],
        },
        "inputs": {
            "growth_7d_pct": round(agg.growth_7d * 100, 1),
            "growth_24h_pct": round(agg.growth_24h * 100, 1),
            "median_velocity_per_hour": round(agg.median_velocity, 1),
            "median_creator_lift": round(agg.median_creator_lift, 2),
            "creator_count": agg.creator_count,
            "video_count": agg.video_count,
            "avg_engagement_rate": round(agg.avg_engagement_rate, 4),
            "engagement_baseline": engagement_baseline,
            "saturation": round(saturation, 3),
            "median_age_hours": round(agg.median_age_hours, 1),
        },
    }

    return {
        "trend_score": round(trend_score, 1),
        "opportunity_score": round(min(100.0, opportunity_score), 1),
        "status": status,
        "competition_level": competition_level,
        "adaptability": adaptability,
        "production_difficulty": production_difficulty,
        "score_breakdown": breakdown,
    }


def explain_opportunity(trend_like: dict) -> list[str]:
    """Plain-language reasons the opportunity score landed where it did."""
    b = trend_like.get("score_breakdown", {})
    inputs = b.get("inputs", {})
    reasons: list[str] = []

    growth = inputs.get("growth_7d_pct", 0)
    if growth >= 50:
        reasons.append(
            f"Adoption is up {growth:.0f}% week over week — creators are still "
            "entering the format, not leaving it."
        )
    elif growth <= 0:
        reasons.append(
            f"Adoption moved {growth:.0f}% this week, so the window is closing rather than opening."
        )

    comp = trend_like.get("competition_level")
    if comp == "low":
        reasons.append(
            f"Only {inputs.get('creator_count', 0)} creators have adopted it, "
            "so the format is not yet crowded."
        )
    elif comp == "high":
        reasons.append(
            "Competition is high — large accounts already own this format, "
            "so differentiation matters more than speed."
        )

    lift = inputs.get("median_creator_lift", 1)
    if lift >= 1.5:
        reasons.append(
            f"Videos in this format do {lift:.1f}x their creator's normal views, "
            "which means the format is carrying the performance, not the audience size."
        )

    if trend_like.get("adaptability") == "high":
        reasons.append("It already works across several unrelated niches, so it should travel well.")

    if trend_like.get("production_difficulty") == "low":
        reasons.append("Production difficulty is low — a phone and a screen recorder are enough.")

    return reasons
