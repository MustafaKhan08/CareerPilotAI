"""
AI Response Parser
==================
Parses and validates raw AI responses returned by the OpenRouter client.

Responsibilities:
- Extract AI message content
- Parse JSON safely
- Validate against Pydantic schemas
- Raise AIParsingError for all parsing/validation failures
"""

from __future__ import annotations

import json
import logging
from typing import Any, Type

from pydantic import ValidationError

from app.ai.exceptions import AIParsingError
from app.ai.schema import (
    ResumeAnalysisResponse,
    ResumeValidationResponse,
)

logger = logging.getLogger(__name__)


class AIResponseParser:
    """
    Parses raw OpenRouter responses into validated Pydantic models.

    This class is intentionally independent of business logic and AI provider
    implementation details. It only converts raw responses into structured,
    validated objects.
    """

    def extract_content(self, response: dict[str, Any]) -> str:
        """
        Extracts the assistant message content from an OpenRouter response.

        Args:
            response: Raw response returned by the AI client.

        Returns:
            Assistant message content as a string.

        Raises:
            AIParsingError:
                If the response structure is invalid or content is missing.
        """
        try:
            content = response["choices"][0]["message"]["content"]

            if not isinstance(content, str):
                raise AIParsingError(
                    "AI response content must be a string."
                )

            return content.strip()

        except (KeyError, IndexError, TypeError) as exc:
            logger.exception("Failed to extract AI response content.")
            raise AIParsingError(
                "Invalid AI response structure."
            ) from exc

    def parse_json(self, content: str) -> dict[str, Any]:
        """
        Parses AI-generated JSON text.

        Args:
            content: JSON string returned by the AI.

        Returns:
            Parsed dictionary.

        Raises:
            AIParsingError:
                If the content is not valid JSON.
        """
        try:
            data = json.loads(content)

            if not isinstance(data, dict):
                raise AIParsingError(
                    "Expected JSON object from AI."
                )

            return data

        except json.JSONDecodeError as exc:
            logger.exception("Failed to decode AI JSON response.")
            raise AIParsingError(
                "AI returned invalid JSON."
            ) from exc

    def parse_resume_validation(
        self,
        response: dict[str, Any],
    ) -> ResumeValidationResponse:
        """
        Parses a resume validation response.

        Args:
            response: Raw OpenRouter response.

        Returns:
            ResumeValidationResponse
        """
        content = self.extract_content(response)
        payload = self.parse_json(content)

        return self._validate_schema(
            payload,
            ResumeValidationResponse,
        )

    def parse_resume_analysis(
        self,
        response: dict[str, Any],
    ) -> ResumeAnalysisResponse:
        """
        Parses a resume analysis response.

        Args:
            response: Raw OpenRouter response.

        Returns:
            ResumeAnalysisResponse
        """
        content = self.extract_content(response)
        payload = self.parse_json(content)

        return self._validate_schema(
            payload,
            ResumeAnalysisResponse,
        )

    def _validate_schema(
        self,
        payload: dict[str, Any],
        schema: Type[
            ResumeValidationResponse | ResumeAnalysisResponse
        ],
    ) -> ResumeValidationResponse | ResumeAnalysisResponse:
        """
        Validates parsed JSON against a Pydantic schema.

        Args:
            payload: Parsed JSON object.
            schema: Target schema class.

        Returns:
            Validated schema instance.

        Raises:
            AIParsingError:
                If schema validation fails.
        """
        try:
            return schema.model_validate(payload)

        except ValidationError as exc:
            logger.exception(
                "Schema validation failed for %s.",
                schema.__name__,
            )
            raise AIParsingError(
                f"Invalid AI response for schema '{schema.__name__}'."
            ) from exc