import { useState, useEffect } from 'react';
import { queueAPI } from '../services/api';
import { BarChart2, TrendingUp, Users, CheckCircle2, Clock, XCircle } from 'lucide-react';

const StatCard = ({ icon: Icon, label, value, color, bg, sub }) => (
  <div className="card" style={{ padding: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
    <div style={{ width: 52, height: 52, borderRadius: 12, background: bg, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
      <Icon size={24} color={color} />
    </div>
    <div>
      <div style={{ fontSize: '2rem', fontWeight: 700, lineHeight: 1.1, color: 'var(--text-primary)' }}>{value ?? '—'}</div>
      <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '0.1rem' }}>{label}</div>
      {sub && <div style={{ fontSize: '0.75rem', color, marginTop: '0.2rem' }}>{sub}</div>}
    </div>
  </div>
);

const Reports = () => {
  const centreId = parseInt(localStorage.getItem('centre_id') || '1', 10);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchStats = async () => {
    try {
      const res = await queueAPI.getCentreStatus(centreId);
      setStats(res.data);
    } catch (err) {
      console.error('Failed to load stats', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const total = stats
    ? stats.waiting_count + stats.processing_count + stats.completed_count
    : 0;

  const completionRate = total > 0
    ? Math.round((stats.completed_count / total) * 100)
    : 0;

  const cards = stats
    ? [
        {
          icon: Users,
          label: 'Total Farmers Today',
          value: total,
          color: '#3b82f6',
          bg: 'rgba(59,130,246,0.1)',
        },
        {
          icon: CheckCircle2,
          label: 'Completed',
          value: stats.completed_count,
          color: '#10b981',
          bg: 'rgba(16,185,129,0.1)',
          sub: `${completionRate}% completion rate`,
        },
        {
          icon: Clock,
          label: 'Currently Waiting',
          value: stats.waiting_count,
          color: '#f59e0b',
          bg: 'rgba(245,158,11,0.1)',
        },
        {
          icon: TrendingUp,
          label: 'In Processing',
          value: stats.processing_count,
          color: '#8b5cf6',
          bg: 'rgba(139,92,246,0.1)',
        },
        {
          icon: BarChart2,
          label: 'Active Counters',
          value: stats.active_counters,
          color: '#06b6d4',
          bg: 'rgba(6,182,212,0.1)',
        },
        {
          icon: XCircle,
          label: 'Queue Status',
          value: stats.is_paused ? 'PAUSED' : 'ACTIVE',
          color: stats.is_paused ? '#ef4444' : '#10b981',
          bg: stats.is_paused ? 'rgba(239,68,68,0.1)' : 'rgba(16,185,129,0.1)',
        },
      ]
    : [];

  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ margin: 0 }}>Reports & Analytics</h2>
        <p style={{ color: 'var(--text-secondary)', margin: '0.25rem 0 0' }}>Today's performance overview for Centre {centreId}</p>
      </div>

      {loading ? (
        <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>Loading…</div>
      ) : (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
            {cards.map((c) => <StatCard key={c.label} {...c} />)}
          </div>

          {/* Progress bar */}
          <div className="card" style={{ padding: '1.5rem' }}>
            <h3 style={{ marginTop: 0 }}>Throughput Progress</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '1rem' }}>
              {stats.completed_count} of {total} farmers processed today
            </p>
            <div style={{ backgroundColor: 'var(--bg-color)', borderRadius: '50px', height: 12, overflow: 'hidden' }}>
              <div style={{
                height: '100%',
                width: `${completionRate}%`,
                background: 'linear-gradient(90deg, var(--primary-color), #3b82f6)',
                borderRadius: '50px',
                transition: 'width 0.6s ease',
              }} />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.5rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              <span>0</span>
              <span style={{ fontWeight: 600, color: 'var(--primary-color)' }}>{completionRate}%</span>
              <span>{total}</span>
            </div>
          </div>

          {/* Queue breakdown table */}
          {stats.queue && stats.queue.length > 0 && (
            <div className="card" style={{ marginTop: '1.5rem', overflow: 'hidden' }}>
              <div style={{ padding: '1rem 1.25rem', borderBottom: '1px solid var(--border-color)' }}>
                <h3 style={{ margin: 0 }}>Live Queue Snapshot</h3>
              </div>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ backgroundColor: 'var(--bg-color)' }}>
                      {['#', 'Token', 'Farmer', 'Status', 'Wait Position'].map((h) => (
                        <th key={h} style={{ padding: '0.75rem 1rem', textAlign: 'left', fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-secondary)', fontWeight: 600, borderBottom: '1px solid var(--border-color)' }}>
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {stats.queue.slice(0, 10).map((entry, i) => (
                      <tr key={entry.booking_id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                        <td style={{ padding: '0.75rem 1rem', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>{i + 1}</td>
                        <td style={{ padding: '0.75rem 1rem', fontWeight: 700, color: 'var(--primary-color)' }}>#{entry.token}</td>
                        <td style={{ padding: '0.75rem 1rem' }}>{entry.farmer_name}</td>
                        <td style={{ padding: '0.75rem 1rem' }}>
                          <span style={{ padding: '0.15rem 0.5rem', borderRadius: '50px', fontSize: '0.75rem', fontWeight: 600, backgroundColor: 'rgba(16,185,129,0.1)', color: '#065f46' }}>{entry.status}</span>
                        </td>
                        <td style={{ padding: '0.75rem 1rem', color: 'var(--text-secondary)' }}>{entry.queue_position ? `#${entry.queue_position}` : '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default Reports;
