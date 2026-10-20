"""
OpenRouter API Client
=====================
Handles low-level communication with the OpenRouter API.
Strictly decoupled from business logic, domain schemas, and user data.
"""

import asyncio
import logging
import random
from typing import Any

import httpx

from app.core.config import settings
from app.ai.exceptions import (
    AIConnectionError,
    AIResponseError,
    AIRateLimitError,
    AINoAvailableKeyError,
    AIAuthenticationError,
    AIModelNotFoundError,
)

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """
    Asynchronous client for interacting with the OpenRouter API.

    Implements connection pooling, exponential backoff, key rotation, and
    model failover to ensure maximum availability and fault tolerance.
    """

    def __init__(self) -> None:
        """
        Initializes the OpenRouterClient with connection pooling and timeouts.
        """
        self.base_url = settings.openrouter_base_url.rstrip("/")
        
        timeout_config = httpx.Timeout(
            connect=settings.ai_connect_timeout,
            read=settings.ai_timeout,
            write=settings.ai_write_timeout,
            pool=settings.ai_pool_timeout,
        )
        limits_config = httpx.Limits(
            max_keepalive_connections=settings.ai_max_keepalive,
            max_connections=settings.ai_max_connections,
        )

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout_config,
            limits=limits_config,
            http2=True,
        )

    async def close(self) -> None:
        """
        Gracefully closes the underlying HTTP client session.
        """
        await self._client.aclose()

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        """
        Sends a chat completion request to OpenRouter using key/model rotation.

        Args:
            messages: List of message objects.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            model: Target model name. Defaults to settings sequence if None.

        Returns:
            Validated raw JSON dictionary response from OpenRouter.

        Raises:
            AINoAvailableKeyError: If configuration is invalid or all retries fail.
        """
        self._validate_config()

        req_temperature = (
            temperature if temperature is not None else settings.ai_temperature
        )
        req_max_tokens = (
            max_tokens if max_tokens is not None else settings.ai_max_tokens
        )
        models_to_try = [model] if model else settings.ai_models

        for key_idx, api_key in enumerate(settings.openrouter_api_keys):
            try:
                return await self._try_api_key(
                    api_key=api_key,
                    key_idx=key_idx,
                    models=models_to_try,
                    messages=messages,
                    temperature=req_temperature,
                    max_tokens=req_max_tokens,
                )
            except AINoAvailableKeyError:
                continue

        logger.error("Exhausted all API keys and models without success.")
        raise AINoAvailableKeyError(
            "Failed to obtain a response after exhausting all API keys and models."
        )

    async def health_check(self) -> bool:
        """
        Performs a lightweight sanity check using the first available key and model.

        Returns:
            True if service responds validly, False otherwise.
        """
        try:
            self._validate_config()
        except AINoAvailableKeyError:
            logger.error("Health check failed: Configuration missing keys or models.")
            return False

        first_key = settings.openrouter_api_keys[0]
        first_model = settings.ai_models[0]
        test_message = [{"role": "user", "content": "ping"}]

        try:
            await self._send_request(
                api_key=first_key,
                key_idx=0,
                model=first_model,
                attempt=1,
                messages=test_message,
                temperature=0.0,
                max_tokens=5,
            )
            return True
        except (AIConnectionError, AIResponseError, AIRateLimitError) as exc:
            logger.error("Health check request failed: %s", exc)
            return False

    async def _try_api_key(
        self,
        api_key: str,
        key_idx: int,
        models: list[str],
        messages: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        """
        Attempts execution across configured models for a single API key.
        """
        for model in models:
            try:
                return await self._try_model(
                    api_key=api_key,
                    key_idx=key_idx,
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except (AIConnectionError, AIResponseError, AIRateLimitError) as exc:
                if isinstance(exc, AIAuthenticationError):
                    logger.warning(
                        "Authentication error on API key index %d. Abandoning key.",
                        key_idx,
                    )
                    break

                logger.warning(
                    "Model %s failed with key index %d: %s. Trying next model.",
                    model,
                    key_idx,
                    exc,
                )
                continue

        raise AINoAvailableKeyError(
            f"API Key Index {key_idx} failed for all attempted models."
        )

    async def _try_model(
        self,
        api_key: str,
        key_idx: int,
        model: str,
        messages: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        """
        Attempts execution for a single model with exponential backoff retries.
        """
        max_retries = settings.ai_max_retries
        backoff_base = settings.ai_backoff_base_seconds

        for attempt in range(1, max_retries + 1):
            if attempt > 1:
                delay = backoff_base * (2 ** (attempt - 2))
                delay += random.uniform(0, 0.5)
                logger.info(
                    "Waiting %0.2fs before retry attempt %d/%d for model %s (Key Index: %d)",
                    delay,
                    attempt,
                    max_retries,
                    model,
                    key_idx,
                )
                await asyncio.sleep(delay)

            try:
                return await self._send_request(
                    api_key=api_key,
                    key_idx=key_idx,
                    model=model,
                    attempt=attempt,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except (AIConnectionError, AIResponseError, AIRateLimitError) as exc:
                if isinstance(exc, (AIAuthenticationError, AIModelNotFoundError)):
                    raise exc

                if attempt == max_retries:
                    logger.error(
                        "Final attempt %d/%d failed for model %s (Key Index: %d)",
                        attempt,
                        max_retries,
                        model,
                        key_idx,
                    )
                    raise exc

                logger.warning(
                    "Attempt %d/%d failed for model %s (Key Index: %d): %s",
                    attempt,
                    max_retries,
                    model,
                    key_idx,
                    exc,
                )

        raise AIConnectionError(f"Exhausted retries for model {model}.")

    async def _send_request(
        self,
        api_key: str,
        key_idx: int,
        model: str,
        attempt: int,
        messages: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        """
        Executes HTTP call to OpenRouter and processes response.
        """
        headers = self._build_headers(api_key)
        payload = self._build_payload(model, messages, temperature, max_tokens)
        endpoint = "/chat/completions"

        logger.info(
            "Sending request | Attempt: %d | Key Index: %d | Model: %s",
            attempt,
            key_idx,
            model,
        )

        try:
            response = await self._client.post(
                url=endpoint,
                headers=headers,
                json=payload,
            )
            return self._handle_response(response, key_idx, model, attempt)

        except httpx.TimeoutException as exc:
            logger.error(
                "Timeout during request | Attempt: %d | Key Index: %d | Model: %s",
                attempt,
                key_idx,
                model,
            )
            raise AIConnectionError("Request to OpenRouter timed out.") from exc

        except httpx.RequestError as exc:
            logger.error(
                "Network error | Attempt: %d | Key Index: %d | Model: %s | Error: %s",
                attempt,
                key_idx,
                model,
                exc,
            )
            raise AIConnectionError(f"Network failure: {exc}") from exc

    def _handle_response(
        self,
        response: httpx.Response,
        key_idx: int,
        model: str,
        attempt: int,
    ) -> dict[str, Any]:
        """
        Maps HTTP response codes to exceptions and parses/validates output.
        """
        elapsed = response.elapsed.total_seconds()
        status = response.status_code

        logger.info(
            "Response received | Status: %d | Attempt: %d | Key Index: %d | Model: %s | Elapsed: %.3fs",
            status,
            attempt,
            key_idx,
            model,
            elapsed,
        )

        if status == 200:
            try:
                data = response.json()
            except ValueError as exc:
                logger.error("Failed to parse JSON response from OpenRouter.")
                raise AIResponseError("Invalid JSON received from OpenRouter.") from exc

            return self._validate_response_schema(data)

        if status in (401, 403):
            raise AIAuthenticationError(
                f"Authentication failure ({status})."
            )

        if status == 404:
            raise AIModelNotFoundError(
                "Model or resource not found (404)."
            )

        if status == 429:
            raise AIRateLimitError("Rate limit exceeded (429).")

        if status == 408:
            raise AIConnectionError("Server request timeout (408).")

        if status in (500, 502, 503, 504):
            raise AIResponseError(f"OpenRouter service error ({status}).")

        raise AIResponseError(f"Unexpected status code from OpenRouter: {status}")

    def _build_headers(self, api_key: str) -> dict[str, str]:
        """
        Constructs HTTP headers required for OpenRouter completions.
        """
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": settings.user_agent,
        }

        return headers

    def _build_payload(
        self,
        model: str,
        messages: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        """
        Constructs the NVIDIA request payload.
        """
        return {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "reasoning_effort": "none",
        }
    def _validate_config(self) -> None:
        """Validate required API configuration."""
    if (
        not settings.openrouter_api_keys
        or not any(key.strip() for key in settings.openrouter_api_keys)
        or not settings.ai_models
    ):
        raise AINoAvailableKeyError(
            "API keys or AI models are not configured."
        )

    def _validate_response_schema(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Ensures response payload matches expected OpenRouter response structure.
        """
        if not isinstance(payload, dict):
            raise AIResponseError("Expected JSON object response from OpenRouter.")

        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise AIResponseError("OpenRouter response missing 'choices' list.")

        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise AIResponseError("Malformed choice object in OpenRouter response.")

        message = first_choice.get("message")
        if not isinstance(message, dict) or "content" not in message:
            raise AIResponseError("OpenRouter response choice missing 'message.content'.")

        if "id" not in payload:
            raise AIResponseError("OpenRouter response missing 'id'.")

        if "model" not in payload:
            raise AIResponseError("OpenRouter response missing 'model'.")

        return payload