"""
Command-Line Interface (CLI) for Amazon Wishlist Analytics & Cart Execution
"""
import argparse
import sys
import asyncio
import json
from src.database.connection import init_db, get_db_context
from src.database.models import WishlistItem
from src.database.crud import get_items, get_recent_orders, get_price_history_for_item
from src.sync.service import SyncService
from src.analytics.visualizer import build_visualization_payload
from src.analytics.budget_optimizer import optimize_cart_budget
from src.cart.execution_service import CartExecutionService
from src.config import settings


def cmd_serve(args):
    """Start the FastAPI dashboard server."""
    import uvicorn
    print(f"🚀 Starting Amazon Wishlist Analytics Dashboard at http://{args.host}:{args.port}")
    uvicorn.run("src.web.app:app", host=args.host, port=args.port, reload=args.reload)


def cmd_sync(args):
    """Sync wishlist from Amazon URL or load demo sample."""
    init_db()
    with get_db_context() as db:
        service = SyncService(db)
        if args.sample or not args.url:
            print("🌱 Loading realistic demo wishlist dataset...")
            res = service.load_sample_dataset()
            print(f"✅ {res['message']}")
        else:
            print(f"🔄 Syncing wishlist from Amazon: {args.url} (Browser: {args.browser})")
            res = asyncio.run(service.sync_from_url(args.url, use_browser=args.browser))
            if res.get("success"):
                print(f"✅ {res['message']} (Price drops: {res['price_drops_detected']})")
            else:
                print(f"❌ {res['message']}")


def cmd_import_cart(args):
    """Import items from active Amazon Shopping Cart into the database."""
    from src.sync.cart_importer import import_cart_via_browser, parse_amazon_cart_html, parse_amazon_cart_text
    from src.database.crud import get_or_create_default_wishlist, upsert_item

    init_db()
    with get_db_context() as db:
        wishlist = get_or_create_default_wishlist(db, title="Amazon Cart Wishlist")

        items_data = []
        json_target = getattr(args, "json", None)
        from pathlib import Path
        if not json_target:
            if Path("cart.json").is_file():
                json_target = "cart.json"
            elif (Path.home() / "Downloads" / "cart.json").is_file():
                json_target = str(Path.home() / "Downloads" / "cart.json")

        if json_target:
            print(f"📄 Found cart JSON file: {json_target}")
            with open(json_target, "r", encoding="utf-8") as f:
                data = json.load(f)
                items_data = data if isinstance(data, list) else data.get("items", [])
        elif getattr(args, "file", None):
            with open(args.file, "r", encoding="utf-8") as f:
                items_data = parse_amazon_cart_html(f.read())
        elif getattr(args, "text", None):
            items_data = parse_amazon_cart_text(args.text)
        else:
            items_data = asyncio.run(import_cart_via_browser())

        if not items_data:
            print("⚠️ No items could be extracted from the cart.")
            return

        print(f"\n📦 Importing {len(items_data)} items from cart into database...")
        for item_data in items_data:
            item = upsert_item(db, item_data, wishlist.id)
            print(f"  • Added: {item.title[:45]} (${item.current_price:.2f}) [ASIN: {item.asin}]")

        print(f"\n✅ Successfully imported {len(items_data)} items into database wishlist '{wishlist.title}'!")
        print("💡 View them in the dashboard (`python run.py serve`) or list them (`python run.py list`).\n")


def cmd_list(args):
    """List tracked wishlist items."""
    init_db()
    with get_db_context() as db:
        items = get_items(db, category=args.category, priority=args.priority, only_target_met=args.target_met)
        if not items:
            print("No items found matching criteria. Run `python run.py sync --sample` to seed demo data.")
            return

        print(f"\n{'ASIN':<12} {'PRIORITY':<8} {'PRICE':<9} {'TARGET':<9} {'DISC%':<7} {'SCORE':<7} {'TITLE'}")
        print("-" * 88)
        for i in items:
            disc = f"{i.discount_percent:.0f}%" if i.discount_percent > 0 else "-"
            t_price = f"${i.target_price:.2f}" if i.target_price else "-"
            target_flag = "🎯" if i.is_target_met else "  "
            print(f"{i.asin:<12} {i.priority:<8} ${i.current_price:<8.2f} {t_price:<9} {disc:<7} {target_flag} {i.title[:38]}")
        print(f"\nTotal items: {len(items)}\n")


