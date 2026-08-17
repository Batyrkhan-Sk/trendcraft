"""Hand-authored format archetypes used to seed a realistic corpus.

These are *inputs* to the engine, not outputs. The seeder writes videos and their
AI analyses; clustering, scoring, status classification and the opportunity score
are then computed for real by the same code that runs in production. That means a
seeded database exercises the actual trend engine rather than displaying
pre-baked answers.

Each archetype also carries a hand-written narrative. It is used only when no
Gemini key is configured — with a key, ``narrative.describe_cluster`` writes these
sections itself.
"""

from __future__ import annotations

ARCHETYPES: list[dict] = [
    {
        "key": "ai_experiment_log",
        "phase": "growing",
        "videos": 26,
        "creators": 19,
        "platforms": ["tiktok", "instagram", "youtube"],
        "niches": ["ai", "productivity", "business", "technology"],
        "countries": ["US", "GB", "DE", "IN"],
        "languages": ["en", "en", "en", "de"],
        "content_type": "experiment",
        "duration": (28, 46),
        "base_views": (48_000, 900_000),
        "engagement": (0.072, 0.128),
        "difficulty": "low",
        "analysis": {
            "content_format": "first-person time-boxed AI experiment log",
            "narrative_structure": ["hook", "premise", "daily process", "result", "verdict"],
            "speaking_style": "casual direct-to-camera narration over screen capture",
            "visual_style": "handheld face cam intercut with full-screen app recording",
            "editing_patterns": [
                "hard cut every 2-3 seconds",
                "day counter overlay",
                "punch-in zoom on the result number",
                "bold burned-in subtitles",
            ],
            "caption_style": "burned-in, 3-4 words per line, centred",
            "emotional_tone": "curiosity",
            "audio_style": "low ambient bed under voiceover, no trending sound",
            "target_audience": "25-34 knowledge workers experimenting with AI tools",
            "production_difficulty": "low",
        },
        "hooks": [
            "I let AI run my entire {noun} for 7 days.",
            "I replaced my {noun} with AI for a week.",
            "I used AI to do my {noun} for 7 days straight.",
            "I gave AI full control of my {noun}. Day 1 broke immediately.",
            "For 7 days I did not touch my {noun}. AI did.",
            "I ran a 7-day experiment: AI instead of my {noun}.",
        ],
        "nouns": [
            "inbox",
            "content calendar",
            "client outreach",
            "codebase",
            "bookkeeping",
            "research workflow",
            "hiring pipeline",
            "meeting notes",
        ],
        "topics": ["AI workflow experiment", "AI tool trial", "automation test"],
        "cta": "Comment which workflow I should hand over next.",
        "narrative": {
            "name": "7-day AI takeover experiments",
            "format_pattern": "I let AI run my X for 7 days",
            "summary": (
                "A creator hands one concrete workflow to an AI tool for a fixed period, "
                "films the daily process as screen capture, and closes on a measured "
                "outcome. Adoption is spreading out of AI-native accounts into "
                "productivity and small-business creators."
            ),
            "common_elements": [
                "Fixed time box stated in the first three seconds",
                "One narrow, nameable workflow rather than a vague goal",
                "Day counter overlay carrying the structure",
                "A number, not an adjective, as the payoff",
                "Screen recording doing the demonstration work",
            ],
            "why_it_works": [
                {
                    "principle": "curiosity_gap",
                    "title": "The outcome is withheld by design",
                    "detail": (
                        "The hook announces the experiment but never the verdict, so the only "
                        "way to resolve it is to stay. The time box makes the open loop feel "
                        "finite and therefore worth waiting out."
                    ),
                },
                {
                    "principle": "concrete_promise",
                    "title": "One workflow, one week, one number",
                    "detail": (
                        "Naming a specific workflow makes the claim checkable, which is what "
                        "separates this from generic AI commentary. Viewers can map it onto "
                        "their own job in the first two seconds."
                    ),
                },
                {
                    "principle": "process_transparency",
                    "title": "The middle is the proof",
                    "detail": (
                        "Screen capture of the actual failures makes the ending credible. It "
                        "also supplies natural mid-video structure, which holds attention past "
                        "the ten-second drop-off where most experiment videos lose viewers."
                    ),
                },
                {
                    "principle": "topic_portable",
                    "title": "Nothing depends on the original subject",
                    "detail": (
                        "The skeleton survives any swap of workflow or industry, which is why "
                        "it is appearing simultaneously in AI, bookkeeping and recruiting "
                        "accounts rather than saturating one niche."
                    ),
                },
            ],
            "format_structure": [
                {
                    "start": 0,
                    "end": 3,
                    "label": "Hook",
                    "detail": "State the experiment and the time box. No greeting, no intro.",
                },
                {
                    "start": 3,
                    "end": 9,
                    "label": "Premise",
                    "detail": "Name the exact workflow and why handing it over is risky.",
                },
                {
                    "start": 9,
                    "end": 26,
                    "label": "Daily process",
                    "detail": "Screen capture across days, with at least one visible failure.",
                },
                {
                    "start": 26,
                    "end": 34,
                    "label": "Result",
                    "detail": "Show the measured outcome on screen as a number.",
                },
                {
                    "start": 34,
                    "end": 38,
                    "label": "Verdict + CTA",
                    "detail": "One-line judgement, then invite the next experiment.",
                },
            ],
        },
    },
    {
        "key": "screen_tutorial_30s",
        "phase": "growing",
        "videos": 24,
        "creators": 17,
        "platforms": ["tiktok", "youtube", "instagram"],
        "niches": ["ai", "technology", "productivity", "design"],
        "countries": ["US", "CA", "GB", "BR"],
        "languages": ["en", "en", "en", "pt"],
        "content_type": "tutorial",
        "duration": (24, 38),
        "base_views": (36_000, 640_000),
        "engagement": (0.068, 0.115),
        "difficulty": "low",
        "analysis": {
            "content_format": "30-second AI screen-recording tutorial",
            "narrative_structure": ["hook", "problem", "demonstration", "result", "cta"],
            "speaking_style": "fast confident voiceover, no on-camera presence",
            "visual_style": "full-screen app capture with cursor highlights and zoom",
            "editing_patterns": [
                "zoom on every cursor click",
                "cut on each screen state change",
                "keyboard shortcut overlays",
                "speed ramp through loading states",
            ],
            "caption_style": "burned-in captions plus keyboard shortcut chips",
            "emotional_tone": "urgency",
            "audio_style": "quiet electronic bed, keyboard click accents",
            "target_audience": "18-30 knowledge workers and builders",
            "production_difficulty": "low",
        },
        "hooks": [
            "You're using {tool} wrong.",
            "Stop typing prompts like this in {tool}.",
            "This {tool} feature replaced my entire {noun}.",
            "{tool} can do this and nobody is using it.",
            "I found the {tool} setting that changes everything.",
            "90% of people miss this in {tool}.",
        ],
        "tools": ["ChatGPT", "Claude", "Notion", "Figma", "Cursor", "Gemini", "Excel", "Canva"],
        "nouns": ["research workflow", "note system", "reporting stack", "design handoff"],
        "topics": ["AI tool tutorial", "workflow shortcut", "hidden feature"],
        "cta": "Save this before you forget the shortcut.",
        "narrative": {
            "name": "30-second AI screen-recording tutorials",
            "format_pattern": "You're using X wrong → here's the correct way",
            "summary": (
                "A single non-obvious capability of a familiar tool, demonstrated end to end "
                "on screen in under 35 seconds with no on-camera presence. The format is "
                "expanding fast from AI accounts into design and general productivity."
            ),
            "common_elements": [
                "Contrarian correction in the opening line",
                "No face cam anywhere in the video",
                "Zoom pushed to ~140% so the UI survives the vertical crop",
                "One capability only — never a feature tour",
                "Save-oriented CTA rather than a follow request",
            ],
            "why_it_works": [
                {
                    "principle": "identity_signal",
                    "title": "The hook accuses the viewer",
                    "detail": (
                        "'You're using it wrong' implicates someone who already uses the tool, "
                        "which is exactly the audience worth keeping. Viewers who disagree "
                        "comment to defend their method, and that argument feeds distribution."
                    ),
                },
                {
                    "principle": "concrete_promise",
                    "title": "One capability, fully shown",
                    "detail": (
                        "Restricting the video to a single feature means the payoff arrives "
                        "inside the runtime. Feature tours fail here because they promise "
                        "breadth the format has no room to deliver."
                    ),
                },
                {
                    "principle": "low_production_cost",
                    "title": "No camera, no lighting, no set",
                    "detail": (
                        "The whole video is a screen recorder and a voice memo. Creators can "
                        "publish several a week, and that repetition is what turns an "
                        "individual hit into a measurable adoption curve."
                    ),
                },
                {
                    "principle": "visible_payoff",
                    "title": "The result is on screen, not narrated",
                    "detail": (
                        "Because the outcome is visible in the same recording as the method, "
                        "viewers verify it themselves. That verification is what converts a "
                        "view into a save."
                    ),
                },
            ],
            "format_structure": [
                {
                    "start": 0,
                    "end": 3,
                    "label": "Hook",
                    "detail": "Contrarian correction naming the tool explicitly.",
                },
                {
                    "start": 3,
                    "end": 9,
                    "label": "Problem",
                    "detail": "Show the slow or wrong way on screen for two seconds.",
                },
                {
                    "start": 9,
                    "end": 24,
                    "label": "Demonstration",
                    "detail": "Perform the correct method, zooming on each click.",
                },
                {
                    "start": 24,
                    "end": 29,
                    "label": "Result",
                    "detail": "Hold on the finished output one beat longer than feels natural.",
                },
                {"start": 29, "end": 32, "label": "CTA", "detail": "Ask for the save, not a follow."},
            ],
        },
    },
    {
        "key": "cost_breakdown_reveal",
        "phase": "emerging",
        "videos": 14,
        "creators": 12,
        "platforms": ["tiktok", "instagram"],
        "niches": ["finance", "business", "travel", "food"],
        "countries": ["US", "GB", "AU", "ES"],
        "languages": ["en", "en", "en", "es"],
        "content_type": "breakdown",
        "duration": (30, 52),
        "base_views": (22_000, 310_000),
        "engagement": (0.081, 0.142),
        "difficulty": "low",
        "analysis": {
            "content_format": "itemised real-cost breakdown reveal",
            "narrative_structure": ["hook", "assumption", "itemised reveal", "true total", "lesson"],
            "speaking_style": "matter-of-fact voiceover, receipts on screen",
            "visual_style": "documents and receipts on a plain surface, top-down",
            "editing_patterns": [
                "running total counter in the corner",
                "cut on each new line item",
                "hold on the final number",
                "hand enters frame to place each item",
            ],
            "caption_style": "line-item labels with prices",
            "emotional_tone": "surprise",
            "audio_style": "no music under the reveal, cash-register accent on the total",
            "target_audience": "25-40 planners and budget-conscious buyers",
            "production_difficulty": "low",
        },
        "hooks": [
            "What {thing} actually costs. Nobody shows you this.",
            "The real price of {thing}, line by line.",
            "I tracked every euro I spent on {thing}.",
            "{thing} cost me 3x what I budgeted. Here's every line.",
            "Everyone lies about what {thing} costs.",
        ],
        "things": [
            "starting a business",
            "a week in Tokyo",
            "opening a coffee shop",
            "moving abroad",
            "running a food truck",
            "a home studio",
        ],
        "topics": ["cost transparency", "budget breakdown", "real spending"],
        "cta": "Tell me what I should price out next.",
        "narrative": {
            "name": "Itemised real-cost breakdowns",
            "format_pattern": "What X actually costs, line by line",
            "summary": (
                "A creator lists every real line item behind something people budget badly "
                "for, revealing a running total on screen. Still small in creator count but "
                "engagement is well above the platform baseline."
            ),
            "common_elements": [
                "Running total visible from the first item",
                "Physical receipts or a spreadsheet on screen",
                "The final number withheld until the last five seconds",
                "No music underneath the reveal",
            ],
            "why_it_works": [
                {
                    "principle": "curiosity_gap",
                    "title": "The total is the whole video",
                    "detail": (
                        "A visible running counter creates a question the viewer answers only "
                        "by reaching the end. Leaving early costs them the number they came for."
                    ),
                },
                {
                    "principle": "identity_signal",
                    "title": "Prices are inherently arguable",
                    "detail": (
                        "Every viewer has a private estimate, and most of them are wrong. The "
                        "comment section fills with corrections and regional comparisons, both "
                        "of which extend distribution well past the first day."
                    ),
                },
                {
                    "principle": "visible_payoff",
                    "title": "Documents beat claims",
                    "detail": (
                        "Showing receipts rather than stating figures removes the credibility "
                        "gap that sinks most finance content, and it is what earns the share."
                    ),
                },
            ],
            "format_structure": [
                {"start": 0, "end": 3, "label": "Hook", "detail": "Name the thing and promise every line."},
                {"start": 3, "end": 10, "label": "Assumption", "detail": "State what people think it costs."},
                {"start": 10, "end": 34, "label": "Itemised reveal", "detail": "One cut per item, counter climbing."},
                {"start": 34, "end": 42, "label": "True total", "detail": "Hold on the final figure in silence."},
                {"start": 42, "end": 46, "label": "Lesson", "detail": "The one line that surprised you most."},
            ],
        },
    },
    {
        "key": "myth_correction",
        "phase": "viral",
        "videos": 48,
        "creators": 42,
        "platforms": ["tiktok", "instagram", "youtube"],
        "niches": ["fitness", "health", "productivity", "finance"],
        "countries": ["US", "GB", "DE", "FR"],
        "languages": ["en", "en", "de", "fr"],
        "content_type": "commentary",
        "duration": (18, 32),
        "base_views": (180_000, 3_400_000),
        "engagement": (0.052, 0.094),
        "difficulty": "low",
        "analysis": {
            "content_format": "corrective myth-busting monologue with proof insert",
            "narrative_structure": ["contrarian hook", "common belief", "correction", "proof", "cta"],
            "speaking_style": "assertive close-up delivery, direct eye contact",
            "visual_style": "tight face cam, single key light, plain background",
            "editing_patterns": [
                "jump cut on every clause",
                "text card for the myth",
                "b-roll or chart insert as proof",
                "hard stop on the final word",
            ],
            "caption_style": "large centred captions with the myth struck through",
            "emotional_tone": "conviction",
            "audio_style": "no music, voice only, room tone",
            "target_audience": "22-40 self-improvement audience",
            "production_difficulty": "low",
        },
        "hooks": [
            "Stop doing {practice}. It's not doing what you think.",
            "{practice} is the most oversold advice in {niche}.",
            "You've been told to {practice}. That's wrong.",
            "Nobody needs to {practice}. Here's what actually matters.",
            "{practice} wastes more time than anything else in {niche}.",
        ],
        "practices": [
            "morning routines",
            "fasted cardio",
            "time blocking",
            "budgeting apps",
            "cold plunges",
            "inbox zero",
            "meal prepping on Sunday",
        ],
        "topics": ["myth correction", "advice teardown", "contrarian take"],
        "cta": "Tell me which one you still believe.",
        "narrative": {
            "name": "Corrective myth-busting monologues",
            "format_pattern": "Stop doing X — here's what actually works",
            "summary": (
                "A tight face-cam monologue that names a widely repeated piece of advice, "
                "rejects it, and substitutes one specific alternative backed by an inserted "
                "proof shot. Already broadly adopted and heavily contested in comments."
            ),
            "common_elements": [
                "Rejection stated before any justification",
                "Exactly one replacement recommendation",
                "A single proof insert — chart, clip or document",
                "No music, so the delivery carries the whole video",
            ],
            "why_it_works": [
                {
                    "principle": "identity_signal",
                    "title": "It forces a position",
                    "detail": (
                        "Naming a practice people publicly follow makes neutrality impossible. "
                        "Agreement and outrage generate the same volume of comments, which is "
                        "why the format survives being wrong."
                    ),
                },
                {
                    "principle": "curiosity_gap",
                    "title": "The replacement is withheld",
                    "detail": (
                        "Rejecting the belief without immediately supplying the alternative "
                        "keeps the loop open through the middle third, which is where "
                        "monologue formats normally lose retention."
                    ),
                },
                {
                    "principle": "low_production_cost",
                    "title": "One take, one light",
                    "detail": (
                        "No location, no b-roll beyond a single insert. Creators can produce "
                        "these daily, which is why the format saturated so quickly."
                    ),
                },
            ],
            "format_structure": [
                {"start": 0, "end": 3, "label": "Contrarian hook", "detail": "Name and reject the practice."},
                {"start": 3, "end": 9, "label": "Common belief", "detail": "State the version people repeat."},
                {"start": 9, "end": 18, "label": "Correction", "detail": "Give the single replacement."},
                {"start": 18, "end": 24, "label": "Proof", "detail": "Cut to the chart, clip or document."},
                {"start": 24, "end": 27, "label": "CTA", "detail": "Invite disagreement explicitly."},
            ],
        },
    },
    {
        "key": "build_in_public_timelapse",
        "phase": "growing",
        "videos": 18,
        "creators": 15,
        "platforms": ["instagram", "tiktok", "youtube"],
        "niches": ["startups", "business", "design", "technology"],
        "countries": ["US", "NL", "SG", "GB"],
        "languages": ["en", "en", "en", "en"],
        "content_type": "vlog",
        "duration": (35, 58),
        "base_views": (28_000, 420_000),
        "engagement": (0.061, 0.104),
        "difficulty": "medium",
        "analysis": {
            "content_format": "silent build-in-public timelapse with text narration",
            "narrative_structure": ["metric card", "silent work", "obstacle", "shipped state", "next target"],
            "speaking_style": "no speech, on-screen text narration only",
            "visual_style": "locked-off desk timelapse, warm practical lighting",
            "editing_patterns": [
                "8-12x speed ramps",
                "text card between segments",
                "revenue or user counter overlay",
                "single ambient track throughout",
            ],
            "caption_style": "narration told entirely through text cards",
            "emotional_tone": "determination",
            "audio_style": "instrumental lo-fi bed, no voiceover",
            "target_audience": "22-35 founders and indie builders",
            "production_difficulty": "medium",
        },
        "hooks": [
            "Day {n} of building {thing} in public.",
            "Month {n}. {thing} made $0 today.",
            "Building {thing} until it makes rent.",
            "Day {n}: {thing} broke in production again.",
            "{thing}, week {n}. Still no users.",
        ],
        "things": [
            "a solo SaaS",
            "an AI notes app",
            "a two-person agency",
            "a marketplace",
            "a Chrome extension",
        ],
        "topics": ["build in public", "founder log", "product progress"],
        "cta": "Follow to see whether this works.",
        "narrative": {
            "name": "Silent build-in-public timelapses",
            "format_pattern": "Day N of building X in public",
            "summary": (
                "No voiceover at all: a locked-off timelapse of real work, narrated entirely "
                "through text cards and a visible metric counter. Growing steadily among "
                "founder accounts on Instagram and TikTok."
            ),
            "common_elements": [
                "Day or week number as the first frame",
                "Zero spoken words in the entire video",
                "A live metric — revenue, users, signups — on screen",
                "At least one visible setback per episode",
            ],
            "why_it_works": [
                {
                    "principle": "process_transparency",
                    "title": "Serialised stakes",
                    "detail": (
                        "The day counter turns individual videos into episodes of one story. "
                        "Viewers return for the number rather than the content, which is what "
                        "produces retention across posts instead of within one."
                    ),
                },
                {
                    "principle": "identity_signal",
                    "title": "Failure is the differentiator",
                    "detail": (
                        "Showing the setback is what separates this from polished founder "
                        "content. Audiences reward the admission because it is rare, and the "
                        "comments become a support thread rather than a debate."
                    ),
                },
                {
                    "principle": "topic_portable",
                    "title": "Works for any visible craft",
                    "detail": (
                        "Nothing depends on software. The same skeleton is already appearing "
                        "in design studios and physical product businesses."
                    ),
                },
            ],
            "format_structure": [
                {"start": 0, "end": 3, "label": "Metric card", "detail": "Day number and the current number."},
                {"start": 3, "end": 22, "label": "Silent work", "detail": "Timelapse at 8-12x, no speech."},
                {"start": 22, "end": 36, "label": "Obstacle", "detail": "Text card naming what broke."},
                {"start": 36, "end": 48, "label": "Shipped state", "detail": "Show the thing working."},
                {"start": 48, "end": 52, "label": "Next target", "detail": "State tomorrow's goal."},
            ],
        },
    },
    {
        "key": "before_after_transformation",
        "phase": "declining",
        "videos": 21,
        "creators": 18,
        "platforms": ["instagram", "tiktok"],
        "niches": ["fitness", "beauty", "design"],
        "countries": ["US", "BR", "GB", "IT"],
        "languages": ["en", "pt", "en", "it"],
        "content_type": "transformation",
        "duration": (15, 26),
        "base_views": (95_000, 1_600_000),
        "engagement": (0.044, 0.071),
        "difficulty": "medium",
        "analysis": {
            "content_format": "before/after transformation reveal on a beat drop",
            "narrative_structure": ["before state", "build-up", "transition", "after reveal"],
            "speaking_style": "no narration, trending audio carries the pacing",
            "visual_style": "matched framing between before and after, same angle",
            "editing_patterns": [
                "transition cut on the beat drop",
                "identical framing across both states",
                "slow push on the after shot",
                "trending audio drives all timing",
            ],
            "caption_style": "single overlay label per state",
            "emotional_tone": "satisfaction",
            "audio_style": "trending audio, transition timed to the drop",
            "target_audience": "18-30 lifestyle and aesthetics audience",
            "production_difficulty": "medium",
        },
        "hooks": [
            "{n} months of {practice}. Same lighting, same angle.",
            "Before and after {n} weeks of {practice}.",
            "{practice} for {n} months changed this completely.",
            "Same room, {n} months apart.",
        ],
        "practices": [
            "consistent training",
            "a skincare routine",
            "one room renovation",
            "learning to cut hair",
            "rebuilding a workspace",
        ],
        "topics": ["transformation", "progress reveal", "before after"],
        "cta": "Ask me anything about the process.",
        "narrative": {
            "name": "Beat-drop before/after reveals",
            "format_pattern": "N months of X — same angle, same light",
            "summary": (
                "A matched-framing before/after cut precisely on a trending audio drop. Reach "
                "per video is still high but creator adoption has been falling for two weeks — "
                "the format is past its peak."
            ),
            "common_elements": [
                "Identical camera position in both states",
                "Transition locked to the audio drop",
                "No spoken narration",
                "Duration under 25 seconds",
            ],
            "why_it_works": [
                {
                    "principle": "visible_payoff",
                    "title": "The payoff is instant and non-verbal",
                    "detail": (
                        "Matched framing lets the viewer measure the change without any "
                        "explanation, which is why it travels across languages. It also means "
                        "the video works with sound off."
                    ),
                },
                {
                    "principle": "low_production_cost",
                    "title": "Two shots and a cut",
                    "detail": (
                        "The entire edit is one transition. The cost sits in the months of "
                        "elapsed time, not the production — which is also why the format is "
                        "now saturating: the supply of finished transformations is finite."
                    ),
                },
            ],
            "format_structure": [
                {"start": 0, "end": 4, "label": "Before state", "detail": "Hold the starting frame, labelled."},
                {"start": 4, "end": 11, "label": "Build-up", "detail": "Short process glimpses on the beat."},
                {"start": 11, "end": 13, "label": "Transition", "detail": "Cut exactly on the drop."},
                {"start": 13, "end": 20, "label": "After reveal", "detail": "Same angle, slow push in."},
            ],
        },
    },
    {
        "key": "rapid_listicle",
        "phase": "emerging",
        "videos": 13,
        "creators": 11,
        "platforms": ["youtube", "tiktok"],
        "niches": ["education", "finance", "business", "productivity"],
        "countries": ["US", "IN", "GB", "PL"],
        "languages": ["en", "en", "en", "pl"],
        "content_type": "listicle",
        "duration": (33, 50),
        "base_views": (19_000, 240_000),
        "engagement": (0.075, 0.121),
        "difficulty": "low",
        "analysis": {
            "content_format": "rapid-fire numbered listicle with per-item proof",
            "narrative_structure": ["hook", "item one", "item two", "item three", "payoff"],
            "speaking_style": "brisk voiceover, one sentence per item",
            "visual_style": "face cam with full-frame graphic cutaways per item",
            "editing_patterns": [
                "numbered corner counter",
                "cutaway graphic on each item",
                "no pause between items",
                "final item held twice as long",
            ],
            "caption_style": "numbered captions matching the counter",
            "emotional_tone": "urgency",
            "audio_style": "percussive bed with a hit on each number",
            "target_audience": "20-35 learners and early-career professionals",
            "production_difficulty": "low",
        },
        "hooks": [
            "3 things I wish I knew before {action}.",
            "3 {noun} mistakes that cost me two years.",
            "3 rules I'd give anyone starting {action}.",
            "The 3 {noun} decisions that actually mattered.",
        ],
        "actions": [
            "starting a business",
            "learning to code",
            "investing",
            "going freelance",
            "managing a team",
        ],
        "nouns": ["career", "money", "hiring", "learning"],
        "topics": ["lessons learned", "advice list", "mistakes to avoid"],
        "cta": "Which one hit hardest?",
        "narrative": {
            "name": "Three-item proof listicles",
            "format_pattern": "3 things I wish I knew before X",
            "summary": (
                "Strictly three items, each with its own visual proof cutaway and no pause "
                "between them. Small but climbing, with engagement well above the platform "
                "baseline for education content."
            ),
            "common_elements": [
                "Exactly three items, never five or ten",
                "A visual cutaway per item rather than a talking head throughout",
                "No transitional filler between items",
                "The last item held noticeably longer",
            ],
            "why_it_works": [
                {
                    "principle": "concrete_promise",
                    "title": "Three is a completable promise",
                    "detail": (
                        "A viewer can estimate the remaining runtime from the first frame and "
                        "decide it is affordable. Ten-item lists fail at exactly this step."
                    ),
                },
                {
                    "principle": "visible_payoff",
                    "title": "Each item pays out on its own",
                    "detail": (
                        "The per-item cutaway means the video delivers value three times "
                        "instead of once at the end, which flattens the mid-video drop-off."
                    ),
                },
                {
                    "principle": "topic_portable",
                    "title": "The counter is the format",
                    "detail": (
                        "Nothing about the structure is subject-specific, which is why it is "
                        "surfacing simultaneously in finance, coding and management accounts."
                    ),
                },
            ],
            "format_structure": [
                {"start": 0, "end": 3, "label": "Hook", "detail": "State the number and the context."},
                {"start": 3, "end": 15, "label": "Item one", "detail": "Claim, then cutaway proof."},
                {"start": 15, "end": 27, "label": "Item two", "detail": "Claim, then cutaway proof."},
                {"start": 27, "end": 40, "label": "Item three", "detail": "The strongest item, held longest."},
                {"start": 40, "end": 44, "label": "Payoff", "detail": "Tie the three together in one line."},
            ],
        },
    },
    {
        "key": "honest_day_in_life",
        "phase": "growing",
        "videos": 16,
        "creators": 14,
        "platforms": ["tiktok", "instagram"],
        "niches": ["lifestyle", "startups", "education", "health"],
        "countries": ["US", "GB", "ES", "MX"],
        "languages": ["en", "en", "es", "es"],
        "content_type": "vlog",
        "duration": (40, 62),
        "base_views": (31_000, 480_000),
        "engagement": (0.066, 0.109),
        "difficulty": "medium",
        "analysis": {
            "content_format": "anti-aesthetic honest day-in-the-life with a timestamped log",
            "narrative_structure": ["timestamp hook", "unglamorous block", "low point", "small win", "reflection"],
            "speaking_style": "unscripted voice memo narration over handheld footage",
            "visual_style": "deliberately rough handheld, natural light, no colour grade",
            "editing_patterns": [
                "on-screen clock stamp per segment",
                "no transitions, straight cuts only",
                "ambient audio kept in",
                "one long unbroken take at the low point",
            ],
            "caption_style": "timestamps as the only overlay",
            "emotional_tone": "honesty",
            "audio_style": "diegetic ambient sound, music only at the end",
            "target_audience": "20-32 viewers tired of polished routine content",
            "production_difficulty": "medium",
        },
        "hooks": [
            "5:40am. Not the aesthetic version of {role} life.",
            "A real day as a {role}. No filter, no edit.",
            "This is what being a {role} actually looks like.",
            "The unedited version of a {role} day.",
        ],
        "roles": ["founder", "nurse", "teacher", "freelancer", "PhD student", "chef"],
        "topics": ["honest routine", "unfiltered day", "reality check"],
        "cta": "Tell me if this matches your day.",
        "narrative": {
            "name": "Anti-aesthetic honest day logs",
            "format_pattern": "A real day as a X — no filter",
            "summary": (
                "A deliberate rejection of polished routine content: timestamped, ungraded, "
                "ambient-sound handheld footage including at least one genuine low point. "
                "Spreading from lifestyle into professional niches."
            ),
            "common_elements": [
                "Visible clock timestamp on every segment",
                "No colour grading and no transitions",
                "One unbroken take at the hardest moment",
                "Music withheld until the final ten seconds",
            ],
            "why_it_works": [
                {
                    "principle": "identity_signal",
                    "title": "It positions against a genre",
                    "detail": (
                        "The format defines itself in opposition to aesthetic morning-routine "
                        "content, which hands it a ready-made audience that already resents "
                        "the thing it rejects."
                    ),
                },
                {
                    "principle": "process_transparency",
                    "title": "The low point is mandatory",
                    "detail": (
                        "Keeping the worst moment uncut is what makes the rest believable. "
                        "Removing it collapses the format back into ordinary vlogging."
                    ),
                },
                {
                    "principle": "low_production_cost",
                    "title": "Polish is a liability here",
                    "detail": (
                        "Rough footage is the point, so production effort is near zero and the "
                        "usual barrier to daily posting disappears."
                    ),
                },
            ],
            "format_structure": [
                {"start": 0, "end": 4, "label": "Timestamp hook", "detail": "Clock on screen, state the role."},
                {"start": 4, "end": 20, "label": "Unglamorous block", "detail": "The boring necessary work."},
                {"start": 20, "end": 36, "label": "Low point", "detail": "One unbroken take, no cuts."},
                {"start": 36, "end": 48, "label": "Small win", "detail": "Something modest that went right."},
                {"start": 48, "end": 55, "label": "Reflection", "detail": "One honest line, music enters."},
            ],
        },
    },
]

BY_KEY = {a["key"]: a for a in ARCHETYPES}
