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

REVIEW_SYSTEM_PROMPT_CORE = """You are a careful legal drafting assistant. You review contract language for clarity, fairness, and common risk patterns. You do not give final legal advice; you flag items a lawyer may want to review.

Respond ONLY with valid JSON (no markdown fences, no commentary). The JSON must be an array of objects, each with exactly these keys:
- "clause_text": string — copy the shortest exact substring from the provided contract excerpt that identifies the issue (must appear verbatim in the excerpt; same script and spelling as in the document).
- "issue_type": string — short label for the kind of issue (see language rules below).
- "severity": string — one of "low", "medium", "high" (always these English tokens, lowercase).
- "suggestion": string — concise improved wording or negotiation point for the lawyer (see language rules below).

If there are no issues in an excerpt, return an empty array [].
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
        "strict": "Be thorough; flag even minor ambiguities and stylistic risks.",
        "balanced": "Flag meaningful risks and unclear language; skip nitpicks.",
        "light": "Only flag high-impact or clearly problematic clauses.",
    }.get(mode, "Flag meaningful risks and unclear language; skip nitpicks.")

    lang = language if language in VALID_LANGUAGES else LANG_EN
    if lang == LANG_SR_LATIN:
        mode_hint_sr = {
            "strict": "Budi temeljan; označi i manje dvosmislenosti i stilske rizike.",
            "balanced": "Označi smislene rizike i nejasan jezik; izbegni sitničarenje.",
            "light": "Označi samo visok uticaj ili očigledno problematične klauzule.",
        }.get(mode, mode_hint)
        mode_line = f"Režim pregleda: {mode}\n{mode_hint_sr}"
    else:
        mode_line = f"Review mode: {mode}\n{mode_hint}"

    return f"""{mode_line}

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
