"""PDF text and metadata extraction using PyMuPDF (fitz)."""

import logging
from dataclasses import dataclass
from pathlib import Path

import pymupdf  # PyMuPDF (the `fitz` import alias is deprecated)

from app.core.exceptions import FileProcessingError
from app.utils.text_cleaner import clean_extracted_text

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExtractedPdf:
    """Result of extracting text and metadata from a PDF file."""

    title: str
    page_count: int
    text: str


def extract_pdf(file_path: Path, *, fallback_title: str) -> ExtractedPdf:
    """Extract cleaned text and metadata from a PDF file on disk.

    Args:
        file_path: Path to the PDF file.
        fallback_title: Title to use if the PDF has no metadata title
            (typically the original uploaded filename without extension).

    Returns:
        An ExtractedPdf with the document's title, page count, and cleaned
        full text (pages joined with a page-break marker).

    Raises:
        FileProcessingError: If the file cannot be opened as a valid PDF,
            or contains zero pages.
    """
    try:
        with pymupdf.open(file_path) as pdf:
            if pdf.page_count == 0:
                raise FileProcessingError("The PDF contains no pages.")

            page_texts = [page.get_text("text") for page in pdf]
            metadata_title = (pdf.metadata or {}).get("title", "").strip()
            page_count = pdf.page_count
    except FileProcessingError:
        raise
    except Exception as exc:  # noqa: BLE001 - any PyMuPDF failure means an invalid/corrupt PDF
        logger.warning("Failed to open PDF %s: %s", file_path, exc)
        raise FileProcessingError(
            "The uploaded file could not be read as a valid PDF."
        ) from exc

    raw_text = "\n\n".join(page_texts)
    cleaned_text = clean_extracted_text(raw_text)
    title = metadata_title or fallback_title

    return ExtractedPdf(title=title, page_count=page_count, text=cleaned_text)
