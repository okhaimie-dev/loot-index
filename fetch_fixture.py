#!/usr/bin/env python3
"""Download the canonical verbose Loot fixture used to build the index.

Source: Provable-Games/stark-loot, tests/verbose_loot.json (all 8,000 bags).

Usage:
    python3 fetch_fixture.py
    python3 fetch_fixture.py --url <raw-url> --out data/verbose_loot.json
"""

from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_URL = (
    "https://raw.githubusercontent.com/Provable-Games/stark-loot/main/tests/verbose_loot.json"
)
DEFAULT_OUT = ROOT / "data" / "verbose_loot.json"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {args.url}")
    with urllib.request.urlopen(args.url, timeout=120) as response:
        payload = response.read()
    raw = json.loads(payload)
    if len(raw) != 8000:
        raise ValueError(f"expected 8,000 bags in fixture, found {len(raw)}")
    args.out.write_bytes(payload)
    print(f"Wrote {args.out} ({len(payload) / 1e6:.1f} MB, {len(raw):,} bags)")


if __name__ == "__main__":
    main()
