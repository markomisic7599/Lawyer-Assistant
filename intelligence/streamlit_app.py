"""Parivodic Intelligence System — Streamlit demo dashboard.

A visual walkthrough of the product for showing colleagues/clients. Works with
zero API keys via built-in sample data; a live sweep is available if a Tavily
key is configured.

Run from the repo root:
    streamlit run intelligence/streamlit_app.py
"""

from __future__ import annotations

import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Allow `import intelligence...` when launched via `streamlit run <path>`.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

from intelligence import cold_pitch, config, fund_radar, notifications, outreach, relationships, solution
from intelligence.clients_data import Client, match_opportunities, sample_clients
from intelligence.demo_data import seed_demo
from intelligence.models import ACTIVE_STAGES, Opportunity, Radar, Stage
from intelligence.relationships import PathType
from intelligence.store import Store

DEMO_DB = config.DATA_DIR / "demo.db"

_RADAR_STYLE = {
    Radar.FIND: ("FIND · new money", "#2e7d54", "#e7f5ee"),
    Radar.STUCK_PROJECT: ("STUCK PROJECT · dispute", "#b3261e", "#fbe9e7"),
    Radar.REGULATORY_MONEY: ("REGULATORY MONEY", "#a1770a", "#fdf5e0"),
}


@st.cache_resource
def get_store() -> Store:
    return Store(db_path=DEMO_DB)


def _score_color(score: int) -> str:
    if score >= 85:
        return "#2e7d54"
    if score >= 70:
        return "#a1770a"
    return "#8a8a8a"


def _chip(text: str, fg: str, bg: str) -> str:
    return (
        f"<span style='background:{bg};color:{fg};padding:2px 10px;border-radius:12px;"
        f"font-size:12px;font-weight:600;white-space:nowrap;'>{text}</span>"
    )


def _move_stage_cb(opp_id: str, key: str) -> None:
    get_store().set_stage(opp_id, Stage(st.session_state[key]))


def _stage_selector(opp: Opportunity, key_prefix: str) -> None:
    options = [s.value for s in Stage]
    key = f"{key_prefix}_stage_{opp.id}"
    st.selectbox(
        "Stage",
        options=options,
        index=options.index(opp.stage.value),
        key=key,
        on_change=_move_stage_cb,
        args=(opp.id, key),
        label_visibility="collapsed",
    )


@st.dialog("✉️ Cold pitch", width="large")
def _outreach_dialog(opp_id: str) -> None:
    store = get_store()
    opp = store.get(opp_id)
    if opp is None:
        st.error("Opportunity not found.")
        return

    label, fg, bg = _RADAR_STYLE[opp.radar]
    st.markdown(f"##### {opp.title}")

    star = " ⭐ decision-maker" if opp.contact.is_decision_maker else ""
    who = opp.contact.name or opp.contact.role or "—"
    left, right = st.columns(2)
    with left:
        st.markdown(f"**Organisation:** {opp.target_org or '—'}")
        st.markdown(f"**Contact:** {who}{star}")
        if opp.contact.name and opp.contact.role:
            st.caption(opp.contact.role)
    with right:
        st.markdown(f"{_chip(label, fg, bg)}", unsafe_allow_html=True)
        st.markdown(f"**Score:** {opp.score} · **Confidence:** {opp.confidence:.0%}")

    st.caption(
        "Cold pitch: signal → relevance → key questions → expertise → free micro-delivery. "
        "No meeting ask in the first message."
    )
    st.divider()

    lang = st.radio(
        "Language",
        options=["sr", "en"],
        format_func=lambda x: "Srpski" if x == "sr" else "English",
        horizontal=True,
        key=f"lang_{opp.id}",
    )
    pitch = cold_pitch.build_cold_pitch(opp, lang=lang)
    to_default = outreach.demo_recipient(opp)

    with st.expander("Formula breakdown", expanded=True):
        st.markdown(f"**A. Poslovni signal:** {pitch.signal}")
        st.markdown(f"**B. Značaj za kompaniju:** {pitch.relevance}")
        st.markdown("**Ključna pitanja:**")
        for q in pitch.key_questions:
            st.markdown(f"- {q}")
        st.markdown(f"**C. Ekspertiza:** {pitch.expertise}")
        st.markdown(f"**D. Mikro-isporuka:** {pitch.micro_delivery}")
        st.caption(f"{pitch.word_count} words · target ~100–150")
        if pitch.passes_rules:
            st.success(pitch.rule_notes[0])
        else:
            for n in pitch.rule_notes:
                st.warning(n)

    to_addr = st.text_input("To", value=to_default, key=f"to_{opp.id}_{lang}")
    subject = st.text_input("Subject", value=pitch.subject, key=f"subj_{opp.id}_{lang}")
    body = st.text_area("Message", value=pitch.body, height=280, key=f"body_{opp.id}_{lang}")

    st.caption("Demo only — no email is actually sent.")

    c1, c2 = st.columns([1, 3])
    if c1.button("📨 Send", type="primary", key=f"send_{opp.id}"):
        with st.spinner("Sending…"):
            time.sleep(0.8)
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
        note = f"[{stamp}] Cold pitch sent to {to_addr} — “{subject}” · offer: {pitch.micro_delivery}"
        opp = store.get(opp_id) or opp
        opp.stage = Stage.CONTACTED
        opp.notes = (opp.notes + "\n" + note).strip()
        opp.next_action_at = "If they accept the material: send it, then one concrete question — no meeting yet"
        store.upsert(opp, preserve_stage=False)
        for pref in ("brief", "pipe"):
            st.session_state[f"{pref}_stage_{opp_id}"] = Stage.CONTACTED.value
        st.session_state["_sent_flash"] = f"Cold pitch sent to {to_addr} · moved to CONTACTED"
        st.rerun()
    c2.button("Cancel", key=f"cancel_{opp.id}")


