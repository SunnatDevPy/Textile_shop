import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import '../styles/Dashboard.css';

export default function Dashboard() {
  const { api } = useAuth();
  const [stats, setStats] = useState(null);
  const [revenue, setRevenue] = useState([]);
  const [topProducts, setTopProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState('month');

  useEffect(() => {
    loadDashboardData();
  }, [period]);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [statsData, revenueData, topProductsData] = await Promise.all([
        api('/dashboard/stats'),
        api(`/dashboard/revenue?period=${period}`),
        api('/dashboard/top-products?limit=10'),
      ]);

      setStats(statsData);
      setRevenue(revenueData?.data || []);
      setTopProducts(topProductsData || []);
    } catch (error) {
      console.error('Dashboard yuklashda xatolik:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num) => {
    return new Intl.NumberFormat('uz-UZ').format(num || 0);
  };

  const formatCurrency = (num) => {
    return new Intl.NumberFormat('uz-UZ').format(num || 0) + ' so\'m';
  };

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="spinner"></div>
        <p>Yuklanmoqda...</p>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h2>Dashboard</h2>
        <div className="period-selector">
          <button
            className={period === 'week' ? 'active' : ''}
            onClick={() => setPeriod('week')}
          >
            Hafta
          </button>
          <button
            className={period === 'month' ? 'active' : ''}
            onClick={() => setPeriod('month')}
          >
            Oy
          </button>
          <button
            className={period === 'year' ? 'active' : ''}
            onClick={() => setPeriod('year')}
          >
            Yil
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#667eea' }}>
            🛒
          </div>
          <div className="stat-content">
            <p className="stat-label">Jami buyurtmalar</p>
            <h3 className="stat-value">{formatNumber(stats?.total_orders)}</h3>
            <p className="stat-sub">Bugun: {formatNumber(stats?.today_orders)}</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#48bb78' }}>
            💰
          </div>
          <div className="stat-content">
            <p className="stat-label">Jami daromad</p>
            <h3 className="stat-value">{formatCurrency(stats?.total_revenue)}</h3>
            <p className="stat-sub">Bugun: {formatCurrency(stats?.today_revenue)}</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#ed8936' }}>
            ⏳
          </div>
          <div className="stat-content">
            <p className="stat-label">Kutilayotgan</p>
            <h3 className="stat-value">{formatNumber(stats?.pending_orders)}</h3>
            <p className="stat-sub">Yangi buyurtmalar</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#f56565' }}>
            ⚠️
          </div>
          <div className="stat-content">
            <p className="stat-label">Kam qolgan</p>
            <h3 className="stat-value">{formatNumber(stats?.low_stock_items)}</h3>
            <p className="stat-sub">Skladda kam</p>
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="charts-grid">
        {/* Revenue Chart */}
        <div className="chart-card">
          <h3>Daromad dinamikasi</h3>
          <div className="chart-container">
            {revenue.length > 0 ? (
              <div className="simple-chart">
                {revenue.map((item, index) => {
                  const maxRevenue = Math.max(...revenue.map(r => r.revenue || 0));
                  const height = maxRevenue > 0 ? ((item.revenue || 0) / maxRevenue) * 100 : 0;

                  return (
                    <div key={index} className="chart-bar-wrapper">
                      <div className="chart-bar-container">
                        <div
                          className="chart-bar"
                          style={{ height: `${height}%` }}
                          title={`${item.date}: ${formatCurrency(item.revenue)}`}
                        ></div>
                      </div>
                      <div className="chart-label">
                        {new Date(item.date).getDate()}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="no-data">Ma'lumot yo'q</p>
            )}
          </div>
        </div>

        {/* Top Products */}
        <div className="chart-card">
          <h3>Top mahsulotlar</h3>
          <div className="top-products-list">
            {topProducts.length > 0 ? (
              topProducts.map((product, index) => (
                <div key={index} className="top-product-item">
                  <div className="product-rank">#{index + 1}</div>
                  <div className="product-info">
                    <p className="product-name">{product.product_name}</p>
                    <p className="product-stats">
                      Sotildi: {formatNumber(product.total_sold)} dona
                    </p>
                  </div>
                  <div className="product-revenue">
                    {formatCurrency(product.total_revenue)}
                  </div>
                </div>
              ))
            ) : (
              <p className="no-data">Ma'lumot yo'q</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
