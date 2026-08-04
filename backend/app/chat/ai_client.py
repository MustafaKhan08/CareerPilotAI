"""
OpenRouter client for the AI Career Mentor.

This module is responsible only for communicating with
the OpenRouter Chat Completions API.

No business logic should exist here.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


# ==========================================================
# Exceptions
# ==========================================================


class ChatClientError(Exception):
    """Base exception for all AI client errors."""


class ChatClientConfigurationError(ChatClientError):
    """Raised when OpenRouter configuration is invalid."""


class ChatClientTimeoutError(ChatClientError):
    """Raised when an OpenRouter request times out."""


class ChatClientConnectionError(ChatClientError):
    """Raised when OpenRouter cannot be reached."""


class ChatClientHTTPError(ChatClientError):
    """Raised when OpenRouter returns an HTTP error."""


class ChatClientResponseError(ChatClientError):
    """Raised when the API response is malformed."""


class ChatClientEmptyResponseError(ChatClientError):
    """Raised when the assistant returns an empty response."""


# ==========================================================
# AI Client
# ==========================================================


class ChatAIClient:
    """
    Low-level asynchronous OpenRouter client.

    Responsibilities:

    - Build HTTP requests
    - Send requests
    - Parse responses
    - Handle networking errors

    This class MUST NOT contain any application
    business logic.
    """

    def __init__(self) -> None:
        """Initialize the reusable HTTP client."""

        self._validate_config()

        timeout = httpx.Timeout(
            connect=settings.ai_connect_timeout,
            read=settings.ai_timeout,
            write=settings.ai_write_timeout,
            pool=settings.ai_pool_timeout,
        )

        limits = httpx.Limits(
            max_connections=settings.ai_max_connections,
            max_keepalive_connections=settings.ai_max_keepalive,
        )

        self._client = httpx.AsyncClient(
            base_url=settings.openrouter_base_url.rstrip("/"),
            timeout=timeout,
            limits=limits,
            http2=True,
            follow_redirects=True,
        )

    async def close(self) -> None:
        """
        Close the underlying HTTP client.
        Should be called during FastAPI shutdown.
        """
        await self._client.aclose()

    async def generate_chat_response(
        self,
        messages: list[dict[str, str]],
    ) -> str:
        """
        Generate an assistant response from OpenRouter.
        Args:
            messages:
                OpenAI-compatible chat messages.
        Returns:
            Assistant response text.
        Raises:
            ChatClientTimeoutError
            ChatClientConnectionError
            ChatClientHTTPError
            ChatClientResponseError
            ChatClientEmptyResponseError
        """
        self._validate_messages(messages)
        logger.info(
            "Sending request to OpenRouter."
        )
        try:
            response = await self._client.post(
                "/chat/completions",
                headers=self._build_headers(),
                json=self._build_payload(messages),
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            logger.exception(
                "OpenRouter request timed out."
            )
            raise ChatClientTimeoutError(
                "OpenRouter request timed out."
            ) from exc
        except httpx.HTTPStatusError as exc:
            logger.exception(
                "OpenRouter returned HTTP %s.",
                exc.response.status_code,
            )
            raise ChatClientHTTPError(
                f"OpenRouter returned HTTP "
                f"{exc.response.status_code}: "
                f"{exc.response.text}"
            ) from exc
        except httpx.RequestError as exc:
            logger.exception(
                "Unable to connect to OpenRouter."
            )
            raise ChatClientConnectionError(
                "Unable to connect to OpenRouter."
            ) from exc
        assistant_response = (
            self._extract_assistant_response(
                response=response,
            )
        )
        logger.info(
            "OpenRouter request completed successfully."
        )
        return assistant_response

    def _build_headers(
        self,
    ) -> dict[str, str]:
        """
        Build OpenRouter HTTP headers.
        """

        headers = {
            "Authorization": (
                f"Bearer "
                f"{settings.openrouter_api_keys[0]}"
            ),
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": settings.user_agent,
        }

        if settings.openrouter_site_url:
            headers["HTTP-Referer"] = (
                settings.openrouter_site_url
            )

        if settings.openrouter_site_name:
            headers["X-Title"] = (
                settings.openrouter_site_name
            )

        return headers

    def _build_payload(
        self,
        messages: list[dict[str, str]],
    ) -> dict[str, Any]:
        """
        Build the OpenRouter request payload.
        """

        return {
            "model": settings.ai_models[0],
            "messages": messages,
            "temperature": settings.ai_temperature,
            "max_tokens": settings.ai_max_tokens,
        }

    def _extract_assistant_response(
        self,
        response: httpx.Response,
    ) -> str:
        """
        Extract assistant text from
        an OpenRouter response.
        """

        try:
            payload = response.json()
            logger.error("OpenRouter Response: %s", payload)

        except ValueError as exc:
            raise ChatClientResponseError(
                "OpenRouter returned invalid JSON."
            ) from exc

        if not isinstance(payload, dict):
            raise ChatClientResponseError(
                "Response must be a JSON object."
            )

        choices = payload.get("choices")

        if (
            not isinstance(choices, list)
            or not choices
        ):
            raise ChatClientResponseError(
                "Missing choices."
            )

        message = choices[0].get("message")

        if not isinstance(message, dict):
            raise ChatClientResponseError(
                "Missing assistant message."
            )

        content = message.get("content")

        if not isinstance(content, str):
            raise ChatClientResponseError(
                "Assistant response must be text."
            )

        if not content.strip():
            raise ChatClientEmptyResponseError(
                "Assistant returned an empty response."
            )

        return content.strip()

    def _validate_config(self) -> None:
        """
        Validate the required OpenRouter configuration.
        """

        if not settings.openrouter_base_url:
            raise ChatClientConfigurationError(
                "OpenRouter base URL is not configured."
            )

        if (
            not settings.openrouter_api_keys
            or not settings.openrouter_api_keys[0].strip()
        ):
            raise ChatClientConfigurationError(
                "No OpenRouter API key is configured."
            )

        if (
            not settings.ai_models
            or not settings.ai_models[0].strip()
        ):
            raise ChatClientConfigurationError(
                "No OpenRouter model is configured."
            )

    def _validate_messages(
        self,
        messages: list[dict[str, str]],
    ) -> None:
        """
        Validate chat messages before sending them
        to OpenRouter.
        """

        if not isinstance(messages, list):
            raise ChatClientResponseError(
                "Messages must be a list."
            )

        if not messages:
            raise ChatClientResponseError(
                "Messages cannot be empty."
            )

        for message in messages:

            if not isinstance(message, dict):
                raise ChatClientResponseError(
                    "Each message must be a dictionary."
                )

            role = message.get("role")
            content = message.get("content")

            if (
                not isinstance(role, str)
                or not role.strip()
            ):
                raise ChatClientResponseError(
                    "Every message must include a valid role."
                )

            if (
                not isinstance(content, str)
                or not content.strip()
            ):
                raise ChatClientResponseError(
                    "Every message must include valid content."
                )


# ==========================================================
# Singleton Client
# ==========================================================

_chat_client = ChatAIClient()


async def generate_chat_response(
    messages: list[dict[str, str]],
) -> str:
    """
    Generate an assistant response using the
    shared OpenRouter client.

    This is the public function that should be
    used throughout the application.
    """

    return await _chat_client.generate_chat_response(
        messages=messages,
    )


async def close_chat_client() -> None:
    """
    Close the shared HTTP client.

    Should be called during FastAPI shutdown.
    """

    await _chat_client.close()