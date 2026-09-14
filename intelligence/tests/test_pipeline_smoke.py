"""Offline smoke tests for the Intelligence System (no network, no API key)."""

from __future__ import annotations

from pathlib import Path

from intelligence import pipeline as pipeline_mod
from intelligence.brief import render_brief
from intelligence.models import Contact, Opportunity, Radar, SourceItem, Stage
from intelligence.search import MockProvider
from intelligence.store import Store


def _opp(oid: str, title: str, score: int, radar: Radar = Radar.FIND) -> Opportunity:
    return Opportunity(
        id=oid,
        title=title,
        radar=radar,
        score=score,
        stage=Stage.QUALIFIED,
        why_now="Project reached ready-to-build; procurement starting.",
        target_org="Acme Energy",
        contact=Contact(role="Project Director", is_decision_maker=True),
        suggested_actions=["Send tailored email", "Find warm intro via bank"],
        source_url="https://example.com/a",
        source_title=title,
    )


def test_store_upsert_dedupe_and_stage(tmp_path: Path) -> None:
    store = Store(db_path=tmp_path / "p.db")
    o = _opp("abc123", "Big solar RTB", 82)
    stored, is_new = store.upsert(o)
    assert is_new is True and stored.stage == Stage.QUALIFIED

    # Human advances the stage.
    assert store.set_stage("abc123", Stage.CONTACTED)

    # Re-seeing the same item must NOT reset a human-managed stage.
    again, is_new2 = store.upsert(_opp("abc123", "Big solar RTB (updated)", 90))
    assert is_new2 is False
    assert again.stage == Stage.CONTACTED
    assert again.score == 90  # score refreshed

    assert len(store.list()) == 1
    assert store.list(stage=Stage.CONTACTED)[0].id == "abc123"


def test_render_brief_empty_and_populated() -> None:
    assert "nema ničega" in render_brief([])
    md = render_brief([_opp("x1", "Factory €150m", 88, Radar.FIND)])
    assert "Factory €150m" in md
    assert "WHO:" in md and "WHY NOW:" in md
    assert "Acme Energy" in md


def test_run_daily_offline(monkeypatch, tmp_path: Path) -> None:
    # Mock search returns one item per executed query.
    item = SourceItem(title="Investor reaches RTB", url="https://ex.com/1", snippet="...")
    provider = MockProvider()
    monkeypatch.setattr(provider, "search", lambda q, **k: [item])

    # Bypass the LLM: qualify anything deterministically.
    def fake_score(it: SourceItem) -> Opportunity:
        return _opp(it.fingerprint(), it.title, 75)

    monkeypatch.setattr(pipeline_mod, "score_item", fake_score)

    store = Store(db_path=tmp_path / "p.db")
    result = pipeline_mod.run_daily([Radar.FIND], store=store, provider=provider)

    assert result.qualified, "expected at least one qualified opportunity"
    assert result.new_count >= 1
    # Same item across many queries must dedupe to a single stored opportunity.
    assert len(store.list()) == 1
