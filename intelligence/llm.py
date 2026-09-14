"""Thin OpenAI wrapper for the Intelligence System (JSON-in/JSON-out)."""

from __future__ import annotations

import json
import re
from typing import Any

from openai import OpenAI

from . import config

_client: OpenAI | None = None


def client() -> OpenAI:
    global _client
    if _client is None:
        if not config.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not set (needed for scoring).")
        kwargs: dict[str, Any] = {"api_key": config.OPENAI_API_KEY}
        if config.OPENAI_BASE_URL:
            kwargs["base_url"] = config.OPENAI_BASE_URL
        _client = OpenAI(**kwargs)
    return _client


def parse_json_object(raw: str) -> dict[str, Any]:
    """Parse a JSON object from model output, tolerating ```json fences."""
    text = (raw or "").strip()
    fence = re.match(r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", text, re.DOTALL | re.IGNORECASE)
    if fence:
        text = fence.group(1).strip()
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object")
    return data


def chat_json(system_prompt: str, user_prompt: str, *, temperature: float = 0.2) -> dict[str, Any]:
    """Call the model and return a parsed JSON object (empty dict on failure)."""
    resp = client().chat.completions.create(
        model=config.MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        response_format={"type": "json_object"},
    )
    raw = resp.choices[0].message.content or "{}"
    try:
        return parse_json_object(raw)
    except (json.JSONDecodeError, ValueError):
        return {}
