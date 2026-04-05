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
from contract_reviewer.logging_setup import ensure_logging
from contract_reviewer.review_pipeline import review_contract_ui

logger = logging.getLogger(__name__)


def _gradio_allowed_paths() -> list[str]:
    """Paths Gradio may expose for download (output dir + project root)."""
    return [
        str(settings.OUTPUT_DIR.resolve()),
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


def build_app() -> gr.Blocks:
    ensure_logging()
    logger.info("Building Gradio Blocks (Contract Reviewer)")
    with gr.Blocks(title="Contract Reviewer") as demo:
        gr.Markdown(
            "## Contract reviewer\n"
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
