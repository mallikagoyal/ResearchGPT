"""Text cleaning utilities applied to raw PDF-extracted text before storage
and, later, before chunking/embedding.
"""

import re
import unicodedata

# Matches 3+ consecutive blank lines (allowing trailing whitespace).
_MULTI_BLANK_LINE_RE = re.compile(r"\n\s*\n\s*\n+")
# Matches runs of horizontal whitespace (spaces/tabs), collapsing to one space.
_MULTI_SPACE_RE = re.compile(r"[ \t]{2,}")
# Control characters (except newline/tab) that sometimes leak from PDF text layers.
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def clean_extracted_text(raw_text: str) -> str:
    """Normalize raw text extracted from a PDF.

    Applies, in order:
    1. Unicode normalization (NFKC) so visually-identical characters compare equal.
    2. Removal of null bytes and other non-printable control characters.
    3. Collapsing repeated horizontal whitespace.
    4. Collapsing 3+ blank lines down to a single blank line.
    5. Trimming leading/trailing whitespace.

    Args:
        raw_text: The unprocessed text extracted from a PDF page.

    Returns:
        Cleaned text, safe to store and later chunk.
    """
    if not raw_text:
        return ""

    text = unicodedata.normalize("NFKC", raw_text)
    text = _CONTROL_CHAR_RE.sub("", text)
    text = _MULTI_SPACE_RE.sub(" ", text)
    text = _MULTI_BLANK_LINE_RE.sub("\n\n", text)
    return text.strip()
