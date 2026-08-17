"""Scenario generation, recreation kits and the "How to Record This Video" guide.

The contract that matters here: output must preserve the *structure* of a trend
while replacing its *substance*. Copying a creator's premise is both a legal and a
product failure — the user's video has to be theirs.
"""

from __future__ import annotations

import logging
from typing import Any

from app.ai import client
from app.ai.prompts import RECORDING_DIRECTOR, SCENARIO_WRITER
from app.ai.schemas import RECORDING_GUIDE_SCHEMA, SCENARIO_BATCH_SCHEMA
from app.core.config import settings

logger = logging.getLogger(__name__)


def _trend_brief(trend: dict) -> str:
    structure = "\n".join(
        f"  {s['start']:.0f}–{s['end']:.0f}s  {s['label']}: {s.get('detail', '')}"
        for s in (trend.get("format_structure") or [])
    )
    mechanisms = "\n".join(
        f"  - {w.get('title')}: {w.get('detail')}" for w in (trend.get("why_it_works") or [])
    )
    return (
        f"TREND: {trend.get('name')}\n"
        f"Pattern: {trend.get('format_pattern')}\n"
        f"Summary: {trend.get('summary')}\n"
        f"Status: {trend.get('status')} | Competition: {trend.get('competition_level')} | "
        f"Median duration: {trend.get('median_duration_sec', 30):.0f}s\n"
        f"Structure:\n{structure or '  (not available)'}\n"
        f"Why it works:\n{mechanisms or '  (not available)'}\n"
        f"Shared elements: {'; '.join(trend.get('common_elements') or []) or '(none)'}\n"
        f"Example hooks from real videos (DO NOT reuse these — they show the shape only):\n"
        + "\n".join(f"  - {h}" for h in (trend.get("example_hooks") or [])[:5])
    )


def _profile_brief(profile: dict) -> str:
    return (
        f"CREATOR\n"
        f"Niche: {profile.get('niche') or 'unspecified'}\n"
        f"Sub-topics: {', '.join(profile.get('sub_niches') or []) or 'unspecified'}\n"
        f"Audience: {profile.get('audience') or 'unspecified'}"
        f"{', age ' + profile['audience_age'] if profile.get('audience_age') else ''}\n"
        f"Platform: {profile.get('platform') or ', '.join(profile.get('platforms') or []) or 'tiktok'}\n"
        f"Goal: {profile.get('goal') or 'audience growth'}\n"
        f"Preferred style: {profile.get('preferred_style') or 'no preference'}\n"
        f"Topic to cover: {profile.get('topic') or '(creator has no specific topic in mind)'}\n"
        f"Production capacity: {profile.get('production_capacity') or 'medium'}\n"
        f"Languages: {', '.join(profile.get('languages') or ['en'])}"
    )


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------


def generate_scenarios(trend: dict, profile: dict, count: int = 3) -> list[dict[str, Any]]:
    result = client.structured_or_none(
        system=SCENARIO_WRITER,
        prompt=(
            f"{_trend_brief(trend)}\n\n{_profile_brief(profile)}\n\n"
            f"Write {count} distinct video scenarios that adapt this trend's structure "
            f"to this creator's niche. Target duration should stay close to the trend's "
            f"median duration. Each scenario must attack a different angle — do not "
            f"produce {count} rewordings of the same idea.\n\n"
            "Hard constraint: keep the structural skeleton, replace every specific. "
            "Nobody reading the output should be able to identify which original video "
            "it came from."
        ),
        schema=SCENARIO_BATCH_SCHEMA,
        model=settings.llm_model,
        temperature=0.85,
    )
    if result and result.get("scenarios"):
        scenarios = result["scenarios"][:count]
        for s in scenarios:
            s["generator_model"] = settings.llm_model
        return scenarios
    return _fallback_scenarios(trend, profile, count)


# Angles used by the offline fallback. Each keeps the trend's skeleton but rotates
# the stance, which is what stops the three outputs collapsing into one.
_ANGLES = [
    (
        "experiment",
        "I handed {topic} over to AI for 7 days",
        "Time-boxed first-person test with a measured outcome.",
    ),
    (
        "contrarian",
        "Everyone in {niche} is wrong about {topic}",
        "Stake out a position against the niche's default belief, then prove it.",
    ),
    (
        "teardown",
        "I rebuilt {topic} from scratch — here is what actually mattered",
        "Strip the subject to its components and show which one carries the result.",
    ),
    (
        "comparison",
        "{topic}: what I expected vs what actually happened",
        "Set an expectation on screen, then undercut it with the real outcome.",
    ),
]