def _render_card(opp: Opportunity, key_prefix: str) -> None:
    label, fg, bg = _RADAR_STYLE[opp.radar]
    with st.container(border=True):
        top, side = st.columns([5, 1])
        with top:
            st.markdown(
                f"{_chip(label, fg, bg)} &nbsp; "
                f"{_chip(f'score {opp.score}', '#fff', _score_color(opp.score))}",
                unsafe_allow_html=True,
            )
            st.markdown(f"#### {opp.title}")
            who = opp.target_org or "_(target TBD)_"
            contact = opp.contact.name or opp.contact.role
            star = " ⭐" if opp.contact.is_decision_maker else ""
            st.markdown(f"**WHO:** {who}" + (f" · _{contact}{star}_" if contact else ""))
            if opp.why_now:
                st.markdown(f"**WHY NOW:** {opp.why_now}")
        with side:
            st.caption("Pipeline stage")
            _stage_selector(opp, key_prefix)
            st.caption(f"conf {opp.confidence:.0%}")
            if st.button("✉️ Cold pitch", key=f"{key_prefix}_draft_{opp.id}",
                         use_container_width=True):
                _outreach_dialog(opp.id)
            if opp.stage == Stage.CONTACTED and "sent" in opp.notes.lower():
                st.caption("✅ contacted")

        with st.expander("Details · second-order · outreach"):
            if opp.entities:
                st.markdown("**Second-order actors** (each a potential client):")
                for e in opp.entities:
                    st.markdown(f"- {e.name}" + (f" — _{e.role}_" if e.role else ""))
            if opp.second_order:
                st.markdown("**Extra angles / workstreams:**")
                for s in opp.second_order:
                    st.markdown(f"- {s}")
            if opp.suggested_actions:
                st.markdown("**Suggested actions:**")
                for a in opp.suggested_actions:
                    st.markdown(f"- {a}")
            if opp.rationale:
                st.markdown(f"**Why flagged:** {opp.rationale}")
            if opp.source_url:
                st.markdown(f"**Source:** [{opp.source_title or opp.source_url}]({opp.source_url})")


_STATUS_STYLE = {
    "Active": ("#2e7d54", "#e7f5ee"),
    "Dormant": ("#a1770a", "#fdf5e0"),
    "Prospect": ("#1264a3", "#e8f1fb"),
}


