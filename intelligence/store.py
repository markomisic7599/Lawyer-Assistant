"""SQLite persistence for the opportunity pipeline.

Keeps state across daily runs so we manage a PIPELINE, not an endless feed.
Dedupe is by opportunity id (a fingerprint of the source URL/title): re-seeing
the same item updates its score/details but never resets a human-managed stage.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from . import config
from .models import Opportunity, Stage

logger = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS opportunities (
    id           TEXT PRIMARY KEY,
    stage        TEXT NOT NULL,
    radar        TEXT NOT NULL,
    score        INTEGER NOT NULL,
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL,
    data         TEXT NOT NULL   -- full Opportunity as JSON
);
CREATE INDEX IF NOT EXISTS idx_opps_stage ON opportunities(stage);
CREATE INDEX IF NOT EXISTS idx_opps_score ON opportunities(score);
"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or config.DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as conn:
            conn.executescript(_SCHEMA)

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def get(self, opp_id: str) -> Opportunity | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT data FROM opportunities WHERE id = ?", (opp_id,)
            ).fetchone()
        return Opportunity.from_dict(json.loads(row["data"])) if row else None

    def upsert(self, opp: Opportunity, *, preserve_stage: bool = True) -> tuple[Opportunity, bool]:
        """Insert new, or refresh score/details of an existing one.

        Returns (stored_opportunity, is_new). By default an existing item's stage
        is preserved (ingestion must never reset a human-managed stage); pass
        ``preserve_stage=False`` for explicit stage changes (see ``set_stage``).
        """
        existing = self.get(opp.id)
        is_new = existing is None
        if existing is not None:
            if preserve_stage:
                opp.stage = existing.stage
            opp.created_at = existing.created_at
            opp.notes = existing.notes or opp.notes
            opp.next_action_at = existing.next_action_at or opp.next_action_at
        opp.updated_at = _now_iso()
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO opportunities (id, stage, radar, score, created_at, updated_at, data)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET
                     stage=excluded.stage, radar=excluded.radar, score=excluded.score,
                     updated_at=excluded.updated_at, data=excluded.data""",
                (
                    opp.id,
                    opp.stage.value,
                    opp.radar.value,
                    opp.score,
                    opp.created_at,
                    opp.updated_at,
                    json.dumps(opp.to_dict(), ensure_ascii=False),
                ),
            )
        return opp, is_new

    def set_stage(self, opp_id: str, stage: Stage) -> bool:
        opp = self.get(opp_id)
        if opp is None:
            return False
        opp.stage = stage
        self.upsert(opp, preserve_stage=False)
        return True

    def list(
        self,
        *,
        stage: Stage | None = None,
        min_score: int = 0,
        limit: int | None = None,
    ) -> list[Opportunity]:
        sql = "SELECT data FROM opportunities WHERE score >= ?"
        params: list[object] = [min_score]
        if stage is not None:
            sql += " AND stage = ?"
            params.append(stage.value)
        sql += " ORDER BY score DESC, updated_at DESC"
        if limit:
            sql += f" LIMIT {int(limit)}"
        with self._conn() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [Opportunity.from_dict(json.loads(r["data"])) for r in rows]
