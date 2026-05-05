import { useState } from "react";
import { DashboardStats, BotSettings, StockMovements, LowStockAlerts } from "./components";

const ORDER_SORT_FIELDS = ["created_at", "id", "status", "payment", "first_name"];
const PRODUCT_SORT_FIELDS = ["id", "name_uz", "price", "is_active", "clothing_type"];

function pretty(value) {
  return typeof value === "string" ? value : JSON.stringify(value, null, 2);
}

function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [baseUrl, setBaseUrl] = useState(localStorage.getItem("admin_base_url") || window.location.origin);
  const [username, setUsername] = useState(localStorage.getItem("admin_username") || "");
  const [password, setPassword] = useState(localStorage.getItem("admin_password") || "");
  const [statusLine, setStatusLine] = useState("Tayyor. Auth ma'lumotlarini saqlang.");

  const [dashboardOut, setDashboardOut] = useState("");
  const [ordersOut, setOrdersOut] = useState("");
  const [productsOut, setProductsOut] = useState("");
  const [bannersOut, setBannersOut] = useState("");

  const [ordersRows, setOrdersRows] = useState([]);
  const [ordersMeta, setOrdersMeta] = useState({ page: 1, page_size: 20, total: 0, total_pages: 0, sort_by: "created_at", sort_dir: "desc" });
  const [ordersFilters, setOrdersFilters] = useState({ status_q: "", payment: "", contact: "", first_name: "", date_from: "", date_to: "" });

  const [productsRows, setProductsRows] = useState([]);
  const [productsMeta, setProductsMeta] = useState({ page: 1, page_size: 20, total: 0, total_pages: 0, sort_by: "id", sort_dir: "desc" });
  const [productsFilters, setProductsFilters] = useState({ search: "", category_id: "", collection_id: "", is_active: "", min_price: "", max_price: "", clothing_type: "" });

  const [productPreview, setProductPreview] = useState(null);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [banners, setBanners] = useState([]);
  const [categories, setCategories] = useState([]);
  const [collections, setCollections] = useState([]);
  const [categoriesOut, setCategoriesOut] = useState("");
  const [collectionsOut, setCollectionsOut] = useState("");
  const [colors, setColors] = useState([]);
  const [sizes, setSizes] = useState([]);
  const [colorsOut, setColorsOut] = useState("");
  const [sizesOut, setSizesOut] = useState("");
  const [showProductForm, setShowProductForm] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);

  const setOk = (msg) => setStatusLine(`OK: ${msg}`);
  const setErr = (msg) => setStatusLine(`Xato: ${msg}`);

  const getAuthHeader = () => {
    if (!username || !password) return {};
    return {
      Authorization: `Basic ${btoa(`${username}:${password}`)}`,
    };
  };

  const api = async (path, options = {}) => {
    const headers = {
      ...getAuthHeader(),
      ...(options.headers || {}),
    };

    if (options.body && !(options.body instanceof FormData) && !headers["Content-Type"]) {
      headers["Content-Type"] = "application/json";
    }

    const res = await fetch(`${baseUrl}${path}`, { ...options, headers });
    const contentType = res.headers.get("content-type") || "";
    const data = contentType.includes("application/json") ? await res.json() : await res.text();

    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${typeof data === "string" ? data : pretty(data)}`);
    }

    return data;
  };

  const saveAuth = () => {
    localStorage.setItem("admin_base_url", baseUrl);
    localStorage.setItem("admin_username", username);
    localStorage.setItem("admin_password", password);
    setOk("Auth ma'lumotlari saqlandi.");
  };

  const checkMe = async () => {
    try {
      const data = await api("/panel/me");
      setDashboardOut(pretty(data));
      setOk("Auth to'g'ri.");
    } catch (e) {
      setErr(e.message);
    }
  };

  const loadHealth = async () => {
    try {
      const [health, ready] = await Promise.all([api("/system/health"), api("/system/ready")]);
      setDashboardOut(pretty({ health, ready }));
      setOk("System holati yuklandi.");
    } catch (e) {
      setErr(e.message);
    }
  };

  const loadBootstrap = async () => {
    try {
      const data = await api("/panel/bootstrap");
      setDashboardOut(pretty(data));
      setOk("Bootstrap yuklandi.");
    } catch (e) {
      setErr(e.message);
    }
  };

  const loadOrdersTable = async (metaPatch = {}, filterPatch = null) => {
    const nextMeta = { ...ordersMeta, ...metaPatch };
    const nextFilters = filterPatch ?? ordersFilters;
    const params = new URLSearchParams({
      page: String(nextMeta.page),
      page_size: String(nextMeta.page_size),
      sort_by: nextMeta.sort_by,
      sort_dir: nextMeta.sort_dir,
    });
    Object.entries(nextFilters).forEach(([k, v]) => {
      if (String(v || "").trim() !== "") params.set(k, String(v).trim());
    });

    try {
      const data = await api(`/order/admin-table?${params.toString()}`);
      setOrdersRows(Array.isArray(data?.data) ? data.data : []);
      setOrdersMeta({ ...nextMeta, ...(data?.meta || {}) });
      setOrdersFilters(nextFilters);
      setOrdersOut(pretty(data));
      setOk("Buyurtmalar jadvali yuklandi.");
    } catch (e) {
      setErr(e.message);
    }
  };

  const loadProductsTable = async (metaPatch = {}, filterPatch = null) => {
    const nextMeta = { ...productsMeta, ...metaPatch };
    const nextFilters = filterPatch ?? productsFilters;
    const params = new URLSearchParams({
      page: String(nextMeta.page),
      page_size: String(nextMeta.page_size),
      sort_by: nextMeta.sort_by,
      sort_dir: nextMeta.sort_dir,
    });
    Object.entries(nextFilters).forEach(([k, v]) => {
      if (String(v || "").trim() !== "") params.set(k, String(v).trim());
    });

    try {
      const data = await api(`/products/admin-table?${params.toString()}`);
      setProductsRows(Array.isArray(data?.data) ? data.data : []);
      setProductsMeta({ ...nextMeta, ...(data?.meta || {}) });
      setProductsFilters(nextFilters);
      setProductsOut(pretty(data));
      setOk("Mahsulotlar jadvali yuklandi.");
    } catch (e) {
      setErr(e.message);
    }
  };

  const onFindProductById = async (event) => {
    event.preventDefault();
    const fd = new FormData(event.currentTarget);
    const productId = Number(fd.get("product_id"));
    if (!productId || productId < 1) {
      setErr("product_id noto'g'ri");
      return;
    }

    try {
      const [productRes, photosRes, itemsRes, detailsRes] = await Promise.all([
        api(`/products/${productId}`),
        api(`/product-photos?product_id=${productId}`),
        api(`/product-items/product/${productId}`),
        api(`/product-details/product/${productId}`),
      ]);

      const payload = {
        product: productRes?.product,
        photos: Array.isArray(photosRes) ? photosRes : [],
        items: Array.isArray(itemsRes) ? itemsRes : [],
        details: Array.isArray(detailsRes) ? detailsRes : [],
      };
      setProductPreview(payload);
      setProductsOut(pretty(payload));
      setOk(`Mahsulot #${productId} topildi.`);
    } catch (e) {
      setProductPreview(null);
      setErr(e.message);
    }
  };

  const normalizePhotoUrl = (photoValue) => {
    const raw = String(photoValue || "").trim();
    if (!raw) return "";
    if (raw.startsWith("http://") || raw.startsWith("https://")) return raw;
    if (raw.startsWith("/media/")) return `${baseUrl}${raw}`;
    if (raw.startsWith("media/")) return `${baseUrl}/${raw}`;
    return `${baseUrl}/media/${raw.replace(/^\/+/, "")}`;
  };

  const loadOrderDetails = async (orderId) => {
    try {
      const data = await api(`/order/${orderId}`);
      setSelectedOrder(data?.data || null);
      setOrdersOut(pretty(data));
      setOk(`Buyurtma #${orderId} yuklandi.`);
    } catch (e) {
      setSelectedOrder(null);
      setErr(e.message);
    }
  };

  const changeOrderStatus = async (orderId, newStatus) => {
    try {
      const formData = new FormData();
      formData.append("new_status", newStatus);
      await api(`/order/${orderId}/status`, { method: "PATCH", body: formData });
      setOk(`Buyurtma #${orderId} statusi o'zgartirildi: ${newStatus}`);
      await loadOrderDetails(orderId);
      await loadOrdersTable();
    } catch (e) {
      setErr(e.message);
    }
  };

  const confirmPayment = async (orderId) => {
    try {
      await api(`/order/${orderId}/confirm-payment`, {
        method: "POST",
        body: JSON.stringify({ next_status: "jarayonda" }),
      });
      setOk(`Buyurtma #${orderId} to'lovi tasdiqlandi.`);
      await loadOrderDetails(orderId);
      await loadOrdersTable();
    } catch (e) {
      setErr(e.message);
    }
  };

  const loadBanners = async () => {
    try {
      const data = await api("/banners");
      setBanners(data?.photos || []);
      setBannersOut(pretty(data));
      setOk("Bannerlar yuklandi.");
    } catch (e) {
      setErr(e.message);
    }
  };

  const uploadBanner = async (event) => {
    event.preventDefault();
    const fd = new FormData(event.currentTarget);
    const photo = fd.get("photo");
    if (!photo || !photo.name) {
      setErr("Rasm tanlang.");
      return;
    }

    try {
      await api("/banners", { method: "POST", body: fd });
      setOk("Banner yuklandi.");
      await loadBanners();
      event.currentTarget.reset();
    } catch (e) {
      setErr(e.message);
    }
  };

  const deleteBanner = async (photoId) => {
    if (!confirm(`Banner #${photoId} o'chirilsinmi?`)) return;
    try {
      await api(`/banners/${photoId}`, { method: "DELETE" });
      setOk(`Banner #${photoId} o'chirildi.`);
      await loadBanners();
    } catch (e) {
      setErr(e.message);
    }
  };

  const loadCategories = async () => {
    try {
      const data = await api("/categories");
      setCategories(Array.isArray(data) ? data : []);
      setCategoriesOut(pretty(data));
      setOk("Kategoriyalar yuklandi.");
    } catch (e) {
      setErr(e.message);
    }
  };

  const createCategory = async (event) => {
    event.preventDefault();
    const fd = new FormData(event.currentTarget);
    try {
      await api("/categories", { method: "POST", body: fd });
      setOk("Kategoriya yaratildi.");
      await loadCategories();
      event.currentTarget.reset();
    } catch (e) {
      setErr(e.message);
    }
  };

  const deleteCategory = async (categoryId) => {
    if (!confirm(`Kategoriya #${categoryId} o'chirilsinmi?`)) return;
    try {
      await api(`/categories/${categoryId}`, { method: "DELETE" });
      setOk(`Kategoriya #${categoryId} o'chirildi.`);
      await loadCategories();
    } catch (e) {
      setErr(e.message);
    }
  };

  const loadCollections = async () => {
    try {
      const data = await api("/collections");
      setCollections(Array.isArray(data) ? data : []);
      setCollectionsOut(pretty(data));
      setOk("Kolleksiyalar yuklandi.");
    } catch (e) {
      setErr(e.message);
    }
  };

  const createCollection = async (event) => {
    event.preventDefault();
    const fd = new FormData(event.currentTarget);
    try {
      await api("/collections", { method: "POST", body: fd });
      setOk("Kolleksiya yaratildi.");
      await loadCollections();
      event.currentTarget.reset();
    } catch (e) {
      setErr(e.message);
    }
  };

  const deleteCollection = async (collectionId) => {
    if (!confirm(`Kolleksiya #${collectionId} o'chirilsinmi?`)) return;
    try {
      await api(`/collections/${collectionId}`, { method: "DELETE" });
      setOk(`Kolleksiya #${collectionId} o'chirildi.`);
      await loadCollections();
    } catch (e) {
      setErr(e.message);
    }
  };

  const loadColors = async () => {
    try {
      const data = await api("/color");
      setColors(Array.isArray(data) ? data : []);
      setColorsOut(pretty(data));
      setOk("Ranglar yuklandi.");
    } catch (e) {
      setErr(e.message);
    }
  };

  const createColor = async (event) => {
    event.preventDefault();
    const fd = new FormData(event.currentTarget);
    try {
      await api("/color", { method: "POST", body: fd });
      setOk("Rang yaratildi.");
      await loadColors();
      event.currentTarget.reset();
    } catch (e) {
      setErr(e.message);
    }
  };

  const deleteColor = async (colorId) => {
    if (!confirm(`Rang #${colorId} o'chirilsinmi?`)) return;
    try {
      await api(`/color/${colorId}`, { method: "DELETE" });
      setOk(`Rang #${colorId} o'chirildi.`);
      await loadColors();
    } catch (e) {
      setErr(e.message);
    }
  };

  const loadSizes = async () => {
    try {
      const data = await api("/size");
      setSizes(Array.isArray(data) ? data : []);
      setSizesOut(pretty(data));
      setOk("O'lchamlar yuklandi.");
    } catch (e) {
      setErr(e.message);
    }
  };

  const createSize = async (event) => {
    event.preventDefault();
    const fd = new FormData(event.currentTarget);
    try {
      await api("/size", { method: "POST", body: fd });
      setOk("O'lcham yaratildi.");
      await loadSizes();
      event.currentTarget.reset();
    } catch (e) {
      setErr(e.message);
    }
  };

  const deleteSize = async (sizeId) => {
    if (!confirm(`O'lcham #${sizeId} o'chirilsinmi?`)) return;
    try {
      await api(`/size/${sizeId}`, { method: "DELETE" });
      setOk(`O'lcham #${sizeId} o'chirildi.`);
      await loadSizes();
    } catch (e) {
      setErr(e.message);
    }
  };

  const createProduct = async (event) => {
    event.preventDefault();
    const fd = new FormData(event.currentTarget);
    try {
      const result = await api("/products", { method: "POST", body: fd });
      setOk(`Mahsulot yaratildi. ID: ${result.id}`);
      setShowProductForm(false);
      await loadProductsTable();
      event.currentTarget.reset();
    } catch (e) {
      setErr(e.message);
    }
  };

  const updateProduct = async (event) => {
    event.preventDefault();
    if (!editingProduct) return;
    const fd = new FormData(event.currentTarget);
    try {
      await api(`/products/${editingProduct.id}`, { method: "PATCH", body: fd });
      setOk(`Mahsulot #${editingProduct.id} yangilandi.`);
      setEditingProduct(null);
      setShowProductForm(false);
      await loadProductsTable();
    } catch (e) {
      setErr(e.message);
    }
  };

  const deleteProduct = async (productId) => {
    if (!confirm(`Mahsulot #${productId} o'chirilsinmi?`)) return;
    try {
      await api(`/products/${productId}`, { method: "DELETE" });
      setOk(`Mahsulot #${productId} o'chirildi.`);
      await loadProductsTable();
    } catch (e) {
      setErr(e.message);
    }
  };

  const startEditProduct = async (productId) => {
    try {
      const data = await api(`/products/${productId}`);
      setEditingProduct(data?.product || null);
      setShowProductForm(true);
      setOk(`Mahsulot #${productId} tahrirlash rejimida.`);
    } catch (e) {
      setErr(e.message);
    }
  };

  return (
    <>
      <header className="topbar">
        <div>
          <h1>Textile Shop Admin (React)</h1>
          <p className="subtitle">API bilan to'g'ridan-to'g'ri ishlovchi yangi panel</p>
        </div>
        <div className="auth-row">
          <input value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} placeholder="Base URL" />
          <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Username" />
          <input value={password} type="password" onChange={(e) => setPassword(e.target.value)} placeholder="Password" />
          <button className="btn-primary" onClick={saveAuth}>Saqlash</button>
          <button onClick={checkMe}>Auth tekshirish</button>
        </div>
      </header>

      <main className="layout">
        <aside className="sidebar">
          <button className={`tab-btn ${activeTab === "dashboard" ? "active" : ""}`} onClick={() => setActiveTab("dashboard")}>Dashboard</button>
          <button className={`tab-btn ${activeTab === "orders" ? "active" : ""}`} onClick={() => setActiveTab("orders")}>Buyurtmalar</button>
          <button className={`tab-btn ${activeTab === "products" ? "active" : ""}`} onClick={() => setActiveTab("products")}>Mahsulotlar</button>
          <button className={`tab-btn ${activeTab === "banners" ? "active" : ""}`} onClick={() => setActiveTab("banners")}>Bannerlar</button>
          <button className={`tab-btn ${activeTab === "categories" ? "active" : ""}`} onClick={() => setActiveTab("categories")}>Kategoriyalar</button>
          <button className={`tab-btn ${activeTab === "collections" ? "active" : ""}`} onClick={() => setActiveTab("collections")}>Kolleksiyalar</button>
          <button className={`tab-btn ${activeTab === "colors" ? "active" : ""}`} onClick={() => setActiveTab("colors")}>Ranglar</button>
          <button className={`tab-btn ${activeTab === "sizes" ? "active" : ""}`} onClick={() => setActiveTab("sizes")}>O'lchamlar</button>
          <button className={`tab-btn ${activeTab === "statistics" ? "active" : ""}`} onClick={() => setActiveTab("statistics")}>📊 Statistika</button>
          <button className={`tab-btn ${activeTab === "stock" ? "active" : ""}`} onClick={() => setActiveTab("stock")}>📦 Ombor</button>
          <button className={`tab-btn ${activeTab === "alerts" ? "active" : ""}`} onClick={() => setActiveTab("alerts")}>⚠️ Ogohlantirishlar</button>
          <button className={`tab-btn ${activeTab === "bot-settings" ? "active" : ""}`} onClick={() => setActiveTab("bot-settings")}>🤖 Bot</button>
        </aside>

        <section className="content">
          <div id="statusLine" className="status-line">{statusLine}</div>

          {activeTab === "dashboard" && (
            <div className="card">
              <h2>Dashboard</h2>
              <div className="actions">
                <button onClick={loadHealth}>Sog'liq + Tayyorlik</button>
                <button onClick={loadBootstrap}>Bootstrap</button>
              </div>
              <pre className="output">{dashboardOut}</pre>
            </div>
          )}

          {activeTab === "statistics" && (
            <DashboardStats api={api} baseUrl={baseUrl} setOk={setOk} setErr={setErr} />
          )}

          {activeTab === "stock" && (
            <StockMovements api={api} setOk={setOk} setErr={setErr} />
          )}

          {activeTab === "alerts" && (
            <LowStockAlerts api={api} setOk={setOk} setErr={setErr} />
          )}

          {activeTab === "bot-settings" && (
            <BotSettings api={api} setOk={setOk} setErr={setErr} />
          )}

          {activeTab === "orders" && (
            <div className="card">
              <h2>Buyurtmalar (server-side)</h2>
              <form
                className="form"
                onSubmit={(e) => {
                  e.preventDefault();
                  const fd = new FormData(e.currentTarget);
                  const nextFilters = {
                    status_q: fd.get("status_q"),
                    payment: fd.get("payment"),
                    contact: fd.get("contact"),
                    first_name: fd.get("first_name"),
                    date_from: fd.get("date_from"),
                    date_to: fd.get("date_to"),
                  };
                  loadOrdersTable(
                    {
                      page: 1,
                      page_size: Number(fd.get("page_size") || 20),
                      sort_by: String(fd.get("sort_by") || "created_at"),
                      sort_dir: String(fd.get("sort_dir") || "desc"),
                    },
                    nextFilters,
                  );
                }}
              >
                <input name="status_q" placeholder="status" defaultValue={ordersFilters.status_q} />
                <input name="payment" placeholder="payment" defaultValue={ordersFilters.payment} />
                <input name="contact" placeholder="contact" defaultValue={ordersFilters.contact} />
                <input name="first_name" placeholder="first_name" defaultValue={ordersFilters.first_name} />
                <input name="date_from" placeholder="date_from YYYY-MM-DD" defaultValue={ordersFilters.date_from} />
                <input name="date_to" placeholder="date_to YYYY-MM-DD" defaultValue={ordersFilters.date_to} />
                <select name="sort_by" defaultValue={ordersMeta.sort_by}>
                  {ORDER_SORT_FIELDS.map((f) => (
                    <option key={f} value={f}>{f}</option>
                  ))}
                </select>
                <select name="sort_dir" defaultValue={ordersMeta.sort_dir}>
                  <option value="desc">desc</option>
                  <option value="asc">asc</option>
                </select>
                <input name="page_size" type="number" min="1" max="200" defaultValue={ordersMeta.page_size} />
                <button type="submit">Jadvalni yuklash</button>
              </form>

              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Sana</th>
                      <th>Mijoz</th>
                      <th>Kontakt</th>
                      <th>To'lov</th>
                      <th>Status</th>
                      <th>Amallar</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ordersRows.length ? ordersRows.map((r) => (
                      <tr key={r.id}>
                        <td>{r.id}</td>
                        <td>{r.created_at}</td>
                        <td>{`${r.first_name || ""} ${r.last_name || ""}`}</td>
                        <td>{r.contact}</td>
                        <td>{r.payment}</td>
                        <td>{r.status}</td>
                        <td>
                          <button onClick={() => loadOrderDetails(r.id)}>Ko'rish</button>
                        </td>
                      </tr>
                    )) : <tr><td colSpan="7">Ma'lumot yo'q</td></tr>}
                  </tbody>
                </table>
              </div>

              <div className="actions">
                <button onClick={() => loadOrdersTable({ page: Math.max(1, (ordersMeta.page || 1) - 1) })}>Oldingi</button>
                <button onClick={() => loadOrdersTable({ page: (ordersMeta.page || 1) + 1 })}>Keyingi</button>
                <span className="help">Sahifa {ordersMeta.page || 1} / {ordersMeta.total_pages || 0} | Jami: {ordersMeta.total || 0}</span>
              </div>

              {selectedOrder && (
                <div className="card">
                  <h3>Buyurtma #{selectedOrder.id} tafsilotlari</h3>
                  <div className="grid2">
                    <div>
                      <p><strong>Mijoz:</strong> {selectedOrder.first_name} {selectedOrder.last_name}</p>
                      <p><strong>Telefon:</strong> {selectedOrder.contact}</p>
                      <p><strong>Email:</strong> {selectedOrder.email_address || "—"}</p>
                      <p><strong>Manzil:</strong> {selectedOrder.address}</p>
                      <p><strong>Shahar:</strong> {selectedOrder.town_city}</p>
                      <p><strong>Mamlakat:</strong> {selectedOrder.country}</p>
                      <p><strong>Pochta indeksi:</strong> {selectedOrder.postcode_zip}</p>
                    </div>
                    <div>
                      <p><strong>Status:</strong> {selectedOrder.status}</p>
                      <p><strong>To'lov:</strong> {selectedOrder.payment}</p>
                      <p><strong>Sana:</strong> {selectedOrder.created_at}</p>
                      <div className="actions">
                        <select id="newStatus" defaultValue={selectedOrder.status}>
                          <option value="yangi">yangi</option>
                          <option value="to'landi">to'landi</option>
                          <option value="jarayonda">jarayonda</option>
                          <option value="tayyor">tayyor</option>
                          <option value="yetkazilmoqda">yetkazilmoqda</option>
                          <option value="yetkazildi">yetkazildi</option>
                          <option value="bekor qilindi">bekor qilindi</option>
                          <option value="vozvrat">vozvrat</option>
                        </select>
                        <button onClick={() => {
                          const newStatus = document.getElementById("newStatus").value;
                          changeOrderStatus(selectedOrder.id, newStatus);
                        }}>Statusni o'zgartirish</button>
                      </div>
                      {selectedOrder.status === "yangi" && (
                        <button className="btn-primary" onClick={() => confirmPayment(selectedOrder.id)}>
                          To'lovni tasdiqlash
                        </button>
                      )}
                    </div>
                  </div>

                  <h4>Mahsulotlar:</h4>
                  <div className="table-wrap">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Mahsulot ID</th>
                          <th>Nomi</th>
                          <th>Soni</th>
                          <th>Narx</th>
                          <th>Jami</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedOrder.order_items?.map((item) => (
                          <tr key={item.id}>
                            <td>{item.product_id}</td>
                            <td>{item.product?.name_uz || "—"}</td>
                            <td>{item.count}</td>
                            <td>{item.price}</td>
                            <td>{item.total}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <button onClick={() => setSelectedOrder(null)}>Yopish</button>
                </div>
              )}

              <pre className="output">{ordersOut}</pre>
            </div>
          )}

          {activeTab === "products" && (
            <div className="card">
              <h2>Mahsulotlar (server-side)</h2>
              <div className="actions">
                <button className="btn-primary" onClick={() => { setShowProductForm(true); setEditingProduct(null); }}>
                  Yangi mahsulot qo'shish
                </button>
              </div>

              {showProductForm && (
                <div className="card">
                  <h3>{editingProduct ? `Mahsulot #${editingProduct.id} tahrirlash` : "Yangi mahsulot yaratish"}</h3>
                  <form className="form" onSubmit={editingProduct ? updateProduct : createProduct}>
                    <input name="name_uz" placeholder="Nomi (UZ)" defaultValue={editingProduct?.name_uz || ""} required />
                    <input name="name_ru" placeholder="Nomi (RU)" defaultValue={editingProduct?.name_ru || ""} required />
                    <input name="name_eng" placeholder="Nomi (ENG)" defaultValue={editingProduct?.name_eng || ""} required />
                    <textarea name="description_uz" placeholder="Tavsif (UZ)" defaultValue={editingProduct?.description_uz || ""} required rows="3"></textarea>
                    <textarea name="description_ru" placeholder="Tavsif (RU)" defaultValue={editingProduct?.description_ru || ""} required rows="3"></textarea>
                    <textarea name="description_eng" placeholder="Tavsif (ENG)" defaultValue={editingProduct?.description_eng || ""} required rows="3"></textarea>
                    <input name="price" type="number" placeholder="Narx" defaultValue={editingProduct?.price || ""} required />
                    <input name="category_id" type="number" placeholder="Kategoriya ID" defaultValue={editingProduct?.category_id || ""} required />
                    <input name="collection_id" type="number" placeholder="Kolleksiya ID" defaultValue={editingProduct?.collection_id || ""} required />
                    <select name="clothing_type" defaultValue={editingProduct?.clothing_type || "erkak"}>
                      <option value="erkak">erkak</option>
                      <option value="ayol">ayol</option>
                    </select>
                    <select name="is_active" defaultValue={editingProduct?.is_active !== false ? "true" : "false"}>
                      <option value="true">Faol</option>
                      <option value="false">Faol emas</option>
                    </select>
                    <input name="photo" type="file" accept="image/*" />
                    <div className="actions">
                      <button type="submit" className="btn-primary">{editingProduct ? "Yangilash" : "Yaratish"}</button>
                      <button type="button" onClick={() => { setShowProductForm(false); setEditingProduct(null); }}>Bekor qilish</button>
                    </div>
                  </form>
                </div>
              )}

              <form
                className="form"
                onSubmit={(e) => {
                  e.preventDefault();
                  const fd = new FormData(e.currentTarget);
                  const nextFilters = {
                    search: fd.get("search"),
                    category_id: fd.get("category_id"),
                    collection_id: fd.get("collection_id"),
                    is_active: fd.get("is_active"),
                    min_price: fd.get("min_price"),
                    max_price: fd.get("max_price"),
                    clothing_type: fd.get("clothing_type"),
                  };
                  loadProductsTable(
                    {
                      page: 1,
                      page_size: Number(fd.get("page_size") || 20),
                      sort_by: String(fd.get("sort_by") || "id"),
                      sort_dir: String(fd.get("sort_dir") || "desc"),
                    },
                    nextFilters,
                  );
                }}
              >
                <input name="search" placeholder="search" defaultValue={productsFilters.search} />
                <input name="category_id" type="number" placeholder="category_id" defaultValue={productsFilters.category_id} />
                <input name="collection_id" type="number" placeholder="collection_id" defaultValue={productsFilters.collection_id} />
                <select name="is_active" defaultValue={productsFilters.is_active}>
                  <option value="">is_active (barchasi)</option>
                  <option value="true">true</option>
                  <option value="false">false</option>
                </select>
                <input name="min_price" type="number" placeholder="min_price" defaultValue={productsFilters.min_price} />
                <input name="max_price" type="number" placeholder="max_price" defaultValue={productsFilters.max_price} />
                <select name="clothing_type" defaultValue={productsFilters.clothing_type}>
                  <option value="">clothing_type (barchasi)</option>
                  <option value="erkak">erkak</option>
                  <option value="ayol">ayol</option>
                </select>
                <select name="sort_by" defaultValue={productsMeta.sort_by}>
                  {PRODUCT_SORT_FIELDS.map((f) => (
                    <option key={f} value={f}>{f}</option>
                  ))}
                </select>
                <select name="sort_dir" defaultValue={productsMeta.sort_dir}>
                  <option value="desc">desc</option>
                  <option value="asc">asc</option>
                </select>
                <input name="page_size" type="number" min="1" max="200" defaultValue={productsMeta.page_size} />
                <button type="submit">Jadvalni yuklash</button>
              </form>

              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Nomi</th>
                      <th>Narx</th>
                      <th>Holati</th>
                      <th>Turi</th>
                      <th>Amallar</th>
                    </tr>
                  </thead>
                  <tbody>
                    {productsRows.length ? productsRows.map((r) => (
                      <tr key={r.id}>
                        <td>{r.id}</td>
                        <td>{r.name_uz}</td>
                        <td>{r.price}</td>
                        <td>{String(r.is_active)}</td>
                        <td>{r.clothing_type}</td>
                        <td>
                          <button onClick={() => startEditProduct(r.id)}>Tahrirlash</button>
                          <button onClick={() => deleteProduct(r.id)}>O'chirish</button>
                        </td>
                      </tr>
                    )) : <tr><td colSpan="6">Ma'lumot yo'q</td></tr>}
                  </tbody>
                </table>
              </div>

              <div className="actions">
                <button onClick={() => loadProductsTable({ page: Math.max(1, (productsMeta.page || 1) - 1) })}>Oldingi</button>
                <button onClick={() => loadProductsTable({ page: (productsMeta.page || 1) + 1 })}>Keyingi</button>
                <span className="help">Sahifa {productsMeta.page || 1} / {productsMeta.total_pages || 0} | Jami: {productsMeta.total || 0}</span>
              </div>

              <div className="grid2">
                <div className="card">
                  <h3>ID bo'yicha tekshirish</h3>
                  <form className="form" onSubmit={onFindProductById}>
                    <input name="product_id" type="number" min="1" required placeholder="product_id" />
                    <button type="submit">Topish</button>
                  </form>
                </div>

                {productPreview?.product && (
                  <div className="card">
                    <h3>Mahsulot preview</h3>
                    <div className="table-wrap" style={{ padding: 12 }}>
                      {productPreview.photos?.[0]?.photo ? (
                        <img
                          src={normalizePhotoUrl(productPreview.photos[0].photo)}
                          alt="product"
                          style={{ maxWidth: "100%", maxHeight: 260, objectFit: "contain", borderRadius: 8 }}
                        />
                      ) : (
                        <p className="help">Rasm topilmadi</p>
                      )}
                      <p><strong>{productPreview.product.name_uz}</strong></p>
                      <p className="help">ID: {productPreview.product.id}</p>
                      <p className="help">Narx: {productPreview.product.price}</p>
                    </div>
                  </div>
                )}
              </div>

              <pre className="output">{productsOut}</pre>
            </div>
          )}

          {activeTab === "banners" && (
            <div className="card">
              <h2>Bannerlar</h2>
              <div className="actions">
                <button onClick={loadBanners}>Bannerlarni yuklash</button>
              </div>

              <form className="form" onSubmit={uploadBanner}>
                <h3>Yangi banner qo'shish</h3>
                <input name="photo" type="file" accept="image/*" required />
                <button type="submit" className="btn-primary">Yuklash</button>
              </form>

              <div className="grid2">
                {banners.map((banner) => (
                  <div key={banner.id} className="card">
                    <img
                      src={normalizePhotoUrl(banner.photo)}
                      alt={`Banner ${banner.id}`}
                      style={{ width: "100%", height: 200, objectFit: "cover", borderRadius: 8 }}
                    />
                    <p className="help">ID: {banner.id}</p>
                    <button onClick={() => deleteBanner(banner.id)}>O'chirish</button>
                  </div>
                ))}
              </div>

              {banners.length === 0 && <p className="help">Bannerlar topilmadi. "Bannerlarni yuklash" tugmasini bosing.</p>}

              <pre className="output">{bannersOut}</pre>
            </div>
          )}

          {activeTab === "categories" && (
            <div className="card">
              <h2>Kategoriyalar</h2>
              <div className="actions">
                <button onClick={loadCategories}>Kategoriyalarni yuklash</button>
              </div>

              <form className="form" onSubmit={createCategory}>
                <h3>Yangi kategoriya qo'shish</h3>
                <input name="name_uz" placeholder="Nomi (UZ)" required />
                <input name="name_ru" placeholder="Nomi (RU)" required />
                <input name="name_eng" placeholder="Nomi (ENG)" required />
                <button type="submit" className="btn-primary">Yaratish</button>
              </form>

              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Nomi (UZ)</th>
                      <th>Nomi (RU)</th>
                      <th>Nomi (ENG)</th>
                      <th>Amallar</th>
                    </tr>
                  </thead>
                  <tbody>
                    {categories.length ? categories.map((cat) => (
                      <tr key={cat.id}>
                        <td>{cat.id}</td>
                        <td>{cat.name_uz}</td>
                        <td>{cat.name_ru}</td>
                        <td>{cat.name_eng}</td>
                        <td>
                          <button onClick={() => deleteCategory(cat.id)}>O'chirish</button>
                        </td>
                      </tr>
                    )) : <tr><td colSpan="5">Ma'lumot yo'q</td></tr>}
                  </tbody>
                </table>
              </div>

              <pre className="output">{categoriesOut}</pre>
            </div>
          )}

          {activeTab === "collections" && (
            <div className="card">
              <h2>Kolleksiyalar</h2>
              <div className="actions">
                <button onClick={loadCollections}>Kolleksiyalarni yuklash</button>
              </div>

              <form className="form" onSubmit={createCollection}>
                <h3>Yangi kolleksiya qo'shish</h3>
                <input name="name_uz" placeholder="Nomi (UZ)" required />
                <input name="name_ru" placeholder="Nomi (RU)" required />
                <input name="name_eng" placeholder="Nomi (ENG)" required />
                <button type="submit" className="btn-primary">Yaratish</button>
              </form>

              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Nomi (UZ)</th>
                      <th>Nomi (RU)</th>
                      <th>Nomi (ENG)</th>
                      <th>Amallar</th>
                    </tr>
                  </thead>
                  <tbody>
                    {collections.length ? collections.map((col) => (
                      <tr key={col.id}>
                        <td>{col.id}</td>
                        <td>{col.name_uz}</td>
                        <td>{col.name_ru}</td>
                        <td>{col.name_eng}</td>
                        <td>
                          <button onClick={() => deleteCollection(col.id)}>O'chirish</button>
                        </td>
                      </tr>
                    )) : <tr><td colSpan="5">Ma'lumot yo'q</td></tr>}
                  </tbody>
                </table>
              </div>

              <pre className="output">{collectionsOut}</pre>
            </div>
          )}

          {activeTab === "colors" && (
            <div className="card">
              <h2>Ranglar</h2>
              <div className="actions">
                <button onClick={loadColors}>Ranglarni yuklash</button>
              </div>

              <form className="form" onSubmit={createColor}>
                <h3>Yangi rang qo'shish</h3>
                <input name="color_code" placeholder="#RRGGBB (masalan: #FF0000)" pattern="^#[0-9A-Fa-f]{6}$" required />
                <button type="submit" className="btn-primary">Yaratish</button>
              </form>

              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Rang kodi</th>
                      <th>Namuna</th>
                      <th>Amallar</th>
                    </tr>
                  </thead>
                  <tbody>
                    {colors.length ? colors.map((color) => (
                      <tr key={color.id}>
                        <td>{color.id}</td>
                        <td>{color.color_code}</td>
                        <td>
                          <div style={{ width: 40, height: 40, backgroundColor: color.color_code, borderRadius: 8, border: "1px solid #555" }}></div>
                        </td>
                        <td>
                          <button onClick={() => deleteColor(color.id)}>O'chirish</button>
                        </td>
                      </tr>
                    )) : <tr><td colSpan="4">Ma'lumot yo'q</td></tr>}
                  </tbody>
                </table>
              </div>

              <pre className="output">{colorsOut}</pre>
            </div>
          )}

          {activeTab === "sizes" && (
            <div className="card">
              <h2>O'lchamlar</h2>
              <div className="actions">
                <button onClick={loadSizes}>O'lchamlarni yuklash</button>
              </div>

              <form className="form" onSubmit={createSize}>
                <h3>Yangi o'lcham qo'shish</h3>
                <input name="name" placeholder="Nomi (S, M, L, XL, 42, 44...)" required />
                <button type="submit" className="btn-primary">Yaratish</button>
              </form>

              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Nomi</th>
                      <th>Amallar</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sizes.length ? sizes.map((size) => (
                      <tr key={size.id}>
                        <td>{size.id}</td>
                        <td>{size.name}</td>
                        <td>
                          <button onClick={() => deleteSize(size.id)}>O'chirish</button>
                        </td>
                      </tr>
                    )) : <tr><td colSpan="3">Ma'lumot yo'q</td></tr>}
                  </tbody>
                </table>
              </div>

              <pre className="output">{sizesOut}</pre>
            </div>
          )}
        </section>
      </main>
    </>
  );
}

export default App;
