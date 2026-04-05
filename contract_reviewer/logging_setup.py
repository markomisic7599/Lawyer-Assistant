"""One-time logging configuration for terminal output (Gradio / desktop)."""

from __future__ import annotations

import logging

_configured = False


def ensure_logging() -> None:
    """Call before first log line so INFO messages appear in the console."""
    global _configured
    if _configured:
        return
    root = logging.getLogger()
    if root.handlers:
        _configured = True
        return
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    # Gradio / OpenAI client use httpx at INFO — very noisy next to our pipeline logs.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    _configured = True
