"""
Unit tests for Cart Safety Guardrails and Remote Cart Link Generator
"""
import pytest
from src.database.models import WishlistItem
from src.cart.safety import validate_cart_safety
from src.cart.remote_cart import build_remote_cart_url


def test_validate_cart_safety_budget_exceeded():
    items = [
        WishlistItem(id=1, asin="B08N5WRWNW", title="Expensive Item", current_price=600.0, in_stock=True)
    ]
    # Safety limit $500
    is_safe, issues = validate_cart_safety(items, override_budget=500.0, require_confirmation=False)
    assert is_safe is False
    assert any("exceeds the safety budget limit" in issue for issue in issues)


def test_validate_cart_safety_surge():
    items = [
        # Target is $100, current price surged to $150 (50% surge > 10% threshold)
        WishlistItem(id=1, asin="B08N5WRWNW", title="Surged Item", current_price=150.0, target_price=100.0, in_stock=True)
    ]
    is_safe, issues = validate_cart_safety(items, override_budget=1000.0, require_confirmation=False)
    assert is_safe is False
    assert any("Price Surge Alert" in issue for issue in issues)


def test_validate_cart_safety_confirmation():
    items = [
        WishlistItem(id=1, asin="B08N5WRWNW", title="Normal Item", current_price=50.0, in_stock=True)
    ]
    is_safe, issues = validate_cart_safety(items, override_budget=500.0, require_confirmation=True, confirmation_confirmed=False)
    assert is_safe is False
    assert any("confirmation required" in issue.lower() for issue in issues)

    # With confirmation
    is_safe2, issues2 = validate_cart_safety(items, override_budget=500.0, require_confirmation=True, confirmation_confirmed=True)
    assert is_safe2 is True
    assert len(issues2) == 0


def test_build_remote_cart_url():
    items = [
        WishlistItem(asin="B08N5WRWNW", current_price=328.0),
        WishlistItem(asin="B07XJ8C8F5", current_price=129.99),
    ]
    url = build_remote_cart_url(items)
    assert "https://www.amazon.com/gp/aws/cart/add.html?" in url
    assert "ASIN.1=B08N5WRWNW" in url
    assert "Quantity.1=1" in url
    assert "ASIN.2=B07XJ8C8F5" in url
    assert "Quantity.2=1" in url
