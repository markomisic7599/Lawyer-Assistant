"""Orchestrate: read .docx → LLM chunks → map spans → annotate → output path."""

from __future__ import annotations

from pathlib import Path

from . import file_utils, settings
from .docx_annotator import IssueAnnotation, annotate_issues
from .docx_reader import extract_runs
from .llm_client import review_document
from .span_mapper import spans_for_clause_or_fallback


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
    workspace: Path | None = None,
) -> Path:
    """
    Copy input into workspace, run extraction + LLM + annotation, return path to reviewed .docx.
    """
    input_docx_path = Path(input_docx_path)
    ws = workspace or file_utils.make_temp_workspace()
    file_utils.ensure_dir(ws)
    local_copy = file_utils.copy_to_workspace(input_docx_path, ws)

    structure = extract_runs(str(local_copy))
    chunks = _chunk_text(structure.full_text, settings.MAX_CHUNK_CHARS)
    raw_issues = review_document(chunks, mode)

    annotations: list[IssueAnnotation] = []
    for item in raw_issues:
        clause = item.get("clause_text", "")
        spans = spans_for_clause_or_fallback(structure, clause)
        if not spans:
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

    file_utils.ensure_dir(settings.OUTPUT_DIR)
    out_name = file_utils.safe_output_name(input_docx_path)
    output_path = settings.OUTPUT_DIR / out_name
    annotate_issues(str(local_copy), str(output_path), annotations, add_summary_page=False)

    if not settings.KEEP_TEMP_FILES:
        try:
            local_copy.unlink(missing_ok=True)  # type: ignore[arg-type]
        except OSError:
            pass

    return output_path


def review_contract_ui(
    uploaded_path: str | None,
    mode: str,
) -> tuple[str, str | None]:
    """
    Gradio-friendly wrapper: returns (status_message, output_file_path_or_none).
    """
    if not uploaded_path:
        return "Please upload a .docx file.", None
    p = Path(uploaded_path)
    if p.suffix.lower() != ".docx":
        return "Only .docx files are supported.", None
    try:
        out = run_review(p, mode)
        return f"Review complete. Saved: {out.name}", str(out)
    except Exception as e:
        return f"Error: {e}", None
