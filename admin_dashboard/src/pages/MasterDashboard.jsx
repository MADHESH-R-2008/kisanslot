import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Building2, Users, CalendarDays, Activity, Clock, CheckSquare,
  WalletCards, ArrowRight, MapPin, XCircle
} from 'lucide-react';
import { masterAPI } from '../services/masterApi';

const StatCard = ({ icon: Icon, label, value, color, bg, onClick }) => (
  <div
    className="card stat-card"
    onClick={onClick}
    style={{ cursor: onClick ? 'pointer' : 'default', transition: 'transform 0.15s, box-shadow 0.15s' }}
    onMouseEnter={(e) => { if (onClick) { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = 'var(--shadow-lg)'; } }}
    onMouseLeave={(e) => { e.currentTarget.style.transform = ''; e.currentTarget.style.boxShadow = ''; }}
  >
    <div className="stat-icon" style={{ backgroundColor: bg, color }}>
      <Icon size={24} />
    </div>
    <div className="stat-info">
      <h3>{label}</h3>
      <p>{value ?? '—'}</p>
    </div>
  </div>
);

const MasterDashboard = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const username = localStorage.getItem('username') || 'Master';
  const districtName = localStorage.getItem('district_name') || '';

  const fetchDashboard = async () => {
    try {
      const res = await masterAPI.dashboard();
      setStats(res.data);
      setError('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
    const interval = setInterval(fetchDashboard, 15000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 300 }}>
        <div style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
          <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>⏳</div>
          <p>Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card" style={{ padding: '2rem', textAlign: 'center', color: 'var(--danger-color)' }}>
        <XCircle size={32} style={{ marginBottom: '0.5rem' }} />
        <p>{error}</p>
        <button className="btn btn-primary" onClick={fetchDashboard} style={{ marginTop: '1rem' }}>Retry</button>
      </div>
    );
  }

  return (
    <div>
      {/* Welcome Banner */}
      <div style={{
        background: 'linear-gradient(135deg, #7c3aed 0%, #2563eb 50%, #0891b2 100%)',
        borderRadius: 16, padding: '1.5rem 2rem', marginBottom: '2rem', color: 'white',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem',
      }}>
        <div>
          <h2 style={{ margin: 0, fontWeight: 700, fontSize: '1.4rem' }}>Welcome, {username}! 👋</h2>
          <p style={{ margin: '0.25rem 0 0', opacity: 0.85, fontSize: '0.9rem' }}>
            MASTER · {new Date().toLocaleDateString('en-IN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
          </p>
        </div>
        <div style={{
          display: 'flex', alignItems: 'center', gap: '0.5rem',
          backgroundColor: 'rgba(255,255,255,0.15)', borderRadius: 50, padding: '0.5rem 1.25rem',
          backdropFilter: 'blur(10px)',
        }}>
          <MapPin size={16} />
          <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{stats?.district || districtName}</span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="stat-grid" style={{ marginBottom: '2rem' }}>
        <StatCard
          icon={Building2} label="Total Centres" value={stats?.total_centres}
          color="#3b82f6" bg="rgba(59,130,246,0.1)"
          onClick={() => navigate('/master/centres')}
        />
        <StatCard
          icon={CheckSquare} label="Active Centres" value={stats?.active_centres}
          color="#10b981" bg="rgba(16,185,129,0.1)"
          onClick={() => navigate('/master/centres')}
        />
        <StatCard
          icon={XCircle} label="Inactive Centres" value={stats?.inactive_centres}
          color="#ef4444" bg="rgba(239,68,68,0.1)"
        />
        <StatCard
          icon={Users} label="Total Operators" value={stats?.total_operators}
          color="#8b5cf6" bg="rgba(139,92,246,0.1)"
          onClick={() => navigate('/master/operators')}
        />
        <StatCard
          icon={CalendarDays} label="Today's Bookings" value={stats?.today_bookings}
          color="#f59e0b" bg="rgba(245,158,11,0.1)"
          onClick={() => navigate('/bookings')}
        />
        <StatCard
          icon={Activity} label="Live Queue" value={stats?.live_queue}
          color="#06b6d4" bg="rgba(6,182,212,0.1)"
          onClick={() => navigate('/queue')}
        />
        <StatCard
          icon={Clock} label="Pending Procurement" value={stats?.pending_procurement}
          color="#f97316" bg="rgba(249,115,22,0.1)"
          onClick={() => navigate('/procurement')}
        />
        <StatCard
          icon={WalletCards} label="Pending Payments" value={stats?.pending_payments}
          color="#ec4899" bg="rgba(236,72,153,0.1)"
          onClick={() => navigate('/payments')}
        />
      </div>

      {/* Quick Actions */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem' }}>
        <div className="card" style={{ padding: '1.5rem' }}>
          <h3 style={{ margin: '0 0 0.5rem' }}>Centre Management</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', margin: '0 0 1.25rem' }}>
            View, create, and manage centres in your district.
          </p>
          <button className="btn btn-primary" onClick={() => navigate('/master/centres')} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            Manage Centres <ArrowRight size={16} />
          </button>
        </div>

        <div className="card" style={{ padding: '1.5rem' }}>
          <h3 style={{ margin: '0 0 0.5rem' }}>Operator Management</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', margin: '0 0 1.25rem' }}>
            Create and manage operators for your centres.
          </p>
          <button className="btn btn-secondary" onClick={() => navigate('/master/operators')} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            Manage Operators <ArrowRight size={16} />
          </button>
        </div>

        <div className="card" style={{ padding: '1.5rem' }}>
          <h3 style={{ margin: '0 0 0.5rem' }}>Queue Monitoring</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', margin: '0 0 1.25rem' }}>
            Monitor live queue across all your district centres.
          </p>
          <button className="btn btn-secondary" onClick={() => navigate('/queue')} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            View Queue <ArrowRight size={16} />
          </button>
        </div>

        <div className="card" style={{ padding: '1.5rem' }}>
          <h3 style={{ margin: '0 0 0.5rem' }}>Reports & Analytics</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', margin: '0 0 1.25rem' }}>
            View district-level reports and performance data.
          </p>
          <button className="btn btn-secondary" onClick={() => navigate('/reports')} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            View Reports <ArrowRight size={16} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default MasterDashboard;
