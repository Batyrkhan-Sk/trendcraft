# TrendCraft

Trend intelligence for short-form video.

TrendCraft collects TikToks and Shorts (in the future Instagram Reels wil be added), uses AI to understand what each
video actually *is*, clusters them into reusable **content formats**, scores which
formats are genuinely emerging, explains *why* they work, and turns the winners
into scripts and shot-by-shot recording plans adapted to one creator's niche.

The distinction the whole product rests on:

> Not "this video got 10M views" — but "30-second AI screen-recording tutorials
> are up 71% this week and being picked up by creators across productivity,
> technology and design."

---

## Deploy

- Link to the platform: https://trendcraft-bk.duckdns.org/

---

## Quick start

```bash
cp .env.example .env          # optional: add GOOGLE_API_KEY
docker compose up -d --build
docker compose exec api python -m seed.seed --reset
```

| Service | URL |
|---|---|
| Web app | http://localhost:3010 |
| API docs | http://localhost:8010/docs |
| Postgres | `localhost:5435` (`trendcraft` / `trendcraft`) |

Ports are non-standard on purpose to avoid colliding with other local stacks;
change them in `docker-compose.yml` if you like.

**It runs with no API keys at all.** Every AI call has a deterministic local
fallback, so the pipeline, the scores and the whole UI work offline. Adding a
Gemini key upgrades quality; it is not required to see the product.

---

## The workflow it demonstrates

```
pick a niche → engine surfaces emerging formats → AI explains why one works
            → "Recreate" → scenario adapted to your niche
            → shot-by-shot recording guide + storyboard
```

Every step is live in the app: `/discover` → a trend page → `/recreate`.

---

## Architecture

```
 ┌──────────────┐   connectors    ┌───────────────┐   Gemini vision
 │ TikTok / IG  │ ──────────────▶ │  normalise    │ ──────────────▶ AI extraction
 │ YouTube      │                 │  (RawVideo)   │                 (hook, format,
 └──────────────┘                 └───────────────┘                  structure, …)
                                                                            │
                                                                            ▼
     dashboard ◀── scoring ◀── aggregation ◀── clustering ◀──────── embeddings
                      │                       (agglomerative,       (gemini-embedding-001
                      │                        cosine)               or local hashing)
                      ▼
              scenario + recording-guide generation
```

| Layer | Choice |
|---|---|
| Frontend | Next.js 16 (App Router), TypeScript, Tailwind v4 |
| Backend | FastAPI, SQLAlchemy 2.0, Pydantic v2 |
| Database | PostgreSQL 16 + pgvector |
| Queue | Redis + Celery (worker + beat) |
| AI | Gemini — generation, native video understanding, embeddings |

### Repository layout

```
backend/
  app/
    connectors/   platform adapters (YouTube is fully functional)
    ai/           Gemini client, prompts, response schemas, embeddings
    services/     scoring · clustering · extraction · narrative · generation
    pipeline/     end-to-end orchestration
    workers/      Celery tasks and schedule
    api/v1/       REST endpoints
  seed/           realistic corpus + archetype definitions
frontend/
  src/app/        routes (dashboard, discover, trend, recreate, scenarios, …)
  src/components/ ui primitives, charts, trend and scenario components
```

---

## The trend engine

### Why not rank by views

Total views measure a creator's audience, not a format's momentum. Every signal
here is normalised — by time (velocity), by the creator's own baseline (lift), or
by the previous window (growth).

**Trend score** — nine weighted signals (`app/services/scoring.py`):

| Signal | Weight | What it captures |
|---|---|---|
| Growth rate | 0.20 | 7-day change in creators adopting the format |
| View velocity | 0.16 | Median views/hour, log-scaled |
| Creator-normalised lift | 0.15 | Views ÷ that creator's own median |
| Engagement rate | 0.13 | Normalised against a per-platform baseline |
| Creator adoption | 0.11 | Distinct creators, log-scaled |
| Share & comment activity | 0.09 | Weighted toward shares and saves |
| Cross-platform presence | 0.06 | Platforms the format appears on |
| Recency | 0.06 | Exponential decay, 96h half-life |
| Historical consistency | 0.04 | Inverse spread of per-video lift |

**Creator-normalised lift** is the signal that makes the product work. A 40k-view
video from a creator who averages 5k is stronger evidence than a 2M-view video
from a creator who always gets 2M.

**Opportunity score (0–100)** re-weights toward actionability: growth,
engagement, *low* competition, recency, cross-platform reach, adaptability, and
ease of production — then discounts declining formats by 35%.

Both scores are returned with a full component breakdown, and the UI renders it:
every number on a trend page can be traced to the signals that produced it.

### Lifecycle status

Classified from measured quantities rather than from the composite score — a
weighted average of squashed signals lives in a narrow band, so any absolute
cut-off on it would be arbitrary.

- **Declining** — adoption falling (checked first: a format holds high reach for
  days after it has turned over)
