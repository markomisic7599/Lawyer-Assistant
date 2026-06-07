"""Prompts for turning legal text into a process-flowchart mind map.

Two prompt families:
  * extraction  - per chunk: pull out steps, decisions, documents, links.
  * consolidation - merge per-chunk partial graphs into one coherent flowchart.
"""

from __future__ import annotations

from .prompts import LANG_EN, LANG_SR_LATIN, VALID_LANGUAGES

DETAIL_OVERVIEW = "overview"
DETAIL_DETAILED = "detailed"
VALID_DETAIL = frozenset({DETAIL_OVERVIEW, DETAIL_DETAILED})

_NODE_TYPE_GUIDE = """Node "type" must be exactly one of:
- "title": the overall process name (use once, as the entry box).
- "process": an action/step someone must perform (rectangle).
- "decision": an approval, review, or authority gate (e.g. a Ministry, commission, or yes/no decision).
- "document": a required input document, study, application, or piece of evidence.
- "outcome": a final result of the process (permit issued, approval, rejection).
- "start"/"end": optional explicit entry/exit points.
"""

_JSON_SHAPE = """Respond with ONLY valid JSON (no markdown fences, no commentary), an object with this shape:
{
  "title": "string - the name of the process",
  "nodes": [
    {"id": "string - short unique slug", "label": "string - concise step text", "type": "process|decision|document|title|outcome|start|end", "article_refs": ["Art. 12 L1", ...]}
  ],
  "edges": [
    {"source": "node id", "target": "node id", "label": "string - optional condition or time limit, e.g. '30 days', 'if rejected'"}
  ]
}
"""

EXTRACTION_SYSTEM_CORE = f"""You are a legal-process analyst. You read statutes, regulations, and procedural rules and turn the PROCEDURE they describe into a flowchart graph (a process mind map), like the diagrams a law firm draws to explain how to obtain a permit or approval.

Focus on the *flow of actions*, not on summarising the law:
- Identify each step an applicant/authority must take, in order.
- Identify decision/approval gates and the bodies responsible (ministries, commissions, agencies).
- Identify required documents, studies, applications, and evidence as their own nodes.
- Capture time limits, deadlines, and branching conditions ("if rejected", "within 15 days") as EDGE labels.
- Whenever the text cites an article/section, attach it to the relevant node's "article_refs" (keep the citation verbatim, e.g. "Art. 135 L1").

{_NODE_TYPE_GUIDE}
Keep labels short (a few words). Connect nodes with edges so the graph reads top-to-bottom in procedural order. Only include what the text supports; do not invent steps.

{_JSON_SHAPE}"""

CONSOLIDATION_SYSTEM_CORE = f"""You are a legal-process analyst assembling one clean flowchart from several partial graphs that were each extracted from a different part of the SAME document.

Your job:
- Merge the partial graphs into a single coherent process flowchart.
- Remove duplicate or near-duplicate nodes (same step described twice); keep the clearest label and union their article_refs.
- Re-number ids to be unique and stable.
- Connect steps across the partial graphs so the overall procedure flows in order from start to outcome.
- Preserve all distinct decision gates, documents, and time-limit/condition edge labels.
- Keep exactly one "title" node for the overall process.

{_NODE_TYPE_GUIDE}
{_JSON_SHAPE}"""


def _language_rule(language: str) -> str:
    lang = language if language in VALID_LANGUAGES else LANG_EN
    if lang == LANG_SR_LATIN:
        return (
            "Jezik: Sve oznake (label) i nazive piši na srpskom jeziku latinicom (ne ćirilica). "
            "Reference na članove (article_refs) ostavi doslovno kako stoje u tekstu."
        )
    return (
        "Language: Write all labels and titles in clear English. "
        "Keep article references (article_refs) verbatim as they appear in the text."
    )


def _detail_rule(detail: str, language: str) -> str:
    lang = language if language in VALID_LANGUAGES else LANG_EN
    is_overview = detail != DETAIL_DETAILED
    if lang == LANG_SR_LATIN:
        return (
            "Nivo detalja: prikaži samo glavne korake i odluke (sažeto)."
            if is_overview
            else "Nivo detalja: uključi sve korake, dokumente, rokove i uslove grananja."
        )
    return (
        "Detail level: include only the main steps and decision gates (concise)."
        if is_overview
        else "Detail level: include every step, required document, deadline, and branching condition."
    )


def build_extraction_system_prompt(language: str) -> str:
    return EXTRACTION_SYSTEM_CORE + "\n" + _language_rule(language) + "\n"


def build_consolidation_system_prompt(language: str) -> str:
    return CONSOLIDATION_SYSTEM_CORE + "\n" + _language_rule(language) + "\n"


def build_extraction_user_prompt(
    chunk_text: str,
    detail: str,
    chunk_index: int,
    chunk_total: int,
    language: str,
) -> str:
    lang = language if language in VALID_LANGUAGES else LANG_EN
    header = (
        f"Ovo je deo {chunk_index + 1} od {chunk_total} istog dokumenta.\n"
        if lang == LANG_SR_LATIN
        else f"This is part {chunk_index + 1} of {chunk_total} of the same document.\n"
    )
    return (
        header
        + _detail_rule(detail, lang)
        + "\n\nDocument text (verbatim):\n---\n"
        + chunk_text
        + "\n---\n\nReturn the JSON graph object as specified."
    )


def build_consolidation_user_prompt(partial_graphs_json: str, detail: str, language: str) -> str:
    lang = language if language in VALID_LANGUAGES else LANG_EN
    intro = (
        "Parcijalni grafovi (JSON niz) iz delova istog dokumenta:\n"
        if lang == LANG_SR_LATIN
        else "Partial graphs (JSON array) extracted from parts of the same document:\n"
    )
    return (
        _detail_rule(detail, lang)
        + "\n\n"
        + intro
        + "---\n"
        + partial_graphs_json
        + "\n---\n\nReturn ONE consolidated JSON graph object as specified."
    )
