"""Rank trends for one creator's "For You" feed.

Relevance is a multiplier on the opportunity score rather than a replacement for
it: a perfectly on-niche trend that is already saturated is still a bad
recommendation, and the feed should say so.
"""

from __future__ import annotations

from typing import Any

# Niches that reliably share formats. Used to widen the feed past exact matches
# without drifting into irrelevance.
ADJACENT_NICHES = {
    "ai": {"technology", "productivity", "business", "startups"},
    "technology": {"ai", "productivity", "gaming"},
    "productivity": {"ai", "business", "education", "technology"},
    "business": {"startups", "productivity", "finance", "marketing"},
    "startups": {"business", "ai", "marketing"},
    "marketing": {"business", "startups", "design"},
    "finance": {"business", "education"},
    "fitness": {"health", "food", "lifestyle"},
    "health": {"fitness", "food"},
    "food": {"lifestyle", "health"},
    "beauty": {"fashion", "lifestyle"},
    "fashion": {"beauty", "lifestyle", "design"},
    "design": {"technology", "marketing", "fashion"},
    "education": {"productivity", "technology", "finance"},
    "gaming": {"technology", "entertainment"},
    "travel": {"lifestyle", "food"},
    "lifestyle": {"travel", "food", "fashion", "beauty"},
}

DIFFICULTY_RANK = {"low": 0, "medium": 1, "high": 2}

GOAL_PREFERENCES = {
    # goal -> (signal boosted, weight)
    "brand_growth": ("cross_platform", 0.08),
    "audience_growth": ("growth", 0.12),
    "sales": ("engagement", 0.10),
    "authority": ("adaptability", 0.08),
    "community": ("engagement", 0.12),
}


def relevance(trend: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    """Return a 0–1 relevance score plus the reasons behind it."""
    reasons: list[str] = []
    score = 0.0

    niche = (profile.get("niche") or "").lower()
    trend_niches = {str(n).lower() for n in (trend.get("niches") or [])}

    # --- niche fit (0.40) ---
    if niche and niche in trend_niches:
        score += 0.40
        reasons.append(f"Already working in {niche}")
    elif niche and (ADJACENT_NICHES.get(niche, set()) & trend_niches):
        score += 0.26
        overlap = sorted(ADJACENT_NICHES.get(niche, set()) & trend_niches)[0]
        reasons.append(f"Working in {overlap}, which shares formats with {niche}")
    elif trend.get("adaptability") == "high":
        score += 0.16
        reasons.append("Travels well across niches")

    # --- platform fit (0.22) ---
    user_platforms = {str(p).lower() for p in (profile.get("platforms") or [])}
    trend_platforms = {str(p).lower() for p in (trend.get("platforms") or [])}
    if user_platforms & trend_platforms:
        overlap = user_platforms & trend_platforms
        score += 0.22 if len(overlap) > 1 else 0.17
        reasons.append(f"Live on {', '.join(sorted(overlap))}")

    # --- language fit (0.12) ---
    user_langs = {str(x).lower() for x in (profile.get("languages") or [])}
    trend_langs = {str(x).lower() for x in (trend.get("languages") or [])}
    if not user_langs or (user_langs & trend_langs):
        score += 0.12
    elif trend_langs:
        reasons.append("Mostly in a language you do not publish in")

    # --- content type fit (0.12) ---
    user_types = {str(t).lower() for t in (profile.get("content_types") or [])}
    trend_types = {str(t).lower() for t in (trend.get("content_types") or [])}
    if user_types & trend_types:
        score += 0.12
        reasons.append(f"Matches your {sorted(user_types & trend_types)[0]} content")

    # --- production capacity fit (0.14) ---
    capacity = DIFFICULTY_RANK.get(profile.get("production_capacity") or "medium", 1)
    required = DIFFICULTY_RANK.get(trend.get("production_difficulty") or "medium", 1)
    if required <= capacity:
        score += 0.14
        if required == 0:
            reasons.append("Low production effort")
    else:
        # Don't hide it, just discount it — the user can still decide to stretch.
        score += 0.04
        reasons.append("Needs more production than you usually do")

    # --- goal alignment ---
    goal = profile.get("goal")
    if goal in GOAL_PREFERENCES:
        signal, weight = GOAL_PREFERENCES[goal]
        components = {
            c["key"]: c["value"]
            for c in trend.get("score_breakdown", {}).get("opportunity_score", {}).get(
                "components", []
            )
        }
        score += weight * components.get(signal, 0.5)

    return {"relevance": round(min(1.0, score), 3), "reasons": reasons[:3]}


def rank_for_user(
    trends: list[dict[str, Any]], profile: dict[str, Any], limit: int | None = None
) -> list[dict[str, Any]]:
    """Blend opportunity with personal relevance.

    Weighting is 60/40 toward relevance so the feed feels personal, but the
    opportunity term keeps saturated or declining formats out of the top slots
    even when they are dead-on for the user's niche.
    """
    scored = []
    for trend in trends:
        rel = relevance(trend, profile)
        opportunity = (trend.get("opportunity_score") or 0) / 100.0
        final = 0.6 * rel["relevance"] + 0.4 * opportunity
        scored.append(
            {
                **trend,
                "relevance_score": rel["relevance"],
                "relevance_reasons": rel["reasons"],
                "feed_score": round(final * 100, 1),
            }
        )

    scored.sort(key=lambda t: -t["feed_score"])
    return scored[:limit] if limit else scored
