"""Mind-map data model + Mermaid/HTML rendering.

The visual target is the legal "process flowchart" the firm hand-draws: a
yellow process title, white rectangular steps annotated with article
references, hexagons for required input documents, green diamonds for
decision/authority gates, green filled boxes for outcomes, and arrows labelled
with time limits. We model that as a typed node/edge graph and render it to a
Mermaid ``flowchart`` because Mermaid produces exactly those shapes and can be
embedded in the app or exported as a standalone, printable HTML page.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any

# Node categories mapped to the shapes/colours seen in the reference diagrams.
NODE_TYPES: frozenset[str] = frozenset(
    {"title", "process", "decision", "document", "outcome", "start", "end"}
)
_DEFAULT_NODE_TYPE = "process"


@dataclass
class MindMapNode:
    id: str
    label: str
    type: str = _DEFAULT_NODE_TYPE
    article_refs: list[str] = field(default_factory=list)

    def normalized_type(self) -> str:
        return self.type if self.type in NODE_TYPES else _DEFAULT_NODE_TYPE


@dataclass
class MindMapEdge:
    source: str
    target: str
    label: str = ""


@dataclass
class MindMap:
    title: str
    nodes: list[MindMapNode] = field(default_factory=list)
    edges: list[MindMapEdge] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "nodes": [asdict(n) for n in self.nodes],
            "edges": [asdict(e) for e in self.edges],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


def mindmap_from_dict(data: dict[str, Any], *, default_title: str = "Process") -> MindMap:
    """Build a validated MindMap from loosely-typed model/JSON output."""
    title = str(data.get("title") or default_title).strip() or default_title
    nodes: list[MindMapNode] = []
    seen_ids: set[str] = set()
    for raw in data.get("nodes", []) or []:
        if not isinstance(raw, dict):
            continue
        node_id = str(raw.get("id", "")).strip()
        label = str(raw.get("label", "")).strip()
        if not node_id or not label or node_id in seen_ids:
            continue
        seen_ids.add(node_id)
        refs_raw = raw.get("article_refs") or []
        refs = [str(r).strip() for r in refs_raw if str(r).strip()] if isinstance(refs_raw, list) else []
        nodes.append(
            MindMapNode(
                id=node_id,
                label=label,
                type=str(raw.get("type", _DEFAULT_NODE_TYPE)).strip().lower(),
                article_refs=refs,
            )
        )
    edges: list[MindMapEdge] = []
    for raw in data.get("edges", []) or []:
        if not isinstance(raw, dict):
            continue
        source = str(raw.get("source", "")).strip()
        target = str(raw.get("target", "")).strip()
        if source in seen_ids and target in seen_ids:
            edges.append(
                MindMapEdge(source=source, target=target, label=str(raw.get("label", "")).strip())
            )
    return MindMap(title=title, nodes=nodes, edges=edges)


# --- Mermaid rendering -------------------------------------------------------

_SAFE_ID_RE = re.compile(r"[^A-Za-z0-9_]")


def _safe_node_id(node_id: str) -> str:
    """Mermaid node ids must be alphanumeric/underscore; namespace the rest."""
    cleaned = _SAFE_ID_RE.sub("_", node_id)
    if not cleaned or not cleaned[0].isalpha():
        cleaned = f"n_{cleaned}"
    return cleaned


def _escape_label(text: str) -> str:
    """Escape a label for use inside a Mermaid quoted node."""
    return text.replace("\\", "/").replace('"', "&quot;").replace("\n", " ").strip()


def _node_label(node: MindMapNode) -> str:
    parts = [_escape_label(node.label)]
    if node.article_refs:
        parts.append("<br/><i>" + _escape_label(", ".join(node.article_refs)) + "</i>")
    return "".join(parts)


def _wrap_shape(node_type: str, mermaid_id: str, label: str) -> str:
    """Wrap a label in the Mermaid shape syntax matching the node type."""
    if node_type == "decision":
        return f'{mermaid_id}{{"{label}"}}'
    if node_type == "document":
        return f'{mermaid_id}{{{{"{label}"}}}}'
    if node_type in {"start", "end"}:
        return f'{mermaid_id}(["{label}"])'
    if node_type == "title":
        return f'{mermaid_id}["{label}"]'
    return f'{mermaid_id}["{label}"]'


_CLASS_DEFS = (
    "classDef title fill:#f3d250,stroke:#c9a227,color:#7a1f1f,font-weight:bold;",
    "classDef process fill:#ffffff,stroke:#4a4a4a,color:#222222;",
    "classDef decision fill:#a7c83f,stroke:#6b8e23,color:#1c2b00;",
    "classDef document fill:#ffffff,stroke:#7a7a7a,color:#333333;",
    "classDef outcome fill:#3c9d6e,stroke:#2e7d54,color:#ffffff,font-weight:bold;",
    "classDef start fill:#e8eef7,stroke:#36588a,color:#10243f;",
    "classDef end fill:#e8eef7,stroke:#36588a,color:#10243f;",
)


def render_mermaid(mind_map: MindMap, *, direction: str = "TD") -> str:
    """Render the mind map to a Mermaid flowchart definition."""
    lines: list[str] = [f"flowchart {direction}"]
    lines.extend(f"    {cd}" for cd in _CLASS_DEFS)

    id_map: dict[str, str] = {}
    for node in mind_map.nodes:
        mermaid_id = _safe_node_id(node.id)
        # Guard against collisions after sanitising distinct ids.
        suffix = 1
        base = mermaid_id
        while mermaid_id in id_map.values():
            mermaid_id = f"{base}_{suffix}"
            suffix += 1
        id_map[node.id] = mermaid_id

    for node in mind_map.nodes:
        mermaid_id = id_map[node.id]
        node_type = node.normalized_type()
        shape = _wrap_shape(node_type, mermaid_id, _node_label(node))
        lines.append(f"    {shape}")
        lines.append(f"    class {mermaid_id} {node_type};")

    for edge in mind_map.edges:
        src = id_map.get(edge.source)
        dst = id_map.get(edge.target)
        if not src or not dst:
            continue
        if edge.label:
            lines.append(f'    {src} -- "{_escape_label(edge.label)}" --> {dst}')
        else:
            lines.append(f"    {src} --> {dst}")

    return "\n".join(lines)


# --- Standalone HTML ---------------------------------------------------------

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{title}</title>
<style>
  body {{ margin: 0; font-family: 'Segoe UI', Arial, sans-serif; background: #fafafa; color: #222; }}
  header {{ padding: 12px 20px; background: #f3d250; border-bottom: 2px solid #c9a227; }}
  header h1 {{ margin: 0; font-size: 18px; color: #7a1f1f; }}
  header p {{ margin: 4px 0 0; font-size: 12px; color: #555; }}
  #diagram {{ width: 100%; overflow: auto; padding: 16px; box-sizing: border-box; }}
  .mermaid {{ display: flex; justify-content: center; }}
  footer {{ padding: 8px 20px; font-size: 11px; color: #888; }}
</style>
</head>
<body>
<header>
  <h1>{title}</h1>
  <p>Process mind map generated from the source document. Scroll/zoom to explore. Use your browser's print to PDF to export.</p>
</header>
<div id="diagram">
  <pre class="mermaid">
{diagram}
  </pre>
</div>
<footer>Generated by Lawyer Assistant &middot; Mermaid flowchart</footer>
<script type="module">
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
  mermaid.initialize({{ startOnLoad: true, securityLevel: 'loose', flowchart: {{ useMaxWidth: false, htmlLabels: true }} }});
</script>
</body>
</html>
"""


def render_html(mind_map: MindMap, *, direction: str = "TD") -> str:
    """Render a self-contained HTML page that draws the Mermaid diagram."""
    diagram = render_mermaid(mind_map, direction=direction)
    safe_title = _escape_label(mind_map.title) or "Process mind map"
    return _HTML_TEMPLATE.format(title=safe_title, diagram=diagram)


def render_iframe(mind_map: MindMap, *, direction: str = "TD", height: int = 720) -> str:
    """Render an iframe (srcdoc) that embeds the standalone HTML.

    Using an iframe lets the Mermaid script run reliably inside Gradio's HTML
    component, isolated from the host page's CSP/sanitisation.
    """
    doc = render_html(mind_map, direction=direction).replace('"', "&quot;")
    return (
        f'<iframe srcdoc="{doc}" '
        f'style="width:100%;height:{height}px;border:1px solid #ddd;border-radius:8px;background:#fff;" '
        f'sandbox="allow-scripts"></iframe>'
    )
