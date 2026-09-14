"""Notification rendering for the demo.

Turns the top opportunities into the kind of alerts the firm would actually
receive — mobile push, Slack/Teams, and email — so a colleague can see how the
system would reach them the moment something worth money happens.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import config
from .models import Opportunity, Radar

_RADAR_ICON = {
    Radar.FIND: "🟢",
    Radar.STUCK_PROJECT: "🔴",
    Radar.REGULATORY_MONEY: "🟡",
}
_RADAR_WORD = {
    Radar.FIND: "New money",
    Radar.STUCK_PROJECT: "Stuck project",
    Radar.REGULATORY_MONEY: "Regulatory",
}
_RADAR_ACCENT = {
    Radar.FIND: "#2e7d54",
    Radar.STUCK_PROJECT: "#b3261e",
    Radar.REGULATORY_MONEY: "#a1770a",
}

# Staggered relative timestamps for a realistic feed.
_WHENS = ["just now", "8m ago", "35m ago", "1h ago", "2h ago", "today, 08:12"]


@dataclass
class Notification:
    opp_id: str
    icon: str
    accent: str
    title: str
    body: str
    when: str
    score: int


def _short(text: str, limit: int = 120) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def build_notifications(opps: list[Opportunity], *, limit: int = 6) -> list[Notification]:
    """Pick the alert-worthy opportunities (highest score / most urgent first)."""
    ranked = sorted(opps, key=lambda o: o.score, reverse=True)[:limit]
    notes: list[Notification] = []
    for i, o in enumerate(ranked):
        who = o.target_org or "New target"
        title = f"{_RADAR_ICON[o.radar]} {_RADAR_WORD[o.radar]} · score {o.score}"
        notes.append(
            Notification(
                opp_id=o.id,
                icon=_RADAR_ICON[o.radar],
                accent=_RADAR_ACCENT[o.radar],
                title=title,
                body=f"{who} — {_short(o.why_now)}",
                when=_WHENS[i % len(_WHENS)],
                score=o.score,
            )
        )
    return notes


def push_card_html(n: Notification) -> str:
    """A mobile / desktop push-notification card."""
    firm = config.FIRM_NAME
    return f"""
<div style="max-width:420px;background:#f4f4f6;border-radius:18px;padding:12px 14px;
            box-shadow:0 6px 20px rgba(0,0,0,0.12);border-left:5px solid {n.accent};
            font-family:-apple-system,Segoe UI,Roboto,sans-serif;margin-bottom:12px;">
  <div style="display:flex;align-items:center;gap:8px;font-size:12px;color:#555;">
    <span style="font-size:16px;">⚖️</span>
    <span style="font-weight:700;color:#222;">{firm}</span>
    <span style="margin-left:auto;">{n.when}</span>
  </div>
  <div style="font-weight:700;font-size:14px;margin-top:6px;color:#111;">{n.title}</div>
  <div style="font-size:13px;color:#333;margin-top:2px;">{n.body}</div>
</div>
"""


def slack_message_html(n: Notification) -> str:
    """A Slack/Teams-style bot message."""
    firm = config.FIRM_NAME
    return f"""
<div style="max-width:520px;background:#fff;border:1px solid #e6e6e6;border-radius:10px;
            padding:12px 14px;margin-bottom:12px;font-family:Lato,Segoe UI,sans-serif;">
  <div style="display:flex;align-items:center;gap:8px;">
    <div style="width:28px;height:28px;border-radius:6px;background:{n.accent};color:#fff;
                display:flex;align-items:center;justify-content:center;font-size:15px;">⚖️</div>
    <span style="font-weight:700;color:#1d1c1d;">{firm}</span>
    <span style="background:#e8e8e8;color:#555;font-size:10px;font-weight:700;
                 border-radius:3px;padding:1px 4px;">APP</span>
    <span style="color:#888;font-size:12px;">{n.when}</span>
  </div>
  <div style="margin-top:6px;font-weight:700;color:#111;">{n.title}</div>
  <div style="color:#333;font-size:14px;margin-top:2px;">{n.body}</div>
  <div style="margin-top:8px;">
    <span style="border:1px solid #d0d0d0;border-radius:6px;padding:4px 10px;font-size:12px;
                 color:#1264a3;font-weight:600;">Open in pipeline →</span>
  </div>
</div>
"""


def email_row_html(n: Notification) -> str:
    """An inbox-style email preview row."""
    firm = config.FIRM_NAME
    return f"""
<div style="max-width:640px;background:#fff;border:1px solid #eee;border-left:4px solid {n.accent};
            border-radius:8px;padding:10px 14px;margin-bottom:8px;
            font-family:Segoe UI,Roboto,sans-serif;">
  <div style="display:flex;align-items:center;font-size:13px;">
    <span style="font-weight:700;color:#111;">{firm} · Daily Intelligence</span>
    <span style="margin-left:auto;color:#888;">{n.when}</span>
  </div>
  <div style="font-weight:600;color:#111;margin-top:3px;">{n.title}</div>
  <div style="color:#666;font-size:13px;margin-top:1px;">{n.body}</div>
</div>
"""