def cmd_deals(args):
    """Show current best deals and price drops."""
    init_db()
    with get_db_context() as db:
        payload = build_visualization_payload(db)
        deals = payload.get("top_deals", [])
        if not deals:
            print("No significant deals detected currently.")
            return

        print("\n🔥 TOP DEALS & PRICE DROPS:")
        print("-" * 75)
        for d in deals:
            print(f"• [{d['deal_score']}/100 Score] {d['title'][:45]}")
            print(f"  Current: ${d['current_price']:.2f} | Was: ${d['original_price']:.2f} | Save: ${d['dollar_discount']:.2f} ({d['discount_percent']}%)")
            print(f"  Status: {d['recommendation_label']}")
            print(f"  URL: https://www.amazon.com/dp/{d['asin']}\n")


def cmd_optimize(args):
    """Run budget knapsack optimizer."""
    init_db()
    with get_db_context() as db:
        items = get_items(db)
        histories = {i.id: get_price_history_for_item(db, i.id) for i in items}
        res = optimize_cart_budget(
            items=items,
            histories_by_item_id=histories,
            budget_limit=args.budget,
            strategy=args.strategy
        )

        print(f"\n🎯 OPTIMIZED CART BUNDLE (Budget Limit: ${res['budget_limit']:.2f})")
        print(f"Strategy: {res['strategy_applied']}")
        print(f"Total Cost: ${res['total_cost']:.2f} (Savings: ${res['total_savings']:.2f}, Left: ${res['remaining_budget']:.2f})")
        print("-" * 75)
        for item in res["selected_items"]:
            t_flag = "🎯 [Target Met]" if item["target_met"] else ""
            print(f"• [{item['priority']}] ${item['current_price']:.2f} (Save ${item['savings']:.2f}) - {item['title'][:45]} {t_flag}")

        if args.cart:
            print("\nExecuting cart order for optimized bundle...")
            cart_service = CartExecutionService(db)
            ids = [i["id"] for i in res["selected_items"]]
            order_res = asyncio.run(cart_service.execute_cart_request(
                item_ids=ids,
                execution_mode=args.mode,
                confirm=True
            ))
            print(f"Order Result: {order_res.get('message')}")
            if order_res.get("remote_cart_url"):
                print(f"Amazon Remote Cart URL: {order_res['remote_cart_url']}")


def cmd_cart(args):
    """Execute shopping cart order for specified ASINs or all target-met items."""
    init_db()
    with get_db_context() as db:
        items = get_items(db)
        if args.asins:
            req_asins = [a.strip() for a in args.asins.split(",")]
            chosen = [i for i in items if i.asin in req_asins]
        elif args.target_met:
            chosen = [i for i in items if i.is_target_met]
        else:
            print("Please specify --asins <ASIN1,ASIN2> or --target-met.")
            return

        if not chosen:
            print("No matching items found for cart execution.")
            return

        cart_service = CartExecutionService(db)
        res = asyncio.run(cart_service.execute_cart_request(
            item_ids=[i.id for i in chosen],
            execution_mode=args.mode,
            confirm=True
        ))

        if res.get("success"):
            print(f"\n✅ {res['message']}")
            print(f"Order Ref: {res.get('order_reference')} | Subtotal: ${res.get('subtotal'):.2f}")
            if res.get("remote_cart_url"):
                print(f"🛒 Direct Amazon Cart Preloader Link:\n{res['remote_cart_url']}\n")
        else:
            print(f"\n❌ Cart execution error: {res.get('error')}")
            if "safety_violations" in res:
                for v in res["safety_violations"]:
                    print(f"  ⚠️  {v}")


