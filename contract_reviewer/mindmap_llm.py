"""LLM calls that turn document chunks into a consolidated process mind map."""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

from . import mindmap_prompts, settings
from .llm_client import build_client
from .logging_setup import ensure_logging
from .mindmap_prompts import VALID_DETAIL, DETAIL_OVERVIEW

logger = logging.getLogger(__name__)


def _parse_json_object(raw: str) -> dict[str, Any]:
    """Parse a JSON object from model output, tolerating ```json fences."""
    text = raw.strip()
    fence = re.match(r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", text, re.DOTALL | re.IGNORECASE)
    if fence:
        text = fence.group(1).strip()
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("Model output must be a JSON object")
    return data


def _chat(system_prompt: str, user_prompt: str) -> str:
    client = build_client()
    resp = client.chat.completions.create(
        model=settings.MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content or "{}"


def extract_graph_from_chunk(
    chunk_text: str,
    detail: str,
    chunk_index: int,
    chunk_total: int,
    language: str,
) -> dict[str, Any]:
    """Extract a partial process graph from a single chunk."""
    system_prompt = mindmap_prompts.build_extraction_system_prompt(language)
    user_prompt = mindmap_prompts.build_extraction_user_prompt(
        chunk_text, detail, chunk_index, chunk_total, language
    )
    logger.info(
        "MindMap LLM: extracting chunk %s/%s (%s chars)…",
        chunk_index + 1,
        chunk_total,
        len(chunk_text),
    )
    t0 = time.perf_counter()
    raw = _chat(system_prompt, user_prompt)
    try:
        data = _parse_json_object(raw)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("MindMap LLM: chunk %s parse failed: %s", chunk_index + 1, exc)
        return {"title": "", "nodes": [], "edges": []}
    logger.info(
        "MindMap LLM: chunk %s/%s done in %.1fs → %s node(s)",
        chunk_index + 1,
        chunk_total,
        time.perf_counter() - t0,
        len(data.get("nodes", []) or []),
    )
    return data


def consolidate_graphs(
    partials: list[dict[str, Any]],
    detail: str,
    language: str,
) -> dict[str, Any]:
    """Merge per-chunk partial graphs into one coherent graph via the model."""
    system_prompt = mindmap_prompts.build_consolidation_system_prompt(language)
    user_prompt = mindmap_prompts.build_consolidation_user_prompt(
        json.dumps(partials, ensure_ascii=False), detail, language
    )
    logger.info("MindMap LLM: consolidating %s partial graph(s)…", len(partials))
    t0 = time.perf_counter()
    raw = _chat(system_prompt, user_prompt)
    data = _parse_json_object(raw)
    logger.info(
        "MindMap LLM: consolidation done in %.1fs → %s node(s)",
        time.perf_counter() - t0,
        len(data.get("nodes", []) or []),
    )
    return data


def merge_partials_fallback(partials: list[dict[str, Any]]) -> dict[str, Any]:
    """Programmatic merge used if LLM consolidation fails.

    Namespaces node ids per chunk to avoid collisions and concatenates nodes and
    edges. Produces a valid (if less polished) graph so the user still gets output.
    """
    title = ""
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    for i, partial in enumerate(partials):
        if not title and partial.get("title"):
            title = str(partial["title"])
        prefix = f"c{i}_"
        for node in partial.get("nodes", []) or []:
            if not isinstance(node, dict) or not node.get("id"):
                continue
            node = dict(node)
            node["id"] = prefix + str(node["id"])
            nodes.append(node)
        for edge in partial.get("edges", []) or []:
            if not isinstance(edge, dict):
                continue
            edge = dict(edge)
            edge["source"] = prefix + str(edge.get("source", ""))
            edge["target"] = prefix + str(edge.get("target", ""))
            edges.append(edge)
    return {"title": title or "Process", "nodes": nodes, "edges": edges}


def build_graph(
    chunks: list[str],
    detail: str,
    language: str,
) -> dict[str, Any]:
    """End-to-end model work: extract per chunk, then consolidate to one graph."""
    ensure_logging()
    detail = detail if detail in VALID_DETAIL else DETAIL_OVERVIEW
    total = len(chunks)
    partials: list[dict[str, Any]] = []
    for i, chunk in enumerate(chunks):
        if not chunk.strip():
            continue
        partials.append(extract_graph_from_chunk(chunk, detail, i, total, language))

    if not partials:
        return {"title": "Process", "nodes": [], "edges": []}
    if len(partials) == 1:
        return partials[0]

    try:
        return consolidate_graphs(partials, detail, language)
    except Exception as exc:  # noqa: BLE001 - fall back to a usable graph
        logger.warning("MindMap LLM: consolidation failed (%s); using fallback merge", exc)
        return merge_partials_fallback(partials)
