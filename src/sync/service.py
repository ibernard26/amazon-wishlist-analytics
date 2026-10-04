"""
Wishlist Synchronization Service
Coordinates fetching, upserting, price tracking, and sample dataset seeding.
"""
import datetime
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from src.database.crud import (
    get_or_create_default_wishlist, upsert_item, get_items
)
from src.sync.scraper import scrape_wishlist_items
from src.sync.sample_data import seed_sample_database

logger = logging.getLogger(__name__)


class SyncService:
    def __init__(self, db: Session):
        self.db = db

    async def sync_from_url(self, url: str, wishlist_title: Optional[str] = None, use_browser: bool = False) -> Dict[str, Any]:
        """Fetch items from an Amazon Wishlist URL and update the database."""
        wishlist = get_or_create_default_wishlist(self.db, title=wishlist_title or "Amazon Wishlist", url=url)
        items_data = await scrape_wishlist_items(url, use_browser=use_browser)

        if not items_data:
            return {
                "success": False,
                "message": f"Could not find or parse items from {url}. Please ensure the wishlist is public or shared.",
                "items_synced": 0
            }

        synced_count = 0
        price_drops = 0
        for item_data in items_data:
            existing = self.db.query(item_data.get("asin")).first() if hasattr(self.db, "query") else None
            item = upsert_item(self.db, item_data, wishlist.id)
            synced_count += 1
            if item.original_price and item.original_price > item.current_price:
                price_drops += 1

        wishlist.last_synced_at = datetime.datetime.now(datetime.timezone.utc)
        self.db.commit()

        return {
            "success": True,
            "message": f"Successfully synced {synced_count} items from Amazon wishlist.",
            "items_synced": synced_count,
            "price_drops_detected": price_drops,
            "wishlist_id": wishlist.id
        }

    def load_sample_dataset(self) -> Dict[str, Any]:
        """Loads realistic sample dataset with 30-day price trends and categories."""
        wishlist = seed_sample_database(self.db)
        items = get_items(self.db, wishlist_id=wishlist.id)
        return {
            "success": True,
            "message": f"Loaded {len(items)} sample items with complete 30-day price history curves.",
            "items_count": len(items),
            "wishlist_id": wishlist.id
        }
