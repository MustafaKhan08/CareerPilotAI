"""Database operations for persisted resume metadata."""

from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.extractions.service import extract_resume_text
from app.resumes.model import Resume
from app.resumes.schema import ResumeCreate


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESUME_UPLOAD_DIRECTORY = PROJECT_ROOT / "uploads" / "resumes"
UPLOAD_CHUNK_SIZE = 1024 * 1024


def create_resume(
    db: Session,
    resume_data: ResumeCreate,
    uploaded_file_path: Path | None = None,
) -> Resume:
    """Commit resume metadata and remove its file if the commit fails."""

    resume = Resume(**resume_data.model_dump())
    db.add(resume)

    try:
        db.commit()

    except Exception:
        db.rollback()

        if uploaded_file_path is not None:
            try:
                uploaded_file_path.unlink(missing_ok=True)
            except OSError:
                pass

        raise

    db.refresh(resume)
    return resume


async def save_resume_upload(
    db: Session,
    file: UploadFile,
    original_filename: str,
    extension: str,
    user_id: int,
) -> Resume:
    """Save a resume file, extract its text, and persist its metadata."""

    destination: Path | None = None

    try:
        RESUME_UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)

        stored_filename = f"{uuid4().hex}{extension}"
        destination = RESUME_UPLOAD_DIRECTORY / stored_filename

        with destination.open("wb") as output_file:
            while chunk := await file.read(UPLOAD_CHUNK_SIZE):
                output_file.write(chunk)

    except OSError as error:
        if destination is not None:
            try:
                destination.unlink(missing_ok=True)
            except OSError:
                pass

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save uploaded file.",
        ) from error

    finally:
        await file.close()

    try:
        extracted_text = extract_resume_text(destination)

    except HTTPException:
        if destination is not None:
            try:
                destination.unlink(missing_ok=True)
            except OSError:
                pass
        raise

    upload_path = destination.relative_to(PROJECT_ROOT).as_posix()

    resume_data = ResumeCreate(
        user_id=user_id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_path=upload_path,
        file_type=extension.lstrip("."),
        extracted_text=extracted_text,
    )

    return create_resume(
        db=db,
        resume_data=resume_data,
        uploaded_file_path=destination,
    )


def get_user_resumes(
    db: Session,
    user_id: int,
) -> list[Resume]:
    """Return all resumes belonging to the authenticated user."""

    return (
        db.query(Resume)
        .filter(Resume.user_id == user_id)
        .order_by(Resume.created_at.desc())
        .all()
    )


def get_resume_by_id(
    db: Session,
    resume_id: int,
    user_id: int,
) -> Resume:
    """Return a single resume belonging to the authenticated user."""

    resume = (
        db.query(Resume)
        .filter(
            Resume.id == resume_id,
            Resume.user_id == user_id,
        )
        .first()
    )

    if resume is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found.",
        )

    return resume


def delete_resume(
    db: Session,
    resume_id: int,
    user_id: int,
) -> None:
    """Delete a user's resume and its uploaded file."""

    resume = get_resume_by_id(
        db=db,
        resume_id=resume_id,
        user_id=user_id,
    )

    file_path = PROJECT_ROOT / resume.file_path

    try:
        file_path.unlink(missing_ok=True)
    except OSError:
        pass

    db.delete(resume)
    db.commit()