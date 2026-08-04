"""Service layer for the Interview Preparation module."""

from __future__ import annotations

import json
import logging

from fastapi import HTTPException
from fastapi import status
from sqlalchemy.orm import Session

from app.analyses.service import (
    format_resume_context,
    latest_analysis_response,
)
from app.chat.ai_client import (
    ChatClientError,
    generate_chat_response,
)
from app.interviews.model import (
    InterviewQuestion,
    InterviewSession,
    InterviewStatus,
)
from app.interviews.prompt import (
    build_question_prompt,
)
from app.interviews.repository import (
    create_interview_session,
    create_question,
)
from app.interviews.schema import (
    AIQuestionSchema,
    InterviewSessionStartResponse,
    InterviewStartRequest,
)
from app.resumes.service import (
    get_latest_resume,
)
from app.users.model import User

logger = logging.getLogger(__name__)


# ==========================================================
# Constants
# ==========================================================

AI_RESPONSE_ERROR = (
    "The AI returned an invalid interview question."
)

NO_RESUME_ERROR = (
    "Please upload a resume before starting an interview."
)

NO_ANALYSIS_ERROR = (
    "Please analyze your resume before starting an interview."
)


# ==========================================================
# Helper Functions
# ==========================================================


def _parse_ai_question(
    ai_response: str,
) -> AIQuestionSchema:
    """
    Parse and validate the AI response.

    Raises:
        HTTPException:
            If the response is not valid JSON
            or does not match the expected schema.
    """

    try:
        payload = json.loads(
            ai_response,
        )

    except json.JSONDecodeError as exc:
        logger.exception(
            "AI returned invalid JSON."
        )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=AI_RESPONSE_ERROR,
        ) from exc

    try:
        return AIQuestionSchema.model_validate(
            payload,
        )

    except Exception as exc:
        logger.exception(
            "AI returned an invalid schema."
        )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=AI_RESPONSE_ERROR,
        ) from exc


def _build_session(
    *,
    current_user: User,
    resume_id: int,
    request: InterviewStartRequest,
) -> InterviewSession:
    """
    Construct a new InterviewSession model.
    """

    return InterviewSession(
        user_id=current_user.id,
        resume_id=resume_id,
        title=request.title,
        interview_type=request.interview_type,
        difficulty=request.difficulty,
        target_role=request.target_role,
        total_questions=request.total_questions,
        current_question_number=1,
        status=InterviewStatus.IN_PROGRESS,
    )


def _build_question(
    *,
    session_id: int,
    question_number: int,
    ai_question: AIQuestionSchema,
) -> InterviewQuestion:
    """
    Construct an InterviewQuestion model.
    """

    return InterviewQuestion(
        session_id=session_id,
        question_order=question_number,
        question=ai_question.question,
    )


# ==========================================================
# START INTERVIEW
# ==========================================================


async def start_interview(
    db: Session,
    current_user: User,
    request: InterviewStartRequest,
) -> InterviewSessionStartResponse:
    """
    Start a new interview session and
    generate the first interview question.

    Workflow
    --------
    1. Retrieve latest uploaded resume.
       → 404 if missing.
    2. Retrieve latest resume analysis.
       → 404 if missing.
    3. Format resume context string.
    4. Build AI prompt.
    5. Call OpenRouter via generate_chat_response.
    6. Parse and validate AI JSON response.
    7. Persist InterviewSession (flush, no commit yet).
    8. Persist InterviewQuestion (flush, no commit yet).
    9. Commit transaction.
    10. Return InterviewSessionStartResponse.
    """

    logger.info(
        "Starting interview for user %s.",
        current_user.id,
    )

    # ----------------------------------------------------------
    # Step 1: Retrieve latest resume
    # ----------------------------------------------------------

    resume = get_latest_resume(
        db=db,
        user_id=current_user.id,
    )

    if resume is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=NO_RESUME_ERROR,
        )

    logger.info(
        "Found resume %s for user %s.",
        resume.id,
        current_user.id,
    )

    # ----------------------------------------------------------
    # Step 2: Retrieve latest resume analysis
    # ----------------------------------------------------------

    analysis = latest_analysis_response(
        db=db,
        resume_id=resume.id,
    )

    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=NO_ANALYSIS_ERROR,
        )

    logger.info(
        "Found analysis for resume %s.",
        resume.id,
    )

    # ----------------------------------------------------------
    # Step 3: Format resume context
    # ----------------------------------------------------------

    resume_context = format_resume_context(
        analysis,
    )

    # ----------------------------------------------------------
    # Step 4: Build AI prompt
    # ----------------------------------------------------------

    prompt = build_question_prompt(
        resume_context=resume_context,
        target_role=request.target_role,
        interview_type=request.interview_type.value,
        difficulty=request.difficulty.value,
    )

    # ----------------------------------------------------------
    # Steps 5–9: Call AI, validate, persist, commit
    # ----------------------------------------------------------

    try:

        # Step 5: Call OpenRouter
        ai_response = await generate_chat_response(
            messages=prompt,
        )

        # Step 6: Parse and validate AI JSON
        ai_question = _parse_ai_question(
            ai_response,
        )

        # Step 7: Persist InterviewSession
        session = _build_session(
            current_user=current_user,
            resume_id=resume.id,
            request=request,
        )

        create_interview_session(
            db=db,
            session=session,
        )

        # Step 8: Persist InterviewQuestion
        question = _build_question(
            session_id=session.id,
            question_number=1,
            ai_question=ai_question,
        )

        create_question(
            db=db,
            question=question,
        )

        # Step 9: Commit transaction
        db.commit()
        db.refresh(session)
        db.refresh(question)

        logger.info(
            "Interview session %s created with question %s.",
            session.id,
            question.id,
        )

        # Step 10: Return response
        return InterviewSessionStartResponse(
            session_id=session.id,
            question_id=question.id,
            question_number=1,
            question=ai_question.question,
            category=ai_question.category,
            difficulty=ai_question.difficulty,
            expected_focus=ai_question.expected_focus,
        )

    except ChatClientError as exc:

        db.rollback()

        logger.exception(
            "OpenRouter request failed: %s",
            exc,
        )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to generate interview question.",
        ) from exc

    except HTTPException:

        db.rollback()

        raise

    except Exception as exc:

        db.rollback()

        logger.exception(
            "Failed to start interview."
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to start interview.",
        ) from exc  