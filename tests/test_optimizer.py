"""
Unit tests for Budget Optimizer & Knapsack Solver
"""
import pytest
from src.database.models import WishlistItem
from src.analytics.budget_optimizer import optimize_cart_budget


def test_optimize_cart_budget():
    items = [
        WishlistItem(id=1, asin="A1", title="Item 1 (High)", current_price=100.0, original_price=150.0, priority="HIGH", in_stock=True),
        WishlistItem(id=2, asin="A2", title="Item 2 (Low Expensive)", current_price=220.0, original_price=220.0, priority="LOW", in_stock=True),
        WishlistItem(id=3, asin="A3", title="Item 3 (Med)", current_price=80.0, original_price=100.0, priority="MEDIUM", in_stock=True),
        WishlistItem(id=4, asin="A4", title="Item 4 (OOS)", current_price=50.0, original_price=50.0, priority="HIGH", in_stock=False),
    ]

    histories = {i.id: [] for i in items}

    # Budget limit of $200
    res = optimize_cart_budget(
        items=items,
        histories_by_item_id=histories,
        budget_limit=200.0,
        strategy="MAX_PRIORITY",
        only_in_stock=True
    )

    assert res["total_cost"] <= 200.0
    assert res["total_cost"] == 180.0  # Item 1 ($100) + Item 3 ($80)
    assert res["item_count"] == 2
    selected_asins = [i["asin"] for i in res["selected_items"]]
    assert "A1" in selected_asins
    assert "A3" in selected_asins
    assert "A4" not in selected_asins  # OOS excluded
    assert "A2" not in selected_asins  # Too expensive for remaining budget
