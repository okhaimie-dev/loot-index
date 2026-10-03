#!/usr/bin/env python3
"""Generate data/tables.json from the stark-loot Cairo source.

Parses the canonical name/ID match tables out of src/core.cairo so the scorer
can attach numeric IDs (needed for on-chain verification) and tier/type/slot
metadata without duplicating the lists by hand.

Usage:
    python3 loot_tables.py --source ../stark-loot/src/core.cairo
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_SOURCE = ROOT.parent / "stark-loot" / "src" / "core.cairo"
DEFAULT_OUT = ROOT / "data" / "tables.json"


def block(text: str, start: str, end: str) -> str:
    begin = text.index(start)
    finish = text.index(end, begin)
    return text[begin:finish]


def string_pairs(chunk: str) -> dict[int, str]:
    pattern = r'(\d+)\s*=>\s*"((?:[^"\\]|\\.)*)"'
    return {int(m.group(1)): m.group(2) for m in re.finditer(pattern, chunk)}


def tier_pairs(chunk: str) -> dict[int, int]:
    pattern = r"(\d+)\s*=>\s*Tier::T(\d)"
    return {int(m.group(1)): int(m.group(2)) for m in re.finditer(pattern, chunk)}


def slot_for(item_id: int) -> str:
    if 1 <= item_id <= 3:
        return "neck"
    if 4 <= item_id <= 8:
        return "ring"
    if 9 <= item_id <= 16 or 42 <= item_id <= 46 or 72 <= item_id <= 76:
        return "weapon"
    if 17 <= item_id <= 21 or 47 <= item_id <= 51 or 77 <= item_id <= 81:
        return "chest"
    if 22 <= item_id <= 26 or 52 <= item_id <= 56 or 82 <= item_id <= 86:
        return "head"
    if 27 <= item_id <= 31 or 57 <= item_id <= 61 or 87 <= item_id <= 91:
        return "waist"
    if 32 <= item_id <= 36 or 62 <= item_id <= 66 or 92 <= item_id <= 96:
        return "foot"
    if 37 <= item_id <= 41 or 67 <= item_id <= 71 or 97 <= item_id <= 101:
        return "hand"
    raise ValueError(f"no slot for item id {item_id}")


def type_for(item_id: int) -> str | None:
    if 9 <= item_id <= 41:
        return "Magic_or_Cloth"
    if 42 <= item_id <= 71:
        return "Blade_or_Hide"
    if 72 <= item_id <= 101:
        return "Bludgeon_or_Metal"
    return None  # necklaces and rings have no combat type


def build(source: Path) -> dict:
    text = source.read_text()
    item_names = string_pairs(block(text, "pub fn get_item_name", "pub fn render_item_name"))
    tiers = tier_pairs(block(text, "pub fn get_tier", "pub fn get_slot"))
    suffixes = string_pairs(block(text, "pub fn suffix_name_by_id", "pub fn name_prefix_by_id"))
    prefixes = string_pairs(block(text, "pub fn name_prefix_by_id", "pub fn name_suffix_by_id"))
    name_suffixes = string_pairs(block(text, "pub fn name_suffix_by_id", "pub fn get_item_name"))

    if len(item_names) != 101:
        raise ValueError(f"expected 101 items, parsed {len(item_names)}")
    if len(tiers) != 101:
        raise ValueError(f"expected 101 tiers, parsed {len(tiers)}")
    if len(suffixes) != 16 or len(prefixes) != 69 or len(name_suffixes) != 18:
        raise ValueError("modifier table sizes are wrong")

    items = {}
    for item_id, name in item_names.items():
        if name in items:
            raise ValueError(f"duplicate item name {name!r}")
        items[name] = {
            "id": item_id,
            "tier": tiers[item_id],
            "slot": slot_for(item_id),
            "type": type_for(item_id),
        }

    return {
        "generated_from": str(source),
        "items": dict(sorted(items.items(), key=lambda kv: kv[1]["id"])),
        "suffixes": dict(sorted(((name, i) for i, name in suffixes.items()), key=lambda kv: kv[1])),
        "name_prefixes": dict(
            sorted(((name, i) for i, name in prefixes.items()), key=lambda kv: kv[1])
        ),
        "name_suffixes": dict(
            sorted(((name, i) for i, name in name_suffixes.items()), key=lambda kv: kv[1])
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    tables = build(args.source)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(tables, indent=1) + "\n")
    print(f"Wrote {args.out} ({len(tables['items'])} items, {len(tables['name_prefixes'])} prefixes)")


if __name__ == "__main__":
    main()
