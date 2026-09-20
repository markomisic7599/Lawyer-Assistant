"""Outreach drafting for the CONVERT phase.

Cold-pitch formula (value first, no meeting ask):
  business signal → relevance for the company → key questions →
  our concrete capability → free micro-delivery

See cold_pitch.py for the full playbook. This module keeps the demo recipient
helper and re-exports the cold-pitch drafter as the default email generator.
"""

from __future__ import annotations

import re
import unicodedata

from .cold_pitch import build_cold_pitch, draft_cold_email  # noqa: F401
from .models import Opportunity

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


def draft_email(opp: Opportunity, lang: str = "sr") -> tuple[str, str]:
    """Return (subject, body) using the cold-pitch playbook."""
    return draft_cold_email(opp, lang=lang)
