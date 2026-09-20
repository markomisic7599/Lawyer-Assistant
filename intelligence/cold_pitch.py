"""Cold-pitch message generator (value-first, no meeting ask).

Formula:
  business signal → relevance for the company → key questions →
  our concrete capability → free micro-delivery

The first message must NOT ask for a meeting, calendar slot or engagement.
It ends by offering a concrete, quickly deliverable material tailored to
the recipient's situation.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import Opportunity, Radar

SENDER_NAME = "Marko Parivodić"
SENDER_TITLE = "Partner"


def _greeting(opp: Opportunity, lang: str) -> str:
    who = (opp.contact.name or "").strip()
    if lang == "sr":
        return f"Poštovani {who}," if who else "Poštovani,"
    return f"Dear {who}," if who else "Dear Sir or Madam,"

# Phrases that turn the message into a generic sales pitch — never use these.
BANNED_PHRASES = (
    "javite nam se ako ste zainteresovani",
    "voljeli bismo da zakažemo sastanak",
    "voljeli bismo da zakazemo sastanak",
    "da li imate 30 minuta",
    "vidimo prostor za potencijalnu saradnju",
    "sveobuhvatnu pravnu podršku",
    "sveobuhvatnu pravnu podrsku",
    "vodeća kancelarija",
    "vodeca kancelarija",
    "predstavimo naše usluge",
    "predstavimo nase usluge",
    "odgovarajući termin za sastanak",
    "odgovarajuci termin za sastanak",
    "would you be open to a brief call",
    "schedule a meeting",
    "book a call",
    "30 minutes",
    "comprehensive legal support",
    "leading law firm",
    "if you are interested, please let us know",
)


@dataclass
class ColdPitch:
    signal: str
    relevance: str
    key_questions: list[str]
    expertise: str
    micro_delivery: str
    closing_line: str
    subject: str
    body: str
    word_count: int
    passes_rules: bool
    rule_notes: list[str]


def _first_sentence(text: str) -> str:
    text = " ".join((text or "").split()).strip()
    if not text:
        return ""
    parts = text.split(". ")
    first = parts[0].rstrip(".")
    return first


def _build_parts(opp: Opportunity, lang: str) -> tuple[str, str, list[str], str, str, str]:
    """Return signal, relevance, questions, expertise, micro_delivery, closing."""
    org = opp.target_org or ("the company" if lang == "en" else "kompanija")
    signal_raw = _first_sentence(opp.why_now) or _first_sentence(opp.title)
    if lang == "sr" and signal_raw:
        # Demo facts may be English; keep the fact, frame the sentence in Serbian.
        signal_framed = (
            f"U javnosti se pojavila informacija relevantna za {org}: {signal_raw}"
        )
    else:
        signal_framed = signal_raw

    if opp.radar == Radar.STUCK_PROJECT:
        if lang == "sr":
            signal = signal_framed or f"javno su se pojavile indikacije zastoja na projektu ({org})"
            relevance = (
                f"Za {org} to može značiti pritisak na rokove, gotovinu i ugovornu poziciju — "
                f"prije nego što stvar preraste u formalni spor."
            )
            questions = [
                "da li kašnjenje potiče (dijelom) od okolnosti koje snosi naručilac",
                "da li su sačuvani relevantni notice-i i zahtjevi za EOT",
                "kako razdvojiti employer-risk od contractor delay-a",
                "da li postoji prostor za strukturisanu nagodbu prije eskalacije",
            ]
            expertise = (
                "Na ovakvim projektima analiziramo ugovorni režim i programe, identifikujemo "
                "pravne i ugovorne rizike, razdvajamo uzroke kašnjenja i pripremamo strategiju "
                "za ostvarivanje ili odbranu zahtjeva."
            )
            micro = (
                "kratku check-listu ključnih pravnih i ugovornih pitanja koja bi trebalo "
                "provjeriti prije narednog koraka"
            )
            closing = (
                f"Ako je ova tema već na Vašem radaru, mogu Vam poslati {micro}."
            )
        else:
            signal = signal_raw or f"public indications of a project delay/dispute involving {org}"
            relevance = (
                f"For {org}, this may create pressure on schedule, cash flow and contractual "
                f"position — before the matter turns into a formal dispute."
            )
            questions = [
                "whether part of the delay originates from employer-controlled matters",
                "whether the relevant notices and EOT claims have been preserved",
                "how to separate employer-risk delay from contractor delay",
                "whether there is room for a structured settlement before escalation",
            ]
            expertise = (
                "On projects like this we analyse the contractual regime and programme, "
                "identify legal and contractual risks, separate delay causation and prepare "
                "a strategy to assert or defend the claim."
            )
            micro = (
                "a short checklist of the key legal and contractual points to verify "
                "before the next step"
            )
            closing = (
                f"If this is already on your radar, I can send you {micro}."
            )

    elif opp.radar == Radar.REGULATORY_MONEY:
        if lang == "sr":
            signal = signal_framed or "objavljena je relevantna regulatorna promjena"
            relevance = (
                f"Za {org} to može otvoriti obavezu usklađivanja ili konkretnu priliku — "
                f"u zavisnosti od toga kako se promjena mapira na postojeći model poslovanja."
            )
            questions = [
                "koje tačke promjene su zaista relevantne za Vaš model",
                "da li postoji rok koji forsira akciju",
                "da li se usklađivanje može kombinovati sa dostupnom koristi / podsticajem",
                "šta je minimum koji treba uraditi bez nepotrebnog prekrajanja ugovora",
            ]
            expertise = (
                "U ovakvim situacijama mapiramo promjenu na konkretan model poslovanja, "
                "identifikujemo pravne i ugovorne rizike i pripremamo ciljani pregled "
                "šta zaista zahtijeva pažnju."
            )
            micro = (
                "pregled promjene i njenog mogućeg uticaja na kompanije iz Vašeg sektora "
                "na jednoj strani"
            )
            closing = (
                f"Pripremio sam kratak {micro}, koji Vam mogu proslijediti."
            )
        else:
            signal = signal_raw or "a relevant regulatory change has been published"
            relevance = (
                f"For {org}, this may create a compliance obligation or a concrete opportunity — "
                f"depending on how the change maps onto the existing business model."
            )
            questions = [
                "which points of the change actually matter for your model",
                "whether there is a hard deadline forcing action",
                "whether compliance can be combined with an available benefit / incentive",
                "what the minimum necessary action is without unnecessary re-papering",
            ]
            expertise = (
                "In situations like this we map the change onto the concrete business model, "
                "identify legal and contractual risks and prepare a targeted one-pager on "
                "what truly needs attention."
            )
            micro = (
                "a one-page overview of the change and its likely impact on companies "
                "in your sector"
            )
            closing = f"I have prepared a short {micro}, which I can send through."

    else:  # FIND
        if lang == "sr":
            signal = signal_framed or f"{org} ulazi u novu fazu projekta"
            relevance = (
                f"Za {org} to može značiti da se u kratkom roku otvaraju pitanja dozvola, "
                f"ugovaranja, zapošljavanja i institucionalnog interfejsa — koja direktno "
                f"utiču na rok i isplativost."
            )
            questions = [
                "koje dozvole i saglasnosti su na kritičnoj putanji",
                "kako sekvencirati land / permits / construction / employment",
                "da li postoji prostor za podsticaje / state-aid",
                "koji ugovorni model najbolje štiti rok i raspodjelu rizika",
            ]
            expertise = (
                "Na ovakvim projektima mapiramo potrebne dozvole i saglasnosti, analiziramo "
                "uslove i rizike, i strukturiramo ugovorni odnos kako bi se zaštitio rok."
            )
            micro = (
                "preliminarnu mapu dozvola i saglasnosti koje bi ovakav projekat "
                "zahtijevao"
            )
            closing = (
                f"Ako razmatrate ovu mogućnost, mogu Vam poslati {micro}."
            )
        else:
            signal = signal_raw or f"{org} is entering a new project phase"
            relevance = (
                f"For {org}, this can quickly open questions around permits, contracting, "
                f"employment and the institutional interface — which directly affect "
                f"schedule and economics."
            )
            questions = [
                "which permits and approvals sit on the critical path",
                "how to sequence land / permits / construction / employment",
                "whether incentives / state-aid may be available",
                "which contractual model best protects schedule and risk allocation",
            ]
            expertise = (
                "On projects like this we map the required permits and approvals, analyse "
                "conditions and risks, and structure the contractual relationship so the "
                "schedule is protected."
            )
            micro = (
                "a preliminary map of the permits and approvals a project of this kind "
                "would require"
            )
            closing = (
                f"If you are considering this, I can send you {micro}."
            )

    return signal, relevance, questions, expertise, micro, closing


def _compose_body(
    opp: Opportunity,
    lang: str,
    signal: str,
    relevance: str,
    questions: list[str],
    expertise: str,
    closing: str,
) -> str:
    greeting = _greeting(opp, lang)
    # Keep to ~3–4 key questions max in the prose.
    qs = questions[:4]
    if lang == "sr":
        q_join = ", ".join(qs[:-1]) + f" i {qs[-1]}" if len(qs) > 1 else qs[0]
        body = (
            f"{greeting}\n\n"
            f"{signal[0].upper() + signal[1:]}. {relevance} "
            f"Ključna pitanja će vjerovatno biti {q_join}.\n\n"
            f"{expertise}\n\n"
            f"{closing}"
        )
        sign = f"\n\nSrdačno,\n{SENDER_NAME.split()[0]}\n{SENDER_TITLE}, Parivodic Lawyers"
    else:
        q_join = ", ".join(qs[:-1]) + f" and {qs[-1]}" if len(qs) > 1 else qs[0]
        body = (
            f"{greeting}\n\n"
            f"{signal[0].upper() + signal[1:]}. {relevance} "
            f"The key questions will likely be {q_join}.\n\n"
            f"{expertise}\n\n"
            f"{closing}"
        )
        sign = f"\n\nKind regards,\n{SENDER_NAME.split()[0]}\n{SENDER_TITLE}, Parivodic Lawyers"
    return body + sign


def _subject(opp: Opportunity, lang: str) -> str:
    org = opp.target_org or ("projekat" if lang == "sr" else "project")
    if opp.radar == Radar.STUCK_PROJECT:
        return (
            f"{org}: kratka check-lista prije narednog koraka"
            if lang == "sr"
            else f"{org}: a short checklist before the next step"
        )
    if opp.radar == Radar.REGULATORY_MONEY:
        return (
            "Kratak pregled nedavne regulatorne promjene"
            if lang == "sr"
            else "A short note on a recent regulatory change"
        )
    return (
        f"Preliminarna mapa dozvola za {org}"
        if lang == "sr"
        else f"A preliminary permit map for {org}"
    )


def _validate(body: str, micro: str) -> tuple[bool, list[str], int]:
    notes: list[str] = []
    lower = body.lower()
    words = [w for w in body.replace("\n", " ").split() if w]
    wc = len(words)

    for phrase in BANNED_PHRASES:
        if phrase in lower:
            notes.append(f"Banned phrase: “{phrase}”")

    if "sastanak" in lower or "meeting" in lower or "calendar" in lower:
        notes.append("Asks for a meeting / calendar — not allowed in the first message.")

    if wc < 70:
        notes.append(f"Too short ({wc} words) — target ~100–150.")
    elif wc > 180:
        notes.append(f"Too long ({wc} words) — target ~100–150.")

    if not micro or len(micro) < 20:
        notes.append("Micro-delivery is missing or too vague.")

    # Must end with an offer to send something, not a call.
    last = body.strip().split("\n\n")[-2] if "\n\n" in body.strip() else body
    offer_markers = (
        "mogu vam poslati",
        "mogu vam proslijediti",
        "vam mogu proslijediti",
        "vam mogu poslati",
        "i can send",
        "which i can send",
    )
    if not any(m in last.lower() for m in offer_markers):
        # also check penultimate paragraph (signature is last)
        paras = [p for p in body.strip().split("\n\n") if p.strip()]
        offer_para = paras[-2] if len(paras) >= 2 else paras[-1]
        if not any(m in offer_para.lower() for m in offer_markers):
            notes.append("Closing does not clearly offer a free micro-delivery.")

    return len(notes) == 0, notes, wc


def build_cold_pitch(opp: Opportunity, lang: str = "sr") -> ColdPitch:
    signal, relevance, questions, expertise, micro, closing = _build_parts(opp, lang)
    body = _compose_body(opp, lang, signal, relevance, questions, expertise, closing)
    subject = _subject(opp, lang)
    ok, notes, wc = _validate(body, micro)
    if ok:
        notes = ["Passes the cold-pitch rules (value first, no meeting ask)."]
    return ColdPitch(
        signal=signal,
        relevance=relevance,
        key_questions=questions,
        expertise=expertise,
        micro_delivery=micro,
        closing_line=closing,
        subject=subject,
        body=body,
        word_count=wc,
        passes_rules=ok,
        rule_notes=notes,
    )


def draft_cold_email(opp: Opportunity, lang: str = "sr") -> tuple[str, str]:
    """Drop-in replacement for outreach.draft_email — cold-pitch formula."""
    pitch = build_cold_pitch(opp, lang=lang)
    return pitch.subject, pitch.body
