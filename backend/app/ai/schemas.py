"""JSON schemas for every structured Gemini call.

Restricted to the OpenAPI subset Gemini's ``response_schema`` accepts: object,
array, string, number, integer, boolean, plus ``enum``, ``required`` and
``propertyOrdering``. No ``$ref``, no ``anyOf``, no ``additionalProperties``.
``propertyOrdering`` matters — Gemini generates fields in the given order, and
putting reasoning-ish fields before conclusions measurably improves quality.
"""

DIFFICULTY_ENUM = ["low", "medium", "high"]

VIDEO_ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "hook": {
            "type": "string",
            "description": "The literal opening line or on-screen text, verbatim if spoken.",
        },
        "opening_frames": {
            "type": "string",
            "description": "What is literally visible and audible in the first 3-5 seconds.",
        },
        "topic": {"type": "string", "description": "Subject matter in 3-8 words."},
        "content_format": {
            "type": "string",
            "description": (
                "The reusable format, independent of topic. "
                "E.g. 'talking head + screen recording tutorial', 'day-in-the-life vlog', "
                "'before/after transformation reveal'."
            ),
        },
        "narrative_structure": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Ordered beats, e.g. ['hook','problem','demonstration','result','cta'].",
        },
        "speaking_style": {"type": "string"},
        "visual_style": {"type": "string"},
        "editing_patterns": {
            "type": "array",
            "items": {"type": "string"},
            "description": "e.g. ['fast cuts every 2s','punch-in zooms','bold burned-in subtitles']",
        },
        "caption_style": {"type": "string"},
        "call_to_action": {"type": "string"},
        "emotional_tone": {"type": "string", "description": "One or two words."},
        "audio_style": {"type": "string", "description": "Music/audio character and role."},
        "target_audience": {"type": "string"},
        "main_message": {"type": "string"},
        "key_moments": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "t": {"type": "number", "description": "Seconds from start."},
                    "label": {"type": "string"},
                    "why": {"type": "string", "description": "Why this moment holds attention."},
                },
                "required": ["t", "label", "why"],
                "propertyOrdering": ["t", "label", "why"],
            },
        },
        "production_difficulty": {"type": "string", "enum": DIFFICULTY_ENUM},
    },
    "required": [
        "hook",
        "opening_frames",
        "topic",
        "content_format",
        "narrative_structure",
        "speaking_style",
        "visual_style",
        "editing_patterns",
        "emotional_tone",
        "main_message",
        "production_difficulty",
    ],
    "propertyOrdering": [
        "opening_frames",
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
        "key_moments",
        "production_difficulty",
    ],
}


TREND_NARRATIVE_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "description": "Short, specific trend name. Max 60 chars. No hype words.",
        },
        "format_pattern": {
            "type": "string",
            "description": "Templated pattern with placeholders, e.g. 'I replaced X with AI'.",
        },
        "summary": {
            "type": "string",
            "description": "Two sentences: what the format is and what is happening to it.",
        },
        "common_elements": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Concrete structural traits every member video shares.",
        },
        "why_it_works": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "principle": {
                        "type": "string",
                        "description": "Short slug, e.g. 'curiosity_gap', 'low_production_cost'.",
                    },
                    "title": {"type": "string"},
                    "detail": {
                        "type": "string",
                        "description": "Two sentences of mechanism, not praise.",
                    },
                },
                "required": ["principle", "title", "detail"],
                "propertyOrdering": ["principle", "title", "detail"],
            },
        },
        "format_structure": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "start": {"type": "number"},
                    "end": {"type": "number"},
                    "label": {"type": "string"},
                    "detail": {"type": "string"},
                },
                "required": ["start", "end", "label", "detail"],
                "propertyOrdering": ["start", "end", "label", "detail"],
            },
        },
    },
    "required": [
        "name",
        "format_pattern",
        "summary",
        "common_elements",
        "why_it_works",
        "format_structure",
    ],
    "propertyOrdering": [
        "format_pattern",
        "name",
        "summary",
        "common_elements",
        "why_it_works",
        "format_structure",
    ],
}


