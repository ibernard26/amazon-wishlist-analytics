"""
Unit tests for Amazon Wishlist HTML Parser
"""
import pytest
from src.sync.parser import parse_wishlist_html, extract_asin, parse_price

SAMPLE_HTML = """
<html>
<body>
  <div id="wishlist-page">
    <li class="g-item-sortable" data-itemid="item_1" data-item-prime-info="/dp/B08N5WRWNW">
      <a id="itemName_1" href="/dp/B08N5WRWNW">Sony WH-1000XM5 Noise Cancelling Headphones</a>
      <span class="a-price"><span class="a-offscreen">$328.00</span></span>
      <span class="a-text-price"><span class="a-offscreen">$399.99</span></span>
      <span id="itemPriority_1">Priority: High</span>
      <div id="itemImage_1"><img src="https://m.media-amazon.com/images/I/sample.jpg" /></div>
      <i class="a-icon-star"><span>4.6 out of 5 stars</span></i>
      <span aria-label="14250 ratings">14,250</span>
    </li>
    <li class="g-item-sortable" data-itemid="item_2" data-item-prime-info="/dp/B07XJ8C8F5">
      <a id="itemName_2" href="/dp/B07XJ8C8F5">Kindle Paperwhite 16GB</a>
      <span class="a-price-whole">129</span><span class="a-price-fraction">99</span>
      <span id="itemPriority_2">Priority: Medium</span>
    </li>
  </div>
</body>
</html>
"""


def test_parse_price():
    assert parse_price("$328.00") == 328.00
    assert parse_price("USD 1,249.99") == 1249.99
    assert parse_price(None) is None
    assert parse_price("Unavailable") is None


def test_extract_asin():
    assert extract_asin("https://www.amazon.com/dp/B08N5WRWNW") == "B08N5WRWNW"
    assert extract_asin("/gp/product/B07XJ8C8F5?ref=xyz") == "B07XJ8C8F5"
    assert extract_asin("ASIN is B09G96TFF7 in text") == "B09G96TFF7"


def test_parse_wishlist_html():
    items = parse_wishlist_html(SAMPLE_HTML)
    assert len(items) == 2

    item1 = next(i for i in items if i["asin"] == "B08N5WRWNW")
    assert "Sony" in item1["title"]
    assert item1["current_price"] == 328.00
    assert item1["original_price"] == 399.99
    assert item1["priority"] == "HIGH"
    assert item1["rating"] == 4.6
    assert item1["reviews_count"] == 14250
    assert item1["in_stock"] is True

    item2 = next(i for i in items if i["asin"] == "B07XJ8C8F5")
    assert item2["current_price"] == 129.99
    assert item2["priority"] == "MEDIUM"


def test_parse_amazon_cart_html():
    from src.sync.cart_importer import parse_amazon_cart_html
    cart_html = """
    <div id="sc-active-cart">
      <div data-asin="B08N5WRWNW" class="sc-list-item">
        <span class="sc-product-title">Sony WH-1000XM5 Noise Canceling</span>
        <span class="sc-product-price">$328.00</span>
        <span class="sc-product-price-basis">$399.99</span>
        <img class="sc-product-image" src="https://m.media-amazon.com/img.jpg">
      </div>
    </div>
    """
    items = parse_amazon_cart_html(cart_html)
    assert len(items) == 1
    assert items[0]["asin"] == "B08N5WRWNW"
    assert items[0]["current_price"] == 328.00
    assert items[0]["original_price"] == 399.99


def test_parse_amazon_cart_text():
    from src.sync.cart_importer import parse_amazon_cart_text
    sample_text = "Item 1 https://www.amazon.com/dp/B08N5WRWNW Price: $328.00 and Item 2 B07XJ8C8F5 $129.99"
    items = parse_amazon_cart_text(sample_text)
    assert len(items) == 2
    assert items[0]["asin"] == "B08N5WRWNW"
    assert items[0]["current_price"] == 328.00
    assert items[1]["asin"] == "B07XJ8C8F5"
    assert items[1]["current_price"] == 129.99

