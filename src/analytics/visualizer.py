"""
Visualization Data Pipeline
Structures aggregated database metrics into Chart.js ready datasets and executive KPI cards.
"""
from typing import Dict, Any, List
from collections import defaultdict
from sqlalchemy.orm import Session
from src.database.models import WishlistItem, PriceHistory
from src.database.crud import get_items, get_price_history_for_item
from src.analytics.price_analytics import compute_item_analytics


def build_visualization_payload(db: Session) -> Dict[str, Any]:
    """Generates complete chart and KPI data for the analytics dashboard."""
    items = get_items(db)
    
    if not items:
        return {
            "kpis": {
                "total_value": 0.0,
                "total_savings": 0.0,
                "items_count": 0,
                "target_met_count": 0,
                "deal_count": 0,
                "avg_discount_pct": 0.0
            },
            "category_chart": {"labels": [], "data": [], "counts": []},
            "priority_chart": {"labels": ["HIGH", "MEDIUM", "LOW"], "data": [0, 0, 0], "counts": [0, 0, 0]},
            "price_timeline_chart": {"dates": [], "datasets": []},
            "price_tiers_chart": {"labels": [], "data": []},
            "top_deals": [],
            "items_table": []
        }

    total_value = 0.0
    total_original_value = 0.0
    target_met_count = 0
    strong_deals = []
    category_totals = defaultdict(float)
    category_counts = defaultdict(int)
    priority_totals = defaultdict(float)
    priority_counts = defaultdict(int)

    price_tiers = {
        "Under $25": 0,
        "$25 - $50": 0,
        "$50 - $100": 0,
        "$100 - $200": 0,
        "$200+": 0
    }

    items_table = []
    histories_by_item = {}

    for item in items:
        total_value += item.current_price
        orig = item.original_price or item.current_price
        total_original_value += orig

        category_totals[item.category] += item.current_price
        category_counts[item.category] += 1

        priority_totals[item.priority] += item.current_price
        priority_counts[item.priority] += 1

        # Price tiers
        p = item.current_price
        if p < 25:
            price_tiers["Under $25"] += 1
        elif p < 50:
            price_tiers["$25 - $50"] += 1
        elif p < 100:
            price_tiers["$50 - $100"] += 1
        elif p < 200:
            price_tiers["$100 - $200"] += 1
        else:
            price_tiers["$200+"] += 1

        # Histories
        histories = get_price_history_for_item(db, item.id)
        histories_by_item[item.id] = histories
        analytics = compute_item_analytics(item, histories)

        if analytics["is_target_met"]:
            target_met_count += 1

        if analytics["deal_score"] >= 65:
            strong_deals.append(analytics)

        items_table.append({
            "id": item.id,
            "asin": item.asin,
            "title": item.title,
            "current_price": item.current_price,
            "original_price": item.original_price,
            "target_price": item.target_price,
            "category": item.category,
            "priority": item.priority,
            "rating": item.rating,
            "reviews_count": item.reviews_count,
            "in_stock": item.in_stock,
            "auto_buy": item.auto_buy,
            "image_url": item.image_url,
            "product_url": item.product_url,
            "discount_percent": analytics["discount_percent"],
            "deal_score": analytics["deal_score"],
            "recommendation": analytics["recommendation"],
            "recommendation_label": analytics["recommendation_label"],
            "is_target_met": analytics["is_target_met"]
        })

    # Sort deals by score
    strong_deals.sort(key=lambda x: x["deal_score"], reverse=True)

    # Total savings
    total_savings = max(0.0, total_original_value - total_value)
    avg_discount = (total_savings / total_original_value * 100) if total_original_value > 0 else 0.0

    # Build Timeline Chart for top items
    # Select top 5 most volatile or highest priority items
    top_timeline_items = sorted(
        items,
        key=lambda i: (i.priority == "HIGH", (i.original_price or 0) - i.current_price),
        reverse=True
    )[:6]

    # Collect unique dates across all top items
    all_dates_set = set()
    for item in top_timeline_items:
        h_list = histories_by_item.get(item.id, [])
        for h in h_list:
            all_dates_set.add(h.recorded_at.strftime("%b %d"))

    sorted_dates = sorted(list(all_dates_set))
    if not sorted_dates:
        sorted_dates = ["Today"]

    # Colors for timeline curves
    palette = [
        {"border": "#3b82f6", "bg": "rgba(59, 130, 246, 0.1)"},  # Blue
        {"border": "#10b981", "bg": "rgba(16, 185, 129, 0.1)"},  # Emerald
        {"border": "#f59e0b", "bg": "rgba(245, 158, 11, 0.1)"},  # Amber
        {"border": "#8b5cf6", "bg": "rgba(139, 92, 246, 0.1)"},  # Purple
        {"border": "#ec4899", "bg": "rgba(236, 72, 153, 0.1)"},  # Pink
        {"border": "#06b6d4", "bg": "rgba(6, 182, 212, 0.1)"},   # Cyan
    ]

    timeline_datasets = []
    for idx, item in enumerate(top_timeline_items):
        color = palette[idx % len(palette)]
        h_list = histories_by_item.get(item.id, [])
        date_price_map = {h.recorded_at.strftime("%b %d"): h.price for h in h_list}
        
        # Build series matching sorted_dates with carry-forward
        series = []
        last_val = item.current_price
        for d in sorted_dates:
            if d in date_price_map:
                last_val = date_price_map[d]
            series.append(last_val)

        timeline_datasets.append({
            "label": item.title[:32] + ("..." if len(item.title) > 32 else ""),
            "data": series,
            "borderColor": color["border"],
            "backgroundColor": color["bg"],
            "tension": 0.3,
            "fill": False,
            "pointRadius": 4,
            "pointHoverRadius": 6
        })

    # Category chart data
    cat_labels = list(category_totals.keys())
    cat_values = [round(category_totals[k], 2) for k in cat_labels]
    cat_counts = [category_counts[k] for k in cat_labels]

    # Priority chart data
    prio_order = ["HIGH", "MEDIUM", "LOW"]
    prio_values = [round(priority_totals[k], 2) for k in prio_order]
    prio_counts = [priority_counts[k] for k in prio_order]

    return {
        "kpis": {
            "total_value": round(total_value, 2),
            "total_savings": round(total_savings, 2),
            "items_count": len(items),
            "target_met_count": target_met_count,
            "deal_count": len(strong_deals),
            "avg_discount_pct": round(avg_discount, 1)
        },
        "category_chart": {
            "labels": cat_labels,
            "data": cat_values,
            "counts": cat_counts
        },
        "priority_chart": {
            "labels": prio_order,
            "data": prio_values,
            "counts": prio_counts
        },
        "price_timeline_chart": {
            "dates": sorted_dates,
            "datasets": timeline_datasets
        },
        "price_tiers_chart": {
            "labels": list(price_tiers.keys()),
            "data": list(price_tiers.values())
        },
        "top_deals": strong_deals[:6],
        "items_table": items_table
    }
