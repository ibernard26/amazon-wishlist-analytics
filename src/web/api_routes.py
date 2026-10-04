"""
REST API Routes for Wishlist Analytics, Budget Optimization, and Cart Automation
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from src.database.connection import get_db
from src.database.models import WishlistItem, CartOrder, Wishlist
from src.database.crud import (
    get_items, get_item_by_asin, upsert_item, get_categories,
    get_recent_orders, get_price_history_for_item
)
from src.sync.service import SyncService
from src.analytics.visualizer import build_visualization_payload
from src.analytics.budget_optimizer import optimize_cart_budget
from src.cart.execution_service import CartExecutionService

router = APIRouter(prefix="/api")


# Request/Response Schemas
class SyncRequest(BaseModel):
    url: Optional[str] = None
    use_sample: bool = False
    use_browser: bool = False


class ItemUpdateRequest(BaseModel):
    target_price: Optional[float] = None
    priority: Optional[str] = None
    auto_buy: Optional[bool] = None
    notes: Optional[str] = None


class ItemCreateRequest(BaseModel):
    asin: str
    title: str
    current_price: float
    original_price: Optional[float] = None
    target_price: Optional[float] = None
    category: Optional[str] = "General"
    priority: Optional[str] = "MEDIUM"
    image_url: Optional[str] = None
    in_stock: bool = True


class OptimizeRequest(BaseModel):
    budget_limit: float = Field(..., gt=0)
    strategy: str = "BALANCED"  # BALANCED, MAX_PRIORITY, MAX_SAVINGS
    only_in_stock: bool = True


class CartExecuteRequest(BaseModel):
    item_ids: List[int]
    execution_mode: str = "REMOTE_LINK"  # REMOTE_LINK, HEADED_AUTOMATION, DRY_RUN
    budget_override: Optional[float] = None
    confirm: bool = True
    headless: bool = False


class CartImportRequest(BaseModel):
    items: Optional[List[Dict[str, Any]]] = None
    html_content: Optional[str] = None
    text_content: Optional[str] = None
    use_browser: bool = False


# Endpoints
@router.get("/dashboard")
def get_dashboard_data(db: Session = Depends(get_db)):
    """Fetch all aggregated metrics, chart series, and active items."""
    return build_visualization_payload(db)


@router.get("/items")
def list_items(
    category: Optional[str] = None,
    priority: Optional[str] = None,
    only_target_met: bool = False,
    only_in_stock: bool = False,
    sort_by: str = "priority",
    db: Session = Depends(get_db)
):
    """Retrieve items with filtering and sorting."""
    return get_items(
        db,
        category=category,
        priority=priority,
        only_target_met=only_target_met,
        only_in_stock=only_in_stock,
        sort_by=sort_by
    )


@router.post("/items")
def add_custom_item(payload: ItemCreateRequest, db: Session = Depends(get_db)):
    """Add a new item manually to the wishlist."""
    wishlist = db.query(Wishlist).first()
    wishlist_id = wishlist.id if wishlist else 1
    item = upsert_item(db, payload.dict(), wishlist_id=wishlist_id)
    return {"success": True, "item_id": item.id, "asin": item.asin}


@router.patch("/items/{item_id}")
def update_item(item_id: int, payload: ItemUpdateRequest, db: Session = Depends(get_db)):
    """Update user preferences for an item (target price, priority, auto-buy flag)."""
    item = db.query(WishlistItem).filter(WishlistItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if payload.target_price is not None:
        item.target_price = payload.target_price
    if payload.priority is not None:
        item.priority = payload.priority
    if payload.auto_buy is not None:
        item.auto_buy = payload.auto_buy
    if payload.notes is not None:
        item.notes = payload.notes

    db.commit()
    db.refresh(item)
    return {"success": True, "item_id": item.id}


@router.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    """Remove an item from the wishlist."""
    item = db.query(WishlistItem).filter(WishlistItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return {"success": True, "message": "Item deleted."}


@router.get("/items/{item_id}/history")
def get_item_history(item_id: int, db: Session = Depends(get_db)):
    """Retrieve price history for a specific item."""
    histories = get_price_history_for_item(db, item_id)
    return [
        {
            "id": h.id,
            "price": h.price,
            "original_price": h.original_price,
            "discount_percent": h.discount_percent,
            "recorded_at": h.recorded_at.isoformat()
        }
        for h in histories
    ]


@router.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    """Retrieve list of distinct product categories."""
    return get_categories(db)


@router.post("/sync")
async def trigger_sync(payload: SyncRequest, db: Session = Depends(get_db)):
    """Sync items from an Amazon Wishlist URL or load the realistic sample dataset."""
    service = SyncService(db)
    if payload.use_sample or not payload.url:
        result = service.load_sample_dataset()
        return result
    else:
        result = await service.sync_from_url(
            url=payload.url,
            use_browser=payload.use_browser
        )
        return result


@router.post("/optimize")
def optimize_budget(payload: OptimizeRequest, db: Session = Depends(get_db)):
    """Solve the optimal cart selection for a given dollar budget constraint."""
    items = get_items(db)
    histories_by_item = {i.id: get_price_history_for_item(db, i.id) for i in items}
    result = optimize_cart_budget(
        items=items,
        histories_by_item_id=histories_by_item,
        budget_limit=payload.budget_limit,
        strategy=payload.strategy,
        only_in_stock=payload.only_in_stock
    )
    return result


@router.post("/cart/execute")
async def execute_cart(payload: CartExecuteRequest, db: Session = Depends(get_db)):
    """Execute shopping cart loading via Direct Amazon Remote Link, Browser Automation, or Dry Run."""
    cart_service = CartExecutionService(db)
    result = await cart_service.execute_cart_request(
        item_ids=payload.item_ids,
        execution_mode=payload.execution_mode,
        budget_override=payload.budget_override,
        confirm=payload.confirm,
        headless=payload.headless
    )
    if not result.get("success") and "safety_violations" in result:
        return result  # Return structured safety issues with 200 so UI can display friendly guardrail alerts
    return result


@router.get("/orders")
def list_orders(db: Session = Depends(get_db)):
    """Retrieve historical cart execution orders and logs."""
    orders = get_recent_orders(db)
    return [
        {
            "id": o.id,
            "order_reference": o.order_reference,
            "status": o.status,
            "execution_mode": o.execution_mode,
            "item_count": o.item_count,
            "subtotal": o.subtotal,
            "currency": o.currency,
            "remote_cart_url": o.remote_cart_url,
            "notes": o.notes,
            "executed_at": o.executed_at.isoformat() if o.executed_at else None,
            "created_at": o.created_at.isoformat()
        }
        for o in orders
    ]


@router.post("/cart/import")
async def import_cart_endpoint(payload: CartImportRequest, db: Session = Depends(get_db)):
    """Import items from active Amazon Cart (via browser session, pasted HTML, or text)."""
    from src.sync.cart_importer import import_cart_via_browser, parse_amazon_cart_html, parse_amazon_cart_text
    from src.database.crud import get_or_create_default_wishlist, upsert_item

    wishlist = get_or_create_default_wishlist(db, title="Imported from Amazon Cart")

    items_data = []
    if payload.items:
        items_data = payload.items
    elif payload.html_content:
        items_data = parse_amazon_cart_html(payload.html_content)
    elif payload.text_content:
        items_data = parse_amazon_cart_text(payload.text_content)
    elif payload.use_browser:
        items_data = await import_cart_via_browser()

    if not items_data:
        return {
            "success": False,
            "message": "No items found in provided cart content or browser session.",
            "imported_count": 0
        }

    imported_items = []
    for item_data in items_data:
        item = upsert_item(db, item_data, wishlist.id)
        imported_items.append({"id": item.id, "asin": item.asin, "title": item.title, "price": item.current_price})

    return {
        "success": True,
        "message": f"Successfully imported {len(imported_items)} items from your Amazon Cart into your Wishlist!",
        "imported_count": len(imported_items),
        "items": imported_items
    }

