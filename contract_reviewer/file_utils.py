"""Temp directories, safe output names, and cleanup for desktop use."""

from __future__ import annotations

import shutil
import tempfile
import time
from pathlib import Path


def make_temp_workspace(prefix: str = "contract_reviewer_") -> Path:
    return Path(tempfile.mkdtemp(prefix=prefix))


def safe_output_name(input_path: str | Path, suffix: str = "_reviewed") -> str:
    p = Path(input_path)
    return f"{p.stem}{suffix}{p.suffix}"


def cleanup_old_files(directory: Path, max_age_seconds: float = 86400.0) -> int:
    """Remove files older than max_age_seconds in directory. Returns count removed."""
    if not directory.exists():
        return 0
    now = time.time()
    removed = 0
    for child in directory.iterdir():
        if child.is_file():
            try:
                if now - child.stat().st_mtime > max_age_seconds:
                    child.unlink()
                    removed += 1
            except OSError:
                continue
    return removed


def copy_to_workspace(src: str | Path, workspace: Path) -> Path:
    src = Path(src)
    dest = workspace / src.name
    shutil.copy2(src, dest)
    return dest


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
