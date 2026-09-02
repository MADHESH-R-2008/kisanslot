import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { LayoutDashboard, Users, CalendarDays, BarChart, Settings, LogOut, CheckSquare } from 'lucide-react';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Queue from './pages/Queue';
import './index.css';

// Simple Auth Context mock for routing
const PrivateRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  return token ? children : <Navigate to="/login" />;
};

const Sidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    navigate('/login');
  };

  const navItems = [
    { path: '/', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/queue', label: 'Queue Management', icon: Users },
    { path: '/bookings', label: 'Bookings', icon: CalendarDays },
    { path: '/procurement', label: 'Procurement', icon: CheckSquare },
    { path: '/reports', label: 'Reports', icon: BarChart },
  ];

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <div style={{width: 32, height: 32, backgroundColor: 'var(--primary-color)', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white'}}>K</div>
        KisanSlot
      </div>
      <div className="sidebar-nav">
        {navItems.map((item) => (
          <div
            key={item.path}
            className={`nav-link ${location.pathname === item.path ? 'active' : ''}`}
            onClick={() => navigate(item.path)}
            style={{cursor: 'pointer'}}
          >
            <item.icon size={20} />
            {item.label}
          </div>
        ))}
      </div>
      <div style={{marginTop: 'auto'}}>
        <div className="nav-link" onClick={handleLogout} style={{cursor: 'pointer', color: 'var(--danger-color)'}}>
          <LogOut size={20} />
          Logout
        </div>
      </div>
    </div>
  );
};

const Layout = ({ children }) => {
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    if (isDark) {
      document.body.setAttribute('data-theme', 'dark');
    } else {
      document.body.removeAttribute('data-theme');
    }
  }, [isDark]);

  return (
    <div className="app-container">
      <Sidebar />
      <div className="main-content">
        <div className="topbar">
          <h2 style={{fontSize: '1.25rem', margin: 0}}>Admin Dashboard</h2>
          <div style={{display: 'flex', alignItems: 'center', gap: '1rem'}}>
            <button className="btn btn-secondary" onClick={() => setIsDark(!isDark)}>
              {isDark ? '☀️ Light' : '🌙 Dark'}
            </button>
            <div style={{width: 40, height: 40, borderRadius: '50%', backgroundColor: 'var(--primary-color)', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold'}}>
              A
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

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<PrivateRoute><Layout><Dashboard /></Layout></PrivateRoute>} />
        <Route path="/queue" element={<PrivateRoute><Layout><Queue /></Layout></PrivateRoute>} />
        <Route path="/bookings" element={<PrivateRoute><Layout><div><h2>Bookings (WIP)</h2></div></Layout></PrivateRoute>} />
        <Route path="/procurement" element={<PrivateRoute><Layout><div><h2>Procurement (WIP)</h2></div></Layout></PrivateRoute>} />
        <Route path="/reports" element={<PrivateRoute><Layout><div><h2>Reports (WIP)</h2></div></Layout></PrivateRoute>} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
