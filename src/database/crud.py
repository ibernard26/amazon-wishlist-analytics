"""
CRUD and Data Access Operations
"""
import datetime
import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc
from src.database.models import (
    Wishlist, WishlistItem, PriceHistory, CartOrder, AutomationRule, OrderStatus
)


def get_or_create_default_wishlist(db: Session, title: str = "My Primary Wishlist", url: Optional[str] = None) -> Wishlist:
    wishlist = db.query(Wishlist).first()
    if not wishlist:
        wishlist = Wishlist(title=title, amazon_url=url)
        db.add(wishlist)
        db.commit()
        db.refresh(wishlist)
    elif url and wishlist.amazon_url != url:
        wishlist.amazon_url = url
        db.commit()
        db.refresh(wishlist)
    return wishlist


def get_items(
    db: Session,
    wishlist_id: Optional[int] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    only_target_met: bool = False,
    only_in_stock: bool = False,
    sort_by: str = "priority",  # priority, price_asc, price_desc, discount_desc, date
) -> List[WishlistItem]:
    query = db.query(WishlistItem)
    if wishlist_id:
        query = query.filter(WishlistItem.wishlist_id == wishlist_id)
    if category and category != "All":
        query = query.filter(WishlistItem.category == category)
    if priority and priority != "All":
        query = query.filter(WishlistItem.priority == priority)
    if only_in_stock:
        query = query.filter(WishlistItem.in_stock == True)
    if only_target_met:
        query = query.filter(
            WishlistItem.target_price.isnot(None),
            WishlistItem.current_price <= WishlistItem.target_price
        )

    if sort_by == "price_asc":
        query = query.order_by(asc(WishlistItem.current_price))
    elif sort_by == "price_desc":
        query = query.order_by(desc(WishlistItem.current_price))
    elif sort_by == "discount_desc":
        # Order by approximate discount
        query = query.order_by(desc(WishlistItem.original_price - WishlistItem.current_price))
    elif sort_by == "priority":
        # HIGH -> MEDIUM -> LOW
        query = query.order_by(
            desc(WishlistItem.priority == "HIGH"),
            desc(WishlistItem.priority == "MEDIUM")
        )
    else:
        query = query.order_by(desc(WishlistItem.updated_at))

    return query.all()


def get_item_by_asin(db: Session, asin: str) -> Optional[WishlistItem]:
    return db.query(WishlistItem).filter(WishlistItem.asin == asin).first()


def upsert_item(db: Session, item_data: Dict[str, Any], wishlist_id: int) -> WishlistItem:
    asin = item_data.get("asin")
    if not asin:
        raise ValueError("ASIN is required to upsert an item.")

    item = get_item_by_asin(db, asin)
    # Upgrade the old placeholder row in place, retaining its ID and history.
    cart_id = item_data.get("cart_id")
    if cart_id and cart_id != asin:
        legacy_item = get_item_by_asin(db, cart_id)
        if legacy_item and item and legacy_item.id != item.id:
            raise ValueError(f"Both {cart_id} and {asin} already exist; reconcile them before importing.")
        if legacy_item and not item:
            item = legacy_item
            item.asin = asin
    new_price = float(item_data.get("current_price", 0.0))
    orig_price = float(item_data.get("original_price", new_price)) if item_data.get("original_price") else new_price

    if not item:
        item = WishlistItem(
            wishlist_id=wishlist_id,
            asin=asin,
            title=item_data.get("title", f"Amazon Item {asin}"),
            current_price=new_price,
            original_price=orig_price,
            target_price=item_data.get("target_price"),
            currency=item_data.get("currency", "USD"),
            category=item_data.get("category", "General"),
            priority=item_data.get("priority", "MEDIUM"),
            rating=item_data.get("rating", 4.5),
            reviews_count=item_data.get("reviews_count", 0),
            image_url=item_data.get("image_url"),
            product_url=item_data.get("product_url", f"https://www.amazon.com/dp/{asin}"),
            in_stock=item_data.get("in_stock", True),
            auto_buy=item_data.get("auto_buy", False),
            notes=item_data.get("notes")
        )
        db.add(item)
        db.flush()
        # Record initial price history
        record_price_history(db, item.id, new_price, orig_price)
    else:
        price_changed = abs(item.current_price - new_price) > 0.01
        item.title = item_data.get("title", item.title)
        item.current_price = new_price
        if item_data.get("original_price"):
            item.original_price = orig_price
        if "target_price" in item_data and item_data["target_price"] is not None:
            item.target_price = float(item_data["target_price"])
        if item_data.get("category"):
            item.category = item_data["category"]
        if item_data.get("priority"):
            item.priority = item_data["priority"]
        if "in_stock" in item_data:
            item.in_stock = item_data["in_stock"]
        if item_data.get("image_url"):
            item.image_url = item_data["image_url"]
        if "product_url" in item_data:
            item.product_url = item_data["product_url"]
        if "notes" in item_data:
            item.notes = item_data["notes"]
        if "auto_buy" in item_data:
            item.auto_buy = item_data["auto_buy"]

        if price_changed:
            record_price_history(db, item.id, new_price, item.original_price)

    db.commit()
    db.refresh(item)
    return item


def record_price_history(db: Session, item_id: int, price: float, original_price: Optional[float] = None, timestamp: Optional[datetime.datetime] = None) -> PriceHistory:
    discount_pct = 0.0
    if original_price and original_price > price:
        discount_pct = round(((original_price - price) / original_price) * 100, 1)

    record = PriceHistory(
        item_id=item_id,
        price=price,
        original_price=original_price or price,
        discount_percent=discount_pct,
        recorded_at=timestamp or datetime.datetime.now(datetime.timezone.utc)
    )
    db.add(record)
    return record


def get_price_history_for_item(db: Session, item_id: int, limit: int = 60) -> List[PriceHistory]:
    return (
        db.query(PriceHistory)
        .filter(PriceHistory.item_id == item_id)
        .order_by(asc(PriceHistory.recorded_at))
        .limit(limit)
        .all()
    )


def create_cart_order(
    db: Session,
    items: List[WishlistItem],
    execution_mode: str,
    remote_cart_url: Optional[str] = None,
    notes: Optional[str] = None
) -> CartOrder:
    subtotal = sum(i.current_price for i in items)
    now = datetime.datetime.now(datetime.timezone.utc)
    order_ref = f"ORD-{now.strftime('%Y%m%d-%H%M%S')}"

    snapshot = [
        {
            "id": i.id,
            "asin": i.asin,
            "title": i.title,
            "price": i.current_price,
            "priority": i.priority,
            "category": i.category,
            "image_url": i.image_url
        }
        for i in items
    ]

    order = CartOrder(
        order_reference=order_ref,
        status=OrderStatus.CARTED.value if execution_mode != "DRY_RUN" else OrderStatus.SIMULATED.value,
        execution_mode=execution_mode,
        item_count=len(items),
        subtotal=round(subtotal, 2),
        currency="USD",
        items_snapshot=json.dumps(snapshot),
        remote_cart_url=remote_cart_url,
        notes=notes,
        executed_at=now
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def get_recent_orders(db: Session, limit: int = 15) -> List[CartOrder]:
    return db.query(CartOrder).order_by(desc(CartOrder.created_at)).limit(limit).all()


def get_categories(db: Session) -> List[str]:
    cats = db.query(WishlistItem.category).distinct().all()
    return [c[0] for c in cats if c[0]]