#: Beat-level guidance for the offline fallback, keyed by the words that show up
#: in structure labels. Each entry is (what to say, what to show). These are
#: writing prompts the creator completes, not filler — a bracketed placeholder
#: like "[Setup] — cover X" is not something anyone can film.
_BEAT_GUIDANCE: list[tuple[tuple[str, ...], str, str]] = [
    (
        ("hook", "contrarian"),
        "{hook}",
        "Face cam, chest-up. Deliver it before any context.",
    ),
    (
        ("premise", "setup", "problem", "belief", "assumption"),
        "Name the exact thing you tested and why it was a risk: “I normally spend "
        "half my week on {topic}, so handing it over was a real bet.”",
        "Medium shot with your workspace visible behind you.",
    ),
    (
        ("process", "demonstration", "work", "item", "reveal", "build"),
        "Narrate what actually happened, including the part that went wrong. "
        "Name the moment it broke before you name the moment it worked.",
        "Screen recording or close b-roll of {topic}. Cut every 2–3 seconds.",
    ),
    (
        ("result", "payoff", "after", "outcome", "total", "moment"),
        "State the outcome as a number, not an adjective: how much time, money or "
        "output changed. Say it out loud as it appears on screen.",
        "Show the result full-frame. Hold one beat longer than feels natural.",
    ),
    (
        ("verdict", "cta", "lesson", "reflection", "next"),
        "One honest sentence on whether it was worth it, then: “Comment what I "
        "should put through this next.”",
        "Back to the hook framing so the video closes its own loop.",
    ),
]


#: Fallback by position, used when a beat's label matches no keyword. Formats name
#: their beats very differently ("Metric card", "Silent work", "Shipped state"),
#: but their *order* is near-universal: promise, context, work, payoff, close.
#: Position is therefore the more reliable signal, with keywords as the override.
_BEAT_BY_POSITION = ("hook", "setup", "process", "result", "cta")


def _beat_guidance(
    label: str, topic: str, niche: str, hook: str, index: int = 0, total: int = 5
) -> tuple[str, str]:
    key = label.lower()

    # Keyword match first — an explicit label beats an inferred position.
    for keywords, line, direction in _BEAT_GUIDANCE:
        if any(word in key for word in keywords):
            return (
                line.format(hook=hook, topic=topic, niche=niche),
                direction.format(topic=topic, niche=niche),
            )

    # Otherwise map the beat's position onto the canonical arc. The first beat is
    # always the promise and the last is always the close, whatever they're called.
    if total <= 1 or index == 0:
        slot = "hook"
    elif index == total - 1:
        slot = "cta"
    else:
        # Distribute the interior beats across setup → process → result.
        interior = (index - 1) / max(1, total - 2)
        slot = _BEAT_BY_POSITION[1 + min(2, int(interior * 3))]

    for keywords, line, direction in _BEAT_GUIDANCE:
        if slot in keywords:
            return (
                line.format(hook=hook, topic=topic, niche=niche),
                direction.format(topic=topic, niche=niche),
            )

    return (
        f"Cover the {label.lower()} of {topic} in one concrete sentence.",
        "Show the work rather than describing it.",
    )


def _fallback_scenarios(trend: dict, profile: dict, count: int) -> list[dict[str, Any]]:
    niche = profile.get("niche") or "your niche"
    topic = profile.get("topic") or trend.get("format_pattern") or "the tool you use most"
    duration = int(trend.get("median_duration_sec") or 30)
    structure = trend.get("format_structure") or []

    scenarios = []
    for key, hook_tpl, concept in _ANGLES[:count]:
        hook = hook_tpl.format(topic=topic, niche=niche)
        script = []
        beats = structure or [
            {"start": 0, "end": 3, "label": "Hook"},
            {"start": 3, "end": duration * 0.35, "label": "Setup"},
            {"start": duration * 0.35, "end": duration * 0.8, "label": "Demonstration"},
            {"start": duration * 0.8, "end": duration, "label": "Payoff"},
        ]
        for i, seg in enumerate(beats):
            label = seg["label"]
            line, direction = _beat_guidance(label, topic, niche, hook, i, len(beats))
            script.append(
                {
                    "start": round(float(seg["start"]), 1),
                    "end": round(float(seg["end"]), 1),
                    "label": label,
                    "script": line,
                    "direction": direction,
                }
            )

        scenarios.append(
            {
                "title": hook,
                "hook": hook,
                "concept": concept,
                "script_structure": script,
                "call_to_action": "Comment the tool you want tested next.",
                "caption": f"{hook} — full breakdown in the comments.",
                "hashtags": [f"#{niche.replace(' ', '').lower()}", "#howto", "#creator"],
                "suggested_duration_sec": duration,
                "suggested_audio": "Original audio, low-level ambient bed under the voiceover.",
                "difficulty": trend.get("production_difficulty") or "medium",
                "why_it_could_work": [
                    f"Keeps the '{trend.get('format_pattern')}' skeleton that is currently "
                    f"growing {trend.get('growth_7d', 0) * 100:+.0f}% per week.",
                    f"Angle ({key}) is not yet saturated inside {niche}.",
                ],
                "derived_from": trend.get("format_pattern") or trend.get("name"),
                "generator_model": "deterministic",
            }
        )
    return scenarios


