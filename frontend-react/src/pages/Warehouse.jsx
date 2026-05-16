import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import '../styles/Warehouse.css';

export default function Warehouse() {
  const { api } = useAuth();
  const [products, setProducts] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [productItems, setProductItems] = useState([]);
  const [colors, setColors] = useState([]);
  const [sizes, setSizes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);
  const [editingItem, setEditingItem] = useState(null);

  useEffect(() => {
    loadProducts();
    loadColors();
    loadSizes();
  }, []);

  const loadProducts = async () => {
    try {
      const data = await api('/products?limit=500&include_inactive=false');
      setProducts(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Mahsulotlar yuklanmadi:', error);
    }
  };

  const loadColors = async () => {
    try {
      const data = await api('/color');
      setColors(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Ranglar yuklanmadi:', error);
    }
  };

  const loadSizes = async () => {
    try {
      const data = await api('/size');
      setSizes(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('O\'lchamlar yuklanmadi:', error);
    }
  };

  const loadProductItems = async (productId) => {
    setLoading(true);
    try {
      const data = await api(`/product-items/product/${productId}`);
      setProductItems(Array.isArray(data) ? data : []);
      setSelectedProduct(products.find(p => p.id === productId));
    } catch (error) {
      console.error('Sklad ma\'lumotlari yuklanmadi:', error);
      setProductItems([]);
    } finally {
      setLoading(false);
    }
  };

  const handleAddItem = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);

    try {
      await api(`/products/${selectedProduct.id}/items`, {
        method: 'POST',
        body: formData,
      });
      setShowAddForm(false);
      loadProductItems(selectedProduct.id);
      e.target.reset();
    } catch (error) {
      alert('Xatolik: ' + error.message);
    }
  };

  const handleUpdateItem = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);

    try {
      await api(`/products/${selectedProduct.id}/items/${editingItem.id}`, {
        method: 'PATCH',
        body: formData,
      });
      setShowEditForm(false);
      setEditingItem(null);
      loadProductItems(selectedProduct.id);
    } catch (error) {
      alert('Xatolik: ' + error.message);
    }
  };

  const handleDeleteItem = async (itemId) => {
    if (!confirm('Ushbu variantni o\'chirmoqchimisiz?')) return;

    try {
      await api(`/products/${selectedProduct.id}/items/${itemId}`, {
        method: 'DELETE',
      });
      loadProductItems(selectedProduct.id);
    } catch (error) {
      alert('Xatolik: ' + error.message);
    }
  };

  const startEdit = (item) => {
    setEditingItem(item);
    setShowEditForm(true);
    setShowAddForm(false);
  };

  const getColorName = (colorId) => {
    const color = colors.find(c => c.id === colorId);
    return color ? color.name_uz : `#${colorId}`;
  };

  const getColorCode = (colorId) => {
    const color = colors.find(c => c.id === colorId);
    return color?.color_code || '#000000';
  };

  const getSizeName = (sizeId) => {
    const size = sizes.find(s => s.id === sizeId);
    return size ? size.name : `#${sizeId}`;
  };

  const getTotalStock = () => {
    return productItems.reduce((sum, item) => sum + (item.total_count || 0), 0);
  };

  const getLowStockCount = () => {
    return productItems.filter(item =>
      item.total_count <= (item.min_stock_level || 10)
    ).length;
  };

  return (
    <div className="warehouse">
      <div className="warehouse-header">
        <h2>Sklad boshqaruvi</h2>
        <p className="subtitle">Mahsulot variantlari va ombor qoldig'i</p>
      </div>

      <div className="warehouse-layout">
        {/* Products List */}
        <div className="products-sidebar">
          <div className="sidebar-header">
            <h3>Mahsulotlar</h3>
            <span className="badge">{products.length}</span>
          </div>
          <div className="products-list">
            {products.map(product => (
              <div
                key={product.id}
                className={`product-item ${selectedProduct?.id === product.id ? 'active' : ''}`}
                onClick={() => loadProductItems(product.id)}
              >
                <div className="product-info">
                  <p className="product-name">{product.name_uz}</p>
                  <p className="product-meta">
                    ID: {product.id} | {product.price.toLocaleString()} so'm
                  </p>
                </div>
                <div className="product-arrow">→</div>
              </div>
            ))}
          </div>
        </div>

        {/* Product Items */}
        <div className="items-content">
          {!selectedProduct ? (
            <div className="empty-state">
              <div className="empty-icon">📦</div>
              <h3>Mahsulot tanlanmagan</h3>
              <p>Chap tarafdan mahsulotni tanlang</p>
            </div>
          ) : (
            <>
              <div className="content-header">
                <div>
                  <h3>{selectedProduct.name_uz}</h3>
                  <p className="product-description">
                    {selectedProduct.description_uz || 'Tavsif yo\'q'}
                  </p>
                </div>
                <button
                  className="btn-primary"
                  onClick={() => {
                    setShowAddForm(true);
                    setShowEditForm(false);
                  }}
                >
                  + Variant qo'shish
                </button>
              </div>

              {/* Stats */}
              <div className="warehouse-stats">
                <div className="stat-box">
                  <span className="stat-label">Jami variantlar</span>
                  <span className="stat-value">{productItems.length}</span>
                </div>
                <div className="stat-box">
                  <span className="stat-label">Jami soni</span>
                  <span className="stat-value">{getTotalStock()}</span>
                </div>
                <div className="stat-box">
                  <span className="stat-label">Kam qolgan</span>
                  <span className="stat-value warning">{getLowStockCount()}</span>
                </div>
              </div>

              {/* Add Form */}
              {showAddForm && (
                <div className="form-card">
                  <h4>Yangi variant qo'shish</h4>
                  <form onSubmit={handleAddItem} className="warehouse-form">
                    <div className="form-row">
                      <div className="form-group">
                        <label>Rang</label>
                        <select name="color_id" required>
                          <option value="">Tanlang</option>
                          {colors.map(color => (
                            <option key={color.id} value={color.id}>
                              {color.name_uz}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div className="form-group">
                        <label>O'lcham</label>
                        <select name="size_id" required>
                          <option value="">Tanlang</option>
                          {sizes.map(size => (
                            <option key={size.id} value={size.id}>
                              {size.name}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>
                    <div className="form-row">
                      <div className="form-group">
                        <label>Soni</label>
                        <input
                          type="number"
                          name="total_count"
                          min="0"
                          required
                          placeholder="0"
                        />
                      </div>
                      <div className="form-group">
                        <label>Minimal chegara</label>
                        <input
                          type="number"
                          name="min_stock_level"
                          min="0"
                          defaultValue="10"
                          placeholder="10"
                        />
                      </div>
                    </div>
                    <div className="form-actions">
                      <button type="submit" className="btn-primary">
                        Saqlash
                      </button>
                      <button
                        type="button"
                        className="btn-secondary"
                        onClick={() => setShowAddForm(false)}
                      >
                        Bekor qilish
                      </button>
                    </div>
                  </form>
                </div>
              )}

              {/* Edit Form */}
              {showEditForm && editingItem && (
                <div className="form-card">
                  <h4>Variantni tahrirlash</h4>
                  <form onSubmit={handleUpdateItem} className="warehouse-form">
                    <div className="form-row">
                      <div className="form-group">
                        <label>Rang</label>
                        <select name="color_id" defaultValue={editingItem.color_id}>
                          {colors.map(color => (
                            <option key={color.id} value={color.id}>
                              {color.name_uz}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div className="form-group">
                        <label>O'lcham</label>
                        <select name="size_id" defaultValue={editingItem.size_id}>
                          {sizes.map(size => (
                            <option key={size.id} value={size.id}>
                              {size.name}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>
                    <div className="form-row">
                      <div className="form-group">
                        <label>Soni</label>
                        <input
                          type="number"
                          name="total_count"
                          min="0"
                          defaultValue={editingItem.total_count}
                        />
                      </div>
                      <div className="form-group">
                        <label>Minimal chegara</label>
                        <input
                          type="number"
                          name="min_stock_level"
                          min="0"
                          defaultValue={editingItem.min_stock_level || 10}
                        />
                      </div>
                    </div>
                    <div className="form-actions">
                      <button type="submit" className="btn-primary">
                        Yangilash
                      </button>
                      <button
                        type="button"
                        className="btn-secondary"
                        onClick={() => {
                          setShowEditForm(false);
                          setEditingItem(null);
                        }}
                      >
                        Bekor qilish
                      </button>
                    </div>
                  </form>
                </div>
              )}

              {/* Items Table */}
              {loading ? (
                <div className="loading-state">
                  <div className="spinner"></div>
                  <p>Yuklanmoqda...</p>
                </div>
              ) : productItems.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-icon">📭</div>
                  <h3>Variantlar yo'q</h3>
                  <p>Yangi variant qo'shish uchun yuqoridagi tugmani bosing</p>
                </div>
              ) : (
                <div className="items-table">
                  <table>
                    <thead>
                      <tr>
                        <th>ID</th>
                        <th>Rang</th>
                        <th>O'lcham</th>
                        <th>Soni</th>
                        <th>Min. chegara</th>
                        <th>Holat</th>
                        <th>Amallar</th>
                      </tr>
                    </thead>
                    <tbody>
                      {productItems.map(item => {
                        const isLowStock = item.total_count <= (item.min_stock_level || 10);
                        return (
                          <tr key={item.id} className={isLowStock ? 'low-stock' : ''}>
                            <td>{item.id}</td>
                            <td>
                              <div className="color-cell">
                                <div
                                  className="color-box"
                                  style={{ backgroundColor: getColorCode(item.color_id) }}
                                ></div>
                                {getColorName(item.color_id)}
                              </div>
                            </td>
                            <td>
                              <span className="size-badge">{getSizeName(item.size_id)}</span>
                            </td>
                            <td>
                              <span className="stock-count">{item.total_count}</span>
                            </td>
                            <td>{item.min_stock_level || 10}</td>
                            <td>
                              {isLowStock ? (
                                <span className="status-badge warning">⚠️ Kam</span>
                              ) : (
                                <span className="status-badge success">✓ Yetarli</span>
                              )}
                            </td>
                            <td>
                              <div className="action-buttons">
                                <button
                                  className="btn-icon"
                                  onClick={() => startEdit(item)}
                                  title="Tahrirlash"
                                >
                                  ✏️
                                </button>
                                <button
                                  className="btn-icon danger"
                                  onClick={() => handleDeleteItem(item.id)}
                                  title="O'chirish"
                                >
                                  🗑️
                                </button>
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
