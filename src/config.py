"""
Application Configuration and Safety Parameters
"""
import os
from pathlib import Path
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseModel):
    # App Information
    app_name: str = "Amazon Wishlist Analytics & Cart Execution Engine"
    version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")

    # Database
    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'wishlist.db'}")
    
    # Server
    host: str = os.getenv("HOST", "127.0.0.1")
    port: int = int(os.getenv("PORT", "8000"))

    # Amazon Settings
    amazon_domain: str = os.getenv("AMAZON_DOMAIN", "amazon.com")
    default_wishlist_url: str = os.getenv("AMAZON_WISHLIST_URL", "")
    user_agent: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    )

    # Safety & Order Guardrails
    max_single_order_budget: float = float(os.getenv("MAX_SINGLE_ORDER_BUDGET", "500.00"))
    max_price_surge_percent: float = float(os.getenv("MAX_PRICE_SURGE_PERCENT", "10.0"))
    require_confirmation_for_orders: bool = os.getenv("REQUIRE_CONFIRMATION_FOR_ORDERS", "true").lower() in ("true", "1", "yes")
    
    # Playwright & Browser Session
    browser_headless: bool = os.getenv("BROWSER_HEADLESS", "false").lower() in ("true", "1", "yes")
    browser_user_data_dir: Path = DATA_DIR / "browser_session"

settings = Settings()
