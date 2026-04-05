"""LLM provider calls — swap implementations here without touching UI or Word code."""

from __future__ import annotations

import json
import re
from typing import Any

from openai import OpenAI

from . import prompts, settings


def normalize_model_output(raw: str) -> list[dict[str, Any]]:
    """
    Parse model output into a list of issue dicts with keys:
    clause_text, issue_type, severity, suggestion.
    Strips optional ```json fences.
    """
    text = raw.strip()
    fence = re.match(r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", text, re.DOTALL | re.IGNORECASE)
    if fence:
        text = fence.group(1).strip()
    data = json.loads(text)
    if not isinstance(data, list):
        raise ValueError("Model output must be a JSON array")
    out: list[dict[str, Any]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        out.append(
            {
                "clause_text": str(item.get("clause_text", "")),
                "issue_type": str(item.get("issue_type", "unknown")),
                "severity": str(item.get("severity", "medium")),
                "suggestion": str(item.get("suggestion", "")),
            }
        )
    return out


def _client() -> OpenAI:
    if not settings.OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add it to your environment or a .env file."
        )
    kwargs: dict[str, Any] = {"api_key": settings.OPENAI_API_KEY}
    if settings.OPENAI_BASE_URL:
        kwargs["base_url"] = settings.OPENAI_BASE_URL
    return OpenAI(**kwargs)


def review_clause(text: str, mode: str) -> list[dict[str, Any]]:
    """Review a single clause/excerpt; returns normalized issue dicts."""
    return review_document([text], mode)


def review_document(chunks: list[str], mode: str) -> list[dict[str, Any]]:
    """
    Send each chunk to the model with the review prompt; concatenate parsed issues.
    """
    client = _client()
    all_issues: list[dict[str, Any]] = []
    total = len(chunks)
    for i, chunk in enumerate(chunks):
        if not chunk.strip():
            continue
        user_content = prompts.build_user_prompt_full_document(chunk, mode, i, total)
        resp = client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[
                {"role": "system", "content": prompts.REVIEW_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.2,
        )
        raw = resp.choices[0].message.content or "[]"
        all_issues.extend(normalize_model_output(raw))
    return all_issues
