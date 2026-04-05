"""LLM provider calls — swap implementations here without touching UI or Word code."""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

from openai import OpenAI

from . import prompts, settings
from .logging_setup import ensure_logging

logger = logging.getLogger(__name__)


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


def review_clause(
    text: str,
    mode: str,
    language: str = prompts.LANG_EN,
) -> list[dict[str, Any]]:
    """Review a single clause/excerpt; returns normalized issue dicts."""
    return review_document([text], mode, language=language)


def review_document(
    chunks: list[str],
    mode: str,
    *,
    language: str = prompts.LANG_EN,
) -> list[dict[str, Any]]:
    """
    Send each chunk to the model with the review prompt; concatenate parsed issues.
    """
    ensure_logging()
    client = _client()
    all_issues: list[dict[str, Any]] = []
    total = len(chunks)
    lang = language if language in prompts.VALID_LANGUAGES else prompts.LANG_EN
    system_prompt = prompts.build_system_prompt(lang)
    logger.info(
        "LLM: model=%s base_url=%s chunk_count=%s mode=%s language=%s",
        settings.MODEL_NAME,
        settings.OPENAI_BASE_URL or "(default OpenAI)",
        total,
        mode,
        lang,
    )
    for i, chunk in enumerate(chunks):
        if not chunk.strip():
            logger.info("LLM: skipping empty chunk %s/%s", i + 1, total)
            continue
        user_content = prompts.build_user_prompt_full_document(
            chunk, mode, i, total, lang
        )
        logger.info(
            "LLM: calling API chunk %s/%s (%s chars) — waiting on the model (no output until the request finishes)…",
            i + 1,
            total,
            len(chunk),
        )
        t0 = time.perf_counter()
        resp = client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.2,
        )
        elapsed = time.perf_counter() - t0
        raw = resp.choices[0].message.content or "[]"
        parsed = normalize_model_output(raw)
        logger.info(
            "LLM: chunk %s/%s done in %.1fs → %s issue(s) parsed",
            i + 1,
            total,
            elapsed,
            len(parsed),
        )
        all_issues.extend(parsed)
    logger.info("LLM: total issues from all chunks: %s", len(all_issues))
    return all_issues
