# Amazon Wishlist Analytics & Shopping Cart Execution Platform

An enterprise-grade, full-stack platform for tracking Amazon wishlists, analyzing price trends, visualizing spend distributions, optimizing basket bundles using algorithmic budget solvers, and executing shopping cart orders on Amazon accounts with built-in safety guardrails.

## Saved clothing cart — October 4, 2026

The complete 23-row clothing list is saved for later retrieval. No purchase or
reminder is scheduled. The user plans to request it again around October 11–18;
do not stage or submit an order until asked.

| File | Purpose |
| --- | --- |
| [cart.json](cart.json) | Analytics/import data with stable `cart_id`, selected descriptions, and preserved original requests |
| [amazon_asin_matches.json](amazon_asin_matches.json) | Original intent, selected ASINs, evidence links, substitutions, and unresolved candidates |
| [amazon-shopping-cart-deployment.json](amazon-shopping-cart-deployment.json) | Complete 23-row future-order plan, manual-review queue, and live-offer gates |
| [MEMORY.md](MEMORY.md) | Retrieval instructions and decisions to preserve for the next session |

There are 14 previously matched original identities, 6 selected substitutes, and
3 manual-review rows. These are identity-research statuses, **not current stock
or purchase approval**. Every saved row has `auto_cart_eligible=false` until its
live offer is reviewed. All existing confirmation and budget caps remain in force.

`current_price` is retained for historical-budget analytics only. The $862.74
subtotal uses original-request snapshot prices; it is not a live quote and does
not establish replacement prices. Original product titles, colors, prices,
delivery text, and target budgets remain under `original_request`. Selected
substitute titles/colors are recorded separately so an ASIN does not carry the
wrong brand or variant description. Pack count is distinct from order quantity.

```bash
# Read and validate all 23 saved lines; no database or Amazon writes
python run.py saved-cart
python run.py saved-cart --json

# Import the snapshot for analytics (not an order)
python run.py import-cart --json cart.json

# Offline data-integrity tests, without third-party dependencies
python3 -m unittest discover -s tests -p 'test_saved_cart.py' -v
```

Importing over the old `CART-001` placeholder data upgrades matching rows in
place, preserving their database IDs/history rather than adding another 23 rows.
If both a placeholder and its real ASIN already exist, import stops for explicit
reconciliation instead of deleting either existing record.

When the user returns, refresh US size/color/pack, price, seller, stock, return
terms, delivery and tax/shipping; resolve all three manual-review rows. Keep
them in the plan or obtain an explicit replacement/removal decision. Never treat
`CART-###` as an Amazon ASIN. Cart staging is separate from final order submission.

---

## 🌟 Key Features

### 1. Amazon Wishlist Synchronization & Ingestion
- **Public & Shared Wishlist Importer**: Ingests items directly from any Amazon Wishlist link (`/hz/wishlist/ls/...`).
- **Multi-Factor Session Handling**: Browser automation support via Playwright with persistent session cache (`user_data_dir`) for private wishlists and zero password exposure.
- **Realistic Sample Dataset Generator**: Pre-loaded with realistic tech, home, office, and book items with 30-day historical price movement curves for immediate exploration.
- **Continuous Price Tracking**: Automatically logs price history and records price drop percentages every time sync is triggered.

### 2. Advanced Data Visualizations & Analytics
- **Executive KPI Cards**: Real-time totals for Wishlist Value, Potential Savings ($ and %), Average Discount Rate, Items at/below Target Price, and Deal Radar alerts.
- **30-Day Price Movement & Volatility Timeline**: Multi-series line charts tracking top items against their historical trends and target prices.
- **Category Allocation Chart**: Doughnut chart visualizing spend and item distribution across departments (Electronics, Office, Home, Books).
- **Priority Allocation Chart**: Bar chart illustrating portfolio value by user priority (`HIGH`, `MEDIUM`, `LOW`).
- **Price Bracket Distribution**: Histogram classifying items into price tiers (<$25, $25-$50, $50-$100, $100-$200, $200+).
- **Deal Heat Radar**: Real-time algorithm scoring deals from 0 to 100 based on distance to 30-day low, discount percentage, target price status, and item priority.

### 3. Algorithmic Budget Optimizer (Knapsack Cart Solver)
- Given a target spending limit (e.g. `$250`), dynamically solves for the mathematically optimal combination of items to cart.
- Supports three strategies:
  - **Balanced**: Maximizes priority weights, deal heat, target achievement, and total savings.
  - **Highest Priority First**: Maximizes High and Medium priority items.
  - **Maximum Savings**: Maximizes total dollar discounts from original retail.
- Excludes out-of-stock items and displays near misses / deferred items.

