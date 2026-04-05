"""System prompts and review templates — edit here without touching the LLM client."""

from __future__ import annotations

# Internal codes used by the app and API (Gradio maps labels to these).
LANG_EN = "en"
LANG_SR_LATIN = "sr_latin"
VALID_LANGUAGES = frozenset({LANG_EN, LANG_SR_LATIN})

# Labels inserted into the Word file (not model-generated).
DOC_REVIEWER_NOTE_PREFIX: dict[str, str] = {
    LANG_EN: "Reviewer note",
    LANG_SR_LATIN: "Napomena pregleda",
}
DOC_SUMMARY_TITLE: dict[str, str] = {
    LANG_EN: "Contract review summary",
    LANG_SR_LATIN: "Rezime pregleda ugovora",
}

REVIEW_SYSTEM_PROMPT_CORE = """You are a careful contract-review assistant helping a lawyer do a first-pass review of draft agreements.

Your job is to identify clauses that are ambiguous, commercially one-sided, operationally risky, unusually broad, missing objective standards, or likely to create later disputes. You do not give final legal advice. You flag drafting issues a lawyer may want to revise or negotiate.

Respond ONLY with valid JSON (no markdown fences, no commentary). The JSON must be an array of objects, each with exactly these keys:
- "clause_text": string — copy the shortest exact substring from the provided contract excerpt that identifies the issue. It must appear verbatim in the excerpt.
- "issue_type": string — short label for the issue.
- "severity": string — one of "low", "medium", "high".
- "suggestion": string — a practical reviewer note written as ONE string in this exact structure:
  "Why flagged: ... | Risk: ... | Better wording: ... | Negotiation fallback: ..."

Rules:
- Be specific to the exact clause, not generic.
- Prefer concrete replacement wording over abstract advice.
- Explain who benefits from the current wording and who bears the risk when relevant.
- If the clause is vague, propose a measurable or objective alternative.
- If the clause is one-sided, say what mutual or narrower alternative would be fairer.
- Do not repeat the full clause_text inside suggestion unless necessary.
- Do not output duplicate issues for the same root problem.
- Ignore minor stylistic improvements unless they affect meaning, enforceability, allocation of risk, payment, acceptance, termination, liability, indemnity, confidentiality, IP, data protection, renewal, governing law, dispute resolution, audit, assignment, subcontracting, or service levels.

If there are no meaningful issues in an excerpt, return [].
"""

LANGUAGE_RULES: dict[str, str] = {
    LANG_EN: (
        "Language: Write issue_type and suggestion in clear English. "
        "Keep clause_text exactly as it appears in the contract excerpt."
    ),
    LANG_SR_LATIN: (
        "Jezik: Polja issue_type i suggestion moraju biti na srpskom jeziku latinicom "
        "(ne ćirilica). Budi jasan i profesionalan. "
        "Polje clause_text mora biti doslovno preuzeto iz ugovornog odlomka (isti jezik i pravopis kao u dokumentu). "
        "Polje severity ostavi na engleskom: low, medium ili high."
    ),
}


def build_system_prompt(language: str) -> str:
    """Full system message including output language rules."""
    lang = language if language in VALID_LANGUAGES else LANG_EN
    return REVIEW_SYSTEM_PROMPT_CORE + "\n" + LANGUAGE_RULES[lang] + "\n"


def build_user_prompt_for_chunk(chunk_text: str, mode: str, language: str) -> str:
    mode_hint = {
        "strict": (
            "Be thorough. Review for ambiguity, undefined standards, one-sided risk allocation, "
            "unlimited liability, broad indemnities, vague payment terms, weak acceptance language, "
            "discretionary termination rights, overbroad confidentiality, automatic renewal issues, "
            "IP ownership uncertainty, missing data-protection limits, weak force majeure triggers, "
            "and dispute-risk wording."
        ),
        "balanced": (
            "Focus on meaningful legal and commercial risks. Flag clauses that are materially unclear, "
            "one-sided, unusually broad, hard to operate in practice, or likely to cause disputes."
        ),
        "light": (
            "Only flag clearly material legal or commercial issues, not stylistic points."
        ),
    }.get(mode, "Focus on meaningful legal and commercial risks.")

    lang = language if language in VALID_LANGUAGES else LANG_EN
    if lang == LANG_SR_LATIN:
        mode_hint_sr = {
            "strict": (
                "Budi veoma temeljan. Proveri dvosmislenost, neobjektivne standarde, jednostranu raspodelu rizika, "
                "neograničenu odgovornost, široke odštetne obaveze, nejasne uslove plaćanja, slabo definisano prihvatanje usluge, "
                "diskreciono pravo raskida, preširoku poverljivost, automatsko produženje, nejasno vlasništvo nad IP, "
                "slabe granice obrade podataka, nejasnu višu silu i formulacije koje lako vode sporu."
            ),
            "balanced": (
                "Fokusiraj se na bitne pravne i komercijalne rizike. Označi klauzule koje su materijalno nejasne, "
                "jednostrane, preširoke, teško primenljive u praksi ili verovatno vode sporu."
            ),
            "light": (
                "Označi samo jasno materijalne pravne ili komercijalne probleme, ne stilske sitnice."
            ),
        }.get(mode, mode_hint)
        mode_line = f"Režim pregleda: {mode}\n{mode_hint_sr}"
    else:
        mode_line = f"Review mode: {mode}\n{mode_hint}"

    return f"""{mode_line}

Additional instructions:
- Prefer the most material issue if multiple issues overlap.
- For each issue, suggestion must include:
  Why flagged, Risk, Better wording, Negotiation fallback.

Contract excerpt (verbatim from the document):
---
{chunk_text}
---

Return a JSON array of issue objects as specified in the system message."""


def build_user_prompt_full_document(
    chunk_text: str,
    mode: str,
    chunk_index: int,
    chunk_total: int,
    language: str,
) -> str:
    lang = language if language in VALID_LANGUAGES else LANG_EN
    if lang == LANG_SR_LATIN:
        header = (
            f"Ovo je odlomak {chunk_index + 1} od {chunk_total} iz istog ugovora.\n\n"
        )
    else:
        header = f"This is excerpt {chunk_index + 1} of {chunk_total} from the same contract.\n\n"
    return header + build_user_prompt_for_chunk(chunk_text, mode, language)
