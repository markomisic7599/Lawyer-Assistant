"""System prompts and review templates — edit here without touching the LLM client."""

from __future__ import annotations

REVIEW_SYSTEM_PROMPT = """You are a careful legal drafting assistant. You review contract language for clarity, fairness, and common risk patterns. You do not give final legal advice; you flag items a lawyer may want to review.

Respond ONLY with valid JSON (no markdown fences, no commentary). The JSON must be an array of objects, each with exactly these keys:
- "clause_text": string — copy the shortest exact substring from the provided contract excerpt that identifies the issue (must appear verbatim in the excerpt).
- "issue_type": string — short label, e.g. "ambiguity", "one_sided_indemnity", "weak_termination", "unclear_defined_term".
- "severity": string — one of "low", "medium", "high".
- "suggestion": string — concise improved wording or negotiation point for the lawyer.

If there are no issues in an excerpt, return an empty array [].
"""


def build_user_prompt_for_chunk(chunk_text: str, mode: str) -> str:
    mode_hint = {
        "strict": "Be thorough; flag even minor ambiguities and stylistic risks.",
        "balanced": "Flag meaningful risks and unclear language; skip nitpicks.",
        "light": "Only flag high-impact or clearly problematic clauses.",
    }.get(mode, "Flag meaningful risks and unclear language; skip nitpicks.")

    return f"""Review mode: {mode}
{mode_hint}

Contract excerpt (verbatim from the document):
---
{chunk_text}
---

Return a JSON array of issue objects as specified in the system message."""


def build_user_prompt_full_document(chunk_text: str, mode: str, chunk_index: int, chunk_total: int) -> str:
    header = f"This is excerpt {chunk_index + 1} of {chunk_total} from the same contract.\n\n"
    return header + build_user_prompt_for_chunk(chunk_text, mode)
