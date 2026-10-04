"""
Playwright Browser Cart Automation Engine
Executes automated cart additions via browser session, supporting dry-run simulation and headed review.
"""
import asyncio
import logging
from typing import List, Dict, Any
from src.config import settings
from src.database.models import WishlistItem
from src.cart.remote_cart import build_remote_cart_url

logger = logging.getLogger(__name__)


async def execute_browser_cart_order(
    items: List[WishlistItem],
    dry_run: bool = False,
    headless: bool = False
) -> Dict[str, Any]:
    """
    Automates adding items to the Amazon shopping cart using Playwright.
    - If dry_run=True, simulates the flow without modifying Amazon state.
    - If dry_run=False, launches browser, loads items into cart, and presents cart review.
    """
    total = sum(i.current_price for i in items)
    remote_url = build_remote_cart_url(items, domain=settings.amazon_domain)

    if dry_run:
        logger.info(f"[DRY-RUN] Simulating cart order for {len(items)} items (${total:.2f})")
        return {
            "success": True,
            "mode": "DRY_RUN",
            "message": f"[Simulation] Successfully simulated carting {len(items)} items. Total: ${total:.2f}",
            "item_count": len(items),
            "subtotal": round(total, 2),
            "remote_cart_url": remote_url
        }

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return {
            "success": False,
            "mode": "ERROR",
            "message": "Playwright is not installed in the current environment.",
            "remote_cart_url": remote_url
        }

    try:
        async with async_playwright() as p:
            user_data = str(settings.browser_user_data_dir)
            context = await p.chromium.launch_persistent_context(
                user_data_dir=user_data,
                headless=headless,
                viewport={"width": 1280, "height": 900},
                user_agent=settings.user_agent,
                args=["--start-maximized"]
            )
            page = await context.new_page()

            # Open remote cart preloader URL directly
            logger.info(f"Navigating to Amazon remote cart preloader: {remote_url}")
            await page.goto(remote_url, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(3000)

            # Check if Amazon asked for "Continue" or "Add to Cart" confirmation
            continue_btn = await page.query_selector("input[name='proceedToCheckout'], input[name='submit.addToCart'], input[name='continue']")
            if continue_btn:
                await continue_btn.click()
                await page.wait_for_timeout(2000)

            # Navigate to cart view to show staged items to user
            await page.goto(f"https://www.{settings.amazon_domain}/gp/cart/view.html", wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)

            # Keep open briefly if headed so user can see it
            if not headless:
                await page.wait_for_timeout(5000)

            await context.close()

            return {
                "success": True,
                "mode": "HEADED_AUTOMATION" if not headless else "HEADLESS_AUTOMATION",
                "message": f"Successfully loaded {len(items)} items into your Amazon shopping cart.",
                "item_count": len(items),
                "subtotal": round(total, 2),
                "remote_cart_url": remote_url
            }

    except Exception as e:
        logger.error(f"Browser cart execution error: {e}")
        return {
            "success": False,
            "mode": "HEADED_AUTOMATION",
            "message": f"Cart execution encountered an error: {str(e)}",
            "item_count": len(items),
            "subtotal": round(total, 2),
            "remote_cart_url": remote_url
        }
