# The Loot Index

**Live:** https://okhaimie-dev.github.io/loot-index/

All 8,000 Loot bags ranked by **greatness** — the only stat the original contract actually
rolls. Static site, zero dependencies, no backend.

- **Look up any bag** — rank, percentile, every item, full hidden modifiers
- **Share cards** — a 1200×630 PNG per bag, generated in the browser
- **Verify on Starknet** — one call to `get_packed_bag` on the deployed stark_loot contract,
  40 fields compared against a client-side decoder built from the documented wire layout
- **Leaderboards** — greatest, most `+1`s, most named items, loadout tier score (beta)

## Quickstart

Requires Python 3.10+ and a modern browser. No npm, no build tooling, no frameworks.

```bash
python3 fetch_fixture.py      # once: downloads the canonical 17 MB fixture
python3 loot_tables.py        # regenerate ID/tier tables from the stark-loot Cairo source
python3 score.py              # writes data/bags.json + data/leaderboards.md
python3 build_site.py         # writes dist/
python3 -m http.server -d dist 8080
# open http://localhost:8080
```

`score.py` also discovers the fixture automatically at `../stark-loot/tests/verbose_loot.json`
if a sibling checkout exists.

## Why greatness

The Loot contract draws every base item and every modifier with `rand % length` — uniformly.
There are no rare items, so item-rarity rankings measure sampling noise. Greatness
(`rand % 21`) is the only per-item value that varies and stacks across all eight slots. The
headline ranking is the sum of the eight rolls.

Tie order: greatness sum, `+1` count, named count, max item, id. Bags with identical score
tuples share a rank; `top_pct` counts strictly better tuples only.

The full method, including why hidden modifiers make the rank final before a bag is revealed,
is rendered at `/about.html`.

## Repo layout

| Path | Purpose |
| --- | --- |
| `score.py` | Scores, ranks, and annotates all bags; `--card <id>` prints one |
| `loot_tables.py` | Parses numeric IDs, tiers, slots, types out of stark-loot's `src/core.cairo` |
| `fetch_fixture.py` | Downloads `tests/verbose_loot.json` from the stark-loot repo |
| `build_site.py` | Scores in memory and writes the deployable `dist/` |
| `site/` | The static site (HTML/CSS/ES modules, no bundler) |
| `tests/` | `python3 -m unittest discover -s tests` |
| `data/tables.json` | Generated ID/tier/slot/type tables (committed) |
| `data/leaderboards.md` | Generated, thread-ready top-20 boards (committed) |

Generated data (`bags.json`, the fixture, `dist/`) is gitignored.

## Deploy

```bash
python3 build_site.py
```

Then publish `dist/` to GitHub Pages, Vercel, Netlify, or any static host. The on-chain
verification feature calls the public Cartridge Starknet RPC from the browser; no keys or
environment variables are required.

## Roadmap

- **Dungeon Power score** — a second ranking from real Loot Survivor/dungeon stats and
  modifier effects, once the Loot Dungeon's bag mechanic is confirmed
- **Item boards** — best individual items per slot
- **Collections** — rank a wallet holding several bags
- **Open data** — the build output is plain JSON anyone can reuse

## License

MIT. Loot's original contract is in the public domain. This is an unofficial community
project, not affiliated with Loot, Provable Games, or Cartridge.
