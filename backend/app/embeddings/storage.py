"""
Embedding Storage
=================

Persistence layer for semantic search embeddings.

Responsibilities:
- Save/load embedding matrices
- Save/load job ID mappings
- Save/load metadata
- Validate embedding index integrity

This module contains no embedding generation or similarity logic.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

from app.embeddings.config import (
    EXPECTED_EMBEDDING_DIMENSION,
    FALLBACK_EMBEDDINGS_PATH,
    FALLBACK_METADATA_PATH,
    JOB_IDS_PATH,
    PRIMARY_EMBEDDINGS_PATH,
    PRIMARY_METADATA_PATH,
)

logger = logging.getLogger(__name__)


class EmbeddingStorage:
    """
    Handles persistence of embedding indexes and metadata.
    """

    @staticmethod
    def save_embeddings(
        embeddings: np.ndarray,
        *,
        primary: bool = True,
    ) -> Path:
        """
        Save an embedding matrix to disk.
        """

        path = (
            PRIMARY_EMBEDDINGS_PATH
            if primary
            else FALLBACK_EMBEDDINGS_PATH
        )

        np.save(path, embeddings)

        logger.info(
            "Saved %d embeddings to %s",
            embeddings.shape[0],
            path,
        )

        return path

    @staticmethod
    def load_embeddings(
        *,
        primary: bool = True,
    ) -> np.ndarray:
        """
        Load an embedding matrix from disk.
        """

        path = (
            PRIMARY_EMBEDDINGS_PATH
            if primary
            else FALLBACK_EMBEDDINGS_PATH
        )

        if not path.exists():
            raise FileNotFoundError(
                f"Embedding file not found: {path}"
            )

        embeddings = np.load(path)

        EmbeddingStorage.validate_embeddings(
            embeddings
        )

        return embeddings

    @staticmethod
    def save_job_ids(
        job_ids: np.ndarray,
    ) -> Path:
        """
        Save ordered job IDs.
        """

        np.save(JOB_IDS_PATH, job_ids)

        logger.info(
            "Saved %d job IDs.",
            len(job_ids),
        )

        return JOB_IDS_PATH

    @staticmethod
    def load_job_ids() -> np.ndarray:
        """
        Load ordered job IDs.
        """

        if not JOB_IDS_PATH.exists():
            raise FileNotFoundError(
                f"Job ID file not found: {JOB_IDS_PATH}"
            )

        return np.load(JOB_IDS_PATH)

    @staticmethod
    def save_metadata(
        metadata: dict[str, Any],
        *,
        primary: bool = True,
    ) -> Path:
        """
        Save metadata JSON.
        """

        path = (
            PRIMARY_METADATA_PATH
            if primary
            else FALLBACK_METADATA_PATH
        )

        with open(
            path,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                metadata,
                file,
                indent=4,
                ensure_ascii=False,
            )

        logger.info(
            "Saved metadata to %s",
            path,
        )

        return path

    @staticmethod
    def load_metadata(
        *,
        primary: bool = True,
    ) -> dict[str, Any]:
        """
        Load metadata JSON.
        """

        path = (
            PRIMARY_METADATA_PATH
            if primary
            else FALLBACK_METADATA_PATH
        )

        if not path.exists():
            raise FileNotFoundError(
                f"Metadata file not found: {path}"
            )

        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    @staticmethod
    def validate_embeddings(
        embeddings: np.ndarray,
    ) -> None:
        """
        Validate an embedding matrix.
        """

        if not isinstance(
            embeddings,
            np.ndarray,
        ):
            raise TypeError(
                "Embeddings must be a NumPy array."
            )

        if embeddings.ndim != 2:
            raise ValueError(
                "Embeddings must be a 2D array."
            )

        if embeddings.shape[1] != EXPECTED_EMBEDDING_DIMENSION:
            raise ValueError(
                f"Expected embedding dimension "
                f"{EXPECTED_EMBEDDING_DIMENSION}, "
                f"got {embeddings.shape[1]}."
            )

        if not np.isfinite(
            embeddings
        ).all():
            raise ValueError(
                "Embeddings contain invalid values."
            )

    @staticmethod
    def validate_index() -> None:
        """
        Validate that embeddings and job IDs match.
        """

        embeddings = (
            EmbeddingStorage.load_embeddings()
        )

        job_ids = (
            EmbeddingStorage.load_job_ids()
        )

        if len(embeddings) != len(job_ids):
            raise ValueError(
                "Embedding count does not match job ID count."
            )

        logger.info(
            "Embedding index validation successful."
        )