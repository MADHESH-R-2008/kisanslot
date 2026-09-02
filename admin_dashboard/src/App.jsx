import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, Users, CalendarDays, BarChart2,
  LogOut, CheckSquare, Building2, Menu, X
} from 'lucide-react';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Queue from './pages/Queue';
import Bookings from './pages/Bookings';
import Procurement from './pages/Procurement';
import Reports from './pages/Reports';
import Centres from './pages/Centres';
import './index.css';

// ── Auth guard ────────────────────────────────────────────────────────────────
const PrivateRoute = ({ children, requiredRoles }) => {
  const token = localStorage.getItem('token');
  const role = localStorage.getItem('role');
  if (!token) return <Navigate to="/login" replace />;
  if (requiredRoles && !requiredRoles.includes(role)) {
    return <Navigate to="/" replace />;
  }
  return children;
};

// ── Sidebar ───────────────────────────────────────────────────────────────────
const Sidebar = ({ collapsed, setCollapsed }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const role = localStorage.getItem('role') || '';

  const handleLogout = () => {
    localStorage.clear();
    navigate('/login');
  };

  // Role-based nav items
  const navItems = [
    { path: '/',            label: 'Dashboard',       icon: LayoutDashboard, roles: null },
    { path: '/queue',       label: 'Queue',           icon: Users,           roles: null },
    { path: '/bookings',    label: 'Bookings',        icon: CalendarDays,    roles: null },
    { path: '/procurement', label: 'Procurement',     icon: CheckSquare,     roles: null },
    { path: '/reports',     label: 'Reports',         icon: BarChart2,       roles: null },
    {
      path: '/centres',
      label: 'Centres',
      icon: Building2,
      roles: ['ADMIN', 'SUPER_ADMIN'],
    },
  ].filter((item) => !item.roles || item.roles.includes(role));

  return (
    <div className="sidebar" style={{ width: collapsed ? 64 : 240, transition: 'width 0.25s ease', overflow: 'hidden' }}>
      <div className="sidebar-header" style={{ justifyContent: collapsed ? 'center' : 'flex-start' }}>
        <div style={{
          width: 32, height: 32, backgroundColor: 'var(--primary-color)',
          borderRadius: 8, display: 'flex', alignItems: 'center',
          justifyContent: 'center', color: 'white', fontWeight: 700, flexShrink: 0,
        }}>K</div>
        {!collapsed && <span style={{ marginLeft: '0.75rem', fontWeight: 700 }}>KisanSlot</span>}
        <button
          onClick={() => setCollapsed(!collapsed)}
          style={{ marginLeft: 'auto', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', display: 'flex', padding: '0.25rem', flexShrink: 0 }}
        >
          {collapsed ? <Menu size={18} /> : <X size={18} />}
        </button>
      </div>

      <div className="sidebar-nav">
        {navItems.map((item) => (
          <div
            key={item.path}
            className={`nav-link ${location.pathname === item.path ? 'active' : ''}`}
            onClick={() => navigate(item.path)}
            style={{ cursor: 'pointer', justifyContent: collapsed ? 'center' : 'flex-start', gap: collapsed ? 0 : '0.75rem', padding: collapsed ? '0.75rem' : undefined }}
            title={collapsed ? item.label : undefined}
          >
            <item.icon size={20} style={{ flexShrink: 0 }} />
            {!collapsed && item.label}
          </div>
        ))}
      </div>

      <div style={{ marginTop: 'auto', padding: '1rem 0' }}>
        {!collapsed && (
          <div style={{ padding: '0.5rem 1rem', marginBottom: '0.5rem' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Signed in as</div>
            <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)', marginTop: '0.15rem' }}>
              {localStorage.getItem('username') || 'Admin'}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--primary-color)', marginTop: '0.1rem' }}>{role}</div>
          </div>
        )}
        <div
          className="nav-link"
          onClick={handleLogout}
          style={{ cursor: 'pointer', color: 'var(--danger-color)', justifyContent: collapsed ? 'center' : 'flex-start', gap: collapsed ? 0 : '0.75rem', padding: collapsed ? '0.75rem' : undefined }}
          title={collapsed ? 'Logout' : undefined}
        >
          <LogOut size={20} style={{ flexShrink: 0 }} />
          {!collapsed && 'Logout'}
        </div>
      </div>
    </div>
  );
};

// ── Layout ────────────────────────────────────────────────────────────────────
const Layout = ({ children }) => {
  const [isDark, setIsDark] = useState(() => localStorage.getItem('theme') === 'dark');
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

  useEffect(() => {
    if (isDark) {
      document.body.setAttribute('data-theme', 'dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.body.removeAttribute('data-theme');
      localStorage.setItem('theme', 'light');
    }
  }, [isDark]);

  const pageTitle = {
    '/': 'Dashboard',
    '/queue': 'Queue Management',
    '/bookings': 'Bookings',
    '/procurement': 'Procurement',
    '/reports': 'Reports & Analytics',
    '/centres': 'Centres',
  }[location.pathname] || 'KisanSlot';

  return (
    <div className="app-container">
      <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />
      <div className="main-content">
        <div className="topbar">
          <h2 style={{ fontSize: '1.2rem', margin: 0, fontWeight: 600 }}>{pageTitle}</h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <button
              className="btn btn-secondary"
              onClick={() => setIsDark(!isDark)}
              style={{ fontSize: '0.85rem', padding: '0.4rem 0.8rem' }}
            >
              {isDark ? '☀️ Light' : '🌙 Dark'}
            </button>
            <div style={{
              width: 36, height: 36, borderRadius: '50%',
              background: 'linear-gradient(135deg, var(--primary-color), #3b82f6)',
              color: 'white', display: 'flex', alignItems: 'center',
              justifyContent: 'center', fontWeight: 700, fontSize: '0.9rem',
            }}>
              {(localStorage.getItem('username') || 'A')[0].toUpperCase()}
            </div>
          </div>
        </div>
        <div className="page-content animate-fade-in">
          {children}
        </div>
      </div>
    </div>
  );
};

// ── App ───────────────────────────────────────────────────────────────────────
function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<PrivateRoute><Layout><Dashboard /></Layout></PrivateRoute>} />
        <Route path="/queue" element={<PrivateRoute><Layout><Queue /></Layout></PrivateRoute>} />
        <Route path="/bookings" element={<PrivateRoute><Layout><Bookings /></Layout></PrivateRoute>} />
        <Route path="/procurement" element={<PrivateRoute><Layout><Procurement /></Layout></PrivateRoute>} />
        <Route path="/reports" element={<PrivateRoute><Layout><Reports /></Layout></PrivateRoute>} />
        <Route
          path="/centres"
          element={
            <PrivateRoute requiredRoles={['ADMIN', 'SUPER_ADMIN']}>
              <Layout><Centres /></Layout>
            </PrivateRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
