"""Relationship Intelligence — warm path to the mandate.

Opportunity Radar finds the work. This module finds the *path* to the work:

  Master Contact Database → Relationship Graph → Warm-path finder →
  Why-now engine → Daily BD Actions (top 3–5)

Uses only illustrative, lawfully-available demo data. Production would connect
mailbox / CRM with GDPR-ZZPL controls — never scrape private LinkedIn data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .models import Opportunity, Radar


class PathType(str, Enum):
    DIRECT = "DIRECT CONTACT"
    FIRST_DEGREE = "1st-degree internal relationship"
    INTERMEDIARY = "Credible intermediary"
    NONE = "NO WARM PATH → cold outreach"


@dataclass
class Contact:
    """One deduplicated person in the master contact database."""

    id: str
    name: str
    company: str
    role: str
    email: str = ""
    phone: str = ""
    linkedin: str = ""  # public profile URL only
    country: str = "Serbia"
    industry: str = ""
    known_by: str = ""  # which Parivodic lawyer owns the relationship
    origin: str = ""  # business card / mailbox / CRM
    strength: int = 50  # 0–100 relationship strength
    email_exchanges: int = 0
    last_contact: str = ""  # e.g. "March 2026" or "14 months ago"
    was_client: bool = False
    notes: str = ""


@dataclass
class GraphEdge:
    """A → B link in the relationship graph."""

    source_id: str  # contact id or "parivodic"
    target_id: str
    relation: str  # "knows", "works_at", "advises", "former_colleague", …


@dataclass
class WarmPath:
    path_type: PathType
    chain: list[str]  # human-readable: ["Milan", "Müller", "Zhang"]
    intermediary: Contact | None
    decision_maker: Contact | None
    strength: int
    ask: str
    suggested_owner: str
    draft_message: str
    why: str


@dataclass
class ContactTrigger:
    """Public business trigger for an existing contact — Why now?"""

    contact_id: str
    score: int
    headline: str
    why_now: str
    likely_needs: list[str]
    suggested_owner: str
    draft: str


@dataclass
class DailyAction:
    """One of the 3–5 morning BD actions."""

    priority: int
    title: str
    opportunity: str
    decision_maker: str
    warm_path_summary: str
    relationship_note: str
    suggested_action: str
    why_parivodic: str
    score: float  # composite ranking
    draft: str
    owner: str


# ── Demo master contacts (deduplicated profiles) ─────────────────────────────


def sample_contacts() -> list[Contact]:
    return [
        Contact(
            id="c-muller",
            name="Peter Müller",
            company="Alpine Advisory GmbH",
            role="Senior Consultant — Energy & Infrastructure",
            email="p.mueller@alpine-advisory.example.com",
            linkedin="https://www.linkedin.com/in/example-mueller",
            country="Austria",
            industry="Energy / Infrastructure",
            known_by="Milan Parivodić",
            origin="Mailbox + prior mandate referral",
            strength=82,
            email_exchanges=17,
            last_contact="March 2026",
            was_client=False,
            notes="Strong professional relationship; referred two matters previously.",
        ),
        Contact(
            id="c-zhang",
            name="Zhang Wei",
            company="Reliance Energy International",
            role="VP International Investments",
            email="z.wei@reliance-energy.example.com",
            country="China / Serbia projects",
            industry="Energy / FDI",
            known_by="",
            origin="Public bio / project announcement",
            strength=5,
            email_exchanges=0,
            last_contact="Never contacted",
            notes="Decision-maker on Serbian investments — no direct relationship yet.",
        ),
        Contact(
            id="c-hoffmann",
            name="Anna Hoffmann",
            company="EuroBank Project Finance",
            role="Head of Project Finance — SEE",
            email="a.hoffmann@eurobank.example.com",
            country="Austria",
            industry="Banking / Finance",
            known_by="Milan Parivodić",
            origin="Business card + mailbox",
            strength=71,
            email_exchanges=9,
            last_contact="6 weeks ago",
            was_client=True,
            notes="Former client on security packages; frequent referral source.",
        ),
        Contact(
            id="c-petrovic",
            name="Ivan Petrović",
            company="Corridor EPC Consortium",
            role="Project Director",
            email="i.petrovic@corridor-epc.example.com",
            country="Serbia",
            industry="Infrastructure & Construction",
            known_by="J. Branković",
            origin="Business card (Belgrade chamber event)",
            strength=48,
            email_exchanges=3,
            last_contact="14 months ago",
            notes="Met once; relationship gone quiet — reactivation candidate.",
        ),
        Contact(
            id="c-tanaka",
            name="Kenji Tanaka",
            company="Mitsubishi Power",
            role="Regional Business Development",
            email="k.tanaka@mhi-power.example.com",
            country="Japan / SEE",
            industry="Energy",
            known_by="Milan Parivodić",
            origin="Business card",
            strength=35,
            email_exchanges=2,
            last_contact="14 months ago",
            notes="Card on file; no recent contact.",
        ),
        Contact(
            id="c-novak",
            name="Elena Novak",
            company="Chamber of Commerce — Foreign Investors",
            role="Director, Investor Relations",
            email="e.novak@chamber.example.com",
            country="Serbia",
            industry="FDI / Institutions",
            known_by="J. Branković",
            origin="Mailbox",
            strength=64,
            email_exchanges=11,
            last_contact="3 weeks ago",
        ),
        Contact(
            id="c-schmidt",
            name="Thomas Schmidt",
            company="Vienna International Counsel LLP",
            role="Partner — CEE Corporate",
            email="t.schmidt@vicounsel.example.com",
            country="Austria",
            industry="Legal / FDI",
            known_by="Milan Parivodić",
            origin="Mailbox + co-counsel",
            strength=78,
            email_exchanges=22,
            last_contact="2 weeks ago",
            notes="Regular co-counsel channel for inbound investors.",
        ),
    ]


def sample_edges() -> list[GraphEdge]:
    """Parivodic → contact → company → decision-maker graph (demo)."""
    return [
        GraphEdge("parivodic", "c-muller", "knows (Milan)"),
        GraphEdge("c-muller", "c-zhang", "advises / professional link"),
        GraphEdge("parivodic", "c-hoffmann", "knows (Milan) · former client"),
        GraphEdge("c-hoffmann", "c-petrovic", "financier ↔ sponsor projects"),
        GraphEdge("parivodic", "c-petrovic", "knows (Branković)"),
        GraphEdge("parivodic", "c-tanaka", "knows (Milan) · card"),
        GraphEdge("parivodic", "c-novak", "knows (Branković)"),
        GraphEdge("parivodic", "c-schmidt", "knows (Milan) · co-counsel"),
        GraphEdge("c-schmidt", "c-zhang", "possible intro channel (FDI)"),
        GraphEdge("c-novak", "c-zhang", "chamber / investor network"),
    ]


def _by_id(contacts: list[Contact]) -> dict[str, Contact]:
    return {c.id: c for c in contacts}


# ── Warm-path finder ─────────────────────────────────────────────────────────


def find_warm_path(
    opp: Opportunity,
    contacts: list[Contact] | None = None,
    edges: list[GraphEdge] | None = None,
) -> WarmPath:
    """Mandatory step before cold outreach: do we have a warm path?"""
    contacts = contacts or sample_contacts()
    edges = edges or sample_edges()
    idx = _by_id(contacts)
    org = (opp.target_org or "").lower()
    title = (opp.title or "").lower()
    entity_blob = " ".join(e.name.lower() for e in opp.entities)
    target_blob = f"{org} {title} {entity_blob}"
    _ = edges  # reserved for full graph walk in production

    hay = target_blob

    # Prefer known intermediary / 1st-degree routes before loose org-token matches.

    # Intermediary: FDI / battery / mining → Müller → Zhang (Srđan example pattern)
    if any(k in hay for k in ("battery", "foreign", "investor", "reliance", "fdi", "china", "lithium", "mining")):
        muller = idx.get("c-muller")
        zhang = idx.get("c-zhang")
        if muller and zhang:
            draft = (
                f"Dear Peter,\n\n"
                f"I hope you are well. We have been following the Serbian developments "
                f"involving Reliance Energy / related FDI. Given your professional link "
                f"with Zhang Wei, would you be open to introducing us so we can offer a "
                f"short preliminary note on Serbian implementation counsel "
                f"(investment, permitting, construction)?\n\n"
                f"No pressure either way — grateful for your view.\n\n"
                f"Best regards,\nMilan"
            )
            return WarmPath(
                path_type=PathType.INTERMEDIARY,
                chain=["Milan Parivodić", "Peter Müller", "Zhang Wei"],
                intermediary=muller,
                decision_maker=zhang,
                strength=muller.strength,
                ask=(
                    "Milan contacts Müller — not Zhang directly. "
                    "Ask: introduction to Zhang regarding Serbian implementation counsel."
                ),
                suggested_owner="Milan Parivodić",
                draft_message=draft,
                why=(
                    f"Warm path found: Zhang ↔ Müller ↔ Milan. "
                    f"Relationship with Müller: Strong ({muller.strength}/100); "
                    f"{muller.email_exchanges} email exchanges; last contact {muller.last_contact}."
                ),
            )

    if any(k in hay for k in ("corridor", "motorway", "eot", "unpaid")):
        hoff = idx.get("c-hoffmann")
        petro = idx.get("c-petrovic")
        if hoff and petro:
            # Prefer direct to Petrović if we know him; else Hoffmann intro
            if petro.known_by and petro.strength >= 30:
                return WarmPath(
                    path_type=PathType.DIRECT,
                    chain=[petro.known_by, petro.name],
                    intermediary=None,
                    decision_maker=petro,
                    strength=petro.strength,
                    ask=f"{petro.known_by} contacts {petro.name} directly (reactivation).",
                    suggested_owner=petro.known_by,
                    draft_message=(
                        f"Dear Ivan,\n\nWe have been following the corridor section developments. "
                        f"If helpful, I can send a short checklist of contractual points worth "
                        f"checking before the next step.\n\nBest regards,\nJelena"
                    ),
                    why=(
                        f"Direct contact at {petro.company}; strength {petro.strength}/100; "
                        f"last contact {petro.last_contact}."
                    ),
                )
            draft = (
                f"Dear Anna,\n\n"
                f"Given the publicly flagged payment / EOT issues on the corridor section, "
                f"would you be comfortable connecting us with the Project Director side "
                f"if helpful? We can send a short checklist of contractual points first.\n\n"
                f"Best regards,\nMilan"
            )
            return WarmPath(
                path_type=PathType.INTERMEDIARY,
                chain=["Milan Parivodić", "Anna Hoffmann", "Ivan Petrović"],
                intermediary=hoff,
                decision_maker=petro,
                strength=hoff.strength,
                ask="Milan contacts Hoffmann for a warm intro toward the EPC / Project Director.",
                suggested_owner="Milan Parivodić",
                draft_message=draft,
                why=(
                    f"Financier link: Hoffmann (strength {hoff.strength}/100, former client) "
                    f"↔ project side. Prefer warm route before cold outreach."
                ),
            )

    if any(k in hay for k in ("solar", "grid", "ipp", "renewable")):
        tanaka = idx.get("c-tanaka")
        if tanaka:
            return WarmPath(
                path_type=PathType.FIRST_DEGREE,
                chain=[tanaka.known_by or "Milan Parivodić", tanaka.name],
                intermediary=None,
                decision_maker=tanaka,
                strength=tanaka.strength,
                ask=f"{tanaka.known_by} reactivates contact with {tanaka.name}.",
                suggested_owner=tanaka.known_by or "Milan Parivodić",
                draft_message=(
                    f"Dear Kenji,\n\nIt has been a while since we last spoke. "
                    f"We noticed recent energy / grid developments in Serbia that may be "
                    f"relevant — happy to send a short one-pager if useful.\n\nBest regards,\nMilan"
                ),
                why=(
                    f"1st-degree contact on file (card); strength {tanaka.strength}/100; "
                    f"last contact {tanaka.last_contact}."
                ),
            )

    # Direct: only when company name clearly overlaps target_org (not entity labels)
    for c in contacts:
        cl = c.company.lower()
        if not org or not c.known_by or c.strength < 30:
            continue
        skip = {
            "project", "finance", "international", "energy", "group", "advisory",
            "consortium", "foreign", "investor", "investors", "company",
        }
        tokens = [t for t in cl.replace("-", " ").split() if len(t) >= 5 and t not in skip]
        if any(t in org for t in tokens) or (len(cl) > 6 and cl in org):
            return WarmPath(
                path_type=PathType.DIRECT,
                chain=[c.known_by, c.name],
                intermediary=None,
                decision_maker=c,
                strength=c.strength,
                ask=f"{c.known_by} contacts {c.name} directly.",
                suggested_owner=c.known_by,
                draft_message=(
                    f"Dear {c.name.split()[0]},\n\n"
                    f"I hope you are well. We noticed recent developments around "
                    f"{opp.target_org or 'your project'} — happy to send a short practical "
                    f"note if useful.\n\nBest regards,\n{c.known_by}"
                ),
                why=f"Direct contact at {c.company}; strength {c.strength}/100.",
            )

    return WarmPath(
        path_type=PathType.NONE,
        chain=[],
        intermediary=None,
        decision_maker=None,
        strength=0,
        ask="No warm path in the database → proceed with cold pitch (value-first).",
        suggested_owner="Milan Parivodić",
        draft_message="",
        why="No direct contact, 1st-degree link or credible intermediary matched.",
    )


# ── Why-now monitoring for existing contacts ─────────────────────────────────


def contact_triggers(contacts: list[Contact] | None = None) -> list[ContactTrigger]:
    contacts = contacts or sample_contacts()
    idx = _by_id(contacts)
    out: list[ContactTrigger] = []

    tanaka = idx.get("c-tanaka")
    if tanaka:
        out.append(
            ContactTrigger(
                contact_id=tanaka.id,
                score=91,
                headline="CONTACT NOW — Mitsubishi Power linked to new Serbian energy work",
                why_now=(
                    f"We have a direct contact ({tanaka.name}); last contact {tanaka.last_contact}; "
                    "company publicly associated with a new energy project in Serbia."
                ),
                likely_needs=["procurement", "construction", "permitting", "claims"],
                suggested_owner=tanaka.known_by or "Milan Parivodić",
                draft=(
                    f"Dear Kenji,\n\nCongratulations on the recent Serbian energy developments. "
                    f"If useful, I can send a short checklist of permitting / contracting points "
                    f"teams typically verify at this stage.\n\nBest regards,\nMilan"
                ),
            )
        )

    petro = idx.get("c-petrovic")
    if petro:
        out.append(
            ContactTrigger(
                contact_id=petro.id,
                score=88,
                headline="CONTACT NOW — Corridor EPC: unpaid certificates / EOT dispute signal",
                why_now=(
                    f"Known contact ({petro.role}); last contact {petro.last_contact}; "
                    "public dispute signal creates a reason to reconnect now."
                ),
                likely_needs=["EOT / claims", "structured settlement", "notices"],
                suggested_owner=petro.known_by or "J. Branković",
                draft=(
                    f"Dear Ivan,\n\nWe have been following the corridor section developments. "
                    f"If helpful, I can send a short checklist of contractual points worth "
                    f"checking before the next step.\n\nBest regards,\nJelena"
                ),
            )
        )

    return sorted(out, key=lambda t: t.score, reverse=True)


# ── Daily BD Actions (top 3–5) ───────────────────────────────────────────────


def _composite(
    opportunity_quality: float,
    mandate_value: float,
    fit: float,
    urgency: float,
    strength: float,
    access: float,
) -> float:
    """Opportunity × value × fit × urgency × relationship × access (0–100 scale inputs)."""
    return round(
        (opportunity_quality / 100)
        * (mandate_value / 100)
        * (fit / 100)
        * (urgency / 100)
        * max(strength, 15)  # floor so cold paths still rank if huge opp
        / 100
        * (access / 100)
        * 100,
        1,
    )


def daily_bd_actions(
    opportunities: list[Opportunity],
    contacts: list[Contact] | None = None,
) -> list[DailyAction]:
    """Morning brief: only the best 3–5 actions, not 40 news items."""
    contacts = contacts or sample_contacts()
    actions: list[DailyAction] = []

    # From opportunity radar + warm path
    for opp in sorted(opportunities, key=lambda o: o.score, reverse=True)[:8]:
        path = find_warm_path(opp, contacts)
        access = {
            PathType.DIRECT: 95,
            PathType.FIRST_DEGREE: 80,
            PathType.INTERMEDIARY: 75,
            PathType.NONE: 35,
        }[path.path_type]
        mandate = 85 if opp.radar == Radar.STUCK_PROJECT else 75 if opp.radar == Radar.FIND else 70
        urgency = min(100, opp.score)
        fit = 90 if opp.radar != Radar.REGULATORY_MONEY else 80
        score = _composite(opp.score, mandate, fit, urgency, float(path.strength or 20), access)

        dm = (
            path.decision_maker.name
            if path.decision_maker
            else (opp.contact.name or opp.contact.role or "TBD")
        )
        warm = (
            f"{path.path_type.value}: {' → '.join(path.chain)}"
            if path.chain
            else path.path_type.value
        )
        rel_note = path.why
        action = path.ask
        draft = path.draft_message
        if path.path_type == PathType.NONE:
            action = "Send value-first cold pitch (micro-delivery), then wait."
            draft = "(Use Cold Pitch tab for the generated message.)"

        why_p = {
            Radar.FIND: "foreign investment + permitting + construction / government interface",
            Radar.STUCK_PROJECT: "construction / claims + structured negotiation before dispute",
            Radar.REGULATORY_MONEY: "competition / commercial compliance + client reactivation",
        }[opp.radar]

        actions.append(
            DailyAction(
                priority=0,
                title=f"New opportunity: {opp.target_org or opp.title[:48]}",
                opportunity=opp.title,
                decision_maker=dm,
                warm_path_summary=warm,
                relationship_note=rel_note,
                suggested_action=action,
                why_parivodic=why_p,
                score=score,
                draft=draft,
                owner=path.suggested_owner,
            )
        )

    # From contact triggers (relationship-first)
    for t in contact_triggers(contacts):
        c = _by_id(contacts).get(t.contact_id)
        if not c:
            continue
        score = _composite(t.score, 80, 85, t.score, float(c.strength), 90)
        actions.append(
            DailyAction(
                priority=0,
                title=t.headline,
                opportunity=t.why_now,
                decision_maker=f"{c.name} · {c.role}",
                warm_path_summary=f"{PathType.DIRECT.value}: {c.known_by} → {c.name}",
                relationship_note=(
                    f"Strength {c.strength}/100; {c.email_exchanges} exchanges; "
                    f"last contact {c.last_contact}."
                ),
                suggested_action=f"{t.suggested_owner} contacts {c.name} today.",
                why_parivodic=", ".join(t.likely_needs),
                score=score,
                draft=t.draft,
                owner=t.suggested_owner,
            )
        )

    actions.sort(key=lambda a: a.score, reverse=True)
    top = actions[:5]
    for i, a in enumerate(top, 1):
        a.priority = i
    return top
