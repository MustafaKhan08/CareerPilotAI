"""
HTTP endpoints for AI-powered resume analysis.
"""

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.analyses.schema import ResumeAnalysisResponse
from app.analyses.service import (
    cached_analysis_exists,
    get_cached_analysis,
    save_ai_analysis,
    should_use_cache,
    to_response,
)
from app.ai.service import ai_service
from app.auth.security import get_current_user
from app.core.config import settings
from app.db.database import get_db
from app.resumes.service import get_resume_by_id
from app.users.model import User

router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)


@router.post(
    "/resumes/{resume_id}/analyze",
    response_model=ResumeAnalysisResponse,
    status_code=status.HTTP_200_OK,
)
async def analyze_resume(
    resume_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    regenerate: bool = False,
) -> ResumeAnalysisResponse:
    """
    Validate, analyze, and persist a previously uploaded resume.

    Workflow:   
        1. Retrieve the authenticated user's resume.
        2. Return its cached analysis when available.
        3. Validate that the uploaded document is a resume.
        4. Otherwise, perform and persist a new ATS analysis.
    """

    # Retrieve the user's resume
    resume = get_resume_by_id(
        db=db,
        resume_id=resume_id,
        user_id=current_user.id,
    )

    # Keep regeneration disabled until query-parameter support is added.
    cached_exists = cached_analysis_exists(
        db=db,
        resume_id=resume.id,
    )

    if should_use_cache(
        regenerate=regenerate,
        cached_exists=cached_exists,
    ):
        cached_analysis = get_cached_analysis(
            db=db,
            resume_id=resume.id,
        )

        if cached_analysis is not None:
            return to_response(cached_analysis)

    # Validate the extracted resume text
    validation = await ai_service.validate_resume(
        resume_text=resume.extracted_text,
    )

    # Reject non-resume documents
    if not validation.is_resume:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation.reason,
        )

    # Perform ATS analysis
    analysis = await ai_service.analyze_resume(
        resume_text=resume.extracted_text,
    )

    saved_analysis = save_ai_analysis(
        db=db,
        resume_id=resume.id,
        ai_response=analysis,
        provider="OpenRouter",
        model_name=settings.ai_models[0],
        model_version=None,
        prompt_version="v1",
        processing_time_ms=None,
    )

    return to_response(saved_analysis)