"""
Integration tests for FastAPI REST API endpoints
"""
import pytest
from starlette.testclient import TestClient
from src.web.app import app
from src.database.connection import init_db, get_db_context
from src.sync.sample_data import seed_sample_database


@pytest.fixture(scope="module")
def client():
    """Module-level fixture to run lifespan and seed database."""
    init_db()
    with get_db_context() as db:
        seed_sample_database(db)
    with TestClient(app) as c:
        yield c


def test_root_html_render(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Amazon Wishlist Analytics" in response.text


def test_dashboard_endpoint(client):
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "kpis" in data
    assert "category_chart" in data
    assert "priority_chart" in data
    assert "price_timeline_chart" in data
    assert "items_table" in data
    assert data["kpis"]["items_count"] > 0


def test_list_items(client):
    response = client.get("/api/items")
    assert response.status_code == 200
    items = response.json()
    assert isinstance(items, list)
    assert len(items) > 0


def test_optimize_endpoint(client):
    payload = {
        "budget_limit": 250.0,
        "strategy": "BALANCED",
        "only_in_stock": True
    }
    response = client.post("/api/optimize", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["total_cost"] <= 250.0
    assert len(res["selected_items"]) > 0


def test_cart_execute_dry_run(client):
    # Fetch first available in-stock item id
    items_res = client.get("/api/items")
    items = items_res.json()
    in_stock_item = next(i for i in items if i["in_stock"])
    item_id = in_stock_item["id"]

    payload = {
        "item_ids": [item_id],
        "execution_mode": "DRY_RUN",
        "confirm": True
    }
    response = client.post("/api/cart/execute", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["success"] is True
    assert res["mode"] == "DRY_RUN"
    assert "remote_cart_url" in res


def test_orders_endpoint(client):
    response = client.get("/api/orders")
    assert response.status_code == 200
    orders = response.json()
    assert isinstance(orders, list)


def test_cart_import_json_endpoint(client):
    payload = {
        "items": [
            {
                "asin": "B0TESTCART1",
                "title": "Imported Test Coffee Beans",
                "current_price": 24.99,
                "original_price": 29.99,
                "priority": "HIGH",
                "category": "Grocery",
                "in_stock": True
            }
        ]
    }
    response = client.post("/api/cart/import", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["success"] is True
    assert res["imported_count"] == 1
