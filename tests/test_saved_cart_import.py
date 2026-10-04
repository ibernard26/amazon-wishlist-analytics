"""The ASIN upgrade must not duplicate existing placeholder inventory."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.database.crud import upsert_item
from src.database.models import Base, Wishlist, WishlistItem


def test_placeholder_upgrade_preserves_id_history_and_target():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        wishlist = Wishlist(title="Saved clothing cart")
        db.add(wishlist)
        db.commit()
        old = upsert_item(db, {"asin": "CART-001", "title": "Ekkovision request", "current_price": 39.99, "target_price": 35.0}, wishlist.id)
        old_id = old.id
        history_count = len(old.price_history)
        updated = upsert_item(db, {"cart_id": "CART-001", "asin": "B078N5CCB5", "title": "NELEUS substitute", "current_price": 39.99, "product_url": "https://www.amazon.com/dp/B078N5CCB5", "notes": "Historical estimate; offer unreviewed", "auto_buy": False}, wishlist.id)
        assert updated.id == old_id
        assert updated.target_price == 35.0
        assert len(updated.price_history) == history_count
        assert updated.title == "NELEUS substitute"
        assert "Historical estimate" in updated.notes
        assert db.query(WishlistItem).count() == 1


def test_duplicate_placeholder_and_real_asin_require_reconciliation():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        wishlist = Wishlist(title="Saved clothing cart")
        db.add(wishlist)
        db.commit()
        for asin in ("CART-001", "B078N5CCB5"):
            upsert_item(db, {"asin": asin, "title": "Existing user row", "current_price": 39.99}, wishlist.id)
        with pytest.raises(ValueError, match="reconcile"):
            upsert_item(db, {"cart_id": "CART-001", "asin": "B078N5CCB5", "current_price": 39.99}, wishlist.id)
        assert db.query(WishlistItem).count() == 2
