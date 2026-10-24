"""Service layer for the Interview Preparation module."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone

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
    InterviewAnswer,
    InterviewQuestion,
    InterviewSession,
    InterviewStatus,
)
from app.interviews.pdf_generator import generate_report_pdf
from app.interviews.prompt import (
    build_evaluation_prompt,
    build_question_prompt,
    build_report_prompt,
)
from app.interviews.repository import (
    create_answer,
    create_interview_session,
    create_question,
    get_answer,
    get_interview_session,
    get_latest_question,
    update_session,
)
from app.interviews.schema import (
    AIEvaluationSchema,
    AIQuestionSchema,
    AIReportSchema,
    InterviewEvaluationResponse,
    InterviewQuestionResponse,
    InterviewReportResponse,
    InterviewSessionStartResponse,
    InterviewStartRequest,
    InterviewTimeoutResponse,
)
from app.resumes.service import (
    get_latest_resume,
)
from app.users.model import User

logger = logging.getLogger(__name__)


# ==========================================================
# Constants
# ==========================================================

AI_QUESTION_ERROR = (
    "The AI returned an invalid interview question."
)

AI_EVALUATION_ERROR = (
    "The AI returned an invalid evaluation."
)

AI_REPORT_ERROR = (
    "The AI returned an invalid interview report."
)

NO_RESUME_ERROR = (
    "Please upload a resume before starting an interview."
)

NO_ANALYSIS_ERROR = (
    "Please analyze your resume before starting an interview."
)

SESSION_NOT_FOUND_ERROR = (
    "Interview session not found."
)

QUESTION_NOT_FOUND_ERROR = (
    "Interview question not found."
)

ALREADY_ANSWERED_ERROR = (
    "This question has already been answered."
)

SESSION_NOT_ACTIVE_ERROR = (
    "This interview session is not active."
)

SESSION_NOT_COMPLETED_ERROR = (
    "The interview report is only available after "
    "the interview is completed."
)

REPORT_DESERIALISATION_ERROR = (
    "Failed to read stored interview report."
)

REPORT_NOT_READY_ERROR = (
    "The interview report has not been generated yet."
)

DEADLINE_EXCEEDED_ERROR = (
    "Interview time has expired. "
    "No further answers can be submitted."
)


# ==========================================================
# Private Helpers — Parsing
# ==========================================================


def _parse_ai_question(
    ai_response: str,
) -> AIQuestionSchema:
    """
    Parse and validate the AI question response.

    Raises:
        HTTPException (502): invalid JSON or schema mismatch.
    """

    try:
        payload = json.loads(ai_response)

    except json.JSONDecodeError as exc:
        logger.exception("AI returned invalid JSON for question.")

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=AI_QUESTION_ERROR,
        ) from exc

    try:
        return AIQuestionSchema.model_validate(payload)

    except Exception as exc:
        logger.exception("AI question response failed schema validation.")

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=AI_QUESTION_ERROR,
        ) from exc


def _parse_ai_evaluation(
    ai_response: str,
) -> AIEvaluationSchema:
    """
    Parse and validate the AI evaluation response.

    Raises:
        HTTPException (502): invalid JSON or schema mismatch.
    """

    try:
        payload = json.loads(ai_response)

    except json.JSONDecodeError as exc:
        logger.exception("AI returned invalid JSON for evaluation.")

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=AI_EVALUATION_ERROR,
        ) from exc

    try:
        return AIEvaluationSchema.model_validate(payload)

    except Exception as exc:
        logger.exception("AI evaluation response failed schema validation.")

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=AI_EVALUATION_ERROR,
        ) from exc


def _parse_ai_report(
    ai_response: str,
) -> AIReportSchema:
    """
    Parse and validate the AI final report response.

    Raises:
        HTTPException (502): invalid JSON or schema mismatch.
    """

    try:
        payload = json.loads(ai_response)

    except json.JSONDecodeError as exc:
        logger.exception("AI returned invalid JSON for report.")

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=AI_REPORT_ERROR,
        ) from exc

    try:
        return AIReportSchema.model_validate(payload)

    except Exception as exc:
        logger.exception("AI report response failed schema validation.")

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=AI_REPORT_ERROR,
        ) from exc


# ==========================================================
# Private Helpers — Model Construction
# ==========================================================


def _build_session(
    *,
    current_user: User,
    resume_id: int,
    request: InterviewStartRequest,
) -> InterviewSession:
    """
    Construct a new InterviewSession model.
    """

    now_utc = datetime.now(timezone.utc)
    deadline = now_utc + timedelta(minutes=request.duration_minutes)

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
        duration_minutes=request.duration_minutes,
        deadline_at=deadline,
        started_at=now_utc,
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


def _build_answer(
    *,
    question_id: int,
    candidate_answer: str,
    evaluation: AIEvaluationSchema,
) -> InterviewAnswer:
    """
    Construct an InterviewAnswer model.

    The evaluation dict is stored as JSON in the database.
    """

    return InterviewAnswer(
        question_id=question_id,
        answer=candidate_answer,
        evaluation=evaluation.model_dump(),
    )


# ==========================================================
# Private Helpers — Resume Context
# ==========================================================


def _load_resume_context(
    db: Session,
    current_user: User,
) -> tuple[int, str]:
    """
    Retrieve the latest resume and analysis for a user,
    and return the formatted resume context string.

    Returns:
        (resume_id, resume_context)

    Raises:
        HTTPException (404) if resume or analysis is missing.
    """

    resume = get_latest_resume(
        db=db,
        user_id=current_user.id,
    )

    if resume is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=NO_RESUME_ERROR,
        )

    analysis = latest_analysis_response(
        db=db,
        resume_id=resume.id,
    )

    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=NO_ANALYSIS_ERROR,
        )

    resume_context = format_resume_context(analysis)

    return resume.id, resume_context


# ==========================================================
# Private Helpers — Interview Transcript
# ==========================================================


def _build_interview_transcript(
    interview_session: InterviewSession,
    only_answered: bool = False,
) -> str:
    """
    Format all questions, candidate answers, and per-question
    evaluations from a completed session into a human-readable
    transcript string suitable for inclusion in the AI report
    prompt.

    The session must have been loaded with joinedload on
    questions and their answers (as done by get_interview_session).

    If only_answered is True, questions without candidate answers
    are excluded from the transcript.

    Returns:
        Formatted transcript string.
    """

    lines: list[str] = []

    for question in interview_session.questions:
        if only_answered and question.answer is None:
            continue

        lines.append(
            f"Question {question.question_order}: "
            f"{question.question}"
        )

        if question.answer is not None:

            lines.append(
                f"Candidate Answer: {question.answer.answer}"
            )

            evaluation = question.answer.evaluation

            if evaluation:
                score = evaluation.get("score", "N/A")
                strengths = evaluation.get("strengths", [])
                weaknesses = evaluation.get("weaknesses", [])
                technical_accuracy = evaluation.get(
                    "technical_accuracy", "N/A"
                )

                lines.append(f"Score: {score}/10")
                lines.append(
                    f"Technical Accuracy: {technical_accuracy}"
                )

                if strengths:
                    lines.append(
                        "Strengths: "
                        + "; ".join(str(s) for s in strengths)
                    )

                if weaknesses:
                    lines.append(
                        "Weaknesses: "
                        + "; ".join(str(w) for w in weaknesses)
                    )

        else:
            lines.append("Candidate Answer: [Not answered]")

        lines.append("")

    return "\n".join(lines).strip()


# ==========================================================
# Private Helpers — Report Persistence & Retrieval
# ==========================================================


def _report_is_cached(
    interview_session: InterviewSession,
) -> bool:
    """
    Return True if a report has already been generated and
    persisted into the session.

    Detection strategy: overall_score is not None AND
    recommendations is a non-empty string that parses as valid
    JSON. This is robust against the case where summary alone
    might be set by future code unrelated to report generation.
    """

    if interview_session.overall_score is None:
        return False

    if not interview_session.recommendations:
        return False

    try:
        json.loads(interview_session.recommendations)
        return True
    except (json.JSONDecodeError, TypeError):
        return False


def _load_cached_report(
    interview_session: InterviewSession,
) -> InterviewReportResponse:
    """
    Deserialise the stored report JSON from the
    recommendations column and return an InterviewReportResponse.

    Raises:
        HTTPException (500): if deserialisation fails.
    """

    try:
        report_data = json.loads(
            interview_session.recommendations
        )
        ai_report = AIReportSchema.model_validate(report_data)

    except Exception as exc:
        logger.exception(
            "Failed to deserialise cached report for session %s.",
            interview_session.id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=REPORT_DESERIALISATION_ERROR,
        ) from exc

    return InterviewReportResponse(
        session_id=interview_session.id,
        overall_score=ai_report.overall_score,
        summary=ai_report.summary,
        strengths=ai_report.strengths,
        weaknesses=ai_report.weaknesses,
        recommendations=ai_report.recommendations,
        career_readiness=ai_report.career_readiness,
        next_steps=ai_report.next_steps,
        completed_at=interview_session.completed_at,
        is_partial=interview_session.status == InterviewStatus.TIMED_OUT,
        status=interview_session.status,
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
    1. Retrieve latest resume → 404 if missing.
    2. Retrieve latest resume analysis → 404 if missing.
    3. Format resume context string.
    4. Build AI question prompt.
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

    resume_id, resume_context = _load_resume_context(
        db=db,
        current_user=current_user,
    )

    logger.info(
        "Loaded resume context for user %s (resume_id=%s).",
        current_user.id,
        resume_id,
    )

    prompt = build_question_prompt(
        resume_context=resume_context,
        target_role=request.target_role,
        interview_type=request.interview_type.value,
        difficulty=request.difficulty.value,
    )

    try:

        ai_response = await generate_chat_response(
            messages=prompt,
        )

        ai_question = _parse_ai_question(ai_response)

        session = _build_session(
            current_user=current_user,
            resume_id=resume_id,
            request=request,
        )

        create_interview_session(
            db=db,
            session=session,
        )

        question = _build_question(
            session_id=session.id,
            question_number=1,
            ai_question=ai_question,
        )

        create_question(
            db=db,
            question=question,
        )

        db.commit()
        db.refresh(session)
        db.refresh(question)

        logger.info(
            "Interview session %s created with question %s.",
            session.id,
            question.id,
        )

        return InterviewSessionStartResponse(
            session_id=session.id,
            question_id=question.id,
            question_number=1,
            question=ai_question.question,
            category=ai_question.category,
            difficulty=ai_question.difficulty,
            expected_focus=ai_question.expected_focus,
            deadline_at=session.deadline_at,
        )

    except ChatClientError as exc:

        db.rollback()

        logger.exception(
            "OpenRouter request failed during start_interview: %s",
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

        logger.exception("Unexpected error in start_interview.")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to start interview.",
        ) from exc


def _is_deadline_passed(deadline_at: datetime | None) -> bool:
    """
    Check if the interview deadline has passed.
    Handles offset-naive datetimes returned by some DB drivers (e.g. SQLite) safely.
    """
    if deadline_at is None:
        return False
    if deadline_at.tzinfo is None:
        deadline_at = deadline_at.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) > deadline_at


# ==========================================================
# SUBMIT ANSWER
# ==========================================================


async def submit_answer(
    db: Session,
    current_user: User,
    session_id: int,
    candidate_answer: str,
) -> InterviewEvaluationResponse:
    """
    Evaluate a candidate's answer to the current question,
    persist the result, advance the session, and optionally
    generate the next question.

    Workflow
    --------
    1.  Load the InterviewSession — verify it exists and
        belongs to the authenticated user.
    2.  Guard: session must be IN_PROGRESS.
    3.  Load the current question (latest by question_order).
    4.  Guard: current question must not already be answered.
    5.  Load resume context for personalised evaluation.
    6.  Build evaluation prompt.
    7.  Call OpenRouter → get evaluation JSON.
    8.  Validate evaluation JSON.
    9.  Persist InterviewAnswer (flush).
    10. If more questions remain:
          a. Build question prompt.
          b. Call OpenRouter → get next question JSON.
          c. Validate question JSON.
          d. Persist next InterviewQuestion (flush).
          e. Advance current_question_number (flush).
          f. Commit.
          g. Return evaluation + next question, completed=False.
    11. If this was the final question:
          a. Advance current_question_number (flush).
          b. Mark session as COMPLETED, set completed_at (flush).
          c. Generate full report immediately and persist (flush).
          d. Commit.
          e. Return evaluation + next_question=None, completed=True.
    """

    logger.info(
        "Submitting answer for session %s by user %s.",
        session_id,
        current_user.id,
    )

    # ----------------------------------------------------------
    # Step 1: Load session (ownership-guarded by repository)
    # ----------------------------------------------------------

    interview_session = get_interview_session(
        db=db,
        session_id=session_id,
        current_user=current_user,
    )

    if interview_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=SESSION_NOT_FOUND_ERROR,
        )

    # ----------------------------------------------------------
    # Step 2: Guard — session must be active
    # ----------------------------------------------------------

    if interview_session.status != InterviewStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=SESSION_NOT_ACTIVE_ERROR,
        )

    # ----------------------------------------------------------
    # Step 2b: Guard — deadline must not have passed
    # ----------------------------------------------------------

    if _is_deadline_passed(interview_session.deadline_at):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=DEADLINE_EXCEEDED_ERROR,
        )

    # ----------------------------------------------------------
    # Step 3: Load the current question
    # ----------------------------------------------------------

    current_question = get_latest_question(
        db=db,
        session_id=session_id,
    )

    if current_question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=QUESTION_NOT_FOUND_ERROR,
        )

    # ----------------------------------------------------------
    # Step 4: Guard — question must not already be answered
    # ----------------------------------------------------------

    existing_answer = get_answer(
        db=db,
        question_id=current_question.id,
    )

    if existing_answer is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ALREADY_ANSWERED_ERROR,
        )

    # ----------------------------------------------------------
    # Step 5: Load resume context
    # ----------------------------------------------------------

    _, resume_context = _load_resume_context(
        db=db,
        current_user=current_user,
    )

    # ----------------------------------------------------------
    # Step 6: Build evaluation prompt
    # ----------------------------------------------------------

    evaluation_prompt = build_evaluation_prompt(
        resume_context=resume_context,
        question=current_question.question,
        candidate_answer=candidate_answer,
    )

    # ----------------------------------------------------------
    # Steps 7–11: AI call + persist + commit (atomic block)
    # ----------------------------------------------------------

    is_final_question = (
        current_question.question_order
        >= interview_session.total_questions
    )

    try:

        # Step 7: Call OpenRouter for evaluation
        eval_raw = await generate_chat_response(
            messages=evaluation_prompt,
        )

        # Step 8: Validate evaluation JSON
        ai_evaluation = _parse_ai_evaluation(eval_raw)

        # Step 9: Persist the answer
        answer = _build_answer(
            question_id=current_question.id,
            candidate_answer=candidate_answer,
            evaluation=ai_evaluation,
        )

        create_answer(
            db=db,
            answer=answer,
        )

        # Attach to current question for report transcript building
        current_question.answer = answer

        logger.info(
            "Answer persisted for question %s (session %s).",
            current_question.id,
            session_id,
        )

        # ----------------------------------------------------------
        # Step 10: More questions remain — generate next question
        # ----------------------------------------------------------

        # Check if deadline passed during AI evaluation of this answer
        time_expired = _is_deadline_passed(interview_session.deadline_at)

        if not is_final_question and not time_expired:

            next_question_number = (
                current_question.question_order + 1
            )

            previous_questions = [
                q.question for q in interview_session.questions
            ]

            question_prompt = build_question_prompt(
                resume_context=resume_context,
                target_role=interview_session.target_role,
                interview_type=interview_session.interview_type.value,
                difficulty=interview_session.difficulty.value,
                previous_questions=previous_questions,
            )

            # Call OpenRouter for next question
            question_raw = await generate_chat_response(
                messages=question_prompt,
            )

            ai_next_question = _parse_ai_question(question_raw)

            next_question_model = _build_question(
                session_id=session_id,
                question_number=next_question_number,
                ai_question=ai_next_question,
            )

            create_question(
                db=db,
                question=next_question_model,
            )

            # Advance session counter
            interview_session.current_question_number = (
                next_question_number
            )

            update_session(
                db=db,
                session=interview_session,
            )

            db.commit()
            db.refresh(next_question_model)

            logger.info(
                "Session %s advanced to question %s.",
                session_id,
                next_question_number,
            )

            return InterviewEvaluationResponse(
                score=ai_evaluation.score,
                strengths=ai_evaluation.strengths,
                weaknesses=ai_evaluation.weaknesses,
                communication=ai_evaluation.communication,
                confidence=ai_evaluation.confidence,
                technical_accuracy=ai_evaluation.technical_accuracy,
                ideal_answer=ai_evaluation.ideal_answer,
                improvements=ai_evaluation.improvements,
                next_question=InterviewQuestionResponse(
                    question_id=next_question_model.id,
                    question_order=next_question_model.question_order,
                    question=next_question_model.question,
                ),
                completed=False,
            )

        # ----------------------------------------------------------
        # Step 11: Final question OR deadline passed during evaluation
        # ----------------------------------------------------------

        interview_session.current_question_number = (
            current_question.question_order
        )
        if time_expired and not is_final_question:
            interview_session.status = InterviewStatus.TIMED_OUT
            logger.info(
                "Deadline expired during evaluation for session %s. Finalized as TIMED_OUT.",
                session_id,
            )
        else:
            interview_session.status = InterviewStatus.COMPLETED

        interview_session.completed_at = datetime.now(timezone.utc)

        # Build transcript and generate report
        transcript = _build_interview_transcript(
            interview_session=interview_session,
            only_answered=True,
        )

        report_prompt = build_report_prompt(
            resume_context=resume_context,
            target_role=interview_session.target_role,
            interview_type=interview_session.interview_type.value,
            difficulty=interview_session.difficulty.value,
            transcript=transcript,
        )

        report_raw = await generate_chat_response(
            messages=report_prompt,
        )

        ai_report = _parse_ai_report(report_raw)

        full_report_json = json.dumps(
            ai_report.model_dump(),
            ensure_ascii=False,
        )

        interview_session.overall_score = ai_report.overall_score
        interview_session.summary = ai_report.summary
        interview_session.recommendations = full_report_json

        update_session(
            db=db,
            session=interview_session,
        )

        db.commit()

        logger.info(
            "Interview session %s completed and report generated.",
            session_id,
        )

        return InterviewEvaluationResponse(
            score=ai_evaluation.score,
            strengths=ai_evaluation.strengths,
            weaknesses=ai_evaluation.weaknesses,
            communication=ai_evaluation.communication,
            confidence=ai_evaluation.confidence,
            technical_accuracy=ai_evaluation.technical_accuracy,
            ideal_answer=ai_evaluation.ideal_answer,
            improvements=ai_evaluation.improvements,
            next_question=None,
            completed=True,
        )

    except ChatClientError as exc:

        db.rollback()

        logger.exception(
            "OpenRouter request failed during submit_answer: %s",
            exc,
        )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to process your answer at this time.",
        ) from exc

    except HTTPException:

        db.rollback()

        raise

    except Exception as exc:

        db.rollback()

        logger.exception(
            "Unexpected error in submit_answer for session %s.",
            session_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to submit answer.",
        ) from exc


# ==========================================================
# FINAL REPORT
# ==========================================================


async def get_or_generate_report(
    db: Session,
    current_user: User,
    session_id: int,
) -> InterviewReportResponse:
    """
    Return the final interview report for a completed session.

    Following architectural change, this endpoint is purely
    a read-only operation. The report generation now happens
    synchronously as part of the final submit_answer call.

    The function signature and name are preserved to prevent
    breaking the router layer.

    Workflow
    --------
    1.  Load InterviewSession — verify ownership.
    2.  Guard: status must be COMPLETED (HTTP 409 if not).
    3.  If report cached → deserialise and return.
    4.  If report not cached → return 404 (Report not ready).
    """

    logger.info(
        "Report requested for session %s by user %s.",
        session_id,
        current_user.id,
    )

    # ----------------------------------------------------------
    # Step 1: Load session (ownership-guarded by repository)
    # get_interview_session joinloads questions + answers.
    # ----------------------------------------------------------

    interview_session = get_interview_session(
        db=db,
        session_id=session_id,
        current_user=current_user,
    )

    if interview_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=SESSION_NOT_FOUND_ERROR,
        )

    # ----------------------------------------------------------
    # Step 2: Guard — interview must be completed or timed out
    # ----------------------------------------------------------

    _report_allowed_statuses = {
        InterviewStatus.COMPLETED,
        InterviewStatus.TIMED_OUT,
    }
    if interview_session.status not in _report_allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=SESSION_NOT_COMPLETED_ERROR,
        )

    # ----------------------------------------------------------
    # Step 3: Return cached report
    # ----------------------------------------------------------

    if _report_is_cached(interview_session):

        logger.info(
            "Returning cached report for session %s.",
            session_id,
        )

        return _load_cached_report(interview_session)

    # ----------------------------------------------------------
    # Step 4: Error if report not found
    # ----------------------------------------------------------

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=REPORT_NOT_READY_ERROR,
    )


# ==========================================================
# REPORT PDF
# ==========================================================


def get_report_pdf(
    db: Session,
    current_user: User,
    session_id: int,
) -> bytes:
    """
    Load the stored interview report and render it as a PDF.

    This function is purely a read operation.
    It does NOT call the AI.
    It does NOT write to the database.

    Workflow
    --------
    1. Load InterviewSession — verify ownership.
    2. Guard: status must be COMPLETED (HTTP 409 if not).
    3. Guard: report must be cached (HTTP 404 if not ready).
    4. Deserialise the stored report JSON.
    5. Build the questions payload for the PDF (text + answer only).
    6. Call generate_report_pdf() from pdf_generator.
    7. Return raw PDF bytes.

    Raises:
        HTTPException (404): session not found or not owned by user.
        HTTPException (409): interview not yet completed.
        HTTPException (404): report not yet generated.
        HTTPException (500): PDF rendering failed.
    """

    logger.info(
        "PDF report requested for session %s by user %s.",
        session_id,
        current_user.id,
    )

    # ----------------------------------------------------------
    # Step 1: Load session
    # get_interview_session joinloads questions + answers.
    # ----------------------------------------------------------

    interview_session = get_interview_session(
        db=db,
        session_id=session_id,
        current_user=current_user,
    )

    if interview_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=SESSION_NOT_FOUND_ERROR,
        )

    # ----------------------------------------------------------
    # Step 2: Guard — interview must be completed or timed out
    # ----------------------------------------------------------

    _report_allowed_statuses = {
        InterviewStatus.COMPLETED,
        InterviewStatus.TIMED_OUT,
    }
    if interview_session.status not in _report_allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=SESSION_NOT_COMPLETED_ERROR,
        )

    # ----------------------------------------------------------
    # Step 3: Guard — report must exist
    # ----------------------------------------------------------

    if not _report_is_cached(interview_session):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=REPORT_NOT_READY_ERROR,
        )

    # ----------------------------------------------------------
    # Step 4: Deserialise stored report JSON
    # ----------------------------------------------------------

    try:
        report_data = json.loads(interview_session.recommendations)
        ai_report = AIReportSchema.model_validate(report_data)

    except Exception as exc:
        logger.exception(
            "Failed to deserialise cached report for PDF (session %s).",
            session_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=REPORT_DESERIALISATION_ERROR,
        ) from exc

    # ----------------------------------------------------------
    # Step 5: Build questions payload
    # Only question text and candidate answer are included.
    # Per-question scores, strengths, weaknesses, ideal answers,
    # technical accuracy, communication, and confidence are
    # intentionally excluded — the final report summarises them.
    # ----------------------------------------------------------

    is_partial_session = interview_session.status == InterviewStatus.TIMED_OUT

    if is_partial_session:
        # Only include questions that were answered
        questions_payload = [
            {
                "order": q.question_order,
                "text": q.question,
                "answer": q.answer.answer,
            }
            for q in interview_session.questions
            if q.answer is not None
        ]
    else:
        questions_payload = [
            {
                "order": q.question_order,
                "text": q.question,
                "answer": q.answer.answer if q.answer is not None else None,
            }
            for q in interview_session.questions
        ]

    # ----------------------------------------------------------
    # Step 6: Render PDF in memory
    # ----------------------------------------------------------

    try:
        pdf_bytes = generate_report_pdf(
            title=interview_session.title,
            target_role=interview_session.target_role,
            interview_type=interview_session.interview_type.value,
            difficulty=interview_session.difficulty.value,
            overall_score=interview_session.overall_score,
            career_readiness=ai_report.career_readiness,
            completed_at=interview_session.completed_at,
            summary=ai_report.summary,
            strengths=ai_report.strengths,
            weaknesses=ai_report.weaknesses,
            recommendations=ai_report.recommendations,
            next_steps=ai_report.next_steps,
            questions=questions_payload,
            is_partial=is_partial_session,
        )

    except Exception as exc:
        logger.exception(
            "PDF rendering failed for session %s.",
            session_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to render interview report PDF.",
        ) from exc

    logger.info(
        "PDF rendered for session %s (%d bytes).",
        session_id,
        len(pdf_bytes),
    )

    # Step 7: Return bytes — the router wraps this in a Response
    return pdf_bytes


# ==========================================================
# TIMEOUT FINALIZATION
# ==========================================================


async def finalize_timeout(
    db: Session,
    current_user: User,
    session_id: int,
) -> InterviewTimeoutResponse:
    """
    Finalize a timed-out interview session.

    Called by the client when the countdown reaches zero.
    This is an idempotent operation — if the session has already
    been marked TIMED_OUT or COMPLETED, it returns success without
    repeating the AI report generation.

    Workflow
    --------
    1. Load session — verify ownership.
    2. If already COMPLETED or TIMED_OUT with a cached report → return OK.
    3. If IN_PROGRESS → mark TIMED_OUT, generate partial report from
       submitted answers only, persist, commit.
    4. Any other status → 409.
    """

    logger.info(
        "Timeout finalization requested for session %s by user %s.",
        session_id,
        current_user.id,
    )

    interview_session = get_interview_session(
        db=db,
        session_id=session_id,
        current_user=current_user,
    )

    if interview_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=SESSION_NOT_FOUND_ERROR,
        )

    # Already finalized — idempotent response
    if interview_session.status in (
        InterviewStatus.COMPLETED,
        InterviewStatus.TIMED_OUT,
    ):
        logger.info(
            "Session %s already finalized (status=%s). Returning OK.",
            session_id,
            interview_session.status,
        )
        return InterviewTimeoutResponse(
            message="Interview already finalized.",
            session_id=session_id,
        )

    if interview_session.status != InterviewStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=SESSION_NOT_ACTIVE_ERROR,
        )

    # Mark timed out
    now_utc = datetime.now(timezone.utc)
    interview_session.status = InterviewStatus.TIMED_OUT
    interview_session.completed_at = now_utc

    # Collect answered questions only
    answered_questions = [
        q for q in interview_session.questions if q.answer is not None
    ]

    try:
        if answered_questions:
            # Build a transcript from answered questions only
            transcript = _build_interview_transcript(
                interview_session=interview_session,
                only_answered=True,
            )

            _, resume_context = _load_resume_context(
                db=db,
                current_user=current_user,
            )

            report_prompt = build_report_prompt(
                resume_context=resume_context,
                target_role=interview_session.target_role,
                interview_type=interview_session.interview_type.value,
                difficulty=interview_session.difficulty.value,
                transcript=transcript,
            )

            report_raw = await generate_chat_response(messages=report_prompt)
            ai_report = _parse_ai_report(report_raw)

        else:
            # Zero answers — produce a minimal honest report without AI
            logger.warning(
                "Session %s timed out with zero answers — generating zero-answer report.",
                session_id,
            )
            ai_report = AIReportSchema(
                overall_score=0.0,
                summary=(
                    "This interview session ended before any answers were submitted. "
                    "No performance data is available."
                ),
                strengths=[],
                weaknesses=["No answers were submitted during the session."],
                recommendations=(
                    "Please attempt the interview again and submit answers "
                    "for each question to receive a meaningful evaluation."
                ),
                career_readiness="Unable to assess — no answers provided.",
                next_steps=["Retry the interview and answer each question."],
            )

        full_report_json = json.dumps(
            ai_report.model_dump(),
            ensure_ascii=False,
        )

        interview_session.overall_score = ai_report.overall_score
        interview_session.summary = ai_report.summary
        interview_session.recommendations = full_report_json

        update_session(db=db, session=interview_session)
        db.commit()

        logger.info(
            "Session %s finalized as TIMED_OUT with report.",
            session_id,
        )

        return InterviewTimeoutResponse(
            message="Interview finalized due to timeout.",
            session_id=session_id,
        )

    except ChatClientError as exc:
        db.rollback()
        logger.exception(
            "AI call failed during timeout finalization for session %s.", session_id
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to generate partial report. Please try again.",
        ) from exc

    except HTTPException:
        db.rollback()
        raise

    except Exception as exc:
        db.rollback()
        logger.exception("Unexpected error during timeout finalization.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to finalize interview.",
        ) from exc