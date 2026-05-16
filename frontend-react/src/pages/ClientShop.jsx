import { useState, useEffect } from 'react';
import '../styles/ClientShop.css';

export default function ClientShop() {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [collections, setCollections] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [selectedCollection, setSelectedCollection] = useState(null);
  const [cart, setCart] = useState([]);
  const [showCart, setShowCart] = useState(false);
  const [showCheckout, setShowCheckout] = useState(false);
  const [loading, setLoading] = useState(true);

  const baseUrl = '/api';

  useEffect(() => {
    loadInitialData();
    loadCartFromStorage();
  }, []);

  useEffect(() => {
    saveCartToStorage();
  }, [cart]);

  const loadInitialData = async () => {
    setLoading(true);
    try {
      const [productsRes, categoriesRes, collectionsRes] = await Promise.all([
        fetch(`${baseUrl}/products?limit=100`).then(r => r.json()),
        fetch(`${baseUrl}/categories`).then(r => r.json()),
        fetch(`${baseUrl}/collections`).then(r => r.json()),
      ]);

      setProducts(Array.isArray(productsRes) ? productsRes : []);
      setCategories(Array.isArray(categoriesRes) ? categoriesRes : []);
      setCollections(Array.isArray(collectionsRes) ? collectionsRes : []);
    } catch (error) {
      console.error('Ma\'lumotlar yuklanmadi:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadCartFromStorage = () => {
    const saved = localStorage.getItem('textile_cart');
    if (saved) {
      try {
        setCart(JSON.parse(saved));
      } catch (e) {
        console.error('Cart yuklashda xatolik:', e);
      }
    }
  };

  const saveCartToStorage = () => {
    localStorage.setItem('textile_cart', JSON.stringify(cart));
  };

  const addToCart = (product) => {
    const existing = cart.find(item => item.id === product.id);
    if (existing) {
      setCart(cart.map(item =>
        item.id === product.id
          ? { ...item, quantity: item.quantity + 1 }
          : item
      ));
    } else {
      setCart([...cart, { ...product, quantity: 1 }]);
    }
  };

  const removeFromCart = (productId) => {
    setCart(cart.filter(item => item.id !== productId));
  };

  const updateQuantity = (productId, quantity) => {
    if (quantity <= 0) {
      removeFromCart(productId);
    } else {
      setCart(cart.map(item =>
        item.id === productId ? { ...item, quantity } : item
      ));
    }
  };

  const getCartTotal = () => {
    return cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  };

  const getCartCount = () => {
    return cart.reduce((sum, item) => sum + item.quantity, 0);
  };

  const filteredProducts = products.filter(product => {
    if (selectedCategory && product.category_id !== selectedCategory) return false;
    if (selectedCollection && product.collection_id !== selectedCollection) return false;
    return true;
  });

  const handleCheckout = async (formData) => {
    try {
      const orderData = {
        first_name: formData.first_name,
        last_name: formData.last_name,
        phone_number: formData.phone_number,
        address: formData.address,
        payment: formData.payment,
        items: cart.map(item => ({
          product_id: item.id,
          product_item_id: 1, // Default, keyin variant tanlash qo'shiladi
          count: item.quantity,
        })),
      };

      const response = await fetch(`${baseUrl}/order`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(orderData),
      });

      if (!response.ok) throw new Error('Buyurtma yaratishda xatolik');

      const result = await response.json();
      const orderId = result.data?.id;

      if (!orderId) throw new Error('Order ID topilmadi');

      // Get payment URLs
      if (formData.payment === 'payme' || formData.payment === 'click') {
        const paymentRes = await fetch(`${baseUrl}/payment-urls?order_id=${orderId}`);
        const paymentData = await paymentRes.json();

        if (formData.payment === 'payme' && paymentData.payme_url) {
          window.location.href = paymentData.payme_url;
        } else if (formData.payment === 'click' && paymentData.click_url) {
          window.location.href = paymentData.click_url;
        }
      } else {
        // Cash payment
        alert('Buyurtma muvaffaqiyatli yaratildi! Buyurtma raqami: ' + orderId);
        setCart([]);
        setShowCheckout(false);
        setShowCart(false);
      }
    } catch (error) {
      alert('Xatolik: ' + error.message);
    }
  };

  if (loading) {
    return (
      <div className="client-loading">
        <div className="spinner"></div>
        <p>Yuklanmoqda...</p>
      </div>
    );
  }

  return (
    <div className="client-shop">
      {/* Header */}
      <header className="shop-header">
        <div className="container">
          <h1>Textile Shop</h1>
          <button className="cart-button" onClick={() => setShowCart(true)}>
            🛒 Savat
            {getCartCount() > 0 && (
              <span className="cart-badge">{getCartCount()}</span>
            )}
          </button>
        </div>
      </header>

      {/* Filters */}
      <div className="shop-filters">
        <div className="container">
          <div className="filter-group">
            <label>Kategoriya:</label>
            <select
              value={selectedCategory || ''}
              onChange={(e) => setSelectedCategory(e.target.value ? Number(e.target.value) : null)}
            >
              <option value="">Barchasi</option>
              {categories.map(cat => (
                <option key={cat.id} value={cat.id}>{cat.name_uz}</option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label>Kolleksiya:</label>
            <select
              value={selectedCollection || ''}
              onChange={(e) => setSelectedCollection(e.target.value ? Number(e.target.value) : null)}
            >
              <option value="">Barchasi</option>
              {collections.map(col => (
                <option key={col.id} value={col.id}>{col.name_uz}</option>
              ))}
            </select>
          </div>

          <button
            className="clear-filters"
            onClick={() => {
              setSelectedCategory(null);
              setSelectedCollection(null);
            }}
          >
            Tozalash
          </button>
        </div>
      </div>

      {/* Products Grid */}
      <div className="shop-content">
        <div className="container">
          <div className="products-grid">
            {filteredProducts.map(product => (
              <div key={product.id} className="product-card">
                <div className="product-image">
                  <img
                    src={`${baseUrl}/media/products/default.jpg`}
                    alt={product.name_uz}
                    onError={(e) => {
                      e.target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="200"%3E%3Crect fill="%23ddd" width="200" height="200"/%3E%3Ctext fill="%23999" x="50%25" y="50%25" text-anchor="middle" dy=".3em"%3ENo Image%3C/text%3E%3C/svg%3E';
                    }}
                  />
                </div>
                <div className="product-info">
                  <h3>{product.name_uz}</h3>
                  <p className="product-description">{product.description_uz}</p>
                  <div className="product-footer">
                    <span className="product-price">
                      {product.price.toLocaleString()} so'm
                    </span>
                    <button
                      className="add-to-cart-btn"
                      onClick={() => addToCart(product)}
                    >
                      + Savatga
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {filteredProducts.length === 0 && (
            <div className="empty-products">
              <p>Mahsulotlar topilmadi</p>
            </div>
          )}
        </div>
      </div>

      {/* Cart Modal */}
      {showCart && (
        <div className="modal-overlay" onClick={() => setShowCart(false)}>
          <div className="modal-content cart-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Savat</h2>
              <button className="close-btn" onClick={() => setShowCart(false)}>×</button>
            </div>

            <div className="modal-body">
              {cart.length === 0 ? (
                <div className="empty-cart">
                  <p>Savat bo'sh</p>
                </div>
              ) : (
                <>
                  <div className="cart-items">
                    {cart.map(item => (
                      <div key={item.id} className="cart-item">
                        <div className="cart-item-info">
                          <h4>{item.name_uz}</h4>
                          <p className="cart-item-price">
                            {item.price.toLocaleString()} so'm
                          </p>
                        </div>
                        <div className="cart-item-actions">
                          <button onClick={() => updateQuantity(item.id, item.quantity - 1)}>
                            −
                          </button>
                          <span>{item.quantity}</span>
                          <button onClick={() => updateQuantity(item.id, item.quantity + 1)}>
                            +
                          </button>
                          <button
                            className="remove-btn"
                            onClick={() => removeFromCart(item.id)}
                          >
                            🗑️
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="cart-total">
                    <span>Jami:</span>
                    <span className="total-amount">
                      {getCartTotal().toLocaleString()} so'm
                    </span>
                  </div>
                </>
              )}
            </div>

            {cart.length > 0 && (
              <div className="modal-footer">
                <button
                  className="checkout-btn"
                  onClick={() => {
                    setShowCart(false);
                    setShowCheckout(true);
                  }}
                >
                  Buyurtma berish
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Checkout Modal */}
      {showCheckout && (
        <CheckoutForm
          cart={cart}
          total={getCartTotal()}
          onClose={() => setShowCheckout(false)}
          onSubmit={handleCheckout}
        />
      )}
    </div>
  );
}

function CheckoutForm({ cart, total, onClose, onSubmit }) {
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    phone_number: '',
    address: '',
    payment: 'cash',
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content checkout-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Buyurtma berish</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <div className="form-group">
              <label>Ism *</label>
              <input
                type="text"
                required
                value={formData.first_name}
                onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label>Familiya *</label>
              <input
                type="text"
                required
                value={formData.last_name}
                onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label>Telefon *</label>
              <input
                type="tel"
                required
                placeholder="+998901234567"
                value={formData.phone_number}
                onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label>Manzil *</label>
              <textarea
                required
                rows="3"
                value={formData.address}
                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label>To'lov usuli *</label>
              <select
                value={formData.payment}
                onChange={(e) => setFormData({ ...formData, payment: e.target.value })}
              >
                <option value="cash">Naqd pul</option>
                <option value="payme">Payme</option>
                <option value="click">Click</option>
              </select>
            </div>

            <div className="order-summary">
              <h3>Buyurtma tafsilotlari</h3>
              {cart.map(item => (
                <div key={item.id} className="summary-item">
                  <span>{item.name_uz} × {item.quantity}</span>
                  <span>{(item.price * item.quantity).toLocaleString()} so'm</span>
                </div>
              ))}
              <div className="summary-total">
                <span>Jami:</span>
                <span>{total.toLocaleString()} so'm</span>
              </div>
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn-secondary" onClick={onClose}>
              Bekor qilish
            </button>
            <button type="submit" className="btn-primary">
              Tasdiqlash
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
