#!/usr/bin/env python3
"""Build the static Loot Index site into dist/.

Reads the canonical fixture, scores all 8,000 bags in memory, then writes:
    dist/                   site files from site/
    dist/data/index.json    compact lookup/leaderboard index (all bags)
    dist/data/stats.json    summary statistics
    dist/data/bag/{id}.json one full record per bag

Usage:
    python3 build_site.py
    python3 build_site.py --out dist --fixture data/verbose_loot.json
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import score

ROOT = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT / "dist"
INDEX_FIELDS = (
    "id",
    "greatness_sum",
    "rank",
    "top_pct",
    "plus_one_count",
    "named_count",
    "max_greatness",
    "tied_count",
    "tier_score",
)


def write_compact(path: Path, payload) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, separators=(",", ":"))
    path.write_text(text)
    return len(text)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--tables", type=Path, default=score.DEFAULT_TABLES)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    fixture = score.resolve_fixture(args.fixture)
    tables = score.load_tables(args.tables)
    raw = score.load_fixture(fixture)
    print(f"Scoring {len(raw):,} bags from {fixture}")
    bags = score.score_fixture(raw, tables)
    score.rank_bags(bags)
    score.annotate_items(bags)
    summary = score.build_summary(bags)

    out = args.out
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    # Site assets.
    shutil.copytree(ROOT / "site", out, dirs_exist_ok=True)

    # Compact lookup index: parallel arrays keep the payload small.
    ordered = sorted(bags, key=lambda b: b["id"])
    index_rows = [[bag[field] for field in INDEX_FIELDS] for bag in ordered]
    size = write_compact(out / "data" / "index.json", {"fields": INDEX_FIELDS, "bags": index_rows})

    # Summary statistics for the landing page and histogram.
    size += write_compact(
        out / "data" / "stats.json",
        {
            "meta": {
                "generated_from": str(fixture),
                "bag_count": len(bags),
                "method": "greatness sum; uniform items/modifiers carry no rarity signal",
                "version": 2,
            },
            "summary": summary,
        },
    )

    # One file per bag for detail pages.
    bag_dir = out / "data" / "bag"
    bag_dir.mkdir(parents=True)
    for bag in ordered:
        size += write_compact(bag_dir / f"{bag['id']}.json", bag)

    leaderboards = ROOT / "data" / "leaderboards.md"
    if leaderboards.is_file():
        shutil.copy2(leaderboards, out / "data" / "leaderboards.md")

    total_mb = sum(f.stat().st_size for f in out.rglob("*") if f.is_file()) / 1e6
    print(f"Wrote {out}/ ({len(ordered):,} bag files, {size / 1e6:.1f} MB of json, {total_mb:.1f} MB total)")
    print("Preview: python3 -m http.server -d dist 8080")


if __name__ == "__main__":
    main()
