"""Orchestrate the mind-map feature: read → chunk → extract → consolidate → render → export."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from . import file_utils, settings
from .document_reader import SUPPORTED_SUFFIXES, read_document
from .logging_setup import ensure_logging
from .mindmap_chunker import chunk_structure
from .mindmap_llm import build_graph
from .mindmap_model import (
    MindMap,
    mindmap_from_dict,
    render_html,
    render_mermaid,
    render_preview_html,
)
from .mindmap_prompts import DETAIL_OVERVIEW, VALID_DETAIL
from .prompts import LANG_EN, VALID_LANGUAGES

logger = logging.getLogger(__name__)


@dataclass
class MindMapResult:
    mind_map: MindMap
    html_path: Path
    mermaid_path: Path
    json_path: Path
    preview_html: str


def generate_mindmap(
    input_path: str | Path,
    *,
    detail: str = DETAIL_OVERVIEW,
    language: str = LANG_EN,
    direction: str = "TD",
) -> MindMapResult:
    """Build a process mind map from a document and write HTML/Mermaid/JSON outputs."""
    ensure_logging()
    lang = language if language in VALID_LANGUAGES else LANG_EN
    detail = detail if detail in VALID_DETAIL else DETAIL_OVERVIEW
    input_path = Path(input_path)
    logger.info("MindMap: starting for %s (detail=%s language=%s)", input_path.name, detail, lang)

    structure = read_document(input_path)
    logger.info(
        "MindMap: read %s block(s), %s chars",
        len(structure.blocks),
        len(structure.full_text),
    )

    chunks = chunk_structure(
        structure,
        settings.MINDMAP_MAX_CHUNK_CHARS,
        overlap_chars=settings.MINDMAP_CHUNK_OVERLAP_CHARS,
    )
    logger.info("MindMap: split into %s chunk(s)", len(chunks))
    if not chunks:
        raise ValueError("The document appears to be empty — nothing to map.")

    graph_dict = build_graph([c.text for c in chunks], detail, lang)
    mind_map = mindmap_from_dict(graph_dict, default_title=input_path.stem)
    logger.info(
        "MindMap: built graph '%s' with %s node(s), %s edge(s)",
        mind_map.title,
        len(mind_map.nodes),
        len(mind_map.edges),
    )

    file_utils.ensure_dir(settings.MINDMAP_OUTPUT_DIR)
    stem = input_path.stem
    html_path = settings.MINDMAP_OUTPUT_DIR / f"{stem}_mindmap.html"
    mermaid_path = settings.MINDMAP_OUTPUT_DIR / f"{stem}_mindmap.mmd"
    json_path = settings.MINDMAP_OUTPUT_DIR / f"{stem}_mindmap.json"

    html_path.write_text(render_html(mind_map, direction=direction), encoding="utf-8")
    mermaid_path.write_text(render_mermaid(mind_map, direction=direction), encoding="utf-8")
    json_path.write_text(mind_map.to_json(), encoding="utf-8")
    logger.info("MindMap: wrote %s, %s, %s", html_path, mermaid_path, json_path)

    return MindMapResult(
        mind_map=mind_map,
        html_path=html_path,
        mermaid_path=mermaid_path,
        json_path=json_path,
        preview_html=render_preview_html(mind_map, direction=direction),
    )


def generate_mindmap_ui(
    uploaded_path: str | None,
    detail: str,
    language: str,
    direction_label: str,
) -> tuple[str, str, str | None, str | None, str | None]:
    """Gradio-friendly wrapper.

    Returns (status, preview_html, html_file, mermaid_file, json_file).
    """
    ensure_logging()
    if not uploaded_path:
        return "Please upload a document.", "", None, None, None
    p = Path(uploaded_path)
    if p.suffix.lower() not in SUPPORTED_SUFFIXES:
        supported = ", ".join(sorted(SUPPORTED_SUFFIXES))
        return f"Unsupported file type. Supported: {supported}.", "", None, None, None

    direction = "LR" if str(direction_label).lower().startswith("left") else "TD"
    try:
        result = generate_mindmap(p, detail=detail, language=language, direction=direction)
    except Exception as exc:  # noqa: BLE001 - surface error in UI
        logger.exception("MindMap: generation failed")
        return f"Error: {exc}", "", None, None, None

    status = (
        f"Mind map ready: {len(result.mind_map.nodes)} step(s), "
        f"{len(result.mind_map.edges)} link(s). Saved: {result.html_path.name}"
    )
    return (
        status,
        result.preview_html,
        str(result.html_path),
        str(result.mermaid_path),
        str(result.json_path),
    )
