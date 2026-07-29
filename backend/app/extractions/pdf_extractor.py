"""PDF text extraction utilities."""

from pathlib import Path

import pdfplumber
from fastapi import HTTPException, status


def extract_pdf_text(file_path: Path) -> str:
    """
    Extract text from every page of a PDF.

    Empty pages are ignored. Raises an HTTPException if extraction fails
    or if no extractable text is found.
    """

    try:
        page_texts: list[str] = []

        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()

                if text and text.strip():
                    page_texts.append(text.strip())

        extracted_text = "\n".join(page_texts).strip()

        if not extracted_text:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No extractable text found in the PDF.",
            )

        return extracted_text

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to extract text from PDF file.",
        ) from error