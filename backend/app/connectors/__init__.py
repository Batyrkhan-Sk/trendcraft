"""Connector registry.

Importing this package registers one connector per platform. TikTok and
Instagram have two possible backends, so the choice is made explicitly here
rather than by import order — which would be an invisible, fragile dependency.
"""

import os

from app.connectors import youtube  # noqa: F401  (registers itself)
from app.connectors.apify import ApifyInstagramConnector, ApifyTikTokConnector
from app.connectors.base import (
    NotConfigured,
    PlatformConnector,
    RawCreator,
    RawVideo,
    all_connectors,
    get_connector,
    register,
)
from app.connectors.social import InstagramConnector, TikTokConnector

# Apify wins when its token is present: it is a concrete, working integration,
# whereas the generic provider connectors need an endpoint to be pointed at.
if os.getenv("APIFY_TOKEN"):
    register(ApifyTikTokConnector())
    register(ApifyInstagramConnector())
else:
    register(TikTokConnector())
    register(InstagramConnector())

__all__ = [
    "ApifyInstagramConnector",
    "ApifyTikTokConnector",
    "NotConfigured",
    "PlatformConnector",
    "RawCreator",
    "RawVideo",
    "all_connectors",
    "get_connector",
    "register",
]
