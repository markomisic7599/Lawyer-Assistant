"""Parivodic Industrial Information Hub — Streamlit demo.

Website-facing content hub (separate from the internal BD intelligence system).
Shows sector browsing, article structure, subscriptions, and the human legal
review queue.

Run from the repo root:
    streamlit run hub/streamlit_app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

from hub import (
    PUBLISH_CRITERIA,
    ContentStatus,
    EditorialState,
    HubArticle,
    Industry,
    Subscriber,
)
from hub.demo_data import articles_for_industries, sample_articles, sample_subscribers

_STATUS_COLOR = {
    ContentStatus.URGENT_ALERT: ("#b3261e", "#fbe9e7"),
    ContentStatus.IMPORTANT: ("#a1770a", "#fdf5e0"),
    ContentStatus.OPPORTUNITY: ("#2e7d54", "#e7f5ee"),
    ContentStatus.CASE_LAW: ("#1264a3", "#e8f1fb"),
    ContentStatus.STRATEGIC: ("#5c4a7a", "#f0ebf5"),
    ContentStatus.NOT_RELEVANT: ("#666", "#eee"),
}


def _chip(text: str, fg: str, bg: str) -> str:
    return (
        f"<span style='background:{bg};color:{fg};padding:2px 10px;border-radius:12px;"
        f"font-size:12px;font-weight:600;white-space:nowrap;'>{text}</span>"
    )


def _status_chip(status: ContentStatus) -> str:
    fg, bg = _STATUS_COLOR.get(status, ("#555", "#eee"))
    return _chip(status.value, fg, bg)


def _industry_chips(inds: list[Industry]) -> str:
    return " ".join(_chip(i.value, "#333", "#f0f0f0") for i in inds)


@st.cache_resource
def _store() -> dict:
    """Simple in-memory demo store (survives Streamlit reruns in-session)."""
    return {
        "articles": sample_articles(),
        "subscribers": sample_subscribers(),
    }


def _published(articles: list[HubArticle]) -> list[HubArticle]:
    return [
        a
        for a in articles
        if a.editorial == EditorialState.PUBLISHED
        and a.status != ContentStatus.NOT_RELEVANT
    ]


def _render_article_card(a: HubArticle, *, key_prefix: str) -> None:
    with st.container(border=True):
        st.markdown(
            f"{_status_chip(a.status)} &nbsp; {_industry_chips(a.industries)}",
            unsafe_allow_html=True,
        )
        st.markdown(f"#### {a.title}")
        st.write(a.executive_summary)
        meta = []
        if a.deadline:
            meta.append(f"⏱ {a.deadline}")
        if a.published_at:
            meta.append(f"Objavljeno: {a.published_at}")
        if meta:
            st.caption(" · ".join(meta))
        if st.button("Otvori analizu →", key=f"{key_prefix}_{a.id}"):
            st.session_state["hub_article"] = a.id
            st.rerun()


def _render_full_article(a: HubArticle) -> None:
    st.markdown(
        f"{_status_chip(a.status)} &nbsp; {_industry_chips(a.industries)}",
        unsafe_allow_html=True,
    )
    st.title(a.title)
    if a.deadline:
        st.warning(f"**Rok:** {a.deadline}")
    st.info(f"**Izvršni sažetak.** {a.executive_summary}")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### Šta se dogodilo?")
        st.write(a.what_happened)
        st.markdown("##### Koje kompanije su pogođene?")
        st.write(a.who_affected)
        st.markdown("##### Zašto je to poslovno važno?")
        st.write(a.why_business_matters)
    with c2:
        st.markdown("##### Ključni rizici")
        for r in a.key_risks:
            st.markdown(f"- {r}")
        st.markdown("##### Šta sada provjeriti / preduzeti")
        for i, ap in enumerate(a.action_points, 1):
            st.markdown(f"{i}. {ap}")

    st.success(f"**Dodatna vrijednost:** {a.micro_delivery}")
    if a.sources:
        st.markdown("##### Izvori")
        for s in a.sources:
            st.markdown(
                f"- [{s.title}]({s.url}) · {s.doc_status.value}"
                + (f" · {s.published}" if s.published else "")
            )
    if st.button("← Nazad na pregled"):
        st.session_state.pop("hub_article", None)
        st.rerun()


def _tab_browse(store: dict) -> None:
    articles = _published(store["articles"])
    st.markdown(
        "Sektorski prilagođen hub — objavljujemo **samo** kada postoji provjerena "
        "informacija koja kompanijama pomaže da iskoriste priliku, izbjegnu rizik "
        "ili donesu bolju odluku. Nema kvote sadržaja."
    )

    industries = st.multiselect(
        "Industrije",
        options=list(Industry),
        default=list(Industry),
        format_func=lambda i: i.value,
        key="browse_industries",
    )
    statuses = st.multiselect(
        "Tip sadržaja",
        options=[s for s in ContentStatus if s != ContentStatus.NOT_RELEVANT],
        default=[s for s in ContentStatus if s != ContentStatus.NOT_RELEVANT],
        format_func=lambda s: s.value,
        key="browse_status",
    )

    shown = [
        a
        for a in articles
        if a.status in statuses and set(a.industries).intersection(industries)
    ]
    shown.sort(key=lambda a: a.urgency, reverse=True)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Objavljeno", len(articles))
    m2.metric("Urgent", sum(a.status == ContentStatus.URGENT_ALERT for a in shown))
    m3.metric("Opportunities", sum(a.status == ContentStatus.OPPORTUNITY for a in shown))
    m4.metric("Prikazano", len(shown))

    if not shown:
        st.info("Nema sadržaja za izabrane filtere — i to je u redu. Kvalitet > kvota.")
    for a in shown:
        _render_article_card(a, key_prefix="browse")


def _tab_subscribe(store: dict) -> None:
    st.markdown(
        "Besplatna pretplata: birate industrije i dobijate **samo** relevantan sadržaj. "
        "Hitni alert odmah · sedmični pregled · mjesečni kalendar rokova. "
        "Ako nema relevantnog sadržaja — email se ne šalje."
    )
    with st.form("subscribe_form"):
        name = st.text_input("Ime")
        email = st.text_input("Email*")
        company = st.text_input("Kompanija")
        inds = st.multiselect(
            "Industrije*",
            options=list(Industry),
            format_func=lambda i: i.value,
        )
        c1, c2, c3 = st.columns(3)
        urgent = c1.checkbox("Hitna obavještenja", value=True)
        weekly = c2.checkbox("Sedmični pregled", value=True)
        monthly = c3.checkbox("Mjesečni kalendar", value=True)
        lang = st.radio("Jezik", ["sr", "en"], horizontal=True,
                        format_func=lambda x: "Srpski" if x == "sr" else "English")
        submitted = st.form_submit_button("Prijavi se", type="primary")
        if submitted:
            if not email or not inds:
                st.error("Email i barem jedna industrija su obavezni.")
            else:
                sub = Subscriber(
                    email=email.strip(),
                    name=name.strip(),
                    company=company.strip(),
                    industries=list(inds),
                    urgent_alerts=urgent,
                    weekly_digest=weekly,
                    monthly_calendar=monthly,
                    language=lang,
                )
                store["subscribers"].append(sub)
                st.success(
                    f"Prijavljeni ste za: {', '.join(i.value for i in inds)}. "
                    "Demo only — email se ne šalje."
                )

    st.divider()
    st.markdown("##### Pretplatnici (demo)")
    for s in store["subscribers"]:
        with st.container(border=True):
            st.markdown(f"**{s.company or s.email}** · {s.name or '—'}")
            st.caption(s.email)
            st.markdown(_industry_chips(s.industries), unsafe_allow_html=True)
            matched = articles_for_industries(store["articles"], s.industries)
            st.caption(
                f"U inboxu bi dobili {len(matched)} relevantnih tekstova "
                f"(od {len(_published(store['articles']))} objavljenih)."
            )
            if matched:
                with st.expander("Šta bi dobili"):
                    for a in matched:
                        st.markdown(f"- **{a.title}** _{a.status.value}_")


def _tab_editorial(store: dict) -> None:
    st.markdown(
        "**Ljudska pravna kontrola.** Sistem ne objavljuje samostalno. "
        "Za svaki nacrt: izvor, status dokumenta, industrije, hitnost, "
        "tvrdnje koje treba provjeriti — advokat odobrava prije objave."
    )
    with st.expander("Filter za objavljivanje (kriterijumi)"):
        st.caption(
            "Tekst se predlaže samo ako događaj ispunjava ≥1 kriterijum. "
            "Ako ne možemo odgovoriti: „Zašto bi direktor / pravna služba ovo čitali danas?“ — ne generisati."
        )
        for c in PUBLISH_CRITERIA:
            st.markdown(f"- {c}")

    queue = [
        a
        for a in store["articles"]
        if a.editorial in {
            EditorialState.INGESTED,
            EditorialState.DRAFT,
            EditorialState.IN_REVIEW,
            EditorialState.REJECTED,
        }
        or a.status == ContentStatus.NOT_RELEVANT
    ]
    # Also show in-review + rejected clearly
    queue = [a for a in store["articles"] if a.editorial != EditorialState.PUBLISHED]

    if not queue:
        st.success("Nema stavki na čekanju.")
        return

    for a in queue:
        with st.container(border=True):
            st.markdown(
                f"{_status_chip(a.status)} &nbsp; "
                f"{_chip(a.editorial.value, '#fff', '#333')} &nbsp; "
                f"{_industry_chips(a.industries)}",
                unsafe_allow_html=True,
            )
            st.markdown(f"**{a.title}**")
            st.caption(f"Hitnost {a.urgency} · pouzdanost {a.reliability:.0%}")
            if a.sources:
                s = a.sources[0]
                st.markdown(
                    f"Izvor: [{s.title}]({s.url}) · **{s.doc_status.value}**"
                    + (f" · {s.published}" if s.published else "")
                )
            if a.claims_to_verify:
                st.markdown("**Tvrdnje za provjeru:**")
                for c in a.claims_to_verify:
                    st.markdown(f"- ⚠️ {c}")
            if a.status == ContentStatus.NOT_RELEVANT:
                st.error(
                    "Status: Not relevant enough — ne objavljivati. "
                    "Nema jasan odgovor zašto bi pravna služba ovo čitala danas."
                )

            b1, b2, b3 = st.columns(3)
            if b1.button("✓ Odobri i objavi", key=f"ok_{a.id}",
                         disabled=a.status == ContentStatus.NOT_RELEVANT):
                a.editorial = EditorialState.PUBLISHED
                if not a.published_at:
                    from datetime import date
                    a.published_at = date.today().isoformat()
                st.rerun()
            if b2.button("✎ Vrati u draft", key=f"draft_{a.id}"):
                a.editorial = EditorialState.DRAFT
                st.rerun()
            if b3.button("✗ Odbij", key=f"rej_{a.id}"):
                a.editorial = EditorialState.REJECTED
                a.status = ContentStatus.NOT_RELEVANT
                st.rerun()


def _tab_about() -> None:
    st.markdown(
        """
