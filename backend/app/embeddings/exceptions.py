"""
Embedding Exceptions
====================

Custom exception hierarchy for the semantic embedding subsystem.

These exceptions isolate embedding-related failures from the rest
of the application and allow the service layer to respond
appropriately.

The hierarchy mirrors the architecture used by the existing
OpenRouter client.
"""


class EmbeddingError(Exception):
    """
    Base exception for all embedding-related errors.
    """


class EmbeddingConfigurationError(EmbeddingError):
    """
    Raised when the embedding subsystem is improperly configured.

    Examples:
        - Missing API keys
        - Missing model names
        - Invalid endpoint URL
    """


class EmbeddingConnectionError(EmbeddingError):
    """
    Raised when the embedding provider cannot be reached.

    Examples:
        - Network unavailable
        - DNS failure
        - Connection refused
    """


class EmbeddingTimeoutError(EmbeddingConnectionError):
    """
    Raised when an embedding request exceeds the configured timeout.
    """


class EmbeddingAuthenticationError(EmbeddingError):
    """
    Raised when authentication with the provider fails.

    Examples:
        - Invalid API key
        - Expired API key
        - Unauthorized request
    """


class EmbeddingRateLimitError(EmbeddingError):
    """
    Raised when the provider returns HTTP 429.
    """


class EmbeddingProviderUnavailableError(EmbeddingError):
    """
    Raised when every configured provider fails.

    This normally happens after both the primary and
    fallback models have been exhausted.
    """


class EmbeddingResponseError(EmbeddingError):
    """
    Raised when the provider returns an invalid response.

    Examples:
        - Invalid JSON
        - Missing embedding field
        - Malformed payload
    """


class EmbeddingDimensionError(EmbeddingError):
    """
    Raised when the returned embedding dimension does
    not match the expected model dimension.
    """


class EmbeddingValidationError(EmbeddingError):
    """
    Raised when embedding validation fails.

    Examples:
        - Empty embedding
        - NaN values
        - Infinite values
    """


class EmbeddingBatchError(EmbeddingError):
    """
    Raised when batch embedding generation fails.
    """