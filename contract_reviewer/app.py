"""Gradio UI: upload .docx, choose mode, download reviewed file."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import gradio as gr
import logging

from contract_reviewer import settings
from contract_reviewer.document_reader import SUPPORTED_SUFFIXES
from contract_reviewer.logging_setup import ensure_logging
from contract_reviewer.mindmap_pipeline import generate_mindmap_ui
from contract_reviewer.review_pipeline import review_contract_ui

logger = logging.getLogger(__name__)


def _gradio_allowed_paths() -> list[str]:
    """Paths Gradio may expose for download (output dirs + project root)."""
    return [
        str(settings.OUTPUT_DIR.resolve()),
        str(settings.MINDMAP_OUTPUT_DIR.resolve()),
        str(_ROOT.resolve()),
    ]


def _upload_to_path(upload: Any) -> str | None:
    if upload is None:
        return None
    if isinstance(upload, str):
        return upload
    if hasattr(upload, "path"):
        return getattr(upload, "path", None)  # type: ignore[no-any-return]
    if isinstance(upload, dict) and "path" in upload:
        return str(upload["path"])
    name = getattr(upload, "name", None)
    return str(name) if name else None


def review_contract_gradio(
    upload,
    mode: str,
    language: str,
) -> tuple[str, str | None]:
    path = _upload_to_path(upload)
    return review_contract_ui(path, mode, language=language)


def generate_mindmap_gradio(
    upload,
    detail: str,
    language: str,
    direction: str,
) -> tuple[str, str, str | None, str | None, str | None]:
    path = _upload_to_path(upload)
    return generate_mindmap_ui(path, detail, language, direction)


def build_app() -> gr.Blocks:
    ensure_logging()
    logger.info("Building Gradio Blocks (Lawyer Assistant)")
    mindmap_filetypes = sorted(SUPPORTED_SUFFIXES)
    with gr.Blocks(title="Lawyer Assistant") as demo:
        gr.Markdown("# Lawyer Assistant")
        with gr.Tabs():
            with gr.Tab("Contract review"):
                gr.Markdown(
                    "Upload a **.docx** contract. Choose **review language** (English or Serbian Latin) "
                    "for issue labels and suggestions. The app returns a copy with **highlights** "
                    "and **reviewer note** paragraphs."
                )
                with gr.Row():
                    file_in = gr.File(
                        label="Contract (.docx)",
                        file_types=[".docx"],
                        type="filepath",
                    )
                    mode = gr.Dropdown(
                        choices=["strict", "balanced", "light"],
                        value="balanced",
                        label="Review mode",
                    )
                    language = gr.Dropdown(
                        choices=[
                            ("English", "en"),
                            ("Srpski (latinica)", "sr_latin"),
                        ],
                        value="en",
                        label="Review language",
                    )
                btn = gr.Button("Review contract", variant="primary")
                status = gr.Textbox(label="Status", interactive=False, lines=2)
                file_out = gr.File(label="Download reviewed .docx")

                btn.click(
                    fn=review_contract_gradio,
                    inputs=[file_in, mode, language],
                    outputs=[status, file_out],
                )

            with gr.Tab("Process mind map"):
                gr.Markdown(
                    "Upload a law, regulation, or procedure "
                    f"(**{', '.join(mindmap_filetypes)}**). The app builds a **process flowchart** "
                    "of the steps, decision/authority gates, required documents, deadlines, and "
                    "article references — rendered below and exportable as HTML, Mermaid, or JSON."
                )
                with gr.Row():
                    mm_file_in = gr.File(
                        label=f"Document ({', '.join(mindmap_filetypes)})",
                        file_types=mindmap_filetypes,
                        type="filepath",
                    )
                    mm_detail = gr.Dropdown(
                        choices=[
                            ("Overview (main steps)", "overview"),
                            ("Detailed (all steps & documents)", "detailed"),
                        ],
                        value="overview",
                        label="Detail level",
                    )
                    mm_language = gr.Dropdown(
                        choices=[
                            ("English", "en"),
                            ("Srpski (latinica)", "sr_latin"),
                        ],
                        value="en",
                        label="Diagram language",
                    )
                    mm_direction = gr.Dropdown(
                        choices=["Top to bottom", "Left to right"],
                        value="Top to bottom",
                        label="Layout",
                    )
                mm_btn = gr.Button("Generate mind map", variant="primary")
                mm_status = gr.Textbox(label="Status", interactive=False, lines=2)
                mm_preview = gr.HTML(label="Mind map preview")
                with gr.Row():
                    mm_html_out = gr.File(label="Download HTML (open in browser)")
                    mm_mmd_out = gr.File(label="Download Mermaid (.mmd)")
                    mm_json_out = gr.File(label="Download JSON")

                mm_btn.click(
                    fn=generate_mindmap_gradio,
                    inputs=[mm_file_in, mm_detail, mm_language, mm_direction],
                    outputs=[mm_status, mm_preview, mm_html_out, mm_mmd_out, mm_json_out],
                )
    return demo


def main() -> None:
    ensure_logging()
    logger.info("Launching Gradio on http://127.0.0.1:7860")
    allowed = _gradio_allowed_paths()
    logger.info("Gradio allowed_paths for downloads: %s", allowed)
    build_app().launch(
        server_name="127.0.0.1",
        server_port=7860,
        allowed_paths=allowed,
    )


if __name__ == "__main__":
    main()
