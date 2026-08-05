"""HTTP endpoints for the Interview Preparation module."""

import re
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.db.database import get_db
from app.interviews.schema import (
    InterviewAnswerRequest,
    InterviewEvaluationResponse,
    InterviewReportResponse,
    InterviewSessionStartResponse,
    InterviewStartRequest,
)
from app.interviews.service import (
    get_or_generate_report,
    get_report_pdf,
    start_interview,
    submit_answer,
)
from app.users.model import User

router = APIRouter(
    prefix="/interviews",
    tags=["Interviews"],
)


# ==========================================================
# START INTERVIEW
# ==========================================================


@router.post(
    "/start",
    response_model=InterviewSessionStartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new interview session",
    description=(
        "Creates a new interview session for the authenticated user "
        "using their latest uploaded resume and resume analysis. "
        "Generates and returns the first interview question."
    ),
)
async def start_interview_endpoint(
    request: InterviewStartRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> InterviewSessionStartResponse:
    """
    Start a new interview session.

    - HTTP 404: resume not uploaded.
    - HTTP 404: resume not yet analyzed.
    """

    return await start_interview(
        db=db,
        current_user=current_user,
        request=request,
    )


# ==========================================================
# SUBMIT ANSWER
# ==========================================================


@router.post(
    "/{session_id}/answer",
    response_model=InterviewEvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit an answer to the current interview question",
    description=(
        "Evaluates the candidate's answer using AI, persists the result, "
        "and returns the evaluation. If more questions remain, the next "
        "question is generated and included in the response. "
        "When the final question is answered, the interview is marked as completed."
    ),
)
async def submit_answer_endpoint(
    session_id: int,
    request: InterviewAnswerRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> InterviewEvaluationResponse:
    """
    Submit an answer to the current interview question.

    - HTTP 404: session not found or not owned by user.
    - HTTP 404: no active question found.
    - HTTP 409: session is not in progress.
    - HTTP 409: question has already been answered.
    - HTTP 502: AI evaluation or question generation failed.
    """

    return await submit_answer(
        db=db,
        current_user=current_user,
        session_id=session_id,
        candidate_answer=request.answer,
    )


# ==========================================================
# FINAL REPORT
# ==========================================================


@router.get(
    "/{session_id}/report",
    response_model=InterviewReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Get the final interview report",
    description=(
        "Returns the final AI-generated report for a completed interview session. "
        "If the report has already been generated, the cached version is returned "
        "immediately without calling the AI again. "
        "If the report has not yet been generated, it is generated now, "
        "persisted, and returned. "
        "The interview must be fully completed before this endpoint is available."
    ),
)
async def get_report_endpoint(
    session_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> InterviewReportResponse:
    """
    Get the final interview report.

    - HTTP 404: session not found or not owned by user.
    - HTTP 409: interview is not yet completed.
    - HTTP 404: report not yet generated.
    """

    return await get_or_generate_report(
        db=db,
        current_user=current_user,
        session_id=session_id,
    )


# ==========================================================
# REPORT PDF DOWNLOAD
# ==========================================================


def _safe_filename(title: str, session_id: int) -> str:
    """
    Derive a safe ASCII filename from the interview title.

    Replaces any character that is not alphanumeric, a hyphen,
    or an underscore with an underscore, then appends the
    session ID so the name is always unique.
    """
    slug = re.sub(r"[^\w\-]", "_", title).strip("_")
    slug = re.sub(r"_+", "_", slug)
    return f"interview_report_{slug}_{session_id}.pdf"


@router.get(
    "/{session_id}/report/pdf",
    status_code=status.HTTP_200_OK,
    summary="Download the final interview report as a PDF",
    description=(
        "Renders and returns the final interview report as a downloadable PDF file. "
        "The interview must be completed and the report must already exist. "
        "No AI calls are made — only stored data is used."
    ),
    response_class=Response,
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "PDF file download.",
        },
        404: {"description": "Session not found or report not yet generated."},
        409: {"description": "Interview not yet completed."},
        500: {"description": "PDF rendering failed."},
    },
)
def get_report_pdf_endpoint(
    session_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    """
    Download the final interview report as a PDF.

    - HTTP 404: session not found or not owned by user.
    - HTTP 409: interview not yet completed.
    - HTTP 404: report not yet generated.
    - HTTP 500: PDF rendering failed.
    """

    pdf_bytes = get_report_pdf(
        db=db,
        current_user=current_user,
        session_id=session_id,
    )

    filename = _safe_filename(
        title="interview",
        session_id=session_id,
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )
