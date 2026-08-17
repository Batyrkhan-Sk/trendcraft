"""Turn a numeric cluster into something a human can act on.

Produces the trend's name, its templated pattern, the "Why it works" breakdown and
the timed format structure shown on the breakdown page.
"""

from __future__ import annotations

import re
import statistics
from collections import Counter
from typing import Any

from app.ai import client
from app.ai.prompts import TREND_NARRATOR
from app.ai.schemas import TREND_NARRATIVE_SCHEMA
from app.core.config import settings

# Structural mechanisms we can assert from the extracted analyses alone. Used by
# the offline fallback and as a vocabulary hint for the model.
MECHANISM_LIBRARY = {
    "curiosity_gap": {
        "title": "Opens a loop the viewer needs closed",
        "detail": (
            "The hook states an outcome without the method, so leaving early means "
            "leaving without the answer. Retention through the first five seconds is "
            "bought by withholding, not by production value."
        ),
    },
    "concrete_promise": {
        "title": "Promises something specific and checkable",
        "detail": (
            "A bounded claim — a number, a timeframe, a named tool — tells the viewer "
            "exactly what they get. Specific promises convert better than vague ones "
            "because the viewer can predict the payoff and decide it is worth 30 seconds."
        ),
    },
    "low_production_cost": {
        "title": "Costs almost nothing to make",
        "detail": (
            "A phone, a screen recording and available light are enough. Low cost per "
            "attempt means creators can post repeatedly, which is what drives an "
            "adoption curve rather than a single spike."
        ),
    },
    "visible_payoff": {
        "title": "The payoff is visual, not described",
        "detail": (
            "The result is shown on screen rather than claimed in voiceover. Viewers "
            "verify the outcome themselves, which is what earns the share instead of "
            "just the like."
        ),
    },
    "topic_portable": {
        "title": "The structure survives a change of subject",
        "detail": (
            "Nothing in the format depends on the original niche. Swapping the subject "
            "leaves the hook, pacing and payoff intact, which is why it spreads across "
            "unrelated categories rather than saturating one."
        ),
    },
    "identity_signal": {
        "title": "Lets the viewer take a side",
        "detail": (
            "The premise implies a position the audience already holds or rejects. "
            "Comments arrive as agreement or correction, and both feed distribution "
            "equally."
        ),
    },
    "process_transparency": {
        "title": "Shows the work, not just the result",
        "detail": (
            "Watching the middle of the process is what makes the ending credible. It "
            "also gives the video natural mid-roll structure, which holds attention "
            "past the ten-second drop-off."
        ),
    },
}


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:150] or "trend"


def _mode(values: list[str | None], default: str = "") -> str:
    filtered = [v for v in values if v]
    return Counter(filtered).most_common(1)[0][0] if filtered else default


def _common_beats(structures: list[list[str]]) -> list[str]:
    """The modal beat sequence, reconstructed position by position."""
    if not structures:
        return ["hook", "body", "payoff", "cta"]
    length = int(statistics.median([len(s) for s in structures if s] or [4]))
    beats: list[str] = []
    for i in range(max(3, min(length, 6))):
        at_i = [s[i] for s in structures if len(s) > i]
        if at_i:
            beats.append(Counter(at_i).most_common(1)[0][0])
    return beats or ["hook", "body", "payoff", "cta"]