def _render_client_card(client: Client, opps: list[Opportunity]) -> None:
    fg, bg = _STATUS_STYLE.get(client.status, ("#555", "#eee"))
    matched = match_opportunities(client, opps)
    reactivation = client.status == "Dormant" and bool(matched)
    with st.container(border=True):
        top, side = st.columns([5, 2])
        with top:
            chips = _chip(client.status, fg, bg)
            if reactivation:
                chips += " &nbsp; " + _chip("♻ reactivation", "#fff", "#b3261e")
            if matched:
                chips += " &nbsp; " + _chip(f"🔗 {len(matched)} live", "#fff", "#1264a3")
            st.markdown(chips, unsafe_allow_html=True)
            st.markdown(f"#### {client.name}")
            st.markdown(f"**{client.sector}** · {client.markets} · client since {client.since}")
            if client.tags:
                st.caption(" · ".join(f"#{t}" for t in client.tags))
        with side:
            st.markdown(f"**Owner:** {client.owner}")
            st.caption(f"Last matter: {client.last_matter}")
            st.caption(f"Last contact: {client.last_contact}")

        if matched:
            st.markdown("**🔗 Live opportunities linked to this client:**")
            for o in matched:
                label, ofg, obg = _RADAR_STYLE[o.radar]
                st.markdown(
                    f"- {_chip(label, ofg, obg)} &nbsp; **{o.title}** "
                    f"({_chip(f'score {o.score}', '#fff', _score_color(o.score))})",
                    unsafe_allow_html=True,
                )
                if st.button("✉️ Cold pitch", key=f"client_draft_{client.id}_{o.id}"):
                    _outreach_dialog(o.id)

        with st.expander("Contacts · notes"):
            if client.contacts:
                st.markdown("**Key contacts:**")
                for c in client.contacts:
                    who = c.name or c.role
                    detail = f" — _{c.role}_" if c.name and c.role else ""
                    st.markdown(f"- {who}{detail}")
            if client.notes:
                st.markdown(f"**Notes:** {client.notes}")


def _sidebar(store: Store) -> tuple[list[Radar], int]:
    with st.sidebar:
        st.markdown("## ⚖️ Parivodic")
        st.caption("Market Intelligence & BD Engine")
        st.divider()

        if st.button("↻ Load sample data", use_container_width=True):
            n = seed_demo(store)
            st.success(f"Loaded {n} sample opportunities.")

        has_key = bool(config.TAVILY_API_KEY)
        if st.button(
            "🔎 Run live sweep",
            use_container_width=True,
            disabled=not has_key,
            help=None if has_key else "Set TAVILY_API_KEY to enable live search.",
        ):
            from intelligence.pipeline import run_daily

            with st.spinner("Scanning the market for mandate triggers…"):
                res = run_daily(store=store)
            st.success(f"{len(res.qualified)} qualified ({res.new_count} new).")
        if not has_key:
            st.caption("Live sweep disabled — no Tavily key. Using sample data.")

        if st.button("🔔 Send test alert", use_container_width=True):
            top = sorted(store.list(), key=lambda o: o.score, reverse=True)
            if top:
                n = notifications.build_notifications(top, limit=1)[0]
                st.toast(f"**{n.title}**\n\n{n.body}", icon="🔔")

        if st.button("🗑 Clear all", use_container_width=True):
            DEMO_DB.unlink(missing_ok=True)
            get_store.clear()
            st.rerun()

        st.divider()
        st.markdown("### Filters")
        radar_labels = {r: _RADAR_STYLE[r][0].split(" · ")[0] for r in Radar}
        selected = st.multiselect(
            "Radars",
            options=list(Radar),
            default=list(Radar),
            format_func=lambda r: radar_labels[r],
        )
        min_score = st.slider("Min score", 0, 100, config.SCORE_THRESHOLD, step=5)
        st.divider()
        st.caption("Demo data is illustrative and fictional.")
    return selected, min_score


