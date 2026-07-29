"""HTTP endpoints for the resume domain."""

from pathlib import Path
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.db.database import get_db
from app.resumes.schema import ResumeListResponse, ResumeResponse
from app.resumes.service import (
    delete_resume,
    get_resume_by_id,
    get_user_resumes,
    save_resume_upload,
)
from app.users.model import User


router = APIRouter(prefix="/resumes", tags=["Resumes"])

ALLOWED_EXTENSIONS = {".pdf", ".docx"}


@router.post(
    "/upload",
    response_model=ResumeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_resume(
    file: Annotated[UploadFile, File(description="A PDF or DOCX resume file")],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ResumeResponse:
    """Upload a resume for the authenticated user."""

    original_filename = file.filename or ""
    extension = Path(original_filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        await file.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .pdf and .docx files are allowed.",
        )

    resume = await save_resume_upload(
        db=db,
        file=file,
        original_filename=original_filename,
        extension=extension,
        user_id=current_user.id,
    )

    return ResumeResponse.model_validate(resume)


@router.get(
    "/",
    response_model=list[ResumeListResponse],
    status_code=status.HTTP_200_OK,
)
def list_resumes(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[ResumeListResponse]:
    """Return all resumes belonging to the authenticated user."""

    resumes = get_user_resumes(
        db=db,
        user_id=current_user.id,
    )

    return [
        ResumeListResponse.model_validate(resume)
        for resume in resumes
    ]


@router.get(
    "/{resume_id}",
    response_model=ResumeResponse,
    status_code=status.HTTP_200_OK,
)
def get_resume(
    resume_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ResumeResponse:
    """Return a single resume belonging to the authenticated user."""

    resume = get_resume_by_id(
        db=db,
        resume_id=resume_id,
        user_id=current_user.id,
    )

    return ResumeResponse.model_validate(resume)


@router.delete(
    "/{resume_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_resume(
    resume_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    """Delete a resume belonging to the authenticated user."""

    delete_resume(
        db=db,
        resume_id=resume_id,
        user_id=current_user.id,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)