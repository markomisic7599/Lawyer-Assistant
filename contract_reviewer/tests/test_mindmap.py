"""Tests for mind-map chunking and Mermaid/graph rendering (pure functions)."""

from __future__ import annotations

from contract_reviewer.docx_reader import DocumentStructure, ParagraphBlock
from contract_reviewer.mindmap_chunker import chunk_structure, is_heading
from contract_reviewer.mindmap_model import (
    MindMap,
    MindMapEdge,
    MindMapNode,
    mindmap_from_dict,
    render_mermaid,
)


def _structure(paragraphs: list[str]) -> DocumentStructure:
    blocks = [ParagraphBlock(paragraph_index=i, text=t, runs=[]) for i, t in enumerate(paragraphs)]
    return DocumentStructure(blocks=blocks, full_text="\n\n".join(paragraphs))


def test_is_heading_detects_articles() -> None:
    assert is_heading("Article 5")
    assert is_heading("Art. 135 L1")
    assert is_heading("Član 12")
    assert is_heading("3.2 Scope")
    assert not is_heading("This is an ordinary sentence about article requirements.")


def test_chunker_breaks_on_article_boundary() -> None:
    paragraphs = [
        "Article 1",
        "x" * 80,
        "Article 2",
        "y" * 80,
        "Article 3",
        "z" * 80,
    ]
    chunks = chunk_structure(_structure(paragraphs), max_chars=100, overlap_chars=0)
    assert len(chunks) >= 2
    # Each new chunk after the first should begin at an article heading.
    for chunk in chunks[1:]:
        assert chunk.text.lstrip().startswith("Article")


def test_chunker_single_chunk_when_small() -> None:
    chunks = chunk_structure(_structure(["Short doc.", "Two paragraphs."]), max_chars=10_000)
    assert len(chunks) == 1


def test_mindmap_from_dict_filters_invalid() -> None:
    data = {
        "title": "Permit process",
        "nodes": [
            {"id": "a", "label": "Apply", "type": "process", "article_refs": ["Art. 1 L1"]},
            {"id": "b", "label": "Ministry decides", "type": "decision"},
            {"id": "", "label": "no id"},  # dropped
            {"id": "a", "label": "dup id"},  # dropped
        ],
        "edges": [
            {"source": "a", "target": "b", "label": "30 days"},
            {"source": "a", "target": "missing"},  # dropped
        ],
    }
    mm = mindmap_from_dict(data)
    assert mm.title == "Permit process"
    assert {n.id for n in mm.nodes} == {"a", "b"}
    assert len(mm.edges) == 1
    assert mm.edges[0].label == "30 days"


def test_render_mermaid_shapes_and_escaping() -> None:
    mm = MindMap(
        title="Test",
        nodes=[
            MindMapNode(id="t", label="Process", type="title"),
            MindMapNode(id="d", label='Ministry "X"', type="decision", article_refs=["Art. 9 L3"]),
            MindMapNode(id="doc", label="EIA Study", type="document"),
            MindMapNode(id="o", label="Permit issued", type="outcome"),
        ],
        edges=[
            MindMapEdge(source="t", target="d"),
            MindMapEdge(source="d", target="doc", label="15 days"),
            MindMapEdge(source="doc", target="o"),
        ],
    )
    out = render_mermaid(mm)
    assert out.startswith("flowchart TD")
    assert "{{" in out  # hexagon document
    assert '{"Ministry &quot;X&quot;' in out  # diamond + escaped quotes
    assert '-- "15 days" -->' in out
    assert "class o outcome;" in out
