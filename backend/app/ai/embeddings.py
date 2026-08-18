"""Embedding providers used for trend clustering.

Two implementations behind one function:

``gemini`` – hosted semantic embeddings (``gemini-embedding-001``). The default.
             Handles paraphrase and multilingual content properly, which matters
             because the same format shows up in several languages at once.
             Truncated to ``embedding_dim`` via Matryoshka output dimensionality
             and re-normalised, as Google recommends for dims below 3072.
``local``   – deterministic feature hashing over word unigrams + bigrams with
             sublinear term frequency and L2 normalisation. No network, no model
             download, stable across runs. Used automatically whenever the API
             key is missing or a request fails, so clustering never hard-stops.

Both return unit-length vectors of ``settings.embedding_dim`` so cosine similarity
is just a dot product.
"""

from __future__ import annotations

import hashlib
import logging
import math
import re
from collections import Counter

import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)

_TOKEN_RE = re.compile(r"[a-z0-9']+")

# Words that carry no format signal — dropped so clusters key on structure.
_STOPWORDS = frozenset(
    # fmt: off
    [
        "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has",
        "have", "how", "i", "in", "is", "it", "its", "of", "on", "or", "that",
        "the", "this", "to", "was", "were", "will", "with", "you", "your", "my",
        "me", "we", "our", "they", "their", "he", "she", "them", "not", "but",
        "if", "so", "than", "then", "there", "here", "just", "really", "very",
        "can", "could", "would", "should", "do", "does", "did", "about",
    ]
    # fmt: on
)


def tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOPWORDS and len(t) > 1]


def _bucket(term: str, dim: int) -> tuple[int, float]:
    """Hash a term to an index plus a sign, the standard hashing-trick pair."""
    digest = hashlib.blake2b(term.encode("utf-8"), digest_size=8).digest()
    value = int.from_bytes(digest, "big")
    return value % dim, 1.0 if (value >> 63) & 1 else -1.0


def embed_local(text: str, dim: int | None = None) -> list[float]:
    dim = dim or settings.embedding_dim
    vec = np.zeros(dim, dtype=np.float32)
    tokens = tokenize(text)
    if not tokens:
        return vec.tolist()

    terms = Counter(tokens)
    # Bigrams capture phrasing ("7 days", "screen recording") that unigrams lose.
    terms.update(f"{a}_{b}" for a, b in zip(tokens, tokens[1:]))

    for term, count in terms.items():
        idx, sign = _bucket(term, dim)
        vec[idx] += sign * (1.0 + math.log(count))

    norm = float(np.linalg.norm(vec))
    return (vec / norm).tolist() if norm else vec.tolist()


def _normalize(vector: list[float]) -> list[float]:
    arr = np.asarray(vector, dtype=np.float32)
    norm = float(np.linalg.norm(arr))
    return (arr / norm).tolist() if norm else arr.tolist()


def _embed_gemini(texts: list[str], task_type: str) -> list[list[float]] | None:
    """Batch-embed via Gemini. Returns ``None`` on any failure so callers fall back."""
    try:
        from google import genai

        client = genai.Client(api_key=settings.google_api_key)
        result = client.models.embed_content(
            model=settings.embedding_model,
            contents=texts,
            config={
                "task_type": task_type,
                "output_dimensionality": settings.embedding_dim,
            },
        )
        # Sub-3072 outputs are truncated Matryoshka vectors and arrive un-normalised.
        return [_normalize(e.values) for e in result.embeddings]
    except Exception as exc:
        logger.warning("Gemini embedding failed, using local encoder: %s", exc)
        return None


def embed(text: str, task_type: str = "SEMANTIC_SIMILARITY") -> list[float]:
    return embed_many([text], task_type)[0]


def embed_many(
    texts: list[str], task_type: str = "SEMANTIC_SIMILARITY", batch_size: int = 100
) -> list[list[float]]:
    if settings.embedding_provider == "gemini" and settings.google_api_key:
        out: list[list[float]] = []
        for start in range(0, len(texts), batch_size):
            chunk = texts[start : start + batch_size]
            vectors = _embed_gemini(chunk, task_type)
            if vectors is None:
                return [embed_local(t) for t in texts]
            out.extend(vectors)
        return out
    return [embed_local(t) for t in texts]


def cosine(a: list[float] | np.ndarray, b: list[float] | np.ndarray) -> float:
    va, vb = np.asarray(a, dtype=np.float32), np.asarray(b, dtype=np.float32)
    na, nb = float(np.linalg.norm(va)), float(np.linalg.norm(vb))
    if not na or not nb:
        return 0.0
    return float(np.dot(va, vb) / (na * nb))


#: Placeholders the heuristic tier emits when it cannot observe a field.
_UNINFORMATIVE = {"", "unknown", "none", "platform default", "original audio"}


def _useful(value: str | None) -> str:
    return "" if not value or str(value).strip().lower() in _UNINFORMATIVE else str(value)


def format_signature(analysis: dict, caption: str = "", hashtags: list | None = None) -> str:
    """Build the text that gets embedded for one video.

    Normally weighted toward *structural* fields — format, narrative beats,
    editing — so two videos on unrelated subjects shot the same way land close
    together. Topic appears once, structure several times.

    That inverts when the analysis came from the heuristic tier. Heuristics pick
    a ``content_format`` from a handful of keyword rules and leave most other
    fields as "unknown", so every video's signature becomes nearly identical and
    the whole corpus collapses into one cluster regardless of threshold.

    When the structural fields carry no information, fall back to the caption and
    hashtags. That clusters closer to *topic* than to format, which is a real
    downgrade — but a topic-clustered corpus is far more useful than a single
    undifferentiated blob, and the fallback disappears as soon as the LLM tier
    can run.
    """
    structure = [str(s) for s in (analysis.get("narrative_structure") or [])]
    editing = [str(e) for e in (analysis.get("editing_patterns") or [])]

    content_format = _useful(analysis.get("content_format"))
    visual = _useful(analysis.get("visual_style"))
    speaking = _useful(analysis.get("speaking_style"))
    tone = _useful(analysis.get("emotional_tone"))

    # Structural signal is present only if the extractor actually observed craft
    # details, not just matched a caption keyword.
    has_structure = bool(visual or speaking or editing)

    if has_structure:
        parts = [
            content_format, content_format,
            " ".join(structure), " ".join(structure),
            _useful(analysis.get("hook")),
            visual, speaking, " ".join(editing), tone,
            _useful(analysis.get("main_message")),
            _useful(analysis.get("topic")),
        ]
    else:
        tags = " ".join(str(h).lstrip("#") for h in (hashtags or []))
        parts = [
            _useful(analysis.get("hook")),
            _useful(analysis.get("main_message")),
            caption[:400],
            tags, tags,
            _useful(analysis.get("topic")),
            content_format,
        ]

    return " ".join(p for p in parts if p)
