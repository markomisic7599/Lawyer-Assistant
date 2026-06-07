"""Orchestrate the mind-map feature: read → chunk → extract → consolidate → render → export."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from . import file_utils, settings
from .document_reader import SUPPORTED_SUFFIXES, read_document
from .logging_setup import ensure_logging
from .mindmap_chunker import chunk_structure
from .mindmap_llm import ProgressCallback, build_graph
from .mindmap_model import (
    MindMap,
    mindmap_from_dict,
    render_dot,
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
    dot_path: Path
    preview_html: str
    mermaid_text: str
    svg_path: Path | None = None


def _render_svg(dot_source: str, stem: str, out_dir: Path) -> Path | None:
    """Render DOT to a standalone SVG via Graphviz.

    Returns the SVG path, or ``None`` if the ``graphviz`` package or the system
    ``dot`` binary is unavailable. The pipeline must never fail just because the
    optional image export could not be produced — the .dot/.html/.mmd outputs
    still let the user render the diagram elsewhere.
    """
    try:
        import graphviz  # noqa: PLC0415 - optional dependency, imported lazily
    except ImportError:
        logger.warning("MindMap: 'graphviz' package not installed; skipping SVG export.")
        return None
    try:
        source = graphviz.Source(
            dot_source, filename=f"{stem}_mindmap_gv", directory=str(out_dir), format="svg"
        )
        rendered = source.render(cleanup=True)
        svg_path = out_dir / f"{stem}_mindmap.svg"
        Path(rendered).replace(svg_path)
        return svg_path
    except Exception:  # noqa: BLE001 - missing 'dot' binary or render error
        logger.warning(
            "MindMap: could not render SVG (is the Graphviz 'dot' binary installed and on PATH?). "
            "Skipping SVG export.",
            exc_info=True,
        )
        return None


def _scaled(cb: ProgressCallback | None, lo: float, hi: float) -> ProgressCallback | None:
    """Map a child callback's 0..1 fraction onto the [lo, hi] sub-range."""
    if cb is None:
        return None
    return lambda frac, desc: cb(lo + (hi - lo) * max(0.0, min(frac, 1.0)), desc)


