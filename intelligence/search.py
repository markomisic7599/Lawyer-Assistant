"""Pluggable web-search ingestion.

A ``SearchProvider`` returns raw ``SourceItem`` candidates for a query. Tavily is
the default; a ``MockProvider`` allows offline testing. Radar-specific query
plans encode *where the money is* so we hunt trigger events, not "legal news".
"""

from __future__ import annotations

import logging
from typing import Protocol

import httpx

from . import config
from .models import Radar, SourceItem

logger = logging.getLogger(__name__)


class SearchProvider(Protocol):
    def search(self, query: str, *, max_results: int, recency_days: int) -> list[SourceItem]:
        ...


class MockProvider:
    """Deterministic offline provider for tests/dev (no network, no API key)."""

    def __init__(self, canned: dict[str, list[SourceItem]] | None = None) -> None:
        self._canned = canned or {}

    def search(self, query: str, *, max_results: int, recency_days: int) -> list[SourceItem]:
        return self._canned.get(query, [])[:max_results]


class TavilyProvider:
    """Tavily Search API (https://tavily.com). Good recency + full content."""

    _ENDPOINT = "https://api.tavily.com/search"

    def __init__(self, api_key: str | None = None, *, timeout: float = 30.0) -> None:
        self._api_key = api_key or config.TAVILY_API_KEY
        self._timeout = timeout

    def search(self, query: str, *, max_results: int, recency_days: int) -> list[SourceItem]:
        if not self._api_key:
            raise RuntimeError(
                "TAVILY_API_KEY is not set. Add it to your environment or .env, "
                "or set PIS_SEARCH_PROVIDER=mock for offline use."
            )
        payload = {
            "api_key": self._api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": "advanced",
            "topic": "news",
            "days": recency_days,
            "include_answer": False,
        }
        try:
            resp = httpx.post(self._ENDPOINT, json=payload, timeout=self._timeout)
            resp.raise_for_status()
            data = resp.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("Tavily search failed for %r: %s", query, exc)
            return []
        items: list[SourceItem] = []
        for r in data.get("results", []) or []:
            items.append(
                SourceItem(
                    title=str(r.get("title", "")).strip(),
                    url=str(r.get("url", "")).strip(),
                    snippet=str(r.get("content", "")).strip(),
                    source=str(r.get("url", "")).split("/")[2] if r.get("url") else "",
                    published=str(r.get("published_date", "")),
                )
            )
        return items


def get_provider() -> SearchProvider:
    """Instantiate the configured search provider."""
    if config.SEARCH_PROVIDER == "mock":
        return MockProvider()
    if config.SEARCH_PROVIDER == "tavily":
        return TavilyProvider()
    raise ValueError(f"Unknown PIS_SEARCH_PROVIDER: {config.SEARCH_PROVIDER!r}")


# --- Radar query plans -------------------------------------------------------
# Each query targets a *trigger event* likely to create a legal mandate in the
# firm's markets. Kept as data so they're easy to tune without touching logic.
_MARKET = config.FIRM_MARKETS

RADAR_QUERIES: dict[Radar, list[str]] = {
    Radar.FIND: [
        f"new foreign investor factory OR plant announcement {_MARKET}",
        f"solar OR wind OR BESS OR gas power project {_MARKET} construction",
        f"mining exploration project permitting OR financing {_MARKET}",
        f"M&A OR joint venture OR project finance deal {_MARKET}",
        f"data center OR logistics center OR hotel large investment {_MARKET}",
        f"EPC contractor wins tender {_MARKET}",
        f"privatization OR distressed asset sale {_MARKET}",
    ],
    Radar.STUCK_PROJECT: [
        f"project delayed OR dispute OR stalled construction {_MARKET}",
        f"contractor unpaid OR extension of time OR claim {_MARKET}",
        f"tender challenged OR procurement complaint {_MARKET}",
        f"investor dispute with government OR permit blocked {_MARKET}",
        f"joint venture dispute OR local community blocks project {_MARKET}",
        f"bank guarantee called OR financing suspended project {_MARKET}",
    ],
    Radar.REGULATORY_MONEY: [
        f"new law OR regulation OR bylaw enacted {_MARKET} business",
        f"new subsidy OR state aid OR tax incentive {_MARKET} investment",
        f"competition authority investigation OR enforcement {_MARKET}",
        f"transitional deadline compliance new rules {_MARKET}",
        f"EBRD OR EIB OR EU funding program {_MARKET}",
    ],
}


def plan_queries(radars: list[Radar] | None = None) -> list[tuple[Radar, str]]:
    """Flatten radar query plans into (radar, query) pairs to execute."""
    selected = radars or list(RADAR_QUERIES.keys())
    return [(radar, q) for radar in selected for q in RADAR_QUERIES.get(radar, [])]
