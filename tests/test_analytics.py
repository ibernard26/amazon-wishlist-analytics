"""
Unit tests for Price Analytics and Deal Scoring
"""
import pytest
import datetime
from src.database.models import WishlistItem, PriceHistory
from src.analytics.price_analytics import compute_item_analytics


def test_compute_item_analytics():
    item = WishlistItem(
        id=1,
        asin="B08N5WRWNW",
        title="Sony Headphones",
        current_price=328.00,
        original_price=399.99,
        target_price=330.00,
        priority="HIGH"
    )

    now = datetime.datetime.now(datetime.timezone.utc)
    histories = [
        PriceHistory(item_id=1, price=399.99, recorded_at=now - datetime.timedelta(days=20)),
        PriceHistory(item_id=1, price=379.00, recorded_at=now - datetime.timedelta(days=10)),
        PriceHistory(item_id=1, price=328.00, recorded_at=now),
    ]

    res = compute_item_analytics(item, histories)

    assert res["min_30d"] == 328.00
    assert res["max_30d"] == 399.99
    assert res["dollar_discount"] == pytest.approx(71.99, 0.01)
    assert res["discount_percent"] == pytest.approx(18.0, 0.1)
    assert res["is_target_met"] is True
    assert res["deal_score"] >= 75.0
    assert res["recommendation"] == "STRONG_BUY"
