"""Re-narrate existing trends with the LLM, without re-clustering.

    docker compose exec api python -m scripts.narrate_trends --limit 8

Clustering and scoring are deterministic and never call a model, so they are
already correct. Only the *narrative* layer — name, pattern, summary, why-it-works,
timed structure — benefits from the LLM. Separating them means a constrained model
quota can be spent on the trends that matter rather than on a full rebuild.

Processes highest-opportunity trends first, and stops cleanly the moment the daily
quota is exhausted rather than burning the remainder on failing calls.
"""

from __future__ import annotations

import argparse
import sys

from sqlalchemy import select

from app.ai import client as llm
from app.db.session import SessionLocal
from app.models import Trend, TrendVideo, Video, VideoAnalysis
from app.services import narrative


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=8, help="How many trends to narrate")
    parser.add_argument("--min-videos", type=int, default=4)
    # The daily quota is per model, so a second model is a second budget.
    parser.add_argument("--model", default=None, help="Override the narration model")
    args = parser.parse_args()

    if not llm.available():
        print("No GOOGLE_API_KEY configured — nothing to do.")
        return 1
    if args.model:
        llm.settings.llm_model = args.model

    with SessionLocal() as db:
        trends = db.scalars(
            select(Trend)
            .where(Trend.video_count >= args.min_videos)
            .order_by(Trend.opportunity_score.desc())
            .limit(args.limit)
        ).all()

        print(f"Narrating {len(trends)} trends with {llm.settings.llm_model}\n")
        done = 0

        for trend in trends:
            rows = db.execute(
                select(Video, VideoAnalysis)
                .join(TrendVideo, TrendVideo.video_id == Video.id)
                .join(VideoAnalysis, VideoAnalysis.video_id == Video.id)
                .where(TrendVideo.trend_id == trend.id)
                .order_by(TrendVideo.similarity.desc())
                .limit(12)
            ).all()
            if not rows:
                continue

            analyses = [
                {
                    "hook": a.hook,
                    "topic": a.topic,
                    "content_format": a.content_format,
                    "narrative_structure": a.narrative_structure,
                    "visual_style": a.visual_style,
                    "editing_patterns": a.editing_patterns,
                    "emotional_tone": a.emotional_tone,
                    "main_message": a.main_message,
                    "duration_sec": v.duration_sec,
                    # Captions carry most of the signal when the corpus was
                    # extracted heuristically rather than from the video itself.
                    "caption": (v.caption or "")[:300],
                }
                for v, a in rows
            ]
            stats = {
                **(trend.score_breakdown or {}).get("inputs", {}),
                "median_duration_sec": trend.median_duration_sec,
                "niches": trend.niches,
                "platforms": trend.platforms,
                "production_difficulty": trend.production_difficulty,
            }

            before = trend.name
            story = narrative.describe_cluster(analyses, stats)

            if story.get("_model") == "deterministic":
                print(f"  ✗ quota exhausted at trend {done + 1} — stopping cleanly")
                break

            trend.name = story["name"]
            trend.format_pattern = story.get("format_pattern")
            trend.summary = story.get("summary", "")
            trend.common_elements = story.get("common_elements", [])
            trend.why_it_works = story.get("why_it_works", [])
            trend.format_structure = story.get("format_structure", [])
            db.commit()
            done += 1
            print(f"  ✓ {before[:34]:<34} → {trend.name}")

        print(f"\nNarrated {done} of {len(trends)}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
