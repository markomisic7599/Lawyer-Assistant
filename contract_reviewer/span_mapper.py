"""Map model-returned clause snippets to paragraph/run ranges in the document structure."""

from __future__ import annotations

from dataclasses import dataclass

from rapidfuzz import fuzz

from . import settings
from .docx_reader import DocumentStructure, ParagraphBlock


@dataclass
class RunSpan:
    """Inclusive run indices within one paragraph block."""

    paragraph_index: int
    run_start: int
    run_end: int
    table_path: tuple[int, int, int] | None = None


def _normalize(s: str) -> str:
    return " ".join(s.split())


def _find_span_in_block(block: ParagraphBlock, needle: str) -> RunSpan | None:
    if not needle.strip():
        return None
    hay = block.text
    if not hay:
        return None
    plain_needle = needle.strip()
    if plain_needle in hay:
        start_char = hay.index(plain_needle)
        end_char = start_char + len(plain_needle)
    else:
        best_ratio = 0.0
        best_slice = (0, min(len(hay), len(plain_needle) + 50))
        window = max(len(plain_needle), 20)
        for i in range(0, max(1, len(hay) - window + 1), max(1, window // 4)):
            chunk = hay[i : i + window + len(plain_needle)]
            r = fuzz.partial_ratio(plain_needle, chunk)
            if r > best_ratio:
                best_ratio = r
                best_slice = (i, min(len(hay), i + len(plain_needle) + 20))
        if best_ratio < settings.FUZZY_MATCH_THRESHOLD:
            return None
        start_char, end_char = best_slice[0], min(len(hay), best_slice[1])

    acc = 0
    run_start = run_end = None
    for r in block.runs:
        rlen = len(r.text)
        if run_start is None and acc + rlen > start_char:
            run_start = r.run_index
        if acc + rlen >= end_char:
            run_end = r.run_index
            break
        acc += rlen
    if run_start is None:
        run_start = 0
    if run_end is None:
        run_end = block.runs[-1].run_index if block.runs else 0
    return RunSpan(
        paragraph_index=block.paragraph_index,
        run_start=run_start,
        run_end=run_end,
        table_path=block.table_path,
    )


def map_clause_to_spans(structure: DocumentStructure, clause_text: str) -> list[RunSpan]:
    """
    Find where clause_text lives; prefer exact substring match in a single block.
    On failure, try fuzzy best block. Returns empty list if no acceptable match.
    """
    needle = clause_text.strip()
    if not needle:
        return []

    for block in structure.blocks:
        if not block.text.strip():
            continue
        if needle in block.text:
            span = _find_span_in_block(block, needle)
            if span:
                return [span]

    candidates: list[tuple[float, RunSpan]] = []
    for block in structure.blocks:
        if not block.text.strip():
            continue
        ratio = fuzz.partial_ratio(_normalize(needle), _normalize(block.text))
        if ratio >= settings.FUZZY_MATCH_THRESHOLD:
            span = _find_span_in_block(block, needle)
            if span:
                candidates.append((ratio, span))

    if not candidates:
        return []
    candidates.sort(key=lambda x: x[0], reverse=True)
    return [candidates[0][1]]


def paragraph_level_span(block: ParagraphBlock) -> RunSpan:
    """Fallback: entire paragraph run range."""
    if not block.runs:
        return RunSpan(
            paragraph_index=block.paragraph_index,
            run_start=0,
            run_end=0,
            table_path=block.table_path,
        )
    return RunSpan(
        paragraph_index=block.paragraph_index,
        run_start=0,
        run_end=block.runs[-1].run_index,
        table_path=block.table_path,
    )


def spans_for_clause_or_fallback(
    structure: DocumentStructure,
    clause_text: str,
    *,
    fallback_paragraph_index: int | None = None,
) -> list[RunSpan]:
    spans = map_clause_to_spans(structure, clause_text)
    if spans:
        return spans
    if fallback_paragraph_index is not None:
        block = next(
            (b for b in structure.blocks if b.paragraph_index == fallback_paragraph_index),
            None,
        )
        if block:
            return [paragraph_level_span(block)]
    return []