### 4. Safe Shopping Cart Execution Engine
- **Mode 1: Direct Amazon 1-Click Cart Preloader (Recommended & Failsafe)**:
  - Generates official Amazon remote cart preloader links (`https://www.amazon.com/gp/aws/cart/add.html?ASIN.1=...&Quantity.1=1...`).
  - Opens directly in your authenticated browser to pre-load all selected items into your Amazon cart in 1 click, with zero credentials or session cookies needed by the backend.
- **Mode 2: Playwright Browser Automation**:
  - Headed or headless browser session that stages items directly in the cart and presents the Amazon cart view for final human-in-the-loop review.
- **Mode 3: Dry-Run Simulation**:
  - Validates budget caps, item availability, and price surge thresholds without touching Amazon.
- **Built-in Safety Guardrails**:
  - **Max Single Order Budget Cap** (default: `$500.00`).
  - **Price Surge Alert** (blocks order if price spiked `>10%` above target).
  - **Out-of-Stock Filter** (prevents broken cart attempts).
  - **Explicit Human Confirmation Required** before execution.

---

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Clone or navigate to the directory
cd "Amazon-Wishlist-Platform"

# Activate the virtual environment
source .venv/bin/activate

# Install dependencies (if needed)
pip install -r requirements.txt
```

### 2. Launch Web Dashboard
```bash
python run.py
# or
python run.py serve --port 8000
```
Open your browser to: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

### 3. Command Line Interface (CLI)
The CLI allows managing wishlists, price checks, optimization, and cart execution directly from your terminal:

```bash
# Display all tracked items with current vs target prices, discounts & status
python run.py list

# View current top deals & 30-day low alerts
python run.py deals

# Run the budget optimizer for a $250 limit
python run.py optimize --budget 250 --strategy BALANCED

# Cart all items that have reached their target price
python run.py cart --target-met --mode REMOTE_LINK

# Cart specific ASINs
python run.py cart --asins B07978J595,B07ZPKN6YR --mode REMOTE_LINK

# View past execution history & audit logs
python run.py orders
```

---

## 📁 Architecture Overview

```
.
├── src/
│   ├── config.py                 # Configuration & safety threshold settings
│   ├── database/
│   │   ├── connection.py         # SQLite engine, sessions & pragmas
│   │   ├── models.py             # Wishlist, WishlistItem, PriceHistory, CartOrder
│   │   └── crud.py               # Data access layer & timeline queries
│   ├── sync/
│   │   ├── parser.py             # Robust HTML parser for Amazon wishlists
│   │   ├── scraper.py            # HTTP & Playwright browser scrapers
│   │   ├── sample_data.py        # Seed dataset with 30-day price trends
│   │   └── service.py            # Synchronization coordinator
│   ├── analytics/
│   │   ├── price_analytics.py    # Statistical metrics, moving averages & deal scoring
│   │   ├── budget_optimizer.py   # Knapsack algorithm for budget-constrained carting
│   │   └── visualizer.py         # Data formatter for Chart.js dashboards
│   ├── cart/
│   │   ├── safety.py             # Guardrails: budget caps, surge checks & validations
│   │   ├── remote_cart.py        # 1-Click Amazon remote cart preloader links
│   │   ├── playwright_cart.py    # Automated browser cart runner
│   │   └── execution_service.py  # Order lifecycle & audit logging
│   └── web/
│       ├── app.py                # FastAPI server & lifespan events
│       ├── api_routes.py         # REST API endpoints
│       ├── static/               # CSS glassmorphism styling & JS client
│       └── templates/            # Responsive HTML5 dashboard template
├── tests/                        # 15 unit & integration tests
├── requirements.txt
├── pytest.ini
└── run.py                        # Executable CLI & server entrypoint
```

---

## 📡 REST API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/` | `GET` | Main interactive web dashboard |
| `/api/dashboard` | `GET` | Complete KPI cards, chart datasets, and items |
| `/api/items` | `GET` | List items with category, priority, and target filtering |
| `/api/items` | `POST` | Add custom item manually |
| `/api/items/{id}` | `PATCH` | Update item target price, priority, or notes |
| `/api/items/{id}/history` | `GET` | Retrieve 30-day price history points |
| `/api/sync` | `POST` | Sync from Amazon URL or reload sample data |
| `/api/optimize` | `POST` | Run knapsack budget solver (`budget_limit`, `strategy`) |
| `/api/cart/execute` | `POST` | Execute cart order (`REMOTE_LINK`, `HEADED_AUTOMATION`, `DRY_RUN`) |
| `/api/orders` | `GET` | Audit log of previous cart executions |

---

## 🧪 Testing

Run the automated test suite:
```bash
pytest -v
```
All 15 tests cover:
- HTML wishlist parsing & ASIN/Price extraction
- Price analytics & Deal score formulas
- Knapsack budget optimization algorithms
- Cart safety guardrail enforcements (budget cap, price surge, out of stock)
- FastAPI REST endpoints & HTML template rendering