### Princip

> Pronaći samo informacije koje zaista imaju vrijednost, objasniti ih iz
> perspektive pogođene industrije i pretvoriti ih u konkretnu poslovnu
> preporuku ili alat.

Sajt ne postoji da bi stalno proizvodio sadržaj. Postoji da bi postao
**centralni i pouzdani industrijski hub** za pravne, regulatorne i poslovne
informacije u Srbiji.

### Obavezna struktura teksta
1. Šta se dogodilo?
2. Koje kompanije su pogođene?
3. Zašto je to poslovno važno?
4. Ključni pravni i komercijalni rizici
5. Postoji li rok?
6. Šta sada provjeriti / preduzeti (3–5 action points)
7. Dodatna vrijednost (mikro-isporuka — ne „kontaktirajte nas“)

### Odnos prema BD sistemu
Ovaj hub je **javni** sloj za sajt i pretplatnike.  
Interni BD/intelligence sistem (`intelligence/`) ostaje odvojen — prati
prilike za mandate i cold pitch.
"""
    )


def main() -> None:
    st.set_page_config(
        page_title="Parivodic Information Hub",
        page_icon="📰",
        layout="wide",
    )
    store = _store()

    # Deep-link to a single article
    aid = st.session_state.get("hub_article")
    if aid:
        art = next((a for a in store["articles"] if a.id == aid), None)
        if art:
            with st.sidebar:
                st.markdown("## 📰 Information Hub")
                st.caption("Industrijski hub · demo")
                if st.button("← Svi tekstovi"):
                    st.session_state.pop("hub_article", None)
                    st.rerun()
            _render_full_article(art)
            return

    with st.sidebar:
        st.markdown("## 📰 Parivodic")
        st.caption("Industrial Information Hub")
        st.divider()
        st.markdown("Javni sloj za **sajt** — sektorski sadržaj, pretplate, editorial.")
        st.caption("Odvojeno od internog BD sistema (`intelligence/`).")
        st.divider()
        st.caption("Demo sadržaj je ilustrativan i fiktivan.")

    st.title("Industrijski information hub")
    st.markdown(
        "> Ne objavljivati zato što je vrijeme za novi tekst — već samo kada postoji "
        "provjerena informacija koja određenoj grupi kompanija može pomoći."
    )

    tab_b, tab_s, tab_e, tab_a = st.tabs(
        ["📚 Pregled", "🔔 Pretplata", "⚖️ Editorial queue", "ℹ️ O hubu"]
    )
    with tab_b:
        _tab_browse(store)
    with tab_s:
        _tab_subscribe(store)
    with tab_e:
        _tab_editorial(store)
    with tab_a:
        _tab_about()


if __name__ == "__main__":
    main()
