"""Solution-first BD engine (the BUILD POSITION phase).

Instead of "we saw you have a problem and can help", this produces
"we saw the problem, analysed it, and here is how we think it could be solved."

For each serious lead it builds a disciplined, public-facts-only position:

    DIAGNOSIS -> HYPOTHESIS -> ROUTE -> (NOT EXECUTION)

giving the target enough to see we understand the problem and have an idea —
but not so much that we've done the mandate for free. Everything here is drafted
from publicly available information only; the real work starts once they engage.

Template-based so it works offline; the same interface can later be LLM-backed.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import config
from .models import Opportunity, Radar

DISCLAIMER = (
    "Based solely on publicly available information, we have identified a "
    "potential route which may be worth exploring."
)

# Conflicts / confidentiality gate — must be cleared before any targeted advice.
CONFLICT_CHECKLIST = [
    "Counterparty conflict-checked against existing clients",
    "Uses only publicly available information",
    "No confidential information from any other matter is used",
    "Confidentiality preserved until the target formally engages",
]


@dataclass
class SolutionBrief:
    problem: str
    what_we_know: list[str]
    serbian_legal_angle: str
    preliminary_diagnosis: str
    free_solution_concept: list[str]  # the ROUTE, step by step (no execution)
    what_to_verify: list[str]
    paid_mandate: str
    decision_maker: str
    warm_route: str
    follow_up: str
    email_subject: str
    email_body: str
    linkedin_message: str
    conflict_checklist: list[str] = field(default_factory=lambda: list(CONFLICT_CHECKLIST))


def _fact(opp: Opportunity) -> str:
    """The single most specific public fact to lead with."""
    why = " ".join((opp.why_now or "").split())
    if not why:
        return f"recent developments concerning {opp.target_org or 'the project'}"
    first = why.split(". ")[0].rstrip(".")
    return first[0].lower() + first[1:] if first else why


def _decision_maker(opp: Opportunity) -> str:
    dm = opp.contact.name or opp.contact.role or "the relevant decision-maker"
    if opp.contact.is_decision_maker:
        dm += " (decision-maker)"
    return dm


def _warm_route(opp: Opportunity) -> str:
    for e in opp.entities:
        role = e.role.lower()
        if any(k in role for k in ("financ", "bank", "counsel", "advis")):
            return f"Potential warm introduction via {e.name} ({e.role})."
    if opp.suggested_actions:
        for a in opp.suggested_actions:
            if "warm" in a.lower() or "intro" in a.lower():
                return a
    return "Direct decision-maker outreach; look for a warm route before going cold."


def build_solution(opp: Opportunity) -> SolutionBrief:
    firm = config.FIRM_NAME
    org = opp.target_org or "the project"
    fact = _fact(opp)
    dm = _decision_maker(opp)

    if opp.radar == Radar.STUCK_PROJECT:
        problem = opp.why_now or "A high-value project appears to be stuck or in dispute."
        what_we_know = [
            f"Target: {org}.",
            f"Public signal: {fact}.",
            "Value at stake and timeline pressure make an early, structured resolution attractive.",
        ]
        legal = (
            "Serbian contract law (ZOO) and the underlying construction/FIDIC regime, "
            "combined with the public procurement framework, govern delay, "
            "extension-of-time entitlement, notices and the allocation of employer vs "
            "contractor risk."
        )
        diagnosis = (
            "At least part of the delay may originate from employer-controlled matters "
            "(e.g. late site access or delayed instructions) rather than contractor fault. "
            "If confirmed by the contractual record, this affects entitlement and leverage."
        )
        route = [
            "Establish causation and separate employer-risk delay from contractor delay",
            "Preserve the relevant notices and extension-of-time entitlement",
            "Distinguish concurrent delay and quantify the critical-path effect",
            "Use the resulting position as leverage in a structured settlement negotiation "
            "with the Employer, before it becomes a formal dispute",
        ]
        verify = [
            "The Contract and any special conditions",
            "The accepted programme and progress records",
            "Correspondence, notices and instructions",
            "The employer's stated reasons for refusing the EOT",
        ]
        mandate = (
            "Confidential review of Contract, programme and correspondence, followed by a "
            "negotiation strategy — with governmental interface and a dispute/arbitration "
            "fallback if required."
        )
        subject = f"{org}: a possible route before this becomes a formal dispute"
        body = (
            f"Dear {opp.contact.name or 'Sir or Madam'},\n\n"
            f"We have been following the developments concerning {org}. Based solely on the "
            f"publicly available information, one aspect caught our attention: {fact}.\n\n"
            "If our understanding of the underlying facts is correct, we believe there may be "
            "a way to separate employer-risk delay from contractor delay, preserve the relevant "
            "extension-of-time entitlement, and use that position as the basis for a structured "
            "negotiation with the Employer before the matter develops into a formal dispute.\n\n"
            "We have dealt with comparable issues on major Serbian energy and infrastructure "
            "projects and would be happy to share our preliminary view on a short call, without "
            "charge. If useful, we could thereafter determine whether a more detailed "
            "contractual/legal review is warranted.\n\n"
            f"Kind regards,\nParivodić / Branković\n{firm}"
        )
    elif opp.radar == Radar.REGULATORY_MONEY:
        problem = opp.why_now or "A regulatory change creates a compliance or opportunity trigger."
        what_we_know = [
            f"Affected: {org}.",
            f"Regulatory signal: {fact}.",
            "The change likely forces action or unlocks a benefit for market participants.",
        ]
        legal = (
            "The new rules interact with existing Serbian commercial/competition (or "
            "state-aid) requirements and any sector-specific regime; the key is which of the "
            "client's specific arrangements are exposed."
        )
        diagnosis = (
            "Based on the client's publicly known model, specific points likely deserve "
            "particular attention — rather than a generic compliance overhaul."
        )
        route = [
            "Map the change onto the client's publicly known structure",
            "Identify the two or three points that genuinely require attention",
            "Where relevant, combine compliance with an available benefit "
            "(subject to eligibility / state-aid intensity)",
            "Prioritise actions by deadline and exposure",
        ]
        verify = [
            "The client's actual contracts / distribution model",
            "Existing compliance posture and prior filings",
            "Eligibility and intensity limits (if incentives are involved)",
        ]
        mandate = (
            "Targeted contract/compliance review and, where applicable, an incentive or "
            "re-papering workstream — scoped to the points that matter."
        )
        subject = "A recent Serbian regulatory change — the two points that matter for you"
        body = (
            f"Dear {opp.contact.name or 'Sir or Madam'},\n\n"
            f"We wanted to flag a recent development: {fact}.\n\n"
            "Based on your publicly known model, we believe points X and Y in particular "
            "deserve attention, and there may be a route to combine the required compliance "
            "with an available benefit, subject to eligibility.\n\n"
            "We would be happy to share our preliminary view on a short call, without charge, "
            "and to then determine whether a more detailed review is warranted.\n\n"
            f"Kind regards,\nParivodić / Branković\n{firm}"
        )
    else:  # FIND
        problem = opp.why_now or "A project is entering a phase that creates immediate legal work."
        what_we_know = [
            f"Target: {org}.",
            f"Phase-change signal: {fact}.",
            "Entering procurement/permitting/construction spawns several parallel workstreams.",
        ]
        legal = (
            "Serbian permitting, land, construction, employment/immigration and "
            "incentive/state-aid frameworks all apply as the project mobilises; sequencing "
            "them correctly protects the schedule."
        )
        diagnosis = (
            "The project will need reliable local counsel to sequence permits, contracting and "
            "employment — and to manage the government interface — at exactly this phase."
        )
        route = [
            "Prepare a preliminary Serbia implementation roadmap",
            "Sequence incentives, land, permits, construction and employment",
            "Identify the institutional/government interface and likely bottlenecks",
            "Flag the critical-path legal steps that protect the timeline",
        ]
        verify = [
            "Project scope, site and timeline",
            "Corporate/investment structure",
            "Which permits and approvals are already underway",
        ]
        mandate = (
            "Implementation support across permitting, contracting, employment and the "
            "government interface as the project proceeds."
        )
        subject = f"Serbian implementation roadmap for {org}"
        body = (
            f"Dear {opp.contact.name or 'Sir or Madam'},\n\n"
            f"We track the market closely and noted that {fact}.\n\n"
            "Based solely on the publicly available information, we believe there may be a way "
            "to protect your timeline by sequencing the Serbian permitting, contracting and "
            "employment steps correctly, and by managing the government interface early.\n\n"
            "We have supported comparable investments in Serbia and would be happy to share a "
            "short preliminary roadmap on a call, without charge, and then determine whether a "
            "more detailed review is warranted.\n\n"
            f"Kind regards,\nParivodić / Branković\n{firm}"
        )

    linkedin = (
        f"Hi {opp.contact.name.split(' ')[0] if opp.contact.name else 'there'} — we've been "
        f"following {org}. Based on public information, we think there may be a specific route "
        f"worth exploring on {fact.split(',')[0]}. Happy to share a brief preliminary view, no "
        f"charge — open to a short call?"
    )

    return SolutionBrief(
        problem=problem,
        what_we_know=what_we_know,
        serbian_legal_angle=legal,
        preliminary_diagnosis=diagnosis,
        free_solution_concept=route,
        what_to_verify=verify,
        paid_mandate=mandate,
        decision_maker=dm,
        warm_route=_warm_route(opp),
        follow_up="If no reply in 5 business days: send a short, specific follow-up "
        "referencing one additional public fact.",
        email_subject=subject,
        email_body=body,
        linkedin_message=linkedin,
    )
