"""
OCR utility helpers.

Responsibilities
----------------
- Detect whether a PDF already contains sufficient readable text.
- Convert PDF pages to numpy images for OCR using pypdfium2.

No OCR logic should exist here.
No business logic should exist here.
"""

from __future__ import annotations

import logging
from pathlib import Path

import re
import numpy as np
import pdfplumber

logger = logging.getLogger(__name__)


# ==========================================================
# Constants
# ==========================================================

# Minimum number of non-whitespace characters required for a
# PDF to be considered a text-based document.
# PDFs below this threshold are treated as scanned images.
OCR_SUFFICIENCY_THRESHOLD = 50


# ==========================================================
# Text Sufficiency
# ==========================================================


def has_sufficient_text(text: str) -> bool:
    """
    Return True if the supplied text contains enough readable
    content to bypass OCR.

    Uses non-whitespace character count so that PDFs with only
    whitespace or line breaks are still treated as scanned.
    """

    return len("".join(text.split())) >= OCR_SUFFICIENCY_THRESHOLD


# ==========================================================
# PDF Text Extraction (non-raising)
# ==========================================================


def attempt_pdf_text_extraction(file_path: Path) -> str:
    """
    Attempt to extract all text from a PDF using pdfplumber.

    Unlike the extraction layer's pdf_extractor, this function
    NEVER raises. It returns an empty string on failure or when
    the PDF contains no selectable text (i.e. scanned pages).

    The caller decides whether the result is sufficient.

    Returns
    -------
    str
        Extracted text, possibly empty.
    """

    try:
        page_texts: list[str] = []

        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()

                if text and text.strip():
                    page_texts.append(text.strip())

        return "\n".join(page_texts).strip()

    except Exception:
        logger.warning(
            "pdfplumber could not extract text from %s.",
            file_path.name,
        )
        return ""


# ==========================================================
# PDF → Image Conversion
# ==========================================================


def render_pdf_pages_to_images(file_path: Path) -> list[np.ndarray]:
    """
    Render every page of a PDF to a numpy image array.

    Uses pypdfium2 (already installed) to rasterise each page at
    2× scale for improved OCR accuracy.

    Returns
    -------
    list[np.ndarray]
        One numpy array per page, in RGB format, ordered by page number.
        Returns an empty list if rendering fails.
    """

    try:
        import pypdfium2  # type: ignore[import]

        images: list[np.ndarray] = []

        pdf = pypdfium2.PdfDocument(str(file_path))

        try:
            for page_index in range(len(pdf)):
                page = pdf[page_index]

                # Render at 2× scale (≈144 DPI equivalent) for OCR accuracy.
                bitmap = page.render(scale=2)
                pil_image = bitmap.to_pil()
                images.append(np.array(pil_image))

        finally:
            pdf.close()

        return images

    except Exception:
        logger.exception(
            "Failed to render PDF pages to images for %s.",
            file_path.name,
        )
        return []
