"""Desktop launcher: run Gradio locally and open it in a pywebview window."""

from __future__ import annotations

import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import webview

from contract_reviewer.app import build_app


def launch_desktop_app(port: int = 7860) -> None:
    demo = build_app()
    demo.queue()
    demo.launch(
        server_name="127.0.0.1",
        server_port=port,
        prevent_thread_lock=True,
        inbrowser=False,
        show_error=True,
    )
    deadline = time.time() + 30
    url = f"http://127.0.0.1:{port}"
    while time.time() < deadline:
        try:
            import urllib.request

            urllib.request.urlopen(url, timeout=0.5)
            break
        except OSError:
            time.sleep(0.2)
    else:
        raise RuntimeError("Gradio server did not become ready in time.")

    window = webview.create_window("Contract Reviewer", url, width=1100, height=800)
    webview.start()


if __name__ == "__main__":
    launch_desktop_app()
