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
    """Build a Mermaid-safe node id.

    Always namespaced with ``n_`` so ids can never collide with Mermaid
    reserved keywords (e.g. ``end``, ``graph``, ``subgraph``, ``class``) or
    start with a non-alphabetic character.
    """
    return "n_" + _SAFE_ID_RE.sub("_", node_id)


def _css_class(node_type: str) -> str:
    """CSS class name for a node type, prefixed to avoid reserved keywords.

    Mermaid reserves words like ``end`` and treats ``start``/``end`` specially,
    so bare ``classDef end`` / ``class x end`` break the parser.
    """
    return f"mm_{node_type}"


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
    "classDef mm_title fill:#f3d250,stroke:#c9a227,color:#7a1f1f,font-weight:bold;",
    "classDef mm_process fill:#ffffff,stroke:#4a4a4a,color:#222222;",
    "classDef mm_decision fill:#a7c83f,stroke:#6b8e23,color:#1c2b00;",
    "classDef mm_document fill:#ffffff,stroke:#7a7a7a,color:#333333;",
    "classDef mm_outcome fill:#3c9d6e,stroke:#2e7d54,color:#ffffff,font-weight:bold;",
    "classDef mm_start fill:#e8eef7,stroke:#36588a,color:#10243f;",
    "classDef mm_end fill:#e8eef7,stroke:#36588a,color:#10243f;",
)


def _build_id_map(mind_map: MindMap) -> dict[str, str]:
    """Map each node id to a unique, syntax-safe id (shared by Mermaid/DOT)."""
    id_map: dict[str, str] = {}
    for node in mind_map.nodes:
        safe_id = _safe_node_id(node.id)
        # Guard against collisions after sanitising distinct ids.
        suffix = 1
        base = safe_id
        while safe_id in id_map.values():
            safe_id = f"{base}_{suffix}"
            suffix += 1
        id_map[node.id] = safe_id
    return id_map


def render_mermaid(mind_map: MindMap, *, direction: str = "TD") -> str:
    """Render the mind map to a Mermaid flowchart definition."""
    lines: list[str] = [f"flowchart {direction}"]
    lines.extend(f"    {cd}" for cd in _CLASS_DEFS)

    id_map = _build_id_map(mind_map)

    for node in mind_map.nodes:
        mermaid_id = id_map[node.id]
        node_type = node.normalized_type()
        shape = _wrap_shape(node_type, mermaid_id, _node_label(node))
        lines.append(f"    {shape}")
        lines.append(f"    class {mermaid_id} {_css_class(node_type)};")

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


# --- Graphviz DOT rendering --------------------------------------------------
#
# DOT is rendered to a flat SVG/PNG (via the ``dot`` engine) so a colleague can
# open the diagram in any browser or image viewer with no internet connection
# and no Mermaid/JS runtime. The shape/colour mapping mirrors the Mermaid one
# so both exports look like the same hand-drawn process flowchart.

# shape + fill/stroke/font per node type; ``rounded`` gives start/end a stadium look.
_DOT_STYLES: dict[str, dict[str, Any]] = {
    "title": {"shape": "box", "fill": "#f3d250", "stroke": "#c9a227", "font": "#7a1f1f", "bold": True},
    "process": {"shape": "box", "fill": "#ffffff", "stroke": "#4a4a4a", "font": "#222222", "bold": False},
    "decision": {"shape": "diamond", "fill": "#a7c83f", "stroke": "#6b8e23", "font": "#1c2b00", "bold": False},
    "document": {"shape": "hexagon", "fill": "#ffffff", "stroke": "#7a7a7a", "font": "#333333", "bold": False},
    "outcome": {"shape": "box", "fill": "#3c9d6e", "stroke": "#2e7d54", "font": "#ffffff", "bold": True},
    "start": {"shape": "box", "fill": "#e8eef7", "stroke": "#36588a", "font": "#10243f", "bold": False, "rounded": True},
    "end": {"shape": "box", "fill": "#e8eef7", "stroke": "#36588a", "font": "#10243f", "bold": False, "rounded": True},
}


