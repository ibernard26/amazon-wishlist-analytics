"""
Database Models for Amazon Wishlist Analytics & Cart Execution
"""
import datetime
from enum import Enum
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    ForeignKey, Text, Index
)
from sqlalchemy.orm import declarative_base, relationship

def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


Base = declarative_base()


class PriorityLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class OrderStatus(str, Enum):
    DRAFT = "DRAFT"
    SIMULATED = "SIMULATED"
    CARTED = "CARTED"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class ExecutionMode(str, Enum):
    REMOTE_LINK = "REMOTE_LINK"          # Direct Amazon 1-click cart preloader URL
    HEADED_AUTOMATION = "HEADED_AUTOMATION" # Playwright browser session
    DRY_RUN = "DRY_RUN"                  # Safety simulation only


class Wishlist(Base):
    __tablename__ = "wishlists"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False, default="My Amazon Wishlist")
    amazon_url = Column(String(1024), nullable=True)
    is_active = Column(Boolean, default=True)
    last_synced_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    items = relationship("WishlistItem", back_populates="wishlist", cascade="all, delete-orphan")


class WishlistItem(Base):
    __tablename__ = "wishlist_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    wishlist_id = Column(Integer, ForeignKey("wishlists.id"), nullable=False, default=1)
    asin = Column(String(20), nullable=False, index=True, unique=True)
    title = Column(String(500), nullable=False)
    current_price = Column(Float, nullable=False, default=0.0)
    original_price = Column(Float, nullable=True)
    target_price = Column(Float, nullable=True)
    currency = Column(String(10), default="USD")
    category = Column(String(100), default="General")
    priority = Column(String(20), default=PriorityLevel.MEDIUM.value)
    rating = Column(Float, default=4.5)
    reviews_count = Column(Integer, default=0)
    image_url = Column(String(1024), nullable=True)
    product_url = Column(String(1024), nullable=True)
    in_stock = Column(Boolean, default=True)
    auto_buy = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    wishlist = relationship("Wishlist", back_populates="items")
    price_history = relationship("PriceHistory", back_populates="item", cascade="all, delete-orphan")

    @property
    def discount_percent(self) -> float:
        if self.original_price and self.original_price > self.current_price:
            return round(((self.original_price - self.current_price) / self.original_price) * 100, 1)
        return 0.0

    @property
    def is_target_met(self) -> bool:
        if self.target_price and self.current_price > 0:
            return self.current_price <= self.target_price
        return False


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(Integer, ForeignKey("wishlist_items.id"), nullable=False, index=True)
    price = Column(Float, nullable=False)
    original_price = Column(Float, nullable=True)
    discount_percent = Column(Float, default=0.0)
    recorded_at = Column(DateTime, default=utc_now, index=True)

    # Relationship
    item = relationship("WishlistItem", back_populates="price_history")


class CartOrder(Base):
    __tablename__ = "cart_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_reference = Column(String(64), unique=True, index=True)
    status = Column(String(30), default=OrderStatus.DRAFT.value)
    execution_mode = Column(String(30), default=ExecutionMode.REMOTE_LINK.value)
    item_count = Column(Integer, default=0)
    subtotal = Column(Float, default=0.0)
    currency = Column(String(10), default="USD")
    items_snapshot = Column(Text, nullable=False)  # JSON-encoded array of items at order time
    remote_cart_url = Column(Text, nullable=True)
    confirmation_token = Column(String(64), nullable=True)
    notes = Column(Text, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)


class AutomationRule(Base):
    __tablename__ = "automation_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), nullable=False)
    condition_type = Column(String(50), nullable=False)  # e.g., 'PRICE_BELOW_TARGET', 'DISCOUNT_GE_PERCENT'
    threshold_value = Column(Float, default=0.0)
    priority_filter = Column(String(20), nullable=True)  # Filter by HIGH, MEDIUM, LOW
    auto_cart = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)
