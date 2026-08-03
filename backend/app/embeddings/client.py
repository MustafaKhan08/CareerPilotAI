"""
NVIDIA Embedding Client
=======================

Handles low-level communication with the NVIDIA Embedding API.

This module intentionally contains no business logic.
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from dataclasses import dataclass
from typing import Any

import httpx
import numpy as np

from app.core.config import settings
from app.embeddings.config import (
    EMBEDDING_BACKOFF_SECONDS,
    EMBEDDING_MAX_RETRIES,
    EMBEDDING_TIMEOUT,
    EXPECTED_EMBEDDING_DIMENSION,
    FALLBACK_EMBEDDING_MODEL,
    NVIDIA_EMBEDDING_API_URL,
    PRIMARY_EMBEDDING_MODEL,
)
from app.embeddings.exceptions import (
    EmbeddingAuthenticationError,
    EmbeddingConfigurationError,
    EmbeddingConnectionError,
    EmbeddingDimensionError,
    EmbeddingError,
    EmbeddingProviderUnavailableError,
    EmbeddingRateLimitError,
    EmbeddingResponseError,
    EmbeddingTimeoutError,
    EmbeddingValidationError,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class EmbeddingProvider:
    """Represent one configured NVIDIA embedding provider."""

    name: str
    api_key: str
    model: str
    index_name: str


class EmbeddingClient:
    """
    Asynchronous client for NVIDIA embedding generation.

    Supports query embeddings, batched passage embeddings, retries,
    primary/fallback provider failover, and response validation.
    """

    def __init__(self) -> None:
        """Initialize persistent HTTP resources for NVIDIA API requests."""

        self._validate_config()

        timeout_config = httpx.Timeout(
            connect=EMBEDDING_TIMEOUT,
            read=EMBEDDING_TIMEOUT,
            write=EMBEDDING_TIMEOUT,
            pool=EMBEDDING_TIMEOUT,
        )

        limits_config = httpx.Limits(
            max_keepalive_connections=settings.ai_max_keepalive,
            max_connections=settings.ai_max_connections,
        )

        self._client = httpx.AsyncClient(
            timeout=timeout_config,
            limits=limits_config,
            http2=True,
        )

        self._providers: tuple[EmbeddingProvider, ...] = (
            EmbeddingProvider(
                name="primary",
                api_key=settings.nvidia_primary_api_key,
                model=PRIMARY_EMBEDDING_MODEL,
                index_name="primary",
            ),
            EmbeddingProvider(
                name="fallback",
                api_key=settings.nvidia_fallback_api_key,
                model=FALLBACK_EMBEDDING_MODEL,
                index_name="fallback",
            ),
        )

    async def close(self) -> None:
        """Gracefully close the underlying HTTP client session."""

        await self._client.aclose()

    async def embed_query(
        self,
        text: str,
    ) -> np.ndarray:
        """
        Generate an embedding for a search query.

        Args:
            text: Resume or search-query text.

        Returns:
            A one-dimensional NumPy embedding array.
        """

        self._validate_text(text)

        embeddings = await self._embed(
            texts=[text],
            input_type="query",
        )

        return embeddings[0]

    async def embed_passages(
        self,
        texts: list[str],
    ) -> np.ndarray:
        """
        Generate batched embeddings for searchable passages.

        Args:
            texts: Job or document texts to embed.

        Returns:
            A two-dimensional NumPy embedding array.
        """

        self._validate_texts(texts)

        return await self._embed(
            texts=texts,
            input_type="passage",
        )

    async def _embed(
        self,
        texts: list[str],
        input_type: str,
    ) -> np.ndarray:
        """Generate embeddings using the primary provider, then fallback."""

        last_error: EmbeddingError | None = None

        for provider_index, provider in enumerate(self._providers):
            try:
                return await self._try_provider(
                    provider=provider,
                    texts=texts,
                    input_type=input_type,
                )

            except EmbeddingError as exc:
                last_error = exc

                logger.warning(
                    "Embedding provider %s failed for model %s: %s",
                    provider.name,
                    provider.model,
                    exc,
                )

                if provider_index < len(self._providers) - 1:
                    logger.info(
                        "Failing over from provider %s to provider %s.",
                        provider.name,
                        self._providers[provider_index + 1].name,
                    )

        logger.error("All embedding providers failed.")

        raise EmbeddingProviderUnavailableError(
            "Failed to generate embeddings with all configured providers."
        ) from last_error

    async def _try_provider(
        self,
        provider: EmbeddingProvider,
        texts: list[str],
        input_type: str,
    ) -> np.ndarray:
        """Attempt an embedding request with exponential backoff retries."""

        for attempt in range(1, EMBEDDING_MAX_RETRIES + 1):
            if attempt > 1:
                delay = EMBEDDING_BACKOFF_SECONDS * (
                    2 ** (attempt - 2)
                )
                delay += random.uniform(0, 0.5)

                logger.info(
                    "Waiting %0.2fs before retry attempt %d/%d for "
                    "provider %s and model %s.",
                    delay,
                    attempt,
                    EMBEDDING_MAX_RETRIES,
                    provider.name,
                    provider.model,
                )

                await asyncio.sleep(delay)

            try:
                return await self._send_request(
                    provider=provider,
                    texts=texts,
                    input_type=input_type,
                    attempt=attempt,
                )

            except EmbeddingAuthenticationError:
                logger.warning(
                    "Authentication failed for provider %s and model %s.",
                    provider.name,
                    provider.model,
                )
                raise

            except (
                EmbeddingConnectionError,
                EmbeddingRateLimitError,
                EmbeddingResponseError,
                EmbeddingTimeoutError,
            ) as exc:
                if attempt == EMBEDDING_MAX_RETRIES:
                    logger.error(
                        "Final attempt %d/%d failed for provider %s "
                        "and model %s: %s",
                        attempt,
                        EMBEDDING_MAX_RETRIES,
                        provider.name,
                        provider.model,
                        exc,
                    )
                    raise

                logger.warning(
                    "Attempt %d/%d failed for provider %s and model %s: %s",
                    attempt,
                    EMBEDDING_MAX_RETRIES,
                    provider.name,
                    provider.model,
                    exc,
                )

        raise EmbeddingProviderUnavailableError(
            f"Retries exhausted for provider {provider.name}."
        )

    async def _send_request(
        self,
        provider: EmbeddingProvider,
        texts: list[str],
        input_type: str,
        attempt: int,
    ) -> np.ndarray:
        """Send one batched request to NVIDIA's embeddings endpoint."""

        headers = self._build_headers(
            api_key=provider.api_key,
        )
        payload = self._build_payload(
            texts=texts,
            model=provider.model,
            input_type=input_type,
        )

        logger.info(
            "Sending embedding request | Provider: %s | Attempt: %d | "
            "Model: %s | Batch Size: %d",
            provider.name,
            attempt,
            provider.model,
            len(texts),
        )

        started_at = time.perf_counter()

        try:
            response = await self._client.post(
                url=NVIDIA_EMBEDDING_API_URL,
                headers=headers,
                json=payload,
            )

        except httpx.TimeoutException as exc:
            logger.error(
                "Embedding request timed out | Provider: %s | Attempt: %d | "
                "Model: %s",
                provider.name,
                attempt,
                provider.model,
            )
            raise EmbeddingTimeoutError(
                "Request to NVIDIA Embedding API timed out."
            ) from exc

        except httpx.RequestError as exc:
            logger.error(
                "Embedding network error | Provider: %s | Attempt: %d | "
                "Model: %s | Error: %s",
                provider.name,
                attempt,
                provider.model,
                exc,
            )
            raise EmbeddingConnectionError(
                f"Network failure: {exc}"
            ) from exc

        elapsed = time.perf_counter() - started_at

        return self._handle_response(
            response=response,
            provider_name=provider.name,
            model=provider.model,
            attempt=attempt,
            expected_count=len(texts),
            elapsed=elapsed,
        )

    def _build_headers(
        self,
        api_key: str,
    ) -> dict[str, str]:
        """Construct authorization and content headers for NVIDIA."""

        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": settings.user_agent,
        }

    def _build_payload(
        self,
        texts: list[str],
        model: str,
        input_type: str,
    ) -> dict[str, Any]:
        """Construct an OpenAI-compatible NVIDIA embeddings payload."""

        return {
            "input": texts,
            "model": model,
            "input_type": input_type,
            "encoding_format": "float",
        }

    def _handle_response(
        self,
        response: httpx.Response,
        provider_name: str,
        model: str,
        attempt: int,
        expected_count: int,
        elapsed: float,
    ) -> np.ndarray:
        """Validate an NVIDIA response and return its embedding matrix."""

        response_status = response.status_code

        logger.info(
            "Embedding response received | Status: %d | Provider: %s | "
            "Attempt: %d | Model: %s | Elapsed: %.3fs",
            response_status,
            provider_name,
            attempt,
            model,
            elapsed,
        )

        if response_status == 200:
            return self._parse_embeddings(
                response=response,
                expected_count=expected_count,
                model=model,
            )

        if response_status in (401, 403):
            raise EmbeddingAuthenticationError(
                f"Authentication failure ({response_status})."
            )

        if response_status == 429:
            raise EmbeddingRateLimitError(
                "NVIDIA Embedding API rate limit exceeded."
            )

        if response_status == 408:
            raise EmbeddingTimeoutError(
                "NVIDIA Embedding API request timed out."
            )

        if response_status in (500, 502, 503, 504):
            raise EmbeddingConnectionError(
                f"NVIDIA Embedding API service error ({response_status})."
            )

        raise EmbeddingResponseError(
            f"Unexpected status code from NVIDIA Embedding API: "
            f"{response_status}"
        )

    def _parse_embeddings(
        self,
        response: httpx.Response,
        expected_count: int,
        model: str,
    ) -> np.ndarray:
        """Parse and validate all embeddings returned by NVIDIA."""

        try:
            payload = response.json()
        except ValueError as exc:
            raise EmbeddingResponseError(
                "Invalid JSON received from NVIDIA Embedding API."
            ) from exc

        if not isinstance(payload, dict):
            raise EmbeddingResponseError(
                "Expected a JSON object from NVIDIA Embedding API."
            )

        data = payload.get("data")

        if not isinstance(data, list) or not data:
            raise EmbeddingResponseError(
                "NVIDIA Embedding API response missing embedding data."
            )

        if len(data) != expected_count:
            raise EmbeddingResponseError(
                "NVIDIA Embedding API returned an unexpected number of "
                "embeddings."
            )

        embeddings = np.empty(
            (
                expected_count,
                EXPECTED_EMBEDDING_DIMENSION,
            ),
            dtype=np.float32,
        )

        returned_indexes: set[int] = set()

        for item in data:
            if not isinstance(item, dict):
                raise EmbeddingResponseError(
                    "NVIDIA Embedding API returned a malformed data item."
                )

            index = item.get("index")
            embedding = item.get("embedding")

            if (
                isinstance(index, bool)
                or not isinstance(index, int)
                or index < 0
                or index >= expected_count
            ):
                raise EmbeddingResponseError(
                    "NVIDIA Embedding API returned an invalid embedding index."
                )

            if index in returned_indexes:
                raise EmbeddingResponseError(
                    "NVIDIA Embedding API returned duplicate embedding indexes."
                )

            embeddings[index] = self._validate_embedding(
                embedding=embedding,
                model=model,
            )

            returned_indexes.add(index)

        if returned_indexes != set(range(expected_count)):
            raise EmbeddingResponseError(
                "NVIDIA Embedding API returned incomplete embedding indexes."
            )

        return embeddings

    def _validate_embedding(
        self,
        embedding: Any,
        model: str,
    ) -> np.ndarray:
        """Validate a single embedding vector from the provider response."""

        if not isinstance(embedding, list) or not embedding:
            raise EmbeddingValidationError(
                "NVIDIA Embedding API returned an empty embedding."
            )

        if any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            for value in embedding
        ):
            raise EmbeddingValidationError(
                "NVIDIA Embedding API returned non-numeric embedding values."
            )

        try:
            vector = np.asarray(
                embedding,
                dtype=np.float32,
            )
        except (TypeError, ValueError) as exc:
            raise EmbeddingValidationError(
                "Failed to convert the embedding to a NumPy array."
            ) from exc

        if vector.ndim != 1:
            raise EmbeddingValidationError(
                "NVIDIA Embedding API returned an invalid embedding shape."
            )

        if vector.size != EXPECTED_EMBEDDING_DIMENSION:
            raise EmbeddingDimensionError(
                f"Model {model} returned embedding dimension {vector.size}; "
                f"expected {EXPECTED_EMBEDDING_DIMENSION}."
            )

        if not np.isfinite(vector).all():
            raise EmbeddingValidationError(
                "NVIDIA Embedding API returned invalid embedding values."
            )

        return vector

    def _validate_config(self) -> None:
        """Validate required embedding client configuration."""

        if not NVIDIA_EMBEDDING_API_URL:
            raise EmbeddingConfigurationError(
                "NVIDIA Embedding API URL is not configured."
            )

        if not PRIMARY_EMBEDDING_MODEL:
            raise EmbeddingConfigurationError(
                "Primary embedding model is not configured."
            )

        if not FALLBACK_EMBEDDING_MODEL:
            raise EmbeddingConfigurationError(
                "Fallback embedding model is not configured."
            )

        if not settings.nvidia_primary_api_key:
            raise EmbeddingConfigurationError(
                "Primary NVIDIA embedding API key is not configured."
            )

        if not settings.nvidia_fallback_api_key:
            raise EmbeddingConfigurationError(
                "Fallback NVIDIA embedding API key is not configured."
            )

        if EMBEDDING_MAX_RETRIES < 1:
            raise EmbeddingConfigurationError(
                "Embedding retry count must be at least one."
            )

        if EMBEDDING_TIMEOUT <= 0:
            raise EmbeddingConfigurationError(
                "Embedding timeout must be greater than zero."
            )

    def _validate_text(
        self,
        text: str,
    ) -> None:
        """Validate text supplied for a single query embedding."""

        if not isinstance(text, str) or not text.strip():
            raise EmbeddingValidationError(
                "Embedding input text must be a non-empty string."
            )

    def _validate_texts(
        self,
        texts: list[str],
    ) -> None:
        """Validate text supplied for batched passage embeddings."""

        if not isinstance(texts, list) or not texts:
            raise EmbeddingValidationError(
                "Embedding passages must be a non-empty list of strings."
            )

        for text in texts:
            self._validate_text(text)