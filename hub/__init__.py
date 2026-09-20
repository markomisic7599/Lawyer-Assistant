"""Central industrial information hub — domain model.

A public-facing content system for the firm website: sector-tagged legal /
regulatory / business briefings for companies operating in Serbia. Separate
from the internal BD intelligence pipeline.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
from enum import Enum
from typing import Any


class Industry(str, Enum):
    MINING = "Mining & Critical Minerals"
    ENERGY = "Energy & Renewables"
    INFRA = "Infrastructure & Construction"
    LIFE_SCIENCES = "Life Sciences & Pharma"
    RETAIL = "Retail & Consumer"
    TECH = "Technology, Data & AI"
    BANKING = "Banking & Finance"
    FDI = "Foreign Investment"
    PROCUREMENT = "Public Procurement"


class ContentStatus(str, Enum):
    """Topic value / publication triage."""

    URGENT_ALERT = "Urgent Alert"
    IMPORTANT = "Important Development"
    OPPORTUNITY = "Business Opportunity"
    CASE_LAW = "Case Law Insight"
    STRATEGIC = "Strategic Analysis"
    NOT_RELEVANT = "Not relevant enough"  # never published


class DocStatus(str, Enum):
    DRAFT = "Nacrt"
    ADOPTED = "Usvojen"
    IN_FORCE = "Na snazi"


class EditorialState(str, Enum):
    """Human legal-control workflow."""

    INGESTED = "Ingested"  # raw signal found
    DRAFT = "Draft analysis"  # AI/editor draft
    IN_REVIEW = "In legal review"
    APPROVED = "Approved"
    PUBLISHED = "Published"
    REJECTED = "Rejected"


# Why publish? At least one must hold — otherwise do not generate.
PUBLISH_CRITERIA = [
    "Creates a concrete business opportunity",
    "Introduces a new obligation",
    "Contains an important deadline",
    "Changes operating conditions",
    "Affects existing contracts or projects",
    "Creates regulatory, financial or reputational risk",
    "Requires documentation or an internal decision",
    "Enables subsidy, financing or project access",
    "Signals material industry development",
    "Solves a problem many companies face",
    "May reasonably create need for legal / strategic advice",
]


@dataclass
class SourceRef:
    title: str
    url: str
    published: str = ""
    doc_status: DocStatus = DocStatus.IN_FORCE


@dataclass
class HubArticle:
    """One published (or draft) hub piece — must follow the mandatory structure."""

    id: str
    title: str  # consequence-oriented, not "Amendments to Law X"
    industries: list[Industry]
    status: ContentStatus
    executive_summary: str
    what_happened: str
    who_affected: str
    why_business_matters: str
    key_risks: list[str]
    deadline: str  # "" if none
    action_points: list[str]  # 3–5 practical checks
    micro_delivery: str  # concrete free material offer — not "contact us"
    sources: list[SourceRef] = field(default_factory=list)
    urgency: int = 50  # 0–100
    reliability: float = 0.8
    published_at: str = ""
    editorial: EditorialState = EditorialState.PUBLISHED
    claims_to_verify: list[str] = field(default_factory=list)
    language: str = "sr"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["industries"] = [i.value for i in self.industries]
        d["status"] = self.status.value
        d["editorial"] = self.editorial.value
        d["sources"] = [
            {**asdict(s), "doc_status": s.doc_status.value} for s in self.sources
        ]
        return d


@dataclass
class Subscriber:
    """Free subscription profile — only gets chosen industries."""

    email: str
    name: str = ""
    company: str = ""
    industries: list[Industry] = field(default_factory=list)
    urgent_alerts: bool = True
    weekly_digest: bool = True
    monthly_calendar: bool = True
    language: str = "sr"
    subscribed_at: str = field(default_factory=lambda: date.today().isoformat())
