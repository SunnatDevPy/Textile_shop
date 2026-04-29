const state = {
  baseUrl: localStorage.getItem("admin_base_url") || window.location.origin,
  username: localStorage.getItem("admin_username") || "",
  password: localStorage.getItem("admin_password") || "",
};

const statusLine = document.getElementById("statusLine");

function setStatus(text, isError = false) {
  statusLine.textContent = isError ? `Xato: ${text}` : `OK: ${text}`;
}

function pretty(v) {
  return JSON.stringify(v, null, 2);
}

function out(id, data) {
  document.getElementById(id).textContent = typeof data === "string" ? data : pretty(data);
}

function bindExpandButtons() {
  document.querySelectorAll(".output").forEach((output) => {
    const toolbar = document.createElement("div");
    toolbar.className = "output-toolbar";
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "expand-btn";
    btn.textContent = "Razvernut";
    btn.addEventListener("click", () => {
      const isExpanded = output.classList.toggle("expanded");
      btn.textContent = isExpanded ? "Svernut" : "Razvernut";
    });
    toolbar.appendChild(btn);
    output.parentNode.insertBefore(toolbar, output);
  });
}

function renderCards(containerId, items) {
  const el = document.getElementById(containerId);
  el.innerHTML = items
    .map(
      (i) =>
        `<div style="min-width:180px;padding:10px;border:1px solid #32476d;border-radius:10px;background:#0b1324">
          <div style="font-size:12px;color:#8fa8d8">${i.label}</div>
          <div style="font-size:20px;font-weight:700">${i.value}</div>
        </div>`
    )
    .join("");
}

function getAuthHeader() {
  if (!state.username || !state.password) return {};
  return { Authorization: "Basic " + btoa(`${state.username}:${state.password}`) };
}

async function api(path) {
  const res = await fetch(`${state.baseUrl}${path}`, { headers: getAuthHeader() });
  const ct = res.headers.get("content-type") || "";
  const body = ct.includes("application/json") ? await res.json() : await res.text();
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${typeof body === "string" ? body : pretty(body)}`);
  return body;
}

function saveAuth() {
  state.baseUrl = document.getElementById("baseUrl").value.trim() || window.location.origin;
  state.username = document.getElementById("username").value.trim();
  state.password = document.getElementById("password").value;
  localStorage.setItem("admin_base_url", state.baseUrl);
  localStorage.setItem("admin_username", state.username);
  localStorage.setItem("admin_password", state.password);
  setStatus("Auth saqlandi");
}

function init() {
  bindExpandButtons();
  document.getElementById("baseUrl").value = state.baseUrl;
  document.getElementById("username").value = state.username;
  document.getElementById("password").value = state.password;

  document.getElementById("saveAuthBtn").addEventListener("click", saveAuth);

  document.getElementById("loadMainKpiBtn").addEventListener("click", async () => {
    try {
      const data = await api("/history/stats/dashboard");
      const d = data?.data || {};
      renderCards("mainKpiCards", [
        { label: "Today revenue", value: d.today_sales?.revenue ?? 0 },
        { label: "Week revenue", value: d.week_sales?.revenue ?? 0 },
        { label: "New orders", value: d.new_orders ?? 0 },
        { label: "Low stock rows", value: (d.low_stock || []).length },
      ]);
      out("mainKpiOut", data);
      setStatus("Asosiy KPI yuklandi");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("loadInventoryBtn").addEventListener("click", async () => {
    try {
      const data = await api("/history/stats/inventory");
      const d = data?.data || {};
      renderCards("inventoryCards", [
        { label: "Products", value: d.products_count ?? 0 },
        { label: "SKU", value: d.sku_count ?? 0 },
        { label: "Total stock", value: d.total_stock ?? 0 },
        { label: "Inventory value", value: d.total_inventory_value ?? 0 },
      ]);
      out("inventoryOut", data);
      setStatus("Sklad KPI yuklandi");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("loadSalesBtn").addEventListener("click", async () => {
    try {
      out("salesOut", await api("/history/stats/sales"));
      setStatus("Sales stats yuklandi");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("loadAnalyticsBtn").addEventListener("click", async () => {
    try {
      out("analyticsOut", await api("/history/stats/analytics-v2"));
      setStatus("Analytics v2 yuklandi");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("loadProductsBtn").addEventListener("click", async () => {
    try {
      out("productsOut", await api("/products"));
      setStatus("Products yuklandi");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("loadProductSearchBtn").addEventListener("click", async () => {
    try {
      out("productsOut", await api("/products/search"));
      setStatus("Products search yuklandi");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("loadProductAdvancedBtn").addEventListener("click", async () => {
    try {
      out("productsOut", await api("/products/search/advanced"));
      setStatus("Products advanced yuklandi");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("loadProductItemsBtn").addEventListener("click", async () => {
    try {
      out("productsOut", await api("/product-items"));
      setStatus("Product items yuklandi");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("loadProductDetailsBtn").addEventListener("click", async () => {
    try {
      out("productsOut", await api("/product-details"));
      setStatus("Product details yuklandi");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("loadOrdersBtn").addEventListener("click", async () => {
    try {
      out("ordersOut", await api("/order"));
      setStatus("Orders yuklandi");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("ordersFilterForm").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const fd = new FormData(ev.target);
    const qs = new URLSearchParams();
    if (fd.get("status_q")) qs.set("status_q", fd.get("status_q"));
    if (fd.get("payment")) qs.set("payment", fd.get("payment"));
    try {
      out("ordersOut", await api(`/order/search?${qs.toString()}`));
      setStatus("Order search yuklandi");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("loadCategoriesBtn").addEventListener("click", async () => {
    try {
      out("lookupsOut", await api("/categories"));
      setStatus("Categories yuklandi");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("loadCollectionsBtn").addEventListener("click", async () => {
    try {
      out("lookupsOut", await api("/collections"));
      setStatus("Collections yuklandi");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("loadColorsBtn").addEventListener("click", async () => {
    try {
      out("lookupsOut", await api("/color"));
      setStatus("Colors yuklandi");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("loadSizesBtn").addEventListener("click", async () => {
    try {
      out("lookupsOut", await api("/size"));
      setStatus("Sizes yuklandi");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("loadMeBtn").addEventListener("click", async () => {
    try {
      out("systemOut", await api("/panel/me"));
      setStatus("Panel me yuklandi");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("loadUsersBtn").addEventListener("click", async () => {
    try {
      out("systemOut", await api("/panel/users"));
      setStatus("Panel users yuklandi");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("loadHealthBtn2").addEventListener("click", async () => {
    try {
      out("systemOut", await api("/system/health"));
      setStatus("Health yuklandi");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("loadReadyBtn2").addEventListener("click", async () => {
    try {
      out("systemOut", await api("/system/ready"));
      setStatus("Ready yuklandi");
    } catch (e) {
      setStatus(e.message, true);
    }
  });
}

init();
