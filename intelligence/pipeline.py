"""Daily run: ingest → score → filter → persist, returning today's opportunities."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from . import config
from .models import Opportunity, Radar, SourceItem
from .scoring import score_item
from .search import get_provider, plan_queries
from .store import Store

logger = logging.getLogger(__name__)


@dataclass
class RunResult:
    fetched: int
    scored: int
    qualified: list[Opportunity]
    new_count: int


def _dedupe(items: list[SourceItem]) -> list[SourceItem]:
    seen: set[str] = set()
    out: list[SourceItem] = []
    for it in items:
        if not it.title and not it.url:
            continue
        fp = it.fingerprint()
        if fp in seen:
            continue
        seen.add(fp)
        out.append(it)
    return out


def run_daily(
    radars: list[Radar] | None = None,
    *,
    store: Store | None = None,
    provider=None,
) -> RunResult:
    """Execute the full daily intelligence sweep across the selected radars."""
    store = store or Store()
    provider = provider or get_provider()

    # 1) INGEST across all radar query plans.
    raw: list[SourceItem] = []
    for radar, query in plan_queries(radars):
        results = provider.search(
            query,
            max_results=config.SEARCH_MAX_RESULTS,
            recency_days=config.SEARCH_RECENCY_DAYS,
        )
        for r in results:
            r.radar_hint = radar
        raw.extend(results)
        logger.info("Query [%s] '%s' -> %s result(s)", radar.value, query, len(results))

    items = _dedupe(raw)[: config.MAX_ITEMS_PER_RUN]
    logger.info("Ingested %s raw, %s unique (capped at %s)", len(raw), len(items), config.MAX_ITEMS_PER_RUN)

    # 2) SCORE through the "why pay us?" lens; drop the noise.
    qualified: list[Opportunity] = []
    new_count = 0
    for item in items:
        opp = score_item(item)
        if opp is None:
            continue
        stored, is_new = store.upsert(opp)
        qualified.append(stored)
        new_count += int(is_new)

    qualified.sort(key=lambda o: o.score, reverse=True)
    logger.info("Qualified %s opportunit(y/ies), %s new", len(qualified), new_count)
    return RunResult(
        fetched=len(items),
        scored=len(items),
        qualified=qualified,
        new_count=new_count,
    )
