"""
Cart Order Execution Service
Orchestrates order creation, safety checks, execution execution pipelines, and audit logging.
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from src.database.models import WishlistItem, CartOrder, OrderStatus, ExecutionMode
from src.database.crud import create_cart_order, get_items
from src.cart.safety import validate_cart_safety
from src.cart.remote_cart import build_remote_cart_url
from src.cart.playwright_cart import execute_browser_cart_order
from src.config import settings


class CartExecutionService:
    def __init__(self, db: Session):
        self.db = db

    async def execute_cart_request(
        self,
        item_ids: List[int],
        execution_mode: str = ExecutionMode.REMOTE_LINK.value,
        budget_override: Optional[float] = None,
        confirm: bool = False,
        headless: bool = False
    ) -> Dict[str, Any]:
        """
        Executes a shopping cart order request across specified items.
        """
        # 1. Fetch requested items
        all_items = get_items(self.db)
        items_map = {i.id: i for i in all_items}
        selected_items = [items_map[iid] for iid in item_ids if iid in items_map]

        if not selected_items:
            return {
                "success": False,
                "error": "No valid items selected for cart execution."
            }

        # 2. Check safety guardrails
        is_safe, issues = validate_cart_safety(
            items=selected_items,
            override_budget=budget_override,
            require_confirmation=settings.require_confirmation_for_orders,
            confirmation_confirmed=confirm
        )

        if not is_safe:
            return {
                "success": False,
                "safety_violations": issues,
                "error": "Order blocked by safety guardrails.",
                "item_count": len(selected_items),
                "subtotal": sum(i.current_price for i in selected_items)
            }

        remote_url = build_remote_cart_url(selected_items, domain=settings.amazon_domain)

        # 3. Handle execution mode
        if execution_mode == ExecutionMode.DRY_RUN.value:
            res = await execute_browser_cart_order(selected_items, dry_run=True)
            order = create_cart_order(
                self.db,
                items=selected_items,
                execution_mode=ExecutionMode.DRY_RUN.value,
                remote_cart_url=remote_url,
                notes="Simulated dry-run order."
            )
            return {
                "success": True,
                "order_id": order.id,
                "order_reference": order.order_reference,
                "status": order.status,
                "mode": ExecutionMode.DRY_RUN.value,
                "item_count": len(selected_items),
                "subtotal": order.subtotal,
                "message": res["message"],
                "remote_cart_url": remote_url
            }

        elif execution_mode == ExecutionMode.HEADED_AUTOMATION.value:
            res = await execute_browser_cart_order(selected_items, dry_run=False, headless=headless)
            status = OrderStatus.CARTED.value if res["success"] else OrderStatus.FAILED.value
            order = create_cart_order(
                self.db,
                items=selected_items,
                execution_mode=ExecutionMode.HEADED_AUTOMATION.value,
                remote_cart_url=remote_url,
                notes=f"Browser automation order. Result: {res['message']}"
            )
            return {
                "success": res["success"],
                "order_id": order.id,
                "order_reference": order.order_reference,
                "status": status,
                "mode": ExecutionMode.HEADED_AUTOMATION.value,
                "item_count": len(selected_items),
                "subtotal": order.subtotal,
                "message": res["message"],
                "remote_cart_url": remote_url
            }

        else:  # REMOTE_LINK (Instant 1-Click Amazon Preloader)
            order = create_cart_order(
                self.db,
                items=selected_items,
                execution_mode=ExecutionMode.REMOTE_LINK.value,
                remote_cart_url=remote_url,
                notes="Generated 1-click Amazon preloader link."
            )
            return {
                "success": True,
                "order_id": order.id,
                "order_reference": order.order_reference,
                "status": order.status,
                "mode": ExecutionMode.REMOTE_LINK.value,
                "item_count": len(selected_items),
                "subtotal": order.subtotal,
                "message": "Direct Amazon Cart Preloader URL generated successfully.",
                "remote_cart_url": remote_url
            }
