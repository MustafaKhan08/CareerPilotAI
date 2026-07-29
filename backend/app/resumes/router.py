"""HTTP endpoints for the resume domain."""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.db.database import get_db
from app.resumes.schema import ResumeResponse
from app.resumes.service import save_resume_upload
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


@router.get("/")
def list_resumes():
    return {"message": "Resume listing endpoint is not implemented yet."}


@router.get("/{resume_id}")
def get_resume(resume_id: int):
    return {"message": "Resume retrieval endpoint is not implemented yet."}


@router.delete("/{resume_id}")
def remove_resume(resume_id: int):
    return {"message": "Resume deletion endpoint is not implemented yet."}