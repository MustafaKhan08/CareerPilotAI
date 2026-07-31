"""
HTTP endpoints for persisted resume analyses.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.analyses.schema import (
    ResumeAnalysisResponse,
    ResumeAnalysisSummary,
)
from app.analyses.service import (
    delete_analysis,
    delete_resume_analyses,
    get_analysis_by_id,
    get_analysis_summaries,
    latest_analysis_response,
    to_response,
)
from app.auth.security import get_current_user
from app.db.database import get_db
from app.resumes.service import get_resume_by_id
from app.users.model import User

router = APIRouter(
    prefix="/analyses",
    tags=["Analyses"],
)


@router.get(
    "/resumes/{resume_id}",
    response_model=list[ResumeAnalysisSummary],
    status_code=status.HTTP_200_OK,
)
def list_resume_analyses(
    resume_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[ResumeAnalysisSummary]:
    """Return the analysis history for an authenticated user's resume."""

    get_resume_by_id(
        db=db,
        resume_id=resume_id,
        user_id=current_user.id,
    )

    return get_analysis_summaries(
        db=db,
        resume_id=resume_id,
    )


@router.get(
    "/resumes/{resume_id}/latest",
    response_model=ResumeAnalysisResponse,
    status_code=status.HTTP_200_OK,
)
def get_latest_resume_analysis(
    resume_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ResumeAnalysisResponse:
    """Return the latest analysis for an authenticated user's resume."""

    get_resume_by_id(
        db=db,
        resume_id=resume_id,
        user_id=current_user.id,
    )

    analysis = latest_analysis_response(
        db=db,
        resume_id=resume_id,
    )

    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found.",
        )

    return analysis


@router.delete(
    "/resumes/{resume_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_resume_analyses(
    resume_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    """Delete every analysis for an authenticated user's resume."""

    get_resume_by_id(
        db=db,
        resume_id=resume_id,
        user_id=current_user.id,
    )

    delete_resume_analyses(
        db=db,
        resume_id=resume_id,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{analysis_id}",
    response_model=ResumeAnalysisResponse,
    status_code=status.HTTP_200_OK,
)
def get_analysis(
    analysis_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ResumeAnalysisResponse:
    """Return an analysis belonging to the authenticated user."""

    analysis = get_analysis_by_id(
        db=db,
        analysis_id=analysis_id,
    )

    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found.",
        )

    get_resume_by_id(
        db=db,
        resume_id=analysis.resume_id,
        user_id=current_user.id,
    )

    return to_response(analysis)

@router.delete(
    "/{analysis_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_analysis(
    analysis_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    """Delete an analysis belonging to the authenticated user."""

    analysis = get_analysis_by_id(
        db=db,
        analysis_id=analysis_id,
    )

    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found.",
        )

    get_resume_by_id(
        db=db,
        resume_id=analysis.resume_id,
        user_id=current_user.id,
    )

    if not delete_analysis(
        db=db,
        analysis_id=analysis_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found.",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)