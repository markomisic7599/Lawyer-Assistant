"""Illustrative sample opportunities for the demo.

These are realistic-looking but fictional scenarios used only to show how the
product looks and feels. They let a colleague explore the dashboard without any
API keys or live data. Replace with a live sweep (`run_daily`) for real use.
"""

from __future__ import annotations

from .models import Contact, Entity, Opportunity, Radar, Stage
from .store import Store


def sample_opportunities() -> list[Opportunity]:
    return [
        Opportunity(
            id="demo-stuck-corridor",
            title="Corridor motorway section — contractor unpaid, EOT dispute brewing",
            radar=Radar.STUCK_PROJECT,
            score=92,
            stage=Stage.QUALIFIED,
            why_now=(
                "Contractor has publicly flagged unpaid interim payment certificates and "
                "an unresolved extension-of-time claim. A formal dispute is likely within "
                "weeks — the ideal window to resolve before multi-year arbitration."
            ),
            rationale=(
                "Classic stuck-project pattern (unpaid certificates + refused EOT) on a "
                "high-value public infrastructure contract; fits the firm's "
                "construction/claims and government-relations strength."
            ),
            confidence=0.82,
            target_org="EPC contractor (motorway section)",
            contact=Contact(role="Project Director / Contract Manager", is_decision_maker=True),
            entities=[
                Entity("State employer / roads authority", "employer"),
                Entity("Export credit financier", "financier"),
                Entity("Independent engineer", "contract administrator"),
            ],
            second_order=[
                "Claims quantum consultant referral",
                "Arbitration counsel if it escalates",
                "Advising the employer side instead (conflict-checked)",
            ],
            suggested_actions=[
                "Warm intro via former government contact before cold outreach",
                "Offer value-first 'Preliminary Claims & EOT Assessment'",
                "Draft tailored email referencing the specific section and RTB status",
            ],
            source_url="https://example.com/news/corridor-eot-dispute",
            source_title="Contractor signals payment dispute on motorway section",
        ),
        Opportunity(
            id="demo-find-battery",
            title="€150m EV battery-components plant reaches Ready-To-Build in Vojvodina",
            radar=Radar.FIND,
            score=88,
            stage=Stage.PERSON_FOUND,
            why_now=(
                "Project just moved from planning to RTB and is entering procurement and "
                "construction — the exact phase change that creates immediate legal work."
            ),
            rationale=(
                "Phase change (RTB → procurement/EPC) on a large FDI project; spawns "
                "permitting, environmental, employment/immigration and state-aid workstreams."
            ),
            confidence=0.77,
            target_org="Foreign battery-materials investor",
            contact=Contact(role="Country Manager", name="", is_decision_maker=False),
            entities=[
                Entity("EPC contractor", "construction"),
                Entity("Equipment supplier", "equipment"),
                Entity("Project-finance bank", "financier"),
                Entity("International counsel (Vienna)", "int'l counsel"),
            ],
            second_order=[
                "Construction & EPC negotiation",
                "Environmental permitting roadmap",
                "Employment / work-permit package for expats",
                "State-aid / incentive structuring",
            ],
            suggested_actions=[
                "Give value first: 'Serbian Permitting Roadmap for Project X'",
                "Target the international counsel as a referral channel, not just the investor",
            ],
            source_url="https://example.com/news/battery-plant-rtb",
            source_title="Battery-components plant reaches ready-to-build stage",
        ),
        Opportunity(
            id="demo-reg-vertical",
            title="New vertical-agreements rules — distributors must re-paper contracts",
            radar=Radar.REGULATORY_MONEY,
            score=85,
            stage=Stage.IDENTIFIED,
            why_now=(
                "New rules on vertical/distribution agreements create a hard compliance "
                "deadline; several existing clients almost certainly need contracts reviewed."
            ),
            rationale=(
                "Regulatory change that forces action, with a direct existing-client "
                "reactivation angle — the strongest kind of opener."
            ),
            confidence=0.9,
            target_org="Existing clients: Coca-Cola HBC, Henkel (likely affected)",
            contact=Contact(role="Legal Director / General Counsel", is_decision_maker=True),
            entities=[Entity("Competition authority", "regulator")],
            second_order=[
                "Distribution-network contract audit",
                "Competition compliance training / business breakfast",
            ],
            suggested_actions=[
                "Flag proactively: 'We wanted to flag a recent Serbian regulatory development…'",
                "Prepare 'Three issues relevant to your distribution network' one-pager",
            ],
            source_url="https://example.com/gazette/vertical-agreements-rules",
            source_title="Official Gazette: new rules on vertical agreements",
        ),
        Opportunity(
            id="demo-find-lithium",
            title="Critical-minerals exploration project moves to permitting & financing",
            radar=Radar.FIND,
            score=86,
            stage=Stage.QUALIFIED,
            why_now=(
                "Exploration licence holder is transitioning to permitting and seeking "
                "project finance — the point where sophisticated Serbian counsel is needed."
            ),
            rationale="Mining/critical-minerals is a firm focus; phase change into permitting/financing.",
            confidence=0.7,
            target_org="Mining exploration company",
            contact=Contact(role="Development Director", is_decision_maker=True),
            entities=[
                Entity("International mining major (potential JV)", "investor"),
                Entity("Development bank", "financier"),
            ],
            second_order=[
                "Environmental & social permitting",
                "Community/government relations",
                "JV / farm-in agreement negotiation",
            ],
            suggested_actions=[
                "Position Branković/Parivodic as critical-minerals counsel",
                "Offer 'Serbian Mining Permitting Roadmap'",
            ],
            source_url="https://example.com/news/critical-minerals-permitting",
            source_title="Exploration project advances toward permitting",
        ),
        Opportunity(
            id="demo-stuck-solar",
            title="Solar IPP financing suspended after grid-connection dispute",
            radar=Radar.STUCK_PROJECT,
            score=81,
            stage=Stage.CONTACTED,
            why_now=(
                "Lenders paused disbursement after a grid-connection disagreement with the "
                "system operator; the sponsor needs this unblocked fast to save the schedule."
            ),
            rationale="Financing halted + regulator/operator dispute = urgent, high-value problem.",
            confidence=0.68,
            target_org="Solar IPP sponsor",
            contact=Contact(role="CFO", is_decision_maker=True),
            entities=[
                Entity("Transmission system operator", "counterparty"),
                Entity("Lender syndicate", "financier"),
            ],
            second_order=["Regulatory strategy", "Lender-side advisory", "EPC schedule/claims"],
            suggested_actions=[
                "Warm route via project-finance bank contact",
                "Draft note on connection-dispute resolution options",
            ],
            source_url="https://example.com/news/solar-financing-suspended",
            source_title="Grid-connection dispute stalls solar financing",
        ),
        Opportunity(
            id="demo-reg-incentive",
            title="New investment-incentive decree — ~€2m benefit for €20m investors",
            radar=Radar.REGULATORY_MONEY,
            score=79,
            stage=Stage.IDENTIFIED,
            why_now=(
                "A new incentive/state-aid decree could bring meaningful money to inbound "
                "investors — a chance to open a relationship by delivering value, not selling."
            ),
            rationale="Rule change that can bring a client money — a strong give-value-first opener.",
            confidence=0.72,
            target_org="Inbound manufacturing investors (pipeline)",
            contact=Contact(role="Investment Director / CFO", is_decision_maker=True),
            entities=[Entity("Development agency", "state body")],
            second_order=["Incentive application support", "Ongoing compliance/reporting"],
            suggested_actions=[
                "Prepare 'Preliminary Serbian Investment Incentive Assessment for Company X'",
                "Consider a short thought-leadership article as a sales asset",
            ],
            source_url="https://example.com/gazette/investment-incentive-decree",
            source_title="Government adopts new investment-incentive decree",
        ),
        Opportunity(
            id="demo-find-datacenter",
            title="International EPC wins data-center tender near Belgrade",
            radar=Radar.FIND,
            score=74,
            stage=Stage.WATCH,
            why_now=(
                "A foreign EPC just won a large data-center build; it will need reliable "
                "local counsel for subcontracts, permits and employment as it mobilises."
            ),
            rationale="EPC contractor winning a tender is a reliable trigger for local legal work.",
            confidence=0.64,
            target_org="International EPC contractor",
            contact=Contact(role="Head of Construction", is_decision_maker=False),
            entities=[
                Entity("Data-center operator (client)", "owner"),
                Entity("Local subcontractors", "subcontractors"),
            ],
            second_order=["Subcontract suite", "Permitting", "Employment/immigration"],
            suggested_actions=["Approach the EPC directly as independent Serbian counsel"],
            source_url="https://example.com/news/datacenter-tender-award",
            source_title="EPC contractor wins data-center tender",
        ),
    ]


def seed_demo(store: Store) -> int:
    """Insert sample opportunities (preserving any stage already set). Returns count."""
    count = 0
    for opp in sample_opportunities():
        existing = store.get(opp.id)
        if existing is not None:
            # keep the demo viewer's manual stage changes across reruns
            opp.stage = existing.stage
        store.upsert(opp, preserve_stage=True)
        count += 1
    return count
