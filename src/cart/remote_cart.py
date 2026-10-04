"""
Amazon Remote Cart & Direct Preloader Link Generator
Generates secure 1-click cart preloading links for Amazon accounts without requiring stored passwords or cookie exfiltration.
"""
from typing import List, Dict, Tuple
from urllib.parse import urlencode
from src.database.models import WishlistItem


def build_remote_cart_url(items: List[WishlistItem], domain: str = "amazon.com") -> str:
    """
    Builds an Amazon 1-Click Cart Preloader URL.
    When the user opens this link in their browser (where their Amazon session is active),
    Amazon automatically stages all specified items and quantities into their cart.
    """
    params = {}
    for idx, item in enumerate(items, start=1):
        params[f"ASIN.{idx}"] = item.asin
        params[f"Quantity.{idx}"] = 1

    query_str = urlencode(params)
    return f"https://www.{domain}/gp/aws/cart/add.html?{query_str}"


def build_alternative_cart_url(items: List[WishlistItem], domain: str = "amazon.com") -> str:
    """Alternative standard Amazon cart add query structure."""
    query_parts = []
    for idx, item in enumerate(items):
        query_parts.append(f"items[{idx}][id]={item.asin}")
        query_parts.append(f"items[{idx}][quantity]=1")
    return f"https://www.{domain}/cart/add-to-cart?{'&'.join(query_parts)}"