def main() -> None:
    st.set_page_config(page_title="Parivodic Intelligence", page_icon="⚖️", layout="wide")
    store = get_store()

    flash = st.session_state.pop("_sent_flash", None)
    if flash:
        st.toast(f"📨 {flash}", icon="✅")

    # First-run convenience: seed sample data so the demo is never empty.
    if not store.list():
        seed_demo(store)

    selected_radars, min_score = _sidebar(store)

    opps = [
        o
        for o in store.list(min_score=min_score)
        if o.radar in selected_radars
    ]

    notes = notifications.build_notifications(opps)
    title_col, bell_col = st.columns([5, 1])
    with title_col:
        st.title("Daily Intelligence")
    with bell_col:
        st.write("")
        with st.popover(f"🔔 {len(notes)}", use_container_width=True):
            st.markdown("##### Alerts")
            if not notes:
                st.caption("No alerts right now.")
            for n in notes:
                st.markdown(
                    f"<div style='border-left:3px solid {n.accent};padding:2px 8px;"
                    f"margin-bottom:8px;'><b>{n.title}</b><br>"
                    f"<span style='font-size:13px;color:#444;'>{n.body}</span><br>"
                    f"<span style='font-size:11px;color:#999;'>{n.when}</span></div>",
                    unsafe_allow_html=True,
                )
    st.markdown(
        "> Not *“what happened today?”* — but *“what happened today that gives someone "
        "a reason to pay Parivodic Lawyers?”*"
    )

    # Metrics row
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Qualified", len(opps))
    c2.metric("🔴 Stuck projects", sum(o.radar == Radar.STUCK_PROJECT for o in opps))
    c3.metric("🟢 New money", sum(o.radar == Radar.FIND for o in opps))
    c4.metric("🟡 Regulatory", sum(o.radar == Radar.REGULATORY_MONEY for o in opps))

    tab_actions, tab_brief, tab_pipeline, tab_funds, tab_warm, tab_contacts, tab_pitch, tab_position, tab_clients, tab_notify = st.tabs(
        [
            "🎯 Today's Actions",
            "📋 Daily Brief",
            "🗂 Pipeline",
            "💰 Fund Radar",
            "🕸 Warm Path",
            "📇 Contacts",
            "✉️ Cold Pitch",
            "🧩 Position Builder",
            "👥 Clients",
            "🔔 Notifications",
        ]
    )

    with tab_actions:
        st.markdown(
            "**Relationship Intelligence × Opportunity Radar.** "
            "Ne 40 vijesti — samo **3–5 najboljih BD akcija** za danas, rangiranih: "
            "`opportunity × mandate value × fit × urgency × relationship strength × access`."
        )
        actions = relationships.daily_bd_actions(opps)
        if not actions:
            st.info("Nema prioritetnih akcija za trenutne filtere.")
        for a in actions:
            with st.container(border=True):
                st.markdown(
                    f"### PRIORITY {a.priority} · score {a.score}"
                )
                st.markdown(f"**{a.title}**")
                st.markdown(f"**Opportunity:** {a.opportunity}")
                st.markdown(f"**Decision maker:** {a.decision_maker}")
                st.markdown(f"**Warm path:** {a.warm_path_summary}")
                st.caption(a.relationship_note)
                st.success(f"**Suggested action:** {a.suggested_action}")
                st.markdown(f"**Why Parivodic:** {a.why_parivodic}")
                st.markdown(f"**Owner:** {a.owner}")
                if a.draft:
                    with st.expander("Suggested message"):
                        st.text_area(
                            "Draft",
                            value=a.draft,
                            height=180,
                            key=f"daily_draft_{a.priority}",
                            label_visibility="collapsed",
                        )

    with tab_brief:
        if not opps:
            st.info("**Danas nema ničega dovoljno dobrog.** No item cleared the bar.")
        for opp in opps:
            _render_card(opp, key_prefix="brief")

    with tab_pipeline:
        active = [s for s in Stage if s in ACTIVE_STAGES]
        cols = st.columns(len(active))
        by_stage: dict[Stage, list[Opportunity]] = {s: [] for s in active}
        for o in opps:
            if o.stage in by_stage:
                by_stage[o.stage].append(o)
        for col, stage in zip(cols, active):
            with col:
                st.markdown(f"**{stage.value.replace('_', ' ').title()}**")
                st.caption(f"{len(by_stage[stage])} item(s)")
                for o in by_stage[stage]:
                    with st.container(border=True):
                        st.markdown(f"**[{o.score}]** {o.title}")
                        st.caption(o.target_org or "target TBD")
                        _stage_selector(o, key_prefix="pipe")
                        if st.button("✉️", key=f"pipe_draft_{o.id}",
                                     help="Cold pitch"):
                            _outreach_dialog(o.id)

    with tab_funds:
        st.markdown(
            "**Investment / Fund Radar.** Fond nije samo potencijalni klijent — "
            "preko njegovog thesis-a nalazimo **kompanije koje raise-uju** i kojima "
            "možemo ponuditi *Investment Readiness* **prije** runde. "
            "Važi za VC, PE, strategic i DFI — ne samo startape."
        )
        funds = fund_radar.sample_funds()
        fund_labels = {f"{f.name} ({f.investor_type.value})": f for f in funds}
        chosen_f = st.selectbox("Investitor / fond", list(fund_labels.keys()), key="fund_sel")
        fund = fund_labels[chosen_f]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Fund size", fund.fund_size)
        c2.metric("Ticket", fund.ticket)
        c3.metric("Type", fund.investor_type.value)
        c4.metric("Geo", fund.geography.split("/")[0].strip())
        st.write(fund.thesis)
        st.caption(
            "Sectors: " + ", ".join(fund.sectors)
            + " · Stages: " + ", ".join(s.value for s in fund.stages)
        )

        st.markdown("##### Matching companies (Investment Fit Score)")
        fits = fund_radar.fits_for_fund(fund.id, min_score=60)
        if not fits:
            st.info("Nema dovoljno jakog fita za ovaj fond u demo setu.")
        for fit in fits:
            with st.container(border=True):
                co = fit.company
                st.markdown(
                    f"**{co.name}** → {fund.name} fit: "
                    f"<span style='background:#2e7d54;color:#fff;padding:2px 8px;"
                    f"border-radius:10px;font-weight:700;'>{fit.score}/100</span>",
                    unsafe_allow_html=True,
                )
                st.caption(
                    f"Stage: {co.stage.value} · Sector: {co.sector} · "
                    f"Estimated raise: {co.estimated_raise}"
                )
                st.markdown("**Fundraising signals:**")
                for s in co.fundraising_signals:
                    st.markdown(f"- {s}")
                st.caption(
                    "Potential investors: "
                    + ", ".join([fund.name] + fit.other_potential_investors)
                )
                st.caption(fit.rationale)

        st.divider()
        st.markdown("##### CONTACT NOW — Investment leads")
        leads = [L for L in fund_radar.rank_leads(min_score=80) if L.fit.fund.id == fund.id]
        if not leads:
            leads = [L for L in fund_radar.rank_leads(min_score=75) if L.fit.fund.id == fund.id]
        if not leads:
            st.caption("Nema CONTACT NOW leada iznad praga za ovaj fond — vidi all-funds ispod.")
        for L in leads[:5]:
            fit = L.fit
            with st.container(border=True):
                st.markdown(f"### CONTACT NOW — {fit.company.name}")
                st.markdown(
                    f"**Razlog:** odgovara **{fit.fund.name}** thesisu i postoje signali "
                    f"da trenutno raise-uje ({fit.company.stage.value})."
                )
                m1, m2, m3 = st.columns(3)
                m1.metric(f"{fit.fund.name} fit", f"{fit.score}/100")
                m2.metric("Opportunity", L.legal.label.split("+")[0].strip()[:22])
                m3.metric("Priority", L.priority_score)
                st.markdown(
                    f"**Decision maker:** {fit.company.decision_maker} "
                    f"({fit.company.decision_role})"
                )
                st.markdown(f"**Warm path:** {L.warm_path.path_type.value}")
                if L.warm_path.chain:
                    st.caption(" → ".join(L.warm_path.chain))
                st.caption(L.warm_path.why)
                st.success(f"**Suggested offer:** {L.legal.micro_offer}")
                with st.expander("Legal workstreams (paid mandate)"):
                    for w in L.legal.workstreams:
                        st.markdown(f"- {w}")
                with st.expander("Pitch"):
                    st.text_input("Subject", value=L.pitch_subject, key=f"inv_subj_{fit.company.id}_{fit.fund.id}")
                    st.text_area("Message", value=L.pitch_body, height=220, key=f"inv_body_{fit.company.id}_{fit.fund.id}")

        with st.expander("Svi fondovi — top matches (demo)"):
            for L in fund_radar.rank_leads(min_score=80)[:8]:
                st.markdown(
                    f"- **{L.fit.company.name}** × {L.fit.fund.name}: "
                    f"fit {L.fit.score}/100 · {L.warm_path.path_type.value}"
                )

    with tab_warm:
        st.markdown(
            "**Obavezna faza prije cold outreach-a:** *Do we have a warm path?* "
            "DIRECT · 1st-degree · intermediary · ili NO WARM PATH."
        )
        if not opps:
            st.info("Nema leadova za filter.")
        else:
            labels = {f"[{o.score}] {o.title}": o for o in sorted(opps, key=lambda x: -x.score)}
            chosen = st.selectbox("Lead", list(labels.keys()), key="warm_lead")
            opp = labels[chosen]
            path = relationships.find_warm_path(opp)

            color = {
                PathType.DIRECT: "#2e7d54",
                PathType.FIRST_DEGREE: "#1264a3",
                PathType.INTERMEDIARY: "#a1770a",
                PathType.NONE: "#b3261e",
            }[path.path_type]
            st.markdown(
                f"<div style='padding:12px 16px;border-left:5px solid {color};"
                f"background:#f7f7f8;border-radius:8px;margin-bottom:12px;'>"
                f"<b>{path.path_type.value}</b><br>{path.why}</div>",
                unsafe_allow_html=True,
            )
            if path.chain:
                st.markdown("**Chain:** " + " → ".join(f"`{x}`" for x in path.chain))
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Ask:** {path.ask}")
                st.markdown(f"**Owner:** {path.suggested_owner}")
                if path.intermediary:
                    st.markdown(
                        f"**Intermediary:** {path.intermediary.name} "
                        f"({path.intermediary.company}) · strength "
                        f"**{path.intermediary.strength}/100**"
                    )
                if path.decision_maker:
                    st.markdown(
                        f"**Decision maker:** {path.decision_maker.name} · "
                        f"{path.decision_maker.role}"
                    )
            with c2:
                if path.path_type == PathType.NONE:
                    st.warning("Nema warm path → koristi Cold Pitch (mikro-isporuka).")
                    if st.button("Otvori Cold Pitch", key="warm_to_cold"):
                        _outreach_dialog(opp.id)
                elif path.draft_message:
                    st.text_area("Suggested message", value=path.draft_message, height=220)

            st.divider()
            st.markdown("##### Why-now triggers (existing contacts)")
            for t in relationships.contact_triggers():
                with st.container(border=True):
                    st.markdown(f"**{t.score}/100** · {t.headline}")
                    st.write(t.why_now)
                    st.caption("Likely needs: " + ", ".join(t.likely_needs))
                    st.markdown(f"→ **{t.suggested_owner}** today")

    with tab_contacts:
        st.markdown(
            "**Master Contact Database** — jedan profil po osobi (dedupe: vizit karta + "
            "mailbox + CRM). Relationship strength 0–100: recency, učestalost, da li je "
            "postojao mandate. Samo zakonito dostupni podaci."
        )
        contacts = relationships.sample_contacts()
        q = st.text_input("Search", placeholder="ime, kompanija, industrija…", key="contact_q")
        for c in contacts:
            blob = f"{c.name} {c.company} {c.role} {c.industry} {c.known_by}".lower()
            if q and q.lower() not in blob:
                continue
            with st.container(border=True):
                top, side = st.columns([4, 1])
                with top:
                    st.markdown(f"#### {c.name}")
                    st.markdown(f"**{c.role}** · {c.company}")
                    st.caption(
                        f"{c.country} · {c.industry} · origin: {c.origin}"
                        + (f" · known by **{c.known_by}**" if c.known_by else "")
                    )
                    if c.notes:
                        st.caption(c.notes)
                with side:
                    st.metric("Strength", f"{c.strength}")
                    st.caption(f"{c.email_exchanges} emails")
                    st.caption(f"Last: {c.last_contact}")
                    if c.was_client:
                        st.caption("✅ former client")
                with st.expander("Details"):
                    st.write(f"Email: `{c.email or '—'}`")
                    st.write(f"Phone: `{c.phone or '—'}`")
                    if c.linkedin:
                        st.markdown(f"[Public LinkedIn]({c.linkedin})")

        st.divider()
        st.markdown("##### Relationship graph (demo edges)")
        edges = relationships.sample_edges()
        idx = {c.id: c for c in contacts}

        def _node(cid: str) -> str:
            if cid == "parivodic":
                return "Parivodic Lawyers"
            return idx[cid].name if cid in idx else cid

        for e in edges:
            st.markdown(f"- **{_node(e.source_id)}** → **{_node(e.target_id)}** _{e.relation}_")

    with tab_pitch:
        st.markdown(
            "**Cold pitch playbook.** Prvo vrijednost, zatim razgovor, tek onda saradnja. "
            "Formula: *poslovni signal → značaj za kompaniju → ključna pitanja → "
            "konkretna ekspertiza → besplatna mikro-isporuka.* "
            "Prva poruka **ne** traži sastanak."
        )
        contact_now = sorted(opps, key=lambda o: o.score, reverse=True)
        if not contact_now:
            st.info("No leads for the current filters.")
        else:
            labels = {f"[{o.score}] {o.title}": o for o in contact_now}
            chosen = st.selectbox(
                "Lead",
                options=list(labels.keys()),
                key="cold_pitch_lead",
            )
            opp = labels[chosen]
            lang = st.radio(
                "Language",
                options=["sr", "en"],
                format_func=lambda x: "Srpski" if x == "sr" else "English",
                horizontal=True,
                key="cold_pitch_lang",
            )
            pitch = cold_pitch.build_cold_pitch(opp, lang=lang)

            label, fg, bg = _RADAR_STYLE[opp.radar]
            st.markdown(
                f"{_chip(label, fg, bg)} &nbsp; "
                f"{_chip(f'score {opp.score}', '#fff', _score_color(opp.score))} &nbsp; "
                f"**{opp.target_org or opp.title}**",
                unsafe_allow_html=True,
            )

            a, b = st.columns(2)
            with a:
                st.markdown("##### A. Poslovni signal")
                st.write(pitch.signal)
                st.markdown("##### B. Značaj za kompaniju")
                st.write(pitch.relevance)
                st.markdown("##### Ključna pitanja")
                for q in pitch.key_questions:
                    st.markdown(f"- {q}")
            with b:
                st.markdown("##### C. Naša ekspertiza")
                st.write(pitch.expertise)
                st.markdown("##### D. Mikro-isporuka")
                st.success(pitch.micro_delivery)
                st.markdown("##### Završetak")
                st.write(pitch.closing_line)
                st.caption(f"{pitch.word_count} riječi · cilj ~100–150")
                if pitch.passes_rules:
                    st.success("✅ " + pitch.rule_notes[0])
                else:
                    for n in pitch.rule_notes:
                        st.warning(n)

            st.divider()
            st.markdown("#### Generisana poruka")
            st.text_input("Subject", value=pitch.subject, key="cold_subj_view")
            st.text_area("Message", value=pitch.body, height=260, key="cold_body_view")
            st.caption(f"To: {outreach.demo_recipient(opp)}")
            if st.button("✉️ Open send dialog", key="cold_open_send"):
                _outreach_dialog(opp.id)

            with st.expander("Šta se ne smije (banned phrases)"):
                st.caption(
                    "Poruka se automatski odbija ako sadrži: traženje sastanka, "
                    "„javite nam se ako ste zainteresovani“, „sveobuhvatnu pravnu podršku“, "
                    "„vodeća kancelarija“, calendar link, itd."
                )
                st.code("\n".join(cold_pitch.BANNED_PHRASES[:8]) + "\n…")

            with st.expander("Logika daljeg kontakta"):
                st.markdown(
                    "1. Ako prihvate materijal → pošalji ga **bez** insistiranja na sastanak.\n"
                    "2. Nakon slanja → jedno konkretno pitanje o njihovoj situaciji.\n"
                    "3. Sastanak tek kada pokažu interes — kao nastavak stručne razmjene."
                )

    with tab_position:
        st.markdown(
            "**Solution-first BD.** Not *“we saw a problem and can help”* — but "
            "*“we saw the problem, analysed it, and here is how we think it could be solved.”* "
            "Public facts only · diagnosis → hypothesis → route · execution stays paid."
        )
        contact_now = sorted(opps, key=lambda o: o.score, reverse=True)
        if not contact_now:
            st.info("No CONTACT NOW leads for the current filters.")
        else:
            labels = {f"[{o.score}] {o.title}": o for o in contact_now}
            chosen = st.selectbox("CONTACT NOW lead", options=list(labels.keys()))
            opp = labels[chosen]
            brief = solution.build_solution(opp)

            label, fg, bg = _RADAR_STYLE[opp.radar]
            st.markdown(
                f"{_chip(label, fg, bg)} &nbsp; "
                f"{_chip(f'score {opp.score}', '#fff', _score_color(opp.score))} &nbsp; "
                f"**{opp.target_org or opp.title}**",
                unsafe_allow_html=True,
            )
            st.info(f"⚠️ {solution.DISCLAIMER}")

            c1, c2 = st.columns(2)
            with c1:
                st.markdown("##### 🔴 The problem")
                st.write(brief.problem)
                st.markdown("##### 📄 What we know (public)")
                for x in brief.what_we_know:
                    st.markdown(f"- {x}")
                st.markdown("##### ⚖️ Serbian legal angle")
                st.write(brief.serbian_legal_angle)
                st.markdown("##### 🔎 Preliminary diagnosis")
                st.write(brief.preliminary_diagnosis)
            with c2:
                st.markdown("##### 🧩 Free solution concept (the route)")
                for i, step in enumerate(brief.free_solution_concept, 1):
                    st.markdown(f"{i}. {step}")
                st.caption("Given free: diagnosis → hypothesis → route. **Not** the full "
                           "claim, memorandum or quantum — that's the paid mandate.")
                st.markdown("##### 🔐 What we'd need to verify")
                for x in brief.what_to_verify:
                    st.markdown(f"- {x}")
                st.markdown("##### 💼 Paid mandate that follows")
                st.success(brief.paid_mandate)

            st.divider()
            r1, r2, r3 = st.columns(3)
            r1.markdown(f"**🎯 Decision-maker**\n\n{brief.decision_maker}")
            r2.markdown(f"**🤝 Warm route**\n\n{brief.warm_route}")
            r3.markdown(f"**⏱ Follow-up**\n\n{brief.follow_up}")

            st.divider()
            st.markdown("#### ⚠️ Conflicts & confidentiality gate")
            st.caption("Clear all before sending targeted advice.")
            checks = [
                st.checkbox(item, key=f"conf_{opp.id}_{i}")
                for i, item in enumerate(brief.conflict_checklist)
            ]
            cleared = all(checks)

            email_tab, li_tab = st.tabs(["✉️ Solution email", "💬 LinkedIn"])
            with email_tab:
                subj = st.text_input("Subject", value=brief.email_subject,
                                     key=f"sol_subj_{opp.id}")
                body = st.text_area("Message", value=brief.email_body, height=320,
                                    key=f"sol_body_{opp.id}")
                to_addr = outreach.demo_recipient(opp)
                st.caption(f"To: {to_addr} · Demo only — no email is actually sent.")
                if st.button("📨 Send solution email", type="primary",
                             disabled=not cleared, key=f"sol_send_{opp.id}",
                             help=None if cleared else "Clear the conflicts gate first."):
                    from datetime import datetime, timezone

                    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
                    saved = store.get(opp.id) or opp
                    saved.stage = Stage.CONTACTED
                    saved.notes = (saved.notes + f"\n[{stamp}] Solution-first outreach sent to "
                                   f"{to_addr} — “{subj}”").strip()
                    saved.next_action_at = "Follow up in 5 business days"
                    store.upsert(saved, preserve_stage=False)
                    for pref in ("brief", "pipe"):
                        st.session_state[f"{pref}_stage_{opp.id}"] = Stage.CONTACTED.value
                    st.session_state["_sent_flash"] = (
                        f"Solution email sent to {to_addr} · moved to CONTACTED"
                    )
                    st.rerun()
                if not cleared:
                    st.warning("Sending is locked until the conflicts & confidentiality gate is cleared.")
            with li_tab:
                st.text_area("LinkedIn message", value=brief.linkedin_message, height=140,
                             key=f"sol_li_{opp.id}")

    with tab_clients:
        st.markdown(
            "The firm's existing relationships, cross-referenced against today's "
            "market intelligence — the private half of the MATCH phase."
        )
        clients = sample_clients()
        # We match against ALL current opportunities, not just the filtered view.
        all_opps = store.list()
        linked = {c.id: match_opportunities(c, all_opps) for c in clients}

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Clients", len(clients))
        m2.metric("Active", sum(c.status == "Active" for c in clients))
        m3.metric("Dormant", sum(c.status == "Dormant" for c in clients))
        m4.metric(
            "♻ Reactivation",
            sum(1 for c in clients if c.status == "Dormant" and linked[c.id]),
        )

        f1, f2, f3 = st.columns([2, 2, 1])
        query = f1.text_input("Search", key="client_search", placeholder="name, sector, tag…")
        sectors = sorted({c.sector for c in clients})
        sel_sector = f2.multiselect("Sector", options=sectors, default=sectors)
        statuses = ["Active", "Dormant", "Prospect"]
        sel_status = f3.multiselect("Status", options=statuses, default=statuses)
        only_linked = st.checkbox("Only clients with live opportunities", value=False)

        q = (query or "").strip().lower()
        shown = 0
        for c in clients:
            if c.sector not in sel_sector or c.status not in sel_status:
                continue
            if only_linked and not linked[c.id]:
                continue
            if q and q not in " ".join([c.name, c.sector, *c.tags, c.owner]).lower():
                continue
            _render_client_card(c, all_opps)
            shown += 1
        if shown == 0:
            st.info("No clients match the current filters.")

    with tab_notify:
        st.markdown(
            "How the team gets alerted the moment something worth money happens — "
            "the same alert delivered across channels."
        )
        if st.button("🔔 Send a test alert"):
            if notes:
                st.toast(f"**{notes[0].title}**\n\n{notes[0].body}", icon="🔔")
        if not notes:
            st.info("No alert-worthy opportunities right now.")
        else:
            ch_push, ch_slack, ch_email = st.columns(3)
            with ch_push:
                st.markdown("**📱 Mobile push**")
                for n in notes[:3]:
                    st.markdown(notifications.push_card_html(n), unsafe_allow_html=True)
            with ch_slack:
                st.markdown("**💬 Slack / Teams**")
                for n in notes[:3]:
                    st.markdown(notifications.slack_message_html(n), unsafe_allow_html=True)
            with ch_email:
                st.markdown("**✉️ Email digest**")
                for n in notes[:6]:
                    st.markdown(notifications.email_row_html(n), unsafe_allow_html=True)


if __name__ == "__main__":
    main()
