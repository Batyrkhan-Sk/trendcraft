"""Stage 4 of the pipeline: turn a video into structured understanding.

Three tiers, tried in order, so the pipeline degrades instead of failing:

1. **Native video** — hand Gemini the actual file (or a YouTube URL, which it
   accepts directly) and let it watch and listen. This is the only tier that can
   report editing rhythm, framing and delivery honestly.
2. **Metadata-only LLM** — caption, hashtags, duration and sound name. Loses
   visual craft but still recovers topic, hook and rough format.
3. **Heuristic** — keyword rules over the caption. No network required. Marked
   ``is_fallback`` so the UI can flag it and a later pass can upgrade it.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from app.ai import client
from app.ai.prompts import VIDEO_ANALYST
from app.ai.schemas import VIDEO_ANALYSIS_SCHEMA
from app.core.config import settings

logger = logging.getLogger(__name__)

ANALYSIS_FIELDS = (
    "hook",
    "topic",
    "content_format",
    "narrative_structure",
    "speaking_style",
    "visual_style",
    "editing_patterns",
    "caption_style",
    "call_to_action",
    "emotional_tone",
    "audio_style",
    "target_audience",
    "main_message",
    "opening_frames",
    "key_moments",
    "production_difficulty",
)


def _build_prompt(video: dict[str, Any]) -> str:
    return (
        "Analyse this short-form video.\n\n"
        f"Platform: {video.get('platform')}\n"
        f"Duration: {video.get('duration_sec')}s\n"
        f"Caption: {video.get('caption') or '(none)'}\n"
        f"Hashtags: {', '.join(video.get('hashtags') or []) or '(none)'}\n"
        f"Sound: {video.get('sound_name') or '(original audio)'}\n"
        f"Creator niche: {video.get('niche') or 'unknown'}\n\n"
        "Extract the reusable format. Remember: format, not topic."
    )


def _analyze_with_video(video: dict[str, Any]) -> dict[str, Any] | None:
    """Tier 1 — multimodal pass over the actual media."""
    if not client.available():
        return None

    url = video.get("url") or ""
    media_path = video.get("local_path")

    try:
        from google import genai
        from google.genai import types

        gclient = genai.Client(api_key=settings.google_api_key)

        if media_path:
            # Files API: required for anything we had to download ourselves.
            uploaded = gclient.files.upload(file=media_path)
            part = types.Part.from_uri(file_uri=uploaded.uri, mime_type=uploaded.mime_type)
        elif "youtube.com" in url or "youtu.be" in url:
            # YouTube URLs are ingested server-side, no download needed.
            part = types.Part.from_uri(file_uri=url, mime_type="video/*")
        else:
            return None

        resp = gclient.models.generate_content(
            model=settings.vision_model,
            contents=[part, _build_prompt(video)],
            config={
                "system_instruction": VIDEO_ANALYST,
                "temperature": 0.2,
                "response_mime_type": "application/json",
                "response_schema": VIDEO_ANALYSIS_SCHEMA,
            },
        )
        import json

        data = json.loads(resp.text)
        data["_model"] = settings.vision_model
        data["_tier"] = "native_video"
        return data
    except Exception as exc:
        logger.warning("Native video analysis failed for %s: %s", video.get("external_id"), exc)
        return None


def _analyze_with_metadata(video: dict[str, Any]) -> dict[str, Any] | None:
    """Tier 2 — text-only inference from what the platform gave us."""
    data = client.structured_or_none(
        system=VIDEO_ANALYST,
        prompt=(
            _build_prompt(video)
            + "\n\nYou do NOT have the video itself, only this metadata. Infer the "
            "format conservatively and do not fabricate specific visual details "
            "such as exact cut timings or camera moves."
        ),
        schema=VIDEO_ANALYSIS_SCHEMA,
        model=settings.llm_fast_model,
        temperature=0.3,
    )
    if data:
        data["_model"] = settings.llm_fast_model
        data["_tier"] = "metadata_only"
    return data


# --- Tier 3: heuristics -----------------------------------------------------

_FORMAT_RULES: list[tuple[re.Pattern, str, list[str]]] = [
    (
        re.compile(r"\b(i (tested|tried|used|ran)|for \d+ days|\d+ day (experiment|challenge))\b"),
        "first-person time-boxed experiment log",
        ["hook", "setup", "process", "result", "verdict"],
    ),
    (
        re.compile(r"\b(tutorial|how to|step by step|guide|walkthrough)\b"),
        "talking head + screen recording tutorial",
        ["hook", "problem", "demonstration", "result", "cta"],
    ),
    (
        re.compile(r"\b(before|after|transformation|glow ?up|makeover)\b"),
        "before/after transformation reveal",
        ["hook", "before state", "process montage", "after reveal"],
    ),
    (
        re.compile(r"\b(mistake|wrong|stop doing|don'?t do|myth)\b"),
        "corrective myth-busting monologue",
        ["contrarian hook", "common belief", "correction", "proof", "cta"],
    ),
    (
        re.compile(r"\b(day in (the|my) life|routine|vlog)\b"),
        "day-in-the-life vlog montage",
        ["hook", "morning", "work block", "evening", "reflection"],
    ),
    (
        re.compile(r"\b(react|reaction|watching|rating|ranking|tier list)\b"),
        "reaction / ranking commentary",
        ["premise", "item 1", "item 2", "item 3", "verdict"],
    ),
]


def _heuristic_analysis(video: dict[str, Any]) -> dict[str, Any]:
    caption = (video.get("caption") or "").lower()
    tags = " ".join(video.get("hashtags") or []).lower()
    haystack = f"{caption} {tags}"

    content_format = "short-form talking head"
    structure = ["hook", "body", "payoff", "cta"]
    for pattern, label, beats in _FORMAT_RULES:
        if pattern.search(haystack):
            content_format, structure = label, beats
            break

    duration = float(video.get("duration_sec") or 0)
    first_sentence = re.split(r"[.!?\n]", video.get("caption") or "")[0].strip()

    return {
        "hook": first_sentence[:180] or "(hook not recoverable from metadata)",
        "opening_frames": "Not analysed — metadata-only ingestion.",
        "topic": (video.get("niche") or "general") + " content",
        "content_format": content_format,
        "narrative_structure": structure,
        "speaking_style": "unknown",
        "visual_style": "unknown",
        "editing_patterns": [],
        "caption_style": "platform default",
        "call_to_action": "",
        "emotional_tone": "unknown",
        "audio_style": video.get("sound_name") or "original audio",
        "target_audience": video.get("niche") or "general",
        "main_message": first_sentence[:240],
        "key_moments": [],
        "production_difficulty": "low" if duration <= 45 else "medium",
        "_model": "heuristic",
        "_tier": "heuristic",
    }


def analyze_video(
    video: dict[str, Any], *, allow_video: bool = True, allow_llm: bool = True
) -> dict[str, Any]:
    """Run the extraction ladder and return a normalised analysis dict.

    ``allow_llm=False`` drops straight to the heuristic tier. Use it for bulk
    backfills when the model quota is exhausted or reserved for other work —
    otherwise every video pays a failed API call before falling back anyway.
    """
    result = None
    if allow_llm and allow_video:
        result = _analyze_with_video(video)
    if result is None and allow_llm:
        result = _analyze_with_metadata(video)
    if result is None:
        result = _heuristic_analysis(video)

    normalised = {field: result.get(field) for field in ANALYSIS_FIELDS}
    normalised["narrative_structure"] = list(normalised.get("narrative_structure") or [])
    normalised["editing_patterns"] = list(normalised.get("editing_patterns") or [])
    normalised["key_moments"] = list(normalised.get("key_moments") or [])
    normalised["production_difficulty"] = normalised.get("production_difficulty") or "medium"
    normalised["extraction_model"] = result.get("_model")
    normalised["is_fallback"] = result.get("_tier") == "heuristic"
    return normalised
