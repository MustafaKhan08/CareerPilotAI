"""
Abstract interfaces for the embedding subsystem.

The rest of the application should depend on these interfaces
rather than concrete implementations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class EmbeddingProvider(ABC):
    """
    Base interface for any embedding provider.
    """

    @abstractmethod
    async def embed(
        self,
        text: str,
    ) -> np.ndarray:
        """
        Generate an embedding for a single text.
        """
        raise NotImplementedError

    @abstractmethod
    async def embed_batch(
        self,
        texts: list[str],
    ) -> np.ndarray:
        """
        Generate embeddings for multiple texts.
        """
        raise NotImplementedError


class StorageProvider(ABC):
    """
    Interface for embedding storage.
    """

    @abstractmethod
    def save_embeddings(
        self,
        embeddings: np.ndarray,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def load_embeddings(
        self,
    ) -> np.ndarray:
        raise NotImplementedError


class SimilarityEngine(ABC):
    """
    Interface for semantic similarity search.
    """

    @abstractmethod
    def search(
        self,
        embedding: np.ndarray,
        top_k: int,
    ):
        raise NotImplementedError