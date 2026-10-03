import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import score  # noqa: E402

TABLES = score.load_tables(ROOT / "data" / "tables.json")
FIXTURE_CANDIDATES = (ROOT / "data" / "verbose_loot.json", score.FALLBACK_FIXTURE)


def synthetic_bag(greatness_by_slot):
    item = {
        "current_name": "Pendant",
        "final_name": "Pendant",
        "item_name": "Pendant",
        "greatness": 0,
        "suffix": "of Power",
        "name_prefix": "Agony",
        "name_suffix": "Bane",
    }
    return {slot: {**item, "greatness": g} for slot, g in zip(score.SLOTS, greatness_by_slot)}


class TestTables(unittest.TestCase):
    def test_item_count_and_ids(self):
        items = TABLES["items"]
        self.assertEqual(len(items), 101)
        self.assertEqual({entry["id"] for entry in items.values()}, set(range(1, 102)))

    def test_known_item_metadata(self):
        self.assertEqual(
            TABLES["items"]["Grave Wand"],
            {"id": 10, "tier": 2, "slot": "weapon", "type": "Magic_or_Cloth"},
        )
        self.assertEqual(
            TABLES["items"]["Gold Ring"],
            {"id": 8, "tier": 1, "slot": "ring", "type": None},
        )

    def test_modifier_tables(self):
        self.assertEqual(TABLES["suffixes"]["of Skill"], 4)
        self.assertEqual(TABLES["name_prefixes"]["Grim"], 33)
        self.assertEqual(TABLES["name_suffixes"]["Shout"], 12)


class TestScoring(unittest.TestCase):
    def test_score_bag_fields(self):
        bag = score.score_bag(7, synthetic_bag([20] * 8), TABLES)
        self.assertEqual(bag["greatness_sum"], 160)
        self.assertEqual(bag["plus_one_count"], 8)
        self.assertEqual(bag["named_count"], 8)
        self.assertEqual(bag["tier_score"], 40)  # Pendant is T1: 8 * (6 - 1)
        self.assertEqual(bag["items"]["weapon"]["id"], 1)

    def test_rank_and_ties(self):
        bags = [
            score.score_bag(1, synthetic_bag([20] * 8), TABLES),
            score.score_bag(2, synthetic_bag([0] * 8), TABLES),
            score.score_bag(3, synthetic_bag([0] * 8), TABLES),
        ]
        score.rank_bags(bags)
        best, tied_a, tied_b = bags
        self.assertEqual((best["rank"], best["top_pct"]), (1, 0.0))
        self.assertEqual((tied_a["rank"], tied_a["tied_count"]), (2, 2))
        self.assertEqual((tied_b["rank"], tied_b["tied_count"]), (2, 2))
        self.assertAlmostEqual(tied_a["top_pct"], 100 / 3, places=1)

    def test_item_percentiles(self):
        bags = [
            score.score_bag(1, synthetic_bag([20] * 8), TABLES),
            score.score_bag(2, synthetic_bag([0] * 8), TABLES),
        ]
        score.annotate_items(bags)
        self.assertEqual(bags[0]["items"]["weapon"]["greatness_top_pct"], 0.0)
        self.assertEqual(bags[1]["items"]["weapon"]["greatness_top_pct"], 50.0)


def fixture_available():
    return any(path.is_file() for path in FIXTURE_CANDIDATES)


class TestCanonicalFixture(unittest.TestCase):
    @unittest.skipUnless(fixture_available(), "canonical fixture not downloaded")
    def test_all_8000_bags(self):
        fixture = score.resolve_fixture(None)
        bags = score.score_fixture(score.load_fixture(fixture), TABLES)
        score.rank_bags(bags)
        by_id = {bag["id"]: bag for bag in bags}
        self.assertEqual(len(bags), 8000)
        self.assertEqual(by_id[2797]["rank"], 1)
        self.assertEqual(by_id[2797]["greatness_sum"], 140)
        self.assertEqual(by_id[1]["rank"], 1933)
        self.assertEqual(by_id[1]["greatness_sum"], 92)
        self.assertEqual(min(b["greatness_sum"] for b in bags), 22)
        self.assertEqual(max(b["greatness_sum"] for b in bags), 140)


if __name__ == "__main__":
    unittest.main()
