"""Read supported documents into the shared DocumentStructure used for chunking.

Reuses the .docx run-level reader from ``docx_reader`` and adds plain-text
support so the mind-map feature can accept the document formats a lawyer is
most likely to have on hand without pulling in heavy dependencies.
"""

from __future__ import annotations

from pathlib import Path

from .docx_reader import DocumentStructure, ParagraphBlock, extract_runs

SUPPORTED_SUFFIXES: frozenset[str] = frozenset({".docx", ".txt", ".md", ".pdf"})


def _structure_from_text(text: str) -> DocumentStructure:
    """Build a DocumentStructure from raw text, splitting on blank lines.

    Runs are intentionally left empty: the mind-map flow only needs the
    paragraph text and ordering, not the run-level anchors that the .docx
    annotator relies on.
    """
    blocks: list[ParagraphBlock] = []
    paragraph_index = 0
    for raw_block in text.replace("\r\n", "\n").split("\n"):
        stripped = raw_block.strip()
        if not stripped:
            continue
        blocks.append(
            ParagraphBlock(paragraph_index=paragraph_index, text=stripped, runs=[])
        )
        paragraph_index += 1
    full_text = "\n\n".join(b.text for b in blocks)
    return DocumentStructure(blocks=blocks, full_text=full_text)


def _text_from_pdf(path: Path) -> str:
    """Extract text from a PDF, page by page, in document order.

    PDF text has no reliable paragraph structure, so we keep pypdf's line
    breaks and let the chunker re-group them on article/heading boundaries.
    """
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages = [(page.extract_text() or "").strip() for page in reader.pages]
    return "\n".join(p for p in pages if p)


def read_document(doc_path: str | Path) -> DocumentStructure:
    """Read a supported document into a DocumentStructure.

    Raises ValueError for unsupported file types so callers can surface a
    friendly message in the UI.
    """
    path = Path(doc_path)
    suffix = path.suffix.lower()
    if suffix == ".docx":
        return extract_runs(str(path))
    if suffix in {".txt", ".md"}:
        return _structure_from_text(path.read_text(encoding="utf-8", errors="replace"))
    if suffix == ".pdf":
        return _structure_from_text(_text_from_pdf(path))
    raise ValueError(
        f"Unsupported document type '{suffix}'. "
        f"Supported types: {', '.join(sorted(SUPPORTED_SUFFIXES))}."
    )
