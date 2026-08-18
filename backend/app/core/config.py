from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "TrendCraft API"
    api_v1_prefix: str = "/api/v1"
    environment: str = "development"

    database_url: str = "postgresql+psycopg://trendcraft:trendcraft@localhost:5432/trendcraft"
    redis_url: str = "redis://localhost:6379/0"

    #: Origins allowed to call the API from a browser. Must match the port the
    #: web app is actually served on — client-side Save/Generate/Recreate calls
    #: are cross-origin and get blocked otherwise.
    cors_origins: list[str] = [
        "http://localhost:3010",
        "http://127.0.0.1:3010",
        "http://localhost:3000",
    ]

    # --- AI -----------------------------------------------------------------
    # One key powers both generation and embeddings. When it is absent every AI
    # call falls back to a deterministic local implementation, so the full
    # pipeline still runs offline.
    google_api_key: str | None = None
    llm_model: str = "gemini-3.6-flash"
    llm_fast_model: str = "gemini-3.5-flash"
    #: Vision + transcription pass over the actual video file.
    vision_model: str = "gemini-3.6-flash"

    # Embeddings. "gemini" uses the hosted model; "local" is a deterministic
    # feature-hashing encoder that needs no network.
    embedding_provider: str = "gemini"
    embedding_model: str = "gemini-embedding-001"
    embedding_dim: int = 768

    #: Shared secret guarding the /pipeline/* endpoints. Those routes spend real
    #: money — Gemini calls, YouTube quota, Apify credit — so on any public
    #: deployment they must not be reachable by anyone who finds the URL. Leave
    #: empty for local development and the guard is disabled.
    pipeline_token: str | None = None

    #: Videos analysed concurrently. Native video analysis is ~30s of mostly
    #: waiting on Gemini, so this is the single biggest lever on pipeline
    #: throughput. Raise it until you start seeing 429s from your tier.
    analysis_concurrency: int = 6

    # --- Trend engine tuning ------------------------------------------------
    min_cluster_size: int = 4
    cluster_similarity_threshold: float = 0.62
    trend_half_life_hours: float = 96.0


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