# ---------------------------------------------------------------------------
# Recreation kit
# ---------------------------------------------------------------------------


def generate_recreation(trend: dict, profile: dict) -> dict[str, Any]:
    """One ready-to-shoot package for a trend — the "Recreate" button's payload."""
    scenarios = generate_scenarios(trend, profile, count=1)
    scenario = scenarios[0]
    scenario["recording_guide"] = generate_recording_guide(trend, scenario, profile)
    scenario["kind"] = "recreation"
    return scenario


# ---------------------------------------------------------------------------
# Recording guide
# ---------------------------------------------------------------------------


def generate_recording_guide(trend: dict, scenario: dict, profile: dict) -> dict[str, Any]:
    duration = scenario.get("suggested_duration_sec") or trend.get("median_duration_sec") or 30
    beats = "\n".join(
        f"  {s['start']:.0f}–{s['end']:.0f}s  {s['label']}: {s.get('script', '')}"
        for s in (scenario.get("script_structure") or [])
    )

    result = client.structured_or_none(
        system=RECORDING_DIRECTOR,
        prompt=(
            f"{_trend_brief(trend)}\n\n{_profile_brief(profile)}\n\n"
            f"SCENARIO TO SHOOT\n"
            f"Title: {scenario.get('title')}\n"
            f"Hook: {scenario.get('hook')}\n"
            f"Concept: {scenario.get('concept')}\n"
            f"Target duration: {duration}s\n"
            f"Script beats:\n{beats}\n\n"
            "Write the complete shooting plan. Produce 4–6 shots that sum to the target "
            "duration. The creator is filming alone on a phone."
        ),
        schema=RECORDING_GUIDE_SCHEMA,
        model=settings.llm_model,
        temperature=0.55,
    )
    if result:
        result["generator_model"] = settings.llm_model
        result["storyboard"] = _storyboard_from_shots(result.get("shots") or [])
        return result

    return _fallback_recording_guide(trend, scenario, duration)


#: Default shot grammar for a hook → demo → payoff → CTA short. Percentages of the
#: total runtime, so it stretches correctly for a 20s or a 60s video.
_SHOT_TEMPLATE = [
    {
        "label": "Shot 1 — Hook",
        "span": (0.0, 0.11),
        "shot_type": "close-up talking head",
        "camera": "Front camera, chest-up close-up, eyes level with the lens, small headroom.",
        "action": "Deliver the hook line straight down the barrel. No intro, no greeting.",
        "editing": "Punch-in zoom on the last two words. Cut the instant the line ends.",
        "storyboard_frame": "Face fills the upper two-thirds, bold hook text across the lower third.",
        "lighting": "Face a window, or put a single soft key just off-axis. Nothing behind you.",
    },
    {
        "label": "Shot 2 — Setup",
        "span": (0.11, 0.32),
        "shot_type": "medium talking head",
        "camera": "Step back to a medium shot so the workspace is visible behind you.",
        "action": "State the problem in one sentence and what you were trying to get out of it.",
        "editing": "Hard cut in from the hook. Keep one jump cut mid-sentence to compress a pause.",
        "storyboard_frame": "Creator centre-left, workspace visible right, caption line at bottom.",
        "lighting": "Same key as the hook. Let the room behind you fall darker.",
    },
    {
        "label": "Shot 3 — Demonstration",
        "span": (0.32, 0.66),
        "shot_type": "screen recording",
        "camera": "Full-screen capture at 60fps, cursor visible, UI zoomed to ~125%.",
        "action": "Show the actual process. Narrate over it rather than appearing on camera.",
        "editing": "Cut every 2–3 seconds. Zoom to 140% on each moment the screen changes.",
        "storyboard_frame": "Screen capture fills frame, small circular face cam bottom-right.",
        "lighting": "None needed — this is a screen capture. Set the OS to dark mode.",
    },
    {
        "label": "Shot 4 — Key moment",
        "span": (0.66, 0.84),
        "shot_type": "split screen",
        "camera": "Before state on the left, after state on the right, both held still.",
        "action": "Reveal the result. Say the number or the outcome out loud as it appears.",
        "editing": "Hold this shot 1s longer than the others — it is the payoff, let it land.",
        "storyboard_frame": "Vertical split, labelled BEFORE / AFTER, result value large on the right.",
        "lighting": "Match both halves. If either was shot on another day, match white balance.",
    },
    {
        "label": "Shot 5 — Result + CTA",
        "span": (0.84, 1.0),
        "shot_type": "close-up talking head",
        "camera": "Back to the hook framing so the video visually closes its own loop.",
        "action": "One-line verdict, then the call to action.",
        "editing": "No music tail. Cut on the final word so the loop restarts cleanly.",
        "storyboard_frame": "Same framing as shot 1, CTA text centred over the lower third.",
        "lighting": "Identical to shot 1 — the visual rhyme is what closes the loop.",
    },
]


