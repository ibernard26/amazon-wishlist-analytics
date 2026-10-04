/**
 * Amazon Wishlist Analytics & Cart Execution Dashboard Client
 */

// Global state
let currentDashboardData = null;
let charts = {
  timeline: null,
  category: null,
  priority: null,
  tiers: null
};

// Selected item IDs for batch carting
const selectedItemIds = new Set();

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", () => {
  initIcons();
  setupEventListeners();
  loadDashboardData();
});

function initIcons() {
  if (window.lucide) {
    window.lucide.createIcons();
  }
}

function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  
  const icon = type === "success" ? "✓" : (type === "error" ? "⚠️" : "ℹ️");
  toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Event Listeners
function setupEventListeners() {
  // Sync buttons
  document.getElementById("btn-open-sync").addEventListener("click", () => openModal("modal-sync"));
  document.getElementById("btn-do-sync").addEventListener("click", handleSync);
  document.getElementById("btn-load-sample").addEventListener("click", handleLoadSample);

  // Optimizer
  const budgetSlider = document.getElementById("opt-budget-slider");
  const budgetInput = document.getElementById("opt-budget-input");

  budgetSlider.addEventListener("input", (e) => {
    budgetInput.value = e.target.value;
  });
  budgetInput.addEventListener("input", (e) => {
    budgetSlider.value = e.target.value;
  });

  document.getElementById("btn-run-optimizer").addEventListener("click", handleRunOptimizer);

  // Table Filters
  document.getElementById("filter-search").addEventListener("input", filterTable);
  document.getElementById("filter-category").addEventListener("change", filterTable);
  document.getElementById("filter-priority").addEventListener("change", filterTable);
  document.getElementById("filter-target-met").addEventListener("change", filterTable);

  // Select all checkbox
  document.getElementById("select-all-items").addEventListener("change", (e) => {
    const checked = e.target.checked;
    document.querySelectorAll(".item-checkbox").forEach(cb => {
      cb.checked = checked;
      const id = parseInt(cb.dataset.id, 10);
      if (checked) selectedItemIds.add(id);
      else selectedItemIds.delete(id);
    });
    updateSelectedCartButton();
  });

  // Batch Cart Action Button
  document.getElementById("btn-cart-selected").addEventListener("click", () => {
    if (selectedItemIds.size === 0) {
      showToast("Please select at least one item to cart.", "error");
      return;
    }
    openCartModal(Array.from(selectedItemIds));
  });

  // Orders History
  document.getElementById("btn-view-orders").addEventListener("click", handleViewOrders);

  // Modal Closers
  document.querySelectorAll(".btn-close-modal").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".modal-backdrop").forEach(m => m.classList.remove("active"));
    });
  });

  // Cart Execute Confirmation
  document.getElementById("btn-confirm-cart").addEventListener("click", handleExecuteCartOrder);
}

function openModal(id) {
  document.getElementById(id).classList.add("active");
}

function closeModal(id) {
  document.getElementById(id).classList.remove("active");
}

// Load Dashboard Data
async function loadDashboardData() {
  try {
    const res = await fetch("/api/dashboard");
    const data = await res.json();
    currentDashboardData = data;

    renderKPIs(data.kpis);
    renderCharts(data);
    renderDealRadar(data.top_deals);
    renderItemsTable(data.items_table);
    populateCategoryFilter(data.category_chart.labels);
    initIcons();
  } catch (err) {
    console.error("Failed to load dashboard data:", err);
    showToast("Failed to fetch dashboard analytics.", "error");
  }
}

// Render KPIs
function renderKPIs(kpis) {
  document.getElementById("kpi-total-val").textContent = `$${kpis.total_value.toFixed(2)}`;
  document.getElementById("kpi-total-sav").textContent = `$${kpis.total_savings.toFixed(2)}`;
  document.getElementById("kpi-avg-disc").textContent = `${kpis.avg_discount_pct}%`;
  document.getElementById("kpi-items-count").textContent = kpis.items_count;
  document.getElementById("kpi-target-met").textContent = kpis.target_met_count;
  document.getElementById("kpi-deal-count").textContent = kpis.deal_count;
}

