// Admin Panel - Yangi funksiyalar uchun qo'shimcha komponentlar

import { useState, useEffect } from "react";

// Dashboard Statistics Component
export function DashboardStats({ api, baseUrl, setOk, setErr }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadStats = async () => {
    setLoading(true);
    try {
      const data = await api("/dashboard/statistics");
      setStats(data);
      setOk("Dashboard statistikasi yuklandi");
    } catch (e) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
  }, []);

  if (loading) return <div className="card"><p>Yuklanmoqda...</p></div>;
  if (!stats) return <div className="card"><button onClick={loadStats}>Statistikani yuklash</button></div>;

  return (
    <div className="dashboard-stats">
      <div className="stats-grid">
        <div className="stat-card">
          <h3>📊 Bugun</h3>
          <p className="stat-value">{stats.today.orders_count}</p>
          <p className="stat-label">Buyurtmalar</p>
          <p className="stat-value">{(stats.today.revenue || 0).toLocaleString()} UZS</p>
          <p className="stat-label">Daromad</p>
        </div>

        <div className="stat-card">
          <h3>📈 Hafta</h3>
          <p className="stat-value">{stats.week.orders_count}</p>
          <p className="stat-label">Buyurtmalar</p>
          <p className="stat-value">{(stats.week.revenue || 0).toLocaleString()} UZS</p>
          <p className="stat-label">Daromad</p>
        </div>

        <div className="stat-card">
          <h3>📅 Oy</h3>
          <p className="stat-value">{stats.month.orders_count}</p>
          <p className="stat-label">Buyurtmalar</p>
          <p className="stat-value">{(stats.month.revenue || 0).toLocaleString()} UZS</p>
          <p className="stat-label">Daromad</p>
          <p className="stat-growth" style={{ color: stats.month.growth_percent >= 0 ? '#4ade80' : '#f87171' }}>
            {stats.month.growth_percent >= 0 ? '↑' : '↓'} {Math.abs(stats.month.growth_percent)}%
          </p>
        </div>

        <div className="stat-card">
          <h3>📦 Ombor</h3>
          <p className="stat-value">{stats.inventory.low_stock_count}</p>
          <p className="stat-label">Kam qolgan</p>
          <p className="stat-value">{stats.inventory.out_of_stock_count}</p>
          <p className="stat-label">Tugagan</p>
          <p className="stat-value">{(stats.inventory.total_value || 0).toLocaleString()} UZS</p>
          <p className="stat-label">Jami qiymat</p>
        </div>
      </div>

      {stats.week.top_products && stats.week.top_products.length > 0 && (
        <div className="card" style={{ marginTop: 20 }}>
          <h3>🏆 TOP mahsulotlar (hafta)</h3>
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Mahsulot</th>
                  <th>Sotildi</th>
                  <th>Daromad</th>
                </tr>
              </thead>
              <tbody>
                {stats.week.top_products.map((p) => (
                  <tr key={p.product_id}>
                    <td>{p.name}</td>
                    <td>{p.total_sold}</td>
                    <td>{(p.total_revenue || 0).toLocaleString()} UZS</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {stats.inventory.low_stock_items && stats.inventory.low_stock_items.length > 0 && (
        <div className="card" style={{ marginTop: 20 }}>
          <h3>⚠️ Kam qolgan mahsulotlar</h3>
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Mahsulot</th>
                  <th>Qoldiq</th>
                  <th>Minimal</th>
                </tr>
              </thead>
              <tbody>
                {stats.inventory.low_stock_items.map((item) => (
                  <tr key={item.id}>
                    <td>{item.product_name}</td>
                    <td style={{ color: '#f87171' }}>{item.total_count}</td>
                    <td>{item.min_stock_level}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

// Bot Settings Component
export function BotSettings({ api, setOk, setErr }) {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [gettingGroups, setGettingGroups] = useState(false);
  const [groups, setGroups] = useState([]);

  const loadSettings = async () => {
    setLoading(true);
    try {
      const data = await api("/bot-settings/");
      setSettings(data);
      setOk("Bot sozlamalari yuklandi");
    } catch (e) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const payload = {
      bot_token: fd.get("bot_token") || null,
      group_ids: fd.get("group_ids") || null,
      is_enabled: fd.get("is_enabled") === "on",
      notify_new_orders: fd.get("notify_new_orders") === "on",
      notify_low_stock: fd.get("notify_low_stock") === "on",
      notify_payment: fd.get("notify_payment") === "on",
    };

    try {
      const data = await api("/bot-settings/", {
        method: "PUT",
        body: JSON.stringify(payload),
      });
      setSettings(data.settings);
      setOk("Bot sozlamalari saqlandi");
    } catch (e) {
      setErr(e.message);
    }
  };

  const testBot = async () => {
    setTesting(true);
    try {
      const data = await api("/bot-settings/test", { method: "POST" });
      if (data.success) {
        setOk(`Bot ishlayapti: @${data.bot_info.username}`);
      } else {
        setErr(data.error || "Bot ulanmadi");
      }
    } catch (e) {
      setErr(e.message);
    } finally {
      setTesting(false);
    }
  };

  const getGroupIds = async () => {
    setGettingGroups(true);
    try {
      const data = await api("/bot-settings/get-updates");
      if (data.success) {
        setGroups(data.groups || []);
        if (data.groups && data.groups.length > 0) {
          setOk(`${data.groups.length} ta guruh topildi`);
        } else {
          setErr("Guruhlar topilmadi. Guruhda /start yoki biror xabar yuboring va qayta urinib ko'ring");
        }
      } else {
        setErr(data.error || "Xatolik yuz berdi");
      }
    } catch (e) {
      setErr(e.message);
    } finally {
      setGettingGroups(false);
    }
  };

  const copyGroupId = (chatId) => {
    navigator.clipboard.writeText(chatId);
    setOk(`Group ID nusxalandi: ${chatId}`);
  };

  useEffect(() => {
    loadSettings();
  }, []);

  if (loading) return <div className="card"><p>Yuklanmoqda...</p></div>;
  if (!settings) return <div className="card"><button onClick={loadSettings}>Sozlamalarni yuklash</button></div>;

  return (
    <div>
      <div className="card" style={{ marginBottom: 20, background: 'rgba(59, 130, 246, 0.1)', borderColor: '#3b82f6' }}>
        <h3>📖 Qo'llanma: Bot Sozlash</h3>

        <div style={{ marginBottom: 16 }}>
          <h4>1️⃣ Bot Token Olish:</h4>
          <ol style={{ marginLeft: 20, color: '#9cb2da' }}>
            <li>Telegram da <strong>@BotFather</strong> ni oching</li>
            <li><code>/newbot</code> buyrug'ini yuboring</li>
            <li>Bot nomini kiriting (masalan: <em>Textile Shop Bot</em>)</li>
            <li>Bot username kiriting (masalan: <em>textile_shop_bot</em>)</li>
            <li>BotFather sizga <strong>token</strong> beradi</li>
            <li>Tokenni pastdagi "Bot Token" maydoniga qo'ying</li>
          </ol>
        </div>

        <div style={{ marginBottom: 16 }}>
          <h4>2️⃣ Group ID Olish:</h4>
          <ol style={{ marginLeft: 20, color: '#9cb2da' }}>
            <li>Telegram da yangi <strong>guruh</strong> yarating</li>
            <li>Botni guruhga <strong>admin</strong> qilib qo'shing</li>
            <li>Guruhda <code>/start</code> yoki biror xabar yuboring</li>
            <li>Pastdagi <strong>"🔍 Group ID Olish"</strong> tugmasini bosing</li>
            <li>Topilgan guruhlardan kerakli guruhni tanlang</li>
            <li>"📋 Nusxalash" tugmasini bosib, Group ID ni yuqoridagi maydoniga qo'ying</li>
          </ol>
          <p style={{ color: '#60a5fa', fontSize: 13, marginTop: 8 }}>
            💡 <strong>Maslahat:</strong> Group ID manfiy son bo'ladi (masalan: -1001234567890)
          </p>
        </div>

        <div style={{ marginBottom: 16 }}>
          <h4>3️⃣ Ko'p Guruh Uchun:</h4>
          <p style={{ color: '#9cb2da', fontSize: 13 }}>
            Bir nechta guruhga xabar yuborish uchun Group ID larni <strong>vergul bilan ajrating</strong>:
            <br />
            <code style={{ background: '#0f1729', padding: '4px 8px', borderRadius: 4, marginTop: 4, display: 'inline-block' }}>
              -1001234567890, -1009876543210, -1005555555555
            </code>
          </p>
        </div>
      </div>

      <div className="card">
        <h2>🤖 Telegram Bot Sozlamalari</h2>
        <form className="form" onSubmit={saveSettings}>
          <div className="form-group">
            <label>Bot Token</label>
            <input
              name="bot_token"
              type="text"
              defaultValue={settings.bot_token || ""}
              placeholder="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
            />
            <p className="help">BotFather dan olingan token</p>
          </div>

          <div className="form-group">
            <label>Group IDs</label>
            <input
              name="group_ids"
              type="text"
              defaultValue={settings.group_ids || ""}
              placeholder="-1001234567890, -1009876543210"
            />
            <p className="help">Vergul bilan ajratilgan group chat ID lar (manfiy sonlar)</p>
            <button type="button" onClick={getGroupIds} disabled={gettingGroups} style={{ marginTop: 8 }}>
              {gettingGroups ? "⏳ Yuklanmoqda..." : "🔍 Group ID Olish"}
            </button>
          </div>

          {groups.length > 0 && (
            <div className="card" style={{ marginTop: 12, background: 'rgba(34, 197, 94, 0.1)', borderColor: '#22c55e' }}>
              <h4>✅ Topilgan Guruhlar:</h4>
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Guruh Nomi</th>
                      <th>Chat ID</th>
                      <th>Amal</th>
                    </tr>
                  </thead>
                  <tbody>
                    {groups.map((group, idx) => (
                      <tr key={idx}>
                        <td>{group.title}</td>
                        <td><code>{group.chat_id}</code></td>
                        <td>
                          <button type="button" onClick={() => copyGroupId(group.chat_id)}>
                            📋 Nusxalash
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="help" style={{ marginTop: 8 }}>
                💡 "Nusxalash" tugmasini bosib, Group ID ni yuqoridagi "Group IDs" maydoniga qo'ying
              </p>
            </div>
          )}

          <div className="form-group">
            <label>
              <input
                name="is_enabled"
                type="checkbox"
                defaultChecked={settings.is_enabled}
              />
              {" "}Bot yoqilgan
            </label>
          </div>

          <div className="form-group">
            <label>
              <input
                name="notify_new_orders"
                type="checkbox"
                defaultChecked={settings.notify_new_orders}
              />
              {" "}Yangi buyurtmalar haqida xabar berish
            </label>
          </div>

          <div className="form-group">
            <label>
              <input
                name="notify_low_stock"
                type="checkbox"
                defaultChecked={settings.notify_low_stock}
              />
              {" "}Kam qolgan mahsulotlar haqida xabar berish
            </label>
          </div>

          <div className="form-group">
            <label>
              <input
                name="notify_payment"
                type="checkbox"
                defaultChecked={settings.notify_payment}
              />
              {" "}To'lovlar haqida xabar berish
            </label>
          </div>

          <div className="actions">
            <button type="submit" className="btn-primary">💾 Saqlash</button>
            <button type="button" onClick={testBot} disabled={testing}>
              {testing ? "⏳ Tekshirilmoqda..." : "✅ Bot ulanishini test qilish"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Stock Movements Component
export function StockMovements({ api, setOk, setErr }) {
  const [movements, setMovements] = useState([]);
  const [stats, setStats] = useState(null);

  const loadMovements = async () => {
    try {
      const data = await api("/stock-movements/?limit=50");
      setMovements(data);
      setOk("Ombor harakatlari yuklandi");
    } catch (e) {
      setErr(e.message);
    }
  };

  const loadStats = async () => {
    try {
      const data = await api("/stock-movements/statistics");
      setStats(data);
      setOk("Ombor statistikasi yuklandi");
    } catch (e) {
      setErr(e.message);
    }
  };

  useEffect(() => {
    loadMovements();
    loadStats();
  }, []);

  return (
    <div>
      {stats && (
        <div className="stats-grid" style={{ marginBottom: 20 }}>
          <div className="stat-card">
            <h3>📊 Jami harakatlar</h3>
            <p className="stat-value">{stats.total_movements}</p>
          </div>
          <div className="stat-card">
            <h3>📥 Kirim</h3>
            <p className="stat-value">{stats.movements_by_type.kirim}</p>
          </div>
          <div className="stat-card">
            <h3>📤 Chiqim</h3>
            <p className="stat-value">{stats.movements_by_type.chiqim}</p>
          </div>
          <div className="stat-card">
            <h3>🔧 Tuzatish</h3>
            <p className="stat-value">{stats.movements_by_type.tuzatish}</p>
          </div>
        </div>
      )}

      <div className="card">
        <h2>📦 Ombor Harakatlari</h2>
        <div className="actions">
          <button onClick={loadMovements}>Yangilash</button>
        </div>

        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Mahsulot</th>
                <th>Turi</th>
                <th>Miqdor</th>
                <th>Sabab</th>
                <th>Sana</th>
              </tr>
            </thead>
            <tbody>
              {movements.length ? movements.map((m) => (
                <tr key={m.id}>
                  <td>{m.id}</td>
                  <td>#{m.product_item_id}</td>
                  <td>
                    <span className={`badge badge-${m.movement_type}`}>
                      {m.movement_type}
                    </span>
                  </td>
                  <td>{m.quantity}</td>
                  <td>{m.reason}</td>
                  <td>{new Date(m.created_at).toLocaleString('uz-UZ')}</td>
                </tr>
              )) : <tr><td colSpan="6">Ma'lumot yo'q</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// Low Stock Alerts Component
export function LowStockAlerts({ api, setOk, setErr }) {
  const [lowStock, setLowStock] = useState([]);
  const [outOfStock, setOutOfStock] = useState([]);

  const loadAlerts = async () => {
    try {
      const [low, out] = await Promise.all([
        api("/alerts/low-stock"),
        api("/alerts/out-of-stock")
      ]);
      setLowStock(low.items || []);
      setOutOfStock(out.items || []);
      setOk("Ogohlantirishlar yuklandi");
    } catch (e) {
      setErr(e.message);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, []);

  return (
    <div>
      <div className="card">
        <h2>⚠️ Kam qolgan mahsulotlar ({lowStock.length})</h2>
        <div className="actions">
          <button onClick={loadAlerts}>Yangilash</button>
        </div>

        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Mahsulot</th>
                <th>Qoldiq</th>
                <th>Minimal</th>
                <th>Farq</th>
              </tr>
            </thead>
            <tbody>
              {lowStock.length ? lowStock.map((item) => (
                <tr key={item.id}>
                  <td>{item.product_name}</td>
                  <td style={{ color: '#f87171', fontWeight: 'bold' }}>{item.total_count}</td>
                  <td>{item.min_stock_level}</td>
                  <td>{item.difference}</td>
                </tr>
              )) : <tr><td colSpan="4">Ma'lumot yo'q</td></tr>}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card" style={{ marginTop: 20 }}>
        <h2>🚫 Tugagan mahsulotlar ({outOfStock.length})</h2>
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Mahsulot</th>
                <th>Minimal daraja</th>
              </tr>
            </thead>
            <tbody>
              {outOfStock.length ? outOfStock.map((item) => (
                <tr key={item.id}>
                  <td>{item.product_name}</td>
                  <td>{item.min_stock_level}</td>
                </tr>
              )) : <tr><td colSpan="2">Ma'lumot yo'q</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
