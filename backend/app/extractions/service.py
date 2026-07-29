"""Resume text extraction service."""

from pathlib import Path

from fastapi import HTTPException, status

from app.extractions.docx_extractor import extract_docx_text
from app.extractions.pdf_extractor import extract_pdf_text


def extract_resume_text(file_path: Path) -> str:
    """
    Extract text from a supported resume file.
    """

    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        text = extract_pdf_text(file_path)

    elif suffix == ".docx":
        text = extract_docx_text(file_path)

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported resume format.",
        )

    if not text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No readable text found in the uploaded resume.",
        )

    return text