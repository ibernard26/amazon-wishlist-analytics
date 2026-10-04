"""
Price Analytics and Deal Evaluation Engine
"""
from typing import List, Dict, Any, Optional
import numpy as np
from sqlalchemy.orm import Session
from src.database.models import WishlistItem, PriceHistory


def compute_item_analytics(item: WishlistItem, histories: List[PriceHistory]) -> Dict[str, Any]:
    """Compute statistical analytics, trends, and Deal Score for a single item."""
    prices = [h.price for h in histories] if histories else [item.current_price]
    
    current_price = item.current_price
    min_price = min(prices) if prices else current_price
    max_price = max(prices) if prices else current_price
    avg_price = float(np.mean(prices)) if prices else current_price
    volatility = float(np.std(prices)) if len(prices) > 1 else 0.0

    # Discount metrics
    original_price = item.original_price or current_price
    dollar_discount = max(0.0, original_price - current_price)
    discount_pct = (dollar_discount / original_price * 100) if original_price > 0 else 0.0

    # Deal Score (0 - 100)
    # Factors:
    # 1. Price vs historical low (up to 40 pts)
    if max_price > min_price:
        proximity_to_low = max(0.0, (max_price - current_price) / (max_price - min_price))
    else:
        proximity_to_low = 1.0 if current_price <= (item.target_price or current_price) else 0.5
    low_score = proximity_to_low * 40.0

    # 2. Discount percentage (up to 35 pts)
    discount_score = min(35.0, (discount_pct / 40.0) * 35.0)

    # 3. Target price achievement (up to 15 pts)
    target_score = 15.0 if (item.target_price and current_price <= item.target_price) else 0.0

    # 4. Priority boost (up to 10 pts)
    priority_score = 10.0 if item.priority == "HIGH" else (5.0 if item.priority == "MEDIUM" else 2.0)

    deal_score = round(min(100.0, low_score + discount_score + target_score + priority_score), 1)

    # Recommendation tag
    if deal_score >= 80 or (item.target_price and current_price <= item.target_price):
        recommendation = "STRONG_BUY"
        recommendation_label = "🔥 Strong Buy (Target Met / Deep Deal)"
    elif deal_score >= 60:
        recommendation = "CONSIDER_BUY"
        recommendation_label = "✨ Good Value (Below Average)"
    elif current_price >= max_price and max_price > min_price:
        recommendation = "WAIT"
        recommendation_label = "⏳ Wait (Near 30-Day High)"
    else:
        recommendation = "FAIR"
        recommendation_label = "⚖️ Fair Market Price"

    return {
        "item_id": item.id,
        "asin": item.asin,
        "title": item.title,
        "current_price": current_price,
        "original_price": original_price,
        "target_price": item.target_price,
        "min_30d": round(min_price, 2),
        "max_30d": round(max_price, 2),
        "avg_30d": round(avg_price, 2),
        "volatility": round(volatility, 2),
        "dollar_discount": round(dollar_discount, 2),
        "discount_percent": round(discount_pct, 1),
        "deal_score": deal_score,
        "recommendation": recommendation,
        "recommendation_label": recommendation_label,
        "is_target_met": (item.target_price is not None and current_price <= item.target_price)
    }
