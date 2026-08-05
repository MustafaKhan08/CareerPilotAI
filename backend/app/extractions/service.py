"""Resume text extraction service."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import HTTPException, status

from app.extractions.docx_extractor import extract_docx_text
from app.ocr.service import ocr_engine
from app.ocr.utils import (
    attempt_pdf_text_extraction,
    has_sufficient_text,
)

logger = logging.getLogger(__name__)


def extract_resume_text(file_path: Path) -> str:
    """
    Extract text from a supported resume file.

    Supported formats
    -----------------
    - PDF  (text-based or scanned)
    - DOCX

    OCR Fallback
    ------------
    For PDFs, normal text extraction is attempted first.
    If the extracted text is insufficient (scanned PDF),
    OCR is performed automatically using EasyOCR.

    Raises
    ------
    HTTPException (400)
        Unsupported file format.
    HTTPException (422)
        No readable text could be extracted from the file.
    """

    suffix = file_path.suffix.lower()

    # ----------------------------------------------------------
    # DOCX — existing extractor, no changes
    # ----------------------------------------------------------

    if suffix == ".docx":
        logger.info("DOCX resume detected: %s", file_path.name)
        return extract_docx_text(file_path)

    # ----------------------------------------------------------
    # PDF — attempt normal extraction, OCR fallback if needed
    # ----------------------------------------------------------

    if suffix == ".pdf":
        logger.info("PDF resume detected: %s", file_path.name)

        extracted_text = attempt_pdf_text_extraction(file_path)

        if has_sufficient_text(extracted_text):
            logger.info(
                "Text PDF detected. Skipping OCR for %s.",
                file_path.name,
            )
            return extracted_text

        # Insufficient text — treat as a scanned PDF
        logger.info(
            "Scanned PDF detected. Running OCR on %s.",
            file_path.name,
        )

        ocr_text = ocr_engine.extract_from_pdf(file_path)

        if not ocr_text or not ocr_text.strip():
            logger.warning(
                "OCR failed to extract readable text from %s.",
                file_path.name,
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No readable text found in the uploaded resume.",
            )

        logger.info(
            "OCR completed successfully for %s (%d characters).",
            file_path.name,
            len(ocr_text),
        )
        return ocr_text

    # ----------------------------------------------------------
    # Unsupported format
    # ----------------------------------------------------------

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Unsupported resume format.",
    )