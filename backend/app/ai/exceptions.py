"""
Custom exceptions for the AI module.
"""


class AIError(Exception):
    """
    Base exception for all AI-related errors.
    """

    pass


class AIConnectionError(AIError):
    """
    Raised when the AI provider cannot be reached.
    """

    pass


class AIResponseError(AIError):
    """
    Raised when the AI returns an invalid or unexpected response.
    """

    pass


class AIParsingError(AIError):
    """
    Raised when the AI response cannot be parsed into valid JSON.
    """

    pass


class AIRateLimitError(AIError):
    """
    Raised when the AI provider rate limit is exceeded.
    """

    pass


class AINoAvailableKeyError(AIError):
    """
    Raised when all configured API keys have been exhausted.
    """

    pass


class ResumeValidationError(AIError):
    """
    Raised when the uploaded document is not a valid resume.
    """
    pass


class AIAuthenticationError(AIResponseError):
    """Raised when authentication with the AI provider fails."""
    pass


class AIModelNotFoundError(AIResponseError):
    """Raised when the requested AI model is unavailable."""

    pass