// Render Charts
function renderCharts(data) {
  const isDark = true;
  const gridColor = "rgba(255, 255, 255, 0.05)";
  const textColor = "#94a3b8";

  // 1. Price Timeline Chart
  const ctxTimeline = document.getElementById("chart-timeline").getContext("2d");
  if (charts.timeline) charts.timeline.destroy();

  charts.timeline = new Chart(ctxTimeline, {
    type: "line",
    data: {
      labels: data.price_timeline_chart.dates,
      datasets: data.price_timeline_chart.datasets
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: {
          position: "top",
          labels: { color: textColor, font: { size: 11 }, boxWidth: 12 }
        },
        tooltip: {
          callbacks: {
            label: (ctx) => ` ${ctx.dataset.label}: $${ctx.parsed.y.toFixed(2)}`
          }
        }
      },
      scales: {
        x: { grid: { color: gridColor }, ticks: { color: textColor } },
        y: {
          grid: { color: gridColor },
          ticks: {
            color: textColor,
            callback: (v) => `$${v}`
          }
        }
      }
    }
  });

  // 2. Category Doughnut Chart
  const ctxCategory = document.getElementById("chart-category").getContext("2d");
  if (charts.category) charts.category.destroy();

  const catColors = ["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#06b6d4"];
  charts.category = new Chart(ctxCategory, {
    type: "doughnut",
    data: {
      labels: data.category_chart.labels,
      datasets: [{
        data: data.category_chart.data,
        backgroundColor: catColors.slice(0, data.category_chart.labels.length),
        borderWidth: 2,
        borderColor: "#1e293b"
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "right", labels: { color: textColor, font: { size: 11 } } },
        tooltip: {
          callbacks: {
            label: (ctx) => ` ${ctx.label}: $${ctx.raw.toFixed(2)}`
          }
        }
      },
      cutout: "68%"
    }
  });

  // 3. Priority Bar Chart
  const ctxPriority = document.getElementById("chart-priority").getContext("2d");
  if (charts.priority) charts.priority.destroy();

  charts.priority = new Chart(ctxPriority, {
    type: "bar",
    data: {
      labels: data.priority_chart.labels,
      datasets: [{
        label: "Total Value ($)",
        data: data.priority_chart.data,
        backgroundColor: ["#ef4444", "#f59e0b", "#94a3b8"],
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => ` Total Value: $${ctx.raw.toFixed(2)}`
          }
        }
      },
      scales: {
        x: { grid: { display: false }, ticks: { color: textColor } },
        y: {
          grid: { color: gridColor },
          ticks: { color: textColor, callback: (v) => `$${v}` }
        }
      }
    }
  });

  // 4. Price Tiers Bar Chart
  const ctxTiers = document.getElementById("chart-tiers").getContext("2d");
  if (charts.tiers) charts.tiers.destroy();

  charts.tiers = new Chart(ctxTiers, {
    type: "bar",
    data: {
      labels: data.price_tiers_chart.labels,
      datasets: [{
        label: "Item Count",
        data: data.price_tiers_chart.data,
        backgroundColor: "#06b6d4",
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: { grid: { display: false }, ticks: { color: textColor } },
        y: {
          grid: { color: gridColor },
          ticks: { color: textColor, stepSize: 1 }
        }
      }
    }
  });
}

// Render Deal Radar Cards
function renderDealRadar(deals) {
  const container = document.getElementById("deal-radar-cards");
  container.innerHTML = "";

  if (!deals || deals.length === 0) {
    container.innerHTML = "<p style='color: var(--text-dim);'>No major price drops detected yet.</p>";
    return;
  }

  deals.forEach(deal => {
    const card = document.createElement("div");
    card.className = "deal-card";
    card.innerHTML = `
      <div class="deal-top">
        <span class="deal-badge">🔥 ${deal.discount_percent}% OFF</span>
        <span class="deal-score-pill">Score: ${deal.deal_score}/100</span>
      </div>
      <a href="https://www.amazon.com/dp/${deal.asin}" target="_blank" class="deal-title" title="${deal.title}">
        ${deal.title.length > 55 ? deal.title.substring(0, 52) + '...' : deal.title}
      </a>
      <div class="deal-metrics">
        <span class="deal-price">$${deal.current_price.toFixed(2)}</span>
        <span class="deal-orig">$${deal.original_price.toFixed(2)}</span>
        <span style="font-size:0.75rem; color:var(--accent-success); margin-left:auto;">Save $${deal.dollar_discount.toFixed(2)}</span>
      </div>
      <div style="display:flex; justify-content:space-between; align-items:center; margin-top:4px;">
        <span style="font-size:0.75rem; color:var(--text-muted);">${deal.recommendation_label}</span>
        <button class="btn btn-amazon btn-sm" onclick="openCartModal([${deal.item_id}])">
          🛒 Quick Cart
        </button>
      </div>
    `;
    container.appendChild(card);
  });
}

