#!/usr/bin/env python3
"""The Loot Index - score and rank all 8,000 Loot bags.

Methodology
===========
The original Loot contract draws every base item and every modifier uniformly
(rand % length). Item identity and modifier identity therefore carry no
scarcity signal: the only per-item value that varies and stacks is greatness
(rand % 21). The headline ranking is the sum of the eight greatness rolls.

Each item is enriched with its numeric ID, tier, slot, and combat type from
data/tables.json (regenerated from the stark-loot Cairo source by
loot_tables.py). Numeric IDs make on-chain verification against the deployed
stark_loot contract possible.

Secondary signals recorded per bag:
    plus_one_count   items at greatness 20 (full name + "+1")
    named_count      items at greatness >= 19 (quoted prefix/suffix name)
    revealed_count   items at greatness > 14 (suffix "of X" visible)
    max_greatness    best single item
    tier_score       sum of (6 - tier) over all eight items; a transparent
                     "loadout tier quality" proxy, not official game power

Tie order: greatness_sum, plus_one_count, named_count, max_greatness, id.
`top_pct` counts strictly better score tuples only, so true ties share the
same rank and percentile.

Usage:
    python3 score.py
    python3 score.py --card 2797
    python3 score.py --fixture data/verbose_loot.json --out data/bags.json
"""

from __future__ import annotations

import argparse
import bisect
import json
from collections import Counter
from pathlib import Path

SLOTS = ("weapon", "chest", "head", "waist", "foot", "hand", "neck", "ring")
ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / "data" / "verbose_loot.json"
FALLBACK_FIXTURE = ROOT.parent / "stark-loot" / "tests" / "verbose_loot.json"
DEFAULT_TABLES = ROOT / "data" / "tables.json"
DEFAULT_OUT = ROOT / "data" / "bags.json"
DEFAULT_LEADERBOARDS = ROOT / "data" / "leaderboards.md"


def resolve_fixture(explicit: Path | None) -> Path:
    candidates = [explicit] if explicit else [DEFAULT_FIXTURE, FALLBACK_FIXTURE]
    for candidate in candidates:
        if candidate and candidate.is_file():
            return candidate
    raise FileNotFoundError(
        "verbose_loot.json not found. Run `python3 fetch_fixture.py` or pass --fixture."
    )


def load_tables(path: Path = DEFAULT_TABLES) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"{path} missing. Run `python3 loot_tables.py` first.")
    return json.loads(path.read_text())


def load_fixture(path: Path) -> dict:
    raw = json.loads(path.read_text())
    if len(raw) != 8000:
        raise ValueError(f"expected 8,000 bags, found {len(raw)}")
    for slot in SLOTS:
        if slot not in next(iter(raw.values())):
            raise ValueError(f"fixture is missing slot {slot!r}")
    return raw


def modifier_id(table: dict, name: str, label: str) -> int | None:
    if not name:
        return None
    value = table.get(name)
    if value is None:
        raise ValueError(f"unknown {label} in fixture: {name!r}")
    return value


def enrich_item(item: dict, tables: dict) -> dict:
    entry = tables["items"].get(item["item_name"])
    if entry is None:
        raise ValueError(f"unknown item name in fixture: {item['item_name']!r}")
    enriched = dict(item)
    enriched.update(
        id=entry["id"],
        tier=entry["tier"],
        slot=entry["slot"],
        type=entry["type"],
        suffix_id=modifier_id(tables["suffixes"], item["suffix"], "suffix"),
        name_prefix_id=modifier_id(tables["name_prefixes"], item["name_prefix"], "name prefix"),
        name_suffix_id=modifier_id(
            tables["name_suffixes"], item["name_suffix"], "name suffix"
        ),
    )
    return enriched


