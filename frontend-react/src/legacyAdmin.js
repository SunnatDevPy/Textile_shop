const state = {
  baseUrl: localStorage.getItem("admin_base_url") || window.location.origin,
  username: localStorage.getItem("admin_username") || "",
  password: localStorage.getItem("admin_password") || "",
  ordersTable: {
    page: 1,
    pageSize: 20,
    sortBy: "created_at",
    sortDir: "desc",
    filters: {},
  },
  productsTable: {
    page: 1,
    pageSize: 20,
    sortBy: "id",
    sortDir: "desc",
    filters: {},
  },
};

const statusLine = document.getElementById("statusLine");

function setStatus(text, isError = false) {
  statusLine.textContent = isError ? `Xato: ${text}` : `OK: ${text}`;
  statusLine.style.borderColor = isError ? "#ef4444" : "#334155";
}

function pretty(obj) {
  return JSON.stringify(obj, null, 2);
}

function out(id, data) {
  const el = document.getElementById(id);
  el.textContent = typeof data === "string" ? data : pretty(data);
}

function getAuthHeader() {
  if (!state.username || !state.password) return {};
  return {
    Authorization: "Basic " + btoa(`${state.username}:${state.password}`),
  };
}

async function api(path, options = {}) {
  const url = `${state.baseUrl}${path}`;
  const headers = {
    ...getAuthHeader(),
    ...(options.headers || {}),
  };

  if (options.body && !(options.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(url, { ...options, headers });
  const contentType = res.headers.get("content-type") || "";
  const body = contentType.includes("application/json") ? await res.json() : await res.text();

  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${typeof body === "string" ? body : pretty(body)}`);
  }
  setStatus(`${path} muvaffaqiyatli bajarildi.`);
  return body;
}

function bindTabs() {
  const tabButtons = document.querySelectorAll(".tab-btn");
  tabButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      tabButtons.forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById(btn.dataset.tab).classList.add("active");
    });
  });
}

function fillAuthInputs() {
  document.getElementById("baseUrl").value = state.baseUrl;
  document.getElementById("username").value = state.username;
  document.getElementById("password").value = state.password;
}

function saveAuth() {
  state.baseUrl = document.getElementById("baseUrl").value.trim() || window.location.origin;
  state.username = document.getElementById("username").value.trim();
  state.password = document.getElementById("password").value;
  localStorage.setItem("admin_base_url", state.baseUrl);
  localStorage.setItem("admin_username", state.username);
  localStorage.setItem("admin_password", state.password);
  setStatus("Auth ma'lumotlari saqlandi.");
}

function toFormData(form) {
  return new FormData(form);
}

function parseBool(v) {
  return String(v).toLowerCase() === "true";
}

function esc(v) {
  return String(v ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function nextSortDir(current, field, activeField) {
  if (activeField !== field) return "desc";
  return current === "desc" ? "asc" : "desc";
}

function renderMetricCards(containerId, items) {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.innerHTML = (items || [])
    .map(
      (i) => `<div style="min-width:180px;padding:10px;border:1px solid #32476d;border-radius:10px;background:#0b1324">
      <div style="font-size:12px;color:#8fa8d8">${esc(i.label)}</div>
      <div style="font-size:20px;font-weight:700">${esc(i.value)}</div>
    </div>`
    )
    .join("");
}

function renderRowsTable(containerId, headers, rows) {
  const el = document.getElementById(containerId);
  if (!el) return;
  const head = headers.map((h) => `<th>${esc(h)}</th>`).join("");
  const body = (rows || []).length
    ? rows
        .map((r) => `<tr>${r.map((c) => `<td>${esc(c)}</td>`).join("")}</tr>`)
        .join("")
    : `<tr><td colspan="${headers.length}">Ma'lumot yo'q</td></tr>`;
  el.innerHTML = `<table class="data-table"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
}

function bindGlobalActions() {
  document.getElementById("saveAuthBtn").addEventListener("click", saveAuth);
  document.getElementById("checkMeBtn").addEventListener("click", async () => {
    try {
      const data = await api("/panel/me");
      setStatus("Autentifikatsiya to'g'ri.");
      out("panelOut", data);
    } catch (e) {
      setStatus(e.message, true);
    }
  });
}

function bindDashboard() {
  document.getElementById("loadHealthBtn").addEventListener("click", async () => {
    try {
      const [health, ready] = await Promise.all([api("/system/health"), api("/system/ready")]);
      out("dashboardOut", { health, ready });
      setStatus("System data loaded.");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("loadDashBtn").addEventListener("click", async () => {
    try {
      const [dashboard, sales, analytics] = await Promise.all([
        api("/history/stats/dashboard"),
        api("/history/stats/sales"),
        api("/history/stats/analytics-v2"),
      ]);

      const d = dashboard?.data || {};
      const s = sales?.data || {};
      const a = analytics?.data || {};

      renderMetricCards("dashKpiCards", [
        { label: "Bugungi tushum", value: d.today_sales?.revenue ?? 0 },
        { label: "Haftalik tushum", value: d.week_sales?.revenue ?? 0 },
        { label: "Yangi buyurtmalar", value: d.new_orders ?? 0 },
        { label: "AOV", value: s.avg_order_value ?? 0 },
        { label: "Sold rate", value: `${((a.funnel?.sold_rate ?? 0) * 100).toFixed(1)}%` },
        { label: "Today/Week nisbati", value: `${((d.today_vs_week_revenue_rate ?? 0) * 100).toFixed(1)}%` },
      ]);

      renderRowsTable(
        "dashPaymentMixTable",
        ["To'lov", "Buyurtma", "Ulush", "Tushum"],
        (a.payment_mix || []).map((x) => [
          x.payment,
          x.orders_count ?? 0,
          `${(((x.orders_rate ?? 0) * 100).toFixed(1))}%`,
          x.revenue ?? 0,
        ])
      );

      renderRowsTable(
        "dashTopCategoriesTable",
        ["Kategoriya", "Soni", "Tushum"],
        (a.top_categories || d.top_categories || []).map((x) => [
          x.name_uz ?? "-",
          x.sold_items ?? 0,
          x.revenue ?? 0,
        ])
      );

      out("dashboardOut", { dashboard, sales, analytics });
      setStatus("Dashboard stats loaded.");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("loadInventoryBtn").addEventListener("click", async () => {
    try {
      const data = await api("/history/stats/inventory");
      out("dashboardOut", data);
      setStatus("Sklad stats loaded.");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("loadBootstrapBtn").addEventListener("click", async () => {
    try {
      const data = await api("/panel/bootstrap");
      out("dashboardOut", data);
      setStatus("Frontend bootstrap loaded.");
    } catch (e) {
      setStatus(e.message, true);
    }
  });
}

function bindOrders() {
  document.getElementById("listOrdersBtn").addEventListener("click", async () => {
    try {
      out("ordersOut", await api("/order"));
      setStatus("Orders loaded.");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("searchOrdersForm").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const fd = new FormData(ev.target);
    const qs = new URLSearchParams();
    ["order_id", "status_q", "payment", "contact"].forEach((k) => {
      const v = fd.get(k);
      if (v) qs.set(k, v);
    });
    try {
      out("ordersOut", await api(`/order/search?${qs.toString()}`));
      setStatus("Order search done.");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("updateStatusForm").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const fd = new FormData(ev.target);
    const orderId = fd.get("order_id");
    const form = new FormData();
    form.set("new_status", fd.get("new_status"));
    try {
      out("ordersOut", await api(`/order/${orderId}/status`, { method: "PATCH", body: form }));
      setStatus("Order status updated.");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("confirmPaymentForm").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const fd = new FormData(ev.target);
    const body = {};
    const nextStatus = String(fd.get("next_status") || "").trim();
    if (nextStatus) body.next_status = nextStatus;
    try {
      out(
        "ordersOut",
        await api(`/order/${fd.get("order_id")}/confirm-payment`, {
          method: "POST",
          body: pretty(body) === "{}" ? undefined : JSON.stringify(body),
        })
      );
      setStatus("Order payment confirmed.");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  async function loadOrdersTable() {
    const params = new URLSearchParams({
      page: String(state.ordersTable.page),
      page_size: String(state.ordersTable.pageSize),
      sort_by: state.ordersTable.sortBy,
      sort_dir: state.ordersTable.sortDir,
    });
    Object.entries(state.ordersTable.filters).forEach(([k, v]) => {
      if (v !== undefined && v !== null && String(v).trim() !== "") params.set(k, String(v).trim());
    });

    const data = await api(`/order/admin-table?${params.toString()}`);
    const rows = Array.isArray(data?.data) ? data.data : [];
    const meta = data?.meta || {};

    const chips = (meta.chips || []).map((c) => `<span class="chip">${esc(c.key)}: ${esc(c.value)}</span>`).join("");
    document.getElementById("ordersFilterChips").innerHTML = chips;

    const tableHtml = `
      <table class="data-table">
        <thead>
          <tr>
            <th class="sortable" data-sort="id">ID</th>
            <th class="sortable" data-sort="created_at">Sana</th>
            <th class="sortable" data-sort="first_name">Mijoz</th>
            <th>Kontakt</th>
            <th class="sortable" data-sort="payment">To'lov</th>
            <th class="sortable" data-sort="status">Status</th>
            <th>Manzil</th>
          </tr>
        </thead>
        <tbody>
          ${
            rows.length
              ? rows
                  .map(
                    (r) => `<tr>
                      <td>${esc(r.id)}</td>
                      <td>${esc(r.created_at)}</td>
                      <td>${esc(`${r.first_name || ""} ${r.last_name || ""}`.trim())}</td>
                      <td>${esc(r.contact)}</td>
                      <td>${esc(r.payment)}</td>
                      <td>${esc(r.status)}</td>
                      <td>${esc(r.address)}</td>
                    </tr>`
                  )
                  .join("")
              : `<tr><td colspan="7">Ma'lumot topilmadi</td></tr>`
          }
        </tbody>
      </table>
    `;
    document.getElementById("ordersTableWrap").innerHTML = tableHtml;
    document.querySelectorAll("#ordersTableWrap th.sortable").forEach((th) => {
      th.addEventListener("click", async () => {
        const field = th.dataset.sort;
        state.ordersTable.sortDir = nextSortDir(state.ordersTable.sortDir, field, state.ordersTable.sortBy);
        state.ordersTable.sortBy = field;
        state.ordersTable.page = 1;
        try {
          await loadOrdersTable();
        } catch (e) {
          setStatus(e.message, true);
        }
      });
    });
    document.getElementById("ordersPageInfo").textContent =
      `Sahifa ${meta.page || state.ordersTable.page} / ${meta.total_pages || 0} | Jami: ${meta.total || 0}`;
  }

  document.getElementById("ordersTableFilterForm").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const fd = new FormData(ev.target);
    state.ordersTable.page = 1;
    state.ordersTable.pageSize = Number(fd.get("page_size") || 20);
    state.ordersTable.sortBy = String(fd.get("sort_by") || "created_at");
    state.ordersTable.sortDir = String(fd.get("sort_dir") || "desc");
    state.ordersTable.filters = {
      status_q: fd.get("status_q"),
      payment: fd.get("payment"),
      contact: fd.get("contact"),
      first_name: fd.get("first_name"),
      date_from: fd.get("date_from"),
      date_to: fd.get("date_to"),
    };
    try {
      await loadOrdersTable();
      setStatus("Buyurtmalar jadvali yuklandi.");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("ordersPrevBtn").addEventListener("click", async () => {
    if (state.ordersTable.page <= 1) return;
    state.ordersTable.page -= 1;
    try {
      await loadOrdersTable();
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("ordersNextBtn").addEventListener("click", async () => {
    state.ordersTable.page += 1;
    try {
      await loadOrdersTable();
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("ordersTableExportBtn").addEventListener("click", async () => {
    try {
      const params = new URLSearchParams({
        sort_by: state.ordersTable.sortBy,
        sort_dir: state.ordersTable.sortDir,
      });
      Object.entries(state.ordersTable.filters).forEach(([k, v]) => {
        if (v !== undefined && v !== null && String(v).trim() !== "") params.set(k, String(v).trim());
      });
      const res = await fetch(`${state.baseUrl}/order/admin-table/export.csv?${params.toString()}`, {
        headers: getAuthHeader(),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = "orders_export.csv";
      link.click();
      setStatus("CSV export yuklab olindi.");
    } catch (e) {
      setStatus(e.message, true);
    }
  });
}

function bindProducts() {
  document.getElementById("listProductsBtn").addEventListener("click", async () => {
    try {
      out("productsOut", await api("/products"));
      setStatus("Products loaded.");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("searchProductsBtn").addEventListener("click", async () => {
    try {
      out("productsOut", await api("/products/search"));
      setStatus("Products search loaded.");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("listItemsBtn").addEventListener("click", async () => {
    try {
      out("productsOut", await api("/product-items"));
      setStatus("Product items loaded.");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("listDetailsBtn").addEventListener("click", async () => {
    try {
      out("productsOut", await api("/product-details"));
      setStatus("Product details loaded.");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("listPhotosBtn").addEventListener("click", async () => {
    try {
      out("productsOut", await api("/product-photos"));
      setStatus("Product photos loaded.");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("createProductForm").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const formData = toFormData(ev.target);
    if (formData.get("is_active") === "") {
      formData.delete("is_active");
    } else {
      formData.set("is_active", parseBool(formData.get("is_active")));
    }
    try {
      out("productsOut", await api("/products", { method: "POST", body: formData }));
      setStatus("Product created.");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  function normalizePhotoUrl(rawPhotoPath) {
    const raw = String(rawPhotoPath || "").trim();
    if (!raw) return "";
    if (raw.startsWith("http://") || raw.startsWith("https://")) return raw;
    if (raw.startsWith("/media/")) return `${state.baseUrl}${raw}`;
    if (raw.startsWith("media/")) return `${state.baseUrl}/${raw}`;
    return `${state.baseUrl}/media/${raw.replace(/^\/+/, "")}`;
  }

  function renderProductByIdCard(payload) {
    const wrap = document.getElementById("productByIdCard");
    if (!wrap) return;

    const product = payload?.product || {};
    const photos = Array.isArray(payload?.photos) ? payload.photos : [];
    const details = Array.isArray(payload?.details) ? payload.details : [];
    const items = Array.isArray(payload?.items) ? payload.items : [];

    const photoSrc = normalizePhotoUrl(
      photos.find((p) => p && p.photo)?.photo
    );

    const detailsHtml = details.length
      ? details
          .map(
            (d) =>
              `<li>${esc(d.name_uz || "-")} / ${esc(d.name_ru || "-")} / ${esc(d.name_eng || "-")}</li>`
          )
          .join("")
      : "<li>Detail topilmadi</li>";

    const itemsHtml = items.length
      ? items
          .map(
            (i) =>
              `<li>ID ${esc(i.id)} | color_id: ${esc(i.color_id)} | size_id: ${esc(i.size_id)} | count: ${esc(i.total_count)}</li>`
          )
          .join("")
      : "<li>Item topilmadi</li>";

    wrap.style.display = "block";
    wrap.innerHTML = `
      <div style="display:grid;grid-template-columns:minmax(180px,260px) 1fr;gap:14px;align-items:start">
        <div style="border:1px solid #334155;border-radius:10px;padding:8px;background:#0b1324;min-height:180px;display:flex;align-items:center;justify-content:center">
          ${
            photoSrc
              ? `<img src="${esc(photoSrc)}" alt="product photo" style="max-width:100%;max-height:260px;border-radius:8px;object-fit:contain" />`
              : `<span class="help">Rasm topilmadi</span>`
          }
        </div>
        <div>
          <h4 style="margin:0 0 8px">Mahsulot #${esc(product.id)}</h4>
          <div class="help" style="margin-bottom:8px">
            <strong>${esc(product.name_uz || "-")}</strong><br/>
            ${esc(product.name_ru || "-")}<br/>
            ${esc(product.name_eng || "-")}
          </div>
          <div class="help" style="margin-bottom:8px">
            Narx: ${esc(product.price)} | Holati: ${esc(product.is_active)} | Turi: ${esc(product.clothing_type)}
          </div>
          <div class="help" style="margin-bottom:8px">
            category_id: ${esc(product.category_id)} | collection_id: ${esc(product.collection_id)}
          </div>
          <div class="help" style="margin-bottom:6px">Tavsif:</div>
          <ul style="margin:0 0 10px 18px">
            <li>${esc(product.description_uz || "-")}</li>
            <li>${esc(product.description_ru || "-")}</li>
            <li>${esc(product.description_eng || "-")}</li>
          </ul>
          <div class="help" style="margin-bottom:6px">Detallar:</div>
          <ul style="margin:0 0 10px 18px">${detailsHtml}</ul>
          <div class="help" style="margin-bottom:6px">Variantlar:</div>
          <ul style="margin:0 0 0 18px">${itemsHtml}</ul>
        </div>
      </div>
    `;
  }

  document.getElementById("getProductByIdForm").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const fd = new FormData(ev.target);
    const productId = Number(fd.get("product_id"));
    if (!productId || productId < 1) {
      setStatus("product_id noto'g'ri", true);
      return;
    }

    try {
      const [productRes, photosRes, itemsRes, detailsRes] = await Promise.all([
        api(`/products/${productId}`),
        api(`/product-photos?product_id=${productId}`),
        api(`/product-items/product/${productId}`),
        api(`/product-details/product/${productId}`),
      ]);

      const product = productRes?.product;
      if (!product) {
        throw new Error("Mahsulot topilmadi");
      }

      const payload = {
        product,
        photos: Array.isArray(photosRes) ? photosRes : [],
        items: Array.isArray(itemsRes) ? itemsRes : [],
        details: Array.isArray(detailsRes) ? detailsRes : [],
      };

      renderProductByIdCard(payload);
      out("productsOut", payload);
      setStatus(`Mahsulot #${productId} muvaffaqiyatli topildi.`);
    } catch (e) {
      const wrap = document.getElementById("productByIdCard");
      if (wrap) {
        wrap.style.display = "block";
        wrap.innerHTML = `<div class="help">Topilmadi yoki xatolik: ${esc(e.message)}</div>`;
      }
      setStatus(e.message, true);
    }
  });

  async function loadProductsTable() {
    const params = new URLSearchParams({
      page: String(state.productsTable.page),
      page_size: String(state.productsTable.pageSize),
      sort_by: state.productsTable.sortBy,
      sort_dir: state.productsTable.sortDir,
    });
    Object.entries(state.productsTable.filters).forEach(([k, v]) => {
      if (v !== undefined && v !== null && String(v).trim() !== "") params.set(k, String(v).trim());
    });

    const data = await api(`/products/admin-table?${params.toString()}`);
    const rows = Array.isArray(data?.data) ? data.data : [];
    const meta = data?.meta || {};
    const chips = (meta.chips || []).map((c) => `<span class="chip">${esc(c.key)}: ${esc(c.value)}</span>`).join("");
    document.getElementById("productsFilterChips").innerHTML = chips;

    const tableHtml = `
      <table class="data-table">
        <thead>
          <tr>
            <th class="sortable" data-sort="id">ID</th>
            <th class="sortable" data-sort="name_uz">Nomi</th>
            <th class="sortable" data-sort="price">Narx</th>
            <th class="sortable" data-sort="is_active">Holati</th>
            <th class="sortable" data-sort="clothing_type">Turi</th>
            <th>Kategoriya</th>
            <th>Kolleksiya</th>
          </tr>
        </thead>
        <tbody>
          ${
            rows.length
              ? rows
                  .map(
                    (r) => `<tr>
                      <td>${esc(r.id)}</td>
                      <td>${esc(r.name_uz)}</td>
                      <td>${esc(r.price)}</td>
                      <td>${esc(r.is_active)}</td>
                      <td>${esc(r.clothing_type)}</td>
                      <td>${esc(r.category_id)}</td>
                      <td>${esc(r.collection_id)}</td>
                    </tr>`
                  )
                  .join("")
              : `<tr><td colspan="7">Ma'lumot topilmadi</td></tr>`
          }
        </tbody>
      </table>
    `;
    document.getElementById("productsTableWrap").innerHTML = tableHtml;
    document.querySelectorAll("#productsTableWrap th.sortable").forEach((th) => {
      th.addEventListener("click", async () => {
        const field = th.dataset.sort;
        state.productsTable.sortDir = nextSortDir(state.productsTable.sortDir, field, state.productsTable.sortBy);
        state.productsTable.sortBy = field;
        state.productsTable.page = 1;
        try {
          await loadProductsTable();
        } catch (e) {
          setStatus(e.message, true);
        }
      });
    });
    document.getElementById("productsPageInfo").textContent =
      `Sahifa ${meta.page || state.productsTable.page} / ${meta.total_pages || 0} | Jami: ${meta.total || 0}`;
  }

  document.getElementById("productsTableFilterForm").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const fd = new FormData(ev.target);
    state.productsTable.page = 1;
    state.productsTable.pageSize = Number(fd.get("page_size") || 20);
    state.productsTable.sortBy = String(fd.get("sort_by") || "id");
    state.productsTable.sortDir = String(fd.get("sort_dir") || "desc");
    state.productsTable.filters = {
      search: fd.get("search"),
      category_id: fd.get("category_id"),
      collection_id: fd.get("collection_id"),
      is_active: fd.get("is_active"),
      min_price: fd.get("min_price"),
      max_price: fd.get("max_price"),
      clothing_type: fd.get("clothing_type"),
    };
    try {
      await loadProductsTable();
      setStatus("Mahsulotlar jadvali yuklandi.");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("productsPrevBtn").addEventListener("click", async () => {
    if (state.productsTable.page <= 1) return;
    state.productsTable.page -= 1;
    try {
      await loadProductsTable();
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("productsNextBtn").addEventListener("click", async () => {
    state.productsTable.page += 1;
    try {
      await loadProductsTable();
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("productsTableExportBtn").addEventListener("click", async () => {
    try {
      const params = new URLSearchParams({
        sort_by: state.productsTable.sortBy,
        sort_dir: state.productsTable.sortDir,
      });
      Object.entries(state.productsTable.filters).forEach(([k, v]) => {
        if (v !== undefined && v !== null && String(v).trim() !== "") params.set(k, String(v).trim());
      });
      const res = await fetch(`${state.baseUrl}/products/admin-table/export.csv?${params.toString()}`, {
        headers: getAuthHeader(),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = "products_export.csv";
      link.click();
      setStatus("Mahsulotlar CSV export yuklab olindi.");
    } catch (e) {
      setStatus(e.message, true);
    }
  });
}

function bindLookups() {
  document.querySelectorAll(".lookup-list-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      try {
        out("lookupsOut", await api(`/${btn.dataset.list}`));
        setStatus(`${btn.dataset.list} loaded.`);
      } catch (e) {
        setStatus(e.message, true);
      }
    });
  });

  document.getElementById("createLookupForm").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const fd = new FormData(ev.target);
    const type = fd.get("type");
    const form = new FormData();
    if (type === "size") {
      form.set("name", fd.get("name"));
    } else if (type === "color") {
      const colorCode = String(fd.get("color_code") || "").trim();
      if (colorCode) form.set("color_code", colorCode);
    } else {
      ["name_uz", "name_ru", "name_eng"].forEach((k) => {
        const v = fd.get(k);
        if (v) form.set(k, v);
      });
    }
    try {
      out("lookupsOut", await api(`/${type}`, { method: "POST", body: form }));
      setStatus(`${type} created.`);
    } catch (e) {
      setStatus(e.message, true);
    }
  });
}

function bindPanelUsers() {
  document.getElementById("listUsersBtn").addEventListener("click", async () => {
    try {
      out("panelOut", await api("/panel/users"));
      setStatus("Panel users loaded.");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("meBtn").addEventListener("click", async () => {
    try {
      out("panelOut", await api("/panel/me"));
      setStatus("Current user loaded.");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("createOperatorForm").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const form = new FormData(ev.target);
    form.set("is_active", parseBool(form.get("is_active")));
    try {
      out("panelOut", await api("/panel/operators", { method: "POST", body: form }));
      setStatus("Operator/Admin created.");
    } catch (e) {
      setStatus(e.message, true);
    }
  });
}

function bindHistory() {
  const map = [
    ["historyOrdersBtn", "/history/orders"],
    ["historyProductsBtn", "/history/products"],
    ["historyLogsBtn", "/history/logs"],
    ["historySalesBtn", "/history/stats/sales"],
    ["historyDashBtn", "/history/stats/dashboard"],
  ];

  map.forEach(([btnId, path]) => {
    document.getElementById(btnId).addEventListener("click", async () => {
      try {
        out("historyOut", await api(path));
        setStatus(`${path} loaded.`);
      } catch (e) {
        setStatus(e.message, true);
      }
    });
  });
}

function bindDevTools() {
  document.getElementById("seedFakeForm").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const fd = new FormData(ev.target);
    const n = Number(fd.get("n") || 3);
    const clearBefore = String(fd.get("clear_before")) === "true";
    const qs = new URLSearchParams({
      n: String(Math.max(1, Math.min(20, n))),
      clear_before: String(clearBefore),
    });
    try {
      out("devOut", await api(`/system/dev/seed-fake?${qs.toString()}`, { method: "POST" }));
      setStatus("Fake data yaratildi.");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("clearFakeBtn").addEventListener("click", async () => {
    try {
      out("devOut", await api("/system/dev/clear-fake", { method: "DELETE" }));
      setStatus("Fake data tozalandi.");
    } catch (e) {
      setStatus(e.message, true);
    }
  });
}

function bindPayments() {
  document.getElementById("clickPrepareForm").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const fd = new FormData(ev.target);
    try {
      out(
        "paymentsOut",
        await api("/payments/click/prepare", {
          method: "POST",
          body: JSON.stringify({ order_id: Number(fd.get("order_id")) }),
        })
      );
      setStatus("Click prepare sent.");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("clickCompleteForm").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const fd = new FormData(ev.target);
    try {
      out(
        "paymentsOut",
        await api("/payments/click/complete", {
          method: "POST",
          body: JSON.stringify({
            order_id: Number(fd.get("order_id")),
            transaction_id: String(fd.get("transaction_id")),
            success: parseBool(fd.get("success")),
          }),
        })
      );
      setStatus("Click complete sent.");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("paymeCheckForm").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const fd = new FormData(ev.target);
    try {
      out(
        "paymentsOut",
        await api("/payments/payme/check", {
          method: "POST",
          body: JSON.stringify({ order_id: Number(fd.get("order_id")) }),
        })
      );
      setStatus("Payme check sent.");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("paymePerformForm").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const fd = new FormData(ev.target);
    try {
      out(
        "paymentsOut",
        await api("/payments/payme/perform", {
          method: "POST",
          body: JSON.stringify({
            order_id: Number(fd.get("order_id")),
            transaction_id: String(fd.get("transaction_id")),
            success: parseBool(fd.get("success")),
          }),
        })
      );
      setStatus("Payme perform sent.");
    } catch (e) {
      setStatus(e.message, true);
    }
  });
}

function bindExcel() {
  document.getElementById("downloadTemplateBtn").addEventListener("click", async () => {
    try {
      const res = await fetch(`${state.baseUrl}/excel/products/template`, {
        headers: getAuthHeader(),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = "products_import_template.xlsx";
      link.click();
      out("excelOut", "Shablon yuklab olindi.");
      setStatus("Excel shabloni yuklab olindi.");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("excelImportForm").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    try {
      out(
        "excelOut",
        await api("/excel/products/import", {
          method: "POST",
          body: new FormData(ev.target),
        })
      );
      setStatus("Excel import request sent.");
    } catch (e) {
      setStatus(e.message, true);
    }
  });
}

export function initLegacyAdminPanel() {
  fillAuthInputs();
  bindTabs();
  bindGlobalActions();
  bindDashboard();
  bindOrders();
  bindProducts();
  bindLookups();
  bindPanelUsers();
  bindHistory();
  bindDevTools();
  bindPayments();
  bindExcel();
}
