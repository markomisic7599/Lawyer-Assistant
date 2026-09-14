"""Core domain model: the Opportunity and its pipeline.

An Opportunity is the single object that flows through the BD pipeline, mirroring
the firm's framework: FIND / STUCK PROJECT / REGULATORY MONEY radars, scored by
the "why would someone pay us?" lens, tracked from IDENTIFIED to MANDATE.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class Radar(str, Enum):
    """Which intelligence radar surfaced this opportunity."""

    FIND = "FIND"  # new investors, market entry, trigger events, phase-change
    STUCK_PROJECT = "STUCK_PROJECT"  # disputes brewing, delays, unpaid, blocked
    REGULATORY_MONEY = "REGULATORY_MONEY"  # new rules that force/enable spend


class Stage(str, Enum):
    """Pipeline stages (in order). Drives the future Kanban board."""

    IDENTIFIED = "IDENTIFIED"
    QUALIFIED = "QUALIFIED"
    PERSON_FOUND = "PERSON_FOUND"
    ROUTE_FOUND = "ROUTE_FOUND"
    CONTACTED = "CONTACTED"
    FOLLOW_UP = "FOLLOW_UP"
    MEETING = "MEETING"
    PROPOSAL = "PROPOSAL"
    MANDATE = "MANDATE"
    LOST = "LOST"
    WATCH = "WATCH"


ACTIVE_STAGES: frozenset[Stage] = frozenset(
    s for s in Stage if s not in {Stage.MANDATE, Stage.LOST}
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Entity:
    """A second-order actor around an opportunity (potential separate client)."""

    name: str
    role: str = ""  # e.g. "investor", "EPC contractor", "financier", "int'l counsel"


@dataclass
class Contact:
    """The specific person to approach (WHO)."""

    role: str = ""  # e.g. "General Counsel", "Country Manager", "Project Director"
    name: str = ""  # filled when reliably identifiable
    is_decision_maker: bool = False


@dataclass
class SourceItem:
    """A raw candidate item from ingestion, before scoring."""

    title: str
    url: str
    snippet: str = ""
    source: str = ""
    published: str = ""
    radar_hint: Radar | None = None

    def fingerprint(self) -> str:
        """Stable id for dedupe (prefer URL, fall back to title)."""
        basis = (self.url or self.title).strip().lower()
        return hashlib.sha1(basis.encode("utf-8")).hexdigest()[:16]


@dataclass
class Opportunity:
    """A scored, tracked BD opportunity."""

    id: str
    title: str
    radar: Radar
    score: int
    stage: Stage = Stage.IDENTIFIED

    # The scoring lens output
    mandate_trigger: bool = True
    why_now: str = ""
    rationale: str = ""
    confidence: float = 0.0

    # WHO / entities / second-order thinking
    target_org: str = ""
    contact: Contact = field(default_factory=Contact)
    entities: list[Entity] = field(default_factory=list)
    second_order: list[str] = field(default_factory=list)  # extra clients/workstreams
    suggested_actions: list[str] = field(default_factory=list)

    # Provenance + lifecycle
    source_url: str = ""
    source_title: str = ""
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)
    next_action_at: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["radar"] = self.radar.value
        d["stage"] = self.stage.value
        return d

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Opportunity":
        contact_raw = data.get("contact") or {}
        entities_raw = data.get("entities") or []
        return Opportunity(
            id=str(data["id"]),
            title=str(data.get("title", "")),
            radar=Radar(data.get("radar", Radar.FIND.value)),
            score=int(data.get("score", 0)),
            stage=Stage(data.get("stage", Stage.IDENTIFIED.value)),
            mandate_trigger=bool(data.get("mandate_trigger", True)),
            why_now=str(data.get("why_now", "")),
            rationale=str(data.get("rationale", "")),
            confidence=float(data.get("confidence", 0.0) or 0.0),
            target_org=str(data.get("target_org", "")),
            contact=Contact(**contact_raw) if isinstance(contact_raw, dict) else Contact(),
            entities=[Entity(**e) for e in entities_raw if isinstance(e, dict)],
            second_order=list(data.get("second_order", []) or []),
            suggested_actions=list(data.get("suggested_actions", []) or []),
            source_url=str(data.get("source_url", "")),
            source_title=str(data.get("source_title", "")),
            created_at=str(data.get("created_at", _now_iso())),
            updated_at=str(data.get("updated_at", _now_iso())),
            next_action_at=str(data.get("next_action_at", "")),
            notes=str(data.get("notes", "")),
        )
