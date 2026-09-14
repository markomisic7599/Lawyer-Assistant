"""Render the daily brief as Markdown (the Phase-0 'UI')."""

from __future__ import annotations

from datetime import date

from .models import Opportunity, Radar

_RADAR_LABEL = {
    Radar.FIND: "🟢 FIND — new money / phase change",
    Radar.STUCK_PROJECT: "🔴 STUCK PROJECT — dispute brewing",
    Radar.REGULATORY_MONEY: "🟡 REGULATORY MONEY — rule-driven work",
}


def _opp_block(opp: Opportunity) -> str:
    lines = [f"### [{opp.score}] {opp.title}"]
    who = opp.target_org or "(target TBD)"
    contact = opp.contact.role or ""
    if opp.contact.name:
        contact = f"{opp.contact.name} — {contact}" if contact else opp.contact.name
    lines.append(f"- **WHO:** {who}" + (f" · {contact}" if contact else ""))
    if opp.why_now:
        lines.append(f"- **WHY NOW:** {opp.why_now}")
    if opp.entities:
        actors = ", ".join(f"{e.name} ({e.role})" if e.role else e.name for e in opp.entities)
        lines.append(f"- **Second-order actors:** {actors}")
    if opp.second_order:
        lines.append(f"- **Extra angles:** {'; '.join(opp.second_order)}")
    if opp.suggested_actions:
        lines.append("- **Suggested actions:**")
        lines.extend(f"    - {a}" for a in opp.suggested_actions)
    if opp.rationale:
        lines.append(f"- **Why flagged:** {opp.rationale}")
    if opp.source_url:
        lines.append(f"- **Source:** [{opp.source_title or opp.source_url}]({opp.source_url})")
    lines.append(f"- _confidence {opp.confidence:.0%} · id `{opp.id}`_")
    return "\n".join(lines)


def render_brief(opportunities: list[Opportunity], *, when: date | None = None) -> str:
    when = when or date.today()
    header = [
        f"# Parivodic Daily Intelligence Brief — {when.isoformat()}",
        "",
        "> Rule: not *\"what happened today?\"* but *\"what happened today that gives "
        "someone a reason to pay Parivodic Lawyers?\"*",
        "",
    ]
    if not opportunities:
        header.append("**Danas nema ničega dovoljno dobrog.** No item cleared the bar today.")
        return "\n".join(header)

    header.append(f"**{len(opportunities)} qualified opportunit(y/ies) today.**\n")
    by_radar: dict[Radar, list[Opportunity]] = {}
    for opp in opportunities:
        by_radar.setdefault(opp.radar, []).append(opp)

    sections: list[str] = []
    for radar in (Radar.STUCK_PROJECT, Radar.FIND, Radar.REGULATORY_MONEY):
        opps = by_radar.get(radar)
        if not opps:
            continue
        sections.append(f"\n## {_RADAR_LABEL[radar]}\n")
        sections.extend(_opp_block(o) + "\n" for o in opps)
    return "\n".join(header + sections)
