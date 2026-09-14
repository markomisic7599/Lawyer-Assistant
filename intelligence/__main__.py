"""CLI: run the daily intelligence sweep and write/print the brief.

Usage (from repo root):
    python -m intelligence                 # all radars, print brief + save file
    python -m intelligence --radar STUCK_PROJECT --radar FIND
    python -m intelligence --pipeline      # just print the current stored pipeline
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date

from . import config
from .brief import render_brief
from .models import Radar, Stage
from .pipeline import run_daily
from .store import Store


def _force_utf8_stdout() -> None:
    """Serbian text (č, ž, đ…) breaks the default Windows cp1252 console."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
        except (AttributeError, ValueError):
            pass


def _configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.INFO if verbose else logging.WARNING,
        format="%(asctime)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Parivodic Intelligence System — daily sweep")
    parser.add_argument(
        "--radar",
        action="append",
        choices=[r.value for r in Radar],
        help="Limit to specific radar(s); repeatable. Default: all.",
    )
    parser.add_argument("--pipeline", action="store_true", help="Print stored pipeline and exit.")
    parser.add_argument("--quiet", action="store_true", help="Less logging.")
    args = parser.parse_args()
    _force_utf8_stdout()
    _configure_logging(not args.quiet)

    store = Store()

    if args.pipeline:
        print(f"# Pipeline — {config.DB_PATH}\n")
        for stage in Stage:
            opps = store.list(stage=stage)
            if not opps:
                continue
            print(f"## {stage.value} ({len(opps)})")
            for o in opps:
                print(f"  [{o.score}] {o.title} — {o.target_org}")
            print()
        return

    radars = [Radar(r) for r in args.radar] if args.radar else None
    result = run_daily(radars, store=store)

    brief_md = render_brief(result.qualified, when=date.today())
    config.BRIEF_DIR.mkdir(parents=True, exist_ok=True)
    out_path = config.BRIEF_DIR / f"brief_{date.today().isoformat()}.md"
    out_path.write_text(brief_md, encoding="utf-8")

    print(brief_md)
    print(
        f"\n---\nFetched {result.fetched} · qualified {len(result.qualified)} "
        f"({result.new_count} new) · saved {out_path}"
    )


if __name__ == "__main__":
    main()
