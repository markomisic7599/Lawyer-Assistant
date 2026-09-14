"""Parivodic Intelligence System (PIS).

A BD/market-intelligence engine for a law firm. Phase 0 (this package) is a
self-contained backend that:

  1. INGEST  - pull candidate items from web search (pluggable provider).
  2. SCORE   - run each item through the "why would someone pay Parivodic?" lens.
  3. TRACK   - persist qualified items as Opportunities in a pipeline (SQLite).
  4. BRIEF   - render a daily Markdown brief of the best opportunities.

The private-knowledge fusion (affected clients, experience match, warm routes)
and the FastAPI + React dashboard are later phases; the code here is structured
with clean seams so those slot in without rework.
"""

from __future__ import annotations

__all__ = ["config", "models"]
