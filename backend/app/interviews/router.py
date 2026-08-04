"""HTTP endpoints for the Interview Preparation module."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.db.database import get_db
from app.interviews.schema import (
    InterviewSessionStartResponse,
    InterviewStartRequest,
)
from app.interviews.service import start_interview
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

    Requires:
    - An uploaded resume (HTTP 404 if missing).
    - A completed resume analysis (HTTP 404 if missing).

    Returns the first AI-generated interview question.
    """

    return await start_interview(
        db=db,
        current_user=current_user,
        request=request,
    )