// Render Items Table
function renderItemsTable(items) {
  const tbody = document.getElementById("items-table-body");
  tbody.innerHTML = "";

  items.forEach(item => {
    const tr = document.createElement("tr");
    tr.dataset.category = item.category;
    tr.dataset.priority = item.priority;
    tr.dataset.targetMet = item.is_target_met ? "true" : "false";
    tr.dataset.search = `${item.title} ${item.asin}`.toLowerCase();

    const isChecked = selectedItemIds.has(item.id);

    tr.innerHTML = `
      <td>
        <input type="checkbox" class="item-checkbox" data-id="${item.id}" ${isChecked ? "checked" : ""}>
      </td>
      <td>
        <div class="item-cell">
          <img src="${item.image_url || 'https://via.placeholder.com/42'}" alt="" class="item-thumb">
          <div class="item-info">
            <a href="${item.product_url}" target="_blank" class="item-title-link" title="${item.title}">${item.title}</a>
            <span class="item-asin">ASIN: ${item.asin} • ${item.category}</span>
          </div>
        </div>
      </td>
      <td>
        <span class="badge-priority prio-${item.priority}">${item.priority}</span>
      </td>
      <td>
        <div style="font-weight:600; color:#fff;">$${item.current_price.toFixed(2)}</div>
        ${item.original_price > item.current_price ? `<div style="font-size:0.75rem; color:var(--text-dim); text-decoration:line-through;">$${item.original_price.toFixed(2)}</div>` : ''}
      </td>
      <td>
        <div style="display:flex; align-items:center; gap:6px;">
          <span>$</span>
          <input type="number" step="0.50" value="${item.target_price || ''}" 
                 style="width: 80px; padding: 4px 6px; font-size: 0.8rem;" 
                 onchange="updateTargetPrice(${item.id}, this.value)">
        </div>
        ${item.is_target_met ? `<span style="font-size:0.72rem; color:var(--accent-success); font-weight:600;">🎯 Target Met</span>` : ''}
      </td>
      <td>
        ${item.discount_percent > 0 ? `<span style="color:var(--accent-success); font-weight:600;">-${item.discount_percent}%</span>` : `<span style="color:var(--text-dim);">0%</span>`}
      </td>
      <td>
        <span class="deal-score-pill">${item.deal_score}/100</span>
      </td>
      <td>
        ${item.in_stock ? `<span style="color:var(--accent-success); font-size:0.8rem;">● In Stock</span>` : `<span style="color:var(--accent-danger); font-size:0.8rem;">● Out of Stock</span>`}
      </td>
      <td>
        <button class="btn btn-amazon btn-sm" onclick="openCartModal([${item.id}])" ${!item.in_stock ? "disabled" : ""}>
          🛒 Add to Cart
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });

  // Attach checkbox listeners
  tbody.querySelectorAll(".item-checkbox").forEach(cb => {
    cb.addEventListener("change", (e) => {
      const id = parseInt(e.target.dataset.id, 10);
      if (e.target.checked) selectedItemIds.add(id);
      else selectedItemIds.delete(id);
      updateSelectedCartButton();
    });
  });
}

function updateSelectedCartButton() {
  const btn = document.getElementById("btn-cart-selected");
  const count = selectedItemIds.size;
  btn.textContent = `🛒 Cart Selected (${count})`;
  btn.style.display = count > 0 ? "inline-flex" : "none";
}

// Populate Categories
function populateCategoryFilter(categories) {
  const select = document.getElementById("filter-category");
  // Keep first option
  select.innerHTML = '<option value="All">All Categories</option>';
  categories.forEach(cat => {
    const opt = document.createElement("option");
    opt.value = cat;
    opt.textContent = cat;
    select.appendChild(opt);
  });
}

// Table Filtering
function filterTable() {
  const search = document.getElementById("filter-search").value.toLowerCase();
  const cat = document.getElementById("filter-category").value;
  const prio = document.getElementById("filter-priority").value;
  const targetMetOnly = document.getElementById("filter-target-met").checked;

  document.querySelectorAll("#items-table-body tr").forEach(row => {
    const rowSearch = row.dataset.search;
    const rowCat = row.dataset.category;
    const rowPrio = row.dataset.priority;
    const rowTargetMet = row.dataset.targetMet === "true";

    let visible = true;
    if (search && !rowSearch.includes(search)) visible = false;
    if (cat !== "All" && rowCat !== cat) visible = false;
    if (prio !== "All" && rowPrio !== prio) visible = false;
    if (targetMetOnly && !rowTargetMet) visible = false;

    row.style.display = visible ? "" : "none";
  });
}

// In-place Target Price Update
async function updateTargetPrice(itemId, newPrice) {
  const priceVal = parseFloat(newPrice);
  if (isNaN(priceVal) || priceVal < 0) return;

  try {
    const res = await fetch(`/api/items/${itemId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target_price: priceVal })
    });
    if (res.ok) {
      showToast("Target price updated!", "success");
      loadDashboardData();
    }
  } catch (err) {
    showToast("Failed to update target price", "error");
  }
}

