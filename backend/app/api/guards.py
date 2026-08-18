"""Route guards for endpoints that cost money to call."""

from __future__ import annotations

import hmac

from fastapi import Header, HTTPException, status

from app.core.config import settings


def require_pipeline_token(
    x_pipeline_token: str | None = Header(default=None, alias="X-Pipeline-Token"),
) -> None:
    """Gate the pipeline routes behind a shared secret.

    Collection and analysis spend Gemini quota, YouTube quota and Apify credit.
    Without this, anyone who discovers the deployment can drain all three.

    When ``PIPELINE_TOKEN`` is unset the guard is a no-op, so local development
    is unaffected — but any public deployment must set it.
    """
    expected = settings.pipeline_token
    if not expected:
        return

    # Constant-time comparison: a plain == leaks the secret's length and prefix
    # through response timing.
    if not x_pipeline_token or not hmac.compare_digest(x_pipeline_token, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid X-Pipeline-Token header required for pipeline operations",
        )
