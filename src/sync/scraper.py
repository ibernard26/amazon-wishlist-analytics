"""
Amazon Wishlist Web Scraper
Fetches wishlist HTML via async HTTP with browser headers, with Playwright browser session support.
"""
import asyncio
import logging
from typing import Optional, List, Dict, Any
import httpx
from src.config import settings
from src.sync.parser import parse_wishlist_html

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": settings.user_agent,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


async def fetch_wishlist_http(url: str) -> str:
    """Fetch wishlist HTML directly via HTTP."""
    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True, headers=HEADERS) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text


async def fetch_wishlist_browser(url: str, headless: bool = True) -> str:
    """Fetch wishlist HTML using Playwright to handle dynamic rendering or authentication cookies."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.warning("Playwright not installed, falling back to HTTP.")
        return await fetch_wishlist_http(url)

    async with async_playwright() as p:
        # Use persistent context if directory exists
        user_data = str(settings.browser_user_data_dir)
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data,
            headless=headless,
            viewport={"width": 1280, "height": 800},
            user_agent=settings.user_agent
        )
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            # Wait for item elements or general body
            await page.wait_for_timeout(2000)
            
            # Scroll down to load lazy elements
            for _ in range(3):
                await page.mouse.wheel(0, 1000)
                await page.wait_for_timeout(500)

            content = await page.content()
            return content
        finally:
            await context.close()


async def scrape_wishlist_items(url: str, use_browser: bool = False) -> List[Dict[str, Any]]:
    """Scrapes and parses wishlist items from an Amazon URL."""
    try:
        if use_browser:
            html = await fetch_wishlist_browser(url)
        else:
            try:
                html = await fetch_wishlist_http(url)
            except Exception as e:
                logger.info(f"Direct HTTP fetch failed ({e}), trying browser session...")
                html = await fetch_wishlist_browser(url)

        items = parse_wishlist_html(html)
        return items
    except Exception as e:
        logger.error(f"Error scraping wishlist from {url}: {e}")
        return []
