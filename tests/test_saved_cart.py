"""Offline regression tests for the complete saved clothing cart."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from src.saved_cart import SavedCartError, load_saved_cart, saved_cart_issues


class SavedCartTests(unittest.TestCase):
    def setUp(self):
        self.saved = load_saved_cart()

    def validate_modified(self, mutate):
        saved = copy.deepcopy(self.saved)
        mutate(saved)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for key, filename in (("cart", "cart.json"), ("matches", "amazon_asin_matches.json"), ("deployment", "amazon-shopping-cart-deployment.json")):
                (root / filename).write_text(json.dumps(saved[key]), encoding="utf-8")
            return load_saved_cart(root)

    def test_all_23_rows_retained(self):
        expected = {f"CART-{index:03d}" for index in range(1, 24)}
        for key, field in (("cart", "items"), ("matches", "matches"), ("deployment", "items")):
            self.assertEqual({row["cart_id"] for row in self.saved[key][field]}, expected)
            self.assertEqual(len(self.saved[key][field]), 23)

    def test_every_saved_row_requires_live_offer_review(self):
        rows = self.saved["deployment"]["items"]
        self.assertEqual(sum(row["deployment_status"] == "manual_review" for row in rows), 3)
        self.assertEqual(sum(row["deployment_status"] == "ready_substitute" for row in rows), 6)
        self.assertTrue(all(not row["auto_cart_eligible"] for row in rows))
        items = [SimpleNamespace(asin=row["asin"] or row["cart_id"]) for row in rows]
        self.assertEqual(len(saved_cart_issues(items)), 23)

    def test_substitutes_have_correct_titles_and_pack_counts(self):
        rows = {row["cart_id"]: row for row in self.saved["cart"]["items"]}
        self.assertIn("NELEUS", rows["CART-001"]["title"])
        self.assertIn("PUMA", rows["CART-005"]["title"])
        self.assertEqual(rows["CART-018"]["package_count"], 3)
        self.assertEqual(rows["CART-018"]["color"], "Black/Grove/White")
        self.assertIn("KEEPSHOWING", rows["CART-018"]["original_request"]["title"])

    def test_coffee_request_is_not_replaced_with_conflicting_child(self):
        row = next(row for row in self.saved["deployment"]["items"] if row["cart_id"] == "CART-015")
        self.assertIsNone(row["asin"])
        self.assertEqual(row["color"], "T3 Coffee")
        self.assertEqual(row["size"], "Large")
        self.assertTrue(saved_cart_issues([SimpleNamespace(asin="B0C7L73TR4")]))
        self.assertTrue(saved_cart_issues([SimpleNamespace(asin="B0C7L5HH9Y")]))

    def test_missing_row_is_rejected(self):
        with self.assertRaises(SavedCartError):
            self.validate_modified(lambda saved: saved["deployment"]["items"].pop())

    def test_changed_asin_is_rejected(self):
        with self.assertRaises(SavedCartError):
            self.validate_modified(lambda saved: saved["deployment"]["items"][0].update(asin="B0TEST0001"))

    def test_stale_summary_is_rejected(self):
        with self.assertRaises(SavedCartError):
            self.validate_modified(lambda saved: saved["deployment"]["summary"].update(manual_review_rows=0))

    def test_unreviewed_offer_cannot_be_eligible(self):
        with self.assertRaises(SavedCartError):
            self.validate_modified(lambda saved: saved["deployment"]["items"][0].update(auto_cart_eligible=True))

    def test_manual_queue_must_cover_all_unresolved_rows(self):
        with self.assertRaises(SavedCartError):
            self.validate_modified(lambda saved: saved["deployment"]["manual_review_queue"].pop())

    def test_non_saved_products_are_not_blocked_by_this_guardrail(self):
        self.assertEqual(saved_cart_issues([SimpleNamespace(asin="B08N5WRWNW")]), [])

    def test_corrupt_artifacts_fail_closed(self):
        with patch("src.saved_cart.load_saved_cart", side_effect=SavedCartError("broken manifest")):
            self.assertIn("broken manifest", saved_cart_issues([SimpleNamespace(asin="B08N5WRWNW")])[0])


if __name__ == "__main__":
    unittest.main()
