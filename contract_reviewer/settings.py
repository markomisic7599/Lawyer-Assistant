"""Central configuration — keep constants and env-backed settings here."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# LLM
MODEL_NAME: str = os.getenv("CONTRACT_REVIEWER_MODEL", "gpt-4o-mini")
OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL: str | None = os.getenv("OPENAI_BASE_URL")  # optional, for compatible APIs

# Chunking
MAX_CHUNK_CHARS: int = int(os.getenv("CONTRACT_REVIEWER_MAX_CHUNK", "12000"))

# Files
_output_env = os.getenv("CONTRACT_REVIEWER_OUTPUT_DIR", "").strip()
OUTPUT_DIR: Path = (
    Path(_output_env).expanduser()
    if _output_env
    else Path.home() / ".contract_reviewer" / "output"
)
KEEP_TEMP_FILES: bool = os.getenv("CONTRACT_REVIEWER_KEEP_TEMP", "").lower() in (
    "1",
    "true",
    "yes",
)

# Review UI defaults
DEFAULT_REVIEW_MODE: str = "balanced"

# Fuzzy match (span_mapper)
FUZZY_MATCH_THRESHOLD: int = int(os.getenv("CONTRACT_REVIEWER_FUZZY_THRESHOLD", "85"))
