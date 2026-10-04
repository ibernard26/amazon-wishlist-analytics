"""Read-only saved-cart retrieval and consistency checks (no Amazon calls)."""
import json
import re
from collections import Counter
from decimal import Decimal
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASIN_PATTERN = re.compile(r"[A-Z0-9]{10}\Z")


class SavedCartError(ValueError):
    """The saved artifacts are incomplete or inconsistent."""


def load_saved_cart(root=None):
    """Load all three files and reject drift instead of silently dropping rows."""
    root = Path(root) if root is not None else PROJECT_ROOT
    try:
        cart = json.loads((root / "cart.json").read_text(encoding="utf-8"))
        matches = json.loads((root / "amazon_asin_matches.json").read_text(encoding="utf-8"))
        deployment = json.loads((root / "amazon-shopping-cart-deployment.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SavedCartError(f"Cannot read saved cart artifacts: {exc}") from exc

    try:
        rows = cart["items"]
        mapped = matches["matches"]
        planned = deployment["items"]
        ids = [row["cart_id"] for row in rows]
        if not ids or len(set(ids)) != len(ids):
            raise SavedCartError("Saved cart IDs must be nonempty and unique.")
        if len(mapped) != len(rows) or len(planned) != len(rows):
            raise SavedCartError("All three files must retain the same row count.")
        if {row["cart_id"] for row in mapped} != set(ids) or {row["cart_id"] for row in planned} != set(ids):
            raise SavedCartError("Cart, match, and deployment IDs must agree.")
        mapping = {row["cart_id"]: row for row in mapped}
        plan = {row["cart_id"]: row for row in planned}
        selected_asins = []
        for row in rows:
            cart_id = row["cart_id"]
            match, intent = mapping[cart_id], plan[cart_id]
            selected = intent.get("asin")
            if selected != match.get("asin"):
                raise SavedCartError(f"ASIN mismatch for {cart_id}.")
            if selected is None:
                if row["asin"] != cart_id or intent["deployment_status"] != "manual_review":
                    raise SavedCartError(f"Unresolved {cart_id} must retain a nonpurchase placeholder.")
            elif row["asin"] != selected or not ASIN_PATTERN.fullmatch(selected):
                raise SavedCartError(f"Invalid selected ASIN for {cart_id}.")
            else:
                selected_asins.append(selected)
            if row["quantity"] != intent["quantity"] or row["quantity"] < 1:
                raise SavedCartError(f"Quantity mismatch for {cart_id}.")
            if row["package_count"] != intent["package_count"] or row["package_count"] < 1:
                raise SavedCartError(f"Pack-count mismatch for {cart_id}.")
            if row["size"] != intent["size"] or row["color"] != intent["color"]:
                raise SavedCartError(f"Variant mismatch for {cart_id}.")
            if row["deployment_status"] != intent["deployment_status"]:
                raise SavedCartError(f"Deployment status mismatch for {cart_id}.")
            if row["price_status"] != "historical_budget_estimate" or intent["price_status"] != row["price_status"]:
                raise SavedCartError(f"Snapshot price must not be represented as a live quote: {cart_id}.")
            if row["current_price"] != intent["repo_snapshot_price"] or row["current_price"] != match["repo_price"]:
                raise SavedCartError(f"Snapshot price mismatch for {cart_id}.")
            if intent.get("auto_cart_eligible") and not intent.get("live_offer_confirmed_at"):
                raise SavedCartError(f"Live offer review missing for {cart_id}.")
        if len(selected_asins) != len(set(selected_asins)):
            raise SavedCartError("Selected child ASINs must be unique.")

        counts = Counter(row["deployment_status"] for row in planned)
        summary = deployment["summary"]
        for status, field in (("ready_exact", "ready_exact_rows"), ("ready_substitute", "ready_substitute_rows"), ("manual_review", "manual_review_rows")):
            if counts[status] != summary[field]:
                raise SavedCartError(f"Summary count is stale: {field}.")
        if set(counts) - {"ready_exact", "ready_substitute", "manual_review"}:
            raise SavedCartError("Unknown deployment status.")
        if summary["total_rows"] != len(rows) or matches["summary"]["total_rows"] != len(rows):
            raise SavedCartError("Total-row summary is stale.")
        if summary["auto_cart_eligible_rows"] != sum(bool(row.get("auto_cart_eligible")) for row in planned):
            raise SavedCartError("Automatic-cart eligibility summary is stale.")
        subtotal = sum(Decimal(str(row["current_price"])) * row["quantity"] for row in rows)
        if subtotal != Decimal(str(summary["repo_listed_subtotal_usd"])):
            raise SavedCartError("Historical subtotal is stale.")
        review_ids = {row["cart_id"] for row in deployment["manual_review_queue"]}
        if review_ids != {row["cart_id"] for row in planned if row["deployment_status"] == "manual_review"}:
            raise SavedCartError("Manual-review queue does not cover every unresolved row.")
    except (KeyError, TypeError) as exc:
        raise SavedCartError(f"Missing or invalid saved-cart field: {exc}") from exc
    return {"cart": cart, "matches": matches, "deployment": deployment}


def saved_cart_issues(items):
    """Prevent stale/unresolved saved rows from being automatically staged."""
    try:
        saved = load_saved_cart()
    except SavedCartError as exc:
        return [f"Saved-cart guardrail: {exc}"]
    lookup = {}
    for row in saved["deployment"]["items"]:
        for key in [row["cart_id"], row.get("asin"), *row.get("candidate_asins", [])]:
            if key:
                lookup[key] = row
    for row in saved["matches"]["matches"]:
        for rejected in row.get("rejected_asins", []):
            lookup[rejected] = {"cart_id": row["cart_id"], "deployment_status": "manual_review", "auto_cart_eligible": False}
    issues = []
    for item in items:
        row = lookup.get(item.asin)
        if row is None:
            continue
        if row["deployment_status"] == "manual_review":
            issues.append(f"Saved-cart guardrail: {row['cart_id']} requires exact US variant/offer review; do not omit it silently.")
        elif not row.get("auto_cart_eligible"):
            issues.append(f"Saved-cart guardrail: {row['cart_id']} needs a live price, stock, seller, and delivery check before staging.")
    return issues
