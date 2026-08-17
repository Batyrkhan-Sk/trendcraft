"""Verify the configured API keys actually work, before spending a pipeline run.

    docker compose exec api python -m scripts.check_keys

Checks each key with the cheapest possible real call, so a typo or a missing
API-enablement surfaces here rather than as an empty dashboard forty minutes
later. Exits non-zero if anything a run depends on is broken.
"""

from __future__ import annotations

import os
import sys

from app.core.config import settings

OK = "\033[32m✓\033[0m"
BAD = "\033[31m✗\033[0m"
WARN = "\033[33m!\033[0m"


def check_gemini_text() -> bool:
    if not settings.google_api_key:
        print(f"{WARN} Gemini        GOOGLE_API_KEY not set — AI falls back to local implementations")
        return True  # Not fatal: the pipeline still runs.
    try:
        from google import genai

        client = genai.Client(api_key=settings.google_api_key)
        resp = client.models.generate_content(
            model=settings.llm_fast_model,
            contents="Reply with the single word: ok",
            config={"max_output_tokens": 2000, "temperature": 0},
        )
        print(f"{OK} Gemini text   {settings.llm_fast_model} → {(resp.text or '').strip()[:20]!r}")
        return True
    except Exception as exc:
        print(f"{BAD} Gemini text   {type(exc).__name__}: {str(exc)[:140]}")
        return False


def check_gemini_embeddings() -> bool:
    if not settings.google_api_key:
        return True
    try:
        from google import genai

        client = genai.Client(api_key=settings.google_api_key)
        result = client.models.embed_content(
            model=settings.embedding_model,
            contents=["trend clustering smoke test"],
            config={
                "task_type": "SEMANTIC_SIMILARITY",
                "output_dimensionality": settings.embedding_dim,
            },
        )
        dim = len(result.embeddings[0].values)
        if dim != settings.embedding_dim:
            print(f"{BAD} Embeddings    returned {dim} dims, DB column expects {settings.embedding_dim}")
            return False
        print(f"{OK} Embeddings    {settings.embedding_model} → {dim} dims")
        return True
    except Exception as exc:
        print(f"{BAD} Embeddings    {type(exc).__name__}: {str(exc)[:140]}")
        return False


def check_gemini_video() -> bool:
    """Confirm the vision model accepts a YouTube URL directly."""
    if not settings.google_api_key:
        return True
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.google_api_key)
        resp = client.models.generate_content(
            model=settings.vision_model,
            contents=[
                types.Part.from_uri(
                    file_uri="https://www.youtube.com/watch?v=aqz-KE-bpKQ", mime_type="video/*"
                ),
                "In three words, what is shown?",
            ],
            config={"max_output_tokens": 2000, "temperature": 0},
        )
        print(f"{OK} Video input   {settings.vision_model} → {(resp.text or '').strip()[:40]!r}")
        return True
    except Exception as exc:
        # Non-fatal: extraction degrades to the metadata-only tier.
        print(f"{WARN} Video input   unavailable, will use metadata-only tier — {str(exc)[:100]}")
        return True


def check_youtube() -> bool:
    key = os.getenv("YOUTUBE_API_KEY") or settings.google_api_key
    if not key:
        print(f"{BAD} YouTube       no YOUTUBE_API_KEY or GOOGLE_API_KEY set")
        return False
    try:
        import httpx

        resp = httpx.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                "key": key,
                "part": "snippet",
                "type": "video",
                "q": "ai tutorial",
                "maxResults": 1,
            },
            timeout=20.0,
        )
        if resp.status_code == 403:
            reason = resp.json().get("error", {}).get("errors", [{}])[0].get("reason", "")
            hint = {
                "accessNotConfigured": "enable 'YouTube Data API v3' on this key's Cloud project",
                "quotaExceeded": "daily quota exhausted — resets at midnight Pacific",
                "forbidden": "key restrictions may be blocking this API",
            }.get(reason, "check key restrictions")
            print(f"{BAD} YouTube       403 {reason} — {hint}")
            return False
        resp.raise_for_status()
        items = resp.json().get("items", [])
        which = "YOUTUBE_API_KEY" if os.getenv("YOUTUBE_API_KEY") else "GOOGLE_API_KEY (fallback)"
        print(f"{OK} YouTube       {which} → {len(items)} result(s), quota cost 100 units")
        return True
    except Exception as exc:
        print(f"{BAD} YouTube       {type(exc).__name__}: {str(exc)[:140]}")
        return False


def check_apify() -> bool:
    """Validate the Apify token and confirm the configured actors exist.

    Deliberately does not start an actor run — that would cost credits just to
    answer "is this token valid".
    """
    token = os.getenv("APIFY_TOKEN")
    if not token:
        print(f"{WARN} Apify         APIFY_TOKEN not set — TikTok/Instagram will be skipped")
        return True
    try:
        import httpx

        from app.connectors.apify import DEFAULT_INSTAGRAM_ACTOR, DEFAULT_TIKTOK_ACTOR

        me = httpx.get(
            "https://api.apify.com/v2/users/me", params={"token": token}, timeout=20.0
        )
        if me.status_code == 401:
            print(f"{BAD} Apify         token rejected (401)")
            return False
        me.raise_for_status()
        user = me.json().get("data", {})
        plan = (user.get("plan") or {}).get("id", "unknown")
        print(f"{OK} Apify         user {user.get('username', '?')} · plan {plan}")

        ok = True
        for env, default in (
            ("APIFY_TIKTOK_ACTOR", DEFAULT_TIKTOK_ACTOR),
            ("APIFY_INSTAGRAM_ACTOR", DEFAULT_INSTAGRAM_ACTOR),
        ):
            actor = os.getenv(env) or default
            resp = httpx.get(
                f"https://api.apify.com/v2/acts/{actor}", params={"token": token}, timeout=20.0
            )
            if resp.status_code == 200:
                name = resp.json().get("data", {}).get("name", actor)
                print(f"{OK} Apify actor   {actor} → {name}")
            else:
                print(f"{BAD} Apify actor   {actor} unreachable ({resp.status_code})")
                ok = False
        return ok
    except Exception as exc:
        print(f"{BAD} Apify         {type(exc).__name__}: {str(exc)[:140]}")
        return False


def main() -> int:
    print("\nChecking configured providers…\n")
    results = [
        check_gemini_text(),
        check_gemini_embeddings(),
        check_gemini_video(),
        check_youtube(),
        check_apify(),
    ]
    ok = all(results)
    print()
    if ok:
        print("All good. Run a live collection with:\n")
        print("  curl -X POST localhost:8010/api/v1/pipeline/run \\")
        print("    -H 'Content-Type: application/json' \\")
        print('    -d \'{"platforms":["youtube"],"niches":["ai","productivity"],'
              '"async_run":false}\'\n')
    else:
        print("Fix the ✗ items above before running a collection.\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
