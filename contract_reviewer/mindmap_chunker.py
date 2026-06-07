"""Structure-aware chunking for legal documents.

The contract-review pipeline splits text on a raw character budget. That is
fine for "scan every paragraph" review, but for building a *process* mind map
we want each chunk to keep whole articles/sections together so the model can
see a procedural step from start to finish. This module reuses the paragraph
blocks produced by ``docx_reader``/``document_reader`` and groups them on
article/heading boundaries, only falling back to a hard character split when a
single section is larger than the budget.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .docx_reader import DocumentStructure

# Matches the start of a legal article/section in the languages this firm works
# in (English + Serbian/Balkan legal drafting), plus generic numbered headings.
_HEADING_PATTERNS = [
    r"^\s*(article|art\.?)\s+\d+",          # Article 12 / Art. 12
    r"^\s*(member|section|sec\.?)\s+\d+",    # Section 4
    r"^\s*(\u010dlan|clan)\s+\d+",          # Član 12 / Clan 12 (Serbian)
    r"^\s*(odeljak|poglavlje|deo)\s+\d+",    # Odeljak / Poglavlje / Deo (Serbian)
    r"^\s*\u00a7\s*\d+",                     # § 12
    r"^\s*\d+(\.\d+)*\.?\s+\S",              # 12.  /  3.2.1  numbered headings
]
_HEADING_RE = re.compile("|".join(_HEADING_PATTERNS), re.IGNORECASE)


@dataclass
class Chunk:
    """A contiguous slice of the document with the section headings it covers."""

    index: int
    text: str
    headings: list[str]


def is_heading(paragraph: str) -> bool:
    """True if the paragraph looks like the start of an article/section."""
    text = paragraph.strip()
    if not text or len(text) > 200:
        return False
    return bool(_HEADING_RE.match(text))


def _hard_split(text: str, max_chars: int) -> list[str]:
    """Split an oversized single section, preferring sentence/newline breaks."""
    pieces: list[str] = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + max_chars, length)
        if end < length:
            window_start = start + max_chars // 2
            break_at = max(
                text.rfind("\n", window_start, end),
                text.rfind(". ", window_start, end),
            )
            if break_at > window_start:
                end = break_at + 1
        pieces.append(text[start:end].strip())
        start = end
    return [p for p in pieces if p]


def chunk_structure(
    structure: DocumentStructure,
    max_chars: int,
    *,
    overlap_chars: int = 0,
) -> list[Chunk]:
    """Group paragraph blocks into chunks that respect article boundaries.

    A new chunk is started when adding the next paragraph would exceed
    ``max_chars`` AND that paragraph begins a new article/section, so steps that
    belong together stay together. ``overlap_chars`` carries the tail of the
    previous chunk into the next one to preserve cross-section context.
    """
    paragraphs = [b.text for b in structure.blocks if b.text.strip()]
    if not paragraphs:
        return []

    chunks: list[Chunk] = []
    buf: list[str] = []
    buf_headings: list[str] = []
    buf_len = 0

    def flush() -> None:
        nonlocal buf, buf_headings, buf_len
        if not buf:
            return
        text = "\n\n".join(buf).strip()
        if len(text) > max_chars * 1.5:
            for piece in _hard_split(text, max_chars):
                chunks.append(Chunk(index=len(chunks), text=piece, headings=buf_headings))
        else:
            chunks.append(Chunk(index=len(chunks), text=text, headings=buf_headings))
        buf, buf_headings, buf_len = [], [], 0

    for para in paragraphs:
        para_len = len(para) + 2
        starts_section = is_heading(para)
        if buf and buf_len + para_len > max_chars and starts_section:
            tail = ""
            if overlap_chars > 0:
                joined = "\n\n".join(buf)
                tail = joined[-overlap_chars:]
            flush()
            if tail:
                buf.append(tail)
                buf_len += len(tail) + 2
        buf.append(para)
        buf_len += para_len
        if starts_section:
            buf_headings.append(para.strip())

    flush()
    return chunks
