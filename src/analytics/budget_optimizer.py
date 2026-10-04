"""
Budget Optimizer & Cart Bundle Solver
Uses dynamic programming / utility-weighted knapsack optimization to determine the best items to purchase given a strict spending limit.
"""
from typing import List, Dict, Any, Optional
from src.database.models import WishlistItem
from src.analytics.price_analytics import compute_item_analytics


def optimize_cart_budget(
    items: List[WishlistItem],
    histories_by_item_id: Dict[int, list],
    budget_limit: float,
    strategy: str = "BALANCED",  # "BALANCED", "MAX_PRIORITY", "MAX_SAVINGS"
    only_in_stock: bool = True
) -> Dict[str, Any]:
    """Optimizes item selection to maximize value/priority under a budget limit."""
    
    # Filter valid items
    candidates = []
    for item in items:
        if only_in_stock and not item.in_stock:
            continue
        if item.current_price <= 0:
            continue
        if item.current_price > budget_limit:
            continue

        histories = histories_by_item_id.get(item.id, [])
        analytics = compute_item_analytics(item, histories)

        # Calculate utility score based on strategy
        priority_multiplier = 3.0 if item.priority == "HIGH" else (1.8 if item.priority == "MEDIUM" else 1.0)
        dollar_savings = analytics["dollar_discount"]
        deal_score = analytics["deal_score"]

        if strategy == "MAX_PRIORITY":
            utility = (priority_multiplier * 50.0) + (deal_score * 0.3)
        elif strategy == "MAX_SAVINGS":
            utility = dollar_savings + (deal_score * 0.5)
        else:  # BALANCED
            target_boost = 25.0 if analytics["is_target_met"] else 0.0
            utility = (priority_multiplier * 30.0) + (deal_score * 0.4) + target_boost + (dollar_savings * 0.2)

        candidates.append({
            "item": item,
            "analytics": analytics,
            "cost": item.current_price,
            "utility": utility,
            "efficiency": utility / item.current_price if item.current_price > 0 else 0
        })

    # Sort candidates by utility efficiency (greedy heuristic with 0/1 knapsack fallback)
    candidates.sort(key=lambda x: x["efficiency"], reverse=True)

    # 0/1 Knapsack using integer cents for exact precision
    capacity_cents = int(budget_limit * 100)
    n = len(candidates)
    
    # If list is reasonably sized, run exact dynamic programming, else greedy
    if n <= 40 and capacity_cents <= 100000:  # <= $1000
        # Scaling step to keep matrix compact (step by 50 cents = 50 units)
        step = 50
        scaled_cap = capacity_cents // step
        dp = [0.0] * (scaled_cap + 1)
        item_picks = [[] for _ in range(scaled_cap + 1)]

        for c in candidates:
            w = max(1, int(c["cost"] * 100) // step)
            val = c["utility"]
            for j in range(scaled_cap, w - 1, -1):
                if dp[j - w] + val > dp[j]:
                    dp[j] = dp[j - w] + val
                    item_picks[j] = item_picks[j - w] + [c]

        selected_candidates = item_picks[scaled_cap]
    else:
        # Fast greedy allocation
        selected_candidates = []
        current_spent = 0.0
        for c in candidates:
            if current_spent + c["cost"] <= budget_limit:
                selected_candidates.append(c)
                current_spent += c["cost"]

    # Calculate final totals
    total_spent = sum(c["cost"] for c in selected_candidates)
    total_original = sum(c["item"].original_price or c["cost"] for c in selected_candidates)
    total_savings = max(0.0, total_original - total_spent)
    remaining_budget = max(0.0, budget_limit - total_spent)

    selected_ids = {c["item"].id for c in selected_candidates}
    deferred = [
        {
            "id": c["item"].id,
            "asin": c["item"].asin,
            "title": c["item"].title,
            "price": c["cost"],
            "priority": c["item"].priority,
            "deal_score": c["analytics"]["deal_score"]
        }
        for c in candidates if c["item"].id not in selected_ids
    ]

    selected_items_payload = [
        {
            "id": c["item"].id,
            "asin": c["item"].asin,
            "title": c["item"].title,
            "category": c["item"].category,
            "priority": c["item"].priority,
            "current_price": c["cost"],
            "original_price": c["item"].original_price,
            "savings": c["analytics"]["dollar_discount"],
            "deal_score": c["analytics"]["deal_score"],
            "image_url": c["item"].image_url,
            "product_url": c["item"].product_url,
            "target_met": c["analytics"]["is_target_met"]
        }
        for c in selected_candidates
    ]

    return {
        "budget_limit": round(budget_limit, 2),
        "total_cost": round(total_spent, 2),
        "total_savings": round(total_savings, 2),
        "remaining_budget": round(remaining_budget, 2),
        "item_count": len(selected_candidates),
        "strategy_applied": strategy,
        "selected_items": selected_items_payload,
        "deferred_items_count": len(deferred),
        "deferred_items": deferred[:5]  # Top 5 near misses
    }
