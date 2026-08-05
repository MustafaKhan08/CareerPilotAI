"""Pydantic schemas for the Interview Preparation module."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.interviews.model import (
    InterviewDifficulty,
    InterviewStatus,
    InterviewType,
)


# ==========================================================
# START INTERVIEW REQUEST
# ==========================================================


class InterviewStartRequest(BaseModel):
    """Request to start a new interview."""

    title: str = Field(
        min_length=1,
        max_length=255,
    )

    target_role: str = Field(
        min_length=1,
        max_length=255,
    )

    interview_type: InterviewType

    difficulty: InterviewDifficulty

    total_questions: int = Field(
        default=10,
        ge=1,
        le=20,
    )


# ==========================================================
# AI QUESTION SCHEMA
# Validates the JSON the AI must return for a question.
# ==========================================================


class AIQuestionSchema(BaseModel):
    """
    Strict schema matching the JSON the AI must produce
    for a single interview question.
    """

    question: str

    category: str

    difficulty: str

    expected_focus: list[str]


# ==========================================================
# AI EVALUATION SCHEMA
# Validates the raw JSON the AI returns for an evaluation.
# Intentionally does not include next_question or completed
# — those are derived by the service layer.
# ==========================================================


class AIEvaluationSchema(BaseModel):
    """
    Strict schema matching the JSON the AI must produce
    when evaluating a candidate's answer.
    """

    score: float = Field(ge=0.0, le=10.0)

    strengths: list[str]

    weaknesses: list[str]

    communication: str

    confidence: str

    technical_accuracy: str

    ideal_answer: str

    improvements: list[str]


# ==========================================================
# AI REPORT SCHEMA
# Validates the raw JSON the AI returns for the final report.
# Intentionally does not include session_id or completed_at
# — those are derived by the service layer from the session.
# ==========================================================


class AIReportSchema(BaseModel):
    """
    Strict schema matching the JSON the AI must produce
    for the final interview report.
    """

    overall_score: float = Field(ge=0.0, le=10.0)

    summary: str

    strengths: list[str]

    weaknesses: list[str]

    recommendations: str

    career_readiness: str

    next_steps: list[str]


# ==========================================================
# START INTERVIEW RESPONSE
# Returned after a session is created and the first
# question is generated.
# ==========================================================


class InterviewSessionStartResponse(BaseModel):
    """
    Response returned after a new interview session is
    created and the first question has been generated.
    """

    session_id: int

    question_id: int

    question_number: int

    question: str

    category: str

    difficulty: str

    expected_focus: list[str]


# ==========================================================
# QUESTION
# ==========================================================


class InterviewQuestionResponse(BaseModel):
    """One interview question returned within an evaluation."""

    question_id: int

    question_order: int

    question: str


# ==========================================================
# ANSWER SUBMISSION REQUEST
# ==========================================================


class InterviewAnswerRequest(BaseModel):
    """User answer submission."""

    answer: str = Field(
        min_length=1,
    )


# ==========================================================
# EVALUATION RESPONSE
# Returned after a candidate submits an answer.
# ==========================================================


class InterviewEvaluationResponse(BaseModel):
    """
    Full evaluation response returned to the client
    after a candidate submits an answer.

    next_question is None when the interview is complete.
    completed is True when this was the final question.
    """

    score: float

    strengths: list[str]

    weaknesses: list[str]

    communication: str

    confidence: str

    technical_accuracy: str

    ideal_answer: str

    improvements: list[str]

    next_question: InterviewQuestionResponse | None = None

    completed: bool


# ==========================================================
# FINAL REPORT RESPONSE
# Returned by GET /interviews/{session_id}/report.
# ==========================================================


class InterviewReportResponse(BaseModel):
    """
    Final interview report returned to the client.

    Combines the AI-generated report content with session
    metadata (session_id, completed_at).
    """

    session_id: int

    overall_score: float

    summary: str

    strengths: list[str]

    weaknesses: list[str]

    recommendations: str

    career_readiness: str

    next_steps: list[str]

    completed_at: datetime


# ==========================================================
# HISTORY
# ==========================================================


class InterviewHistoryItem(BaseModel):
    """Interview history item."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    title: str

    target_role: str

    interview_type: InterviewType

    difficulty: InterviewDifficulty

    status: InterviewStatus

    overall_score: float | None

    total_questions: int

    current_question_number: int

    created_at: datetime

    completed_at: datetime | None


class InterviewHistoryResponse(BaseModel):
    """Interview history."""

    interviews: list[
        InterviewHistoryItem
    ]


# ==========================================================
# SESSION DETAILS
# ==========================================================


class InterviewAnswerItem(BaseModel):
    """Stored interview answer."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    answer: str

    evaluation: dict[str, Any] | None

    created_at: datetime


class InterviewQuestionItem(BaseModel):
    """Stored interview question."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    question_order: int

    question: str

    answer: InterviewAnswerItem | None


class InterviewSessionResponse(BaseModel):
    """Complete interview session."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    title: str

    target_role: str

    interview_type: InterviewType

    difficulty: InterviewDifficulty

    status: InterviewStatus

    overall_score: float | None

    summary: str | None

    recommendations: str | None

    total_questions: int

    current_question_number: int

    started_at: datetime | None

    completed_at: datetime | None

    created_at: datetime

    questions: list[
        InterviewQuestionItem
    ]


# ==========================================================
# DELETE
# ==========================================================


class InterviewDeleteResponse(BaseModel):
    """Delete interview response."""

    message: Literal[
        "Interview deleted successfully."
    ]