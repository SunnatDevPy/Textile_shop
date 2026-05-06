import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import '../styles/Layout.css';

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const menuItems = [
    { id: 'dashboard', icon: '📊', text: 'Dashboard', path: '/dashboard' },
    { id: 'products', icon: '📦', text: 'Tovarlar', path: '/products' },
    { id: 'warehouse', icon: '🏭', text: 'Sklad', path: '/warehouse' },
    { id: 'orders', icon: '🛒', text: 'Buyurtmalar', path: '/orders' },
    { id: 'categories', icon: '📑', text: 'Kategoriyalar', path: '/categories' },
    { id: 'collections', icon: '🎨', text: 'Kolleksiyalar', path: '/collections' },
    { id: 'colors', icon: '🎨', text: 'Ranglar', path: '/colors' },
    { id: 'sizes', icon: '📏', text: 'O\'lchamlar', path: '/sizes' },
    { id: 'stock-movements', icon: '📋', text: 'Harakatlar', path: '/stock-movements' },
    { id: 'alerts', icon: '⚠️', text: 'Ogohlantirishlar', path: '/alerts' },
    { id: 'settings', icon: '⚙️', text: 'Sozlamalar', path: '/settings' },
  ];

  const handleNavigation = (path) => {
    navigate(path);
  };

  const openClientPage = () => {
    window.open('/client', '_blank');
  };

  return (
    <div className="layout">
      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <h2>Textile Shop</h2>
          <button
            className="sidebar-toggle"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            {sidebarOpen ? '←' : '→'}
          </button>
        </div>

        <nav className="sidebar-nav">
          {menuItems.map(item => (
            <a
              key={item.id}
              href={item.path}
              className={`nav-item ${window.location.pathname === item.path ? 'active' : ''}`}
              onClick={(e) => {
                e.preventDefault();
                handleNavigation(item.path);
              }}
            >
              <span className="nav-icon">{item.icon}</span>
              {sidebarOpen && <span className="nav-text">{item.text}</span>}
            </a>
          ))}

          {/* Client Page Button */}
          <div className="nav-divider"></div>
          <button
            className="nav-item client-btn"
            onClick={openClientPage}
          >
            <span className="nav-icon">🛍️</span>
            {sidebarOpen && <span className="nav-text">Klient sahifasi</span>}
          </button>
        </nav>

        <div className="sidebar-footer">
          <div className="user-info">
            <div className="user-avatar">
              {user?.username?.charAt(0).toUpperCase()}
            </div>
            {sidebarOpen && (
              <div className="user-details">
                <p className="user-name">{user?.username}</p>
                <p className="user-role">{user?.status}</p>
              </div>
            )}
          </div>
          <button className="logout-btn" onClick={logout} title="Chiqish">
            <span className="nav-icon">🚪</span>
            {sidebarOpen && <span>Chiqish</span>}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="main-content">
        <header className="topbar">
          <div className="topbar-left">
            <h1>Admin Panel</h1>
          </div>
          <div className="topbar-right">
            <button className="client-page-btn" onClick={openClientPage}>
              🛍️ Klient sahifasi
            </button>
            <div className="user-badge">
              <span className="user-avatar-small">
                {user?.username?.charAt(0).toUpperCase()}
              </span>
              <span className="user-name-small">{user?.username}</span>
            </div>
          </div>
        </header>

        <main className="content">
          {children}
        </main>
      </div>
    </div>
  );
}
