"""Gemini wrapper that always returns structured JSON.

Design notes
------------
* Structured output uses Gemini's native ``response_schema`` + JSON mime type,
  which constrains decoding rather than merely asking for JSON in prose.
* If ``GOOGLE_API_KEY`` is absent the call raises :class:`LLMUnavailable` and
  every caller falls back to a deterministic local implementation. The whole
  pipeline therefore runs end to end offline — useful for demos, tests and CI.
* ``response_schema`` accepts a subset of OpenAPI schema. Keep schemas to
  object/array/string/number/boolean with ``enum`` and ``required``; ``$ref``,
  ``anyOf`` unions and ``additionalProperties`` are not supported.
"""

from __future__ import annotations

import json
import logging
import random
import time
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

#: Transient server-side conditions. 503 "high demand" is common on the newest
#: flash models and resolves within seconds — without a retry these fall through
#: to the deterministic fallback, which silently degrades output quality on a
#: fault that would have cleared on its own.
_RETRYABLE = ("429", "500", "502", "503", "504", "UNAVAILABLE", "RESOURCE_EXHAUSTED")

#: Markers of a quota that resets on a daily boundary rather than a short window.
#: Retrying these just burns wall-clock time — they cannot clear within a request.
_EXHAUSTED_FOR_THE_DAY = ("PerDay", "per day", "GenerateRequestsPerDay")


class LLMUnavailable(RuntimeError):
    pass


class DailyQuotaExhausted(LLMUnavailable):
    """The model's per-day request allowance is gone; it will not recover today."""


#: Models known to have hit their daily cap in this process. A circuit breaker:
#: once a model is in here, further calls fail instantly instead of spending
#: seconds discovering the same thing. Without this, a batch of N videos issues
#: N doomed requests per tier — which is how a day's quota gets consumed
#: producing nothing but fallbacks.
_EXHAUSTED_TODAY: set[str] = set()


def is_exhausted(model: str) -> bool:
    return model in _EXHAUSTED_TODAY


def mark_exhausted(model: str) -> None:
    if model not in _EXHAUSTED_TODAY:
        logger.warning("Daily quota exhausted for %s — skipping it for this run", model)
        _EXHAUSTED_TODAY.add(model)


def reset_exhausted() -> None:
    """Clear the breaker, e.g. for a long-running worker crossing midnight UTC."""
    _EXHAUSTED_TODAY.clear()


def is_daily_quota_error(exc: Exception) -> bool:
    text = str(exc)
    return "RESOURCE_EXHAUSTED" in text and any(
        marker in text for marker in _EXHAUSTED_FOR_THE_DAY
    )


def _is_retryable(exc: Exception) -> bool:
    text = str(exc)
    if any(marker in text for marker in _EXHAUSTED_FOR_THE_DAY):
        return False
    return any(code in text for code in _RETRYABLE)


_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client
    if not settings.google_api_key:
        raise LLMUnavailable("GOOGLE_API_KEY is not configured")
    try:
        from google import genai
    except ImportError as exc:  # pragma: no cover
        raise LLMUnavailable("google-genai package not installed") from exc
    _client = genai.Client(api_key=settings.google_api_key)
    return _client


def available() -> bool:
    return bool(settings.google_api_key)


def structured(
    *,
    system: str,
    prompt: str,
    schema: dict[str, Any],
    model: str | None = None,
    max_tokens: int = 8192,
    temperature: float = 0.6,
    attempts: int = 4,
) -> dict[str, Any]:
    """Run one Gemini turn and return an object matching ``schema``.

    Retries transient server errors with exponential backoff and jitter. Schema
    and auth errors are not retried — they will fail identically every time.
    """
    client = _get_client()
    chosen = model or settings.llm_model
    if is_exhausted(chosen):
        raise DailyQuotaExhausted(f"{chosen} hit its daily cap earlier in this run")
    last_error: Exception | None = None

    for attempt in range(attempts):
        try:
            resp = client.models.generate_content(
                model=chosen,
                contents=prompt,
                config={
                    "system_instruction": system,
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                    "response_mime_type": "application/json",
                    "response_schema": schema,
                },
            )
        except Exception as exc:
            last_error = exc
            if is_daily_quota_error(exc):
                mark_exhausted(chosen)
                raise DailyQuotaExhausted(str(exc)[:200]) from exc
            if attempt == attempts - 1 or not _is_retryable(exc):
                raise
            delay = 2**attempt + random.uniform(0, 1)
            logger.info(
                "Gemini %s transient error (attempt %d/%d), retrying in %.1fs: %s",
                chosen, attempt + 1, attempts, delay, str(exc)[:120],
            )
            time.sleep(delay)
            continue

        text = (resp.text or "").strip()
        if not text:
            # Usually a safety block or a truncated response; a retry rarely
            # helps, but one cheap re-roll costs little at this temperature.
            last_error = LLMUnavailable(f"model {chosen} returned an empty response")
            if attempt == attempts - 1:
                raise last_error
            time.sleep(1)
            continue

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise LLMUnavailable(f"model {chosen} returned non-JSON output") from exc
        return parsed if isinstance(parsed, dict) else {"result": parsed}

    raise LLMUnavailable(str(last_error))


def structured_or_none(**kwargs: Any) -> dict[str, Any] | None:
    """Best-effort variant: log and return ``None`` instead of raising."""
    try:
        return structured(**kwargs)
    except LLMUnavailable as exc:
        logger.debug("LLM unavailable: %s", exc)
        return None
    except Exception as exc:  # network, rate limit, safety block
        logger.warning("Gemini call failed, falling back to deterministic path: %s", exc)
        return None


def dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)