def generate_mindmap(
    input_path: str | Path,
    *,
    detail: str = DETAIL_OVERVIEW,
    language: str = LANG_EN,
    direction: str = "TD",
    progress_cb: ProgressCallback | None = None,
) -> MindMapResult:
    """Build a process mind map from a document and write HTML/Mermaid/JSON outputs.

    ``progress_cb`` (if given) reports a 0..1 fraction with a short description.
    """
    ensure_logging()
    lang = language if language in VALID_LANGUAGES else LANG_EN
    detail = detail if detail in VALID_DETAIL else DETAIL_OVERVIEW
    input_path = Path(input_path)
    logger.info("MindMap: starting for %s (detail=%s language=%s)", input_path.name, detail, lang)

    if progress_cb is not None:
        progress_cb(0.02, "Reading document…")
    structure = read_document(input_path)
    logger.info(
        "MindMap: read %s block(s), %s chars",
        len(structure.blocks),
        len(structure.full_text),
    )

    if progress_cb is not None:
        progress_cb(0.08, "Splitting into sections…")
    chunks = chunk_structure(
        structure,
        settings.MINDMAP_MAX_CHUNK_CHARS,
        overlap_chars=settings.MINDMAP_CHUNK_OVERLAP_CHARS,
    )
    logger.info("MindMap: split into %s chunk(s)", len(chunks))
    if not chunks:
        raise ValueError("The document appears to be empty — nothing to map.")

    # The LLM work is the slow part: give it the bulk of the bar (0.1 → 0.85).
    graph_dict = build_graph(
        [c.text for c in chunks], detail, lang, progress_cb=_scaled(progress_cb, 0.1, 0.85)
    )
    mind_map = mindmap_from_dict(graph_dict, default_title=input_path.stem)
    logger.info(
        "MindMap: built graph '%s' with %s node(s), %s edge(s)",
        mind_map.title,
        len(mind_map.nodes),
        len(mind_map.edges),
    )

    if progress_cb is not None:
        progress_cb(0.88, "Rendering diagram & exporting files…")
    file_utils.ensure_dir(settings.MINDMAP_OUTPUT_DIR)
    stem = input_path.stem
    html_path = settings.MINDMAP_OUTPUT_DIR / f"{stem}_mindmap.html"
    mermaid_path = settings.MINDMAP_OUTPUT_DIR / f"{stem}_mindmap.mmd"
    json_path = settings.MINDMAP_OUTPUT_DIR / f"{stem}_mindmap.json"
    dot_path = settings.MINDMAP_OUTPUT_DIR / f"{stem}_mindmap.dot"

    mermaid_text = render_mermaid(mind_map, direction=direction)
    dot_text = render_dot(mind_map, direction=direction)
    html_path.write_text(render_html(mind_map, direction=direction), encoding="utf-8")
    mermaid_path.write_text(mermaid_text, encoding="utf-8")
    json_path.write_text(mind_map.to_json(), encoding="utf-8")
    dot_path.write_text(dot_text, encoding="utf-8")

    svg_path = _render_svg(dot_text, stem, settings.MINDMAP_OUTPUT_DIR)
    logger.info(
        "MindMap: wrote %s, %s, %s, %s%s",
        html_path,
        mermaid_path,
        json_path,
        dot_path,
        f", {svg_path}" if svg_path else " (no SVG)",
    )

    if progress_cb is not None:
        progress_cb(1.0, "Done")
    return MindMapResult(
        mind_map=mind_map,
        html_path=html_path,
        mermaid_path=mermaid_path,
        json_path=json_path,
        dot_path=dot_path,
        preview_html=render_preview_html(mind_map, direction=direction),
        mermaid_text=mermaid_text,
        svg_path=svg_path,
    )


def generate_mindmap_ui(
    uploaded_path: str | None,
    detail: str,
    language: str,
    direction_label: str,
    progress_cb: ProgressCallback | None = None,
) -> tuple[str, str, str | None, str | None, str | None, str | None, str | None, str]:
    """Gradio-friendly wrapper.

    Returns (status, preview_html, html_file, svg_file, mermaid_file, json_file,
    dot_file, mermaid_source). ``svg_file`` is ``None`` when Graphviz is not
    available to render the image. ``progress_cb`` (if given) reports a 0..1
    fraction with a short description while the mind map is generated.
    """
    ensure_logging()
    if not uploaded_path:
        return "Please upload a document.", "", None, None, None, None, None, ""
    p = Path(uploaded_path)
    if p.suffix.lower() not in SUPPORTED_SUFFIXES:
        supported = ", ".join(sorted(SUPPORTED_SUFFIXES))
        return f"Unsupported file type. Supported: {supported}.", "", None, None, None, None, None, ""

    direction = "LR" if str(direction_label).lower().startswith("left") else "TD"
    try:
        result = generate_mindmap(
            p, detail=detail, language=language, direction=direction, progress_cb=progress_cb
        )
    except Exception as exc:  # noqa: BLE001 - surface error in UI
        logger.exception("MindMap: generation failed")
        return f"Error: {exc}", "", None, None, None, None, None, ""

    image_note = "" if result.svg_path else " (install Graphviz for the SVG image export)"
    status = (
        f"Mind map ready: {len(result.mind_map.nodes)} step(s), "
        f"{len(result.mind_map.edges)} link(s). Saved: {result.html_path.name}{image_note}"
    )
    return (
        status,
        result.preview_html,
        str(result.html_path),
        str(result.svg_path) if result.svg_path else None,
        str(result.mermaid_path),
        str(result.json_path),
        str(result.dot_path),
        result.mermaid_text,
    )
