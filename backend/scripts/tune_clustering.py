"""Choose CLUSTER_SIMILARITY_THRESHOLD from the corpus instead of guessing.

    docker compose exec api python -m scripts.tune_clustering

The threshold is **embedding-model dependent**, which is easy to miss. The local
hashing encoder produces sparse vectors whose cosine similarities cluster low, so
0.62 separates formats well. Hosted semantic embeddings put almost any two
short-form captions in the 0.7–0.9 band, and the same 0.62 merges the entire
corpus into one cluster.

This prints the actual pairwise similarity distribution and the cluster counts
each candidate threshold would produce, so the value can be picked from evidence.
"""

from __future__ import annotations

import random
import statistics
import sys

import numpy as np
from sqlalchemy import select

from app.core.config import settings
from app.db.session import SessionLocal
from app.models import VideoAnalysis
from app.services import clustering

CANDIDATES = [0.55, 0.62, 0.70, 0.75, 0.80, 0.84, 0.88, 0.92]


def main() -> int:
    with SessionLocal() as db:
        rows = db.scalars(select(VideoAnalysis).where(VideoAnalysis.embedding.isnot(None))).all()

    if len(rows) < 20:
        print(f"Only {len(rows)} embedded analyses — collect more before tuning.")
        return 1

    ids = [r.video_id for r in rows]
    vectors = [list(r.embedding) for r in rows]
    matrix = np.asarray(vectors, dtype=np.float32)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    matrix = matrix / norms

    print(f"\nCorpus: {len(rows)} embedded videos")
    print(f"Provider: {settings.embedding_provider} · dim {settings.embedding_dim}")
    print(f"Current CLUSTER_SIMILARITY_THRESHOLD: {settings.cluster_similarity_threshold}\n")

    # Sample pairs rather than computing the full N^2 matrix.
    rng = random.Random(0)
    sims = []
    for _ in range(min(20000, len(rows) * 40)):
        i, j = rng.randrange(len(rows)), rng.randrange(len(rows))
        if i != j:
            sims.append(float(np.dot(matrix[i], matrix[j])))

    qs = statistics.quantiles(sims, n=100)
    print("Pairwise cosine similarity distribution")
    print(f"  min    {min(sims):.3f}")
    for p in (10, 25, 50, 75, 90, 95, 99):
        print(f"  p{p:<5} {qs[p - 1]:.3f}")
    print(f"  max    {max(sims):.3f}\n")

    print("Clusters produced at each threshold")
    print(f"  {'threshold':<11}{'trends':>8}{'clustered':>11}{'largest':>9}  verdict")
    best = None
    for t in CANDIDATES:
        clusters = clustering.cluster_embeddings(ids, vectors, threshold=t)
        n = len(clusters)
        covered = sum(c.size for c in clusters)
        largest = max((c.size for c in clusters), default=0)
        share = largest / max(1, covered)

        # A single cluster swallowing most of the corpus means the threshold is
        # too permissive; dozens of tiny ones mean it is too strict.
        if n == 0:
            verdict = "nothing clusters"
        elif n == 1 or share > 0.6:
            verdict = "over-merged"
        elif n > len(rows) / 6:
            verdict = "fragmented"
        else:
            verdict = "usable"
            if best is None:
                best = t
        print(f"  {t:<11.2f}{n:>8}{covered:>11}{largest:>9}  {verdict}")

    print()
    if best:
        print(f"Suggested: CLUSTER_SIMILARITY_THRESHOLD={best}")
        print("Set it in .env, then:")
        print("  docker compose restart api worker beat")
        print("  curl -X POST .../api/v1/pipeline/rebuild-trends -H 'X-Pipeline-Token: ...'")
    else:
        print("No candidate produced a usable split. That usually means extraction")
        print("quality is the real problem — heuristic analyses describe most videos")
        print("identically, so no threshold can separate them. Run analysis with the")
        print("LLM tier enabled on a subset and re-check.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