def _fallback_recording_guide(trend: dict, scenario: dict, duration: float) -> dict[str, Any]:
    shots = []
    for i, tpl in enumerate(_SHOT_TEMPLATE, start=1):
        start, end = tpl["span"][0] * duration, tpl["span"][1] * duration
        shots.append(
            {
                "index": i,
                "label": tpl["label"],
                "start": round(start, 1),
                "end": round(end, 1),
                "shot_type": tpl["shot_type"],
                "camera": tpl["camera"],
                "action": tpl["action"],
                "spoken": scenario.get("hook", "") if i == 1 else "",
                "on_screen_text": scenario.get("hook", "") if i == 1 else "",
                "lighting": tpl["lighting"],
                "editing": tpl["editing"],
                "storyboard_frame": tpl["storyboard_frame"],
            }
        )

    return {
        "shots": shots,
        "camera_setup": {
            "talking_head": (
                "Phone at eye level on a small tripod, roughly an arm's length away. "
                "Chest-up framing, lens at eye height, look at the lens and not at yourself."
            ),
            "screen_recording": (
                "Record at 60fps in a clean window: hide bookmarks, close notifications, "
                "zoom the UI to about 125% so text survives the vertical crop."
            ),
            "b_roll": [
                "Hands on the keyboard, shot from a shallow side angle",
                "Top-down of the desk with the result visible on screen",
                "A slow push-in on the final output",
            ],
            "lighting": "One soft source in front, nothing bright behind you.",
            "audio": "Clip mic or wired earbuds. Record in the smallest soft room available.",
            "angles": ["Front camera at eye level", "Slight side angle for b-roll", "Top-down desk"],
        },
        "editing_blueprint": {
            "cuts": "Every 2–3 seconds during the demonstration, longer only on the payoff.",
            "zooms": [
                "Punch-in on the final words of the hook",
                "140% zoom each time the screen state changes",
                "Slow push on the result reveal",
            ],
            "text_overlays": [
                "Hook text on screen for the full first 3 seconds",
                "Label the before and after states explicitly",
                "Put the result value on screen as a number",
            ],
            "subtitles": "Burned in, 2–4 words per line, centred, appearing on the spoken word.",
            "speed_changes": ["1.5–2x through any waiting or loading", "1x on the payoff"],
            "transitions": ["Hard cuts only", "One whip pan into the reveal at most"],
            "sound_design": "Quiet bed under the voice, one soft accent on the reveal.",
        },
        "gear": ["Phone", "Small tripod", "Clip mic or wired earbuds", "Screen recorder"],
        "common_mistakes": [
            "Greeting the audience before the hook — it costs the first three seconds.",
            "Screen recording at default zoom, which is unreadable after the vertical crop.",
            "Explaining the result instead of showing it on screen.",
            "Letting music run past the final word, which breaks the loop.",
        ],
        "estimated_shoot_minutes": 25,
        "estimated_edit_minutes": 40,
        "generator_model": "deterministic",
        "storyboard": _storyboard_from_shots(shots),
    }


def _storyboard_from_shots(shots: list[dict]) -> list[dict]:
    """Frame-by-frame view derived from the shot list.

    Kept as a projection of ``shots`` rather than a separate generation so the
    storyboard can never drift out of sync with the plan it illustrates.
    """
    return [
        {
            "frame": i,
            "timecode": f"{int(s.get('start', 0)) // 60}:{int(s.get('start', 0)) % 60:02d}",
            "start": s.get("start", 0),
            "end": s.get("end", 0),
            "label": s.get("label", f"Shot {i}"),
            "shot_type": s.get("shot_type", ""),
            "description": s.get("storyboard_frame") or s.get("action", ""),
            "on_screen_text": s.get("on_screen_text") or "",
        }
        for i, s in enumerate(shots, start=1)
    ]