def score_bag(bag_id: int, raw_bag: dict, tables: dict) -> dict:
    items = {slot: enrich_item(raw_bag[slot], tables) for slot in SLOTS}
    greatness = [items[slot]["greatness"] for slot in SLOTS]
    tier_score = sum(6 - items[slot]["tier"] for slot in SLOTS)
    return {
        "id": bag_id,
        "greatness_sum": sum(greatness),
        "max_greatness": max(greatness),
        "plus_one_count": sum(1 for g in greatness if g == 20),
        "named_count": sum(1 for g in greatness if g >= 19),
        "revealed_count": sum(1 for g in greatness if g > 14),
        "tier_score": tier_score,
        "items": items,
    }


def score_fixture(raw: dict, tables: dict) -> list[dict]:
    return [score_bag(int(bag_id), raw[bag_id], tables) for bag_id in raw]


def score_tuple(bag: dict) -> tuple:
    return (
        bag["greatness_sum"],
        bag["plus_one_count"],
        bag["named_count"],
        bag["max_greatness"],
    )


def band_label(top_pct: float) -> str:
    for limit, label in (
        (0.1, "Top 0.1%"),
        (1, "Top 1%"),
        (5, "Top 5%"),
        (10, "Top 10%"),
        (25, "Top 25%"),
        (50, "Top 50%"),
    ):
        if top_pct <= limit:
            return label
    return "Bottom 50%"


def rank_bags(bags: list[dict]) -> None:
    """Attach rank, top_pct, band and tied_count in place."""
    n = len(bags)
    ascending = sorted(score_tuple(bag) for bag in bags)
    for bag in bags:
        t = score_tuple(bag)
        better = n - bisect.bisect_right(ascending, t)
        equal = bisect.bisect_right(ascending, t) - bisect.bisect_left(ascending, t)
        bag["rank"] = better + 1
        bag["tied_count"] = equal
        bag["top_pct"] = round(100 * better / n, 2)
        bag["band"] = band_label(bag["top_pct"])


def annotate_items(bags: list[dict]) -> None:
    """Attach each item's greatness percentile across all 64,000 items."""
    all_greatness = sorted(
        bag["items"][slot]["greatness"] for bag in bags for slot in SLOTS
    )
    total = len(all_greatness)
    for bag in bags:
        for slot in SLOTS:
            item = bag["items"][slot]
            greater = total - bisect.bisect_right(all_greatness, item["greatness"])
            item["greatness_top_pct"] = round(100 * greater / total, 2)