def cmd_orders(args):
    """View cart execution order audit logs."""
    init_db()
    with get_db_context() as db:
        orders = get_recent_orders(db, limit=args.limit)
        if not orders:
            print("No orders recorded yet.")
            return
        print(f"\n{'ORDER REF':<22} {'STATUS':<10} {'MODE':<18} {'ITEMS':<6} {'TOTAL':<9} {'DATE'}")
        print("-" * 80)
        for o in orders:
            d_str = o.created_at.strftime("%Y-%m-%d %H:%M")
            print(f"{o.order_reference:<22} {o.status:<10} {o.execution_mode:<18} {o.item_count:<6} ${o.subtotal:<8.2f} {d_str}")


def main():
    parser = argparse.ArgumentParser(description="Amazon Wishlist Analytics & Shopping Cart Execution Engine")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # serve
    p_serve = subparsers.add_parser("serve", help="Run web visualization dashboard")
    p_serve.add_argument("--host", default=settings.host, help="Host to bind")
    p_serve.add_argument("--port", type=int, default=settings.port, help="Port to bind")
    p_serve.add_argument("--reload", action="store_true", help="Enable live auto-reload")

    # sync
    p_sync = subparsers.add_parser("sync", help="Sync items from Amazon Wishlist")
    p_sync.add_argument("--url", help="Amazon Wishlist URL")
    p_sync.add_argument("--sample", action="store_true", help="Load rich demo tech sample data")
    p_sync.add_argument("--browser", action="store_true", help="Use Playwright browser session")

    # list
    p_list = subparsers.add_parser("list", help="List tracked items")
    p_list.add_argument("--category", help="Filter by category")
    p_list.add_argument("--priority", help="Filter by priority (HIGH, MEDIUM, LOW)")
    p_list.add_argument("--target-met", action="store_true", help="Only show items at/below target price")

    # deals
    subparsers.add_parser("deals", help="Show deal radar and price drop alerts")

    # optimize
    p_opt = subparsers.add_parser("optimize", help="Run budget knapsack optimizer")
    p_opt.add_argument("--budget", type=float, default=250.0, help="Dollar budget limit (default: 250)")
    p_opt.add_argument("--strategy", default="BALANCED", choices=["BALANCED", "MAX_PRIORITY", "MAX_SAVINGS"])
    p_opt.add_argument("--cart", action="store_true", help="Immediately stage the optimized bundle into cart")
    p_opt.add_argument("--mode", default="REMOTE_LINK", choices=["REMOTE_LINK", "HEADED_AUTOMATION", "DRY_RUN"])

    # cart
    p_cart = subparsers.add_parser("cart", help="Execute shopping cart order")
    p_cart.add_argument("--asins", help="Comma-separated ASINs (e.g., B08N5WRWNW,B07XJ8C8F5)")
    p_cart.add_argument("--target-met", action="store_true", help="Cart all items currently at/below target price")
    p_cart.add_argument("--mode", default="REMOTE_LINK", choices=["REMOTE_LINK", "HEADED_AUTOMATION", "DRY_RUN"])

    # orders
    p_ord = subparsers.add_parser("orders", help="View past executed orders")
    p_ord.add_argument("--limit", type=int, default=10, help="Number of records to show")

    # import-cart
    p_import = subparsers.add_parser("import-cart", help="Import items from your Amazon Shopping Cart")
    p_import.add_argument("--file", help="Path to saved cart.html file")
    p_import.add_argument("--text", help="Pasted cart text or ASINs")
    p_import.add_argument("--json", help="Path to JSON file containing cart items")

    args = parser.parse_args()

    if not args.command:
        # Default action: run server
        class DefaultArgs:
            host = settings.host
            port = settings.port
            reload = False
        cmd_serve(DefaultArgs())
        return

    commands = {
        "serve": cmd_serve,
        "sync": cmd_sync,
        "import-cart": cmd_import_cart,
        "list": cmd_list,
        "deals": cmd_deals,
        "optimize": cmd_optimize,
        "cart": cmd_cart,
        "orders": cmd_orders
    }

    cmd_fn = commands.get(args.command)
    if cmd_fn:
        cmd_fn(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
