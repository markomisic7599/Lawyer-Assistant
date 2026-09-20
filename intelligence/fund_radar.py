"""Investment / Fund Radar.

Tracks investors (VC, PE, strategic, DFIs) and their thesis — not primarily
as clients, but as a signal to find companies that may raise from them and
need legal help *before* the round (investment readiness).

Flow:
  Fund thesis → matching companies → fundraising signals → FIT SCORE →
  Parivodic opportunity → warm path → CONTACT NOW outreach
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .models import Opportunity, Radar
from .relationships import PathType, WarmPath, find_warm_path, sample_contacts


class InvestorType(str, Enum):
    VC = "VC"
    PE = "PE"
    STRATEGIC = "Strategic"
    DFI = "DFI / Development"
    FAMILY = "Family office"
    ANGEL = "Angel / syndicate"


class CompanyStage(str, Enum):
    PRE_SEED = "Pre-seed"
    SEED = "Seed"
    SERIES_A = "Series A"
    GROWTH = "Growth"
    BUYOUT = "Buyout / later"


@dataclass
class Fund:
    id: str
    name: str
    investor_type: InvestorType
    fund_size: str
    ticket: str
    stages: list[CompanyStage]
    sectors: list[str]
    geography: str
    thesis: str
    portfolio_examples: list[str] = field(default_factory=list)
    source_url: str = ""
    announced: str = ""


@dataclass
class TargetCompany:
    id: str
    name: str
    sector: str
    stage: CompanyStage
    country: str
    description: str
    estimated_raise: str
    fundraising_signals: list[str]
    decision_maker: str
    decision_role: str
    email_demo: str = ""


@dataclass
class FundFit:
    fund: Fund
    company: TargetCompany
    score: int
    rationale: str
    other_potential_investors: list[str]


@dataclass
class LegalOpportunity:
    label: str
    workstreams: list[str]
    micro_offer: str


@dataclass
class InvestmentLead:
    fit: FundFit
    legal: LegalOpportunity
    warm_path: WarmPath
    pitch_subject: str
    pitch_body: str
    priority_score: float


INVESTMENT_WORKSTREAMS = [
    "Corporate cleanup",
    "Cap table",
    "Founders' arrangements",
    "IP ownership & assignment",
    "ESOP",
    "Regulatory / licensing",
    "Investment DD readiness",
    "Term sheet review",
    "SHA / investment agreement",
    "Negotiation with the fund",
]


def sample_funds() -> list[Fund]:
    return [
        Fund(
            id="fund-forty5",
            name="Forty.5 Ventures",
            investor_type=InvestorType.VC,
            fund_size="$30m",
            ticket="$200k–1m",
            stages=[CompanyStage.PRE_SEED, CompanyStage.SEED],
            sectors=["AI", "Fintech", "Cybersecurity", "Gaming"],
            geography="Serbia / SEE",
            thesis=(
                "New $30m fund seeking AI, fintech, cybersecurity and gaming startups "
                "from Serbia and the wider SEE region; tickets $200k–1m at seed."
            ),
            portfolio_examples=["ExampleFin AI", "SecurePay SEE"],
            source_url="https://example.com/forty5-fund-launch",
            announced="2026-09-01",
        ),
        Fund(
            id="fund-southcentral",
            name="SouthCentral Ventures",
            investor_type=InvestorType.VC,
            fund_size="€40m+",
            ticket="€500k–3m",
            stages=[CompanyStage.SEED, CompanyStage.SERIES_A],
            sectors=["B2B SaaS", "AI", "Fintech", "Marketplace"],
            geography="Western Balkans / SEE",
            thesis="Regional VC focusing on scalable B2B and AI-enabled products from the Balkans.",
            portfolio_examples=["Regional SaaS Co"],
            announced="ongoing",
        ),
        Fund(
            id="fund-ebrd-venture",
            name="EBRD Venture / Partner funds",
            investor_type=InvestorType.DFI,
            fund_size="Programme",
            ticket="€1m–5m+",
            stages=[CompanyStage.SERIES_A, CompanyStage.GROWTH],
            sectors=["Climate tech", "Fintech", "Infrastructure-adjacent tech"],
            geography="Serbia / Western Balkans",
            thesis=(
                "DFI-linked capital for growth companies with regional expansion "
                "and climate / inclusion angle."
            ),
            announced="ongoing",
        ),
        Fund(
            id="fund-strategic-energy",
            name="Strategic Energy Investor (EU utility)",
            investor_type=InvestorType.STRATEGIC,
            fund_size="Corporate venturing",
            ticket="€2m–15m",
            stages=[CompanyStage.GROWTH, CompanyStage.BUYOUT],
            sectors=["Energy", "Renewables", "Grid / flexibility"],
            geography="SEE",
            thesis=(
                "Strategic minority / JV stakes in renewables developers and "
                "flexibility platforms in SEE."
            ),
            announced="2026-08",
        ),
    ]


def sample_companies() -> list[TargetCompany]:
    return [
        TargetCompany(
            id="co-neuralpay",
            name="NeuralPay d.o.o.",
            sector="AI / Fintech",
            stage=CompanyStage.SEED,
            country="Serbia",
            description="AI-driven payment fraud detection for regional banks and PSPs.",
            estimated_raise="€500k–1m",
            fundraising_signals=[
                "Founder publicly announced a new seed round",
                "Hiring Head of Engineering + Compliance lead",
                "Accepted into a regional accelerator this quarter",
            ],
            decision_maker="Marko Jovanović",
            decision_role="Founder / CEO",
            email_demo="marko@neuralpay.example.com",
        ),
        TargetCompany(
            id="co-cybershield",
            name="CyberShield SEE",
            sector="Cybersecurity",
            stage=CompanyStage.SEED,
            country="Serbia",
            description="Managed detection & response for mid-market companies in SEE.",
            estimated_raise="€400k–800k",
            fundraising_signals=[
                "Raising seed; pitch deck shared at Belgrade tech meetup",
                "Won a government digitalisation grant",
            ],
            decision_maker="Ana Kovač",
            decision_role="Founder",
            email_demo="ana@cybershield.example.com",
        ),
        TargetCompany(
            id="co-gameforge",
            name="GameForge Studios",
            sector="Gaming",
            stage=CompanyStage.PRE_SEED,
            country="Serbia",
            description="Mobile mid-core studio with first title in soft launch.",
            estimated_raise="€200k–500k",
            fundraising_signals=[
                "Founder discussing fundraising on public channels",
                "Soft launch metrics published; seeking seed capital",
            ],
            decision_maker="Luka Nikolić",
            decision_role="CEO",
            email_demo="luka@gameforge.example.com",
        ),
        TargetCompany(
            id="co-climatesense",
            name="ClimateSense Balkans",
            sector="Climate tech / AI",
            stage=CompanyStage.SERIES_A,
            country="Serbia",
            description="AI energy-efficiency SaaS for industrial clients across SEE.",
            estimated_raise="€2m–4m",
            fundraising_signals=[
                "Series A process opened with advisors",
                "Internationalisation into Romania / Bulgaria announced",
            ],
            decision_maker="Ivana Petrić",
            decision_role="CEO",
            email_demo="ivana@climatesense.example.com",
        ),
        TargetCompany(
            id="co-flexgrid",
            name="FlexGrid Energy",
            sector="Energy / Renewables",
            stage=CompanyStage.GROWTH,
            country="Serbia",
            description="Flexibility / battery aggregation platform for the Serbian market.",
            estimated_raise="€5m–12m (strategic)",
            fundraising_signals=[
                "In talks with strategic utility investors (public interview)",
                "Expanding team for grid-code compliance",
            ],
            decision_maker="Stefan Marković",
            decision_role="CFO",
            email_demo="stefan@flexgrid.example.com",
        ),
    ]


def _sector_overlap(fund: Fund, company: TargetCompany) -> float:
    cs = company.sector.lower().replace("/", " ")
    hits = 0
    for s in fund.sectors:
        sl = s.lower()
        if sl in cs or any(tok in cs.split() for tok in sl.replace("/", " ").split() if len(tok) > 2):
            hits += 1
    return min(1.0, hits / max(1, min(2, len(fund.sectors))))


def investment_fit_score(fund: Fund, company: TargetCompany) -> FundFit:
    sector = _sector_overlap(fund, company)
    stage = 1.0 if company.stage in fund.stages else 0.25
    geo = (
        1.0
        if any(g in company.country.lower() for g in ("serbia", "see", "balkan"))
        and any(g in fund.geography.lower() for g in ("serbia", "see", "balkan", "western"))
        else 0.4
    )
    signals = min(1.0, 0.35 * len(company.fundraising_signals))
    ticket_ok = 0.85
    if fund.investor_type == InvestorType.STRATEGIC and "energy" in company.sector.lower():
        ticket_ok = 0.95
    if fund.investor_type == InvestorType.DFI and company.stage in {
        CompanyStage.SERIES_A,
        CompanyStage.GROWTH,
    }:
        ticket_ok = 0.9

    raw = 0.30 * sector + 0.25 * stage + 0.15 * geo + 0.20 * signals + 0.10 * ticket_ok
    score = int(round(raw * 100))

    # Demo anchors (clear narrative for the colleague)
    anchors = {
        ("fund-forty5", "co-neuralpay"): 91,
        ("fund-forty5", "co-cybershield"): 88,
        ("fund-forty5", "co-gameforge"): 84,
        ("fund-strategic-energy", "co-flexgrid"): 89,
        ("fund-ebrd-venture", "co-climatesense"): 86,
        ("fund-southcentral", "co-neuralpay"): 78,
    }
    if (fund.id, company.id) in anchors:
        score = anchors[(fund.id, company.id)]

    others = [f.name for f in sample_funds() if f.id != fund.id][:2]
    rationale = (
        f"Sector overlap {sector:.0%}; stage {company.stage.value} "
        f"{'fits' if stage > 0.5 else 'partial'}; "
        f"{len(company.fundraising_signals)} fundraising signal(s); "
        f"geo {fund.geography}."
    )
    return FundFit(
        fund=fund,
        company=company,
        score=score,
        rationale=rationale,
        other_potential_investors=others,
    )


def legal_opportunity_for(fit: FundFit) -> LegalOpportunity:
    if fit.fund.investor_type == InvestorType.STRATEGIC:
        label = "Strategic investment / JV readiness + Financing Round"
        offer = (
            "besplatan preliminary Strategic Investment Readiness Check "
            "(governance, regulatory, offtake / JV issues)"
        )
    elif fit.fund.investor_type == InvestorType.DFI:
        label = "DFI / growth round readiness"
        offer = "besplatan preliminary Investment Readiness Check (DD + ESG / compliance basics)"
    else:
        label = "Investment Readiness + Financing Round"
        offer = "besplatan preliminary Investment Readiness Check"

    return LegalOpportunity(
        label=label,
        workstreams=list(INVESTMENT_WORKSTREAMS),
        micro_offer=offer,
    )


def _warm_for_investment(fit: FundFit) -> WarmPath:
    """Use relationship graph; add co-counsel intro for the flagship NeuralPay demo."""
    from .models import Contact as ModelContact

    company = fit.company
    opp = Opportunity(
        id=f"inv-{company.id}",
        title=f"Foreign investor seed AI fintech {company.name} {company.sector}",
        radar=Radar.FIND,
        score=fit.score,
        why_now="; ".join(company.fundraising_signals[:2]),
        target_org=company.name,
        contact=ModelContact(
            name=company.decision_maker,
            role=company.decision_role,
            is_decision_maker=True,
        ),
    )
    path = find_warm_path(opp, contacts=sample_contacts())

    if path.path_type == PathType.NONE and company.id == "co-neuralpay":
        contacts = {c.id: c for c in sample_contacts()}
        schmidt = contacts.get("c-schmidt")
        if schmidt:
            return WarmPath(
                path_type=PathType.INTERMEDIARY,
                chain=["Milan Parivodić", schmidt.name, company.decision_maker],
                intermediary=schmidt,
                decision_maker=None,
                strength=schmidt.strength,
                ask=(
                    f"Milan asks {schmidt.name} for an intro to "
                    f"{company.decision_maker} ({company.name})."
                ),
                suggested_owner="Milan Parivodić",
                draft_message="",
                why=(
                    f"Co-counsel / FDI channel: {schmidt.name} "
                    f"(strength {schmidt.strength}/100) as credible intermediary."
                ),
            )
    return path


def build_pitch(fit: FundFit, legal: LegalOpportunity, warm: WarmPath) -> tuple[str, str]:
    company = fit.company
    fund = fit.fund
    who = company.decision_maker.split()[0] if company.decision_maker else "there"
    subject = f"{company.name}: preliminary investment-readiness review"
    body = (
        f"Dear {who},\n\n"
        f"We have been following fundraising activity in your sector and noted that "
        f"new regional funds — including {fund.name} ({fund.fund_size}, tickets "
        f"{fund.ticket}) — are actively looking for companies with a profile close to "
        f"{company.name} ({company.sector}, {company.stage.value}).\n\n"
        f"Based on publicly visible signals ({company.fundraising_signals[0].lower()}), "
        f"it appears you may be entering a fundraising phase. If useful, we can prepare a "
        f"preliminary investment-readiness review to flag issues an institutional investor "
        f"would typically open during DD "
        f"(corporate, cap table, IP, founders' arrangements, regulatory).\n\n"
        f"Happy to send a short checklist first — no charge.\n\n"
        f"Kind regards,\nMilan Parivodić\nPartner, Parivodic Lawyers"
    )
    if warm.path_type != PathType.NONE and warm.intermediary:
        # Outreach goes to intermediary first
        mid = warm.intermediary.name.split()[0]
        subject = f"Intro request: {company.name} × investment readiness"
        body = (
            f"Dear {mid},\n\n"
            f"Hope you are well. We are looking at {company.name} "
            f"({company.sector}, {company.stage.value}) in light of {fund.name}'s thesis "
            f"({', '.join(fund.sectors[:3])}; {fund.geography}). "
            f"Would you be open to introducing us to {company.decision_maker} so we can "
            f"offer a free preliminary Investment Readiness Check ahead of their round?\n\n"
            f"Best regards,\nMilan"
        )
    return subject, body


def rank_leads(min_score: int = 75) -> list[InvestmentLead]:
    """All fund × company pairs above threshold, with legal opp + warm path + pitch."""
    leads: list[InvestmentLead] = []
    for fund in sample_funds():
        for company in sample_companies():
            fit = investment_fit_score(fund, company)
            if fit.score < min_score:
                continue
            legal = legal_opportunity_for(fit)
            warm = _warm_for_investment(fit)
            subj, body = build_pitch(fit, legal, warm)
            access = {
                PathType.DIRECT: 95,
                PathType.FIRST_DEGREE: 80,
                PathType.INTERMEDIARY: 75,
                PathType.NONE: 40,
            }[warm.path_type]
            priority = round(fit.score * 0.7 + access * 0.3, 1)
            leads.append(
                InvestmentLead(
                    fit=fit,
                    legal=legal,
                    warm_path=warm,
                    pitch_subject=subj,
                    pitch_body=body,
                    priority_score=priority,
                )
            )
    leads.sort(key=lambda L: L.priority_score, reverse=True)
    return leads


def fits_for_fund(fund_id: str, min_score: int = 60) -> list[FundFit]:
    fund = next(f for f in sample_funds() if f.id == fund_id)
    fits = [investment_fit_score(fund, c) for c in sample_companies()]
    return sorted([f for f in fits if f.score >= min_score], key=lambda f: -f.score)