def build_summary(bags: list[dict]) -> dict:
    sums = [bag["greatness_sum"] for bag in bags]
    ordered = sorted(
        bags,
        key=lambda b: (
            -b["greatness_sum"],
            -b["plus_one_count"],
            -b["named_count"],
            -b["max_greatness"],
            b["id"],
        ),
    )
    by_plus_ones = sorted(
        bags, key=lambda b: (-b["plus_one_count"], -b["greatness_sum"], b["id"])
    )
    by_named = sorted(bags, key=lambda b: (-b["named_count"], -b["greatness_sum"], b["id"]))
    by_tier = sorted(bags, key=lambda b: (-b["tier_score"], -b["greatness_sum"], b["id"]))
    bands = Counter(bag["band"] for bag in bags)

    def row(bag: dict) -> dict:
        return {
            "id": bag["id"],
            "greatness_sum": bag["greatness_sum"],
            "plus_one_count": bag["plus_one_count"],
            "named_count": bag["named_count"],
            "tier_score": bag["tier_score"],
            "rank": bag["rank"],
            "top_pct": bag["top_pct"],
        }

    return {
        "greatness_sum": {
            "min": min(sums),
            "max": max(sums),
            "mean": round(sum(sums) / len(sums), 2),
            "median": sorted(sums)[len(sums) // 2],
        },
        "histogram": {str(k): v for k, v in sorted(Counter(sums).items())},
        "bands": dict(bands),
        "top_greatness": [row(b) for b in ordered[:20]],
        "top_plus_ones": [row(b) for b in by_plus_ones[:20]],
        "top_named": [row(b) for b in by_named[:20]],
        "top_tier": [row(b) for b in by_tier[:20]],
    }


def write_leaderboards(summary: dict, path: Path) -> None:
    def table(rows: list[dict]) -> str:
        lines = [
            "| Rank | Bag | Greatness | +1s | Named | Tier score | Top % |",
            "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
        for r in rows:
            lines.append(
                f"| {r['rank']} | [{r['id']}](https://opensea.io/assets/ethereum/"
                f"0xFF9C1b15B16263C61d017ee9F65C50e4AE0113D7/{r['id']}) | "
                f"{r['greatness_sum']} | {r['plus_one_count']} | {r['named_count']} | "
                f"{r['tier_score']} | {r['top_pct']}% |"
            )
        return "\n".join(lines)

    lines = [
        "# The Loot Index - leaderboards",
        "",
        "Generated by `score.py` from the canonical verbose fixture (all 8,000 bags).",
        "Ranking: sum of the eight greatness rolls; ties share a rank.",
        "",
        "## Top 20 by greatness",
        "",
        table(summary["top_greatness"]),
        "",
        "## Most `+1` items",
        "",
        table(summary["top_plus_ones"]),
        "",
        "## Most named items (greatness >= 19)",
        "",
        table(summary["top_named"]),
        "",
        "## Highest loadout tier score (beta proxy, not official game power)",
        "",
        table(summary["top_tier"]),
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def print_card(bags: list[dict], bag_id: int) -> None:
    bag = next(b for b in bags if b["id"] == bag_id)
    print(
        f"Bag #{bag['id']}  rank #{bag['rank']} of 8,000  "
        f"({bag['band']}, top {bag['top_pct']}%, tied with {bag['tied_count']})"
    )
    print(
        f"Greatness {bag['greatness_sum']}  |  {bag['plus_one_count']}x +1  |  "
        f"{bag['named_count']} named  |  {bag['revealed_count']} revealed  |  "
        f"max {bag['max_greatness']}  |  tier score {bag['tier_score']}"
    )
    for slot in SLOTS:
        item = bag["items"][slot]
        marker = (
            " +1" if item["greatness"] == 20 else (" named" if item["greatness"] >= 19 else "")
        )
        print(
            f"  {slot:>6}  {item['item_name']:<22} id {item['id']:>3}  "
            f"T{item['tier']}  greatness {item['greatness']:>2}{marker}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--tables", type=Path, default=DEFAULT_TABLES)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--leaderboards", type=Path, default=DEFAULT_LEADERBOARDS)
    parser.add_argument("--card", type=int, help="print one bag's card and exit")
    args = parser.parse_args()

    fixture = resolve_fixture(args.fixture)
    tables = load_tables(args.tables)
    raw = load_fixture(fixture)
    bags = score_fixture(raw, tables)
    rank_bags(bags)
    annotate_items(bags)
    summary = build_summary(bags)

    if args.card is not None:
        print_card(bags, args.card)
        return

    payload = {
        "meta": {
            "generated_from": str(fixture),
            "bag_count": len(bags),
            "method": "greatness sum; uniform items/modifiers carry no rarity signal",
            "version": 2,
        },
        "summary": summary,
        "bags": sorted(bags, key=lambda b: b["id"]),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=1) + "\n")
    write_leaderboards(summary, args.leaderboards)

    sums = summary["greatness_sum"]
    print(f"Scored {len(bags):,} bags from {fixture}")
    print(
        f"Greatness sum: min {sums['min']}, median {sums['median']}, "
        f"mean {sums['mean']}, max {sums['max']}"
    )
    print(f"Wrote {args.out} and {args.leaderboards}")
    print()
    print("Top 5 by greatness:")
    for r in summary["top_greatness"][:5]:
        print(
            f"  bag {r['id']:>4}  greatness {r['greatness_sum']:>3}  "
            f"+1s {r['plus_one_count']}  named {r['named_count']}  tier {r['tier_score']}"
        )
    print()
    print_card(bags, summary["top_greatness"][0]["id"])


if __name__ == "__main__":
    main()
