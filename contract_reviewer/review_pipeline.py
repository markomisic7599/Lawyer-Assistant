"""Orchestrate: read .docx → LLM chunks → map spans → annotate → output path."""

from __future__ import annotations

import logging
from pathlib import Path

from . import file_utils, settings
from .docx_annotator import IssueAnnotation, annotate_issues
from .docx_reader import extract_runs
from .llm_client import review_document
from .logging_setup import ensure_logging
from .prompts import LANG_EN, VALID_LANGUAGES
from .span_mapper import spans_for_clause_or_fallback

logger = logging.getLogger(__name__)


def _chunk_text(full: str, max_chars: int) -> list[str]:
    if len(full) <= max_chars:
        return [full]
    chunks: list[str] = []
    start = 0
    while start < len(full):
        end = min(start + max_chars, len(full))
        if end < len(full):
            break_at = full.rfind("\n\n", start, end)
            if break_at > start + max_chars // 2:
                end = break_at + 2
        chunks.append(full[start:end])
        start = end
    return chunks


def run_review(
    input_docx_path: str | Path,
    mode: str,
    *,
    language: str = LANG_EN,
    workspace: Path | None = None,
) -> Path:
    """
    Copy input into workspace, run extraction + LLM + annotation, return path to reviewed .docx.
    """
    ensure_logging()
    lang = language if language in VALID_LANGUAGES else LANG_EN
    input_docx_path = Path(input_docx_path)
    logger.info(
        "Starting review for %s (mode=%s language=%s)",
        input_docx_path.name,
        mode,
        lang,
    )
    ws = workspace or file_utils.make_temp_workspace()
    file_utils.ensure_dir(ws)
    local_copy = file_utils.copy_to_workspace(input_docx_path, ws)
    logger.info("Working copy: %s (workspace=%s)", local_copy, ws)

    structure = extract_runs(str(local_copy))
    logger.info(
        "Extracted %s paragraph blocks, %s chars plain text",
        len(structure.blocks),
        len(structure.full_text),
    )
    chunks = _chunk_text(structure.full_text, settings.MAX_CHUNK_CHARS)
    logger.info(
        "Split into %s chunk(s), max_chunk=%s chars",
        len(chunks),
        settings.MAX_CHUNK_CHARS,
    )
    raw_issues = review_document(chunks, mode, language=lang)
    logger.info("Model returned %s raw issue row(s)", len(raw_issues))

    annotations: list[IssueAnnotation] = []
    skipped_map = 0
    for item in raw_issues:
        clause = item.get("clause_text", "")
        spans = spans_for_clause_or_fallback(structure, clause)
        if not spans:
            skipped_map += 1
            logger.info(
                "Skipped issue (no doc span): type=%s clause=%r",
                item.get("issue_type"),
                (clause[:120] + "…") if len(clause) > 120 else clause,
            )
            continue
        annotations.append(
            IssueAnnotation(
                clause_text=clause,
                issue_type=item.get("issue_type", "unknown"),
                severity=item.get("severity", "medium"),
                suggestion=item.get("suggestion", ""),
                spans=spans,
            )
        )

    logger.info(
        "Mapped %s annotation(s); %s issue(s) had no matching text in the .docx",
        len(annotations),
        skipped_map,
    )
    file_utils.ensure_dir(settings.OUTPUT_DIR)
    out_name = file_utils.safe_output_name(input_docx_path)
    output_path = settings.OUTPUT_DIR / out_name
    logger.info("Writing annotated doc to %s", output_path)
    annotate_issues(
        str(local_copy),
        str(output_path),
        annotations,
        language=lang,
        add_summary_page=False,
    )
    logger.info("Saved reviewed file: %s", output_path)

    if not settings.KEEP_TEMP_FILES:
        try:
            local_copy.unlink(missing_ok=True)  # type: ignore[arg-type]
        except OSError:
            pass

    return output_path


def review_contract_ui(
    uploaded_path: str | None,
    mode: str,
    language: str = LANG_EN,
) -> tuple[str, str | None]:
    """
    Gradio-friendly wrapper: returns (status_message, output_file_path_or_none).
    """
    ensure_logging()
    if not uploaded_path:
        logger.info("Gradio: no file uploaded")
        return "Please upload a .docx file.", None
    p = Path(uploaded_path)
    if p.suffix.lower() != ".docx":
        logger.info("Gradio: rejected non-docx path=%s", p)
        return "Only .docx files are supported.", None
    lang = language if language in VALID_LANGUAGES else LANG_EN
    logger.info("Gradio: review requested path=%s mode=%s language=%s", p, mode, lang)
    try:
        out = run_review(p, mode, language=lang)
        logger.info("Gradio: success output=%s", out)
        return f"Review complete. Saved: {out.name}", str(out)
    except Exception as e:
        logger.exception("Gradio: review failed")
        return f"Error: {e}", None
