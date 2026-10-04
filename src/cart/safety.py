"""
Safety and Guardrails Module for Amazon Cart Execution
Protects against runaway spending, sudden price surges, and unauthorized order placement.
"""
from typing import List, Dict, Any, Tuple
from src.config import settings
from src.database.models import WishlistItem


class CartSafetyViolation(Exception):
    """Raised when an order violates safety guardrails."""
    pass


def validate_cart_safety(
    items: List[WishlistItem],
    override_budget: float = None,
    require_confirmation: bool = True,
    confirmation_confirmed: bool = False
) -> Tuple[bool, List[str]]:
    """
    Validates a list of items against all safety guardrails.
    Returns (is_valid, list_of_warnings_or_errors).
    """
    issues = []
    
    if not items:
        return False, ["Cart cannot be empty."]

    # 1. Check out-of-stock items
    unavailable = [i.title for i in items if not i.in_stock]
    if unavailable:
        issues.append(f"Unavailable/Out of Stock items detected: {', '.join(unavailable[:3])}")

    # 2. Check total budget threshold
    subtotal = sum(i.current_price for i in items)
    budget_limit = override_budget if override_budget is not None else settings.max_single_order_budget

    if subtotal > budget_limit:
        issues.append(
            f"Subtotal (${subtotal:.2f}) exceeds the safety budget limit (${budget_limit:.2f}). "
            f"Adjust budget limit or remove items."
        )

    # 3. Check for price surge
    surge_threshold = settings.max_price_surge_percent / 100.0
    for item in items:
        if item.target_price and item.target_price > 0:
            if item.current_price > item.target_price * (1.0 + surge_threshold):
                issues.append(
                    f"Price Surge Alert: '{item.title[:25]}' current price (${item.current_price:.2f}) "
                    f"exceeds target (${item.target_price:.2f}) by >{settings.max_price_surge_percent:.0f}%."
                )

    # 4. Confirmation requirement
    if settings.require_confirmation_for_orders and require_confirmation and not confirmation_confirmed:
        issues.append("Safety Guardrail: Explicit user confirmation required before order execution.")

    is_valid = len(issues) == 0
    return is_valid, issues