// Sync Handlers
async function handleSync() {
  const url = document.getElementById("sync-url-input").value.trim();
  const useBrowser = document.getElementById("sync-browser-check").checked;
  const btn = document.getElementById("btn-do-sync");
  
  if (!url) {
    showToast("Please enter a valid Amazon Wishlist URL.", "error");
    return;
  }

  btn.disabled = true;
  btn.textContent = "Syncing with Amazon...";

  try {
    const res = await fetch("/api/sync", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: url, use_browser: useBrowser })
    });
    const result = await res.json();

    if (result.success) {
      showToast(result.message, "success");
      closeModal("modal-sync");
      loadDashboardData();
    } else {
      showToast(result.message || "Failed to sync wishlist.", "error");
    }
  } catch (err) {
    showToast("Network error syncing wishlist.", "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "Sync Wishlist";
  }
}

async function handleLoadSample() {
  const btn = document.getElementById("btn-load-sample");
  btn.disabled = true;
  btn.textContent = "Loading Demo Data...";

  try {
    const res = await fetch("/api/sync", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ use_sample: true })
    });
    const result = await res.json();
    if (result.success) {
      showToast(result.message, "success");
      closeModal("modal-sync");
      loadDashboardData();
    }
  } catch (err) {
    showToast("Error loading demo data.", "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "Load Sample Tech Wishlist (Demo)";
  }
}

// Budget Optimizer Handler
let lastOptimizerResult = null;

async function handleRunOptimizer() {
  const budget = parseFloat(document.getElementById("opt-budget-input").value);
  const strategy = document.getElementById("opt-strategy-select").value;
  const resultsContainer = document.getElementById("optimizer-results");

  try {
    const res = await fetch("/api/optimize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ budget_limit: budget, strategy: strategy, only_in_stock: true })
    });
    const data = await res.json();
    lastOptimizerResult = data;

    resultsContainer.style.display = "block";
    document.getElementById("opt-res-spent").textContent = `$${data.total_cost.toFixed(2)}`;
    document.getElementById("opt-res-savings").textContent = `$${data.total_savings.toFixed(2)}`;
    document.getElementById("opt-res-remaining").textContent = `$${data.remaining_budget.toFixed(2)}`;
    document.getElementById("opt-res-count").textContent = data.item_count;

    const chipsContainer = document.getElementById("opt-selected-chips");
    chipsContainer.innerHTML = "";

    data.selected_items.forEach(item => {
      const chip = document.createElement("div");
      chip.className = "opt-chip";
      chip.innerHTML = `
        <span class="badge-priority prio-${item.priority}" style="padding:1px 5px; font-size:0.65rem;">${item.priority}</span>
        <span>${item.title.substring(0, 30)}...</span>
        <strong>$${item.current_price.toFixed(2)}</strong>
      `;
      chipsContainer.appendChild(chip);
    });

    document.getElementById("btn-cart-optimized").onclick = () => {
      const ids = data.selected_items.map(i => i.id);
      openCartModal(ids);
    };

    showToast(`Optimized cart solved: ${data.item_count} items for $${data.total_cost.toFixed(2)}`, "success");
  } catch (err) {
    showToast("Failed to run budget optimizer", "error");
  }
}

