"""Stage 6: group video analyses into content formats.

Agglomerative clustering with average linkage over cosine distance. Chosen over
k-means because the number of live formats is unknown and changes daily — a
distance threshold expresses "how similar must two videos be to count as the same
format", which is a question we can actually answer, unlike "how many formats
exist this week".

Singletons and clusters below ``min_cluster_size`` are discarded: one creator
doing something unusual is not a trend, and reporting it as one is exactly the
failure mode this product exists to avoid.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class Cluster:
    members: list[str]
    #: Per-member cosine similarity to the centroid, same order as ``members``.
    similarities: list[float]
    centroid: list[float]

    @property
    def size(self) -> int:
        return len(self.members)


def _normalize_rows(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


def cluster_embeddings(
    ids: list[str],
    vectors: list[list[float]],
    *,
    threshold: float | None = None,
    min_size: int | None = None,
) -> list[Cluster]:
    """Return clusters ordered largest-first."""
    threshold = threshold if threshold is not None else settings.cluster_similarity_threshold
    min_size = min_size if min_size is not None else settings.min_cluster_size

    if len(ids) < min_size:
        return []

    matrix = _normalize_rows(np.asarray(vectors, dtype=np.float32))
    labels = _fit_labels(matrix, threshold)

    clusters: list[Cluster] = []
    for label in sorted(set(labels)):
        idx = [i for i, lab in enumerate(labels) if lab == label]
        if len(idx) < min_size:
            continue
        subset = matrix[idx]
        centroid = subset.mean(axis=0)
        norm = np.linalg.norm(centroid)
        centroid = centroid / norm if norm else centroid
        sims = (subset @ centroid).tolist()

        # Order members by how prototypical they are — the breakdown page shows the
        # top ones as examples, and a badly-fitting member there reads as a bug.
        order = sorted(range(len(idx)), key=lambda i: -sims[i])
        clusters.append(
            Cluster(
                members=[ids[idx[i]] for i in order],
                similarities=[round(sims[i], 4) for i in order],
                centroid=centroid.tolist(),
            )
        )

    clusters.sort(key=lambda c: -c.size)
    return clusters


def _fit_labels(matrix: np.ndarray, threshold: float) -> list[int]:
    """Agglomerative labels, with a dependency-free fallback."""
    distance_threshold = 1.0 - threshold
    try:
        from sklearn.cluster import AgglomerativeClustering

        model = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=distance_threshold,
            metric="cosine",
            linkage="average",
        )
        return model.fit_predict(matrix).tolist()
    except Exception as exc:
        logger.warning("sklearn clustering unavailable (%s); using greedy fallback", exc)
        return _greedy_labels(matrix, threshold)


def _greedy_labels(matrix: np.ndarray, threshold: float) -> list[int]:
    """Single-pass nearest-centroid assignment.

    Lower quality than agglomerative (order-dependent, no merging) but adequate
    and dependency-free.
    """
    centroids: list[np.ndarray] = []
    counts: list[int] = []
    labels: list[int] = []

    for row in matrix:
        best, best_sim = -1, -1.0
        for i, centroid in enumerate(centroids):
            sim = float(np.dot(row, centroid))
            if sim > best_sim:
                best, best_sim = i, sim
        if best >= 0 and best_sim >= threshold:
            counts[best] += 1
            merged = centroids[best] + (row - centroids[best]) / counts[best]
            norm = np.linalg.norm(merged)
            centroids[best] = merged / norm if norm else merged
            labels.append(best)
        else:
            centroids.append(row.copy())
            counts.append(1)
            labels.append(len(centroids) - 1)
    return labels


def assign_to_existing(
    vector: list[float],
    centroids: dict[str, list[float]],
    *,
    threshold: float | None = None,
) -> tuple[str | None, float]:
    """Match a newly analysed video against known trends.

    Used by the incremental path so freshly ingested videos join existing trends
    without a full re-cluster.
    """
    threshold = threshold if threshold is not None else settings.cluster_similarity_threshold
    if not centroids:
        return None, 0.0

    v = np.asarray(vector, dtype=np.float32)
    norm = np.linalg.norm(v)
    if not norm:
        return None, 0.0
    v = v / norm

    best_id, best_sim = None, -1.0
    for trend_id, centroid in centroids.items():
        c = np.asarray(centroid, dtype=np.float32)
        cn = np.linalg.norm(c)
        if not cn:
            continue
        sim = float(np.dot(v, c / cn))
        if sim > best_sim:
            best_id, best_sim = trend_id, sim

    return (best_id, best_sim) if best_sim >= threshold else (None, max(0.0, best_sim))
