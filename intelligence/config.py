"""Central configuration for the Intelligence System (env-backed)."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- LLM (reuses the same OpenAI credentials as the rest of the app) ---------
MODEL_NAME: str = os.getenv("PIS_MODEL", os.getenv("CONTRACT_REVIEWER_MODEL", "gpt-5.4-mini"))
OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL: str | None = os.getenv("OPENAI_BASE_URL")

# --- Search / ingestion ------------------------------------------------------
# Provider: "tavily" (default), or "mock" for offline testing.
SEARCH_PROVIDER: str = os.getenv("PIS_SEARCH_PROVIDER", "tavily").strip().lower()
TAVILY_API_KEY: str | None = os.getenv("TAVILY_API_KEY")
# Max results requested per search query.
SEARCH_MAX_RESULTS: int = int(os.getenv("PIS_SEARCH_MAX_RESULTS", "8"))
# How far back (days) a result may be to still count as a "trigger event".
SEARCH_RECENCY_DAYS: int = int(os.getenv("PIS_SEARCH_RECENCY_DAYS", "14"))

# --- Scoring -----------------------------------------------------------------
# Opportunities scoring below this (0-100) are dropped ("danas nema ničega").
SCORE_THRESHOLD: int = int(os.getenv("PIS_SCORE_THRESHOLD", "60"))
# Cap how many items we score per run to control cost.
MAX_ITEMS_PER_RUN: int = int(os.getenv("PIS_MAX_ITEMS_PER_RUN", "60"))

# --- Storage / output --------------------------------------------------------
_data_env = os.getenv("PIS_DATA_DIR", "").strip()
DATA_DIR: Path = (
    Path(_data_env).expanduser() if _data_env else Path.home() / ".parivodic_intelligence"
)
DB_PATH: Path = DATA_DIR / "pipeline.db"
BRIEF_DIR: Path = DATA_DIR / "briefs"

# --- Firm context (kept here so the scoring prompt stays firm-specific) ------
FIRM_NAME: str = os.getenv("PIS_FIRM_NAME", "Parivodic Lawyers")
FIRM_MARKETS: str = os.getenv("PIS_MARKETS", "Serbia and the Western Balkans")
