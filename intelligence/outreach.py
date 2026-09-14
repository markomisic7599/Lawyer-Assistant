"""Outreach drafting for the CONVERT phase.

Turns a scored Opportunity into a ready-to-send, value-first email tailored to
its radar (FIND / STUCK PROJECT / REGULATORY MONEY), in English or Serbian.

For the demo this is template-based so it works offline with no API key. The
same interface can later be backed by the LLM for fully bespoke drafts.
"""

from __future__ import annotations

import re
import unicodedata

from . import config
from .models import Opportunity, Radar

# Demo sender identity (purely illustrative).
SENDER_NAME = "Marko Parivodić"
SENDER_TITLE = "Partner"
SENDER_EMAIL = "marko.parivodic@parivodic.rs"


def _slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "", text).lower()
    return text or "office"


def demo_recipient(opp: Opportunity) -> str:
    """A plausible, clearly-fake recipient address for the demo."""
    name = (opp.contact.name or "").strip()
    org_slug = _slug(opp.target_org.split(",")[0]) if opp.target_org else "office"
    if name:
        parts = [p for p in re.split(r"\s+", name) if p]
        local = ".".join(_slug(p) for p in parts[:2]) or "contact"
        return f"{local}@{org_slug}.example.com"
    return f"office@{org_slug}.example.com"


def _greeting(opp: Opportunity, lang: str) -> str:
    who = opp.contact.name.strip() if opp.contact.name.strip() else ""
    if lang == "sr":
        return f"Poštovani {who}," if who else "Poštovani,"
    return f"Dear {who}," if who else "Dear Sir or Madam,"


def _first_action(opp: Opportunity) -> str:
    return opp.suggested_actions[0] if opp.suggested_actions else ""


def draft_email(opp: Opportunity, lang: str = "en") -> tuple[str, str]:
    """Return (subject, body) tailored to the opportunity's radar and language."""
    firm = config.FIRM_NAME
    greeting = _greeting(opp, lang)
    org = opp.target_org or ("the project" if lang == "en" else "projekat")

    if lang == "sr":
        sign = f"\n\nS poštovanjem,\n{SENDER_NAME}\n{SENDER_TITLE}, {firm}\n{SENDER_EMAIL}"
        if opp.radar == Radar.STUCK_PROJECT:
            subject = f"{org}: rešavanje spora pre eskalacije"
            body = (
                f"{greeting}\n\n"
                f"Pratimo razvoj situacije oko projekta i primetili smo sledeće: {opp.why_now}\n\n"
                f"{firm} redovno pomaže stranama u ovakvim situacijama da spor reše rano, "
                f"pre nego što pređe u dugotrajnu i skupu arbitražu.\n\n"
                f"Kao prvi korak, rado bismo Vam bez obaveze pripremili kratku preliminarnu "
                f"procenu pozicije i mogućih opcija. Da li biste bili otvoreni za kratak "
                f"poziv ove nedelje?"
            )
        elif opp.radar == Radar.REGULATORY_MONEY:
            subject = "Nedavna regulatorna promena u Srbiji koja se tiče Vašeg poslovanja"
            body = (
                f"{greeting}\n\n"
                f"Želeli smo da Vam proaktivno skrenemo pažnju na nedavni razvoj: {opp.why_now}\n\n"
                f"S obzirom na Vaše poslovanje u Srbiji, ovo verovatno zahteva određene "
                f"prilagodbe. Pripremili smo kratak pregled ključnih tačaka koje su "
                f"relevantne baš za Vas.\n\n"
                f"Ako želite, možemo Vam ga poslati ili to ukratko prođemo na pozivu."
            )
        else:  # FIND
            subject = f"Pravna podrška u Srbiji za {org}"
            body = (
                f"{greeting}\n\n"
                f"Pratimo tržište i primetili smo da {org} ulazi u novu fazu: {opp.why_now}\n\n"
                f"{firm} je nezavisna kancelarija koja u ovakvim projektima pomaže investitorima "
                f"kroz izdavanje dozvola, ugovaranje i regulatorna pitanja u Srbiji.\n\n"
                f"Kao prvi korak, rado bismo Vam bez obaveze pripremili kratak vodič kroz "
                f"relevantne korake. Da li biste bili otvoreni za kratak poziv?"
            )
        return subject, body + sign

    # English
    sign = f"\n\nKind regards,\n{SENDER_NAME}\n{SENDER_TITLE}, {firm}\n{SENDER_EMAIL}"
    if opp.radar == Radar.STUCK_PROJECT:
        subject = f"{org}: resolving this before it escalates"
        body = (
            f"{greeting}\n\n"
            f"We follow this project closely and noted the following: {opp.why_now}\n\n"
            f"{firm} regularly helps parties in situations like this reach an early "
            f"resolution, before matters turn into lengthy and costly arbitration.\n\n"
            f"As a first step, we would be glad to prepare a short, no-obligation "
            f"preliminary assessment of the position and available options. Would you "
            f"be open to a brief call this week?"
        )
    elif opp.radar == Radar.REGULATORY_MONEY:
        subject = "A recent Serbian regulatory change relevant to your business"
        body = (
            f"{greeting}\n\n"
            f"We wanted to proactively flag a recent development: {opp.why_now}\n\n"
            f"Given your operations in Serbia, this likely calls for some adjustments. "
            f"We have put together a short summary of the key points that are relevant "
            f"specifically to you.\n\n"
            f"If helpful, we can send it over or walk through it on a quick call."
        )
    else:  # FIND
        subject = f"Serbian legal support as {org} moves ahead"
        body = (
            f"{greeting}\n\n"
            f"We track the market closely and saw that {org} is entering a new phase: "
            f"{opp.why_now}\n\n"
            f"{firm} is an independent firm that supports investors on projects like this "
            f"across permitting, contracting and regulatory matters in Serbia.\n\n"
            f"As a first step, we would be happy to prepare a short, no-obligation roadmap "
            f"of the relevant steps. Would you be open to a brief call?"
        )
    if opp.radar == Radar.FIND and _first_action(opp):
        pass  # keep the body focused; suggested actions are shown in the UI
    return subject, body + sign
