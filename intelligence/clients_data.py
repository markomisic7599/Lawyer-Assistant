"""The firm's existing client database (illustrative demo data).

This is the private half of the intelligence system: the firm's own relationships.
Fusing it with the public opportunity feed is what powers the MATCH phase —
existing-client reactivation, warm-intro routes, and conflict awareness.

All data here is fictional and for demo purposes only.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import Opportunity


@dataclass
class ClientContact:
    name: str
    role: str


@dataclass
class Client:
    id: str
    name: str
    sector: str
    status: str  # "Active" | "Dormant" | "Prospect"
    owner: str  # relationship partner
    markets: str
    since: int
    last_matter: str
    last_contact: str  # relative, e.g. "3 weeks ago"
    contacts: list[ClientContact] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)  # for matching against opportunities
    notes: str = ""

    def match_terms(self) -> list[str]:
        return [self.name, *self.aliases]


def sample_clients() -> list[Client]:
    return [
        Client(
            id="cl-cchbc",
            name="Coca-Cola HBC Srbija",
            sector="FMCG / Beverages",
            status="Active",
            owner="M. Parivodić",
            markets="Serbia",
            since=2016,
            last_matter="Distribution agreements review",
            last_contact="3 weeks ago",
            contacts=[
                ClientContact("", "Legal Director"),
                ClientContact("", "Head of Compliance"),
            ],
            tags=["competition", "distribution", "commercial"],
            aliases=["Coca-Cola HBC", "Coca-Cola", "CCHBC"],
        ),
        Client(
            id="cl-henkel",
            name="Henkel Srbija",
            sector="Consumer / Adhesives",
            status="Active",
            owner="J. Branković",
            markets="Serbia, Montenegro",
            since=2018,
            last_matter="Supplier contract dispute",
            last_contact="6 weeks ago",
            contacts=[ClientContact("", "General Counsel")],
            tags=["commercial", "disputes"],
            aliases=["Henkel"],
        ),
        Client(
            id="cl-abbott",
            name="Abbott Laboratories",
            sector="Pharma / Healthcare",
            status="Dormant",
            owner="M. Parivodić",
            markets="Serbia, Western Balkans",
            since=2015,
            last_matter="Regulatory approval support",
            last_contact="14 months ago",
            contacts=[ClientContact("", "Regulatory Affairs Lead")],
            tags=["pharma", "regulatory"],
            aliases=["Abbott"],
            notes="Relationship gone quiet — strong reactivation candidate.",
        ),
        Client(
            id="cl-reddys",
            name="Dr. Reddy's Laboratories",
            sector="Pharma / Healthcare",
            status="Active",
            owner="J. Branković",
            markets="Serbia",
            since=2019,
            last_matter="Employment restructuring",
            last_contact="2 months ago",
            contacts=[ClientContact("", "HR Director"), ClientContact("", "Country Manager")],
            tags=["employment", "pharma"],
            aliases=["Dr. Reddy's", "Dr Reddy", "Reddy's"],
        ),
        Client(
            id="cl-balkan-infra",
            name="Balkan Infrastructure JV",
            sector="Construction / Infrastructure",
            status="Active",
            owner="M. Parivodić",
            markets="Serbia, North Macedonia",
            since=2021,
            last_matter="EPC contract negotiation",
            last_contact="1 week ago",
            contacts=[ClientContact("", "Project Director")],
            tags=["construction", "EPC", "claims"],
            aliases=["Balkan Infrastructure", "EPC contractor"],
        ),
        Client(
            id="cl-vetropark",
            name="Vetropark Energija",
            sector="Energy / Renewables",
            status="Dormant",
            owner="J. Branković",
            markets="Serbia",
            since=2020,
            last_matter="Grid-connection advisory",
            last_contact="10 months ago",
            contacts=[ClientContact("", "CFO")],
            tags=["energy", "renewables", "regulatory"],
            aliases=["Vetropark", "Solar IPP", "IPP sponsor"],
            notes="Prior grid-connection work — relevant to current IPP disputes.",
        ),
        Client(
            id="cl-aik",
            name="Regional Development Bank",
            sector="Banking / Finance",
            status="Active",
            owner="M. Parivodić",
            markets="Western Balkans",
            since=2017,
            last_matter="Project-finance security package",
            last_contact="5 weeks ago",
            contacts=[ClientContact("", "Head of Project Finance")],
            tags=["finance", "project-finance", "referral-source"],
            aliases=["Development Bank", "Regional Development Bank", "financier"],
            notes="Frequent referral source for sponsors needing local counsel.",
        ),
        Client(
            id="cl-delta-retail",
            name="Delta Retail Group",
            sector="Retail / Distribution",
            status="Active",
            owner="J. Branković",
            markets="Serbia",
            since=2019,
            last_matter="Franchise & distribution agreements",
            last_contact="4 months ago",
            contacts=[ClientContact("", "Legal Director")],
            tags=["distribution", "commercial", "competition"],
            aliases=["Delta Retail", "Delta"],
        ),
    ]


def match_opportunities(client: Client, opps: list[Opportunity]) -> list[Opportunity]:
    """Find live opportunities that reference this client (by name/alias)."""
    terms = [t.lower() for t in client.match_terms() if t]
    matched: list[Opportunity] = []
    for o in opps:
        haystack = " ".join(
            [
                o.target_org or "",
                o.why_now or "",
                o.rationale or "",
                o.title or "",
                " ".join(e.name for e in o.entities),
            ]
        ).lower()
        if any(term in haystack for term in terms):
            matched.append(o)
    return matched
