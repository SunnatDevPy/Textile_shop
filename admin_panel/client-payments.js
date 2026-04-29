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

function auth() {
  if (!state.username || !state.password) return {};
  return { Authorization: "Basic " + btoa(`${state.username}:${state.password}`) };
}

async function api(path, method = "GET", body = undefined) {
  const headers = { ...auth() };
  if (body && !(body instanceof FormData)) headers["Content-Type"] = "application/json";
  const res = await fetch(`${state.baseUrl}${path}`, { method, headers, body });
  const ct = res.headers.get("content-type") || "";
  const data = ct.includes("application/json") ? await res.json() : await res.text();
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${typeof data === "string" ? data : pretty(data)}`);
  return data;
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

  document.getElementById("loadPaymentKpiBtn").addEventListener("click", async () => {
    try {
      out("paymentKpiOut", await api("/history/stats/sales"));
      setStatus("Payment KPI yuklandi");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("orderPaymentSearchForm").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const fd = new FormData(ev.target);
    const qs = new URLSearchParams();
    if (fd.get("payment")) qs.set("payment", fd.get("payment"));
    if (fd.get("status_q")) qs.set("status_q", fd.get("status_q"));
    try {
      out("orderSearchOut", await api(`/order/search?${qs.toString()}`));
      setStatus("Order payment qidiruvi bajarildi");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("clickPrepareForm").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const fd = new FormData(ev.target);
    try {
      out("paymentOpsOut", await api("/payments/click/prepare", "POST", JSON.stringify({ order_id: Number(fd.get("order_id")) })));
      setStatus("Click prepare yuborildi");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("clickCompleteForm").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const fd = new FormData(ev.target);
    try {
      out(
        "paymentOpsOut",
        await api(
          "/payments/click/complete",
          "POST",
          JSON.stringify({
            order_id: Number(fd.get("order_id")),
            transaction_id: String(fd.get("transaction_id")),
            success: true,
          })
        )
      );
      setStatus("Click complete yuborildi");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("paymeCheckForm").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const fd = new FormData(ev.target);
    try {
      out("paymentOpsOut", await api("/payments/payme/check", "POST", JSON.stringify({ order_id: Number(fd.get("order_id")) })));
      setStatus("Payme check yuborildi");
    } catch (e) {
      setStatus(e.message, true);
    }
  });

  document.getElementById("paymePerformForm").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const fd = new FormData(ev.target);
    try {
      out(
        "paymentOpsOut",
        await api(
          "/payments/payme/perform",
          "POST",
          JSON.stringify({
            order_id: Number(fd.get("order_id")),
            transaction_id: String(fd.get("transaction_id")),
            success: true,
          })
        )
      );
      setStatus("Payme perform yuborildi");
    } catch (e) {
      setStatus(e.message, true);
    }
  });
}

init();
