import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import '../styles/Products.css';

export default function Products() {
  const { api } = useAuth();
  const [products, setProducts] = useState([]);
  const [productPhotos, setProductPhotos] = useState({});
  const [categories, setCategories] = useState([]);
  const [collections, setCollections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [filters, setFilters] = useState({
    search: '',
    category_id: '',
    collection_id: '',
    clothing_type: '',
  });

  useEffect(() => {
    loadData();
  }, [filters]);

  const toCleanQuery = (rawFilters) => {
    const params = new URLSearchParams();
    Object.entries(rawFilters).forEach(([key, value]) => {
      const cleaned = String(value ?? '').trim();
      if (cleaned !== '') {
        params.set(key, cleaned);
      }
    });
    params.set('limit', '100');
    return params.toString();
  };

  const normalizePhotoUrl = (photoValue) => {
    const raw = String(photoValue || '').trim();
    if (!raw) return '';
    if (raw.startsWith('http://') || raw.startsWith('https://')) return raw;
    if (raw.startsWith('/media/')) return `/api${raw}`;
    if (raw.startsWith('media/')) return `/api/${raw}`;
    return `/api/media/${raw.replace(/^\/+/, '')}`;
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const [productsRes, categoriesRes, collectionsRes, photosRes] = await Promise.all([
        api(`/products/search/advanced?${toCleanQuery(filters)}`),
        api('/categories'),
        api('/collections'),
        api('/product-photos'),
      ]);

      const productList = Array.isArray(productsRes?.data) ? productsRes.data : [];
      setProducts(productList);
      setCategories(Array.isArray(categoriesRes) ? categoriesRes : []);
      setCollections(Array.isArray(collectionsRes) ? collectionsRes : []);
      const photosList = Array.isArray(photosRes) ? photosRes : [];
      const photosByProduct = photosList.reduce((acc, item) => {
        if (!item?.product_id || !item?.photo) return acc;
        if (!acc[item.product_id]) {
          acc[item.product_id] = normalizePhotoUrl(item.photo);
        }
        return acc;
      }, {});
      setProductPhotos(photosByProduct);
    } catch (error) {
      console.error('Ma\'lumotlar yuklanmadi:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);

    try {
      if (editingProduct) {
        await api(`/products/${editingProduct.id}`, {
          method: 'PATCH',
          body: formData,
        });
      } else {
        await api('/products', {
          method: 'POST',
          body: formData,
        });
      }
      setShowForm(false);
      setEditingProduct(null);
      loadData();
    } catch (error) {
      alert('Xatolik: ' + error.message);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Mahsulotni o\'chirmoqchimisiz?')) return;

    try {
      await api(`/products/${id}`, { method: 'DELETE' });
      loadData();
    } catch (error) {
      alert('Xatolik: ' + error.message);
    }
  };

  const startEdit = async (product) => {
    setEditingProduct(product);
    setShowForm(true);
  };

  return (
    <div className="products-page">
      <div className="page-header">
        <div>
          <h2>Tovarlar</h2>
          <p className="subtitle">Mahsulotlar boshqaruvi</p>
        </div>
        <button
          className="btn-primary"
          onClick={() => {
            setEditingProduct(null);
            setShowForm(true);
          }}
        >
          + Yangi mahsulot
        </button>
      </div>

      {/* Filters */}
      <div className="filters-card">
        <div className="filters-grid">
          <input
            type="text"
            placeholder="Qidirish..."
            value={filters.search}
            onChange={(e) => setFilters({ ...filters, search: e.target.value })}
          />
          <select
            value={filters.category_id}
            onChange={(e) => setFilters({ ...filters, category_id: e.target.value })}
          >
            <option value="">Barcha kategoriyalar</option>
            {categories.map(cat => (
              <option key={cat.id} value={cat.id}>{cat.name_uz}</option>
            ))}
          </select>
          <select
            value={filters.collection_id}
            onChange={(e) => setFilters({ ...filters, collection_id: e.target.value })}
          >
            <option value="">Barcha kolleksiyalar</option>
            {collections.map(col => (
              <option key={col.id} value={col.id}>{col.name_uz}</option>
            ))}
          </select>
          <select
            value={filters.clothing_type}
            onChange={(e) => setFilters({ ...filters, clothing_type: e.target.value })}
          >
            <option value="">Barcha turlar</option>
            <option value="erkak">Erkak</option>
            <option value="ayol">Ayol</option>
            <option value="unisex">Unisex</option>
          </select>
        </div>
      </div>

      {/* Form Modal */}
      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{editingProduct ? 'Mahsulotni tahrirlash' : 'Yangi mahsulot'}</h3>
              <button className="close-btn" onClick={() => setShowForm(false)}>×</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="modal-body">
                <div className="form-grid">
                  <div className="form-group">
                    <label>Nomi (UZ) *</label>
                    <input
                      name="name_uz"
                      required
                      defaultValue={editingProduct?.name_uz}
                    />
                  </div>
                  <div className="form-group">
                    <label>Nomi (RU) *</label>
                    <input
                      name="name_ru"
                      required
                      defaultValue={editingProduct?.name_ru}
                    />
                  </div>
                  <div className="form-group">
                    <label>Nomi (ENG) *</label>
                    <input
                      name="name_eng"
                      required
                      defaultValue={editingProduct?.name_eng}
                    />
                  </div>
                  <div className="form-group">
                    <label>Narx *</label>
                    <input
                      name="price"
                      type="number"
                      required
                      defaultValue={editingProduct?.price}
                    />
                  </div>
                  <div className="form-group">
                    <label>Kategoriya *</label>
                    <select name="category_id" required defaultValue={editingProduct?.category_id}>
                      <option value="">Tanlang</option>
                      {categories.map(cat => (
                        <option key={cat.id} value={cat.id}>{cat.name_uz}</option>
                      ))}
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Kolleksiya *</label>
                    <select name="collection_id" required defaultValue={editingProduct?.collection_id || ''}>
                      <option value="">Tanlang</option>
                      {collections.map(col => (
                        <option key={col.id} value={col.id}>{col.name_uz}</option>
                      ))}
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Turi *</label>
                    <select name="clothing_type" required defaultValue={editingProduct?.clothing_type || 'erkak'}>
                      <option value="erkak">Erkak</option>
                      <option value="ayol">Ayol</option>
                      <option value="unisex">Unisex</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Holat</label>
                    <select name="is_active" defaultValue={editingProduct?.is_active !== false ? 'true' : 'false'}>
                      <option value="true">Faol</option>
                      <option value="false">Faol emas</option>
                    </select>
                  </div>
                </div>
                <div className="form-group">
                  <label>Tavsif (UZ)</label>
                  <textarea
                    name="description_uz"
                    rows="3"
                    defaultValue={editingProduct?.description_uz}
                  />
                </div>
                <div className="form-group">
                  <label>Tavsif (RU)</label>
                  <textarea
                    name="description_ru"
                    rows="3"
                    defaultValue={editingProduct?.description_ru}
                  />
                </div>
                <div className="form-group">
                  <label>Tavsif (ENG)</label>
                  <textarea
                    name="description_eng"
                    rows="3"
                    defaultValue={editingProduct?.description_eng}
                  />
                </div>
                {!editingProduct && (
                  <div className="form-group">
                    <label>Rasm</label>
                    <input name="photo" type="file" accept="image/*" />
                  </div>
                )}
              </div>
              <div className="modal-footer">
                <button type="button" className="btn-secondary" onClick={() => setShowForm(false)}>
                  Bekor qilish
                </button>
                <button type="submit" className="btn-primary">
                  {editingProduct ? 'Yangilash' : 'Yaratish'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Products Grid */}
      {loading ? (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Yuklanmoqda...</p>
        </div>
      ) : products.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📦</div>
          <h3>Mahsulotlar yo'q</h3>
          <p>Yangi mahsulot qo'shish uchun yuqoridagi tugmani bosing</p>
        </div>
      ) : (
        <div className="products-grid">
          {products.map(product => (
            <div key={product.id} className="product-card">
              <div className="product-image">
                <img
                  src={productPhotos[product.id] || '/api/media/products/default.jpg'}
                  alt={product.name_uz}
                  onError={(e) => {
                    e.target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="200"%3E%3Crect fill="%23ddd" width="200" height="200"/%3E%3Ctext fill="%23999" x="50%25" y="50%25" text-anchor="middle" dy=".3em"%3ENo Image%3C/text%3E%3C/svg%3E';
                  }}
                />
                {!product.is_active && (
                  <div className="inactive-badge">Faol emas</div>
                )}
              </div>
              <div className="product-info">
                <h3>{product.name_uz}</h3>
                <p className="product-meta">
                  ID: {product.id} | {product.clothing_type}
                </p>
                <p className="product-price">
                  {product.price.toLocaleString()} so'm
                </p>
                <div className="product-actions">
                  <button
                    className="btn-icon"
                    onClick={() => startEdit(product)}
                    title="Tahrirlash"
                  >
                    ✏️
                  </button>
                  <button
                    className="btn-icon danger"
                    onClick={() => handleDelete(product.id)}
                    title="O'chirish"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
