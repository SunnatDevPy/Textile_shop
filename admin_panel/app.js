const state = {
  baseUrl: localStorage.getItem("admin_base_url") || window.location.origin,
  username: localStorage.getItem("admin_username") || "",
  password: localStorage.getItem("admin_password") || "",
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
  setStatus("Auth saved.");
}

function toFormData(form) {
  return new FormData(form);
}

function parseBool(v) {
  return String(v).toLowerCase() === "true";
}

function bindGlobalActions() {
  document.getElementById("saveAuthBtn").addEventListener("click", saveAuth);
  document.getElementById("checkMeBtn").addEventListener("click", async () => {
    try {
      const data = await api("/panel/me");
      setStatus("Auth is valid.");
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
      const data = await api("/history/stats/dashboard");
      out("dashboardOut", data);
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
      const data = await api("/frontend/bootstrap");
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
      out("excelOut", "Template downloaded.");
      setStatus("Excel template downloaded.");
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

function init() {
  fillAuthInputs();
  bindTabs();
  bindGlobalActions();
  bindDashboard();
  bindOrders();
  bindProducts();
  bindLookups();
  bindPanelUsers();
  bindHistory();
  bindPayments();
  bindExcel();
}

init();