- **Viral** — large reach *and* wide adoption; growth may have flattened
- **Emerging** — fewer than 15 creators; too small a base for its growth rate to
  be treated as a trajectory
- **Growing** — meaningful base and accelerating

### Clustering

Agglomerative, average linkage, cosine distance. A distance threshold answers a
question we can actually answer ("how similar must two videos be to count as the
same format") rather than k-means' unanswerable one ("how many formats exist this
week"). Clusters below `MIN_CLUSTER_SIZE` are discarded — one creator doing
something unusual is not a trend.

Embeddings are built from *structural* fields (format, narrative beats, editing,
hook) rather than captions, weighted so two videos on unrelated subjects shot the
same way land close together.

---

## Data sources

| Platform | Status | Needs |
|---|---|---|
| **YouTube** | Fully implemented | `YOUTUBE_API_KEY` (falls back to `GOOGLE_API_KEY`) |
| TikTok | Adapter ready | `TIKTOK_PROVIDER_URL` — a dataset vendor |
| Instagram | Adapter ready | `INSTAGRAM_PROVIDER_URL` — a dataset vendor |

Neither TikTok nor Instagram offers a public discovery API: TikTok's Research API
is limited to approved academic institutions, and the Instagram Graph API only
reaches accounts you own. Both connectors therefore talk to a configurable HTTP
endpoint with a documented request/response envelope — point them at Apify,
Bright Data, Ensemble or similar. See `backend/app/connectors/social.py`.

Adding a platform means writing one module that yields `RawVideo` and calling
`register()`. Nothing downstream knows which platform a video came from.

```bash
# Run a real collection once a key is present
curl -X POST localhost:8010/api/v1/pipeline/run \
  -H 'Content-Type: application/json' \
  -d '{"platforms":["youtube"],"niches":["ai","productivity"],"async_run":false}'
```

---

## The seeded corpus

`seed/seed.py` generates 180 videos across 8 hand-authored format archetypes,
then runs **the production clustering, scoring and classification code** over
them. Nothing on the dashboard is a hard-coded ranking — change an archetype and
the scores and statuses move with it. The last run recovered all 8 archetypes at
100% cluster purity.

**These videos are synthetic.** Handles, URLs and metrics are generated. The
corpus exists so the engine can be exercised without credentials — it is not
retrieved content. Point a connector at a real API to replace it.

Hand-written trend narratives in `seed/archetypes.py` are used *only* when no
Gemini key is configured; with a key, the model writes them.

---

## AI configuration

One key covers all three AI roles:

```bash
GOOGLE_API_KEY=...            # https://aistudio.google.com/apikey
LLM_MODEL=gemini-3.6-flash    # trend narration, scenarios, recording guides
VISION_MODEL=gemini-3.6-flash # native video understanding
EMBEDDING_MODEL=gemini-embedding-001
```

**Video analysis degrades in three tiers** so the pipeline never hard-fails:

1. **Native video** — Gemini watches the actual file (YouTube URLs are ingested
   server-side without a download). Only this tier can honestly report editing
   rhythm, framing and delivery.
2. **Metadata-only** — caption, hashtags, duration. Recovers topic and rough
   format; explicitly instructed not to fabricate visual detail.
3. **Heuristic** — keyword rules, no network. Flagged `is_fallback` so the UI can
   mark it and a later pass can upgrade it.

Clustering and scoring never call a model, so they are unaffected by key
availability.

---

## Background jobs

Different stages run at different cadences (`app/workers/celery_app.py`):

| Task | Schedule | Why |
|---|---|---|
| `collect` | every 3h | Platform data doesn't move faster; respects YouTube's 10k/day quota |
| `analyze` | every 10 min | Queue drain — the slow, expensive stage runs continuously in small batches |
| `refresh_metrics` | hourly | Re-reads counters so velocity is a measurement, not a lifetime average |
| `rebuild_trends` | nightly | Cluster boundaries only need to be right once a day |

---

## Development

```bash
# Backend
cd backend && pip install -e ".[dev]"
uvicorn app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev     # :3010

# Reseed
docker compose exec api python -m seed.seed --reset
```

Tuning knobs (`.env`): `MIN_CLUSTER_SIZE`, `CLUSTER_SIMILARITY_THRESHOLD`,
`TREND_HALF_LIFE_HOURS`. Changing `EMBEDDING_DIM` requires a `--reset`, since the
pgvector column dimension is fixed at table creation.

---

## Known limits

- **Competition thresholds are fitted to a small corpus.** The midpoints in
  `classify_competition` ("20 creators is average adoption") reflect a single
  slice and need re-fitting against production-scale data. They are named
  constants for exactly that reason.
- **JSON array filtering** uses a text-containment check, which is fine at this
  table size but should become a `jsonb` operator past a few hundred thousand
  rows.
- **No auth.** Identity is a request header; `get_current_user` is the single
  function to replace.
- **Thumbnails** are absent for seeded videos, so cards fall back to a
  typographic panel — platform CDNs expire thumbnail URLs aggressively, and a
  grid of broken images reads as a bug rather than as missing data.