// Cart Order Modal & Execution
let pendingCartItemIds = [];

function openCartModal(itemIds) {
  pendingCartItemIds = itemIds;
  const modal = document.getElementById("modal-cart");
  const listContainer = document.getElementById("cart-review-list");
  listContainer.innerHTML = "";

  if (!currentDashboardData) return;

  const itemMap = new Map(currentDashboardData.items_table.map(i => [i.id, i]));
  const items = itemIds.map(id => itemMap.get(id)).filter(Boolean);

  let subtotal = 0;
  items.forEach(item => {
    subtotal += item.current_price;
    const row = document.createElement("div");
    row.style.cssText = "display:flex; justify-content:space-between; align-items:center; padding:8px 0; border-bottom:1px solid var(--border-color); font-size:0.85rem;";
    row.innerHTML = `
      <div style="display:flex; align-items:center; gap:8px;">
        <span class="badge-priority prio-${item.priority}">${item.priority}</span>
        <span style="max-width:320px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${item.title}</span>
      </div>
      <strong>$${item.current_price.toFixed(2)}</strong>
    `;
    listContainer.appendChild(row);
  });

  document.getElementById("cart-review-total").textContent = `$${subtotal.toFixed(2)}`;
  document.getElementById("cart-review-count").textContent = items.length;

  openModal("modal-cart");
}

async function handleExecuteCartOrder() {
  const mode = document.getElementById("cart-exec-mode").value;
  const btn = document.getElementById("btn-confirm-cart");

  btn.disabled = true;
  btn.textContent = "Processing Cart Order...";

  try {
    const res = await fetch("/api/cart/execute", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        item_ids: pendingCartItemIds,
        execution_mode: mode,
        confirm: true,
        headless: false
      })
    });
    const result = await res.json();

    if (result.success) {
      closeModal("modal-cart");
      showToast(result.message, "success");

      // If Remote Link mode, open the Amazon pre-loaded cart directly in a new tab!
      if (result.remote_cart_url && (mode === "REMOTE_LINK" || mode === "HEADED_AUTOMATION")) {
        window.open(result.remote_cart_url, "_blank");
      }

      // Clear selections
      selectedItemIds.clear();
      updateSelectedCartButton();
      loadDashboardData();
    } else {
      if (result.safety_violations) {
        showToast(`Safety Guardrail: ${result.safety_violations[0]}`, "error");
      } else {
        showToast(result.error || "Cart execution failed", "error");
      }
    }
  } catch (err) {
    showToast("Error executing shopping cart order.", "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "Confirm & Execute Cart Order";
  }
}

// Past Orders Audit
async function handleViewOrders() {
  try {
    const res = await fetch("/api/orders");
    const orders = await res.json();
    const container = document.getElementById("orders-history-list");
    container.innerHTML = "";

    if (orders.length === 0) {
      container.innerHTML = "<p style='color:var(--text-dim); padding:16px 0;'>No orders executed yet.</p>";
    } else {
      orders.forEach(o => {
        const item = document.createElement("div");
        item.style.cssText = "padding:12px; background:var(--bg-primary); border:1px solid var(--border-color); border-radius:8px; margin-bottom:8px;";
        item.innerHTML = `
          <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
            <strong>${o.order_reference}</strong>
            <span style="color:var(--accent-success); font-weight:600;">$${o.subtotal.toFixed(2)}</span>
          </div>
          <div style="font-size:0.8rem; color:var(--text-muted); display:flex; justify-content:space-between;">
            <span>Mode: ${o.execution_mode} • ${o.item_count} items</span>
            <span>${new Date(o.created_at).toLocaleString()}</span>
          </div>
          ${o.remote_cart_url ? `<a href="${o.remote_cart_url}" target="_blank" style="font-size:0.75rem; color:var(--accent-primary); display:inline-block; margin-top:6px;">Open Amazon Cart Preloader ↗</a>` : ''}
        `;
        container.appendChild(item);
      });
    }

    openModal("modal-orders");
  } catch (err) {
    showToast("Failed to load order history", "error");
  }
}
