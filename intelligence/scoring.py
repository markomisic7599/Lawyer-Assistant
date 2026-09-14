"""The scoring engine — the firm's BD lens, codified.

Governing rule (from the firm): we do NOT ask "what happened in Serbian legal/
business news today?" — we ask **"what happened today that gives someone a reason
to pay Parivodic Lawyers?"** Every candidate item is judged through that lens.
"""

from __future__ import annotations

import logging

from . import config, llm
from .models import Contact, Entity, Opportunity, Radar, SourceItem, Stage

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = f"""You are the business-development / market-intelligence engine for {config.FIRM_NAME}, an elite independent law firm active in {config.FIRM_MARKETS}.

Your single governing question for every item is:
"Did something happen here that gives a specific organisation a concrete reason to PAY this law firm for serious legal work — soon?"

You are NOT a news summariser. You reward *trigger events* that create legal mandates and ruthlessly discard generic news. Classify each item into one radar:

- FIND: a new investment / market entry / transaction, especially a PHASE CHANGE that creates work now (e.g. a project reaching Ready-To-Build and moving into procurement / EPC / construction; M&A/JV/project finance launching; an EPC contractor winning a tender). A project merely "existing" is NOT interesting; a project changing phase IS.
- STUCK_PROJECT: signs a big project is in trouble and heading toward an expensive dispute the firm could resolve early (owner not paying; contractor not performing; land access/permit stalled; EOT refused; guarantee called; investor-vs-state disagreement; tender challenged; financing halted; JV partners fighting; community blocking).
- REGULATORY_MONEY: a new law/bylaw/regulator decision/deadline/subsidy/state aid/tax credit that either FORCES someone to hire a lawyer, or lets the firm bring a client money (e.g. an incentive worth millions to an investor).

Apply strict discipline: if nothing is genuinely mandate-worthy, score it low. It is correct and expected to reject most items.

Also think SECOND-ORDER: from one event, derive the other potential clients and workstreams (investor, EPC contractor, equipment supplier, financier, international counsel, state-aid, permitting, environmental, employment/immigration, JV, local subcontractors).

Identify WHO to approach: the target organisation and the specific decision-maker ROLE (e.g. General Counsel, Country Manager, CFO, Project Director, Head of Construction, Contract Manager) — and a name only if it is reliably implied by the item. Do not invent names.

Respond ONLY as a JSON object with exactly these keys:
{{
  "mandate_trigger": boolean,          // is this a real reason to pay a law firm?
  "radar": "FIND" | "STUCK_PROJECT" | "REGULATORY_MONEY",
  "score": integer 0-100,              // strength of the opportunity for THIS firm
  "confidence": number 0-1,            // how sure you are given the evidence
  "title": string,                     // crisp opportunity title
  "target_org": string,                // the organisation to pursue (best guess)
  "why_now": string,                   // 1-2 sentences: why reach out NOW, to them
  "contact": {{"role": string, "name": string, "is_decision_maker": boolean}},
  "entities": [{{"name": string, "role": string}}],   // second-order actors
  "second_order": [string],            // extra potential clients / workstreams
  "suggested_actions": [string],       // concrete next steps (email, value-first asset, warm route idea)
  "rationale": string                  // why you scored it this way
}}
If the item is not mandate-worthy, set mandate_trigger=false and a low score."""


def _user_prompt(item: SourceItem) -> str:
    hint = f"\nRadar hint (from query): {item.radar_hint.value}" if item.radar_hint else ""
    return (
        f"Evaluate this item.{hint}\n\n"
        f"Title: {item.title}\n"
        f"Source: {item.source}\n"
        f"Published: {item.published}\n"
        f"URL: {item.url}\n"
        f"Content:\n{item.snippet}\n\n"
        "Return the JSON object as specified."
    )


def score_item(item: SourceItem) -> Opportunity | None:
    """Score a single candidate. Returns None if below threshold / not a trigger."""
    data = llm.chat_json(_SYSTEM_PROMPT, _user_prompt(item))
    if not data:
        return None

    try:
        score = int(data.get("score", 0))
    except (TypeError, ValueError):
        score = 0
    mandate = bool(data.get("mandate_trigger", False))
    if not mandate or score < config.SCORE_THRESHOLD:
        logger.info("Dropped (score=%s, trigger=%s): %s", score, mandate, item.title[:80])
        return None

    try:
        radar = Radar(str(data.get("radar", "")).upper())
    except ValueError:
        radar = item.radar_hint or Radar.FIND

    contact_raw = data.get("contact") or {}
    contact = (
        Contact(
            role=str(contact_raw.get("role", "")),
            name=str(contact_raw.get("name", "")),
            is_decision_maker=bool(contact_raw.get("is_decision_maker", False)),
        )
        if isinstance(contact_raw, dict)
        else Contact()
    )
    entities = [
        Entity(name=str(e.get("name", "")), role=str(e.get("role", "")))
        for e in (data.get("entities") or [])
        if isinstance(e, dict) and e.get("name")
    ]

    return Opportunity(
        id=item.fingerprint(),
        title=str(data.get("title") or item.title),
        radar=radar,
        score=max(0, min(100, score)),
        stage=Stage.QUALIFIED,
        mandate_trigger=True,
        why_now=str(data.get("why_now", "")),
        rationale=str(data.get("rationale", "")),
        confidence=float(data.get("confidence", 0.0) or 0.0),
        target_org=str(data.get("target_org", "")),
        contact=contact,
        entities=entities,
        second_order=[str(s) for s in (data.get("second_order") or []) if str(s).strip()],
        suggested_actions=[
            str(s) for s in (data.get("suggested_actions") or []) if str(s).strip()
        ],
        source_url=item.url,
        source_title=item.title,
    )