SHOT_SCHEMA = {
    "type": "object",
    "properties": {
        "index": {"type": "integer"},
        "label": {"type": "string", "description": "e.g. 'Shot 1 — Hook'"},
        "start": {"type": "number"},
        "end": {"type": "number"},
        "shot_type": {
            "type": "string",
            "enum": [
                "close-up talking head",
                "medium talking head",
                "wide shot",
                "screen recording",
                "b-roll",
                "split screen",
                "over-the-shoulder",
                "top-down",
                "reaction shot",
            ],
        },
        "camera": {"type": "string", "description": "Angle, distance, device, lens behaviour."},
        "action": {"type": "string", "description": "What happens on screen."},
        "spoken": {"type": "string", "description": "What the creator says, verbatim."},
        "on_screen_text": {"type": "string"},
        "lighting": {"type": "string"},
        "editing": {"type": "string", "description": "Cuts, zooms, transitions, speed."},
        "storyboard_frame": {
            "type": "string",
            "description": (
                "One sentence describing the composition of the representative frame, "
                "as if briefing a storyboard artist."
            ),
        },
    },
    "required": [
        "index",
        "label",
        "start",
        "end",
        "shot_type",
        "camera",
        "action",
        "editing",
        "storyboard_frame",
    ],
    "propertyOrdering": [
        "index",
        "label",
        "start",
        "end",
        "shot_type",
        "camera",
        "action",
        "spoken",
        "on_screen_text",
        "lighting",
        "editing",
        "storyboard_frame",
    ],
}


RECORDING_GUIDE_SCHEMA = {
    "type": "object",
    "properties": {
        "shots": {"type": "array", "items": SHOT_SCHEMA},
        "camera_setup": {
            "type": "object",
            "properties": {
                "talking_head": {"type": "string"},
                "screen_recording": {"type": "string"},
                "b_roll": {"type": "array", "items": {"type": "string"}},
                "lighting": {"type": "string"},
                "audio": {"type": "string"},
                "angles": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["talking_head", "screen_recording", "b_roll", "lighting", "audio"],
            "propertyOrdering": [
                "talking_head",
                "screen_recording",
                "b_roll",
                "lighting",
                "audio",
                "angles",
            ],
        },
        "editing_blueprint": {
            "type": "object",
            "properties": {
                "cuts": {"type": "string"},
                "zooms": {"type": "array", "items": {"type": "string"}},
                "text_overlays": {"type": "array", "items": {"type": "string"}},
                "subtitles": {"type": "string"},
                "speed_changes": {"type": "array", "items": {"type": "string"}},
                "transitions": {"type": "array", "items": {"type": "string"}},
                "sound_design": {"type": "string"},
            },
            "required": ["cuts", "zooms", "text_overlays", "subtitles"],
            "propertyOrdering": [
                "cuts",
                "zooms",
                "text_overlays",
                "subtitles",
                "speed_changes",
                "transitions",
                "sound_design",
            ],
        },
        "gear": {"type": "array", "items": {"type": "string"}},
        "common_mistakes": {"type": "array", "items": {"type": "string"}},
        "estimated_shoot_minutes": {"type": "integer"},
        "estimated_edit_minutes": {"type": "integer"},
    },
    "required": ["shots", "camera_setup", "editing_blueprint", "gear", "common_mistakes"],
    "propertyOrdering": [
        "shots",
        "camera_setup",
        "editing_blueprint",
        "gear",
        "common_mistakes",
        "estimated_shoot_minutes",
        "estimated_edit_minutes",
    ],
}


SCENARIO_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "hook": {"type": "string", "description": "The literal first line. Under 12 words."},
        "concept": {"type": "string", "description": "Two to three sentences."},
        "script_structure": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "start": {"type": "number"},
                    "end": {"type": "number"},
                    "label": {"type": "string"},
                    "script": {"type": "string", "description": "Words to say, verbatim."},
                    "direction": {"type": "string", "description": "What to show while saying it."},
                },
                "required": ["start", "end", "label", "script", "direction"],
                "propertyOrdering": ["start", "end", "label", "script", "direction"],
            },
        },
        "call_to_action": {"type": "string"},
        "caption": {"type": "string"},
        "hashtags": {"type": "array", "items": {"type": "string"}},
        "suggested_duration_sec": {"type": "integer"},
        "suggested_audio": {"type": "string"},
        "difficulty": {"type": "string", "enum": DIFFICULTY_ENUM},
        "why_it_could_work": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Reasons tied to the source trend's mechanics, not generic advice.",
        },
        "derived_from": {
            "type": "string",
            "description": "Which structural element of the source trend this keeps.",
        },
    },
    "required": [
        "title",
        "hook",
        "concept",
        "script_structure",
        "call_to_action",
        "caption",
        "hashtags",
        "suggested_duration_sec",
        "difficulty",
        "why_it_could_work",
        "derived_from",
    ],
    "propertyOrdering": [
        "title",
        "hook",
        "concept",
        "script_structure",
        "call_to_action",
        "caption",
        "hashtags",
        "suggested_duration_sec",
        "suggested_audio",
        "difficulty",
        "why_it_could_work",
        "derived_from",
    ],
}

SCENARIO_BATCH_SCHEMA = {
    "type": "object",
    "properties": {"scenarios": {"type": "array", "items": SCENARIO_SCHEMA}},
    "required": ["scenarios"],
}
