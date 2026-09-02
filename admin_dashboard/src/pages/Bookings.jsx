import { useState, useEffect } from 'react';
import { queueAPI } from '../services/api';
import { Search, RefreshCw } from 'lucide-react';

const statusColors = {
  CONFIRMED: { bg: '#fef3c7', color: '#92400e' },
  ARRIVED:   { bg: '#dbeafe', color: '#1e40af' },
  WAITING:   { bg: '#fef3c7', color: '#92400e' },
  CALLED:    { bg: '#ede9fe', color: '#5b21b6' },
  PROCESSING:{ bg: '#d1fae5', color: '#065f46' },
  COMPLETED: { bg: '#f0fdf4', color: '#15803d' },
  CANCELLED: { bg: '#fee2e2', color: '#991b1b' },
  NO_SHOW:   { bg: '#fecaca', color: '#7f1d1d' },
};

const StatusBadge = ({ status }) => {
  const s = statusColors[status] || { bg: '#f3f4f6', color: '#374151' };
  return (
    <span style={{ backgroundColor: s.bg, color: s.color, padding: '0.2rem 0.65rem', borderRadius: '50px', fontSize: '0.75rem', fontWeight: 600 }}>
      {status}
    </span>
  );
};

const Bookings = () => {
  const [bookings, setBookings] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  const fetchBookings = async () => {
    setLoading(true);
    try {
      const res = await queueAPI.getAdminList();
      setBookings(res.data);
      setFiltered(res.data);
    } catch (err) {
      console.error('Failed to load bookings', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchBookings(); }, []);

  useEffect(() => {
    let data = bookings;
    if (statusFilter !== 'ALL') {
      data = data.filter((b) => b.status === statusFilter);
    }
    if (search.trim()) {
      const q = search.toLowerCase();
      data = data.filter(
        (b) =>
          b.booking_id?.toLowerCase().includes(q) ||
          b.farmer_name?.toLowerCase().includes(q) ||
          b.crop?.toLowerCase().includes(q) ||
          String(b.token_number).includes(q)
      );
    }
    setFiltered(data);
  }, [search, statusFilter, bookings]);

  const statuses = ['ALL', 'CONFIRMED', 'WAITING', 'ARRIVED', 'CALLED', 'PROCESSING', 'COMPLETED', 'CANCELLED', 'NO_SHOW'];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ margin: 0 }}>Bookings</h2>
          <p style={{ color: 'var(--text-secondary)', margin: '0.25rem 0 0' }}>All active bookings for your centre</p>
        </div>
        <button className="btn btn-secondary" onClick={fetchBookings} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <RefreshCw size={16} /> Refresh
        </button>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.25rem', flexWrap: 'wrap', alignItems: 'center' }}>
        <div style={{ position: 'relative', flex: '1', minWidth: '200px' }}>
          <Search size={16} style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }} />
          <input
            type="text"
            placeholder="Search by name, booking ID, crop…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ width: '100%', padding: '0.6rem 0.75rem 0.6rem 2.25rem', borderRadius: '8px', border: '1px solid var(--border-color)', backgroundColor: 'var(--card-bg)', color: 'var(--text-primary)', outline: 'none', fontSize: '0.875rem' }}
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          style={{ padding: '0.6rem 0.75rem', borderRadius: '8px', border: '1px solid var(--border-color)', backgroundColor: 'var(--card-bg)', color: 'var(--text-primary)', outline: 'none', fontSize: '0.875rem' }}
        >
          {statuses.map((s) => <option key={s} value={s}>{s === 'ALL' ? 'All Statuses' : s}</option>)}
        </select>
      </div>

      <div className="card" style={{ overflow: 'hidden' }}>
        <div style={{ padding: '0.75rem 1.25rem', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
            {filtered.length} booking{filtered.length !== 1 ? 's' : ''}
          </span>
        </div>
        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>Loading bookings…</div>
        ) : filtered.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>No bookings found.</div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ backgroundColor: 'var(--bg-color)' }}>
                  {['Token', 'Booking ID', 'Farmer', 'Crop', 'Qty (kg)', 'Slot', 'Vehicle', 'Status'].map((h) => (
                    <th key={h} style={{ padding: '0.75rem 1rem', textAlign: 'left', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-secondary)', fontWeight: 600, borderBottom: '1px solid var(--border-color)', whiteSpace: 'nowrap' }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((b) => (
                  <tr key={b.booking_id}
                    style={{ borderBottom: '1px solid var(--border-color)', transition: 'background 0.15s' }}
                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--bg-color)'}
                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = ''}
                  >
                    <td style={{ padding: '0.8rem 1rem', fontWeight: 700, color: 'var(--primary-color)' }}>#{b.token_number}</td>
                    <td style={{ padding: '0.8rem 1rem', fontSize: '0.8rem', color: 'var(--text-secondary)', fontFamily: 'monospace' }}>{b.booking_id}</td>
                    <td style={{ padding: '0.8rem 1rem', fontWeight: 500 }}>{b.farmer_name || b.centre || '—'}</td>
                    <td style={{ padding: '0.8rem 1rem' }}>{b.crop}</td>
                    <td style={{ padding: '0.8rem 1rem', textAlign: 'right' }}>{b.quantity?.toLocaleString() || '—'}</td>
                    <td style={{ padding: '0.8rem 1rem', fontSize: '0.8rem' }}>
                      <div>{b.date}</div>
                      <div style={{ color: 'var(--text-secondary)' }}>{b.time}</div>
                    </td>
                    <td style={{ padding: '0.8rem 1rem', fontSize: '0.875rem' }}>{b.vehicle_number || '—'}</td>
                    <td style={{ padding: '0.8rem 1rem' }}><StatusBadge status={b.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default Bookings;
