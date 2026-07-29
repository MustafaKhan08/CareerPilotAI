"""DOCX text extraction utilities."""

from pathlib import Path

from docx import Document
from fastapi import HTTPException, status


def extract_docx_text(file_path: Path) -> str:
    """
    Extract text from a DOCX document.

    Empty paragraphs are ignored. Raises an HTTPException if extraction
    fails or if no extractable text is found.
    """

    try:
        document = Document(file_path)

        extracted_text = "\n".join(
            paragraph.text.strip()
            for paragraph in document.paragraphs
            if paragraph.text.strip()
        ).strip()

        if not extracted_text:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No extractable text found in the DOCX file.",
            )

        return extracted_text

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to extract text from DOCX file.",
        ) from error    