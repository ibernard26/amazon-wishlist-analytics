"""
Amazon Cart Importer
Allows importing items directly from the Amazon Shopping Cart into the Wishlist Database.
Supports:
1. Interactive Headed Playwright Session (User logs in safely in their local browser window, zero credentials shared).
2. Direct HTML or Text snippet parsing.
"""
import re
import asyncio
import logging
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from src.config import settings
from src.sync.parser import parse_price, extract_asin

logger = logging.getLogger(__name__)


def parse_amazon_cart_html(html_content: str) -> List[Dict[str, Any]]:
    """Parse Amazon Shopping Cart HTML page and return structured items."""
    soup = BeautifulSoup(html_content, "html.parser")
    items: List[Dict[str, Any]] = []
    seen_asins = set()

    # Look for active cart item containers
    containers = soup.select(
        "div[data-asin]:not([data-asin='']), div.sc-list-item, div.sc-list-item-content, div.sc-item-content-group"
    )

    for c in containers:
        asin = c.get("data-asin")
        if not asin:
            # Check links
            link = c.select_one("a[href*='/dp/'], a[href*='/gp/product/']")
            if link:
                asin = extract_asin(link["href"])

        if not asin or asin in seen_asins:
            continue

        # Title
        title_el = (
            c.select_one("span.sc-product-title")
            or c.select_one("a.sc-product-link span")
            or c.select_one("span.a-truncate-cut")
            or c.select_one("h4 a span")
        )
        title = title_el.get_text(strip=True) if title_el else f"Amazon Product {asin}"

        # Price
        price = None
        price_el = (
            c.select_one("span.sc-product-price")
            or c.select_one("span.a-price .a-offscreen")
            or c.select_one("span.sc-price")
            or c.select_one("div.sc-item-price-block span")
        )
        if price_el:
            price = parse_price(price_el.get_text(strip=True))

        # Strikethrough / Original Price if available
        orig_price = price
        strike_el = c.select_one("span.a-text-price .a-offscreen, span.sc-product-price-basis")
        if strike_el:
            parsed_orig = parse_price(strike_el.get_text(strip=True))
            if parsed_orig and parsed_orig > (price or 0):
                orig_price = parsed_orig

        # Image
        image_url = None
        img_el = c.select_one("img.sc-product-image, img[src*='media-amazon']")
        if img_el:
            image_url = img_el.get("src")

        # In stock
        in_stock = True
        avail_el = c.select_one("span.sc-product-availability, span.a-color-price")
        if avail_el and any(w in avail_el.get_text().lower() for w in ["unavailable", "out of stock"]):
            in_stock = False

        seen_asins.add(asin)
        items.append({
            "asin": asin,
            "title": title,
            "current_price": price or 0.0,
            "original_price": orig_price or price or 0.0,
            "target_price": round((price or 0.0) * 0.9, 2) if price else None,
            "category": "Shopping Cart",
            "priority": "HIGH",
            "image_url": image_url,
            "product_url": f"https://www.amazon.com/dp/{asin}",
            "in_stock": in_stock,
            "notes": "Imported from active Amazon Shopping Cart"
        })

    return items


def parse_amazon_cart_text(text_content: str) -> List[Dict[str, Any]]:
    """Fallback text parser for copied text from Amazon Cart."""
    items = []
    # Find all ASINs or URLs with prices in the text
    asin_matches = re.findall(r"(?:dp/|product/|\b)([B0-9][A-Z0-9]{9})\b", text_content)
    price_matches = re.findall(r"\$\s*(\d+(?:\.\d{2})?)", text_content)

    seen = set()
    for idx, asin in enumerate(asin_matches):
        if asin in seen or asin.startswith("00000"):
            continue
        seen.add(asin)
        price = float(price_matches[idx]) if idx < len(price_matches) else 0.0
        items.append({
            "asin": asin,
            "title": f"Amazon Cart Item ({asin})",
            "current_price": price,
            "original_price": price,
            "target_price": round(price * 0.9, 2) if price > 0 else None,
            "category": "Shopping Cart",
            "priority": "HIGH",
            "product_url": f"https://www.amazon.com/dp/{asin}",
            "in_stock": True,
            "notes": "Parsed from cart text"
        })

    return items


async def import_cart_via_browser(timeout_seconds: int = 120) -> List[Dict[str, Any]]:
    """
    Launches an interactive browser session to let the user view their cart safely.
    Zero passwords or credentials are sent to our app; user authenticates natively in Chromium.
    Once loaded, this function extracts cart items and returns them.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.error("Playwright is not installed.")
        return []

    print("\n🌐 Launching secure browser window for Amazon Cart...")
    print("👉 If you are not signed in, please sign in securely in the opened browser window.")
    print("🔒 Zero credentials are sent to this app — you sign in directly on amazon.com.\n")

    async with async_playwright() as p:
        user_data = str(settings.browser_user_data_dir)
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data,
            headless=False,
            viewport={"width": 1280, "height": 900},
            user_agent=settings.user_agent,
            args=["--start-maximized"]
        )
        page = await context.new_page()

        try:
            await page.goto("https://www.amazon.com/gp/cart/view.html", wait_until="domcontentloaded", timeout=60000)
            
            # Wait for user to sign in if redirected to sign-in page
            print("⏳ Waiting for cart page to load (up to 2 minutes for login/MFA if needed)...")
            for _ in range(timeout_seconds // 2):
                url = page.url
                if "cart" in url.lower() and "signin" not in url.lower():
                    # We are on the cart page!
                    await page.wait_for_timeout(3000)
                    content = await page.content()
                    items = parse_amazon_cart_html(content)
                    if items:
                        print(f"🎉 Successfully detected {len(items)} items in your Amazon Cart!")
                        return items
                await asyncio.sleep(2)

            # Final attempt
            content = await page.content()
            items = parse_amazon_cart_html(content)
            return items

        finally:
            await context.close()