def _dot_html_escape(text: str) -> str:
    """Escape text for a DOT HTML-like label (``label=<...>``)."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", " ")
        .strip()
    )


def _dot_quote(text: str) -> str:
    """Escape text for a double-quoted DOT string (edge labels)."""
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").strip()


def _dot_node_label(node: MindMapNode, style: dict[str, Any]) -> str:
    """HTML-like label: bold/plain title plus an italic line of article refs."""
    main = _dot_html_escape(node.label)
    if style.get("bold"):
        main = f"<B>{main}</B>"
    parts = [main]
    if node.article_refs:
        refs = _dot_html_escape(", ".join(node.article_refs))
        parts.append(f'<BR/><FONT POINT-SIZE="10"><I>{refs}</I></FONT>')
    return "<" + "".join(parts) + ">"


def render_dot(mind_map: MindMap, *, direction: str = "TD") -> str:
    """Render the mind map to a Graphviz DOT digraph definition."""
    rankdir = "LR" if str(direction).upper() == "LR" else "TB"
    id_map = _build_id_map(mind_map)
    title = _dot_html_escape(mind_map.title) or "Process mind map"

    lines: list[str] = [
        "digraph mindmap {",
        f"    rankdir={rankdir};",
        '    bgcolor="#ffffff";',
        f'    labelloc="t"; label=<<B>{title}</B>>; fontname="Helvetica"; fontsize="16";',
        '    node [fontname="Helvetica", fontsize="12", style="filled", penwidth="1.5"];',
        '    edge [fontname="Helvetica", fontsize="10", color="#555555"];',
    ]

    for node in mind_map.nodes:
        node_id = id_map[node.id]
        style = _DOT_STYLES.get(node.normalized_type(), _DOT_STYLES[_DEFAULT_NODE_TYPE])
        shape_style = "filled,rounded" if style.get("rounded") else "filled"
        lines.append(
            f"    {node_id} ["
            f"label={_dot_node_label(node, style)}, "
            f'shape={style["shape"]}, style="{shape_style}", '
            f'fillcolor="{style["fill"]}", color="{style["stroke"]}", '
            f'fontcolor="{style["font"]}"];'
        )

    for edge in mind_map.edges:
        src = id_map.get(edge.source)
        dst = id_map.get(edge.target)
        if not src or not dst:
            continue
        if edge.label:
            lines.append(f'    {src} -> {dst} [label="{_dot_quote(edge.label)}"];')
        else:
            lines.append(f"    {src} -> {dst};")

    lines.append("}")
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
  mermaid.initialize({{ startOnLoad: true, securityLevel: 'loose', maxEdges: 5000, maxTextSize: 5000000, flowchart: {{ useMaxWidth: false, htmlLabels: true }} }});
</script>
</body>
</html>
"""


def render_html(mind_map: MindMap, *, direction: str = "TD") -> str:
    """Render a self-contained HTML page that draws the Mermaid diagram."""
    diagram = render_mermaid(mind_map, direction=direction)
    safe_title = _escape_label(mind_map.title) or "Process mind map"
    return _HTML_TEMPLATE.format(title=safe_title, diagram=diagram)


def _html_escape(text: str) -> str:
    """Escape so Mermaid source survives as literal text inside <pre>.

    Gradio's HTML component sanitises its value, so we cannot rely on inline
    scripts or iframe srcdoc. Instead we emit a plain ``<pre class="mermaid">``
    (which survives sanitisation) and let a page-level Mermaid script render it.
    The diagram source is HTML-escaped so tags inside node labels (e.g. <br/>)
    stay as text and are not collapsed by the sanitiser.
    """
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_preview_html(mind_map: MindMap, *, direction: str = "TD") -> str:
    """Render a sanitisation-safe HTML snippet for the in-app Gradio preview.

    Requires the Mermaid loader injected into the page <head> (see app.py),
    which exposes ``window.__mermaidRun`` to process ``.mermaid`` blocks.
    """
    diagram = _html_escape(render_mermaid(mind_map, direction=direction))
    return (
        '<div style="overflow:auto;max-height:75vh;border:1px solid #e5e5e5;'
        'border-radius:8px;background:#fff;padding:12px;">'
        f'<pre class="mermaid" style="background:#fff;border:none;margin:0;">{diagram}</pre>'
        "</div>"
    )
