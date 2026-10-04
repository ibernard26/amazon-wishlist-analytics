"""
Realistic Sample Seed Dataset for Amazon Wishlist Analytics & Testing
"""
import datetime
import random
from typing import List, Dict, Any

SAMPLE_WISHLIST_ITEMS: List[Dict[str, Any]] = [
    {
        "asin": "B08N5WRWNW",
        "title": "Sony WH-1000XM5 Wireless Noise Canceling Headphones",
        "current_price": 328.00,
        "original_price": 399.99,
        "target_price": 330.00,
        "category": "Electronics",
        "priority": "HIGH",
        "rating": 4.6,
        "reviews_count": 14250,
        "in_stock": True,
        "auto_buy": True,
        "image_url": "https://m.media-amazon.com/images/I/61V48-7Xp8L._AC_SL1500_.jpg",
        "product_url": "https://www.amazon.com/dp/B08N5WRWNW",
        "notes": "Target met! Excellent for focus and programming.",
        "history_trend": [399.99, 399.99, 380.00, 368.00, 379.99, 349.99, 328.00]
    },
    {
        "asin": "B07XJ8C8F5",
        "title": "Kindle Paperwhite (16 GB) – 6.8\" display, warm light, waterproof",
        "current_price": 129.99,
        "original_price": 149.99,
        "target_price": 120.00,
        "category": "Electronics",
        "priority": "HIGH",
        "rating": 4.7,
        "reviews_count": 28900,
        "in_stock": True,
        "auto_buy": False,
        "image_url": "https://m.media-amazon.com/images/I/61t04yI-3IL._AC_SL1000_.jpg",
        "product_url": "https://www.amazon.com/dp/B07XJ8C8F5",
        "notes": "Waiting for Black Friday / Prime Day drop to $119.",
        "history_trend": [149.99, 149.99, 139.99, 149.99, 134.99, 129.99, 129.99]
    },
    {
        "asin": "B09G96TFF7",
        "title": "Apple iPad Mini (A15 Bionic chip, 8.3-inch Liquid Retina Display, 64GB)",
        "current_price": 399.00,
        "original_price": 499.00,
        "target_price": 400.00,
        "category": "Electronics",
        "priority": "MEDIUM",
        "rating": 4.8,
        "reviews_count": 9410,
        "in_stock": True,
        "auto_buy": True,
        "image_url": "https://m.media-amazon.com/images/I/717Q364JACL._AC_SL1500_.jpg",
        "product_url": "https://www.amazon.com/dp/B09G96TFF7",
        "notes": "$100 discount (20% off) - Target met!",
        "history_trend": [499.00, 479.00, 459.00, 449.00, 429.00, 399.00, 399.00]
    },
    {
        "asin": "B0B7CM273C",
        "title": "Logitech MX Master 3S Wireless Performance Mouse",
        "current_price": 89.99,
        "original_price": 99.99,
        "target_price": 85.00,
        "category": "Office",
        "priority": "HIGH",
        "rating": 4.7,
        "reviews_count": 8200,
        "in_stock": True,
        "auto_buy": False,
        "image_url": "https://m.media-amazon.com/images/I/61ni3t1ryQL._AC_SL1500_.jpg",
        "product_url": "https://www.amazon.com/dp/B0B7CM273C",
        "notes": "Ergonomic quiet clicks, fast magspeed scroll wheel.",
        "history_trend": [99.99, 99.99, 95.00, 99.99, 92.50, 89.99, 89.99]
    },
    {
        "asin": "B091J3NYVF",
        "title": "Keychron Q1 QMK Custom Mechanical Keyboard (Gateron G Pro Brown)",
        "current_price": 169.99,
        "original_price": 179.99,
        "target_price": 150.00,
        "category": "Office",
        "priority": "MEDIUM",
        "rating": 4.5,
        "reviews_count": 1340,
        "in_stock": True,
        "auto_buy": False,
        "image_url": "https://m.media-amazon.com/images/I/61820Z3vV4L._AC_SL1500_.jpg",
        "product_url": "https://www.amazon.com/dp/B091J3NYVF",
        "notes": "CNC aluminum body, hot-swappable.",
        "history_trend": [179.99, 179.99, 179.99, 174.99, 169.99, 169.99, 169.99]
    },
    {
        "asin": "B07978J595",
        "title": "Fellow Stagg EKG Electric Gooseneck Kettle for Pour-over Coffee",
        "current_price": 149.00,
        "original_price": 195.00,
        "target_price": 150.00,
        "category": "Home & Kitchen",
        "priority": "HIGH",
        "rating": 4.6,
        "reviews_count": 5120,
        "in_stock": True,
        "auto_buy": True,
        "image_url": "https://m.media-amazon.com/images/I/61aG-6E8y7L._AC_SL1500_.jpg",
        "product_url": "https://www.amazon.com/dp/B07978J595",
        "notes": "24% price drop! Great deal under target price.",
        "history_trend": [195.00, 195.00, 185.00, 175.00, 165.00, 149.00, 149.00]
    },
    {
        "asin": "B01C5O2P4O",
        "title": "Designing Data-Intensive Applications: The Big Ideas Behind Reliable Systems",
        "current_price": 38.49,
        "original_price": 49.99,
        "target_price": 35.00,
        "category": "Books",
        "priority": "HIGH",
        "rating": 4.8,
        "reviews_count": 7890,
        "in_stock": True,
        "auto_buy": False,
        "image_url": "https://m.media-amazon.com/images/I/71u9s2a+pAL._AC_SL1500_.jpg",
        "product_url": "https://www.amazon.com/dp/B01C5O2P4O",
        "notes": "Martin Kleppmann classic for data engineers and system architects.",
        "history_trend": [49.99, 45.00, 44.99, 41.20, 39.99, 38.49, 38.49]
    },
    {
        "asin": "B07ZPKN6YR",
        "title": "Anker 737 Power Bank (PowerCore 24K, 140W 3-Port Portable Charger)",
        "current_price": 99.99,
        "original_price": 149.99,
        "target_price": 100.00,
        "category": "Electronics",
        "priority": "MEDIUM",
        "rating": 4.7,
        "reviews_count": 6430,
        "in_stock": True,
        "auto_buy": True,
        "image_url": "https://m.media-amazon.com/images/I/61Yw6J6vKLL._AC_SL1500_.jpg",
        "product_url": "https://www.amazon.com/dp/B07ZPKN6YR",
        "notes": "33% off ($50 discount) - High capacity laptop charging.",
        "history_trend": [149.99, 139.99, 129.99, 119.99, 109.99, 99.99, 99.99]
    },
    {
        "asin": "B08K39PBXW",
        "title": "Stanley Quencher H2.0 FlowState Stainless Steel Tumbler 40 oz",
        "current_price": 45.00,
        "original_price": 45.00,
        "target_price": 38.00,
        "category": "Home & Kitchen",
        "priority": "LOW",
        "rating": 4.7,
        "reviews_count": 48200,
        "in_stock": True,
        "auto_buy": False,
        "image_url": "https://m.media-amazon.com/images/I/71u5R2nUv6L._AC_SL1500_.jpg",
        "product_url": "https://www.amazon.com/dp/B08K39PBXW",
        "notes": "Everyday hydration tumbler.",
        "history_trend": [45.00, 45.00, 45.00, 45.00, 45.00, 45.00, 45.00]
    },
    {
        "asin": "B0BDHX8Z63",
        "title": "Bose QuietComfort Ultra Wireless Noise Cancelling Earbuds",
        "current_price": 249.00,
        "original_price": 299.00,
        "target_price": 230.00,
        "category": "Electronics",
        "priority": "MEDIUM",
        "rating": 4.3,
        "reviews_count": 3410,
        "in_stock": True,
        "auto_buy": False,
        "image_url": "https://m.media-amazon.com/images/I/51r2c5L47YL._AC_SL1200_.jpg",
        "product_url": "https://www.amazon.com/dp/B0BDHX8Z63",
        "notes": "Spatial audio with world-class noise cancellation.",
        "history_trend": [299.00, 299.00, 289.00, 279.00, 269.00, 249.00, 249.00]
    },
    {
        "asin": "B09B2W5FG8",
        "title": "AeroPress Clear Coffee Maker – Shatterproof Tritan Espresso Style Press",
        "current_price": 49.95,
        "original_price": 49.95,
        "target_price": 40.00,
        "category": "Home & Kitchen",
        "priority": "LOW",
        "rating": 4.8,
        "reviews_count": 12890,
        "in_stock": True,
        "auto_buy": False,
        "image_url": "https://m.media-amazon.com/images/I/61U4+48M-rL._AC_SL1500_.jpg",
        "product_url": "https://www.amazon.com/dp/B09B2W5FG8",
        "notes": "Compact lightweight travel coffee brewing.",
        "history_trend": [49.95, 49.95, 49.95, 49.95, 47.95, 49.95, 49.95]
    },
    {
        "asin": "B09JS3D7ZG",
        "title": "BenQ ScreenBar Halo LED Monitor Light Bar with Wireless Controller",
        "current_price": 179.00,
        "original_price": 179.00,
        "target_price": 155.00,
        "category": "Office",
        "priority": "LOW",
        "rating": 4.6,
        "reviews_count": 2180,
        "in_stock": False,
        "auto_buy": False,
        "image_url": "https://m.media-amazon.com/images/I/61f2H7uT2rL._AC_SL1500_.jpg",
        "product_url": "https://www.amazon.com/dp/B09JS3D7ZG",
        "notes": "Currently out of stock - monitor auto dimming back light.",
        "history_trend": [179.00, 179.00, 169.00, 179.00, 179.00, 179.00, 179.00]
    }
]


def seed_sample_database(db):
    """Seed the database with sample wishlist data and realistic price history."""
    from src.database.crud import get_or_create_default_wishlist, upsert_item, record_price_history

    wishlist = get_or_create_default_wishlist(
        db,
        title="My Tech & Workspace Wishlist",
        url="https://www.amazon.com/hz/wishlist/ls/SAMPLE_USER_LIST"
    )

    now = datetime.datetime.now(datetime.timezone.utc)
    base_time = now - datetime.timedelta(days=30)

    for item_data in SAMPLE_WISHLIST_ITEMS:
        history_points = item_data.get("history_trend", [item_data["current_price"]])
        
        # Upsert the item
        item = upsert_item(db, item_data, wishlist.id)

        # Clear any auto-generated single point and populate historical curve
        for idx, hist_price in enumerate(history_points):
            point_time = base_time + datetime.timedelta(days=(idx * 5))
            record_price_history(
                db,
                item_id=item.id,
                price=float(hist_price),
                original_price=item.original_price,
                timestamp=point_time
            )

    wishlist.last_synced_at = now
    db.commit()
    return wishlist