def _timed_structure(beats: list[str], duration: float) -> list[dict]:
    """Distribute beats across the median duration with a front-loaded hook.

    The first beat is pinned to three seconds regardless of length — that is a
    property of the platforms, not of the format.
    """
    duration = max(12.0, duration or 30.0)
    if not beats:
        return []

    hook_end = min(3.0, duration * 0.12)
    remaining = duration - hook_end
    # Weight the demonstration-ish middle beats more heavily than the tail.
    weights = [1.0] * (len(beats) - 1)
    if len(weights) >= 2:
        weights[len(weights) // 2] = 1.8
    if weights:
        weights[-1] = 0.7
    total = sum(weights) or 1.0

    segments = [
        {
            "start": 0.0,
            "end": round(hook_end, 1),
            "label": beats[0].title(),
            "detail": "The promise is made before anything is explained.",
        }
    ]
    cursor = hook_end
    for beat, weight in zip(beats[1:], weights):
        span = remaining * (weight / total)
        segments.append(
            {
                "start": round(cursor, 1),
                "end": round(min(duration, cursor + span), 1),
                "label": beat.title(),
                "detail": "",
            }
        )
        cursor += span
    return segments


def _fallback_narrative(analyses: list[dict], stats: dict) -> dict[str, Any]:
    formats = [a.get("content_format") for a in analyses]
    dominant = _mode(formats, "short-form format")
    tones = [a.get("emotional_tone") for a in analyses]
    beats = _common_beats([a.get("narrative_structure") or [] for a in analyses])
    duration = stats.get("median_duration_sec") or 30.0

    # Pull the shared opening words across hooks — that is usually the pattern.
    hooks = [(a.get("hook") or "").strip() for a in analyses if a.get("hook")]
    pattern = dominant
    if len(hooks) >= 3:
        first_words = [" ".join(h.split()[:3]).lower() for h in hooks]
        common, count = Counter(first_words).most_common(1)[0]
        if count >= max(2, len(hooks) // 3):
            pattern = f"{common.capitalize()} X …"

    mechanisms = ["curiosity_gap", "concrete_promise"]
    if stats.get("production_difficulty") == "low":
        mechanisms.append("low_production_cost")
    if len(stats.get("niches") or []) >= 3:
        mechanisms.append("topic_portable")
    if any("demonstration" in b or "process" in b for b in beats):
        mechanisms.append("process_transparency")
    if any(t and t.lower() in {"surprise", "shock", "satisfaction"} for t in tones):
        mechanisms.append("visible_payoff")

    growth = stats.get("growth_7d_pct", 0)
    direction = "growing" if growth > 0 else "cooling"
    editing = Counter(
        e for a in analyses for e in (a.get("editing_patterns") or [])
    ).most_common(4)

    return {
        "name": dominant[:60].strip().capitalize(),
        "format_pattern": pattern,
        "summary": (
            f"{dominant.capitalize()} running about {int(duration)} seconds, "
            f"structured as {' → '.join(beats)}. Adoption is {direction} "
            f"({growth:+.0f}% week over week) across "
            f"{len(stats.get('niches') or [])} niche(s)."
        ),
        "common_elements": [
            f"Structure: {' → '.join(beats)}",
            f"Median duration: {int(duration)}s",
            *[f"{label} ({n} of {len(analyses)} videos)" for label, n in editing],
        ],
        "why_it_works": [
            {"principle": key, **MECHANISM_LIBRARY[key]} for key in dict.fromkeys(mechanisms)
        ],
        "format_structure": _timed_structure(beats, duration),
        "_model": "deterministic",
    }


def describe_cluster(analyses: list[dict], stats: dict) -> dict[str, Any]:
    """Name and explain one cluster. LLM-first, deterministic fallback."""
    if not analyses:
        return _fallback_narrative([], stats)

    sample = analyses[:12]
    payload = {
        "measured_statistics": stats,
        "videos": [
            {
                "hook": a.get("hook"),
                "topic": a.get("topic"),
                "content_format": a.get("content_format"),
                "narrative_structure": a.get("narrative_structure"),
                "visual_style": a.get("visual_style"),
                "editing_patterns": a.get("editing_patterns"),
                "emotional_tone": a.get("emotional_tone"),
                "main_message": a.get("main_message"),
                "duration_sec": a.get("duration_sec"),
            }
            for a in sample
        ],
    }

    result = client.structured_or_none(
        system=TREND_NARRATOR,
        prompt=(
            f"{len(analyses)} videos were clustered together as one format.\n\n"
            f"{client.dumps(payload)}\n\n"
            "Name the shared format and explain its mechanism. "
            "Available mechanism slugs (use these where they fit, invent others only "
            f"if none apply): {', '.join(MECHANISM_LIBRARY)}."
        ),
        schema=TREND_NARRATIVE_SCHEMA,
        model=settings.llm_model,
        temperature=0.5,
    )
    if not result:
        return _fallback_narrative(analyses, stats)

    result["_model"] = settings.llm_model
    # Guard against a model that returns an empty or degenerate structure.
    if not result.get("format_structure"):
        beats = _common_beats([a.get("narrative_structure") or [] for a in analyses])
        result["format_structure"] = _timed_structure(beats, stats.get("median_duration_sec", 30))
    return result


def build_slug(name: str, existing: set[str]) -> str:
    base = _slugify(name)
    slug, n = base, 2
    while slug in existing:
        slug = f"{base}-{n}"
        n += 1
    return slug
