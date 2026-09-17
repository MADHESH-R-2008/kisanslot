import { useState, useEffect } from 'react';
import { Users, Clock, CheckCircle, Activity, Building2, ArrowRight, SkipForward, Zap, Monitor } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { queueAPI } from '../services/api';

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

const Dashboard = () => {
  const navigate = useNavigate();
  const centreId = parseInt(localStorage.getItem('centre_id') || '1', 10);
  const [stats, setStats] = useState({
    waiting_count: 0, processing_count: 0, serving_count: 0,
    completed_count: 0, skipped_count: 0, cancelled_count: 0,
    active_counters: 0, is_paused: false,
  });
  const role = localStorage.getItem('role') || '';
  const username = localStorage.getItem('username') || 'Admin';

  const fetchStats = async () => {
    try {
      const currentCentreId = parseInt(localStorage.getItem('centre_id') || '1', 10);
      const res = await queueAPI.getCentreStatus(currentCentreId);
      setStats(res.data);
    } catch (err) {
      console.error('Failed to fetch stats', err);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 10000);
    return () => clearInterval(interval);
  }, []);

  const total = stats.waiting_count + stats.processing_count + (stats.serving_count || 0) + stats.completed_count;

  return (
    <div>
      {/* Welcome banner */}
      <div style={{
        background: 'linear-gradient(135deg, var(--primary-color) 0%, #3b82f6 100%)',
        borderRadius: 16, padding: '1.5rem 2rem', marginBottom: '2rem', color: 'white',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem',
      }}>
        <div>
          <h2 style={{ margin: 0, fontWeight: 700, fontSize: '1.4rem' }}>Welcome, {username}! 👋</h2>
          <p style={{ margin: '0.25rem 0 0', opacity: 0.85, fontSize: '0.9rem' }}>
            {role} · Centre {centreId} · {new Date().toLocaleDateString('en-IN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
          </p>
        </div>
        {stats.is_paused && (
          <span style={{ backgroundColor: 'rgba(255,255,255,0.2)', borderRadius: '50px', padding: '0.4rem 1rem', fontWeight: 600, fontSize: '0.875rem' }}>
            ⚠️ Queue Paused
          </span>
        )}
      </div>

      {/* Stats Grid */}
      <div className="stat-grid" style={{ marginBottom: '2rem' }}>
        <StatCard icon={Users} label="Total Farmers Today" value={total} color="#3b82f6" bg="rgba(59,130,246,0.1)" onClick={() => navigate('/bookings')} />
        <StatCard icon={Clock} label="Waiting" value={stats.waiting_count} color="#f59e0b" bg="rgba(245,158,11,0.1)" onClick={() => navigate('/queue')} />
        <StatCard icon={Zap} label="Serving" value={(stats.processing_count || 0) + (stats.serving_count || 0)} color="#3b82f6" bg="rgba(59,130,246,0.1)" onClick={() => navigate('/queue')} />
        <StatCard icon={CheckCircle} label="Completed" value={stats.completed_count} color="#10b981" bg="rgba(16,185,129,0.1)" onClick={() => navigate('/reports')} />
        <StatCard icon={SkipForward} label="Skipped" value={stats.skipped_count || 0} color="#f97316" bg="rgba(249,115,22,0.1)" />
        <StatCard icon={Activity} label="Active Counters" value={stats.active_counters} color="#8b5cf6" bg="rgba(139,92,246,0.1)" />
      </div>

      {/* Quick Actions */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem' }}>
        <div className="card" style={{ padding: '1.5rem' }}>
          <h3 style={{ margin: '0 0 0.5rem' }}>Queue Management</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', margin: '0 0 1.25rem' }}>
            Call farmers, update statuses, pause/resume the queue.
          </p>
          <button className="btn btn-primary" onClick={() => navigate('/queue')} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            Go to Queue <ArrowRight size={16} />
          </button>
        </div>

        <div className="card" style={{ padding: '1.5rem' }}>
          <h3 style={{ margin: '0 0 0.5rem' }}>Procurement</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', margin: '0 0 1.25rem' }}>
            Record quality checks, weighing and complete purchases.
          </p>
          <button className="btn btn-secondary" onClick={() => navigate('/procurement')} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            Open Procurement <ArrowRight size={16} />
          </button>
        </div>

        <div className="card" style={{ padding: '1.5rem' }}>
          <h3 style={{ margin: '0 0 0.5rem' }}>Reports</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', margin: '0 0 1.25rem' }}>
            View today's throughput, completion rate, and queue snapshot.
          </p>
          <button className="btn btn-secondary" onClick={() => navigate('/reports')} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            View Reports <ArrowRight size={16} />
          </button>
        </div>

        <div className="card" style={{ padding: '1.5rem' }}>
          <h3 style={{ margin: '0 0 0.5rem' }}>Counter Management</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', margin: '0 0 1.25rem' }}>
            View counter status, toggle active/inactive, and monitor assignments.
          </p>
          <button className="btn btn-secondary" onClick={() => navigate('/queue')} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <Monitor size={16} /> Manage Counters <ArrowRight size={16} />
          </button>
        </div>

        {['ADMIN', 'SUPER_ADMIN'].includes(role) && (
          <div className="card" style={{ padding: '1.5rem' }}>
            <h3 style={{ margin: '0 0 0.5rem' }}>Centres</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', margin: '0 0 1.25rem' }}>
              Create, edit, or remove procurement centres.
            </p>
            <button className="btn btn-secondary" onClick={() => navigate('/centres')} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              Manage Centres <ArrowRight size={16} />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
