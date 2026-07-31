"""
AI Service
==========
Business-layer orchestration for AI-powered resume validation and ATS analysis.

Responsibilities:
- Build AI prompts
- Call the OpenRouter client
- Parse AI responses
- Return validated domain schemas

This module intentionally contains no FastAPI or HTTP-specific logic.
"""

from __future__ import annotations

import logging

from app.ai.client import OpenRouterClient
from app.ai.parser import AIResponseParser
from app.ai.prompts import (
    build_resume_analysis_messages,
    build_resume_validation_messages,
)
from app.ai.schema import ResumeValidationResponse
from app.analyses.schema import ResumeAnalysisResponse

logger = logging.getLogger(__name__)


class AIService:
    """
    Coordinates prompt generation, AI communication,
    and response parsing.

    This class contains the business logic layer between
    FastAPI routers and the OpenRouter client.
    """

    def __init__(self) -> None:
        """
        Initializes reusable AI dependencies.
        """
        self.client = OpenRouterClient()
        self.parser = AIResponseParser()

    async def close(self) -> None:
        """
        Releases any resources held by the AI client.

        Should be called during application shutdown.
        """
        await self.client.close()

    async def validate_resume(
        self,
        resume_text: str,
    ) -> ResumeValidationResponse:
        """
        Validates whether a resume contains sufficient
        information before ATS analysis.

        Workflow:
            Resume Text
                 │
                 ▼
          Prompt Builder
                 │
                 ▼
        OpenRouter Client
                 │
                 ▼
         Response Parser
                 │
                 ▼
        ResumeValidationResponse

        Args:
            resume_text:
                Plain text extracted from the uploaded resume.

        Returns:
            ResumeValidationResponse

        Raises:
            Any AI-related exception propagated from the
            client or parser.
        """

        logger.info("Starting resume validation.")

        messages = build_resume_validation_messages(
            resume_text=resume_text,
        )

        response = await self.client.chat_completion(
            messages=messages,
        )

        parsed_response = self.parser.parse_resume_validation(
            response=response,
        )

        logger.info(
            "Resume validation completed successfully."
        )

        return parsed_response

    async def analyze_resume(
        self,
        resume_text: str,
    ) -> ResumeAnalysisResponse:
        """
        Performs a complete ATS analysis of a validated resume.

        Workflow:
            Resume Text
                 │
                 ▼
          Prompt Builder
                 │
                 ▼
        OpenRouter Client
                 │
                 ▼
         Response Parser
                 │
                 ▼
        ResumeAnalysisResponse

        Args:
            resume_text:
                Plain text extracted from the uploaded resume.

        Returns:
            ResumeAnalysisResponse

        Raises:
            Any AI-related exception propagated from the
            client or parser.
        """

        logger.info("Starting ATS resume analysis.")

        messages = build_resume_analysis_messages(
            resume_text=resume_text,
        )

        response = await self.client.chat_completion(
            messages=messages,
        )

        parsed_response = self.parser.parse_resume_analysis(
            response=response,
        )

        logger.info(
            "ATS resume analysis completed successfully."
        )

        return parsed_response


# Singleton service instance
#
# Reused across the application to avoid repeatedly creating
# HTTP clients and connection pools.
ai_service = AIService()