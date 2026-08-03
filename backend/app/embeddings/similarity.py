"""
Semantic Similarity Engine
==========================

Provides fast vectorized cosine similarity search over the
generated embedding index.

Responsibilities
----------------
- Load embedding index
- Normalize embeddings
- Compute cosine similarity
- Return Top-K matching job IDs

No database logic should exist here.
"""

from __future__ import annotations

import logging

import numpy as np

from app.embeddings.storage import EmbeddingStorage

logger = logging.getLogger(__name__)


class SimilarityEngine:
    """
    Performs semantic retrieval over the embedding index.
    """

    def __init__(self) -> None:

        self._loaded = False

        self.embeddings: np.ndarray | None = None

        self.job_ids: np.ndarray | None = None

        self.normalized_embeddings: np.ndarray | None = None


    def load(self) -> None:
        """
        Load the embedding index into memory.
        """
        if self._loaded:
            return
        logger.info(
            "Loading embedding index..."
        )
        self.embeddings = (
            EmbeddingStorage.load_embeddings()
        )
        self.job_ids = (
            EmbeddingStorage.load_job_ids()
        )
        self.normalized_embeddings = (
            self._normalize(
                self.embeddings
            )
        )
        self._loaded = True
        logger.info(
            "Loaded %d embeddings.",
            len(self.job_ids),
        )
    def unload(self) -> None:
        """
        Release memory used by the index.
        """
        self.embeddings = None
        self.job_ids = None
        self.normalized_embeddings = None
        self._loaded = False
        logger.info(
            "Embedding index unloaded."
        )


    @staticmethod
    def _normalize(
        vectors: np.ndarray,
    ) -> np.ndarray:
        """
        Normalize vectors for cosine similarity.
        """
        norms = np.linalg.norm(
            vectors,
            axis=1,
            keepdims=True,
        )
        norms = np.clip(
            norms,
            1e-12,
            None,
        )
        return vectors / norms


    def search(
        self,
        query_embedding: np.ndarray,
        *,
        top_k: int = 20,
        page: int = 1,
        limit: int = 20,
    ) -> list[dict[str, float | int]]:
        """
        Perform semantic similarity search.

        Parameters
        ----------
        query_embedding:
            A single embedding vector.

        top_k:
            Number of candidates to retrieve before pagination.

        page:
            1-based page number.

        limit:
            Number of results per page.

        Returns
        -------
        List of dictionaries containing:

        - job_id
        - similarity_score
        """

        if page < 1:
            raise ValueError(
                "Page must be >= 1."
            )

        if limit < 1:
            raise ValueError(
                "Limit must be >= 1."
            )

        if not self._loaded:
            self.load()

        if self.normalized_embeddings is None:
            raise RuntimeError(
                "Embedding index is not loaded."
            )

        if self.job_ids is None:
            raise RuntimeError(
                "Job IDs are not loaded."
            )

        if self.embeddings is None:
            raise RuntimeError(
                "Embeddings are not loaded."
            )

        query_embedding = np.asarray(
            query_embedding,
            dtype=np.float32,
        )

        if query_embedding.ndim == 2:
            query_embedding = query_embedding[0]

        if (
            query_embedding.shape[-1]
            != self.embeddings.shape[1]
        ):
            raise ValueError(
                "Query embedding dimension does not "
                "match the loaded embedding index."
            )

        query_embedding = (
            query_embedding
            / max(
                np.linalg.norm(query_embedding),
                1e-12,
            )
        )

        similarities = (
            self.normalized_embeddings
            @ query_embedding
        )

        if len(similarities) == 0:
            return []

        top_k = min(
            top_k,
            len(similarities),
        )

        candidate_indices = np.argpartition(
            similarities,
            -top_k,
        )[-top_k:]

        candidate_scores = similarities[
            candidate_indices
        ]

        sorted_order = np.argsort(
            candidate_scores
        )[::-1]

        sorted_indices = candidate_indices[
            sorted_order
        ]

        start = (page - 1) * limit
        end = start + limit

        paged_indices = sorted_indices[
            start:end
        ]

        results: list[
            dict[str, float | int]
        ] = []

        for index in paged_indices:

            results.append(
                {
                    "job_id": int(
                        self.job_ids[index]
                    ),
                    "similarity_score": float(
                        similarities[index]
                    ),
                }
            )

        return results


# ==========================================================
# Shared Similarity Engine
# ==========================================================

# Single shared instance used throughout the application.
# The embedding index is loaded once during FastAPI startup.
similarity_engine = SimilarityEngine()