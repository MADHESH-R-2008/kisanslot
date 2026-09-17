import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, Users, CalendarDays, BarChart2,
  LogOut, CheckSquare, Building2, Menu, X, Bell
} from 'lucide-react';
import { notificationAPI } from './services/api';
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

// ── Notification Dropdown ───────────────────────────────────────────────────
const NotificationMenu = () => {
  const [open, setOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);

  const fetchNotifications = async () => {
    try {
      const res = await notificationAPI.list();
      const items = res.data.items || (Array.isArray(res.data) ? res.data : []);
      const count = res.data.unread_count !== undefined
        ? res.data.unread_count
        : items.filter((n) => !n.is_read).length;
      setNotifications(items);
      setUnreadCount(count);
    } catch (err) {
      // Silently catch error if offline or unauthenticated
    }
  };

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleMarkRead = async (id, e) => {
    e.stopPropagation();
    try {
      await notificationAPI.markRead(id);
      fetchNotifications();
    } catch (err) {
      console.error('Failed to mark read', err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationAPI.markAllRead();
      fetchNotifications();
    } catch (err) {
      console.error('Failed to mark all read', err);
    }
  };

  return (
    <div style={{ position: 'relative' }}>
      <button
        onClick={() => setOpen(!open)}
        className="btn btn-secondary"
        style={{
          position: 'relative',
          padding: '0.45rem 0.65rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.35rem',
          borderRadius: 8,
        }}
        title="Notifications"
      >
        <Bell size={18} />
        {unreadCount > 0 && (
          <span style={{
            position: 'absolute',
            top: -4,
            right: -4,
            backgroundColor: 'var(--danger-color, #ef4444)',
            color: 'white',
            borderRadius: '10px',
            fontSize: '0.7rem',
            fontWeight: 700,
            padding: '2px 6px',
            lineHeight: 1,
          }}>
            {unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div style={{
          position: 'absolute',
          right: 0,
          top: '120%',
          width: 320,
          maxHeight: 400,
          backgroundColor: 'var(--bg-surface, #ffffff)',
          border: '1px solid var(--border-color, #e2e8f0)',
          borderRadius: 12,
          boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.15)',
          zIndex: 100,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}>
          <div style={{
            padding: '0.75rem 1rem',
            borderBottom: '1px solid var(--border-color, #e2e8f0)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            backgroundColor: 'var(--bg-subtle, #f8fafc)',
          }}>
            <div style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--text-primary)' }}>
              Notifications {unreadCount > 0 && `(${unreadCount})`}
            </div>
            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllRead}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--primary-color, #10b981)',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Mark all read
              </button>
            )}
          </div>

          <div style={{ overflowY: 'auto', flex: 1, padding: '0.5rem 0' }}>
            {notifications.length === 0 ? (
              <div style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                No notifications
              </div>
            ) : (
              notifications.map((n) => (
                <div
                  key={n.id}
                  style={{
                    padding: '0.65rem 1rem',
                    borderBottom: '1px solid var(--border-color, #f1f5f9)',
                    backgroundColor: n.is_read ? 'transparent' : 'rgba(16, 185, 129, 0.06)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.2rem',
                    cursor: 'pointer',
                  }}
                  onClick={(e) => !n.is_read && handleMarkRead(n.id, e)}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: n.is_read ? 600 : 700, fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                      {n.title}
                    </span>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>
                      {new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.3 }}>
                    {n.message}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
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
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <NotificationMenu />
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
