"""
Amazon Wishlist HTML Parser
Extracts ASIN, title, price, original price, image, rating, priority, and availability from Amazon Wishlist HTML.
"""
import re
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup


def parse_price(price_str: Optional[str]) -> Optional[float]:
    if not price_str:
        return None
    # Strip non-numeric except dot
    cleaned = re.sub(r"[^\d.]", "", price_str)
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def extract_asin(text: str) -> Optional[str]:
    # Amazon standard 10-character alphanumeric ASIN
    match = re.search(r"/(?:dp|gp/product)/([A-Z0-9]{10})", text)
    if match:
        return match.group(1)
    # Direct asin pattern
    match = re.search(r"\b([B0-9][A-Z0-9]{9})\b", text)
    if match:
        return match.group(1)
    return None


def parse_wishlist_html(html_content: str) -> List[Dict[str, Any]]:
    """Parse Amazon Wishlist HTML page and return structured items."""
    soup = BeautifulSoup(html_content, "html.parser")
    items: List[Dict[str, Any]] = []

    # Amazon wishlist item containers
    containers = soup.select(
        "li.g-item-sortable, div[data-itemid], li[data-id], div.g-item-details"
    )

    # Fallback to general product items if not structured as wishlist list
    if not containers:
        containers = soup.select("div.s-result-item[data-asin]")

    seen_asins = set()

    for container in containers:
        asin = None
        # 1. Check data attributes
        if container.has_attr("data-item-prime-info"):
            asin = extract_asin(container["data-item-prime-info"])
        if not asin and container.has_attr("data-asin") and container["data-asin"]:
            asin = container["data-asin"]

        # 2. Extract from internal links
        links = container.find_all("a", href=True)
        for link in links:
            found = extract_asin(link["href"])
            if found:
                asin = found
                break

        if not asin or asin in seen_asins:
            continue

        # Extract Title
        title = None
        title_el = (
            container.select_one("a[id^='itemName_']")
            or container.select_one("h2 a span, h2 span, h3 span")
            or container.select_one("a.a-link-normal[title]")
        )
        if title_el:
            title = title_el.get_text(strip=True)
        if not title:
            # Try any link with text
            for link in links:
                txt = link.get_text(strip=True)
                if len(txt) > 10 and not any(k in txt.lower() for k in ["add to cart", "see details", "prime"]):
                    title = txt
                    break
        if not title:
            title = f"Amazon Item {asin}"

        # Extract Current Price
        current_price = None
        price_el = (
            container.select_one("span.a-price .a-offscreen")
            or container.select_one("span[id^='itemPrice_']")
            or container.select_one("span.a-color-price")
        )
        if price_el:
            current_price = parse_price(price_el.get_text(strip=True))

        if current_price is None:
            # Try combining whole and fraction
            whole = container.select_one("span.a-price-whole")
            fraction = container.select_one("span.a-price-fraction")
            if whole:
                frac_text = fraction.get_text(strip=True) if fraction else "00"
                current_price = parse_price(f"{whole.get_text(strip=True)}.{frac_text}")

        # Extract Original / Strikethrough Price
        orig_price = None
        strike_el = (
            container.select_one("span.a-text-price .a-offscreen")
            or container.select_one("span[data-a-strike='true'] .a-offscreen")
        )
        if strike_el:
            orig_price = parse_price(strike_el.get_text(strip=True))

        if not orig_price or (current_price and orig_price < current_price):
            orig_price = current_price or 0.0

        # Extract Image URL
        image_url = None
        img_el = (
            container.select_one("div[id^='itemImage_'] img")
            or container.select_one("img.s-image")
            or container.select_one("img[src*='media-amazon']")
        )
        if img_el:
            image_url = img_el.get("src") or img_el.get("data-src")

        # Extract Rating
        rating = 4.5
        rating_el = container.select_one("i.a-icon-star span, i.a-icon-star-small span")
        if rating_el:
            match = re.search(r"([\d.]+)\s+out of", rating_el.get_text())
            if match:
                rating = float(match.group(1))

        # Extract Reviews Count
        reviews_count = 0
        reviews_el = container.select_one("span[aria-label*='ratings'], a[href*='customerReviews']")
        if reviews_el:
            r_match = re.search(r"([\d,]+)", reviews_el.get_text())
            if r_match:
                reviews_count = int(r_match.group(1).replace(",", ""))

        # Priority detection
        priority = "MEDIUM"
        priority_el = container.select_one("span[id^='itemPriority_']")
        if priority_el:
            p_text = priority_el.get_text(strip=True).upper()
            if "HIGH" in p_text:
                priority = "HIGH"
            elif "LOW" in p_text:
                priority = "LOW"

        # Stock status
        in_stock = True
        stock_el = container.select_one("span.a-color-price, div.a-alert-content")
        if stock_el and "unavailable" in stock_el.get_text().lower():
            in_stock = False

        seen_asins.add(asin)
        items.append({
            "asin": asin,
            "title": title,
            "current_price": current_price or 0.0,
            "original_price": orig_price,
            "target_price": round((current_price or 0.0) * 0.9, 2) if current_price else None,
            "rating": rating,
            "reviews_count": reviews_count,
            "priority": priority,
            "image_url": image_url,
            "product_url": f"https://www.amazon.com/dp/{asin}",
            "in_stock": in_stock,
            "category": "Wishlist Item"
        })

    return items
