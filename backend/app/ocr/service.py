"""
OCR service for CareerPilotAI.

Responsibilities
----------------
- Initialise the EasyOCR reader once during application startup.
- Expose OCR extraction for scanned PDF files.
- Release the reader during application shutdown.

The EasyOCR model is loaded exactly once via the FastAPI lifespan
manager in app/main.py and shared across all requests.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

from app.ocr.utils import render_pdf_pages_to_images

logger = logging.getLogger(__name__)


class OcrEngine:
    """
    Thin wrapper around EasyOCR that follows the same
    load() / unload() lifecycle pattern used by the
    SimilarityEngine throughout this project.

    An instance is created at module level and initialised
    once during FastAPI startup — never per-request.
    """

    def __init__(self) -> None:
        self._reader: object | None = None
        self._loaded: bool = False

    # ----------------------------------------------------------
    # Lifecycle
    # ----------------------------------------------------------

    def load(self) -> None:
        """
        Load the EasyOCR reader into memory.

        Called once from the FastAPI lifespan manager during startup.
        Subsequent calls are no-ops.
        """

        if self._loaded:
            return

        logger.info("Loading EasyOCR model...")

        try:
            import easyocr  # type: ignore[import]

            # gpu=False ensures CPU-only inference, which is safe in
            # all deployment environments without a CUDA GPU.
            # verbose=False suppresses EasyOCR's internal progress bars.
            self._reader = easyocr.Reader(
                ["en"],
                gpu=False,
                verbose=False,
            )

            self._loaded = True
            logger.info("EasyOCR model loaded successfully.")

        except Exception:
            logger.exception("Failed to load EasyOCR model.")
            raise

    def unload(self) -> None:
        """
        Release the EasyOCR reader from memory.

        Called from the FastAPI lifespan manager during shutdown.
        """

        self._reader = None
        self._loaded = False
        logger.info("EasyOCR model unloaded.")

    # ----------------------------------------------------------
    # Private
    # ----------------------------------------------------------

    def _ensure_loaded(self) -> None:
        """
        Guard that raises if the engine has not been initialised.

        This protects against accidental calls before startup
        or after shutdown.
        """

        if not self._loaded or self._reader is None:
            raise RuntimeError(
                "OcrEngine is not loaded. "
                "Ensure ocr_engine.load() is called during application startup."
            )

    def _run_reader(self, image: np.ndarray) -> str:
        """
        Run EasyOCR on a single numpy image array.

        Parameters
        ----------
        image:
            A numpy RGB array of one rendered PDF page.

        Returns
        -------
        str
            Concatenated text extracted from the image.
        """

        self._ensure_loaded()

        # easyocr.Reader.readtext returns a list of (bbox, text, confidence)
        # tuples when detail=1, or just text strings when detail=0.
        # paragraph=True merges nearby words into coherent lines.
        results: list[str] = self._reader.readtext(  # type: ignore[union-attr]
            image,
            detail=0,
            paragraph=True,
        )

        return "\n".join(results)

    # ----------------------------------------------------------
    # Public OCR operations
    # ----------------------------------------------------------

    def extract_from_pdf(self, file_path: Path) -> str:
        """
        Run OCR on every page of a scanned PDF.

        Each page is rasterised to a numpy image using pypdfium2
        and then processed by EasyOCR individually. All page
        texts are concatenated and returned.

        Parameters
        ----------
        file_path:
            Absolute path to the PDF file.

        Returns
        -------
        str
            Merged text from all pages, possibly empty.
        """

        logger.info("Running OCR on scanned PDF: %s", file_path.name)

        images = render_pdf_pages_to_images(file_path)

        logger.info(
            "Rendered %d page(s) for OCR.",
            len(images),
        )

        if not images:
            logger.warning(
                "No pages could be rendered from PDF: %s",
                file_path.name,
            )
            return ""

        page_texts: list[str] = []

        for page_number, image in enumerate(images, start=1):

            try:
                page_text = self._run_reader(image)

                if page_text and page_text.strip():
                    page_texts.append(page_text.strip())

                logger.info(
                    "OCR page %d/%d complete (%d chars).",
                    page_number,
                    len(images),
                    len(page_text),
                )

            except Exception:
                logger.exception(
                    "OCR failed for page %d of %s.",
                    page_number,
                    file_path.name,
                )

        merged_text = "\n".join(page_texts)
        char_count = len(merged_text.replace(" ", "").replace("\n", ""))

        logger.info(
            "OCR extracted %d characters from %d page(s) of %s.",
            char_count,
            len(images),
            file_path.name,
        )

        return merged_text


# ==========================================================
# Shared OCR Engine
# ==========================================================

# Single shared instance used throughout the application.
# The EasyOCR model is loaded once during FastAPI startup
# via ocr_engine.load() in app/main.py.
ocr_engine = OcrEngine()
